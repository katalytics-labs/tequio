"""Disposable development identity/export guards, not privacy or agent certification."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DevelopmentTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.count = 0
        self.project, self.lab = self.fixture()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, root, *args):
        return subprocess.check_output(['git', '-C', str(root), *args],
                                       env=os.environ | {'GIT_OPTIONAL_LOCKS': '0'}, stderr=subprocess.DEVNULL).decode().strip()

    def fixture(self):
        self.count += 1
        folder = self.base / str(self.count)
        project, lab = folder / 'tequio', folder / 'tequio-lab'
        project.mkdir(parents=True)
        lab.mkdir()
        files = {'.gitignore': '.tequio/\n', 'README.md': '# Fixture\n\nVersion 0.9.0.\n',
                 'CONTRIBUTING.md': 'Fixture contribution contract\n', 'LICENSE': 'Fixture notice\n',
                 'bundle.json': '{}\n', 'AGENTS.md': 'PRIVATE DEVELOPMENT GUIDANCE FIXTURE\n',
                 'src/tequio/__init__.py': '__version__ = "0.9.0"\n',
                 'skills/tequio-briefing/SKILL.md': 'Briefing fixture\n'}
        for name, text in files.items():
            path = project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.git(project, 'init', '-q', '-b', 'main')
        for name, value in {'user.name': 'Synthetic test fixture', 'user.email': 'fixture@example.invalid',
                            'remote.origin.url': 'https://example.invalid/team/tequio-dev.git',
                            'tequio.canonicalRoot': str(project), 'tequio.labPath': str(lab),
                            'tequio.expectedOrigin': 'git@example.invalid:team/tequio-dev.git',
                            'tequio.integrationBranch': 'main'}.items():
            self.git(project, 'config', '--local', name, value)
        self.git(project, 'add', *files)
        self.git(project, 'commit', '-q', '-m', 'Synthetic disposable source')
        (lab / 'layout.json').write_text(json.dumps({'schema_version': 1,
            'canonical_checkout': str(project), 'private_lab': str(lab)}))
        (lab / 'AGENTS.md').write_text('Private fixture lab guidance\n')
        return project, lab

    def snapshot(self, root):
        return {str(p.relative_to(root)): (p.stat().st_mode & 0o777, p.read_bytes())
                for p in root.rglob('*') if p.is_file() and not p.is_symlink()}

    def run_tool(self, tool, project=None, *args):
        project = project or self.project
        before = self.snapshot(project)
        result = subprocess.run([sys.executable, str(ROOT / 'tools' / tool),
                                 '--project', str(project), *args], capture_output=True, text=True)
        self.assertEqual(self.snapshot(project), before, 'Read-only tool mutated project or Git bytes')
        return result, json.loads(result.stdout)

    def test_checkout_identity_and_dirty_warning_are_read_only(self):
        result, data = self.run_tool('check_checkout.py')
        self.assertEqual(result.returncode, 0, data)
        self.assertEqual(data['issues'], [])
        self.assertEqual(data['version'], '0.9.0')
        self.assertTrue(data['briefing_skill_present'])
        self.assertTrue(data['clean'])
        (self.project / 'README.md').write_text('# Owner change\nVersion 0.9.0.\n')
        result, data = self.run_tool('check_checkout.py')
        self.assertEqual(result.returncode, 0, data)
        self.assertFalse(data['clean'])
        self.assertTrue(data['warnings'])

    def test_checkout_refuses_mismatched_or_missing_identity(self):
        cases = [('tequio.canonicalRoot', str(self.base / 'other')),
                 ('remote.origin.url', 'https://example.invalid/team/other.git'),
                 ('tequio.integrationBranch', 'other'), ('tequio.labPath', str(self.base / 'missing')),
                 ('tequio.expectedOrigin', None)]
        for key, value in cases:
            with self.subTest(key=key):
                project, _ = self.fixture()
                if value is None:
                    self.git(project, 'config', '--local', '--unset', key)
                else:
                    self.git(project, 'config', '--local', key, value)
                result, data = self.run_tool('check_checkout.py', project)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(data['issues'])
        (self.project / 'README.md').write_text('Version 0.8.0.\n')
        result, data = self.run_tool('check_checkout.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any('version' in issue for issue in data['issues']))

    def test_missing_repository_never_initializes_or_repairs(self):
        folder = self.base / 'not-a-repository'
        folder.mkdir()
        result, data = self.run_tool('check_checkout.py', folder)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(data['issues'])
        self.assertEqual(list(folder.iterdir()), [])

    def test_credential_bearing_remote_is_not_echoed(self):
        secret = 'SYNTHETIC-DO-NOT-ECHO'
        self.git(self.project, 'config', '--local', 'remote.origin.url',
                 'https://fixture:' + secret + '@example.invalid/team/tequio-dev.git')
        result, data = self.run_tool('check_checkout.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertIsNone(data['origin_identity'])

    def test_public_inventory_reads_committed_bytes_omits_development_guidance(self):
        head = self.git(self.project, 'rev-parse', 'HEAD')
        committed = (self.project / 'README.md').read_bytes()
        (self.project / 'README.md').write_text('UNCOMMITTED PRIVATE FIXTURE TEXT\n')
        result, data = self.run_tool('public_inventory.py', None, '--commit', head)
        self.assertEqual(result.returncode, 0, data)
        self.assertEqual(data['source_commit'], head)
        self.assertFalse(data['creates_export'])
        self.assertEqual(data['omitted_development_files'], ['AGENTS.md'])
        self.assertNotIn('AGENTS.md', data['files'])
        self.assertEqual(data['files']['README.md']['sha256'], hashlib.sha256(committed).hexdigest())
        self.assertNotIn('UNCOMMITTED PRIVATE FIXTURE', result.stdout)
        self.assertNotIn('fixture@example.invalid', result.stdout)

    def test_public_inventory_requires_exact_commit_not_refs_or_blobs(self):
        head = self.git(self.project, 'rev-parse', 'HEAD')
        blob = self.git(self.project, 'rev-parse', 'HEAD:README.md')
        for identity in ['HEAD', 'main', head[:12], blob, '0' * 40]:
            with self.subTest(identity=identity):
                result, data = self.run_tool('public_inventory.py', None, '--commit', identity)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('error', data)
                self.assertFalse(data['creates_export'])

    def test_public_inventory_refuses_private_unknown_and_symlink_entries(self):
        for name in ['session.txt', 'docs/.codex/record.json', 'docs/raw.jsonl',
                     'src/__pycache__/cache.pyc', 'tools/auth.json', 'docs/link']:
            with self.subTest(path=name):
                project, _ = self.fixture()
                path = project / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if name == 'docs/link':
                    path.symlink_to('../README.md')
                else:
                    path.write_text('Synthetic private or undeclared fixture\n')
                self.git(project, 'add', '-f', name)
                self.git(project, 'commit', '-q', '-m', 'Synthetic invalid candidate')
                head = self.git(project, 'rev-parse', 'HEAD')
                result, data = self.run_tool('public_inventory.py', project, '--commit', head)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()
