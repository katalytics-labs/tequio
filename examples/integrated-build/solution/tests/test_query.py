import copy
import unittest
from collections import UserDict

from siteledger.query import select_records


def record(identifier="one", place="North", status="open", evidence=None):
    return dict(id=identifier, place=place, status=status,
                evidence=[] if evidence is None else evidence)


class SelectRecordsTests(unittest.TestCase):
    def test_order_exact_filters_and_new_list(self):
        rows = [record("3"), record("1", status="verified"),
                record("2", place="north"), record("4")]
        result = select_records(rows)
        self.assertEqual(result, rows)
        self.assertIsNot(result, rows)
        self.assertEqual(select_records(rows, place="North", status="open"),
                         [rows[0], rows[3]])
        self.assertEqual(select_records(rows, place="missing"), [])
        self.assertEqual(select_records(rows, status="verified"), [rows[1]])

    def test_preserves_nested_input_and_supports_mappings(self):
        rows = [UserDict(record(evidence=['a,"b.csv', "photo;2.png"]))]
        before = copy.deepcopy(rows)
        result = select_records(iter(rows))
        self.assertEqual(rows, before)
        self.assertIs(result[0], rows[0])
        result.clear()
        self.assertEqual(rows, before)

    def test_empty_and_all_valid_statuses(self):
        self.assertEqual(select_records([]), [])
        for status in ("open", "in-progress", "verified"):
            with self.subTest(status=status):
                row = record(status=status)
                self.assertEqual(select_records([row], status=status), [row])

    def test_invalid_records_are_value_errors(self):
        cases = [None, 1, [], {}, record(identifier=""), record(identifier=3),
                 record(place=""), record(place=None), record(status="closed"),
                 record(status=[]), record(evidence="photo.png"),
                 record(evidence=("a",)), record(evidence=[1])]
        for field in ("id", "place", "status", "evidence"):
            row = record()
            del row[field]
            cases.append(row)
        for invalid in cases:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    select_records([invalid])

    def test_invalid_excluded_record_still_rejected_without_mutation(self):
        rows = [record(), record(place="South", evidence=[None])]
        before = copy.deepcopy(rows)
        with self.assertRaises(ValueError):
            select_records(rows, place="North")
        self.assertEqual(rows, before)

    def test_unknown_requested_status_even_with_no_records(self):
        for status in ("OPEN", "", [], 0):
            with self.subTest(status=status):
                with self.assertRaises(ValueError):
                    select_records([], status=status)

    def test_noniterable_collection_is_value_error(self):
        for rows in (None, 42):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    select_records(rows)


if __name__ == "__main__":
    unittest.main()
