"""Disposable repositories only; lane inspection does not mutate Git or registry."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from tequio.git_isolation import configure, create_lane, inspect_lanes


class LaneHealth(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.git(self.root, 'init', '-b', 'main')
        self.git(self.root, 'config', 'user.name', 'Fixture')
        self.git(self.root, 'config', 'user.email', 'fixture@example.invalid')
        (self.root / '.gitignore').write_text('.tequio/\n')
        (self.root / 'source').write_text('base\n')
        self.git(self.root, 'add', '.')
        self.git(self.root, 'commit', '-m', 'fixture')
        configure(self.root, True)
        self.record = create_lane(self.root, 'worker')
        self.lane = Path(self.record['path'])

    def git(self, root, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        return subprocess.run(['git', '-C', str(root), *args], check=True,
                              capture_output=True, text=True, timeout=10, env=env).stdout.strip()

    def inspect(self):
        return inspect_lanes(self.root)['lanes'][0]

    def test_healthy_registry_preserved_and_read_only(self):
        registry = self.root / '.tequio/git-isolation.json'
        state = json.loads(registry.read_text())
        state['lanes'][0]['extension'] = {'keep': True}
        registry.write_text(json.dumps(state))
        before = registry.read_bytes()
        gitdir = Path(self.git(self.lane, 'rev-parse', '--absolute-git-dir'))
        index_bytes = (gitdir / 'index').read_bytes()
        index_time = (gitdir / 'index').stat().st_mtime_ns
        result = self.inspect()
        self.assertEqual(result['health'], 'healthy')
        self.assertEqual(result['extension'], {'keep': True})
        for key, value in self.record.items():
            self.assertEqual(result[key], value)
        self.assertEqual(result['actual']['branch'], 'tequio/worker')
        self.assertEqual(result['actual']['head'], self.git(self.lane, 'rev-parse', 'HEAD'))
        self.assertEqual(registry.read_bytes(), before)
        self.assertEqual((gitdir / 'index').read_bytes(), index_bytes)
        self.assertEqual((gitdir / 'index').stat().st_mtime_ns, index_time)
        self.assertFalse((self.root / '.tequio/git-isolation.lock').exists())

    def test_changed_branch_and_detached(self):
        self.git(self.lane, 'switch', '-c', 'other')
        self.assertEqual(self.inspect()['health'], 'branch-mismatch')
        self.git(self.lane, 'checkout', '--detach')
        result = self.inspect()
        self.assertEqual(result['health'], 'detached')
        self.assertIsNone(result['actual']['branch'])

    def test_dirty_active_lane(self):
        (self.lane / 'source').write_text('active work\n')
        result = self.inspect()
        self.assertEqual(result['health'], 'dirty')
        self.assertTrue(result['actual']['dirty'])
        self.assertFalse(result['actual']['conflicted'])
        self.assertNotIn('invalid', result)

    def test_index_untracked_and_operation_markers(self):
        (self.lane / 'source').write_text('staged\n')
        self.git(self.lane, 'add', 'source')
        (self.lane / 'extra').write_text('untracked\n')
        gitdir = Path(self.git(self.lane, 'rev-parse', '--absolute-git-dir'))
        (gitdir / 'rebase-merge').mkdir()
        (gitdir / 'CHERRY_PICK_HEAD').write_text(self.record['base_commit'] + '\n')
        actual = self.inspect()['actual']
        self.assertTrue(actual['index_dirty'])
        self.assertFalse(actual['worktree_dirty'])
        self.assertTrue(actual['untracked'])
        self.assertIn('rebase-merge', actual['in_progress'])
        self.assertIn('CHERRY_PICK_HEAD', actual['in_progress'])

    def test_conflict_and_merge_observed(self):
        (self.root / 'source').write_text('main\n')
        self.git(self.root, 'commit', '-am', 'main edit')
        (self.lane / 'source').write_text('worker\n')
        self.git(self.lane, 'commit', '-am', 'worker edit')
        with self.assertRaises(subprocess.CalledProcessError):
            self.git(self.lane, 'merge', 'main')
        result = self.inspect()
        self.assertTrue(result['actual']['conflicted'])
        self.assertIn('MERGE_HEAD', result['actual']['in_progress'])
        self.assertEqual(result['health'], 'dirty')

    def test_missing_nonrepo_and_foreign(self):
        shutil.rmtree(self.lane)
        self.assertEqual(self.inspect()['health'], 'missing')
        self.lane.mkdir()
        self.assertEqual(self.inspect()['health'], 'unavailable')
        self.git(self.lane, 'init', '-b', 'foreign')
        self.git(self.lane, 'config', 'user.name', 'Fixture')
        self.git(self.lane, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.lane, 'commit', '--allow-empty', '-m', 'foreign')
        self.assertEqual(self.inspect()['health'], 'foreign')

    def test_symlink_not_followed_and_external_git_environment_ignored(self):
        with patch.dict(os.environ, {'GIT_DIR': '/nonexistent', 'GIT_WORK_TREE': '/nonexistent'}):
            self.assertEqual(self.inspect()['health'], 'healthy')
        shutil.rmtree(self.lane)
        self.lane.symlink_to(self.root, target_is_directory=True)
        result = self.inspect()
        self.assertEqual(result['health'], 'unavailable')
        self.assertEqual(result['issues'], ['symlink-path'])

    def test_non_git_default_is_read_only(self):
        plain = Path(self.temp.name) / 'plain'
        plain.mkdir()
        result = inspect_lanes(plain)
        self.assertFalse(result['repository'])
        self.assertFalse(result['enabled'])
        self.assertEqual(result['lanes'], [])
        self.assertEqual(list(plain.iterdir()), [])

    def test_inspection_timeout_is_reported(self):
        from tequio import git_isolation
        original = git_isolation._inspection_git
        def fail(path, *args):
            if Path(path) == self.lane:
                raise git_isolation.GitIsolationError('timed out')
            return original(path, *args)
        with patch.object(git_isolation, '_inspection_git', side_effect=fail):
            self.assertEqual(self.inspect()['health'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
