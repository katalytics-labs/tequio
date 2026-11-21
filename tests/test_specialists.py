import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tequio.core import Error,Workspace,digest,load
from task_review_fixtures import reviewed_import
from tequio.install import install,uninstall
from tequio.specialists import Factory,validate_package
ROOT=Path(__file__).resolve().parents[1]

class SpecialistFactory(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.project=self.base/'project';self.project.mkdir();install(ROOT,self.project)
        brief=self.base/'brief.md';brief.write_text('Use a selected stack to deliver bounded behavior with actual evidence.')
        self.w=Workspace.create(self.project,'main',brief)
        (self.w.path/'analysis/requirements.md').write_text('Actual fixture requirements: test expected output and error behavior.')
        self.w.record('analysis');(self.w.path/'plans/delivery.md').write_text('Chosen technology and explicit test contract.');self.w.record('plan')
        self.factory=Factory(self.w);self.package=self.base/'package';self.package.mkdir();(self.package/'references').mkdir()
        (self.package/'references/source.md').write_text('Synthetic source notes for deterministic tests only. Source authority and factual coverage need independent review; schema checks do not establish those facts.')
        (self.package/'SKILL.md').write_text('---\nname: fixture-specialist\ndescription: "Exercise a bounded fixture technology behavior."\n---\n\nRead the actual task and current implementation. Preserve source requirements and return actual expected and failed behavior evidence. Read [source notes](references/source.md). Keep assignment scope and actual integration explicit.\n')
        self.spec={'schema_version':1,'id':'fixture-specialist','mode':'implementation','technologies':[{'name':'fixture','version':'1','selection':'selected'}],'capabilities':['Fixture behavior'],'exclusions':['Other work'],'triggers':['Fixture requests'],'acceptance':['Actual success/error behavior'],'context':['analysis/requirements.md','plans/delivery.md'],'sources':[{'url':'https://example.org/reference','kind':'primary','accessed':'2026-01-01','locator':'Fixture-only synthetic notes','artifact':'references/source.md'}],'checks':[[sys.executable,'-m','unittest','discover','-s','tests','-v']]}
        self.save()
        self.fixture=self.base/'exercise';self.fixture.mkdir();(self.fixture/'tests').mkdir();(self.fixture/'tests/test_real.py').write_text('import unittest\nclass TestBehavior(unittest.TestCase):\n def test_result(self): self.assertEqual(sum([1,2]),3)\n')
    def tearDown(self):self.tmp.cleanup()
    def save(self): (self.package/'specialist.json').write_text(json.dumps(self.spec))
    def register(self,replace=False):return self.factory.register(self.package,'author',replace)
    def reviewed(self,findings=None,reviewer='reviewer'):
        with self.factory.locked() as d:
            e=d['specialists']['fixture-specialist'];ref=e['exercise'];receipt=load(self.factory.root/ref['path']);revision=e['revision']
        p=self.w.path/'reviews/specialist.json';p.write_text(json.dumps({'schema_version':1,'reviewer':reviewer,'revision':revision,'exercise_sha256':ref['sha256'],'fixture_snapshot':receipt['snapshot'],'coverage':['Synthetic test checks actual command execution, not model expertise'],'source_checks':['Synthetic fixture sources only; deterministic state exercise'],'limitations':['No real technology qualification claimed by this test'],'findings':findings or []}))
        return str(p.relative_to(self.w.path))
    def qualify(self):
        self.register();self.factory.validate('fixture-specialist');self.assertTrue(self.factory.exercise('fixture-specialist',self.fixture)['passed']);self.factory.qualify('fixture-specialist','reviewer',self.reviewed())
    def task(self):return {'id':'NEW','title':'Use specialist','outcome':'Expected behavior','scope':'Fixture','exclusions':'Other work','sources':['briefs/brief.md'],'writes':['result.py'],'reads':[],'specialists':['fixture-specialist'],'checks':[[sys.executable,'-c','print(1)']],'acceptance':['Expected outcome'],'documentation':{'mode':'not-needed','paths':[],'reason':'This isolated coordinator fixture changes no product behavior or user-facing contract.'},'handoff':'Evidence','risk':'normal','security_assessment':{'surfaces':[], 'reason':'This deterministic isolated fixture changes no security surface.'}}
    def test_full_lifecycle_and_task_binding(self):
        self.qualify();binding=self.factory.resolve('fixture-specialist');self.assertEqual(binding['mode'],'implementation')
        p=self.w.path/'tasks/import.json';p.write_text(json.dumps([self.task()]));reviewed_import(self.w,p)
        c=self.w.claim('writer');self.assertIn('fixture-specialist',c['task']['specialist_bindings'])
        self.register(replace=True)
        with self.assertRaises(Error):self.w.verify('NEW',c['token'])
    def test_draft_or_format_is_not_exercise_tested(self):
        self.register()
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist')
        self.factory.validate('fixture-specialist')
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist')
        t=self.task();t['stage']='draft';self.w.validate_task(t)
    def test_sources_and_references_rejected(self):
        cases=[('sources',[]),('mode','wrong')]
        for key,value in cases:
            original=self.spec[key];self.spec[key]=value;self.save()
            with self.assertRaises(Error):validate_package(self.package)
            self.spec[key]=original
        self.save();(self.package/'references/source.md').unlink()
        with self.assertRaises(Error):validate_package(self.package)
    def test_candidate_research_cannot_become_implementation(self):
        self.spec['technologies'][0]['selection']='candidate';self.save()
        with self.assertRaises(Error):self.register()
        self.spec['mode']='research';self.save();self.qualify()
        self.factory.resolve('fixture-specialist','research')
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist','implementation')
    def test_changed_context_and_package_invalidate(self):
        self.qualify();(self.w.path/'plans/delivery.md').write_text('Changed technology/requirements')
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist')
        self.assertTrue(self.factory.inspect()['specialists'][0]['stale'])
    def test_author_and_open_findings_cannot_qualify(self):
        self.register();self.factory.validate('fixture-specialist');self.factory.exercise('fixture-specialist',self.fixture)
        with self.assertRaises(Error):self.factory.qualify('fixture-specialist','author',self.reviewed(reviewer='author'))
        with self.assertRaises(Error):self.factory.qualify('fixture-specialist','reviewer',self.reviewed(findings=['Missing acceptance']))
    def test_failed_exercise_and_wrong_review_binding(self):
        self.spec['checks']=[[sys.executable,'-c','raise SystemExit(1)']];self.save();self.register();self.factory.validate('fixture-specialist')
        self.assertFalse(self.factory.exercise('fixture-specialist',self.fixture)['passed'])
        with self.assertRaises(Error):self.factory.qualify('fixture-specialist','reviewer',self.reviewed())
    def test_receipt_or_report_tampering_denied(self):
        self.qualify();(self.w.path/'reviews/specialist.json').write_text('{}')
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist')
    def test_fixture_outside_project_and_source_symlinks(self):
        self.register();self.factory.validate('fixture-specialist')
        with self.assertRaises(Error):self.factory.exercise('fixture-specialist',self.project)
        (self.package/'link').symlink_to(self.package/'SKILL.md')
        with self.assertRaises(Error):validate_package(self.package)
    def test_publish_prefix_assets_and_installer_preservation(self):
        self.qualify();result=self.factory.publish('fixture-specialist');dest=self.project/result['discovery']
        self.assertTrue((dest/'references/source.md').exists())
        install(ROOT,self.project);self.assertTrue(dest.exists());uninstall(self.project);self.assertTrue(dest.exists());self.assertTrue(self.factory.index.exists())
    def test_publish_refuses_modified_discovery(self):
        self.qualify();result=self.factory.publish('fixture-specialist');p=Path(result['discovery'])/'SKILL.md';p.write_text('Owner edit')
        with self.assertRaises(Error):self.factory.publish('fixture-specialist')
    def test_workflow_assets_installed_and_source_revisions_immutable(self):
        self.assertTrue((self.project/'.agents/skills/tequio-specialists/references/procedure.md').is_file())
        self.register();entry=self.factory.inspect()['specialists'][0];old=Path(entry['package'])/'SKILL.md';before=old.read_bytes()
        (self.package/'SKILL.md').write_text((self.package/'SKILL.md').read_text()+'New guidance\n')
        self.assertEqual(old.read_bytes(),before)
        with self.assertRaises(Error):self.register()
        self.register(replace=True);self.assertEqual(old.read_bytes(),before)

class FactoryRegression(unittest.TestCase):
    setUp=SpecialistFactory.setUp
    tearDown=SpecialistFactory.tearDown
    save=SpecialistFactory.save
    register=SpecialistFactory.register
    reviewed=SpecialistFactory.reviewed
    qualify=SpecialistFactory.qualify
    task=SpecialistFactory.task
    def test_uninstall_does_not_bypass_generated_qualification(self):
        self.register();uninstall(self.project)
        with self.assertRaises(Error):self.w.validate_task(self.task())
    def test_quoted_name_and_prefix_migration(self):
        p=self.package/'SKILL.md';p.write_text(p.read_text().replace('name: fixture-specialist','name: "fixture-specialist"'))
        self.qualify();first=self.factory.publish('fixture-specialist');install(ROOT,self.project,prefix='tq-')
        second=self.factory.publish('fixture-specialist')
        self.assertFalse(Path(first['discovery']).exists())
        self.assertIn('name: tq-fixture-specialist\n',(Path(second['discovery'])/'SKILL.md').read_text())
    def test_qualified_research_task_is_distinct(self):
        self.spec['mode']='research';self.spec['technologies'][0]['selection']='candidate';self.save();self.qualify()
        t=self.task();t['kind']='research';self.w.validate_task(t)
        t['kind']='implementation'
        with self.assertRaises(Error):self.w.validate_task(t)

class CapturedEvidence(unittest.TestCase):
    setUp=SpecialistFactory.setUp
    tearDown=SpecialistFactory.tearDown
    save=SpecialistFactory.save
    register=SpecialistFactory.register
    reviewed=SpecialistFactory.reviewed
    qualify=SpecialistFactory.qualify
    task=SpecialistFactory.task
    def test_historical_capture_survives_original_fixture_cleanup(self):
        self.qualify();shutil.rmtree(self.fixture)
        self.factory.resolve('fixture-specialist')
        e=self.factory.inspect()['specialists'][0];receipt=load(self.factory.root/e['exercise']['path'])
        (self.factory.root/receipt['capture']/'tests/test_real.py').write_text('Modified historical evidence')
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist')
        self.assertTrue(self.factory.inspect()['specialists'][0]['stale'])
    def test_local_dependency_content_is_captured(self):
        (self.fixture/'node_modules').mkdir();(self.fixture/'node_modules/runtime.js').write_text('actual dependency data')
        self.qualify();e=self.factory.inspect()['specialists'][0];receipt=load(self.factory.root/e['exercise']['path'])
        self.assertEqual((self.factory.root/receipt['capture']/'node_modules/runtime.js').read_text(),'actual dependency data')
    def test_material_symlinks_rejected(self):
        self.register();self.factory.validate('fixture-specialist');(self.fixture/'alias').symlink_to(self.fixture/'tests')
        with self.assertRaises(Error):self.factory.exercise('fixture-specialist',self.fixture)

class ProjectVersionContext(unittest.TestCase):
    setUp=SpecialistFactory.setUp
    tearDown=SpecialistFactory.tearDown
    save=SpecialistFactory.save
    register=SpecialistFactory.register
    reviewed=SpecialistFactory.reviewed
    qualify=SpecialistFactory.qualify
    def test_project_lockfile_change_invalidates_qualification(self):
        p=self.project/'requirements.txt';p.write_text('example==1.0\n');self.spec['project_context']=['requirements.txt'];self.save();self.qualify()
        p.write_text('example==2.0\n')
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist')

class ExerciseAttemptInvalidation(unittest.TestCase):
    setUp=SpecialistFactory.setUp
    tearDown=SpecialistFactory.tearDown
    save=SpecialistFactory.save
    register=SpecialistFactory.register
    reviewed=SpecialistFactory.reviewed
    qualify=SpecialistFactory.qualify
    def test_aborted_new_exercise_cannot_reuse_old_green_receipt(self):
        self.qualify();(self.fixture/'bad-link').symlink_to(self.fixture/'tests')
        with self.assertRaises(Error):self.factory.exercise('fixture-specialist',self.fixture)
        with self.assertRaises(Error):self.factory.resolve('fixture-specialist')
        self.assertIsNone(self.factory.inspect()['specialists'][0]['exercise'])
