"""Synthetic configuration controls, never model selection/identity attestation."""
import concurrent.futures
import copy
import itertools
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch
import test_lifecycle as fixture
from tequio.core import Error
from tequio import run_context as context


class ModelDelegation(unittest.TestCase):
    setUp = fixture.Lifecycle.setUp
    tearDown = fixture.Lifecycle.tearDown
    task = fixture.Lifecycle.task
    add = fixture.Lifecycle.add
    docs = fixture.Lifecycle.docs
    report = fixture.Lifecycle.report
    finish = fixture.Lifecycle.finish

    def base(self):
        value = json.loads((fixture.ROOT / 'templates/run-policy.json').read_bytes())
        value.pop('model_delegation', None)
        return value

    def write(self, value):
        path = self.w.path / 'run-policy.json'
        path.write_text(json.dumps(value)); return path

    def configured(self):
        value = self.base(); value['model_delegation'] = context.model_delegation_defaults()
        return value

    def route(self, action='status'):
        return context.routing(self.root, 'fixture', action)

    def test_optional_validator_modes_fallbacks_and_caps(self):
        default = context.model_delegation_defaults()
        self.assertTrue(context.valid_model_delegation(default))
        for correctness, security, unavailable, preferred in itertools.product(
                ('optional', 'preferred', 'required'), ('optional', 'preferred', 'required'),
                ('host-default', 'stop'), ('record-and-continue', 'review-pending')):
            value = copy.deepcopy(default)
            value['review_diversity'].update(correctness=correctness, security=security)
            value['fallback'].update(unavailable_choice=unavailable, unmet_preferred_diversity=preferred)
            self.assertTrue(context.valid_model_delegation(value))
        value = copy.deepcopy(default)
        value['available_choices'] = ['é' * 256] + ['option-' + str(i) for i in range(31)]
        value['routing_preferences'] = [{'work': str(i) + 'w' * 1000, 'choice': value['available_choices'][0], 'reason': 'r' * 1024} for i in range(32)]
        self.assertTrue(context.valid_model_delegation(value))
        value['available_choices'].append('overflow')
        self.assertFalse(context.valid_model_delegation(value))

    def test_invalid_supplied_blocks_disabled_or_enabled_never_ignored(self):
        default = context.model_delegation_defaults()
        invalid = [None, [], {}, {**default, 'version': True}, {**default, 'enabled': 1},
                   {**default, 'extra': 'not allowed'}]
        for choices in [['same', 'same'], [' padded'], ['newline\n'], ['\x00'], ['x' * 257], [1], {}]:
            invalid.append({**default, 'available_choices': choices})
        for preferences in [[{'work': 'w', 'choice': 'missing', 'reason': 'r'}],
                            [{'work': 'w', 'choice': 'ok', 'reason': 'r'}] * 2,
                            [{'work': 'w', 'choice': 'ok', 'reason': 'r', 'extra': True}],
                            [{'work': 'w', 'choice': 'ok', 'reason': 'r' * 1025}],
                            [{'work': '\t', 'choice': 'ok', 'reason': 'r'}]]:
            invalid.append({**default, 'available_choices': ['ok'], 'routing_preferences': preferences})
        invalid.extend([{**default, 'review_diversity': {'basis': 'provider', 'correctness': 'optional', 'security': 'preferred'}},
                        {**default, 'review_diversity': {**default['review_diversity'], 'override': True}},
                        {**default, 'fallback': {**default['fallback'], 'unavailable_choice': 'retry-forever'}}])
        for block in invalid:
            for disabled in (False, True):
                with self.subTest(block=block, disabled=disabled):
                    block = copy.deepcopy(block)
                    if isinstance(block, dict) and disabled and type(block.get('enabled')) is bool: block['enabled'] = False
                    self.assertFalse(context.valid_model_delegation(block))
                    value = self.base(); value['model_delegation'] = block
                    path = self.write(value); raw = path.read_bytes()
                    self.assertEqual(context.policy(self.w.path)['state'], 'invalid')
                    self.assertIsNone(self.route()['enabled'])
                    for action in ('on', 'off'):
                        with self.assertRaises(Error): self.route(action)
                        self.assertEqual(raw, path.read_bytes())

    def test_legacy_canonical_digest_unknown_fields_and_large_observation_unchanged(self):
        value = self.base(); value['private-extra'] = 'marker' * 250000
        path = self.write(value)
        self.assertEqual(context.policy(self.w.path), {'state': 'valid', 'digest': context.digest(value)})
        self.assertEqual(self.route()['policy_state'], 'unreadable')
        value['private-extra'] = 'private-markers'
        path.write_text(json.dumps(value, indent=4, sort_keys=True))
        before = context.policy(self.w.path)
        path.write_text(json.dumps(value, separators=(',', ':')))
        self.assertEqual(before, context.policy(self.w.path))
        value['model_delegation'] = context.model_delegation_defaults(); self.write(value)
        self.assertNotEqual(before['digest'], context.policy(self.w.path)['digest'])

    def test_missing_status_off_noop_and_new_conservative_policy_mode(self):
        files = {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()}
        self.assertFalse(context.routing(self.root, None)['enabled'])
        self.assertFalse(self.route()['configured'])
        self.assertFalse(self.route('off')['changed'])
        self.assertEqual(files, {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()})
        with self.assertRaises(Error): context.routing(self.root, None, 'on')
        with self.assertRaises(Error): context.routing(self.root, 'absent', 'on')
        result = self.route('on'); self.assertTrue(result['changed']); self.assertIsNone(result['previous_policy_digest'])
        path = self.w.path / 'run-policy.json'; value = json.loads(path.read_bytes())
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(value['mode'], 'next-chunk'); self.assertEqual(value['tasks'], [])
        self.assertFalse(any(value[k] for k in ('allow_local_commits', 'allow_local_merges', 'allow_push')))
        self.assertEqual(value['parallel_writers'], 1)
        self.assertIn('no execution authorization', value['scope'])

    def test_toggle_preserves_preferences_unknown_content_modes_and_noop_bytes(self):
        value = self.configured(); block = value['model_delegation']
        block['available_choices'] = ['private-option-marker']
        block['routing_preferences'] = [{'work': 'private-work-marker', 'choice': 'private-option-marker', 'reason': 'private-rationale-marker'}]
        block['review_diversity']['security'] = 'required'; value['unrelated-private'] = {'keep': [1, 2]}
        path = self.write(value); os.chmod(path, 0o640)
        raw = path.read_bytes()
        self.assertFalse(self.route('on')['changed']); self.assertEqual(raw, path.read_bytes())
        result = self.route('off'); self.assertFalse(result['enabled']); self.assertTrue(result['changed'])
        expected = copy.deepcopy(value); expected['model_delegation']['enabled'] = False
        self.assertEqual(json.loads(path.read_bytes()), expected)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
        raw = path.read_bytes(); self.assertFalse(self.route('off')['changed']); self.assertEqual(raw, path.read_bytes())
        self.assertTrue(self.route('on')['enabled']); self.assertEqual(json.loads(path.read_bytes()), value)
        self.assertNotIn('private-', json.dumps(result))
        self.assertEqual(set(result), {'schema_version', 'workspace', 'configured', 'enabled', 'policy_state', 'changed', 'policy_digest', 'previous_policy_digest'})

    def test_absent_block_on_preserves_base_off_does_not_add_block(self):
        value = self.base(); value['unknown'] = {'a': True}; path = self.write(value)
        raw = path.read_bytes(); self.assertFalse(self.route('off')['changed']); self.assertEqual(raw, path.read_bytes())
        self.route('on'); actual = json.loads(path.read_bytes()); actual.pop('model_delegation')
        self.assertEqual(actual, value)

    def test_symlink_fifo_directory_and_oversize_are_nonblocking_unreadable(self):
        path = self.w.path / 'run-policy.json'; outside = self.root / 'outside-policy'; outside.write_text(json.dumps(self.configured()))
        for kind in ('symlink', 'fifo', 'directory', 'oversize'):
            with self.subTest(kind=kind):
                if kind == 'symlink': path.symlink_to(outside)
                elif kind == 'fifo': os.mkfifo(path)
                elif kind == 'directory': path.mkdir()
                else: path.write_bytes(b' ' * 1048577)
                self.assertEqual(self.route()['policy_state'], 'unreadable')
                with self.assertRaises(Error): self.route('on')
                if kind == 'directory': path.rmdir()
                else: path.unlink()
        self.assertEqual(json.loads(outside.read_bytes()), self.configured())

    def test_invalid_base_json_and_serialized_limit_refuse_without_repair(self):
        path = self.w.path / 'run-policy.json'
        for raw in (b'{broken', b'[]', b'null', json.dumps({**self.base(), 'allow_push': 1}).encode()):
            path.write_bytes(raw)
            self.assertEqual(self.route()['policy_state'], 'invalid')
            for action in ('on', 'off'):
                with self.assertRaises(Error): self.route(action)
                self.assertEqual(raw, path.read_bytes())
        value = self.base(); value['large-private-field'] = 'x' * (1048576 - 550)
        # Compute a valid near-cap source independent of incidental template prose.
        value['large-private-field'] = 'x' * (1048576 - len(json.dumps({**value, 'large-private-field': ''}, separators=(',', ':')).encode()) - 1)
        raw = json.dumps(value, separators=(',', ':')).encode(); path.write_bytes(raw)
        self.assertLessEqual(len(raw), 1048576)
        with self.assertRaisesRegex(Error, 'size limit'): self.route('on')
        self.assertEqual(raw, path.read_bytes())

    def test_deep_json_is_invalid_or_compactly_preserved_without_recursion_failure(self):
        path=self.w.path/'run-policy.json'
        raw=b'['*200000+b'0'+b']'*200000;path.write_bytes(raw)
        self.assertLess(len(raw),1048576)
        result=self.route();self.assertEqual(result['policy_state'],'invalid');self.assertIsNone(result['enabled'])
        for action in ('on','off'):
            with self.assertRaises(Error):self.route(action)
            self.assertEqual(path.read_bytes(),raw)
        # A parseable deep unrelated field must not expand quadratically by indentation.
        raw=(json.dumps(self.base())[:-1]+',"unknown_deep":'+'['*1500+'0'+']'*1500+'}').encode()
        path.write_bytes(raw)
        self.assertTrue(self.route('on')['enabled'])
        self.assertLessEqual(path.stat().st_size,1048576)
        value=json.loads(path.read_bytes())['unknown_deep'];depth=0
        while isinstance(value,list):depth+=1;value=value[0]
        self.assertEqual(depth,1500);self.assertEqual(value,0)

    def test_concurrent_toggles_share_project_coordination(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.route('on'), range(2)))
        self.assertEqual(sum(r['changed'] for r in results), 1)
        self.assertTrue(self.route()['enabled'])

    def test_detected_external_byte_and_mode_changes_refuse(self):
        import tempfile
        original = tempfile.mkstemp
        for change in ('bytes', 'mode'):
            path = self.write(self.configured()); os.chmod(path, 0o600)
            def changed(*args, **kwargs):
                result = original(*args, **kwargs)
                if change == 'bytes': path.write_text(json.dumps({**self.configured(), 'external': True}))
                else: os.chmod(path, 0o644)
                return result
            with patch('tempfile.mkstemp', changed):
                with self.assertRaisesRegex(Error, 'changed externally'): self.route('off')
            self.assertTrue(json.loads(path.read_bytes())['model_delegation']['enabled'])
            self.assertEqual(list(self.w.path.glob('.run-policy-*')), [])

    def test_failure_before_replace_retains_bytes_after_replace_reports_uncertainty(self):
        path = self.write(self.configured()); raw = path.read_bytes()
        with patch('os.replace', side_effect=OSError('synthetic prepublication failure')):
            with self.assertRaisesRegex(Error, 'inspect routing status'): self.route('off')
        self.assertEqual(raw, path.read_bytes()); self.assertEqual(list(self.w.path.glob('.run-policy-*')), [])
        original = os.fsync; calls = []
        def fail_directory(fd):
            calls.append(fd)
            if len(calls) == 2: raise OSError('synthetic postreplace directory sync failure')
            return original(fd)
        with patch('os.fsync', fail_directory):
            with self.assertRaisesRegex(Error, 'replacement may have occurred'): self.route('off')
        self.assertFalse(self.route()['enabled'])

    def test_checkpoint_resume_observes_toggle_without_rewriting_checkpoint(self):
        self.w.checkpoint('Synthetic bounded context before routing configuration.', 'Inspect explicit owner intent.')
        path = self.w.path / 'checkpoint.json'; raw = path.read_bytes()
        self.route('on')
        self.assertTrue(context.resume(self.w)['policy_changed']); self.assertEqual(raw, path.read_bytes())
        self.w.checkpoint('Synthetic bounded context with routing configured.', 'Continue within approved scope.')
        self.assertFalse(context.resume(self.w)['policy_changed'])
        self.route('off'); self.assertTrue(context.resume(self.w)['policy_changed'])

    def test_required_configuration_does_not_add_core_model_identity_gate(self):
        value = self.configured(); value['model_delegation']['review_diversity']['correctness'] = 'required'; self.write(value)
        self.add(self.task('A')); claim = self.w.claim('synthetic-implementer', 'A')
        with self.assertRaises(Error): self.w.complete('A', claim['token'], 'Requested diverse model cannot replace evidence.')
        self.w.verify('A', claim['token']); self.docs(claim)
        with self.assertRaises(Error): self.w.review('A', claim['token'], 'synthetic-implementer', 'correctness', self.report(), [])
        self.w.review('A', claim['token'], 'synthetic-independent-actor', 'correctness', self.report(), [])
        self.w.complete('A', claim['token'], 'Synthetic independent actor mechanics; actual model identity is unknown.')

    def test_security_actor_separation_remains_mandatory_when_routing_off(self):
        self.write(self.configured()); self.route('off')
        self.add(self.task('SECURITY', risk='security'))
        claim = self.w.claim('synthetic-implementer', 'SECURITY')
        self.w.verify('SECURITY', claim['token']); self.docs(claim)
        self.w.review('SECURITY', claim['token'], 'synthetic-correctness', 'correctness', self.report(), [])
        with self.assertRaises(Error):
            self.w.review('SECURITY', claim['token'], 'synthetic-correctness', 'security', self.report(), [])
        with self.assertRaises(Error):
            self.w.complete('SECURITY', claim['token'], 'Routing off does not waive separate required security review.')
        self.w.review('SECURITY', claim['token'], 'synthetic-security', 'security', self.report(), [])
        self.w.complete('SECURITY', claim['token'], 'Distinct synthetic actors satisfied ordinary evidence mechanics; models remain unknown.')

    def test_lane_status_uses_original_controller_and_mutations_refuse(self):
        from tequio.git_isolation import configure, create_lane
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'.gitignore').write_text('.tequio/\n')
        subprocess.run(['git','-C',str(self.root),'add','brief.md','.gitignore'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
        configure(self.root,True);lane=Path(create_lane(self.root,'routing-fixture')['path'])
        command=[sys.executable,str(fixture.ROOT/'bin/tequio'),'--project',str(lane),'--workspace','fixture','routing']
        read=subprocess.run(command,capture_output=True,text=True,timeout=15)
        self.assertEqual(read.returncode,0,read.stderr);self.assertEqual(json.loads(read.stdout)['workspace'],'fixture')
        for action in ['on','off']:
            refused=subprocess.run(command+[action],capture_output=True,text=True,timeout=15)
            self.assertEqual(refused.returncode,2);self.assertIn('original controller',refused.stderr)
        self.assertFalse((self.w.path/'run-policy.json').exists())
        self.assertFalse((lane/'.tequio/workspaces').exists())

    def test_cli_status_projection_and_changes(self):
        def cli(*args):
            result = subprocess.run([sys.executable, str(fixture.ROOT / 'bin/tequio'), '--project', str(self.root), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr); return json.loads(result.stdout)
        self.assertFalse(cli('routing')['configured'])
        self.assertTrue(cli('--workspace', 'fixture', 'routing', 'on')['enabled'])
        self.assertFalse(cli('--workspace', 'fixture', 'routing', 'off')['enabled'])


if __name__ == '__main__': unittest.main()
