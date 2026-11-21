import concurrent.futures
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from tequio.core import Error, Workspace, load, tree_hash
from task_review_fixtures import reviewed_import, synthetic_draft
from tequio.install import install, uninstall
from tequio.workflow import WORKFLOW_SKILLS

ROOT = Path(__file__).resolve().parents[1]

class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'brief.md').write_text('Implement actual isolated behavior with evidence and bounded ownership.\n')
        self.w = Workspace.create(self.root, 'fixture', self.root / 'brief.md')
        (self.w.path / 'analysis/requirements.md').write_text('Required behavior: preserve original inputs and demonstrate expected output and denied paths.\n')
        self.w.record('analysis')
        (self.w.path / 'plans/delivery.md').write_text('Deliver independent bounded outcomes, verify actual behavior, review evidence then integrate.\n')
        self.w.record('plan')

    def tearDown(self):
        self.temp.cleanup()

    def task(self, tid='A', writes=None, depends=None, risk='normal', reads=None):
        return {'id':tid,'title':'Write observable result','outcome':'A caller sees a persisted result','scope':'One fixture behavior','exclusions':'No outside services','sources':['briefs/brief.md','analysis/requirements.md','plans/delivery.md'],'depends_on':depends or [],'reads':reads or [],'writes':writes or [tid.lower()+'.txt'],'specialists':[],'risk':risk,'security_assessment':{'surfaces':[], 'reason':'This deterministic isolated fixture changes no security surface.'},'acceptance':['A real subprocess completes with the expected result'],'checks':[[sys.executable,'-c','print("actual check")']],'documentation':{'mode':'not-needed','paths':[],'reason':'This isolated coordinator fixture changes no product behavior or user-facing contract.'},'handoff':'Report check evidence and gaps'}

    def add(self, *tasks):
        p = self.w.path / 'tasks/import.json'
        p.write_text(json.dumps(tasks))
        reviewed_import(self.w,p)

    def report(self):
        p = self.w.path / 'reviews/report.md'
        p.write_text('Independent reviewer inspected the actual task criteria, declared subprocess check and output. The check ran and produced the expected fixture output. No findings for this bounded fixture.\n')
        return str(p.relative_to(self.w.path))

    def docs(self, claim):
        with self.w.transaction() as con:
            task=json.loads(con.execute('SELECT body FROM tasks WHERE id=?',(claim['id'],)).fetchone()[0])
        report={'summary':'Checked the fixture task sources against the executed coordinator behavior; no product documentation changes are needed for this state-only test.', 'deviations':[], 'reconciliation':[{'source':x,'actual':['brief.md'],'docs':[],'disposition':'implemented','notes':'This fixture verifies coordinator state transitions rather than changing a product interface.'} for x in task['sources']]}
        p=self.w.path/('reviews/'+claim['id']+'-docs.json');p.write_text(json.dumps(report))
        return self.w.document(claim['id'],claim['token'],str(p.relative_to(self.w.path)))

    def finish(self, claim, security=False):
        self.assertTrue(self.w.verify(claim['id'], claim['token'])['passed'])
        self.docs(claim)
        self.w.review(claim['id'], claim['token'], 'reviewer', 'correctness', self.report(), [])
        if security:
            self.w.review(claim['id'], claim['token'], 'attacker', 'security', self.report(), [])
        return self.w.complete(claim['id'], claim['token'], 'Verified fixture outcome')

    def test_real_checks_and_completion(self):
        self.add(self.task())
        c = self.w.claim('writer')
        self.finish(c)
        self.assertEqual(self.w.status()['tasks'][0]['status'], 'done')
        self.assertFalse(self.w.status()['tasks'][0]['dispatchable'])

    def test_concurrent_claim_once(self):
        self.add(self.task())
        def claim(i):
            try: return Workspace(self.root,'fixture').claim('writer'+str(i))['id']
            except Error: return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(claim, range(6)))
        self.assertEqual(results.count('A'), 1)

    def test_dependencies_and_conflicts(self):
        self.add(self.task('A', ['src']), self.task('B', ['src/child.py']), self.task('C', ['other.py'], ['A']))
        a = self.w.claim('writer','A')
        with self.assertRaises(Error): self.w.claim('writer2','B')
        with self.assertRaises(Error): self.w.claim('writer2','C')
        self.finish(a)
        self.assertEqual(self.w.claim('writer3','C')['id'],'C')

    def test_read_write_conflict_and_parallel_independent(self):
        self.add(self.task('A',['src']), self.task('B',['b.txt'],reads=['src']), self.task('C',['c.txt']))
        self.w.claim('one','A')
        with self.assertRaises(Error): self.w.claim('two','B')
        self.assertEqual(self.w.claim('three','C')['id'],'C')

    def test_stale_content_not_mtime(self):
        self.add(self.task())
        p=self.w.path/'briefs/brief.md'; stat=p.stat();p.write_text('Changed requirements.');os.utime(p,ns=(stat.st_atime_ns,stat.st_mtime_ns))
        with self.assertRaises(Error):self.w.claim('writer')
        self.assertIn('analysis',self.w.status()['stale_phases'])

    def test_tokens_and_expired_lease(self):
        self.add(self.task());c=self.w.claim('writer')
        with self.assertRaises(Error):self.w.verify('A','fake')
        with self.assertRaises(Error):self.w.recover('A','I have not inspected live owner')
        with sqlite3.connect(self.w.path/'state.sqlite3') as con:con.execute('UPDATE tasks SET lease=?',(time.time()-1,))
        with self.assertRaises(Error):self.w.verify('A',c['token'])
        self.w.recover('A','Verified the fixture worker is stopped; preserve evidence and retry')
        self.assertEqual(self.w.claim('new')['id'],'A')

    def test_review_required_and_security_distinct(self):
        self.add(self.task(risk='security'));c=self.w.claim('writer');self.w.verify('A',c['token'])
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Done')
        with self.assertRaises(Error):self.w.review('A',c['token'],'writer','correctness',self.report(),[])
        self.docs(c)
        self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Done')
        self.w.review('A',c['token'],'attacker','security',self.report(),['Boundary not demonstrated'])
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Done')

    def test_changed_code_invalidates_evidence(self):
        self.add(self.task());c=self.w.claim('writer');self.w.verify('A',c['token'])
        self.docs(c)
        self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])
        (self.root/'a.txt').write_text('Changed behavior')
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Done')

    def test_tampered_receipt_refuses(self):
        self.add(self.task());c=self.w.claim('writer');self.w.verify('A',c['token'])
        p=next((self.w.path/'evidence').glob('*.json'));s=load(p);s['passed']=False;p.write_text(json.dumps(s))
        with self.assertRaises(Error):self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])

    def test_failed_timeout_and_missing_commands_not_clean(self):
        for i,argv in enumerate([[sys.executable,'-c','raise SystemExit(3)'],[sys.executable,'-c','import time;time.sleep(3)'],['/nonexistent/tequio-command']]):
            t=self.task('T'+str(i));t['checks']=[argv];self.add(t);c=self.w.claim('writer',t['id'])
            self.assertFalse(self.w.verify(t['id'],c['token'],timeout=1)['passed'])
            self.w.release(t['id'],c['token'],'Retain observed failure',blocked=True)

    def test_replan_preserves_history_and_requires_new_receipts(self):
        self.add(self.task());c=self.w.claim('writer')
        with self.assertRaises(Error):self.w.replan('Changed requirements')
        self.w.release('A',c['token'],'Replan requested');self.w.replan('Changed requirements')
        self.assertEqual(self.w.status()['tasks'][0]['status'],'superseded')
        with self.assertRaises(Error):self.add(self.task('B'))
        self.w.record('analysis');self.w.record('plan');self.add(self.task('B'))
        self.assertEqual(self.w.claim('writer')['id'],'B')

    def test_draft_not_dispatchable_and_cycles_rejected(self):
        t=synthetic_draft(self.task());self.add(t)
        with self.assertRaises(Error):self.w.claim('writer')
        with self.assertRaises(Error):self.add(self.task('B',depends=['C']),self.task('C',depends=['B']))

    def test_path_traversal_and_symlink_rejected(self):
        for path in ['../out','/tmp/out','.tequio/secret','.git/config','src/*.py']:
            with self.subTest(path=path), self.assertRaises(Error):self.add(self.task(writes=[path]))
        (self.root/'alias').symlink_to(self.root/'safe')
        with self.assertRaises(Error):self.add(self.task(writes=['alias/file']))

    def test_resume_read_only_and_checkpoint_drift(self):
        self.add(self.task());self.w.checkpoint('Fixture prepared','Claim A')
        before=(self.w.path/'state.sqlite3').read_bytes();self.assertFalse(self.w.resume()['project_changed']);self.assertEqual(before,(self.w.path/'state.sqlite3').read_bytes())
        (self.root/'new.txt').write_text('external edit');self.assertTrue(self.w.resume()['project_changed'])

class Installation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'AGENTS.md').write_text('Owner instructions remain intact\n')
        (self.root/'.gitignore').write_text('existing-rule\n')
    def tearDown(self):self.temp.cleanup()
    def test_install_upgrade_uninstall_isolated(self):
        result=install(ROOT,self.root)
        self.assertGreater(result['files'],30)
        self.assertEqual((self.root/'AGENTS.md').read_text(),'Owner instructions remain intact\n')
        command=[sys.executable,str(self.root/'bin/tequio'),'--help']
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
        install(ROOT,self.root)
        self.assertEqual((self.root/'.gitignore').read_text().count('# BEGIN TEQUIO'),1)
        evidence=self.root/'.tequio/workspaces/retained.txt';evidence.parent.mkdir(parents=True);evidence.write_text('Private evidence')
        uninstall(self.root)
        self.assertTrue(evidence.exists());self.assertTrue((self.root/'AGENTS.md').exists());self.assertFalse((self.root/'bin/tequio').exists())
    def test_collision_has_no_side_effect(self):
        p=self.root/'.agents/skills/tequio-build/SKILL.md';p.parent.mkdir(parents=True);p.write_text('Existing skill')
        with self.assertRaises(Error):install(ROOT,self.root)
        self.assertFalse((self.root/'.tequio').exists())
        self.assertEqual(p.read_text(),'Existing skill')
        install(ROOT,self.root,prefix='tq-')
        self.assertTrue((self.root/'.agents/skills/tq-tequio-build/SKILL.md').exists())
    def test_modified_owned_file_refuses_upgrade_uninstall(self):
        install(ROOT,self.root);p=self.root/'.agents/skills/tequio-build/SKILL.md';p.write_text('Owner customization')
        with self.assertRaises(Error):install(ROOT,self.root)
        with self.assertRaises(Error):uninstall(self.root)
        self.assertEqual(p.read_text(),'Owner customization')
    def test_symlink_destination_refuses(self):
        (self.root/'.tequio').symlink_to(self.root/'outside')
        with self.assertRaises(Error):install(ROOT,self.root)

if __name__=='__main__':unittest.main()

class ReviewRegressions(unittest.TestCase):
    setUp = Lifecycle.setUp
    tearDown = Lifecycle.tearDown
    task = Lifecycle.task
    add = Lifecycle.add
    report = Lifecycle.report
    finish = Lifecycle.finish
    docs = Lifecycle.docs
    def test_dependency_output_drift_blocks_dependent(self):
        self.add(self.task('A',['a.txt']),self.task('B',['b.txt'],['A']))
        (self.root/'a.txt').write_text('Reviewed result')
        a=self.w.claim('writer','A');self.finish(a)
        (self.root/'a.txt').write_text('Broken result')
        with self.assertRaises(Error): self.w.claim('writer2','B')

    def test_conflicting_other_workspace_claim_refused(self):
        peer=Workspace.create(self.root,'peer',self.root/'brief.md')
        (peer.path/'analysis/requirements.md').write_text('Peer requirements')
        peer.record('analysis');(peer.path/'plans/delivery.md').write_text('Peer plan');peer.record('plan')
        p=peer.path/'tasks/import.json';p.write_text(json.dumps([self.task('PEER',['shared'])]));reviewed_import(peer,p)
        self.add(self.task('A',['shared/one.py']));self.w.claim('one','A')
        with self.assertRaises(Error):peer.claim('two','PEER')

    def test_timeout_terminates_spawned_child(self):
        code='import subprocess,sys,time; subprocess.Popen([sys.executable,"-c", "import time;from pathlib import Path;time.sleep(2);Path(\"late.txt\").write_text(\"late\")"]);time.sleep(10)'
        task=self.task();task['checks']=[[sys.executable,'-c',code]];self.add(task);c=self.w.claim('writer')
        self.assertFalse(self.w.verify('A',c['token'],timeout=1)['passed'])
        time.sleep(1.5);self.assertFalse((self.root/'late.txt').exists())

class InstallerRegressions(unittest.TestCase):
    setUp = Installation.setUp
    tearDown = Installation.tearDown
    def test_installed_self_upgrade_refuses_without_deleting_runtime(self):
        install(ROOT,self.root)
        before=(self.root/'.tequio/runtime/tequio/core.py').read_bytes()
        p=subprocess.run([sys.executable,str(self.root/'bin/tequio'),'install',str(self.root)],capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertIn('Incomplete source',p.stderr)
        self.assertEqual(before,(self.root/'.tequio/runtime/tequio/core.py').read_bytes())
        self.assertEqual(subprocess.run([sys.executable,str(self.root/'bin/tequio'),'--help'],capture_output=True).returncode,0)
    def test_invalid_source_refuses_without_changes(self):
        install(ROOT,self.root);before=(self.root/'.tequio/manifest.json').read_bytes()
        with self.assertRaises(Error): install(self.root/'nonexistent',self.root)
        self.assertEqual(before,(self.root/'.tequio/manifest.json').read_bytes())
    def test_generic_empty_specialists_allowed_unknown_refused(self):
        install(ROOT,self.root);brief=self.root/'brief.md';brief.write_text('Generic project brief');w=Workspace.create(self.root,'main',brief)
        (w.path/'analysis/r.md').write_text('Real analysis');w.record('analysis');(w.path/'plans/p.md').write_text('Real plan');w.record('plan')
        t={'id':'G','title':'Generic','outcome':'Expected result','scope':'Fixture','exclusions':'Others','sources':['briefs/brief.md'],'writes':['main.py'],'checks':[[sys.executable,'-c','print(1)']],'acceptance':['Expected output'],'specialists':[],'risk':'normal','security_assessment':{'surfaces':[], 'reason':'This deterministic isolated fixture changes no security surface.'},'documentation':{'mode':'not-needed','paths':[],'reason':'This isolated coordinator fixture changes no product behavior or user-facing contract.'},'handoff':'Report evidence'}
        w.validate_task(t);t['specialists']=['imaginary-specialist']
        with self.assertRaises(Error):w.validate_task(t)

class MetadataRegression(unittest.TestCase):
    setUp=Lifecycle.setUp
    tearDown=Lifecycle.tearDown
    task=Lifecycle.task
    add=Lifecycle.add
    report=Lifecycle.report
    docs=Lifecycle.docs
    def test_executable_mode_change_invalidates_completion(self):
        p=self.root/'run.sh';p.write_text('#!/bin/sh\nexit 0\n');p.chmod(0o755)
        t=self.task();t['checks']=[['./run.sh']];self.add(t);c=self.w.claim('writer');self.w.verify('A',c['token'])
        self.docs(c)
        self.w.review('A',c['token'],'reviewer','correctness',self.report(),[])
        p.chmod(0o644)
        with self.assertRaises(Error):self.w.complete('A',c['token'],'Done')

class BundleCompleteness(unittest.TestCase):
    def test_missing_required_skill_refuses_upgrade_without_mutation(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);source=base/'source';target=base/'target';target.mkdir()
            shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('__pycache__'))
            install(ROOT,target);before=(target/'.tequio/manifest.json').read_bytes()
            (source/'skills/tequio-inspect/SKILL.md').unlink()
            with self.assertRaises(Error):install(source,target)
            self.assertEqual(before,(target/'.tequio/manifest.json').read_bytes())

class FinalReviewRegressions(unittest.TestCase):
    def test_modified_installed_executable_mode_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);install(ROOT,root);(root/'bin/tequio').chmod(0o644)
            with self.assertRaises(Error):install(ROOT,root)
            with self.assertRaises(Error):uninstall(root)
    def test_status_respects_peer_claims(self):
        helper=Lifecycle();helper.setUp()
        try:
            peer=Workspace.create(helper.root,'peer',helper.root/'brief.md')
            (peer.path/'analysis/requirements.md').write_text('Actual analysis');peer.record('analysis');(peer.path/'plans/delivery.md').write_text('Actual plan');peer.record('plan')
            task=helper.task('B',['shared']);p=peer.path/'tasks/import.json';p.write_text(json.dumps([task]));reviewed_import(peer,p)
            helper.add(helper.task('A',['shared']));helper.w.claim('one','A')
            self.assertFalse(peer.status()['tasks'][0]['dispatchable'])
        finally:helper.tearDown()

class GenericDistributionBoundary(unittest.TestCase):
    def test_bundle_refuses_accidental_project_specialist(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'source';shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('__pycache__'))
            original=(source/'bundle.json').read_bytes();private=source/'skills/private-project-specialist';private.mkdir();(private/'SKILL.md').write_text('Private project expertise')
            result=subprocess.run([sys.executable,str(source/'tools/build_bundle.py')],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('Distribution boundary',result.stderr)
            self.assertEqual((source/'bundle.json').read_bytes(),original)
    def test_installed_framework_has_only_workflows_and_generic_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);install(ROOT,root)
            names={p.name for p in (root/'.tequio/skills').iterdir()}
            self.assertEqual(names,set(WORKFLOW_SKILLS));self.assertIn('tequio-briefing',names);self.assertFalse(any(n.endswith('-specialist') for n in names))
            self.assertEqual({p.name for p in (root/'.tequio/profiles').iterdir()},{'generic.md'})

class SkillRenameUpgrade(unittest.TestCase):
    def test_upgrade_removes_obsolete_skill_alias_and_keeps_project_assets(self):
        from tequio.core import digest
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);install(ROOT,root)
            # Synthetic previous installation entry exercises manifest-owned removal.
            legacy=root/'.agents/skills/old-build/SKILL.md';legacy.parent.mkdir(parents=True);legacy.write_text('Synthetic legacy skill, owned by the old installation.')
            manifest=load(root/'.tequio/manifest.json');manifest['files']['.agents/skills/old-build/SKILL.md']=digest(legacy.read_bytes());manifest['modes']['.agents/skills/old-build/SKILL.md']=legacy.stat().st_mode & 0o777
            (root/'.tequio/manifest.json').write_text(json.dumps(manifest))
            project=root/'.agents/skills/project-owned/SKILL.md';project.parent.mkdir(parents=True);project.write_text('Private project skill')
            install(ROOT,root)
            self.assertFalse(legacy.parent.exists());self.assertEqual(project.read_text(),'Private project skill')
            self.assertTrue((root/'.agents/skills/tequio-build/SKILL.md').exists())
