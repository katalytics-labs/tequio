"""Synthetic revision mechanics; fixture actors do not claim real independence."""
import json
import fcntl
import subprocess
import sys
import unittest
from unittest.mock import patch
import test_lifecycle as lifecycle
from tequio.core import Error
from tequio.revision import Revision, dependencies, expected_inputs
from tequio.task_review import AREAS


class RevisionTests(unittest.TestCase):
    setUp = lifecycle.Lifecycle.setUp
    tearDown = lifecycle.Lifecycle.tearDown
    task = lifecycle.Lifecycle.task
    add = lifecycle.Lifecycle.add
    docs = lifecycle.Lifecycle.docs
    finish = lifecycle.Lifecycle.finish
    report = lifecycle.Lifecycle.report

    def proposal(self, **changes):
        self.add(self.task('A'), self.task('B', depends=['A']), self.task('C', depends=['B']), self.task('X'))
        proposal = {'version': 1, 'reason': 'Split synthetic producer into explicit independent prerequisites.', 'supersede': ['A'],
                    'replacements': {'A': ['A1', 'A2']}, 'tasks': [self.task('A1'), self.task('A2')],
                    'rebindings': [{'consumer': 'B', 'from': ['A'], 'to': ['A1', 'A2']}]}
        proposal.update(changes)
        self.rel = 'tasks/revision.json'; (self.w.path / self.rel).write_text(json.dumps(proposal))
        self.engine = Revision(self.w)
        return proposal

    def accept(self):
        self.rid = self.engine.prepare(self.rel, 'synthetic-author')['revision']
        for kind in AREAS:
            rel = 'reviews/revision-' + kind + '.json'
            body = {'operation': 'revision', 'revision': self.rid,
                    'summary': 'Synthetic fixture verifies explicit declarations and failure paths in an isolated temporary workspace; it does not assert live independent human review.',
                    'coverage': {a: 'Synthetic test coverage binds declarations and current evidence for ' + a for a in AREAS[kind]}, 'findings': []}
            (self.w.path / rel).write_text(json.dumps(body))
            self.engine.review(self.rid, 'synthetic-' + kind, kind, rel)

    def rows(self):
        with self.w.transaction() as con:
            return {r['id']: dict(r) for r in con.execute('SELECT * FROM tasks')}

    def test_split_preserves_body_history_and_requires_new_evidence(self):
        self.proposal(); before = self.rows(); self.accept()
        result = self.engine.apply(self.rid)
        self.assertEqual(result['rebound'], ['B'])
        after = self.rows()
        for tid in ('A', 'B', 'C', 'X'):
            self.assertEqual(before[tid]['body'], after[tid]['body'])
        b = json.loads(after['B']['body'])
        self.assertEqual(dependencies(self.w, b), ['A1', 'A2'])
        self.assertNotEqual(expected_inputs(self.w, b), b['inputs'])
        with self.assertRaises(Error): self.w.claim('synthetic-worker', 'B')
        self.finish(self.w.claim('synthetic-worker', 'A1'))
        self.finish(self.w.claim('synthetic-worker', 'A2'))
        self.finish(self.w.claim('synthetic-worker', 'B'))
        self.finish(self.w.claim('synthetic-worker', 'C'))
        self.assertTrue(self.engine.apply(self.rid)['already_applied'])
        self.assertEqual(self.engine.status(self.rid)['state'], 'applied')

    def test_read_only_preview_and_status_do_not_change_database_or_files(self):
        self.proposal()
        files = {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()}
        view = self.engine.preview(self.rel)
        self.assertEqual(view['affected_unfinished'], ['A', 'B', 'C'])
        self.assertEqual(view['unaffected'], ['X'])
        self.assertNotIn('token', json.dumps(view))
        self.assertEqual(files, {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()})
        self.accept()
        files = {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()}
        self.assertEqual(self.engine.status(self.rid)['state'], 'reviewed')
        self.assertEqual(files, {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()})

    def test_atomic_failure_then_retry(self):
        self.proposal(); self.accept(); before = self.rows()
        original = self.w.event
        def fail(con, kind, data):
            if kind == 'revision-applied':
                self.assertEqual(con.execute("SELECT status FROM tasks WHERE id='A'").fetchone()[0], 'superseded')
                self.assertTrue(con.execute("SELECT 1 FROM tasks WHERE id='A1'").fetchone())
                raise RuntimeError('Synthetic injected failure after supersession and before commit')
            return original(con, kind, data)
        with patch.object(self.w, 'event', fail):
            with self.assertRaises(RuntimeError): self.engine.apply(self.rid)
        self.assertEqual(before, self.rows())
        self.assertEqual(self.engine.status(self.rid)['state'], 'reviewed')
        self.engine.apply(self.rid)

    def test_active_affected_descendant_blocks_but_unrelated_claim_survives(self):
        self.proposal(); self.accept()
        self.w.claim('synthetic-other', 'X')
        with self.assertRaisesRegex(Error, 'stale'): self.engine.apply(self.rid)
        self.accept(); self.engine.apply(self.rid)
        self.assertEqual(self.rows()['X']['owner'], 'synthetic-other')

    def test_proposal_report_and_context_drift_refuse(self):
        self.proposal(); self.accept()
        path = self.w.path / 'reviews/revision-correctness.json'; path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(Error, 'changed'): self.engine.apply(self.rid)
        self.assertEqual(self.rows()['A']['status'], 'ready')

    def test_strict_graph_rejects_missing_rebinding_and_cycles(self):
        self.proposal(rebindings=[])
        with self.assertRaisesRegex(Error, 'incoming edge'): self.engine.preview(self.rel)
        p = json.loads((self.w.path / self.rel).read_text())
        p['rebindings'] = [{'consumer': 'B', 'from': ['A'], 'to': ['C']}]
        (self.w.path / self.rel).write_text(json.dumps(p))
        with self.assertRaisesRegex(Error, 'cycle'): self.engine.preview(self.rel)

    def test_rebind_only_and_duplicate_keys(self):
        self.proposal(supersede=[], replacements={}, tasks=[], rebindings=[{'consumer': 'B', 'from': ['A'], 'to': ['X']}])
        self.accept(); self.engine.apply(self.rid)
        self.assertEqual(dependencies(self.w, json.loads(self.rows()['B']['body'])), ['X'])
        (self.w.path / self.rel).write_text('{"version":1,"version":1}')
        with self.assertRaisesRegex(Error, 'Duplicate'): self.engine.preview(self.rel)

    def test_historical_legacy_consumer_keeps_raw_history_and_blocks_downstream(self):
        self.proposal()
        self.finish(self.w.claim('synthetic-worker', 'A'))
        self.finish(self.w.claim('synthetic-worker', 'B'))
        # Normal completion requires A done, which cannot be superseded. Seed only
        # this impossible legacy inconsistency to test defensive historical handling.
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET status='ready',owner=NULL,token=NULL,lease=NULL WHERE id='A'")
        p = json.loads((self.w.path / self.rel).read_text()); p['rebindings'] = []
        (self.w.path / self.rel).write_text(json.dumps(p))
        before = self.rows()['B']
        self.assertIn('B', self.engine.preview(self.rel)['historical_consumers'])
        self.accept(); self.engine.apply(self.rid)
        self.assertEqual(before, self.rows()['B'])
        with self.assertRaises(Error): self.w.claim('synthetic-worker', 'C')
        self.assertEqual(dependencies(self.w, json.loads(before['body'])), ['A'])

    def test_second_revision_and_normal_later_import(self):
        self.proposal(); self.accept(); self.engine.apply(self.rid)
        p = {'version': 1, 'reason': 'Use another explicit prerequisite in the synthetic second revision.',
             'supersede': [], 'replacements': {}, 'tasks': [],
             'rebindings': [{'consumer': 'B', 'from': ['A1', 'A2'], 'to': ['X']}]}
        (self.w.path / self.rel).write_text(json.dumps(p))
        self.accept(); self.engine.apply(self.rid)
        self.add(self.task('Y', depends=['B']))
        self.assertEqual(dependencies(self.w, json.loads(self.rows()['B']['body'])), ['X'])

    def test_release_clears_owner_and_allows_rebinding_preview(self):
        self.proposal(supersede=[], replacements={}, tasks=[],
                      rebindings=[{'consumer': 'B', 'from': ['A'], 'to': ['X']}])
        self.finish(self.w.claim('synthetic-worker', 'A'))
        claim = self.w.claim('synthetic-worker', 'B')
        self.w.release('B', claim['token'], 'Inspected fixture worker; no activity remains.')
        row = self.rows()['B']
        for field in ('owner', 'token', 'lease', 'checks', 'reviews'):
            self.assertIsNone(row[field])
        self.assertEqual(self.engine.preview(self.rel)['blockers'], [])
        with self.w.transaction() as con:
            events = [json.loads(r[0]) for r in con.execute("SELECT data FROM events WHERE kind='claimed'")]
        self.assertTrue(any(e['id'] == 'B' and e['owner'] == 'synthetic-worker' for e in events))

    def test_legacy_released_ready_owner_recovers_then_allows_revision_preview(self):
        self.proposal(supersede=[], replacements={}, tasks=[],
                      rebindings=[{'consumer': 'B', 'from': ['A'], 'to': ['X']}])
        self.finish(self.w.claim('synthetic-worker', 'A'))
        claim = self.w.claim('synthetic-worker', 'B')
        self.w.release('B', claim['token'], 'Inspected fixture worker; no activity remains.')
        # Model a prior-release row in this disposable SQLite fixture only.
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET owner='synthetic-worker' WHERE id='B'")
        before = self.rows()['B']
        self.assertTrue(self.engine.preview(self.rel)['blockers'])
        # Ownership normalization is not execution: stale input does not prevent
        # it, but still prevents claiming/running the now-unowned task.
        (self.w.path / 'plans/delivery.md').write_text('Changed fixture plan requiring reconciliation.')
        self.w.recover('B', 'Inspected fixture processes; released worker has stopped.')
        after = self.rows()['B']
        self.assertIsNone(after['owner'])
        self.assertEqual(before['body'], after['body'])
        with self.assertRaises(Error): self.w.claim('synthetic-next', 'B')
        self.w.record('plan')
        self.assertFalse(any(b.get('task') == 'B' and b['reason'] == 'active ownership or ineligible state'
                             for b in self.engine.preview(self.rel)['blockers']))

    def test_released_old_evidence_stale_and_independent_scoped_proof_current(self):
        self.proposal(supersede=[], replacements={}, tasks=[],
                      rebindings=[{'consumer': 'B', 'from': ['A'], 'to': ['X']}])
        self.finish(self.w.claim('synthetic-worker', 'A'))
        claim = self.w.claim('synthetic-worker', 'B')
        self.w.verify('B', claim['token']); self.docs(claim)
        before = self.rows(); body = json.loads(before['B']['body'])
        old_inputs = self.w.task_inputs(body)
        docs_ref = body['documentation_receipt']
        old_checks = before['B']['checks']
        old_ref = json.loads(old_checks)
        old_receipt = self.w.receipt(old_ref)
        self.w.release('B', claim['token'], 'Synthetic pause before dependency revision.', blocked=True)
        self.w.recover('B', 'Synthetic released worker has ceased all fixture activity.')
        independent = {}
        for tid in ('S', 'T', 'U'):
            scoped = self.task(tid)
            scoped['freshness'] = {'mode': 'scoped-v1', 'independent': True, 'shared_contracts': [], 'config': [], 'mandatory_context': []}
            self.add(scoped); self.finish(self.w.claim('synthetic-worker', tid))
            independent[tid] = self.rows()[tid]
        self.accept(); self.engine.apply(self.rid)
        after = self.rows(); new_body = json.loads(after['B']['body'])
        self.assertNotEqual(old_inputs, self.w.task_inputs(new_body))
        self.assertEqual(new_body['documentation_receipt'], docs_ref)
        self.assertEqual(self.w.documentation_state(new_body)['state'], 'outstanding')
        self.assertIn('stale', self.w.documentation_state(new_body)['reason'])
        for tid, original in independent.items():
            self.assertEqual(original, after[tid])
            with self.w.transaction() as con:
                self.assertTrue(self.w.dependencies_current(con, json.loads(after[tid]['body'])))
            self.assertEqual(self.w.review_state(after[tid], json.loads(after[tid]['body']), None)['state'], 'current')
        self.assertNotEqual(old_receipt['snapshot'], self.w.task_snapshot(new_body))
        self.assertEqual(old_receipt, self.w.receipt(old_ref))

    def test_applied_retry_checks_original_reviews_without_current_phase_requirement(self):
        self.proposal(); self.accept(); self.engine.apply(self.rid)
        (self.w.path / 'plans/delivery.md').write_text('Changed synthetic plan after successful application.')
        self.assertTrue(self.engine.apply(self.rid)['already_applied'])
        report = self.w.path / 'reviews/revision-correctness.json'
        raw = report.read_bytes(); report.write_bytes(raw + b'\n')
        with self.assertRaisesRegex(Error, 'report missing or changed'): self.engine.apply(self.rid)
        report.write_bytes(raw); report.unlink()
        with self.assertRaisesRegex(Error, 'report missing or changed'): self.engine.apply(self.rid)

    def test_replacement_duplicate_edges_refused(self):
        p = self.proposal()
        p['tasks'][0]['depends_on'] = ['X', 'X']
        (self.w.path / self.rel).write_text(json.dumps(p))
        with self.assertRaisesRegex(Error, 'Duplicate'): self.engine.preview(self.rel)

    def test_held_and_observed_live_verification_guards_refuse_without_mutation(self):
        self.proposal(); self.accept(); before = self.rows()
        folder = self.w.path / 'verification'; folder.mkdir(exist_ok=True)
        with (folder / 'C.lock').open('a+') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(Error, 'operation active'): self.engine.apply(self.rid)
            self.assertEqual(before, self.rows())
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], start_new_session=True)
        try:
            (folder / 'C.json').write_text(json.dumps({'version': 1, 'state': 'running', 'process_group': child.pid, 'child_pid': child.pid}))
            with self.assertRaisesRegex(Error, 'still live'): self.engine.apply(self.rid)
            self.assertEqual(before, self.rows())
        finally:
            child.terminate(); child.wait(timeout=5)

    def test_broad_replan_after_overlay_preserves_history_and_accepts_new_tasks(self):
        self.proposal(); self.accept(); self.engine.apply(self.rid)
        before = self.rows()
        self.w.replan('Synthetic broad scope change requires new definitions and current phase records.')
        for tid, row in self.rows().items():
            self.assertEqual(row['body'], before[tid]['body'])
            self.assertEqual(row['status'], 'superseded')
        self.w.record('analysis'); self.w.record('plan')
        self.add(self.task('NEXT'))
        self.assertEqual(self.w.claim('synthetic-worker', 'NEXT')['id'], 'NEXT')

    def test_superseded_descendant_does_not_poison_later_revision(self):
        self.proposal(supersede=['C'], replacements={'C': ['C1']},
                      tasks=[self.task('C1', depends=['B'])], rebindings=[])
        self.accept(); self.engine.apply(self.rid)
        p = {'version': 1, 'reason': 'Synthetic subsequent explicit consumer refinement.',
             'supersede': [], 'replacements': {}, 'tasks': [],
             'rebindings': [{'consumer': 'B', 'from': ['A'], 'to': ['X']}]}
        (self.w.path / self.rel).write_text(json.dumps(p))
        view = self.engine.preview(self.rel)
        self.assertEqual(view['affected_unfinished'], ['B', 'C1'])
        self.assertFalse(view['blockers'])
        before = self.rows()['C']
        self.accept(); self.engine.apply(self.rid)
        self.assertEqual(before, self.rows()['C'])

    def test_no_overlay_compatibility_version_and_history_corruption(self):
        self.proposal()
        before = self.rows(); task = json.loads(before['B']['body'])
        self.assertEqual(dependencies(self.w, task), ['A'])
        self.assertEqual(expected_inputs(self.w, task), task['inputs'])
        self.assertEqual(self.w.task_inputs(task), task['inputs'])
        self.accept(); self.engine.apply(self.rid)
        with self.w.transaction() as con:
            con.execute("UPDATE meta SET value='2' WHERE key='revision-version'")
        with self.assertRaisesRegex(Error, 'Unsupported'): dependencies(self.w, task)
        with self.w.transaction() as con:
            con.execute("UPDATE meta SET value='1' WHERE key='revision-version'")
            con.execute('DELETE FROM meta WHERE key=?', ('revision-binding-history:' + self.rid + ':B',))
        with self.assertRaisesRegex(Error, 'history'): dependencies(self.w, task)

    def test_affected_owner_blocks_even_if_lease_expired(self):
        self.proposal()
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET owner='synthetic-owner',token='private',lease=0 WHERE id='C'")
        self.assertTrue(self.engine.preview(self.rel)['blockers'])
        with self.assertRaises(Error): self.engine.prepare(self.rel, 'synthetic-author')

    def test_unknown_verification_attempt_and_expired_owner_refused(self):
        self.proposal(); self.accept()
        path = self.w.path / 'verification/C.json'; path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps({'version': 1, 'state': 'launching'}))
        with self.assertRaises(Error): self.engine.apply(self.rid)
        path.unlink()
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET owner='synthetic-owner',token='private-token',lease=0 WHERE id='C'")
        view = self.engine.preview(self.rel)
        self.assertTrue(view['blockers'])
        self.assertNotIn('private-token', json.dumps(view))


if __name__ == '__main__': unittest.main()
