"""Small synthetic outcome traces, not model behavior or billing evidence."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
import test_lifecycle as fixtures
from tequio.core import Error
from tequio.revision import Revision
from tequio.task_review import AREAS


class ProportionalFlow(unittest.TestCase):
    setUp=fixtures.Lifecycle.setUp
    tearDown=fixtures.Lifecycle.tearDown
    task=fixtures.Lifecycle.task
    add=fixtures.Lifecycle.add
    docs=fixtures.Lifecycle.docs
    report=fixtures.Lifecycle.report
    finish=fixtures.Lifecycle.finish

    def scoped(self,tid,depends=None):
        t=self.task(tid,depends=depends)
        t['freshness']={'mode':'scoped-v1','independent':True,'shared_contracts':[],'config':[],'mandatory_context':[]}
        return t

    def rows(self):
        with self.w.transaction() as c:return {r['id']:dict(r) for r in c.execute('SELECT * FROM tasks')}

    def reviewed_revision(self,p):
        rel='tasks/trace-revision.json';(self.w.path/rel).write_text(json.dumps(p))
        engine=Revision(self.w);rid=engine.prepare(rel,'synthetic-author')['revision']
        for kind in AREAS:
            r={'operation':'revision','revision':rid,'summary':'Synthetic controlled graph and history trace exercises local review machinery only; no authentic independent reviewer or model judgment is asserted.',
               'coverage':{a:'Synthetic explicit graph, immutable history and current local fixture evidence checked for '+a for a in AREAS[kind]},'findings':[]}
            report='reviews/trace-'+kind+'.json';(self.w.path/report).write_text(json.dumps(r));engine.review(rid,'synthetic-'+kind,kind,report)
        return engine,rid

    def test_three_branch_revision_reduces_definition_churn(self):
        tasks=[self.scoped('P'),self.scoped('C',['P']),self.scoped('U'),self.scoped('V',['U']),self.scoped('X'),self.scoped('Y',['X']),self.scoped('ANCHOR')]
        self.add(*tasks);self.finish(self.w.claim('fixture','ANCHOR'))
        before=self.rows();phase=self.w.inputs()
        # The broad branch runs on another real disposable database, never a saved PASS.
        from tequio.core import Workspace
        other=self.root/'broad';other.mkdir();(other/'brief.md').write_text('Synthetic independent branch comparison.')
        broad=Workspace.create(other,'trace',other/'brief.md')
        for d,f in [('analysis','requirements.md'),('plans','delivery.md')]:
            (broad.path/d/f).write_text('Synthetic current specification for independent observable task outcomes.');broad.record('analysis' if d=='analysis' else 'plan')
        from task_review_fixtures import reviewed_import
        candidate=broad.path/'tasks/import.json';candidate.write_text(json.dumps(tasks[:6]));reviewed_import(broad,candidate)
        broad.replan('Synthetic producer split using deliberate legacy broad replan.')
        with broad.transaction() as c:broad_replaced=[r[0] for r in c.execute("SELECT id FROM tasks WHERE status='superseded'")]
        broad.record('analysis');broad.record('plan')
        replacements=[self.scoped('P1'),self.scoped('P2'),self.scoped('C1',['P1','P2']),self.scoped('U1'),self.scoped('V1',['U1']),self.scoped('X1'),self.scoped('Y1',['X1'])]
        candidate.write_text(json.dumps(replacements));reviewed_import(broad,candidate)
        proposal={'version':1,'reason':'Split a synthetic producer without rewriting independent roadmap definitions.','supersede':['P'],'replacements':{'P':['P1','P2']},'tasks':replacements[:2],
                  'rebindings':[{'consumer':'C','from':['P'],'to':['P1','P2']}]}
        engine,rid=self.reviewed_revision(proposal);result=engine.apply(rid);after=self.rows()
        self.assertEqual(len(broad_replaced),6);self.assertEqual(len(result['superseded']),1)
        self.assertEqual(len(replacements),7);self.assertEqual(len(result['imported']),2)
        self.assertEqual(result['rebound'],['C']);self.assertEqual(before['C']['body'],after['C']['body'])
        for tid in ['U','V','X','Y','ANCHOR']:self.assertEqual(before[tid],after[tid])
        self.assertEqual(phase,self.w.inputs())
        self.assertEqual(self.w.review_state(after['ANCHOR'],json.loads(after['ANCHOR']['body']),None)['state'],'current')
        # Authoring operation calls: replan+2 phase records+prepare+2 reviews+import
        # versus revision prepare+2 reviews+apply. Initial shared setup excluded.
        with broad.transaction() as c:
            kinds=[r[0] for r in c.execute('SELECT kind FROM events')]
        cut=kinds.index('replanned');broad_calls=len([k for k in kinds[cut:] if k in {'replanned','phase-recorded','task-batch-prepared','task-batch-reviewed','tasks-imported'}])
        with self.w.transaction() as c:
            revision_calls=c.execute("SELECT count(*) FROM events WHERE kind IN ('revision-prepared','revision-reviewed','revision-applied')").fetchone()[0]
        self.assertEqual((broad_calls,revision_calls),(7,4))

    def test_feedback_does_not_replace_current_acceptance_after_config_change(self):
        (self.root/'policy.json').write_text('{"allowed":false}')
        t=self.scoped('A');t['freshness']['config']=['policy.json'];t['risk']='security';t['security_assessment']={'surfaces':['authorization','configuration'],'reason':'Synthetic authorization configuration changes require current correctness and security evidence.'};self.add(t)
        claim=self.w.claim('fixture','A');self.w.verify('A',claim['token']);self.docs(claim)
        self.report()  # Feedback file alone is not a registered acceptance review.
        with self.assertRaises(Error):self.w.complete('A',claim['token'],'Unregistered feedback cannot close work')
        self.w.review('A',claim['token'],'synthetic-reviewer','correctness',self.report(),[])
        self.w.review('A',claim['token'],'synthetic-security','security',self.report(),[])
        (self.root/'policy.json').write_text('{"allowed":true}')
        with self.assertRaises(Error):self.w.complete('A',claim['token'],'Changed authorization configuration needs current proof')
        self.w.verify('A',claim['token']);self.docs(claim)
        with self.assertRaises(Error):self.w.complete('A',claim['token'],'New checks/docs invalidate prior review')
        self.w.review('A',claim['token'],'synthetic-reviewer','correctness',self.report(),[])
        with self.assertRaises(Error):self.w.complete('A',claim['token'],'Fresh correctness does not substitute for current security review')
        self.w.review('A',claim['token'],'synthetic-security','security',self.report(),[])
        self.w.complete('A',claim['token'],'Current fixture behavior, reconciliation and both reviews obtained')

    def adapter(self,broken):
        p=self.root/'product';p.mkdir(exist_ok=True)
        (p/'adapter.py').write_text('import multiprocessing\n'
            +'def context():return multiprocessing.get_context('+repr('spawn' if broken else 'fork')+')\n'
            +'def parse(value):\n    if value not in '+repr(('active','inactive') if broken else ('ready','processing'))+':raise ValueError("unsupported state")\n    return value\n')
        return p

    def probe_then_integrate(self,product,prerequisite=True,budget=2):
        if not prerequisite:return {'state':'unqualified','reason':'missing-prerequisite'}
        if budget<2:return {'state':'unqualified','reason':'resource-ceiling'}
        probe=subprocess.run([sys.executable,'-c','import adapter;assert adapter.context().get_start_method()=="fork";assert adapter.parse("ready")=="ready"'],cwd=product,capture_output=True)
        if probe.returncode:return {'state':'needs-correction','probe_exit':probe.returncode}
        # This local file stands for an expensive effect, not an actual service.
        result=subprocess.run([sys.executable,'-c','import adapter;from pathlib import Path;assert adapter.parse("ready")=="ready";Path("effect-count").write_text(str(int(Path("effect-count").read_text())+1) if Path("effect-count").exists() else "1")'],cwd=product,capture_output=True)
        return {'state':'supported' if result.returncode==0 else 'needs-correction','integration_exit':result.returncode}

    def test_product_boundary_probe_prevents_effect_until_corrected(self):
        product=self.adapter(True)
        self.assertEqual(self.probe_then_integrate(product)['state'],'needs-correction')
        self.assertFalse((product/'effect-count').exists())
        # Avoid same-second bytecode reuse for the deliberately edited temporary module.
        import shutil
        shutil.rmtree(product/'__pycache__',ignore_errors=True)
        product=self.adapter(False)
        self.assertEqual(self.probe_then_integrate(product)['state'],'supported')
        self.assertEqual((product/'effect-count').read_text(),'1')
        adverse=subprocess.run([sys.executable,'-c','import adapter;adapter.parse("unknown")'],cwd=product,capture_output=True)
        self.assertNotEqual(adverse.returncode,0)
        self.assertEqual((product/'effect-count').read_text(),'1')

    def test_missing_input_and_ceiling_stay_unqualified(self):
        product=self.adapter(False)
        self.assertEqual(self.probe_then_integrate(product,prerequisite=False),{'state':'unqualified','reason':'missing-prerequisite'})
        self.assertEqual(self.probe_then_integrate(product,budget=0),{'state':'unqualified','reason':'resource-ceiling'})
        self.assertFalse((product/'effect-count').exists())

    def test_complete_capability_observation_can_rule_out_a_requirement(self):
        product=self.adapter(False)
        positive=subprocess.run([sys.executable,'-c','import adapter;assert adapter.parse("ready")=="ready"'],cwd=product)
        required=subprocess.run([sys.executable,'-c','import adapter;adapter.parse("delayed")'],cwd=product,capture_output=True)
        self.assertEqual(positive.returncode,0);self.assertNotEqual(required.returncode,0)
        self.assertIn(b'unsupported state',required.stderr)
        decision='unsupported-required-state' if positive.returncode==0 and required.returncode!=0 and b'unsupported state' in required.stderr else 'unqualified'
        self.assertEqual(decision,'unsupported-required-state')
        self.assertFalse((product/'effect-count').exists())


if __name__=='__main__':unittest.main()
