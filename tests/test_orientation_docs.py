import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import test_lifecycle as fixtures
ROOT=fixtures.ROOT
from tequio.core import Error,Workspace

class DocumentationGate(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    report=fixtures.Lifecycle.report
    docs=fixtures.Lifecycle.docs
    def prepare(self,change_docs=True):
        (self.root/'impl.py').write_text('VALUE=1\n')
        (self.root/'docs').mkdir();(self.root/'docs/API.md').write_text('# Current behavior\n\nThe observed implementation exposes VALUE equal to one.\n')
        t=self.task();t['writes']=['impl.py','docs/API.md'];t['documentation']={'mode':'update','paths':['docs/API.md'],'reason':'The public value changes, requiring its behavior contract to be updated.'};t['checks']=[[sys.executable,'-c','import impl; assert impl.VALUE == 2']]
        self.add(t);c=self.w.claim('writer');(self.root/'impl.py').write_text('VALUE=2\n')
        if change_docs:(self.root/'docs/API.md').write_text('# Current behavior\n\nThe verified implementation exposes VALUE equal to two; the earlier value is no longer supported.\n')
        self.assertTrue(self.w.verify('A',c['token'])['passed']);return c
    def reconciliation(self,c):
        with self.w.transaction() as con:task=json.loads(con.execute("SELECT body FROM tasks WHERE id='A'").fetchone()[0])
        data={'summary':'Compared the actual task, its plan sources, current implementation and passing behavior check; the updated contract states the observed value correctly.','deviations':[],'reconciliation':[{'source':source,'actual':['impl.py'],'docs':['docs/API.md'],'disposition':'implemented','notes':'The actual implementation and its passing check now expose value two, as the updated contract records.'} for source in task['sources']]}
        p=self.w.path/'reviews/docs.json';p.write_text(json.dumps(data));return p,data
    def test_changed_docs_reconciliation_review_and_completion(self):
        c=self.prepare();p,_=self.reconciliation(c);self.w.document('A',c['token'],'reviews/docs.json')
        self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])
        self.assertEqual(self.w.complete('A',c['token'],'Actual value and documentation verified')['completed'],'A')
    def test_missing_policy_and_noop_updates_rejected(self):
        t=self.task();t.pop('documentation')
        with self.assertRaises(Error):self.w.validate_task(t)
        c=self.prepare(change_docs=False);self.reconciliation(c)
        with self.assertRaises(Error):self.w.document('A',c['token'],'reviews/docs.json')
    def test_source_coverage_and_deviations_checked(self):
        c=self.prepare();p,data=self.reconciliation(c);data['reconciliation'].pop();p.write_text(json.dumps(data))
        with self.assertRaises(Error):self.w.document('A',c['token'],'reviews/docs.json')
        p,data=self.reconciliation(c);data['deviations']=['The implementation does not match the agreed scope'];p.write_text(json.dumps(data))
        with self.assertRaises(Error):self.w.document('A',c['token'],'reviews/docs.json')
    def test_missing_docs_receipt_blocks_even_clean_review(self):
        c=self.prepare();self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Tests passed')
        self.reconciliation(c);self.w.document('A',c['token'],'reviews/docs.json')
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Documentation recorded after old review')
    def test_report_change_invalidates_completion(self):
        c=self.prepare();p,data=self.reconciliation(c);self.w.document('A',c['token'],'reviews/docs.json');self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])
        data['summary']+=' Changed after review';p.write_text(json.dumps(data))
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Done')
    def test_no_change_requires_explicit_reconciliation_and_review(self):
        self.add(self.task());c=self.w.claim('writer');self.w.verify('A',c['token']);self.docs(c)
        with self.assertRaises(Error):self.w.complete('A',c['token'],'No docs change needed')
        self.w.review('A',c['token'],'reviewer','correctness',self.report(),[]);self.w.complete('A',c['token'],'State-only fixture verified')
    def test_doc_paths_must_be_owned_and_not_private(self):
        t=self.task();t['documentation']={'mode':'update','paths':['docs/API.md'],'reason':'A public behavior change requires documented contracts.'}
        with self.assertRaises(Error):self.w.validate_task(t)
        t['writes']=['.tequio'];t['documentation']['paths']=['.tequio/internal.md']
        with self.assertRaises(Error):self.w.documentation_policy(t)

class Orientation(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    report=fixtures.Lifecycle.report
    docs=fixtures.Lifecycle.docs
    finish=fixtures.Lifecycle.finish
    def test_fresh_workspace_current_plan_and_ready_task(self):
        self.assertEqual(self.w.status()['workflow']['next']['skill'],'tequio-tasks')
        self.add(self.task());state=self.w.status();self.assertEqual(state['workflow']['next']['skill'],'tequio-build');self.assertEqual(state['workflow']['outstanding'],1)
    def test_review_with_missing_docs_is_named(self):
        self.add(self.task());c=self.w.claim('writer');self.w.verify('A',c['token']);state=self.w.status();self.assertEqual(state['workflow']['stage'],'documentation-and-review')
        self.docs(c);self.assertEqual(self.w.status()['workflow']['next']['skill'],'tequio-inspect')
    def test_stale_inputs_and_expired_claim_need_reconciliation(self):
        self.add(self.task());c=self.w.claim('writer');(self.w.path/'briefs/brief.md').write_text('Changed requirements')
        self.assertEqual(self.w.status()['workflow']['next']['skill'],'tequio-pickup')
    def test_all_recorded_tasks_is_not_release_readiness(self):
        self.add(self.task());self.finish(self.w.claim('writer'));state=self.w.status()['workflow'];self.assertEqual(state['stage'],'recorded-work-complete');self.assertEqual(state['next']['skill'],'tequio-inspect');self.assertIn('not a product-readiness',state['scope'])
    def test_status_read_only_without_workspace_and_with_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            project=Path(temp);run=subprocess.run([sys.executable,str(ROOT/'bin/tequio'),'--project',str(project),'status'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout)['workflow']['stage'],'intake');self.assertEqual(list(project.iterdir()),[]);self.assertEqual(json.loads(run.stdout)['workflow']['next']['skill'],'tequio-briefing');self.assertIn('existing brief',json.loads(run.stdout)['workflow']['next']['reason'])
        before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.w.status();after={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()};self.assertEqual(before,after)
    def test_missing_analysis_and_planning_are_distinguished(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);brief=root/'brief.md';brief.write_text('A real brief');w=Workspace.create(root,'new',brief)
            self.assertEqual(w.status()['workflow']['next']['skill'],'tequio-explore')
            (w.path/'analysis/r.md').write_text('Source-linked requirements and observed risks');w.record('analysis')
            self.assertEqual(w.status()['workflow']['next']['skill'],'tequio-design')

class LegacyMigration(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    def test_active_legacy_task_is_not_sent_back_to_implementation(self):
        self.add(self.task());self.w.claim('writer')
        # Construct a genuine older persisted task shape to exercise upgrade handling.
        with self.w.transaction() as con:
            row=con.execute("SELECT body FROM tasks WHERE id='A'").fetchone();body=json.loads(row[0]);body.pop('documentation');con.execute("UPDATE tasks SET body=? WHERE id='A'",(json.dumps(body),))
        state=self.w.status()['workflow'];self.assertEqual(state['stage'],'task-contract-migration');self.assertEqual(state['next']['skill'],'tequio-redirect')

class ReviewOrientation(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    docs=fixtures.Lifecycle.docs
    report=fixtures.Lifecycle.report
    def test_fresh_review_recommends_closure_not_duplicate_review(self):
        self.add(self.task());claim=self.w.claim('writer');self.w.verify('A',claim['token']);self.docs(claim);self.w.review('A',claim['token'],'reviewer','correctness',self.report(),[])
        state=self.w.status()['workflow'];self.assertEqual(state['stage'],'ready-for-closure');self.assertEqual(state['next']['skill'],'tequio-build')
    def test_security_review_remaining_is_named(self):
        self.add(self.task(risk='security'));claim=self.w.claim('writer');self.w.verify('A',claim['token']);self.docs(claim);self.w.review('A',claim['token'],'reviewer','correctness',self.report(),[])
        self.assertEqual(self.w.status()['workflow']['next']['skill'],'tequio-challenge')

class ExplicitDocFreshness(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    report=fixtures.Lifecycle.report
    def test_declared_doc_hash_is_checked_even_under_snapshot_exclusion(self):
        target='docs/node_modules/API.md';file=self.root/target;file.parent.mkdir(parents=True);file.write_text('# API\n\nThe initial documented public output value is one.\n')
        t=self.task();t['writes']=['docs'];t['documentation']={'mode':'update','paths':[target],'reason':'The changed behavior contract requires a matching documentation update.'};self.add(t);c=self.w.claim('writer')
        file.write_text('# API\n\nThe newly verified documented public output value is two.\n');self.w.verify('A',c['token'])
        data={'summary':'Reconciled the precise task and source scope with the current documented contract and recorded check output.','deviations':[],'reconciliation':[{'source':s,'actual':['brief.md'],'docs':[target],'disposition':'implemented','notes':'This fixture tests direct documentation freshness even when a general snapshot excludes its directory.'} for s in t['sources']]}
        (self.w.path/'reviews/docs.json').write_text(json.dumps(data));self.w.document('A',c['token'],'reviews/docs.json');self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])
        file.write_text('# API\n\nThis is changed documentation that was not checked or reviewed.\n')
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Done')
