"""Real local-process recovery regressions; every killed process belongs to a fixture."""
import concurrent.futures
import contextlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time
from unittest import mock
import unittest

import test_lifecycle
from tequio.core import Error, Workspace, tree_hash
from tequio.verification import paths, save


class VerificationRecovery(unittest.TestCase):
    setUp = test_lifecycle.Lifecycle.setUp
    tearDown = test_lifecycle.Lifecycle.tearDown
    task = test_lifecycle.Lifecycle.task
    add = test_lifecycle.Lifecycle.add
    def expire(self):
        with contextlib.closing(sqlite3.connect(self.w.path / 'state.sqlite3')) as con:
            con.execute('UPDATE tasks SET lease=?', (time.time()-1,)); con.commit()

    def start_task(self, code):
        task = self.task()
        task['checks'] = [[sys.executable, '-c', code]]
        self.add(task)
        return self.w.claim('writer')

    def wait_file(self, path):
        until = time.monotonic()+8
        while time.monotonic() < until:
            if path.exists(): return
            time.sleep(.02)
        self.fail('fixture did not start')

    def legacy_released(self):
        claim = self.start_task('print("fixture")')
        self.w.release('A', claim['token'], 'Inspected fixture worker; all activity stopped.')
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET owner='legacy-fixture-worker' WHERE id='A'")
        return claim

    def row(self):
        with self.w.transaction() as con:
            return dict(con.execute("SELECT * FROM tasks WHERE id='A'").fetchone())

    def test_ready_normalization_requires_exact_legacy_release_shape(self):
        self.legacy_released(); baseline = self.row()
        for field, value in [('owner', None), ('owner', ''), ('token', 'active-token'),
                             ('lease', 0), ('lease', time.time()+60),
                             ('checks', '{}'), ('reviews', '{}')]:
            with self.subTest(field=field, value=value):
                with self.w.transaction() as con:
                    con.execute('UPDATE tasks SET ' + field + '=? WHERE id=?', (value, 'A'))
                before = self.row()
                with self.assertRaises(Error):
                    self.w.recover('A', 'Inspected fixture processes; no worker remains.', True)
                self.assertEqual(before, self.row())
                with self.w.transaction() as con:
                    con.execute('UPDATE tasks SET ' + field + '=? WHERE id=?', (baseline[field], 'A'))
        with self.assertRaises(Error): self.w.recover('A', ' ')
        self.assertEqual(baseline, self.row())

    def test_ready_normalization_refuses_unknown_even_with_stopped_ack(self):
        self.legacy_released(); _, metadata = paths(self.w, 'A')
        for content in [json.dumps({'version':1, 'state':'launching', 'attempt':'fixture'}), '{broken']:
            with self.subTest(content=content):
                metadata.write_text(content); before = self.row(); original = metadata.read_bytes()
                for ack in [False, True]:
                    with self.assertRaises(Error):
                        self.w.recover('A', 'Inspected fixture handles; no process observed.', ack)
                    self.assertEqual(before, self.row())
                    self.assertEqual(original, metadata.read_bytes())

    def test_ready_normalization_refuses_held_or_live_then_known_absent(self):
        import fcntl
        self.legacy_released(); lock, metadata = paths(self.w, 'A'); before = self.row()
        with lock.open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                with self.assertRaises(Error): self.w.recover('A', 'Inspected fixture operation still held.', True)
                self.assertEqual(before, self.row())
            finally: fcntl.flock(handle, fcntl.LOCK_UN)
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'], start_new_session=True)
        try:
            save(metadata, {'version':1, 'state':'running', 'attempt':'fixture', 'process_group':child.pid})
            original = metadata.read_bytes()
            with self.assertRaises(Error): self.w.recover('A', 'Inspected fixture child still running.', True)
            self.assertEqual(before, self.row()); self.assertEqual(original, metadata.read_bytes())
        finally:
            child.kill(); child.wait(timeout=5)
        self.w.recover('A', 'Inspected fixture child group is now absent.')
        self.assertIsNone(self.row()['owner'])
        self.assertEqual(json.loads(metadata.read_text())['state'], 'reconciled')

    def test_live_expired_duplicate_release_and_recovery(self):
        c = self.start_task("import pathlib,time;pathlib.Path('.tequio/started').touch();time.sleep(.7)")
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(self.w.verify, 'A', c['token'])
            self.wait_file(self.root / '.tequio/started')
            self.expire()
            state = self.w.status()['tasks'][0]['verification']
            self.assertTrue(state['lock_held'])
            self.assertTrue(state['observed_group_live'])
            for action in (lambda:self.w.verify('A', c['token']),
                           lambda:self.w.release('A', c['token'], 'still checking'),
                           lambda:self.w.recover('A', 'Inspected fixture; still running', True),
                           lambda:self.w.claim('replacement', 'A')):
                with self.assertRaises(Error): action()
            self.assertTrue(future.result()['passed'])
        self.assertEqual(self.w.verification_status('A')['attempt']['state'], 'completed')

    def test_complete_and_acceptance_mutations_refused_during_reverify(self):
        c = self.start_task("import pathlib,time;p=pathlib.Path('.tequio/reverify');p.touch() if p.exists() else None;time.sleep(.5) if p.exists() else None")
        self.assertTrue(self.w.verify('A', c['token'])['passed'])
        test_lifecycle.Lifecycle.docs(self, c)
        report = test_lifecycle.Lifecycle.report(self)
        self.w.review('A', c['token'], 'reviewer', 'correctness', report, [])
        # A stopped child is not proof that its result was accepted before a caller crash.
        _, metadata = paths(self.w, 'A')
        accepted = metadata.read_bytes()
        attempt = json.loads(accepted); attempt['state'] = 'stopped'; save(metadata, attempt)
        with self.assertRaisesRegex(Error, 'Unresolved verification result'):
            self.w.complete('A', c['token'], 'cannot use old accepted check')
        metadata.write_bytes(accepted)
        (self.root/'.tequio/reverify').touch()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(self.w.verify, 'A', c['token'])
            until = time.monotonic()+5
            while not self.w.verification_status('A')['lock_held'] and time.monotonic()<until:
                time.sleep(.01)
            with self.assertRaisesRegex(Error, 'operation active'):
                self.w.complete('A', c['token'], 'must not close old evidence')
            with self.assertRaisesRegex(Error, 'operation active'):
                self.w.review('A', c['token'], 'reviewer', 'correctness', report, [])
            self.assertTrue(future.result()['passed'])

    def test_stale_heartbeat_expired_owner_and_token_fencing(self):
        c = self.start_task('print("ok")')
        (self.w.path/'plans/delivery.md').write_text('Changed')
        self.expire()
        result = self.w.heartbeat('A', c['token'])
        self.assertFalse(result['execution_eligible'])
        with self.assertRaises(Error): self.w.verify('A', c['token'])
        with self.assertRaises(Error): self.w.complete('A', c['token'], 'not allowed')
        self.w.release('A', c['token'], 'reconcile drift')
        with self.assertRaises(Error): self.w.heartbeat('A', c['token'])

    def test_old_token_cannot_attach_after_corrupt_owner_change(self):
        c = self.start_task('print("ok")')
        original = self.w.heartbeat
        def lose(tid, token):
            with contextlib.closing(sqlite3.connect(self.w.path/'state.sqlite3')) as con:
                con.execute('UPDATE tasks SET token=?', ('replacement-token',)); con.commit()
            return original(tid, token)
        with mock.patch.object(self.w, 'heartbeat', side_effect=lose):
            with self.assertRaises(Error): self.w.verify('A', c['token'])
        with contextlib.closing(sqlite3.connect(self.w.path/'state.sqlite3')) as con:
            self.assertIsNone(con.execute('SELECT checks FROM tasks').fetchone()[0])
        self.assertEqual(list((self.w.path/'evidence').iterdir()), [])

    def test_unknown_launch_ack_and_readonly_status(self):
        c = self.start_task('print("ok")')
        before = tree_hash(self.root)
        self.w.status(); self.w.verification_status('A')
        self.assertEqual(before, tree_hash(self.root))
        lock, metadata = paths(self.w, 'A'); lock.parent.mkdir(exist_ok=True)
        save(metadata, {'version':1, 'state':'launching', 'attempt':'fixture'})
        original = metadata.read_bytes()
        for action in (lambda:self.w.verify('A', 'invalid'),
                       lambda:self.w.release('A', 'invalid', 'inspect'),
                       lambda:self.w.recover('A', 'Inspected fixture; no child launched', True)):
            with self.assertRaises(Error): action()
            self.assertEqual(metadata.read_bytes(), original)
        self.expire()
        with self.assertRaises(Error): self.w.recover('A', 'Inspected unknown launch state')
        with self.assertRaises(Error): self.w.recover('A', 'short', True)
        self.w.recover('A', 'Inspected fixture handles; no child launched', True)
        c2 = self.w.claim('replacement')
        with self.assertRaises(Error): self.w.verify('A', c['token'])
        self.assertTrue(self.w.verify('A', c2['token'])['passed'])

    def test_recovery_persistence_failures_preserve_recoverability(self):
        self.start_task('print("ok")')
        lock, metadata = paths(self.w, 'A')
        save(metadata, {'version':1, 'state':'launching', 'attempt':'fixture'})
        original = metadata.read_bytes()
        self.expire()
        reason = 'Inspected fixture handles; no child launched'
        with mock.patch('tequio.verification.save', side_effect=OSError('fixture disk failure')):
            with self.assertRaises(OSError): self.w.recover('A', reason, True)
        self.assertEqual(metadata.read_bytes(), original)
        with contextlib.closing(sqlite3.connect(self.w.path/'state.sqlite3')) as con:
            self.assertEqual(con.execute('SELECT status FROM tasks').fetchone()[0], 'running')
        # Fail the transaction after UPDATE, forcing rollback after the stopped observation saved.
        with mock.patch.object(self.w, 'event', side_effect=sqlite3.OperationalError('fixture DB failure')):
            with self.assertRaises(sqlite3.OperationalError): self.w.recover('A', reason, True)
        self.assertEqual(json.loads(metadata.read_text())['state'], 'reconciled')
        with contextlib.closing(sqlite3.connect(self.w.path/'state.sqlite3')) as con:
            self.assertEqual(con.execute('SELECT status FROM tasks').fetchone()[0], 'running')
        self.w.recover('A', reason)
        self.assertEqual(self.w.claim('replacement')['id'], 'A')

    def test_metadata_read_failure_reports_unknown(self):
        self.start_task('print("ok")')
        lock, metadata = paths(self.w, 'A')
        save(metadata, {'version':1, 'state':'launching', 'attempt':'fixture'})
        original = Path.read_text
        def fail_metadata(path, *args, **kwargs):
            if path == metadata: raise PermissionError('fixture read denied')
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, 'read_text', fail_metadata):
            state = self.w.verification_status('A')
            self.assertEqual(state['attempt']['state'], 'unknown')
            self.assertEqual(self.w.status()['tasks'][0]['verification']['attempt']['state'], 'unknown')
            with self.assertRaises(Error): self.w.recover('A', 'Inspect unknown attempt')
        metadata.write_text('{broken')
        self.expire()
        self.w.recover('A', 'Inspected fixture handles; unknown attempt stopped', True)
        self.assertEqual(self.w.verification_status('A')['attempt']['state'], 'reconciled')

    def test_crashed_controller_child_live_then_absent(self):
        c = self.start_task("import pathlib,time;pathlib.Path('.tequio/started').touch();time.sleep(60)")
        code = "from tequio.core import Workspace;import sys;Workspace(sys.argv[1],'fixture').verify('A',sys.argv[2])"
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
        parent = subprocess.Popen([sys.executable, '-c', code, str(self.root), c['token']], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        group = None
        try:
            self.wait_file(self.root/'.tequio/started')
            group = self.w.verification_status('A')['attempt']['process_group']
            parent.kill(); parent.wait(timeout=5)
            self.expire()
            self.assertFalse(self.w.verification_status('A')['lock_held'])
            self.assertTrue(self.w.verification_status('A')['observed_group_live'])
            for ack in (False, True):
                with self.assertRaises(Error): self.w.recover('A', 'Inspected fixture live child', ack)
            os.killpg(group, signal.SIGKILL)
            # macOS reaps orphaned fixture children; other hosts may retain zombies.
            until = time.monotonic()+5
            while self.w.verification_status('A')['observed_group_live'] and time.monotonic()<until:
                time.sleep(.02)
            self.assertFalse(self.w.verification_status('A')['observed_group_live'])
            self.w.recover('A', 'Observed fixture child group absent')
            self.assertEqual(self.w.verification_status('A')['attempt']['state'], 'reconciled')
        finally:
            if parent.poll() is None: parent.kill(); parent.wait()
            if group:
                try: os.killpg(group, signal.SIGKILL)
                except ProcessLookupError: pass

    def test_timeout_spawn_error_and_interrupt_cleanup(self):
        c = self.start_task('import time;time.sleep(60)')
        self.assertFalse(self.w.verify('A', c['token'], timeout=1)['passed'])
        self.assertFalse(self.w.verification_status('A')['observed_group_live'])
        with mock.patch('tequio.core.subprocess.Popen', side_effect=FileNotFoundError('fixture missing')):
            self.assertFalse(self.w.verify('A', c['token'])['passed'])
        with mock.patch('tequio.core.subprocess.Popen', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): self.w.verify('A', c['token'])
        self.assertEqual(self.w.verification_status('A')['attempt']['state'], 'launching')
        with self.assertRaises(Error): self.w.release('A', c['token'], 'needs inspection')

