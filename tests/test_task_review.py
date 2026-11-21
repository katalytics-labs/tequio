"""Task-authoring review gate: content, context, identity and report freshness."""
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
from test_lifecycle import Lifecycle, ROOT
from task_review_fixtures import synthetic_draft
from tequio.core import Error
from tequio.task_review import TaskReview, AREAS

class TaskReviewTests(unittest.TestCase):
    setUp = Lifecycle.setUp
    tearDown = Lifecycle.tearDown
    task = Lifecycle.task

    def prepare(self, task=None):
        self.path = self.w.path / 'tasks/proposal.json'
        self.path.write_text(json.dumps([task or self.task()]))
        self.gate = TaskReview(self.w)
        self.batch = self.gate.prepare(self.path, 'author')['batch']
        return self.batch

    def report(self, kind, findings=None):
        rel = 'reviews/task-' + kind + '.json'
        body = {'batch': self.batch,
                'summary': 'Synthetic unit-fixture report inspects task coverage, actual dependency and ownership declarations and check definitions; no live independent assessment claimed.',
                'coverage': {area: 'Synthetic fixture inspected declarations for ' + area + '; semantic adequacy is represented only for this isolated test.' for area in AREAS[kind]},
                'findings': findings or []}
        (self.w.path / rel).write_text(json.dumps(body))
        return rel

    def accept(self):
        for kind in AREAS:
            self.gate.review(self.batch, 'reviewer-' + kind, kind, self.report(kind))

    def test_unreviewed_import_refused(self):
        self.prepare()
        with self.assertRaisesRegex(Error, 'Missing task-batch correctness'):
            self.w.import_tasks(self.path)

    def test_unprepared_import_refused(self):
        p = self.w.path / 'tasks/new.json'; p.write_text(json.dumps([self.task()]))
        with self.assertRaisesRegex(Error, 'unreviewed'):
            self.w.import_tasks(p)

    def test_two_reviews_allow_import_but_not_task_completion(self):
        self.prepare(); self.accept()
        self.assertEqual(self.gate.status(self.path)['state'], 'reviewed')
        self.assertEqual(self.w.import_tasks(self.path)['imported'], ['A'])
        c = self.w.claim('writer')
        with self.assertRaises(Error): self.w.complete('A', c['token'], 'Not implemented or reviewed')

    def test_drafts_also_require_reviews(self):
        t=synthetic_draft(self.task());self.prepare(t)
        with self.assertRaises(Error): self.w.import_tasks(self.path)
        self.accept();self.w.import_tasks(self.path)
        self.assertFalse(self.w.status()['tasks'][0]['dispatchable'])

    def test_author_and_same_actor_denied(self):
        self.prepare()
        with self.assertRaisesRegex(Error,'author cannot'):
            self.gate.review(self.batch,'author','correctness',self.report('correctness'))
        self.gate.review(self.batch,'one','correctness',self.report('correctness'))
        with self.assertRaisesRegex(Error,'must be distinct'):
            self.gate.review(self.batch,'one','redteam',self.report('redteam'))
        with self.assertRaisesRegex(Error,'author is immutable'):
            self.gate.prepare(self.path,'other-author')

    def test_findings_block_import_and_new_report_can_clear(self):
        self.prepare();self.accept()
        self.gate.review(self.batch,'reviewer-redteam','redteam',self.report('redteam',['All-draft backlog has no stated path to execution']))
        with self.assertRaisesRegex(Error,'Resolve task-batch redteam findings'):
            self.w.import_tasks(self.path)
        self.gate.review(self.batch,'reviewer-redteam','redteam',self.report('redteam'))
        self.w.import_tasks(self.path)

    def test_task_changes_require_new_batch(self):
        self.prepare();self.accept();tasks=json.loads(self.path.read_text())
        tasks[0]['writes']=['different.txt'];self.path.write_text(json.dumps(tasks))
        self.assertEqual(self.gate.status(self.path)['state'],'review-required')
        with self.assertRaisesRegex(Error,'unreviewed'):self.w.import_tasks(self.path)
        self.assertNotEqual(self.batch,self.gate.prepare(self.path,'author')['batch'])

    def test_whitespace_only_task_changes_preserve_review(self):
        self.prepare();self.accept();self.path.write_text(json.dumps(json.loads(self.path.read_text()),indent=4))
        self.w.import_tasks(self.path)

    def test_report_tampering_and_deletion_block(self):
        self.prepare();self.accept();p=self.w.path/'reviews/task-correctness.json'
        original=p.read_text();p.write_text(original+'\n')
        with self.assertRaisesRegex(Error,'changed'):self.w.import_tasks(self.path)
        p.write_text(original);p.unlink()
        with self.assertRaisesRegex(Error,'missing'):self.w.import_tasks(self.path)

    def test_changed_plan_requires_new_review_even_after_receipt_refresh(self):
        self.prepare();self.accept();p=self.w.path/'plans/delivery.md';p.write_text(p.read_text()+'\nChanged scope.')
        self.w.record('plan')
        with self.assertRaisesRegex(Error,'unreviewed'):self.w.import_tasks(self.path)
        self.assertNotEqual(self.batch,self.gate.prepare(self.path,'author')['batch'])

    def test_wrong_binding_incomplete_coverage_and_report_escape(self):
        self.prepare();rel=self.report('correctness');p=self.w.path/rel;original=json.loads(p.read_text())
        for key,value in [('batch','0'*64),('coverage',{}),('findings',None),('summary','thin')]:
            body={**original,key:value};p.write_text(json.dumps(body))
            with self.assertRaises(Error):self.gate.review(self.batch,'reviewer','correctness',rel)
        with self.assertRaises(Error):self.gate.review(self.batch,'reviewer','correctness','../outside.json')

    def test_report_replacement_after_read_cannot_bind_unvalidated_bytes(self):
        self.prepare()
        rel=self.report('correctness'); path=self.w.path/rel
        clean=path.read_bytes(); changed=json.loads(clean)
        changed['findings']=['A real unresolved task-design defect']
        original=type(path).read_bytes
        def replace_on_read(p):
            data=original(p)
            if p==path:
                path.write_text(json.dumps(changed))
            return data
        with patch.object(type(path),'read_bytes',replace_on_read):
            self.gate.review(self.batch,'reviewer-correctness','correctness',rel)
        self.gate.review(self.batch,'reviewer-redteam','redteam',self.report('redteam'))
        with self.assertRaisesRegex(Error,'changed'):
            self.w.import_tasks(self.path)

    def test_cited_source_outside_phase_directories_is_bound(self):
        source=self.w.path/'evidence/requirement.md';source.write_text('An actual additional requirement.')
        t=self.task();t['sources'].append('evidence/requirement.md')
        self.prepare(t);self.accept();source.write_text('Changed evidence-backed requirement.')
        with self.assertRaisesRegex(Error,'unreviewed'):self.w.import_tasks(self.path)
        self.assertEqual(self.gate.status(self.path)['state'],'review-required')

    def test_ready_specialist_bindings_are_part_of_review_context(self):
        original=self.w.specialist_bindings
        with patch.object(self.w,'specialist_bindings',return_value={'fixture':{'revision':'one'}}):
            self.prepare();self.accept()
        with patch.object(self.w,'specialist_bindings',return_value={'fixture':{'revision':'two'}}):
            with self.assertRaisesRegex(Error,'unreviewed'):self.w.import_tasks(self.path)

    def test_cli_review_status_is_read_only(self):
        self.prepare()
        r=subprocess.run([sys.executable,str(ROOT/'bin/tequio'),'--project',str(self.root),'--workspace','fixture','task-review-status',str(self.path)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['state'],'review-required')
        self.assertEqual(self.w.status()['tasks'],[])

if __name__=='__main__':unittest.main()
