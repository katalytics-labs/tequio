"""Public CLI Git selection and no-repository regression coverage."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from tequio.cli import main


class GitCLI(unittest.TestCase):
    def call(self, root, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(['--project', str(root), *args])
        return code, out.getvalue(), err.getvalue()

    def test_nonrepo_status_is_read_only_and_shared_works(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            code, out, err = self.call(root, 'status')
            self.assertEqual(code, 0, err)
            self.assertIn('git_isolation', json.loads(out))
            self.assertEqual(list(root.iterdir()), [])
            code, out, err = self.call(root, 'git', 'configure', 'shared')
            self.assertEqual(code, 0, err)
            self.assertFalse((root / '.git').exists())
            code, out, err = self.call(root, 'git', 'configure', 'worktrees')
            self.assertEqual(code, 2)
            self.assertFalse((root / '.git').exists())

    def test_lane_lifecycle_refused_and_status_uses_controller(self):
        from tequio.git_isolation import configure, create_lane
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'repo'
            root.mkdir()
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / '.gitignore').write_text('.tequio/\n')
            (root / 'brief.md').write_text('Fixture scope with observable ownership and guarded task execution.\n')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
            code, out, err = self.call(root, 'workspace', '--brief', str(root / 'brief.md'))
            self.assertEqual(code, 0, err)
            configure(root, True)
            lane = Path(create_lane(root, 'one')['path'])
            code, out, err = self.call(lane, 'workspace', '--brief', str(lane / 'brief.md'))
            self.assertEqual(code, 2)
            self.assertIn('original controller', err)
            self.assertFalse((lane / '.tequio/workspaces').exists())
            code, out, err = self.call(lane, 'status')
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)['workspace'], str((root / '.tequio/workspaces/main').resolve()))

    def test_existing_repo_does_not_enable_itself(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            before = sorted(p.name for p in root.iterdir())
            code, out, err = self.call(root, 'git', 'status')
            self.assertEqual(code, 0, err)
            self.assertEqual(before, sorted(p.name for p in root.iterdir()))
            code, out, err = self.call(root, 'git', 'lane', 'unapproved')
            self.assertEqual(code, 2)
            self.assertFalse((root / '.tequio').exists())


if __name__ == '__main__':
    unittest.main()
