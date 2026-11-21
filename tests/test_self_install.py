"""Disposable self-source install/removal cases, never the actual source checkout."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from tequio.core import Error
from tequio.install import install, uninstall

ROOT = Path(__file__).resolve().parents[1]


class SelfInstallation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.count = 0

    def tearDown(self):
        self.temp.cleanup()

    def source(self):
        self.count += 1
        source = self.base / ('source-' + str(self.count))
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '.tequio', '.agents', '__pycache__'))
        return source

    def image(self, root):
        return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink()
                else (p.stat().st_mode & 0o777, p.read_bytes())
                for p in root.rglob('*') if p.is_file() or p.is_symlink()}

    def test_self_install_upgrade_uninstall_preserves_source_and_evidence(self):
        root = self.source();launcher = root / 'bin/tequio';launcher.chmod(0o640)
        expected = launcher.read_bytes()
        evidence = root / '.tequio/workspaces/existing/evidence.txt'
        evidence.parent.mkdir(parents=True);evidence.write_text('Preserved private evidence')
        result = install(root, root)
        self.assertEqual(result['mode'], 'source-checkout')
        manifest = json.loads((root / '.tequio/manifest.json').read_text())
        self.assertNotIn('bin/tequio', manifest['files']);self.assertNotIn('bin/tequio', manifest['modes'])
        self.assertNotIn('/bin/tequio', (root / '.gitignore').read_text())
        self.assertTrue((root / '.agents/skills/tequio-briefing/SKILL.md').is_file())
        self.assertTrue((root / '.tequio/runtime/tequio/install.py').is_file())
        install(root, root)
        self.assertEqual(launcher.read_bytes(), expected);self.assertEqual(launcher.stat().st_mode & 0o777, 0o640)
        uninstall(root)
        self.assertEqual(launcher.read_bytes(), expected);self.assertEqual(launcher.stat().st_mode & 0o777, 0o640)
        self.assertEqual(evidence.read_text(), 'Preserved private evidence')
        result = subprocess.run([sys.executable, '-B', str(launcher), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_or_symlink_source_launcher_refuses_without_changes(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink):
                root = self.source();launcher = root / 'bin/tequio';launcher.unlink()
                if symlink:launcher.symlink_to(root / 'src/tequio/cli.py')
                before = self.image(root)
                with self.assertRaises(Error):install(root, root)
                self.assertEqual(self.image(root), before)
                self.assertFalse((root / '.tequio/manifest.json').exists())

    def test_other_source_does_not_adopt_self_installed_launcher(self):
        root = self.source();other = self.source();install(root, root)
        before = self.image(root)
        with self.assertRaises(Error):install(other, root)
        self.assertEqual(self.image(root), before)

    def test_self_install_refuses_prior_launcher_ownership(self):
        source = self.source();target = self.base / 'installed';target.mkdir()
        self.assertEqual(install(source, target)['mode'], 'snapshot')
        # Synthetic transition: add source material beside an existing installer-owned launcher.
        for name in ('src', 'skills', 'roles', 'templates', 'profiles'):
            shutil.copytree(source / name, target / name)
        for name in ('bundle.json', 'LICENSE'):
            shutil.copy2(source / name, target / name)
        before = self.image(target)
        with self.assertRaisesRegex(Error, 'owns the launcher'):install(target, target)
        self.assertEqual(self.image(target), before)


if __name__ == '__main__':
    unittest.main()
