"""Real synthetic command executions and publication races; no live credentials."""
import concurrent.futures
import contextlib
import io
import json
import sys
import time
import unittest
from unittest.mock import patch
import test_lifecycle as fixtures
from tequio.core import Workspace, digest
from tequio.cli import main


class VerificationSummary(unittest.TestCase):
    setUp = fixtures.Lifecycle.setUp
    tearDown = fixtures.Lifecycle.tearDown
    task = fixtures.Lifecycle.task
    add = fixtures.Lifecycle.add

    def start(self, checks):
        t=self.task();t['checks']=checks;self.add(t);return self.w.claim('writer')

    def call(self, claim, summary=True, timeout=120):
        out,err=io.StringIO(),io.StringIO()
        argv=['--project',str(self.root),'--workspace','fixture','verify','A','--token',claim['token'],'--timeout',str(timeout)]
        if summary:argv.append('--summary')
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):code=main(argv)
        return code,out.getvalue(),err.getvalue()

    def validate(self, summary):
        self.assertEqual(set(summary),{'schema_version','task','passed','stable','checks','receipt','diagnostics','omitted_diagnostics'})
        self.assertEqual(summary['schema_version'],1)
        self.assertEqual(set(summary['checks']),{'executed','passed','failed'})
        self.assertEqual(set(summary['receipt']),{'path','hash'})
        for d in summary['diagnostics']:self.assertEqual(set(d),{'check','code'})
        raw=(self.w.path/summary['receipt']['path']).read_bytes()
        self.assertEqual(digest(raw),summary['receipt']['hash'])
        receipt=json.loads(raw)
        for k in ['task','passed','stable']:self.assertEqual(summary[k],receipt[k])
        self.assertNotIn('diagnostics',receipt)
        return receipt

    def test_success_volume_privacy_and_exact_schema(self):
        c=self.start([[sys.executable,'-c',"print('PRIVATE_STDOUT\\n'*2000);import sys;print('PRIVATE_STDERR',file=sys.stderr);sys.stdout.buffer.write(bytes([255]))"]])
        code,out,err=self.call(c);self.assertEqual(code,0,err)
        s=json.loads(out);r=self.validate(s)
        self.assertLess(len(out.encode()),2048);self.assertNotIn('PRIVATE_',out)
        self.assertGreater(len(r['results'][0]['stdout']),20000)
        self.assertIn('\ufffd',r['results'][0]['stdout'])
        self.assertEqual(s['checks'],{'executed':1,'passed':1,'failed':0})
        self.assertEqual(s['diagnostics'],[]);self.assertEqual(s['omitted_diagnostics'],0)
        # Larger output through a supported separate fixture, without changing stored definitions.
        self.tearDown();self.setUp()
        c=self.start([[sys.executable,'-c',"print('PRIVATE_STDOUT\\n'*20000)"]])
        code,out2,err=self.call(c);self.assertEqual(code,0,err)
        self.assertEqual(len(out2.encode()),len(out.encode()));self.validate(json.loads(out2))

    def test_failure_codes_cap_overflow_and_no_raw_output(self):
        c=self.start([[sys.executable,'-c',"import sys;print('PRIVATE_timeout; process group terminated');print('PRIVATE_ERR',file=sys.stderr);sys.exit(3)"] for _ in range(5)])
        code,out,err=self.call(c);self.assertEqual(code,1,err);s=json.loads(out);self.validate(s)
        self.assertEqual(s['checks'],{'executed':5,'passed':0,'failed':5})
        self.assertEqual(s['diagnostics'],[{'check':i,'code':'check-nonzero'} for i in [1,2,3]])
        self.assertEqual(s['omitted_diagnostics'],2);self.assertNotIn('PRIVATE',out)

    def test_timeout_launch_and_unstable_are_distinct(self):
        c=self.start([[sys.executable,'-c','import time;time.sleep(3)'],['missing-PRIVATE-command']])
        code,out,err=self.call(c,timeout=1);self.assertEqual(code,1,err);s=json.loads(out);self.validate(s)
        self.assertEqual(s['diagnostics'],[{'check':1,'code':'check-timeout'},{'check':2,'code':'check-launch-failed'}])
        self.assertNotIn('PRIVATE',out)
        self.tearDown();self.setUp()
        c=self.start([[sys.executable,'-c',"from pathlib import Path;Path('a.txt').write_text('changed')"]])
        code,out,err=self.call(c);self.assertEqual(code,1,err);s=json.loads(out);self.validate(s)
        self.assertFalse(s['stable']);self.assertEqual(s['checks']['failed'],0)
        self.assertEqual(s['diagnostics'],[{'check':None,'code':'snapshot-unstable'}])

    def test_default_cli_and_public_api_receipt_unchanged(self):
        c=self.start([[sys.executable,'-c','print("actual result")']])
        r=self.w.verify('A',c['token'])
        self.assertEqual(set(r),{'task','at','snapshot','inputs','stable','results','passed'})
        self.assertEqual(set(r['results'][0]),{'argv','exit_code','stdout','stderr'})
        code,out,err=self.call(c,summary=False);self.assertEqual(code,0,err)
        self.assertEqual(set(json.loads(out)),set(r));self.assertIn('actual result',out)

    def test_summary_identity_survives_later_verification(self):
        c=self.start([[sys.executable,'-c','print("actual result")']])
        original=Workspace._verify
        def publish_then_race(w,*args,**kwargs):
            result=original(w,*args,**kwargs)
            if kwargs.get('summary'):original(w,*args)
            return result
        with patch.object(Workspace,'_verify',publish_then_race):code,out,err=self.call(c)
        self.assertEqual(code,0,err);s=json.loads(out);self.validate(s)
        with self.w.transaction() as con:latest=json.loads(con.execute('SELECT checks FROM tasks').fetchone()[0])
        self.assertNotEqual(latest['path'],s['receipt']['path'])
        self.assertNotEqual(latest['hash'],s['receipt']['hash'])

    def test_guard_refusal_and_publication_failure_never_show_old_pass(self):
        c=self.start([[sys.executable,'-c',"from pathlib import Path;import time;Path('.tequio/started').touch();time.sleep(.4)"]])
        self.w.verify('A',c['token']);(self.root/'.tequio/started').unlink()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future=pool.submit(self.w._verify,'A',c['token'],summary=True)
            until=time.monotonic()+5
            while not (self.root/'.tequio/started').exists() and time.monotonic()<until:time.sleep(.01)
            self.assertTrue((self.root/'.tequio/started').exists())
            code,out,err=self.call(c);self.assertEqual(code,2);self.assertEqual(out,'')
            self.assertTrue(future.result()['receipt']['passed'])
        from tequio import core
        original=core.write
        def fail_publication(path,value):
            if '/evidence/' in str(path):raise OSError('synthetic publication refused')
            return original(path,value)
        with self.w.transaction() as con:old=con.execute('SELECT checks FROM tasks').fetchone()[0]
        with patch('tequio.core.write',side_effect=fail_publication):code,out,err=self.call(c)
        self.assertEqual(code,2);self.assertEqual(out,'');self.assertIn('publication refused',err)
        with self.w.transaction() as con:self.assertEqual(con.execute('SELECT checks FROM tasks').fetchone()[0],old)
        wrong={**c,'token':'invalid-token'}
        code,out,err=self.call(wrong);self.assertEqual(code,2);self.assertEqual(out,'')
