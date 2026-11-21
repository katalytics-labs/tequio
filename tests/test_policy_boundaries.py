"""Temporary policy/functional boundary mechanics; all reviewer actors are synthetic.

Actual subprocesses inspect current product/policy bytes. These fixtures establish
content binding and lifecycle behavior, never genuine independent review.
"""
import hashlib
import json
import sys
import unittest
import test_lifecycle as fixture
from tequio.core import Error
from tequio.revision import Revision
from tequio.task_review import AREAS


class PolicyBoundaries(unittest.TestCase):
    setUp = fixture.Lifecycle.setUp
    tearDown = fixture.Lifecycle.tearDown
    task = fixture.Lifecycle.task
    add = fixture.Lifecycle.add
    docs = fixture.Lifecycle.docs
    report = fixture.Lifecycle.report
    finish = fixture.Lifecycle.finish

    def scoped(self, tid, writes, reads=(), depends=()):
        task = self.task(tid, writes=writes, reads=list(reads), depends=list(depends))
        task['freshness'] = {'mode': 'scoped-v1', 'independent': True,
                             'shared_contracts': [], 'config': [], 'mandatory_context': []}
        return task

    def setup_product(self):
        (self.root / 'src').mkdir(); (self.root / 'docs').mkdir(); (self.root / 'config').mkdir()
        (self.root / 'src/component.py').write_text('def result():\n    return 42\n')
        (self.root / 'docs/interface.md').write_text('result() returns the integer 42.\n')
        (self.root / 'config/runtime.json').write_text('{"enabled": true}\n')
        self.policy = b'.tequio/\n.agents/\nsecrets/\n'
        (self.root / '.gitignore').write_bytes(self.policy)
        functional = self.scoped('FUNCTION', ['src/component.py', 'docs/interface.md'], ['config/runtime.json'])
        functional['checks'] = [[sys.executable, '-c',
            "import runpy,json,pathlib; m=runpy.run_path('src/component.py'); assert m['result']()==42; assert json.loads(pathlib.Path('config/runtime.json').read_text())['enabled']; assert 'integer 42' in pathlib.Path('docs/interface.md').read_text()"]]
        consumer = self.scoped('CONSUMER', ['consumer.txt'], ['src/component.py', 'docs/interface.md'], ['FUNCTION'])
        consumer['checks'] = [[sys.executable, '-c', "import runpy; assert runpy.run_path('src/component.py')['result']()==42"]]
        policy = self.policy_task('POLICY', self.policy)
        integration = self.scoped('INTEGRATE', ['integrated.txt'], ['src/component.py', '.gitignore'], ['CONSUMER', 'POLICY'])
        integration['checks'] = [[sys.executable, '-c', "import runpy,pathlib; assert runpy.run_path('src/component.py')['result']()==42; assert 'secrets/' in pathlib.Path('.gitignore').read_text().splitlines()"]]
        self.add(functional, consumer, policy, integration)
        return functional, consumer, policy, integration

    def policy_task(self, tid, expected):
        task = self.scoped(tid, ['.gitignore'])
        task['risk'] = 'security'
        task['security_assessment'] = {'surfaces': ['data-export', 'configuration'],
            'reason': 'Synthetic exact ignore policy check protects private runtime and secret paths.'}
        task['checks'] = [[sys.executable, '-c',
            "import hashlib,pathlib; raw=pathlib.Path('.gitignore').read_bytes(); assert hashlib.sha256(raw).hexdigest()==" + repr(hashlib.sha256(expected).hexdigest()) + "; assert {'.tequio/','.agents/','secrets/'} <= set(raw.decode().splitlines())"]]
        return task

    def rows(self):
        with self.w.transaction() as con:
            return {r['id']: dict(r) for r in con.execute('SELECT * FROM tasks')}

    def current(self, tid):
        row = self.rows()[tid]
        return self.w.review_state(row, json.loads(row['body']), None)['state'] == 'current'

    def complete(self, tid, security=False):
        self.finish(self.w.claim('synthetic-worker', tid), security=security)

    def rebind(self):
        proposal = {'version': 1, 'reason': 'Synthetic completed policy successor requires fresh exact-byte privacy proof.',
            'supersede': [], 'replacements': {}, 'tasks': [],
            'rebindings': [{'consumer': 'INTEGRATE', 'from': ['CONSUMER', 'POLICY'], 'to': ['CONSUMER', 'POLICY-NEXT']}]}
        relative = 'tasks/policy-revision.json'
        (self.w.path / relative).write_text(json.dumps(proposal))
        gate = Revision(self.w); rid = gate.prepare(relative, 'synthetic-author')['revision']
        for kind in AREAS:
            report = 'reviews/policy-revision-' + kind + '.json'
            (self.w.path / report).write_text(json.dumps({'operation': 'revision', 'revision': rid,
                'summary': 'Synthetic fixture checks explicit policy successor lineage, exact byte requirements and unchanged functional dependency; no actual independent assessment is represented.',
                'coverage': {area: 'Synthetic local control inspects declarations and bounded current evidence for ' + area for area in AREAS[kind]}, 'findings': []}))
            gate.review(rid, 'synthetic-' + kind, kind, report)
        return gate.apply(rid)

    def test_policy_change_preserves_functional_proof_and_requires_current_successor(self):
        self.setup_product()
        self.complete('FUNCTION'); self.complete('CONSUMER'); self.complete('POLICY', security=True)
        before = self.rows()
        refs = {tid: json.loads(before[tid]['checks']) for tid in ('FUNCTION', 'CONSUMER', 'POLICY')}
        receipts = {tid: self.w.receipt(ref) for tid, ref in refs.items()}
        new_policy = self.policy + b'private-cache/\n'
        (self.root / '.gitignore').write_bytes(new_policy)
        self.assertTrue(self.current('FUNCTION')); self.assertTrue(self.current('CONSUMER'))
        self.assertFalse(self.current('POLICY'))
        with self.assertRaises(Error): self.w.claim('synthetic-worker', 'INTEGRATE')
        successor = self.policy_task('POLICY-NEXT', new_policy)
        successor['outcome'] = 'Successor to historical POLICY verifies current exact private-path protections.'
        self.add(successor)
        result = self.rebind()
        self.assertEqual(result['superseded'], []); self.assertEqual(result['imported'], [])
        self.assertEqual(result['rebound'], ['INTEGRATE'])
        after = self.rows()
        for tid in ('FUNCTION', 'CONSUMER', 'POLICY'):
            self.assertEqual(before[tid], after[tid])
            self.assertEqual(receipts[tid], self.w.receipt(refs[tid]))
        self.assertEqual(before['INTEGRATE']['body'], after['INTEGRATE']['body'])
        claim = self.w.claim('synthetic-worker', 'POLICY-NEXT')
        # The successor command reads exact bytes again: even a valid privacy list
        # with different content fails; no previous PASS/result can substitute.
        (self.root / '.gitignore').write_bytes(new_policy + b'# changed after claim\n')
        self.assertFalse(self.w.verify('POLICY-NEXT', claim['token'])['passed'])
        (self.root / '.gitignore').write_bytes(new_policy)
        self.finish(claim, security=True)
        self.assertTrue(self.current('POLICY-NEXT'))
        self.complete('INTEGRATE')
        self.assertTrue(self.current('INTEGRATE'))
        self.assertEqual(before['POLICY'], self.rows()['POLICY'])

    def test_functional_code_config_and_semantic_docs_all_invalidate_proof(self):
        self.setup_product(); self.complete('FUNCTION'); self.complete('CONSUMER')
        for relative, changed in [('src/component.py', 'def result():\n    return 43\n'),
                                  ('config/runtime.json', '{"enabled": false}\n'),
                                  ('docs/interface.md', 'result() now returns a string.\n')]:
            with self.subTest(path=relative):
                path = self.root / relative; original = path.read_bytes(); path.write_text(changed)
                self.assertFalse(self.current('FUNCTION'))
                consumer = json.loads(self.rows()['CONSUMER']['body'])
                with self.w.transaction() as con:
                    self.assertFalse(self.w.dependencies_current(con, consumer))
                path.write_bytes(original)
                self.assertTrue(self.current('FUNCTION'))

    def test_policy_readers_parent_overlap_and_global_producers_remain_coupled(self):
        self.setup_product()
        direct = self.scoped('POLICY-READER', ['reader.txt'], ['.gitignore'])
        # A concrete parent directory includes a policy child; root '.' itself
        # is rejected by the existing resource validator.
        (self.root / 'config/privacy.rules').write_bytes(self.policy)
        parent = self.scoped('PARENT-READER', ['parent.txt'], ['config'])
        global_task = self.task('GLOBAL')
        mixed = self.scoped('MIXED', ['mixed.txt'], depends=['GLOBAL'])
        dependent = self.scoped('POLICY-DEPENDENT', ['dependent.txt'], depends=['POLICY'])
        self.add(direct, parent, global_task, mixed, dependent)
        self.complete('POLICY', security=True); self.complete('POLICY-DEPENDENT')
        self.complete('GLOBAL'); self.complete('MIXED'); self.complete('POLICY-READER'); self.complete('PARENT-READER')
        self.assertTrue(all(self.current(tid) for tid in ('GLOBAL', 'MIXED', 'POLICY-READER', 'PARENT-READER')))
        (self.root / '.gitignore').write_bytes(self.policy + b'private-cache/\n')
        self.assertTrue(self.current('PARENT-READER'))
        for tid in ('GLOBAL', 'MIXED', 'POLICY-READER', 'POLICY-DEPENDENT'):
            with self.subTest(task=tid):
                self.assertFalse(self.current(tid))
        (self.root / 'config/privacy.rules').write_bytes(self.policy + b'private-cache/\n')
        self.assertFalse(self.current('PARENT-READER'))

    def test_exact_byte_match_does_not_excuse_missing_private_path_protection(self):
        self.setup_product()
        bad_policy = b'.tequio/\n.agents/\n'
        (self.root / '.gitignore').write_bytes(bad_policy)
        self.add(self.policy_task('UNSAFE-POLICY', bad_policy))
        claim = self.w.claim('synthetic-worker', 'UNSAFE-POLICY')
        self.assertFalse(self.w.verify('UNSAFE-POLICY', claim['token'])['passed'])
        with self.assertRaises(Error):
            self.w.complete('UNSAFE-POLICY', claim['token'], 'A matching hash alone cannot pass privacy checks.')


if __name__ == '__main__': unittest.main()
