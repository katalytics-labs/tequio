"""Bounded policy, publication and acceptance integration; fixtures are synthetic."""
import base64
import copy
import json
import sys
import unittest
from unittest.mock import patch
import test_lifecycle as fixtures
from tequio.core import Error,digest
from tequio.reporting import proof,validate_check_receipt
from tequio.cli import verification_summary


class CaptureReceipts(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    docs=fixtures.Lifecycle.docs
    report=fixtures.Lifecycle.report
    def bounded(self,checks,limit=1024):
        t=self.task();t['checks']=checks;t['capture']={'version':1,'mode':'bounded-v1','max_bytes':limit};self.add(t);return t,self.w.claim('writer')
    def test_bounded_success_hash_proof_docs_review_and_completion(self):
        t,c=self.bounded([[sys.executable,'-c',"print('actual result')"]])
        e=self.w._verify('A',c['token'],summary=True);r=e['receipt'];s=verification_summary(e)
        self.assertTrue(r['passed']);self.assertEqual(r['schema_version'],2);self.assertEqual(s['checks'],{'attempted':1,'executed':1,'passed':1,'failed':0,'skipped':0});self.assertEqual(s['schema_version'],2)
        self.assertEqual(self.w.receipt(e['reference']),r);self.assertEqual(proof(self.root,'fixture','A')['tasks'][0]['checks']['state'],'current')
        self.docs(c);self.w.review('A',c['token'],'synthetic-reviewer','correctness',self.report(),[]);self.w.complete('A',c['token'],'Actual bounded fixture accepted');self.assertEqual(self.w.status()['tasks'][0]['status'],'done')
    def test_limit_exit_zero_skips_unattempted_and_fails_closed(self):
        t,c=self.bounded([[sys.executable,'-c',"print('PRIVATE_OUTPUT'*100)"],[sys.executable,'-c',"raise RuntimeError('must not launch')"]],16)
        e=self.w._verify('A',c['token'],summary=True);r=e['receipt'];s=verification_summary(e)
        self.assertFalse(r['passed']);self.assertEqual(r['capture']['retained_bytes'],16);self.assertEqual(r['capture']['attempted'],1);self.assertEqual(r['capture']['skipped'],[{'check':2,'reason':'limit-exceeded'}]);self.assertEqual(s['checks']['skipped'],1);self.assertNotIn('PRIVATE',json.dumps(s));self.assertEqual(s['diagnostics'][0]['code'],'capture-limit-exceeded')
        self.assertEqual(proof(self.root,'fixture','A')['tasks'][0]['checks']['state'],'failed')
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Incomplete evidence cannot pass')
    def test_launch_failure_counts_attempt_not_execution_and_continues(self):
        t,c=self.bounded([['missing-PRIVATE-command'],[sys.executable,'-c','print("success")']])
        s=verification_summary(self.w._verify('A',c['token'],summary=True));self.assertEqual(s['checks'],{'attempted':2,'executed':1,'passed':1,'failed':1,'skipped':0});self.assertFalse(s['passed']);self.assertNotIn('PRIVATE',json.dumps(s));self.assertEqual(s['diagnostics'][0],{'check':1,'code':'check-launch-failed'})
    def test_timeout_retains_raw_and_readable_prefix(self):
        t,c=self.bounded([[sys.executable,'-c',"import os,time;os.write(1,b'prefix\\xff');time.sleep(3)"]])
        r=self.w.verify('A',c['token'],timeout=1);self.assertFalse(r['passed']);self.assertEqual(base64.b64decode(r['results'][0]['capture']['stdout_base64']),b'prefix\xff');self.assertIn('prefix',r['results'][0]['stdout']);self.assertEqual(r['capture']['state'],'timeout')
    def test_budget_is_attempt_wide_exact_boundary_and_nonzero_continues(self):
        t,c=self.bounded([[sys.executable,'-c',"import os;os.write(1,b'1234')"],[sys.executable,'-c',"import os;os.write(2,b'56789')"]],8)
        r=self.w.verify('A',c['token']);self.assertFalse(r['passed']);self.assertEqual(r['capture']['retained_bytes'],8);self.assertEqual(r['capture']['attempted'],2)
    def test_malformed_policy_including_drafts_refused(self):
        good={'version':1,'mode':'bounded-v1','max_bytes':10}
        for value in [None,{},dict(good,version=True),dict(good,max_bytes=True),dict(good,max_bytes=0),dict(good,max_bytes=16777217),dict(good,extra='private')]:
            for stage in ['ready','draft']:
                t=self.task();t.update(capture=value,stage=stage)
                with self.assertRaises(Error):self.w.validate_task(t)
    def test_corrupt_counts_base64_unknown_version_cannot_be_accepted(self):
        t,c=self.bounded([[sys.executable,'-c','print("actual")']]);r=self.w.verify('A',c['token'])
        mutations=[]
        for key,value in [('schema_version',99),('passed',False)]:
            bad=copy.deepcopy(r);bad[key]=value;mutations.append(bad)
        for key,value in [('complete',False),('attempted',2),('executed',0),('retained_bytes',999),('skipped',[{'check':1,'reason':'timeout'}])]:
            bad=copy.deepcopy(r);bad['capture'][key]=value;mutations.append(bad)
        bad=copy.deepcopy(r);bad['results'][0]['capture']['stdout_base64']='%%%';mutations.append(bad)
        bad=copy.deepcopy(r);bad['results'][0]['capture']['stdout_observed_bytes']+=1;bad['capture']['observed_bytes']+=1;mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(Error):validate_check_receipt(bad,t)
        # Even a correctly rehashed malformed bounded record is refused by acceptance.
        with self.w.transaction() as con:ref=json.loads(con.execute('SELECT checks FROM tasks').fetchone()[0])
        p=self.w.path/ref['path'];p.write_text(json.dumps(mutations[2]));ref['hash']=digest(p.read_bytes())
        with self.w.transaction() as con:con.execute('UPDATE tasks SET checks=?',(json.dumps(ref),))
        self.assertEqual(proof(self.root,'fixture','A')['tasks'][0]['checks']['state'],'invalid')
        with self.assertRaises(Error):self.docs(c)
    def test_oversized_receipt_rejected_before_json_load(self):
        t,c=self.bounded([[sys.executable,'-c','print("x")']],1);self.w.verify('A',c['token'])
        with self.w.transaction() as con:ref=json.loads(con.execute('SELECT checks FROM tasks').fetchone()[0])
        p=self.w.path/ref['path'];p.write_bytes(b'x'*(1048576+9))
        with self.assertRaisesRegex(Error,'size limit'):self.w.check_receipt(t,ref)
    def test_publication_failure_keeps_old_pointer_but_cannot_reuse_old_pass(self):
        t,c=self.bounded([[sys.executable,'-c','print("actual")']]);self.w.verify('A',c['token'])
        with self.w.transaction() as con:old=con.execute('SELECT checks FROM tasks').fetchone()[0]
        from tequio import core
        original=core.write
        def fail(p,data):
            if '/evidence/' in str(p):raise OSError('synthetic publish failure')
            return original(p,data)
        with patch.object(core,'write',fail),self.assertRaises(OSError):self.w.verify('A',c['token'])
        with self.w.transaction() as con:self.assertEqual(con.execute('SELECT checks FROM tasks').fetchone()[0],old)
        with self.assertRaises(Error):self.w.complete('A',c['token'],'No new accepted result')

    def test_bounded_envelope_and_current_inputs_are_required(self):
        t,c=self.bounded([[sys.executable,'-c','print("actual")']]);r=self.w.verify('A',c['token'])
        for key in ['inputs','snapshot','at']:
            bad=copy.deepcopy(r);del bad[key]
            with self.assertRaises(Error):validate_check_receipt(bad,t)
        with self.w.transaction() as con:ref=json.loads(con.execute('SELECT checks FROM tasks').fetchone()[0])
        r['inputs']='0'*64;p=self.w.path/ref['path'];p.write_text(json.dumps(r));ref['hash']=digest(p.read_bytes())
        with self.w.transaction() as con:con.execute('UPDATE tasks SET checks=?',(json.dumps(ref),))
        self.assertEqual(proof(self.root,'fixture','A')['tasks'][0]['checks']['state'],'stale')
        with self.assertRaisesRegex(Error,'inputs stale'):self.docs(c)

    def test_final_publication_size_includes_integration_and_newline(self):
        t,c=self.bounded([[sys.executable,'-c','print("x")']],64);ceiling=8*64+1048576
        from tequio import core
        original=json.dumps;written=[];write=core.write
        def encoded(obj,*a,**kw):
            if isinstance(obj,dict) and obj.get('schema_version')==2 and 'results' in obj:
                return ' '*(ceiling if 'integration' in obj else ceiling-1)
            return original(obj,*a,**kw)
        def spy(path,value):written.append(str(path));return write(path,value)
        meta={'commit':'a'*40,'head':'b'*40,'epoch':1}
        with patch('tequio.integration.Journal.classify',return_value=meta),patch('tequio.integration.Journal.gate'),patch.object(json,'dumps',encoded),patch.object(core,'write',spy):
            with self.assertRaisesRegex(Error,'size limit'):self.w.verify('A',c['token'])
        self.assertFalse(written)

    def test_registered_integration_rejects_oversized_bounded_receipt(self):
        import test_integration_journal as f
        case=f.Integration();original=case.task
        case.task=lambda *a,**kw:{**original(*a,**kw),'capture':{'version':1,'mode':'bounded-v1','max_bytes':1024}}
        case.setUp()
        try:
            case.plan();case.merge();case.j.reconcile('A');r=case.w.verify('A',case.c['token']);self.assertTrue(r['passed'])
            with case.w.transaction() as con:ref=json.loads(con.execute('SELECT checks FROM tasks').fetchone()[0])
            path=case.w.path/ref['path'];path.write_bytes(b'x'*(8*1024+1048577));ref['hash']=digest(path.read_bytes())
            with case.w.transaction() as con:con.execute('UPDATE tasks SET checks=?',(json.dumps(ref),))
            read=case.w.receipt
            def bounded(ref_arg,**kw):
                if ref_arg['path']==ref['path']:self.assertIsNotNone(kw.get('max_bytes'))
                return read(ref_arg,**kw)
            with patch.object(case.w,'receipt',bounded):self.assertEqual(case.state(),'needs-checks')
        finally:case.tearDown()

if __name__=='__main__':unittest.main()
