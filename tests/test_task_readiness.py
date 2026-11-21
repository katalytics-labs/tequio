"""Synthetic readiness mechanics, not proof of agent discovery or review behavior."""
import copy
import json
import unittest
import test_lifecycle as fixtures
from task_review_fixtures import synthetic_draft, reviewed_import
from tequio.core import Error
from tequio.task_review import TaskReview, DRAFT_CATEGORIES


class ReadinessTests(unittest.TestCase):
    setUp = fixtures.Lifecycle.setUp
    tearDown = fixtures.Lifecycle.tearDown
    task = fixtures.Lifecycle.task
    add = fixtures.Lifecycle.add
    finish = fixtures.Lifecycle.finish
    docs = fixtures.Lifecycle.docs
    report = fixtures.Lifecycle.report

    def prepare(self, tasks):
        self.path = self.w.path / 'tasks/proposal.json'
        self.path.write_text(json.dumps(tasks))
        return TaskReview(self.w).prepare(self.path, 'synthetic-task-author')

    def test_reject_missing_and_malformed_decisions(self):
        base = synthetic_draft(self.task())
        variants = [None, [], {}, {**base['draft'], 'extra': True}]
        for key, value in [('version', True), ('version', 2), ('category', []),
                           ('category', 'dependency-wait'), ('category', 'later-wave'),
                           ('category', 'routine-choice'), ('reason', ' thin '),
                           ('next_action', None), ('source', 'plans/delivery.md#uncited')]:
            variants.append({**base['draft'], key: value})
        for decision in variants:
            with self.subTest(decision=decision):
                task = copy.deepcopy(base); task['draft'] = decision
                with self.assertRaises(Error): self.prepare([task])
                with self.w.transaction() as con, self.assertRaises(Error):
                    TaskReview(self.w).require_import(con, [task])

    def test_categories_and_safe_summary(self):
        for category in DRAFT_CATEGORIES:
            t = synthetic_draft(self.task()); t['draft']['category'] = category
            if category == 'missing-specialist-qualification': t['specialists'] = ['fixture-specialist']
            result = self.prepare([t])
            self.assertEqual(result['readiness'], {'ready': 0, 'draft': 1,
                             'drafts': [{'id': 'A', 'category': category}]})
            for field in ('reason', 'next_action', 'source'):
                self.assertNotIn(t['draft'][field], json.dumps(result))
        t = synthetic_draft(self.task()); t['draft']['category'] = 'missing-specialist-qualification'
        with self.assertRaisesRegex(Error, 'named specialists'): self.prepare([t])
        del t['specialists']
        with self.assertRaisesRegex(Error, 'named specialists'): self.prepare([t])

    def test_pending_legacy_record_cannot_bypass_new_validation(self):
        t = self.task(); result = self.prepare([t]); batch = result['batch']
        # Synthetic pre-contract pending record, not alteration of a live controller.
        with self.w.transaction() as con:
            key = 'task-batch:' + batch
            record = json.loads(con.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()[0])
            record['tasks'][0]['stage'] = 'draft'
            con.execute('UPDATE meta SET value=? WHERE key=?', (json.dumps(record), key))
            with self.assertRaisesRegex(Error, 'Draft requires'):
                TaskReview(self.w)._record(con, batch)

    def test_legacy_imported_draft_unchanged_and_not_promoted(self):
        t = synthetic_draft(self.task()); self.prepare([t]); reviewed_import(self.w, self.path)
        # Represent already imported pre-contract history in an isolated fixture.
        del t['draft']; body = json.dumps(t)
        with self.w.transaction() as con:
            con.execute('UPDATE tasks SET body=? WHERE id=?', (body, 'A'))
        self.w.status()
        with self.assertRaises(Error): self.w.claim('writer', 'A')
        with self.w.transaction() as con:
            row = con.execute('SELECT body,status FROM tasks WHERE id=?', ('A',)).fetchone()
            self.assertEqual(tuple(row), (body, 'draft'))

    def test_ready_dependency_waits_without_becoming_draft(self):
        a = self.task('A'); b = self.task('B', depends=['A']); b['stage'] = 'ready'
        result = self.prepare([a, b]); self.assertEqual(result['readiness']['ready'], 2)
        reviewed_import(self.w, self.path)
        tasks = {t['id']: t for t in self.w.status()['tasks']}
        self.assertEqual(tasks['B']['status'], 'ready'); self.assertFalse(tasks['B']['dispatchable'])
        with self.assertRaises(Error): self.w.claim('consumer', 'B')
        self.finish(self.w.claim('producer', 'A'))
        self.assertEqual(self.w.claim('consumer', 'B')['id'], 'B')

    def test_source_change_invalidates_draft_review(self):
        t = synthetic_draft(self.task()); self.prepare([t]); reviewed_import(self.w, self.path)
        source = self.w.path / t['draft']['source']; source.write_text(source.read_text() + '\nChanged decision.')
        self.assertEqual(TaskReview(self.w).status(self.path)['state'], 'review-required')
