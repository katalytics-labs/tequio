import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import test_lifecycle as fixtures
from tequio.reporting import proof
from tequio.core import digest


class Reporting(unittest.TestCase):
    setUp = fixtures.Lifecycle.setUp
    tearDown = fixtures.Lifecycle.tearDown
    task = fixtures.Lifecycle.task
    add = fixtures.Lifecycle.add
    report = fixtures.Lifecycle.report
    docs = fixtures.Lifecycle.docs

    def prepare(self):
        self.add(self.task())
        c = self.w.claim('writer')
        self.w.verify('A', c['token'])
        return c

    def result(self):
        return proof(self.root, 'fixture', 'A')['tasks'][0]

    def test_missing_and_redaction_read_only(self):
        self.add(self.task())
        before = {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()}
        original = sqlite3.connect
        def readonly(*a, **kw):
            self.assertIn('mode=ro', a[0]); self.assertTrue(kw['uri'])
            return original(*a, **kw)
        with patch('tequio.reporting.sqlite3.connect', side_effect=readonly):
            r = self.result()
        self.assertEqual(r['checks']['state'], 'missing')
        self.assertEqual(r['documentation']['state'], 'missing')
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()})
        text = json.dumps(r)
        for key in ['token', 'baseline', 'stdout', 'stderr', 'argv', 'title', 'summary']:
            self.assertNotIn('"'+key+'"', text)

    def test_current_stale_and_historical(self):
        c = self.prepare(); self.docs(c)
        self.w.review('A', c['token'], 'reviewer', 'correctness', self.report(), [])
        self.assertEqual(self.result()['evidence'], 'current')
        self.w.complete('A', c['token'], 'Actual completed fixture')
        (self.root/'drift.txt').write_text('changed')
        r = self.result()
        self.assertEqual(r['evidence'], 'historical')
        self.assertEqual(r['checks']['state'], 'stale')

    def test_failed_tampered_and_missing(self):
        t = self.task(); t['checks'] = [[sys.executable, '-c', 'raise SystemExit(1)']]
        self.add(t); c = self.w.claim('writer'); self.w.verify('A', c['token'])
        self.assertEqual(self.result()['checks']['state'], 'failed')
        with self.w.transaction() as con:
            ref = json.loads(con.execute('SELECT checks FROM tasks').fetchone()[0])
        file = self.w.path/ref['path']; file.write_text('{}')
        self.assertEqual(self.result()['checks']['state'], 'invalid')
        file.unlink()
        self.assertEqual(self.result()['checks']['state'], 'missing')

    def test_malformed_and_private_review(self):
        c = self.prepare(); self.docs(c)
        path = self.report(); (self.w.path/path).write_text('PRIVATE CONTENT MUST NOT APPEAR ' * 5)
        self.w.review('A', c['token'], 'reviewer', 'correctness', path, ['PRIVATE FINDING'])
        r = self.result(); self.assertEqual(r['reviews']['correctness']['state'], 'failed')
        self.assertNotIn('PRIVATE', json.dumps(r))
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET checks='not-json'")
        self.assertEqual(self.result()['evidence'], 'invalid')

    def test_dependency_drift(self):
        c = self.prepare(); self.docs(c)
        self.w.review('A', c['token'], 'reviewer', 'correctness', self.report(), [])
        self.w.complete('A', c['token'], 'Completed prerequisite fixture')
        self.add(self.task('B', depends=['A']))
        c = self.w.claim('writer', 'B'); self.w.verify('B', c['token'])
        self.assertEqual(proof(self.root, 'fixture', 'B')['tasks'][0]['dependencies'][0]['state'], 'current')
        (self.root/'a.txt').write_text('dependency drift')
        self.assertEqual(proof(self.root, 'fixture', 'B')['tasks'][0]['dependencies'][0]['state'], 'stale')

    def test_invalid_lifecycle_cannot_appear_current(self):
        c = self.prepare(); self.docs(c)
        self.w.review('A', c['token'], 'reviewer', 'correctness', self.report(), [])
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET status='unknown-state'")
        self.assertEqual(self.result()['evidence'], 'invalid')

    def test_recursive_legacy_dependency_lifecycle_drift(self):
        for filename in ['a.txt', 'b.txt', 'c.txt']:
            (self.root/filename).write_text('Existing verified fixture output')
        self.add(self.task('A'), self.task('B', depends=['A']), self.task('C', depends=['B']))
        for tid in ['A', 'B', 'C']:
            c = self.w.claim('writer', tid)
            self.w.verify(tid, c['token'])
            # The shared helper targets A; create the same substantive reconciliation for each task.
            with self.w.transaction() as con:
                body = json.loads(con.execute('SELECT body FROM tasks WHERE id=?', (tid,)).fetchone()[0])
            report = {'summary': 'Checked the actual fixture implementation, source requirements and passing subprocess results; no user-facing contract changes.',
                      'deviations': [], 'reconciliation': [
                          {'source': source, 'actual': body['writes'], 'docs': [], 'disposition': 'implemented',
                           'notes': 'The isolated fixture changes no public behavior and needs no product documentation.'}
                          for source in body['sources']]}
            file = self.w.path/'reviews'/('docs-'+tid+'.json'); file.write_text(json.dumps(report))
            self.w.document(tid, c['token'], str(file.relative_to(self.w.path)))
            self.w.review(tid, c['token'], 'reviewer', 'correctness', self.report(), [])
            if tid != 'C':
                self.w.complete(tid, c['token'], 'Actual prerequisite fixture verified')
        self.assertEqual(proof(self.root, 'fixture', 'C')['tasks'][0]['evidence'], 'current')
        with self.w.transaction() as con:
            con.execute("UPDATE tasks SET status='blocked' WHERE id='A'")
            self.assertFalse(self.w.dependencies_current(con, body))
        r = proof(self.root, 'fixture', 'C')['tasks'][0]
        self.assertEqual(r['dependencies'][0]['state'], 'stale')
        self.assertEqual(r['evidence'], 'incomplete')

    def test_document_and_review_integrity(self):
        c = self.prepare(); self.docs(c)
        self.w.review('A', c['token'], 'reviewer', 'correctness', self.report(), [])
        r = self.result()
        self.assertTrue((self.w.path/r['checks']['receipt']).is_file())
        self.assertTrue((self.w.path/r['documentation']['report']).is_file())
        self.assertTrue((self.w.path/r['reviews']['correctness']['report']).is_file())
        (self.w.path/r['reviews']['correctness']['report']).write_text('altered')
        self.assertEqual(self.result()['reviews']['correctness']['state'], 'invalid')
        (self.w.path/r['documentation']['report']).write_text('{}')
        self.assertEqual(self.result()['documentation']['state'], 'invalid')

    def test_timeout_is_failed_not_invalid(self):
        t = self.task(); t['checks'] = [[sys.executable, '-c', 'import time; time.sleep(3)']]
        self.add(t); c = self.w.claim('writer'); self.w.verify('A', c['token'], timeout=1)
        self.assertEqual(self.result()['checks']['state'], 'failed')

    def test_unsafe_receipt_never_read_or_rendered(self):
        self.prepare()
        with self.w.transaction() as con:
            con.execute('UPDATE tasks SET checks=?', (json.dumps({'path': '../PRIVATE', 'hash': 'invalid'}),))
        r = self.result()
        self.assertEqual(r['checks']['state'], 'invalid')
        self.assertNotIn('PRIVATE', json.dumps(r))

    def test_cli_no_workspace_creates_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            proc = subprocess.run([sys.executable, str(fixtures.ROOT/'bin/tequio'), '--project', folder, 'proof'], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['workflow']['stage'], 'intake')
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_cli_task(self):
        self.prepare()
        proc = subprocess.run([sys.executable, str(fixtures.ROOT/'bin/tequio'), '--project', str(self.root), '--workspace', 'fixture', 'proof', 'A'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['tasks'][0]['checks']['state'], 'current')

    def test_damaged_bodies_are_isolated_read_only_and_private(self):
        self.add(self.task('A'), self.task('B'), self.task('C'))
        for tid in ['A', 'B', 'C']:
            for raw in ['{', 'null', '[]', '42', '"PRIVATE BODY"']:
                with self.subTest(tid=tid, raw=raw):
                    with self.w.transaction() as con:
                        original=con.execute('SELECT body FROM tasks WHERE id=?',(tid,)).fetchone()[0]
                        con.execute('UPDATE tasks SET body=? WHERE id=?',(raw,tid))
                    before={str(p):p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()}
                    result=proof(self.root,'fixture')['tasks']
                    for item in result:
                        self.assertEqual(item['evidence'],'invalid' if item['task']==tid else 'incomplete')
                    self.assertNotIn('PRIVATE',json.dumps(result))
                    self.assertEqual(before,{str(p):p.read_bytes() for p in self.w.path.rglob('*') if p.is_file()})
                    with self.w.transaction() as con: con.execute('UPDATE tasks SET body=? WHERE id=?',(original,tid))

    def test_journal_failure_cannot_break_invalid_body_fallback(self):
        self.add(self.task())
        with self.w.transaction() as con: con.execute("UPDATE tasks SET body='null'")
        for exc in [AttributeError('PRIVATE'), sqlite3.DatabaseError('PRIVATE')]:
            with patch('tequio.integration.Journal.status',side_effect=exc):
                r=self.result()
                self.assertEqual(r['evidence'],'invalid')
                self.assertEqual(r['integration'],{'state':'unavailable'})
                self.assertNotIn('PRIVATE',json.dumps(r))
        # A genuinely malformed persisted journal is observed, never repaired.
        with self.w.transaction() as con: con.execute('CREATE TABLE integration_intents(wrong TEXT)')
        before=(self.w.path/'state.sqlite3').read_bytes()
        self.assertEqual(self.result()['integration']['state'],'invalid')
        self.assertEqual(before,(self.w.path/'state.sqlite3').read_bytes())

if __name__ == '__main__':
    unittest.main()
