import copy
import csv
import io
from types import MappingProxyType
import unittest

from siteledger.export import evidence_csv


def record(**changes):
    result = {"id": "r1", "place": "North", "status": "open", "evidence": []}
    result.update(changes)
    return result


class EvidenceCsvTests(unittest.TestCase):
    def test_empty_has_headers(self):
        self.assertEqual(evidence_csv([]), "id,place,status,evidence\r\n")

    def test_csv_quoting_join_order_and_preservation(self):
        records = [
            record(id='r,"2"', place="South\nRoom", evidence=['a,b.png', 'a"b.txt', 'c\nd.pdf']),
            record(id="r1", status="verified", evidence=["plain.txt", "last.txt"]),
            record(id="r3", status="in-progress"),
        ]
        original = copy.deepcopy(records)
        text = evidence_csv(records)
        self.assertIn('"r,""2"""', text)
        self.assertEqual(list(csv.reader(io.StringIO(text, newline=""))), [
            ["id", "place", "status", "evidence"],
            ['r,"2"', "South\nRoom", "open", 'a,b.png;a"b.txt;c\nd.pdf'],
            ["r1", "North", "verified", "plain.txt;last.txt"],
            ["r3", "North", "in-progress", ""],
        ])
        self.assertEqual(records, original)

    def test_mapping_iterable_and_extra_fields(self):
        item = MappingProxyType(record(extra="ignored", evidence=[""]))
        rows = list(csv.reader(io.StringIO(evidence_csv(iter([item])))))
        self.assertEqual(rows[1], ["r1", "North", "open", ""])

    def test_malformed_records_raise_value_error(self):
        invalid = [None, [], "record", 42]
        for field in ("id", "place", "status", "evidence"):
            missing = record()
            del missing[field]
            invalid.append(missing)
        for field in ("id", "place"):
            invalid.extend(record(**{field: value}) for value in (None, "", 0, [], True))
        invalid.extend(record(status=value) for value in ("closed", "OPEN", "", None, [], {}))
        invalid.extend(record(evidence=value) for value in (None, "file", (), {}, [1], [None], ["ok", []]))
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                evidence_csv([item])

    def test_invalid_later_record_preserves_all_input(self):
        records = [record(evidence=["a"]), record(evidence=[17])]
        original = copy.deepcopy(records)
        with self.assertRaises(ValueError):
            evidence_csv(records)
        self.assertEqual(records, original)

    def test_non_iterable_collection_is_value_error(self):
        for value in (None, 12):
            with self.subTest(value=value), self.assertRaises(ValueError):
                evidence_csv(value)


if __name__ == "__main__":
    unittest.main()
