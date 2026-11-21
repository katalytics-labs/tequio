"""CLI intake and real module-invocation contract tests."""

import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from siteledger.cli import build_parser, load_records, main


class CliIntakeTests(unittest.TestCase):
    def test_parser_keeps_exact_filter_values(self):
        args = build_parser().parse_args(
            ["records.json", "--place", "North hall", "--status", "unknown"]
        )
        self.assertEqual(args.input_json, "records.json")
        self.assertEqual(args.place, "North hall")
        self.assertEqual(args.status, "unknown")

    def test_loads_utf8_json_without_semantic_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "records.json"
            payload = [{"place": "México"}]
            source.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(load_records(source), payload)

    def test_bad_json_is_concise_error_without_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            source.write_text("{", encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = main([str(source)])
            self.assertEqual(result, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(stderr.getvalue().startswith("siteledger: "))
            self.assertNotIn("Traceback", stderr.getvalue())


class CliSubprocessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "records.json"
        self.records = [
            {"id": "second", "place": 'México, "North"', "status": "open",
             "evidence": ["photo,1.jpg", 'quote".txt', "line\nbreak"]},
            {"id": "first", "place": "South", "status": "verified", "evidence": []},
            {"id": "third", "place": 'México, "North"', "status": "verified",
             "evidence": ["proof.pdf"]},
        ]
        self.write(self.records)

    def write(self, payload):
        self.source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "siteledger.cli", str(self.source), *args],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def assert_failure(self, result):
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("siteledger: "), result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(len(result.stderr.splitlines()), 1)

    def test_success_preserves_order_quoting_and_input_file(self):
        before = self.source.read_bytes()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn('"México, ""North"""', result.stdout)
        self.assertEqual(list(csv.reader(io.StringIO(result.stdout))), [
            ["id", "place", "status", "evidence"],
            ["second", 'México, "North"', "open", 'photo,1.jpg;quote".txt;line\nbreak'],
            ["first", "South", "verified", ""],
            ["third", 'México, "North"', "verified", "proof.pdf"],
        ])
        self.assertEqual(self.source.read_bytes(), before)

    def test_filters_are_exact_and_combined(self):
        for args, ids in [
            (["--place", 'México, "North"'], ["second", "third"]),
            (["--status", "verified"], ["first", "third"]),
            (["--place", 'México, "North"', "--status", "verified"], ["third"]),
            (["--place", "south"], []),
        ]:
            with self.subTest(args=args):
                result = self.invoke(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                rows = list(csv.reader(io.StringIO(result.stdout)))
                self.assertEqual(rows[0], ["id", "place", "status", "evidence"])
                self.assertEqual([row[0] for row in rows[1:]], ids)

    def test_empty_input_emits_header(self):
        self.write([])
        result = self.invoke()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(result.stdout, "id,place,status,evidence\n")

    def test_unknown_requested_status(self):
        self.assert_failure(self.invoke("--status", "closed"))

    def test_malformed_records_and_containers(self):
        for payload in [{}, "", None, 7, [None], [{"id": ""}],
                        [self.records[0], {**self.records[1], "evidence": [7]}],
                        [{**self.records[0], "status": "closed"}]]:
            with self.subTest(payload=payload):
                self.write(payload)
                self.assert_failure(self.invoke())

    def test_invalid_filtered_out_record_still_fails_without_partial_csv(self):
        self.write([self.records[0], {**self.records[1], "evidence": "invalid"}])
        self.assert_failure(self.invoke("--place", self.records[0]["place"]))

    def test_invalid_json(self):
        self.source.write_text("{", encoding="utf-8")
        self.assert_failure(self.invoke())

    def test_missing_file(self):
        self.source.unlink()
        self.assert_failure(self.invoke())

    def test_invalid_utf8(self):
        self.source.write_bytes(b"\xff")
        self.assert_failure(self.invoke())
