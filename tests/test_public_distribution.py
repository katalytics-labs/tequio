import json
import hashlib
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tequio import __version__
from tequio.install import install, uninstall
ROOT=Path(__file__).resolve().parents[1]

class PublicDistribution(unittest.TestCase):
    def test_routing_skill_and_toggle_work_in_default_and_prefixed_install(self):
        from tequio.core import Workspace
        for prefix in ('','team-'):
            with self.subTest(prefix=prefix),tempfile.TemporaryDirectory() as folder:
                project=Path(folder).resolve();install(ROOT,project,prefix=prefix)
                discovery=project/'.agents/skills'/(prefix+'tequio-routing')/'SKILL.md'
                self.assertEqual(discovery.read_text().splitlines()[1],'name: '+prefix+'tequio-routing')
                record=json.loads((project/'.tequio/templates/delegation-record.json').read_text())
                self.assertEqual(record['observed']['source'],'unknown')
                self.assertIsNone(record['requested_choice']);self.assertIsNone(record['observed']['model'])
                command=[sys.executable,str(project/'bin/tequio'),'--project',str(project),'--workspace','pilot','routing']
                missing=subprocess.run(command,capture_output=True,text=True,timeout=15)
                self.assertEqual(missing.returncode,0,missing.stderr)
                self.assertFalse(json.loads(missing.stdout)['enabled'])
                self.assertFalse((project/'.tequio/workspaces').exists())
                brief=project/'brief.md';brief.write_text('Synthetic installed workspace for explicit routing configuration.')
                w=Workspace.create(project,'pilot',brief)
                enabled=subprocess.run(command+['on'],capture_output=True,text=True,timeout=15)
                self.assertEqual(enabled.returncode,0,enabled.stderr);self.assertTrue(json.loads(enabled.stdout)['enabled'])
                policy=w.path/'run-policy.json';value=json.loads(policy.read_text())
                self.assertEqual(policy.stat().st_mode&0o777,0o600)
                value['model_delegation']['available_choices']=['PRIVATE_CHOICE_MARKER']
                value['model_delegation']['routing_preferences']=[{'work':'bounded interpretation','choice':'PRIVATE_CHOICE_MARKER','reason':'PRIVATE_REASON_MARKER'}]
                policy.write_text(json.dumps(value))
                disabled=subprocess.run(command+['off'],capture_output=True,text=True,timeout=15)
                self.assertEqual(disabled.returncode,0,disabled.stderr);self.assertFalse(json.loads(disabled.stdout)['enabled'])
                after=json.loads(policy.read_text());self.assertEqual(after['model_delegation']['available_choices'],['PRIVATE_CHOICE_MARKER'])
                before=policy.read_bytes();read=subprocess.run(command,capture_output=True,text=True,timeout=15)
                self.assertEqual(read.returncode,0,read.stderr);self.assertEqual(before,policy.read_bytes())
                self.assertNotIn('PRIVATE_',read.stdout+disabled.stdout)
                base=[sys.executable,str(project/'bin/tequio'),'--project',str(project),'--workspace','pilot']
                saved=subprocess.run(base+['checkpoint','--summary','Synthetic installed policy observation','--next','Inspect current policy'],capture_output=True,text=True,timeout=15)
                self.assertEqual(saved.returncode,0,saved.stderr)
                image={str(p.relative_to(w.path)):p.read_bytes() for p in w.path.rglob('*') if p.is_file()}
                for args in [['progress'],['status'],['proof'],['resume','--summary']]:
                    observed=subprocess.run(base+args,capture_output=True,text=True,timeout=15)
                    self.assertEqual(observed.returncode,0,observed.stderr);self.assertNotIn('PRIVATE_',observed.stdout)
                self.assertEqual(image,{str(p.relative_to(w.path)):p.read_bytes() for p in w.path.rglob('*') if p.is_file()})
                after['model_delegation']['enabled']='invalid';policy.write_text(json.dumps(after));before=policy.read_bytes()
                invalid=subprocess.run(command+['on'],capture_output=True,text=True,timeout=15)
                self.assertEqual(invalid.returncode,2);self.assertEqual(before,policy.read_bytes())
                damaged=subprocess.run(base+['resume','--summary'],capture_output=True,text=True,timeout=15)
                self.assertEqual(damaged.returncode,0,damaged.stderr)
                self.assertEqual(json.loads(damaged.stdout)['context']['policy']['state'],'invalid')
                self.assertNotIn('PRIVATE_',damaged.stdout);self.assertEqual(before,policy.read_bytes())


    def test_license_is_in_bundle_and_installed_snapshot(self):
        manifest=json.loads((ROOT/'bundle.json').read_text())
        self.assertIn('LICENSE',manifest['files'])
        with tempfile.TemporaryDirectory() as temp:
            install(ROOT,temp)
            self.assertEqual((Path(temp)/'.tequio/LICENSE').read_bytes(),(ROOT/'LICENSE').read_bytes())
            self.assertEqual(json.loads((Path(temp)/'.tequio/manifest.json').read_text())['version'], __version__)
    def test_reproducible_example_stops_honestly_at_review(self):
        process=subprocess.run([sys.executable,str(ROOT/'examples/quickstart/run_demo.py')],capture_output=True,text=True,timeout=60)
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)
        self.assertIn('review-pending',process.stdout)
        self.assertIn('completion refused',process.stdout)

    def test_briefing_installs_with_default_and_custom_prefix(self):
        for prefix in ('', 'team-'):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as temp:
                project=Path(temp)
                install(ROOT,project,prefix=prefix)
                discovery=project/'.agents/skills'/(prefix+'tequio-briefing')/'SKILL.md'
                self.assertIn('name: '+prefix+'tequio-briefing',discovery.read_text())
                reference=(project/'.tequio/skills/tequio-briefing/SKILL.md').read_text()
                self.assertIn('name: tequio-briefing', reference)
                self.assertIn('$'+prefix+'tequio-explore', reference)
                self.assertIn('$'+prefix+'tequio-explore',discovery.read_text())
                if not prefix:
                    self.assertEqual(reference,(ROOT/'skills/tequio-briefing/SKILL.md').read_text())

    def test_synthetic_previous_inventory_upgrade_adds_briefing_preserves_draft(self):
        # Synthetic old inventory tests upgrade mechanics, not a historical release archive.
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);source=base/'source';project=base/'project';project.mkdir()
            shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('.git','__pycache__','.tequio','.agents'))
            shutil.rmtree(source/'skills/tequio-briefing')
            workflow=source/'src/tequio/workflow.py'
            workflow.write_text(workflow.read_text().replace("'brief': 'tequio-briefing', ",''))
            manifest=json.loads((source/'bundle.json').read_text())
            del manifest['files']['skills/tequio-briefing/SKILL.md']
            manifest['files']['src/tequio/workflow.py']=hashlib.sha256(workflow.read_bytes()).hexdigest()
            (source/'bundle.json').write_text(json.dumps(manifest))
            install(source,project)
            self.assertFalse((project/'.agents/skills/tequio-briefing').exists())
            draft=project/'.tequio/intake/idea/brief.md';draft.parent.mkdir(parents=True);draft.write_text('Owner draft and unresolved intent')
            install(ROOT,project)
            self.assertTrue((project/'.agents/skills/tequio-briefing/SKILL.md').is_file())
            self.assertEqual(draft.read_text(),'Owner draft and unresolved intent')
            self.assertEqual(json.loads((project/'.tequio/manifest.json').read_text())['version'],__version__)



    def test_prefixed_instruction_tokens_both_trees_and_owned_upgrade(self):
        from tequio.core import Error
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);source=base/'source';project=base/'project';project.mkdir()
            shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('.git','__pycache__','.tequio','.agents'))
            extra=source/'skills/tequio-design/references/tokens.md';extra.parent.mkdir(exist_ok=True)
            extra.write_text('$tequio-tasks `$tequio-build` $tequio-check-extra $team-tequio-check $OTHER .tequio/skills/tequio-tasks/SKILL.md')
            design=source/'skills/tequio-design/SKILL.md'
            design.write_bytes(design.read_bytes().replace(b'\n', b'\r\n'))
            manifest=json.loads((source/'bundle.json').read_text())
            manifest['files'][str(design.relative_to(source))]=hashlib.sha256(design.read_bytes()).hexdigest()
            manifest['files'][str(extra.relative_to(source))]=hashlib.sha256(extra.read_bytes()).hexdigest()
            (source/'bundle.json').write_text(json.dumps(manifest))
            original={k:(source/k).read_bytes() for k in manifest['files']}
            unrelated=project/'.agents/skills/tequio-tasks/SKILL.md';unrelated.parent.mkdir(parents=True);unrelated.write_text('Unrelated owner skill')
            for _ in range(2):
                install(source,project,'team-')
                self.assertIn('name: team-tequio-design\n',(project/'.agents/skills/team-tequio-design/SKILL.md').read_text())
                self.assertIn(b'\r\n',(project/'.tequio/skills/tequio-design/SKILL.md').read_bytes())
                for folder in ['.agents/skills/team-tequio-design','.tequio/skills/tequio-design']:
                    self.assertIn('$team-tequio-tasks',(project/folder/'SKILL.md').read_text())
                    text=(project/folder/'references/tokens.md').read_text()
                    self.assertEqual(text,'$team-tequio-tasks `$team-tequio-build` $tequio-check-extra $team-tequio-check $OTHER .tequio/skills/tequio-tasks/SKILL.md')
                owned=json.loads((project/'.tequio/manifest.json').read_text())
                for path,h in owned['files'].items(): self.assertEqual(hashlib.sha256((project/path).read_bytes()).hexdigest(),h)
                self.assertEqual(original,{k:(source/k).read_bytes() for k in original})
            changed=project/'.tequio/skills/tequio-design/references/tokens.md';saved=changed.read_bytes();changed.write_bytes(saved+b' owner edit')
            with self.assertRaises(Error): install(source,project,'team-')
            with self.assertRaises(Error): uninstall(project)
            changed.write_bytes(saved);uninstall(project)
            self.assertEqual(unrelated.read_text(),'Unrelated owner skill')

if __name__=='__main__':unittest.main()
