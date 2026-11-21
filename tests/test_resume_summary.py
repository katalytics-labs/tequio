"""Compact delivery with real read-only state and checkpoint substitution races."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import test_lifecycle as fixtures
from tequio.run_context import compact_resume
from tequio import run_context


class ResumeSummary(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    def image(self):return {str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
    def observe(self):
        before=self.image();r=compact_resume(self.w);self.assertEqual(before,self.image());return r
    def test_schema_default_compatibility_privacy_and_size(self):
        self.add(self.task());self.w.checkpoint('PRIVATE_SUMMARY '*5000,'PRIVATE_NEXT '*5000)
        r=self.observe();self.assertEqual(set(r),{'schema_version','workspace','workflow','counts','changes','context','checkpoint','focus','active','execution_checkpoints','usage'})
        self.assertLess(len(json.dumps(r).encode()),8192);self.assertNotIn('PRIVATE',json.dumps(r));self.assertNotIn('task_ids',r['context']);self.assertNotIn('tasks',r)
        saved=(self.w.path/'checkpoint.json').read_bytes();import hashlib
        self.assertEqual(r['checkpoint']['reference']['hash'],hashlib.sha256(saved).hexdigest())
        full=self.w.resume();self.assertIn('PRIVATE_SUMMARY',full['checkpoint']['summary']);self.assertIn('tasks',full['current']);self.assertNotIn('schema_version',full)
    def test_missing_legacy_invalid_and_unsupported(self):
        self.assertEqual(self.observe()['checkpoint']['state'],'missing')
        saved=self.w.checkpoint('valid saved summary','next authorized bounded task')
        p=self.w.path/'checkpoint.json'
        for body,state in [(None,'invalid'),({'checkpoint_version':99},'invalid')]:
            p.write_text(json.dumps(body));self.assertEqual(self.observe()['checkpoint']['state'],state)
        p.write_text(json.dumps(saved|{'checkpoint_version':99}));self.assertEqual(self.observe()['checkpoint']['state'],'unsupported')
        legacy={k:v for k,v in saved.items() if k not in ('checkpoint_version','context')};p.write_text(json.dumps(legacy));r=self.observe();self.assertEqual(r['checkpoint']['state'],'legacy');self.assertTrue(r['changes']['context_unknown'])
    def test_same_read_identity_and_no_indirect_symlink_read(self):
        self.w.checkpoint('original checkpoint','continue only authorized work')
        p=self.w.path/'checkpoint.json';raw=p.read_bytes();original=run_context._checkpoint_bytes
        with tempfile.TemporaryDirectory() as d:
            external=Path(d)/'PRIVATE';external.write_text('PRIVATE_EXTERNAL')
            def acquire(w):
                result=original(w);p.unlink();p.symlink_to(external);return result
            read=Path.read_bytes
            def forbid(path):
                if path==p and path.is_symlink():raise AssertionError('indirect checkpoint read')
                return read(path)
            with patch.object(run_context,'_checkpoint_bytes',acquire),patch.object(Path,'read_bytes',forbid):r=compact_resume(self.w)
            import hashlib
            self.assertEqual(r['checkpoint']['reference']['hash'],hashlib.sha256(raw).hexdigest());self.assertNotIn('PRIVATE',json.dumps(r))
            r=compact_resume(self.w);self.assertEqual(r['checkpoint']['state'],'unavailable');self.assertIsNone(r['checkpoint']['reference'])
            p.unlink()
    def test_active_cap_unknowns_and_current_drift(self):
        with self.w.transaction() as con:
            config=json.loads(con.execute("SELECT value FROM meta WHERE key='config'").fetchone()[0]);config['max_parallel']=5;con.execute("UPDATE meta SET value=? WHERE key='config'",(json.dumps(config),))
        self.add(*[self.task('A'+str(i)) for i in range(4)])
        self.w.checkpoint('saved','continue only authorized work')
        for i in range(4):self.w.claim('owner'+str(i),'A'+str(i))
        r=self.observe();self.assertEqual(r['active']['count'],4);self.assertEqual(len(r['active']['items']),3);self.assertEqual(r['active']['omitted'],1);self.assertTrue(r['changes']['task_progress_changed']);self.assertLess(len(json.dumps(r)),8192)
    def test_cli_intake_default_refusal_and_existing_workspace(self):
        argv=[sys.executable,str(fixtures.ROOT/'bin/tequio'),'--project',str(self.root),'--workspace','fixture','resume']
        r=subprocess.run(argv+['--summary'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['schema_version'],1);self.assertEqual(set(json.loads(r.stdout)),set(compact_resume(self.w)));self.assertNotIn('git_isolation',json.loads(r.stdout));self.assertLess(len(r.stdout.encode()),8192)
        with tempfile.TemporaryDirectory() as d:
            argv=[sys.executable,str(fixtures.ROOT/'bin/tequio'),'--project',d,'resume']
            self.assertEqual(subprocess.run(argv,capture_output=True).returncode,2)
            r=subprocess.run(argv+['--summary'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['workflow']['stage'],'intake');self.assertEqual(list(Path(d).iterdir()),[])
    def test_projection_does_not_copy_malformed_enum_or_identifier(self):
        self.add(self.task());self.w.claim('writer')
        original=run_context._resume
        def malformed(w,checkpoint=None):
            r=original(w,checkpoint);r['current']['workflow']['next']['task']='PRIVATE/path';r['current']['workflow']['stage']='PRIVATE_STAGE';r['current']['workflow']['counts']={'PRIVATE_STATUS':1};return r
        with patch.object(run_context,'_resume',malformed):r=compact_resume(self.w)
        self.assertNotIn('PRIVATE',json.dumps(r));self.assertTrue(r['changes']['context_unknown']);self.assertIsNone(r['workflow']['next']['task'])

    def test_counts_only_and_clock_projection_are_unknown_without_raw_values(self):
        self.w.checkpoint('healthy saved context','continue authorized scope')
        original=run_context._resume
        def malformed(w,checkpoint=None):
            r=original(w,checkpoint);r['current']['workflow']['counts']={'PRIVATE_STATUS':1};return r
        with patch.object(run_context,'_resume',malformed):r=compact_resume(self.w)
        self.assertTrue(r['changes']['context_unknown']);self.assertNotIn('PRIVATE',json.dumps(r))
        def clock(w,checkpoint=None):
            r=original(w,checkpoint);r['current']['execution_checkpoints'].update(state='PRIVATE_STATE',clock='PRIVATE_CLOCK',extra='PRIVATE_EXTRA');return r
        with patch.object(run_context,'_resume',clock):r=compact_resume(self.w)
        self.assertTrue(r['changes']['context_unknown']);self.assertNotIn('PRIVATE',json.dumps(r));self.assertNotIn('extra',r['execution_checkpoints'])

    def test_workspace_parent_alias_is_not_followed(self):
        original=self.w.path;aside=original.with_name('original-aside');original.rename(aside)
        with tempfile.TemporaryDirectory() as d:
            outside=Path(d);(outside/'checkpoint.json').write_text('PRIVATE_EXTERNAL');original.symlink_to(outside,target_is_directory=True)
            try:
                with patch.object(self.w,'status',side_effect=AssertionError('must not inspect aliased current state')):
                    r=compact_resume(self.w)
                self.assertTrue(r['changes']['context_unknown']);self.assertIsNone(r['active']['count']);self.assertNotIn('PRIVATE',json.dumps(r));self.assertEqual(r['checkpoint']['state'],'unavailable')
            finally:original.unlink();aside.rename(original)

if __name__=='__main__':unittest.main()
