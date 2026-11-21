"""Real CLI revision plumbing on synthetic workspaces; actors are test setup."""
import contextlib
import io
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import test_lifecycle as fixtures
from tequio.cli import main
from tequio.core import digest, Error
from tequio.task_review import AREAS


class RevisionCLI(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    docs=fixtures.Lifecycle.docs
    report=fixtures.Lifecycle.report
    finish=fixtures.Lifecycle.finish

    def call(self,*args,project=None):
        out,err=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            code=main(['--project',str(project or self.root),'--workspace','fixture',*args])
        return code,out.getvalue(),err.getvalue()

    def proposal(self):
        self.add(self.task('A'),self.task('B',depends=['A']),self.task('U'))
        a=self.task('A1');a['writes']=['a.txt']
        b=self.task('A2');b['writes']=['a2.txt']
        value={'version':1,'reason':'Split a synthetic producer and explicitly preserve unchanged consumer identity.',
               'supersede':['A'],'replacements':{'A':['A1','A2']},'tasks':[a,b],
               'rebindings':[{'consumer':'B','from':['A'],'to':['A1','A2']}]}
        (self.w.path/'tasks/revision.json').write_text(json.dumps(value));return value

    def test_preview_and_status_are_readonly_and_summary_private(self):
        self.proposal()
        before={str(p.relative_to(self.w.path)):p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()}
        code,out,err=self.call('revise','preview','--proposal','tasks/revision.json')
        self.assertEqual(code,0,err)
        self.assertNotIn('Split a synthetic',out)
        self.assertNotIn('actual check',out)
        self.assertNotIn('token',out.lower())
        after={str(p.relative_to(self.w.path)):p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
        code,out,err=self.call('revise','status','f'*64)
        self.assertEqual(code,2)
        self.assertEqual(before,{str(p.relative_to(self.w.path)):p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()})

    def test_missing_reviews_and_unsafe_proposal_refuse_without_mutation(self):
        self.proposal()
        code,out,err=self.call('revise','prepare','--proposal','tasks/revision.json','--author','synthetic-author')
        self.assertEqual(code,0,err)
        r=json.loads(out);revision=r['revision']
        with self.w.transaction() as con:before=[tuple(x) for x in con.execute('SELECT * FROM tasks ORDER BY id')]
        code,out,err=self.call('revise','apply','--revision',revision)
        self.assertEqual(code,2)
        with self.w.transaction() as con:self.assertEqual(before,[tuple(x) for x in con.execute('SELECT * FROM tasks ORDER BY id')])
        for path in ['../escape.json','/absolute.json']:
            self.assertEqual(self.call('revise','preview','--proposal',path)[0],2)

    def test_real_cli_reviews_apply_status_and_rebound_lifecycle(self):
        self.proposal()
        self.w.checkpoint('Synthetic graph baseline before revision','Run the exact reviewed proposal')
        code,out,err=self.call('revise','prepare','--proposal','tasks/revision.json','--author','synthetic-author')
        self.assertEqual(code,0,err);revision=json.loads(out)['revision']
        for kind in AREAS:
            rel='reviews/revision-'+kind+'.json'
            report={'operation':'revision','revision':revision,'summary':'Synthetic test reviewer exercises exact CLI report bindings, prospective graph and controlled failure paths; this fixture does not authenticate independent actors.',
                    'coverage':{area:'Synthetic inspected graph, history, privacy and declared current checks in isolated local fixture.' for area in AREAS[kind]},'findings':[]}
            (self.w.path/rel).write_text(json.dumps(report))
            code,out,err=self.call('revise','review',revision,'--actor','synthetic-'+kind,'--kind',kind,'--report',rel)
            self.assertEqual(code,0,err)
        self.assertEqual(self.call('revise','status',revision)[0],0)
        code,out,err=self.call('revise','apply','--revision',revision)
        self.assertEqual(code,0,err);self.assertEqual(json.loads(out)['rebound'],['B'])
        resumed=json.loads(self.call('resume','--summary')[1])
        self.assertTrue(resumed['changes']['task_scope_changed'])
        code,out,err=self.call('revise','apply','--revision',revision)
        self.assertEqual(code,0,err);self.assertTrue(json.loads(out)['already_applied'])
        self.assertEqual(json.loads(self.call('revise','status',revision)[1])['state'],'applied')
        self.finish(self.w.claim('fixture-writer','A1'))
        self.finish(self.w.claim('fixture-writer','A2'))
        claim=self.w.claim('fixture-writer','B');self.finish(claim)
        proof=json.loads(self.call('proof','B')[1])['tasks'][0]
        self.assertEqual([d['task'] for d in proof['dependencies']],['A1','A2'])
        self.assertEqual(proof['evidence'],'current')

    def test_supported_entrypoint_refuses_future_capability_marker(self):
        with self.w.transaction() as con:
            con.execute('INSERT INTO meta VALUES (?,?)',('revision-version','2'))
        code,out,err=self.call('status')
        self.assertEqual(code,2);self.assertIn('Unsupported revision',err)
        self.assertEqual(out,'')

    def test_lane_revision_mutation_refused_and_preview_uses_controller(self):
        from tequio.git_isolation import configure,create_lane
        self.proposal()
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'.gitignore').write_text('.tequio/\n')
        subprocess.run(['git','-C',str(self.root),'add','brief.md','.gitignore'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
        configure(self.root,True);lane=Path(create_lane(self.root,'revision-fixture')['path'])
        code,out,err=self.call('revise','prepare','--proposal','tasks/revision.json','--author','synthetic-author',project=lane)
        self.assertEqual(code,2);self.assertIn('original controller',err)
        code,out,err=self.call('revise','preview','--proposal','tasks/revision.json',project=lane)
        self.assertEqual(code,0,err)
        self.assertFalse((lane/'.tequio/workspaces').exists())


if __name__=='__main__':unittest.main()
