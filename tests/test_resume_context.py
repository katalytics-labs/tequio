import contextlib
import copy
import json
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path
from test_lifecycle import Lifecycle, ROOT


class ResumeContext(unittest.TestCase):
    setUp = Lifecycle.setUp
    tearDown = Lifecycle.tearDown
    task = Lifecycle.task
    add = Lifecycle.add
    # Reuse fixture helpers, not the lifecycle test methods.
    def policy(self):
        value = {'mode': 'next-chunk', 'scope': 'private scope prose', 'tasks': ['A'],
                 'integration_branch': None, 'allow_local_commits': False,
                 'allow_local_merges': False, 'allow_push': False, 'parallel_writers': 1,
                 'note': 'private secret note'}
        return value

    def prepare(self):
        self.add(self.task())
        self.p = self.w.path / 'run-policy.json'
        self.p.write_text(json.dumps(self.policy()))
        self.w.checkpoint('saved', 'continue')

    def image(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def unchanged_read(self):
        before = self.image()
        result = self.w.resume()
        self.assertEqual(before, self.image())
        return result

    def test_unchanged_and_private(self):
        self.prepare()
        r = self.unchanged_read()
        self.assertFalse(r['policy_changed']); self.assertFalse(r['task_scope_changed'])
        self.assertFalse(r['context_unknown']); self.assertFalse(r['task_progress_changed'])
        self.assertNotIn('private secret note', json.dumps(r))
        self.assertNotIn('private scope prose', json.dumps(r))

    def test_policy_changes(self):
        self.prepare()
        for key, value in [('mode', 'backlog'), ('tasks', ['A', 'B']), ('scope', 'revised private prose'),
                           ('allow_local_commits', True), ('allow_local_merges', True), ('allow_push', True),
                           ('parallel_writers', 2), ('integration_branch', 'main'), ('note', 'changed')]:
            with self.subTest(key=key):
                policy = self.policy(); policy[key] = value
                self.p.write_text(json.dumps(policy))
                r = self.unchanged_read()
                self.assertTrue(r['policy_changed']); self.assertFalse(r['task_scope_changed'])

    def test_formatting_noise(self):
        self.prepare(); self.p.write_text(json.dumps(self.policy(), indent=4, sort_keys=True))
        self.assertFalse(self.unchanged_read()['policy_changed'])

    def test_missing_invalid_policy(self):
        self.prepare()
        for content, state in [(None, 'missing'), ('null', 'invalid'), ('{', 'invalid'), ('{}', 'invalid')]:
            if content is None: self.p.unlink()
            else: self.p.write_text(content)
            r = self.unchanged_read()
            self.assertTrue(r['policy_changed']); self.assertEqual(r['context']['policy']['state'], state)

    def test_missing_policy_unchanged(self):
        self.prepare(); self.p.unlink(); self.w.checkpoint('saved', 'continue')
        self.assertFalse(self.unchanged_read()['policy_changed'])

    def test_task_import(self):
        self.prepare(); self.add(self.task('B'))
        self.assertTrue(self.unchanged_read()['task_scope_changed'])

    def test_task_definition_fields(self):
        self.prepare()
        with contextlib.closing(sqlite3.connect(self.w.path / 'state.sqlite3')) as con:
            body = json.loads(con.execute("SELECT body FROM tasks WHERE id='A'").fetchone()[0])
        for key, value in [('scope', 'changed'), ('acceptance', ['changed']), ('checks', [[sys.executable, '-V']]), ('exclusions', 'changed')]:
            changed = copy.deepcopy(body); changed[key] = value
            with contextlib.closing(sqlite3.connect(self.w.path / 'state.sqlite3')) as con:
                con.execute("UPDATE tasks SET body=? WHERE id='A'", (json.dumps(changed),))
                con.commit()
            self.assertTrue(self.unchanged_read()['task_scope_changed'])

    def test_progress_does_not_change_scope(self):
        self.prepare(); before = self.w.resume()['context']
        claim = self.w.claim('actual-writer', 'A')
        self.w.heartbeat('A', claim['token'])
        after = self.unchanged_read()
        self.assertFalse(after['task_scope_changed']); self.assertTrue(after['task_progress_changed'])
        self.assertNotEqual(before['progress_digest'], after['context']['progress_digest'])

    def test_runtime_fields_do_not_change_scope(self):
        self.prepare()
        from tequio.freshness import RUNTIME_FIELDS
        with contextlib.closing(sqlite3.connect(self.w.path / 'state.sqlite3')) as con:
            body = json.loads(con.execute("SELECT body FROM tasks WHERE id='A'").fetchone()[0])
            for key in RUNTIME_FIELDS - {'inputs', 'specialist_bindings'}: body[key] = 'runtime observation'
            con.execute("UPDATE tasks SET body=? WHERE id='A'", (json.dumps(body),))
            con.commit()
        self.assertFalse(self.unchanged_read()['task_scope_changed'])

    def test_corrupt_checkpoints_cli_readonly(self):
        self.prepare(); cp = self.w.path / 'checkpoint.json'
        good = json.loads(cp.read_text())
        missing = dict(good); del missing['summary']
        version = dict(good, checkpoint_version=99)
        context = dict(good, context={})
        for content in ['{', 'null', '[]', '{}', json.dumps(missing), json.dumps(version), json.dumps(context)]:
            with self.subTest(content=content):
                cp.write_text(content); before = self.image()
                proc = subprocess.run([sys.executable, str(ROOT / 'bin/tequio'), '--project', str(self.root), '--workspace', 'fixture', 'resume'], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                r = json.loads(proc.stdout)
                self.assertEqual(r['current']['tasks'][0]['id'], 'A')
                self.assertTrue(r['context_unknown']); self.assertIsNone(r['project_changed'])
                self.assertIsNone(r['inputs_changed']); self.assertIsNone(r['policy_changed']); self.assertIsNone(r['task_scope_changed']); self.assertIsNone(r['task_progress_changed'])
                self.assertIsNotNone(r['checkpoint_issue']); self.assertEqual(before, self.image())

    def test_legacy(self):
        self.prepare(); cp = self.w.path / 'checkpoint.json'; data = json.loads(cp.read_text())
        del data['checkpoint_version']; del data['context']; cp.write_text(json.dumps(data))
        r = self.unchanged_read()
        self.assertTrue(r['context_unknown']); self.assertIsNone(r['policy_changed']); self.assertIsNone(r['task_progress_changed'])
        self.assertFalse(r['project_changed']); self.assertFalse(r['inputs_changed'])
        self.assertEqual(r['checkpoint_issue']['code'], 'legacy-context-unknown')

    def test_absent_checkpoint(self):
        before = self.image(); r = self.w.resume()
        self.assertEqual(before, self.image()); self.assertTrue(r['context_unknown'])
        self.assertEqual(r['checkpoint_issue']['code'], 'missing')


del Lifecycle
