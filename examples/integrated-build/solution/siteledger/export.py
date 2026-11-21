"""Validated evidence CSV export."""

from collections.abc import Mapping
import csv
import io


_STATUSES = ("open", "in-progress", "verified")


def evidence_csv(records):
    """Return records as CSV, preserving input order and objects.

    Malformed records raise ValueError. Extra mapping fields are ignored.
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("id", "place", "status", "evidence"))
    try:
        iterator = iter(records)
    except TypeError as exc:
        raise ValueError("records must be iterable") from exc
    for index, record in enumerate(iterator):
        if not isinstance(record, Mapping):
            raise ValueError(f"record {index} must be a mapping")
        for field in ("id", "place"):
            if not isinstance(record.get(field), str) or not record[field]:
                raise ValueError(f"record {index}: {field} must be a nonempty string")
        status = record.get("status")
        if not isinstance(status, str) or status not in _STATUSES:
            raise ValueError(f"record {index}: invalid status")
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or any(
            not isinstance(name, str) for name in evidence
        ):
            raise ValueError(f"record {index}: evidence must be a list of strings")
        writer.writerow((record["id"], record["place"], status, ";".join(evidence)))
    return output.getvalue()
