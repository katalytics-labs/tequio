"""Disposable repositories only; never operates on the source checkout's Git state."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tequio.git_isolation import (GitIsolationError, configure, create_lane,
                                  detect, inspect_lanes)


class GitIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'repo'
        self.root.mkdir()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def repo(self):
        self.git('init')
        (self.root / '.gitignore').write_text('.tequio/\n')
        (self.root / 'source.txt').write_text('original\n')
        (self.root / 'nested').mkdir()
        (self.root / 'nested/file.txt').write_text('nested\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-m', 'fixture')

    def test_nonrepo_and_disabled_detection_read_only(self):
        self.assertFalse(detect(self.root)['repository'])
        with self.assertRaises(GitIsolationError):
            create_lane(self.root, 'one')
        self.assertFalse((self.root / '.tequio').exists())
        with self.assertRaises(GitIsolationError):
            configure(self.root, True)
        self.assertEqual(configure(self.root, False)['mode'], 'shared-folder')
        self.assertFalse((self.root / '.git').exists())

    def test_discovery_subfolder_and_worktree(self):
        self.repo()
        self.assertTrue(detect(self.root / 'nested')['repository'])
        self.assertFalse((self.root / '.tequio').exists())
        configure(self.root, True)
        record = create_lane(self.root, 'one')
        lane = Path(record['path'])
        self.assertEqual(detect(lane)['control_root'], str(self.root))
        self.assertEqual(detect(lane)['git_common_dir'], detect(self.root)['git_common_dir'])
        self.assertEqual(inspect_lanes(lane)['lanes'][0]['lane'], 'one')
        self.assertEqual((lane / 'source.txt').read_text(), 'original\n')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_controller_in_repository_subfolder(self):
        self.repo()
        controller = self.root / 'nested'
        configure(controller, True)
        lane = create_lane(controller, 'nested')
        self.assertEqual(Path(lane['path']).name, 'nested')
        self.assertEqual(detect(lane['path'])['controller'], str(controller))

    def test_invalid_inputs_dirty_and_preservation(self):
        self.repo()
        configure(self.root, True)
        for name in ('../escape', '-x', 'a/b', '', 'a.b'):
            with self.assertRaises(GitIsolationError):
                create_lane(self.root, name)
        for base in ('--help', 'does-not-exist', 'HEAD\x00bad'):
            with self.assertRaises(GitIsolationError):
                create_lane(self.root, 'bad', base)
        (self.root / 'source.txt').write_text('user changes\n')
        with self.assertRaisesRegex(GitIsolationError, 'changes'):
            create_lane(self.root, 'dirty')
        self.assertEqual((self.root / 'source.txt').read_text(), 'user changes\n')
        self.assertEqual(self.git('branch', '--list', 'tequio/*'), '')

    def test_collision_and_lock(self):
        self.repo()
        configure(self.root, True)
        create_lane(self.root, 'one')
        with self.assertRaises(GitIsolationError):
            create_lane(self.root, 'one')
        self.git('branch', 'tequio/existing')
        with self.assertRaises(GitIsolationError):
            create_lane(self.root, 'existing')
        target = self.root.parent / 'repo-tequio-target'
        target.mkdir()
        with self.assertRaises(GitIsolationError):
            create_lane(self.root, 'target')
        lock = self.root / '.tequio/git-isolation.lock'
        lock.write_text('active')
        with self.assertRaisesRegex(GitIsolationError, 'locked'):
            create_lane(self.root, 'locked')
        self.assertEqual(lock.read_text(), 'active')

    def test_ignored_private_directory_required_and_symlink_refused(self):
        self.repo()
        (self.root / '.gitignore').write_text('')
        with self.assertRaises(GitIsolationError):
            configure(self.root, True)
        (self.root / '.tequio').symlink_to(self.root / 'nested', target_is_directory=True)
        with self.assertRaises(GitIsolationError):
            configure(self.root, False)

    def test_repository_path_with_trailing_space(self):
        original = self.root
        self.root = original.with_name('repo ')
        original.rename(self.root)
        self.repo()
        self.assertEqual(detect(self.root)['repository_root'], str(self.root))
        configure(self.root, True)
        lane = create_lane(self.root, 'spaces')
        self.assertEqual((Path(lane['path']) / 'source.txt').read_text(), 'original\n')

    def test_historical_symlink_project_cannot_escape_lane(self):
        self.repo()
        nested = self.root / 'nested'
        (nested / 'file.txt').unlink()
        nested.rmdir()
        other = self.root / 'other'
        other.mkdir()
        (other / 'file.txt').write_text('preserve\n')
        nested.symlink_to(other, target_is_directory=True)
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-m', 'historical symlink')
        historical = self.git('rev-parse', 'HEAD')
        nested.unlink()
        nested.mkdir()
        (nested / 'file.txt').write_text('current\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-m', 'current directory')
        configure(nested, True)
        with self.assertRaisesRegex(GitIsolationError, 'symlinks'):
            create_lane(nested, 'escape', historical)
        self.assertFalse((other / '.tequio').exists())
        self.assertEqual((other / 'file.txt').read_text(), 'preserve\n')
        self.assertEqual(inspect_lanes(nested)['lanes'], [])
        self.assertTrue((self.root.parent / 'repo-tequio-escape').is_dir())

    def test_registry_failure_preserves_created_work(self):
        self.repo()
        configure(self.root, True)
        with patch('tequio.git_isolation._save', side_effect=OSError('disk failure')):
            with self.assertRaisesRegex(GitIsolationError, 'preserved branch'):
                create_lane(self.root, 'partial')
        self.assertTrue((self.root.parent / 'repo-tequio-partial/source.txt').exists())
        self.assertEqual(self.git('for-each-ref', '--format=%(refname:short)', 'refs/heads/tequio/partial'), 'tequio/partial')
        self.assertFalse((self.root / '.tequio/git-isolation.lock').exists())


if __name__ == '__main__':
    unittest.main()
