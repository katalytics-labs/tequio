"""Read-only prerequisite observations with real checks and synthetic historical data."""
import concurrent.futures
import json
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import test_lifecycle as fixtures
from task_review_fixtures import synthetic_draft
from tequio.core import Error


class StatusPrerequisites(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    docs=fixtures.Lifecycle.docs
    report=fixtures.Lifecycle.report
    finish=fixtures.Lifecycle.finish

    def image(self):
        return {str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def observe(self):
        before=self.image();s=self.w.status();self.assertEqual(before,self.image());return s

    def prepare(self):
        self.add(self.task());c=self.w.claim('synthetic-writer');self.w.verify('A',c['token']);return c

    def test_stale_candidate_must_stabilize_before_reconciliation(self):
        c=self.prepare();self.docs(c)
        self.w.review('A',c['token'],'synthetic-reviewer','correctness',self.report(),[])
        self.assertEqual(self.observe()['workflow']['stage'],'ready-for-closure')
        (self.root/'a.txt').write_text('implementation changed')
        s=self.observe();self.assertEqual(s['tasks'][0]['checks'],{'state':'stale'})
        self.assertEqual(s['workflow']['stage'],'verification-required')
        self.assertIn('Finish outstanding implementation/documentation edits',s['workflow']['next']['reason'])
        with self.assertRaisesRegex(Error,'Verify actual behavior'):self.docs(c)
        # Finish remaining documentation edits before the one new final verification.
        (self.root/'behavior.md').write_text('current observed behavior')
        self.assertEqual(self.observe()['workflow']['stage'],'verification-required')
        self.w.verify('A',c['token']);self.assertEqual(self.observe()['workflow']['stage'],'documentation-and-review')
        self.docs(c);self.assertEqual(self.observe()['workflow']['stage'],'review')
        with self.w.transaction() as con:self.assertEqual(con.execute("SELECT count(*) FROM events WHERE kind='verified'").fetchone()[0],2)

    def test_missing_failed_invalid_unavailable_are_fixed_observations(self):
        c=self.prepare()
        with self.w.transaction() as con:
            original=con.execute("SELECT checks FROM tasks WHERE id='A'").fetchone()[0]
            con.execute("UPDATE tasks SET checks=NULL WHERE id='A'")
        self.assertEqual(self.observe()['tasks'][0]['checks'],{'state':'missing'})
        with self.w.transaction() as con:con.execute("UPDATE tasks SET checks=? WHERE id='A'",(original,))
        with patch.object(self.w,'receipt',side_effect=OSError('PRIVATE_ERROR')):
            s=self.observe();self.assertEqual(s['tasks'][0]['checks'],{'state':'unavailable'})
            self.assertNotIn('PRIVATE',json.dumps(s['tasks'][0]['checks']))
        ref=json.loads(original);(self.w.path/ref['path']).write_text('{PRIVATE}')
        self.assertEqual(self.observe()['tasks'][0]['checks'],{'state':'invalid'})
        self.assertEqual(self.observe()['workflow']['stage'],'verification-required')
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Missing evidence cannot close')

    def test_actual_failed_check_is_not_current(self):
        t=self.task();t['checks']=[[sys.executable,'-c','raise SystemExit(3)']];self.add(t);c=self.w.claim('writer')
        self.assertFalse(self.w.verify('A',c['token'])['passed'])
        self.assertEqual(self.observe()['tasks'][0]['checks'],{'state':'failed'})
        # Corrupted lifecycle fixture cannot turn failed evidence into a review recommendation.
        with self.w.transaction() as con:con.execute("UPDATE tasks SET status='review'")
        self.assertEqual(self.observe()['workflow']['stage'],'verification-required')

    def test_draft_projection_privacy_and_legacy_unknown(self):
        t=synthetic_draft(self.task());t['draft']['reason']='PRIVATE_REASON '+t['draft']['reason'];t['draft']['next_action']='PRIVATE_ACTION '+t['draft']['next_action'];self.add(t)
        s=self.observe();self.assertEqual(s['tasks'][0]['draft_readiness'],{'state':'recorded','category':'unresolved-product-decision'})
        self.assertEqual(s['workflow']['next']['task'],'A');self.assertNotIn('PRIVATE',json.dumps(s))
        self.assertIn('metadata alone',s['workflow']['next']['reason'])
        with self.w.transaction() as con:
            body=json.loads(con.execute('SELECT body FROM tasks').fetchone()[0]);del body['draft'];con.execute('UPDATE tasks SET body=?',(json.dumps(body),))
        self.assertEqual(self.observe()['tasks'][0]['draft_readiness'],{'state':'legacy-unknown','category':None})
        with self.w.transaction() as con:
            body['draft']={'category':'PRIVATE_CATEGORY'};con.execute('UPDATE tasks SET body=?',(json.dumps(body),))
        s=self.observe();self.assertEqual(s['tasks'][0]['draft_readiness'],{'state':'invalid','category':None});self.assertNotIn('PRIVATE',json.dumps(s))
        with self.assertRaises(Error):self.w.claim('writer','A')

    def test_recorded_draft_is_selected_before_legacy_unknown(self):
        old=synthetic_draft(self.task('OLD'));new=synthetic_draft(self.task('NEW'));self.add(old,new)
        with self.w.transaction() as con:
            body=json.loads(con.execute("SELECT body FROM tasks WHERE id='OLD'").fetchone()[0]);del body['draft'];con.execute("UPDATE tasks SET body=? WHERE id='OLD'",(json.dumps(body),))
        s=self.observe();self.assertEqual(s['workflow']['next']['task'],'NEW')
        self.assertEqual(s['tasks'][0]['draft_readiness']['state'],'legacy-unknown')
        self.assertEqual(s['tasks'][1]['draft_readiness']['state'],'recorded')

    def test_ready_dependency_and_closed_history_are_distinct(self):
        self.add(self.task('A'),self.task('B',depends=['A']))
        s=self.observe();b=s['tasks'][1];self.assertEqual(b['status'],'ready');self.assertFalse(b['dispatchable']);self.assertEqual(b['draft_readiness']['state'],'not-applicable')
        self.finish(self.w.claim('writer','A'));s=self.observe()
        self.assertEqual(s['tasks'][0]['checks'],{'state':'not-observed'});self.assertTrue(s['tasks'][1]['dispatchable'])

    def test_live_verification_precedes_another_action(self):
        t=self.task();t['checks']=[[sys.executable,'-c',"from pathlib import Path;import time;Path('.tequio/started').touch();time.sleep(.3)"]];self.add(t);c=self.w.claim('writer')
        with concurrent.futures.ThreadPoolExecutor() as pool:
            f=pool.submit(self.w.verify,'A',c['token']);until=time.monotonic()+4
            while not (self.root/'.tequio/started').exists() and time.monotonic()<until:time.sleep(.01)
            self.assertTrue((self.root/'.tequio/started').exists());s=self.w.status()
            self.assertEqual(s['workflow']['stage'],'reconcile-active-work')
            self.assertEqual(s['workflow']['next']['skill'],'tequio-pickup')
            with self.assertRaises(Error):self.w.verify('A',c['token'])
            self.assertTrue(f.result()['passed'])

    def test_phase_integration_and_security_review_precedence(self):
        c=self.prepare()
        with patch('tequio.integration.Journal.status',return_value={'tasks':[{'task':'A','state':'pending-integration'}]}):
            self.assertEqual(self.observe()['workflow']['stage'],'reconcile-active-work')
        (self.w.path/'plans/delivery.md').write_text('changed current plan')
        self.assertEqual(self.observe()['workflow']['next']['skill'],'tequio-pickup')

    def test_integration_barrier_and_stopped_attempt_cannot_recommend_closure(self):
        c=self.prepare();self.docs(c);self.w.review('A',c['token'],'synthetic-reviewer','correctness',self.report(),[])
        self.assertEqual(self.observe()['workflow']['stage'],'ready-for-closure')
        for state in ['needs-checks','needs-docs','needs-review']:
            with self.subTest(state=state),patch('tequio.integration.Journal.status',return_value={'tasks':[{'task':'A','state':state}]}):
                self.assertEqual(self.observe()['workflow']['stage'],'reconcile-active-work')
        from tequio.verification import paths,save
        _,metadata=paths(self.w,'A')
        save(metadata,{'version':1,'state':'stopped','attempt':'synthetic-stopped-fixture','child_pid':None,'process_group':None})
        s=self.observe();self.assertEqual(s['tasks'][0]['checks']['state'],'current')
        self.assertEqual(s['workflow']['next']['skill'],'tequio-pickup')
        with self.assertRaisesRegex(Error,'Unresolved verification result'):
            self.w.complete('A',c['token'],'Old PASS cannot bypass stopped attempt')

    def test_journal_reconciliation_names_the_affected_active_task(self):
        self.add(self.task('A'),self.task('B'));self.w.claim('writer-a','A');b=self.w.claim('writer-b','B')
        self.w.verify('B',b['token']);self.docs(b)
        with patch('tequio.integration.Journal.status',return_value={'tasks':[{'task':'B','state':'needs-docs'}]}):
            self.assertEqual(self.observe()['workflow']['next']['task'],'B')
        with patch('tequio.integration.Journal.status',return_value={'tasks':[],'state':'invalid'}):
            self.assertEqual(self.observe()['workflow']['next']['task'],'A')

    def test_current_security_findings_are_not_hidden_by_checks(self):
        self.add(self.task(risk='security'));c=self.w.claim('writer');self.w.verify('A',c['token']);self.docs(c)
        self.w.review('A',c['token'],'synthetic-correctness','correctness',self.report(),[])
        self.assertEqual(self.observe()['workflow']['stage'],'security-review')
        self.w.review('A',c['token'],'synthetic-security','security',self.report(),['Synthetic open security finding'])
        self.assertEqual(self.observe()['workflow']['stage'],'review-follow-up')

    def test_cli_and_existing_lane_intake_contract_remains(self):
        self.add(self.task());r=subprocess.run([sys.executable,str(fixtures.ROOT/'bin/tequio'),'--project',str(self.root),'--workspace','fixture','status'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['tasks'][0]['checks']['state'],'missing')

if __name__=='__main__':unittest.main()
