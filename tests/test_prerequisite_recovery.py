"""Synthetic evidence recovery; fixture actors are not real independent reviews."""
import json
import sys
import unittest
from unittest.mock import patch
import test_lifecycle as lifecycle
import test_revision as revision_tests
from tequio.core import Error
from tequio.revision import Revision


class Recovery(unittest.TestCase):
    setUp = lifecycle.Lifecycle.setUp
    tearDown = lifecycle.Lifecycle.tearDown
    add = lifecycle.Lifecycle.add
    docs = lifecycle.Lifecycle.docs
    finish = lifecycle.Lifecycle.finish
    report = lifecycle.Lifecycle.report
    rows = revision_tests.RevisionTests.rows
    accept = revision_tests.RevisionTests.accept

    def task(self, *args, **kwargs):
        t = lifecycle.Lifecycle.task(self, *args, **kwargs)
        t['freshness'] = {'mode':'scoped-v1', 'independent':True,
                          'shared_contracts':[], 'config':[], 'mandatory_context':[]}
        return t

    def chain(self):
        (self.root/'backend').mkdir()
        (self.root/'backend/guard').write_text('original pin')
        (self.root/'a.txt').write_text('accepted')
        a = self.task('A', reads=['backend'], risk='security')
        a['checks'] = [[sys.executable, '-c', "from pathlib import Path; assert Path('a.txt').read_text() == 'accepted'"]]
        b = self.task('B', depends=['A'])
        c = self.task('C', depends=['B'])
        self.add(a, b, c)
        self.finish(self.w.claim('synthetic-author','A'), security=True)
        self.finish(self.w.claim('synthetic-author','B'))
        return a, b

    def test_transitive_context_drift_names_root_and_supported_recovery(self):
        a,b = self.chain()
        original = self.rows()
        receipts = {str(p):p.read_bytes() for p in (self.w.path/'evidence').glob('*')}
        (self.root/'backend/guard').write_text('legitimate new pin')
        for tid in ('A','B'):
            body=json.loads(original[tid]['body'])
            self.assertEqual(body['inputs'],self.w.task_inputs(body))
            self.assertEqual(body['result_hash'],self.w.resource_hash(body['writes']))
            self.assertNotEqual(body['result_snapshot'],self.w.task_snapshot(body))
        with self.assertRaisesRegex(Error, 'dependency A.*scoped context snapshot changed'):
            self.w.claim('synthetic-consumer','C')
        waiting=next(t for t in self.w.status()['tasks'] if t['id']=='C')['waiting_on']
        self.assertTrue(any('dependency A' in x for x in waiting))
        ar={**a,'id':'AR'};br={**b,'id':'BR','depends_on':['AR']}
        self.add(ar,br)
        proposal={'version':1,'reason':'Current evidence-only successors replace stale acceptance for one unfinished consumer; historical rows remain.', 'supersede':[], 'replacements':{}, 'tasks':[], 'rebindings':[{'consumer':'C','from':['B'],'to':['BR']}]}
        self.rel='tasks/recovery.json';(self.w.path/self.rel).write_text(json.dumps(proposal));self.engine=Revision(self.w);self.accept();self.engine.apply(self.rid)
        with self.assertRaises(Error):self.w.claim('synthetic-consumer','C')
        ar_claim=self.w.claim('synthetic-author','AR')
        self.assertTrue(self.w.verify('AR',ar_claim['token'])['passed']);self.docs(ar_claim)
        self.w.review('AR',ar_claim['token'],'reviewer','correctness',self.report(),[])
        with self.assertRaises(Error):self.w.complete('AR',ar_claim['token'],'Missing mandatory security review')
        with self.assertRaises(Error):self.w.claim('synthetic-consumer','C')
        self.w.review('AR',ar_claim['token'],'attacker','security',self.report(),[])
        self.w.complete('AR',ar_claim['token'],'Fresh current proof')
        self.finish(self.w.claim('synthetic-author','BR'))
        current=self.rows()
        for tid in ('A','B'):self.assertEqual(original[tid],current[tid])
        for p,raw in receipts.items():
            from pathlib import Path
            self.assertEqual(raw,Path(p).read_bytes())
        c=self.w.claim('synthetic-consumer','C');self.w.release('C',c['token'],'Check subsequent drift')
        (self.root/'backend/guard').write_text('another drift')
        with self.assertRaisesRegex(Error,'dependency AR.*scoped context snapshot changed'):self.w.claim('synthetic-consumer','C')
        (self.root/'a.txt').write_text('bad changed output')
        with self.assertRaisesRegex(Error,'dependency AR.*owned outputs changed'):self.w.claim('synthetic-consumer','C')

    def test_changed_actual_output_fails_fresh_check(self):
        a,b=self.chain();(self.root/'a.txt').write_text('bad output')
        with self.assertRaisesRegex(Error,'dependency A.*owned outputs changed'):self.w.claim('synthetic-consumer','C')
        self.add({**a,'id':'AR'})
        c=self.w.claim('synthetic-author','AR');self.assertFalse(self.w.verify('AR',c['token'])['passed'])
        with self.assertRaises(Error):self.w.complete('AR',c['token'],'Cannot promote failed proof')

    def test_historical_specialist_not_resolved_but_live_specialist_is(self):
        historical=self.task('H'); historical['sources'].append('journal/history-source.md')
        source=self.w.path/'journal/history-source.md';source.write_text('Historical source retained in revision context.')
        self.add(historical,self.task('A'),self.task('C',depends=['A']))
        self.finish(self.w.claim('synthetic-author','H'))
        proposal={'version':1,'reason':'Rebind unfinished consumer without resolving unrelated completed specialist context.', 'supersede':[], 'replacements':{}, 'tasks':[], 'rebindings':[{'consumer':'C','from':['A'],'to':['H']}]}
        rel='tasks/context.json';(self.w.path/rel).write_text(json.dumps(proposal))
        original=self.w.specialist_bindings
        def bindings(task):
            if task['id']=='H':raise Error('Historical specialist context unavailable')
            return original(task)
        with patch.object(self.w,'specialist_bindings',side_effect=bindings):
            before=Revision(self.w).preview(rel)['revision']
            source.write_text('Historical source changes must still invalidate prepared context.')
            self.assertNotEqual(before,Revision(self.w).preview(rel)['revision'])
        def unavailable(task):
            if task['id']=='A':raise Error('Current specialist not qualified')
            return original(task)
        with patch.object(self.w,'specialist_bindings',side_effect=unavailable):
            with self.assertRaises(Error):Revision(self.w).preview(rel)
            with self.assertRaises(Error):self.w.claim('synthetic-author','A')

    def test_unavailable_dependency_fails_closed_without_private_error_prose(self):
        self.chain()
        original=self.w.resource_hash
        def unavailable(paths):
            if paths == ['a.txt']: raise OSError('PRIVATE filesystem detail')
            return original(paths)
        with patch.object(self.w,'resource_hash',side_effect=unavailable):
            with self.assertRaisesRegex(Error,'dependency A evidence unavailable or invalid') as caught:
                self.w.claim('synthetic-consumer','C')
            self.assertNotIn('PRIVATE',str(caught.exception))
