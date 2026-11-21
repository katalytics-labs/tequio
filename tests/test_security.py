"""Deterministic security contracts; fixture identities are not production review."""
import json
from test_lifecycle import Lifecycle
from tequio.core import Error
from tequio.reporting import proof


class SecurityWorkflow(Lifecycle):
    # Reuse setup/helpers without duplicating inherited lifecycle tests in discovery.
    def release_task(self, scoped=False):
        task=self.task(risk='security', reads=['candidate'])
        task.update(kind='release', candidate_paths=['candidate'])
        if scoped:
            task['freshness']={'mode':'scoped-v1','independent':True,'shared_contracts':[],'config':[],'mandatory_context':[]}
        return task

    def release_report(self, gaps=None):
        data={'candidate_paths':['candidate'], 'gaps':gaps or [],'coverage':{}}
        for area in ('candidate-inventory','dependencies','configuration','privacy-export'):
            data['coverage'][area]={'disposition':'reviewed','reason':'Inspected fixture candidate and documented bounded evidence coverage.', 'evidence':['candidate']}
        path=self.w.path/'reviews/release.json';path.write_text(json.dumps(data));return 'reviews/release.json'

    def test_assessment_import_and_drafts(self):
        for value in (None,{},[], {'surfaces':['unknown'],'reason':'A sufficiently long concrete fixture explanation.'}):
            task=self.task();task.update(stage='draft',security_assessment=value)
            with self.assertRaises(Error):self.w.validate_task(task)
        task=self.task();task.pop('security_assessment')
        with self.assertRaises(Error):self.w.validate_task(task)
        task['stage']='draft';self.w.validate_task(task)
        task=self.task();task['security_assessment']['surfaces']=['authorization']
        with self.assertRaises(Error):self.w.validate_task(task)
        task['risk']='security';self.w.validate_task(task)

    def test_release_scope_validation_and_missing_output(self):
        task=self.release_task()
        for candidates in ([],['../outside'],['.'],['.tequio'],['elsewhere'],['candidate/*']):
            task['candidate_paths']=candidates
            with self.assertRaises(Error):self.w.validate_task(task)
        task=self.release_task();task['risk']='normal'
        with self.assertRaises(Error):self.w.validate_task(task)
        self.add(self.release_task());claim=self.w.claim('writer')
        self.assertTrue(self.w.heartbeat('A',claim['token'])['execution_eligible'])
        with self.assertRaises(Error):self.w.verify('A',claim['token'])
        self.w.release('A',claim['token'],'Missing output can be built after reclaiming this fixture task')

    def test_release_report_and_lifecycle(self):
        (self.root/'candidate').mkdir();(self.root/'candidate/product.txt').write_text('Reviewed fixture')
        self.add(self.release_task());claim=self.w.claim('writer');self.w.verify('A',claim['token']);self.docs(claim)
        self.w.review('A',claim['token'],'correctness-reviewer','correctness',self.report(),[])
        with self.assertRaises(Error):self.w.complete('A',claim['token'],'premature')
        with self.assertRaises((Error,ValueError)):self.w.review('A',claim['token'],'security-reviewer','security',self.report(),[])
        report=self.release_report()
        with self.assertRaises(Error):self.w.review('A',claim['token'],'correctness-reviewer','security',report,[])
        self.w.review('A',claim['token'],'security-reviewer','security',report,[])
        self.assertEqual(self.w.complete('A',claim['token'],'Reviewed deterministic candidate')['completed'],'A')

    def test_candidate_drift_all_freshness_modes(self):
        for scoped in (False,True):
            task=self.release_task(scoped); task['reads']=['candidate','node_modules','bin/tequio'];task['candidate_paths']=['candidate']
            (self.root/'candidate').mkdir(exist_ok=True)
            (self.root/'bin').mkdir(exist_ok=True);(self.root/'bin/tequio').write_text('initial')
            folder=self.root/'node_modules';folder.mkdir(exist_ok=True);file=folder/'dependency.js';file.write_text('one')
            before=self.w.task_snapshot(task);file.write_text('two')
            self.assertNotEqual(before,self.w.task_snapshot(task))
            before=self.w.task_snapshot(task);(self.root/'bin/tequio').write_text('changed'+str(scoped))
            self.assertNotEqual(before,self.w.task_snapshot(task))

    def test_release_report_coverage_rejections(self):
        from tequio.security import release_report
        (self.root/'candidate').mkdir();task=self.release_task()
        report=self.release_report();path=self.w.path/report;original=json.loads(path.read_text())
        import copy
        mutations=[lambda d:d['coverage'].pop('dependencies'),
                   lambda d:d.update(candidate_paths=['different']),
                   lambda d:d['coverage']['candidate-inventory'].update(disposition='not-applicable'),
                   lambda d:d['coverage']['dependencies'].update(evidence=[]),
                   lambda d:d['coverage']['configuration'].update(reason='too short'),
                   lambda d:d['coverage']['privacy-export'].update(evidence=['../outside']),
                   lambda d:d.pop('gaps')]
        for mutate in mutations:
            data=copy.deepcopy(original);mutate(data);path.write_text(json.dumps(data))
            with self.assertRaises(Error):release_report(self.w,task,path)
        original['coverage']['dependencies'].update(disposition='not-applicable', evidence=[])
        path.write_text(json.dumps(original));release_report(self.w,task,path)

    def test_release_evidence_drift_denies_current_review(self):
        (self.root/'candidate').mkdir();file=self.root/'candidate/app';file.write_text('one')
        self.add(self.release_task(True));claim=self.w.claim('writer');self.w.verify('A',claim['token']);self.docs(claim)
        self.w.review('A',claim['token'],'reviewer','correctness',self.report(),[])
        self.w.review('A',claim['token'],'security-reviewer','security',self.release_report(),[])
        file.write_text('two')
        with self.assertRaises(Error):self.w.complete('A',claim['token'],'Stale candidate forbidden')
        with self.assertRaises(Error):self.w.review('A',claim['token'],'new-reviewer','security',self.release_report(),[])
        self.assertEqual(self.w.status()['tasks'][0]['review']['state'],'stale')
        self.assertNotEqual(proof(self.root,'fixture')['tasks'][0]['evidence'],'current')

    def legacy(self, status):
        self.add(self.task());claim=self.w.claim('writer') if status=='running' else None
        with self.w.transaction() as con:
            body=json.loads(con.execute("SELECT body FROM tasks WHERE id='A'").fetchone()[0]);body.pop('security_assessment')
            con.execute("UPDATE tasks SET body=?,status=? WHERE id='A'",(json.dumps(body),status))
        return claim

    def test_legacy_active_escape_and_readonly(self):
        claim=self.legacy('running');status=self.w.status()
        self.assertEqual(status['tasks'][0]['security']['state'],'migration-required')
        self.assertEqual(status['workflow']['stage'],'task-contract-migration')
        self.assertEqual(proof(self.root,'fixture')['tasks'][0]['security']['state'],'migration-required')
        self.assertFalse(self.w.heartbeat('A',claim['token'])['execution_eligible'])
        with self.assertRaises(Error):self.w.verify('A',claim['token'])
        self.w.release('A',claim['token'],'Migrate this unfinished task through explicit replan')
        with self.assertRaises(Error):self.w.claim('next')

    def test_historical_missing_assessment_readable(self):
        self.legacy('done')
        self.assertEqual(self.w.status()['tasks'][0]['security']['state'],'historical')
        self.assertEqual(proof(self.root,'fixture')['tasks'][0]['security']['state'],'historical')

# Prevent unittest from rerunning inherited tests for this subclass.
for _name in list(vars(Lifecycle)):
    if _name.startswith('test_') and _name not in vars(SecurityWorkflow):
        setattr(SecurityWorkflow, _name, None)
del Lifecycle
