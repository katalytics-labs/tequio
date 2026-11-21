"""Export validated evidence records through the public query and CSV helpers."""

import argparse
import json
import sys

from .query import select_records
from .export import evidence_csv


def build_parser():
    """Describe the public invocation without duplicating helper validation."""
    parser = argparse.ArgumentParser(description="Export evidence records as CSV")
    parser.add_argument("input_json", metavar="INPUT_JSON")
    parser.add_argument("--place")
    parser.add_argument("--status")
    return parser


def load_records(path):
    """Read JSON; semantic record validation belongs to the public helpers."""
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        records = load_records(args.input_json)
        if not isinstance(records, list):
            raise ValueError("input JSON must be an array of records")
        selected = select_records(records, place=args.place, status=args.status)
        output = evidence_csv(selected)
    except (OSError, ValueError) as exc:
        print(f"siteledger: {exc}", file=sys.stderr)
        return 2

    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
