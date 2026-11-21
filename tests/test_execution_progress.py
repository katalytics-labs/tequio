"""Synthetic coordination fixtures and real CLI checks, not host-cost telemetry."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import test_lifecycle as fixtures
from tequio.cli import main
from tequio.core import Error
from tequio.execution_progress import progress
from tequio.run_context import policy


class ExecutionProgress(unittest.TestCase):
    setUp = fixtures.Lifecycle.setUp
    tearDown = fixtures.Lifecycle.tearDown
    task = fixtures.Lifecycle.task
    add = fixtures.Lifecycle.add

    def write_policy(self, limits=True):
        value = {'mode': 'next-chunk', 'scope': 'PRIVATE_SCOPE_SENTINEL', 'tasks': ['A'],
                 'integration_branch': None, 'allow_local_commits': False,
                 'allow_local_merges': False, 'allow_push': False, 'parallel_writers': 1,
                 'private_note': 'PRIVATE_NOTE_SENTINEL'}
        if limits is not False:
            value['execution_checkpoints'] = ({'version': 1, 'wall_minutes': 30,
                                               'max_verifications_per_task': 2} if limits is True else limits)
        self.p = self.w.path / 'run-policy.json'
        self.p.write_text(json.dumps(value))
        return value

    def image(self, root=None):
        root = root or self.root
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}

    def observe(self, task=None, **kwargs):
        before = self.image()
        result = progress(self.root, 'fixture', task, **kwargs)
        self.assertEqual(before, self.image(), 'Observation mutated project/state/evidence')
        return result

    def publish(self, kind, data):
        # Explicitly synthetic lifecycle-publication fixture; not actual independent review.
        with self.w.transaction() as con:
            self.w.event(con, kind, data)

    def call(self, root, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(['--project', str(root), '--workspace', 'fixture', *args])
        return code, out.getvalue(), err.getvalue()

    def test_legacy_missing_invalid_and_configured_policy(self):
        self.assertEqual(self.observe()['execution_checkpoints']['state'], 'policy-missing')
        self.write_policy(False)
        self.assertEqual(policy(self.w.path)['state'], 'valid')
        self.assertEqual(self.observe()['execution_checkpoints']['state'], 'legacy-unbudgeted')
        self.write_policy()
        result = self.observe()
        self.assertEqual(result['execution_checkpoints']['state'], 'configured')
        self.assertIsNone(result['execution_checkpoints']['elapsed_wall_seconds'])
        self.assertTrue(result['execution_checkpoints']['checkpoint_required'])
        self.assertEqual(result['usage'], {'tokens': None, 'cost': None, 'source': 'unavailable'})
        self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_strict_limits_and_private_invalid_values(self):
        good = {'version': 1, 'wall_minutes': 30, 'max_verifications_per_task': 2}
        bad = [None, [], {}, {**good, 'extra': 'SECRET_LIMIT_SENTINEL'}]
        for field in good:
            for value in [True, False, 0, -1, 1.5, '2', float('nan'), float('inf')]:
                bad.append({**good, field: value})
        bad.append({**good, 'version': 2})
        for value in bad:
            with self.subTest(value=value):
                self.write_policy(value)
                self.assertEqual(policy(self.w.path)['state'], 'invalid')
                result = self.observe()
                self.assertEqual(result['execution_checkpoints']['state'], 'policy-invalid')
                self.assertIsNone(result['execution_checkpoints']['limits'])
                self.assertNotIn('SECRET_LIMIT_SENTINEL', json.dumps(result))

    def test_counter_kinds_failed_publications_and_privacy(self):
        self.add(self.task())
        self.write_policy()
        self.w.checkpoint('PRIVATE_SUMMARY', 'PRIVATE_NEXT_ACTION')
        common = {'id': 'A', 'token': 'SECRET_TOKEN_SENTINEL', 'stdout': 'PRIVATE_STDOUT',
                  'findings': ['PRIVATE_FINDING'], 'actor': 'PRIVATE_ACTOR', 'receipt': {'path': 'missing-private-receipt'}}
        for passed in [False, True]:
            self.publish('verified', common | {'passed': passed})
        for kind in ['correctness', 'correctness', 'security']:
            self.publish('reviewed', common | {'kind': kind})
        self.publish('documentation-recorded', common)
        result = self.observe('A')
        item = result['tasks'][0]
        self.assertEqual(item['published_verifications'], 2)
        self.assertEqual(item['successful_verifications'], 1)
        self.assertEqual(item['correctness_reviews'], 2)
        self.assertEqual(item['security_reviews'], 1)
        self.assertEqual(item['documentation_records'], 1)
        self.assertEqual(result['recorded_done'], 0)
        self.assertIn({'reason': 'verification-checkpoint', 'task': 'A'}, result['execution_checkpoints']['reasons'])
        text = json.dumps(result)
        self.assertNotIn('SECRET_', text)
        self.assertNotIn('PRIVATE_', text)
        self.assertNotIn('missing-private-receipt', text)
        # Reporting a checkpoint must not erase accumulated verification history.
        self.w.checkpoint('checkpoint reported', 'assess before extending')
        self.assertEqual(self.observe('A')['tasks'][0]['published_verifications'], 2)

    def test_observed_wall_time_threshold_and_clock_unknowns(self):
        self.write_policy()
        saved = self.w.checkpoint('saved', 'continue')
        at = saved['at']
        self.assertFalse(self.observe(now=at + 1)['execution_checkpoints']['checkpoint_required'])
        self.assertIn({'reason': 'wall-time-checkpoint'}, self.observe(now=at + 1800)['execution_checkpoints']['reasons'])
        path = self.w.path / 'checkpoint.json'
        for content in ['{', 'null', json.dumps({'at': at}), json.dumps(saved | {'checkpoint_version': 99})]:
            path.write_text(content)
            result = self.observe(now=at + 1)
            self.assertIsNone(result['execution_checkpoints']['elapsed_wall_seconds'])
            self.assertTrue(result['execution_checkpoints']['checkpoint_required'])
        for value in [True, -1, float('nan'), float('inf'), 10 ** 500, at + 100]:
            path.write_text(json.dumps(saved | {'at': value}))
            self.assertEqual(self.observe(now=at + 1)['execution_checkpoints']['clock'], 'invalid-time')
        path.write_text(json.dumps(saved))
        value = json.loads(self.p.read_text()); value['private_note'] = 'CHANGED_PRIVATE'
        self.p.write_text(json.dumps(value))
        result = self.observe(now=at + 1)
        self.assertEqual(result['execution_checkpoints']['clock'], 'policy-drift')
        self.assertIsNone(result['execution_checkpoints']['elapsed_wall_seconds'])

    def test_policy_changed_between_reads_is_unknown_and_private(self):
        self.write_policy()
        original = policy(self.w.path)
        value = json.loads(self.p.read_text()); value['private_note'] = 'RACING_PRIVATE_SENTINEL'
        self.p.write_text(json.dumps(value))
        with mock.patch('tequio.execution_progress.policy', return_value=original):
            result = self.observe()
        self.assertEqual(result['execution_checkpoints']['state'], 'policy-changed-during-read')
        self.assertIsNone(result['execution_checkpoints']['limits'])
        self.assertNotIn('RACING_PRIVATE_SENTINEL', json.dumps(result))

    def test_corrupt_observed_events_never_imply_within_budget(self):
        self.add(self.task()); self.write_policy(); self.w.checkpoint('saved', 'continue')
        with self.w.transaction() as con:
            for raw in ['PRIVATE_INVALID_JSON', 'null', '[]', '{"id":"A","passed":"PRIVATE_BAD_VALUE"}']:
                con.execute('INSERT INTO events(at,kind,data) VALUES(0,?,?)', ('verified', raw))
        self.publish('reviewed', {'id': 'A', 'kind': 'PRIVATE_BAD_KIND'})
        result = self.observe('A')
        self.assertEqual(result['observation_issues'], 5)
        self.assertIn({'reason': 'observation-incomplete'}, result['execution_checkpoints']['reasons'])
        self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_real_failed_successful_checks_do_not_bypass_acceptance(self):
        t = self.task();t['writes'] = ['flag'];t['checks'] = [[sys.executable, '-c', "from pathlib import Path; assert Path('flag').is_file()"]]
        self.add(t);self.write_policy();claim = self.w.claim('writer')
        self.assertFalse(self.w.verify('A', claim['token'])['passed'])
        (self.root / 'flag').write_text('actual correction')
        self.assertTrue(self.w.verify('A', claim['token'])['passed'])
        result = self.observe('A')
        self.assertEqual(result['tasks'][0]['published_verifications'], 2)
        self.assertEqual(result['tasks'][0]['successful_verifications'], 1)
        with self.assertRaises(Error):
            self.w.complete('A', claim['token'], 'Counters are not acceptance evidence')
        (self.root / 'flag').write_text('changed after check')
        with self.assertRaises(Error):
            self.w.complete('A', claim['token'], 'Changed current content still refuses closure')

    def test_completed_tasks_do_not_raise_loop_warning(self):
        # Synthetic historical closure fixture tests presentation only, not forged acceptance.
        self.add(self.task());self.write_policy();self.w.checkpoint('saved', 'continue')
        for _ in range(3):self.publish('verified', {'id': 'A', 'passed': True})
        self.publish('completed', {'id': 'A', 'summary': 'PRIVATE_COMPLETION'})
        with self.w.transaction() as con:con.execute("UPDATE tasks SET status='done' WHERE id='A'")
        result = self.observe()
        self.assertEqual(result['recorded_done'], 1)
        self.assertEqual(result['tasks'][0]['completion_records'], 1)
        self.assertFalse(result['execution_checkpoints']['checkpoint_required'])
        self.assertNotIn('PRIVATE_', json.dumps(result))

    def test_unknown_task_and_no_workspace_are_read_only(self):
        before = self.image()
        with self.assertRaises(Error):progress(self.root, 'fixture', 'UNKNOWN')
        self.assertEqual(before, self.image())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);code, out, err = self.call(root, 'progress')
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)['workflow']['stage'], 'intake')
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_lane_routes_to_original_controller(self):
        from tequio.git_isolation import configure, create_lane
        self.add(self.task());self.write_policy()
        (self.root / '.gitignore').write_text('.tequio/\n')
        for argv in [['git','init','-q',str(self.root)],
                     ['git','-C',str(self.root),'config','user.email','synthetic@example.invalid'],
                     ['git','-C',str(self.root),'config','user.name','Synthetic fixture'],
                     ['git','-C',str(self.root),'add','brief.md','.gitignore'],
                     ['git','-C',str(self.root),'commit','-qm','Synthetic lane fixture']]:
            subprocess.run(argv,check=True,capture_output=True)
        configure(self.root, True)
        lane = Path(create_lane(self.root, 'observations')['path'])
        before = self.image();lane_before = self.image(lane)
        code, out, err = self.call(lane, 'progress', 'A')
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)['tasks'][0]['task'], 'A')
        self.assertEqual(self.image(), before);self.assertEqual(self.image(lane), lane_before)
        self.assertFalse((lane / '.tequio/workspaces').exists())
        code,out,err=self.call(lane,'status')
        self.assertEqual(code,0,err);observed=json.loads(out)
        self.assertEqual(observed['execution_checkpoints']['state'],'configured')
        self.assertEqual(observed['workspace'],str(self.w.path))
        self.assertEqual(self.image(),before);self.assertEqual(self.image(lane),lane_before)


    def test_status_reuses_progress_without_changing_readiness_or_bytes(self):
        self.add(self.task()); self.write_policy()
        self.w.checkpoint('saved', 'continue')
        at=json.loads((self.w.path/'checkpoint.json').read_text())['at']
        for now,due in [(at+1,False),(at+1801,True)]:
            before=self.image()
            with mock.patch('tequio.execution_progress.time.time',return_value=now):
                full=progress(self.root,'fixture');status=self.w.status()
            for key in ('execution_checkpoints','usage'):self.assertEqual(status[key],full[key])
            self.assertEqual(status['execution_checkpoints']['checkpoint_required'],due)
            self.assertTrue(status['tasks'][0]['dispatchable'])
            self.assertEqual(status['workflow']['next']['skill'],'tequio-build')
            self.assertNotIn('published_verifications',json.dumps(status))
            self.assertNotIn('PRIVATE_',json.dumps(status))
            self.assertEqual(before,self.image())

    def test_status_missing_legacy_invalid_clock_and_counter_observations(self):
        self.assertEqual(self.w.status()['execution_checkpoints']['state'],'policy-missing')
        self.write_policy(False)
        self.assertEqual(self.w.status()['execution_checkpoints']['state'],'legacy-unbudgeted')
        self.p.write_text('null')
        self.assertEqual(self.w.status()['execution_checkpoints']['state'],'policy-invalid')
        self.write_policy();self.w.checkpoint('saved','continue')
        (self.w.path/'checkpoint.json').write_text('null')
        self.assertEqual(self.w.status()['execution_checkpoints']['clock'],'unusable')
        with self.w.transaction() as con:con.execute("INSERT INTO events(at,kind,data) VALUES(0,'verified','PRIVATE_INVALID')")
        self.assertIn({'reason':'observation-incomplete'},self.w.status()['execution_checkpoints']['reasons'])
        for exc in [OSError('PRIVATE_ERROR'), ValueError('PRIVATE_ERROR'), KeyError('PRIVATE_ERROR')]:
            before=self.image()
            with mock.patch('tequio.execution_progress.progress',side_effect=exc):status=self.w.status()
            self.assertEqual(status['execution_checkpoints'],{
                'state':'unavailable','limits':None,'clock':'unavailable','elapsed_wall_seconds':None,
                'checkpoint_required':True,'reasons':[{'reason':'observation-incomplete'}]})
            self.assertEqual(status['usage'],{'tokens':None,'cost':None,'source':'unavailable'})
            self.assertNotIn('PRIVATE_',json.dumps(status));self.assertEqual(before,self.image())


if __name__ == '__main__':
    unittest.main()
