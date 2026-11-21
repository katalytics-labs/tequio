"""Validate and filter evidence ledger records without changing them."""

from collections.abc import Mapping

_STATUSES = ("open", "in-progress", "verified")


def select_records(records, place=None, status=None):
    """Return validated records matching exact filters in their original order.

    The returned list is new; its entries are the original record mappings.
    Every input record is validated, including records excluded by filters.
    """
    if status is not None and status not in _STATUSES:
        raise ValueError("unknown requested status")
    try:
        iterator = iter(records)
    except TypeError as exc:
        raise ValueError("records must be an iterable of mappings") from exc

    selected = []
    for record in iterator:
        if not isinstance(record, Mapping):
            raise ValueError("record must be a mapping")
        for field in ("id", "place"):
            value = record.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"record {field} must be a nonempty string")
        if record.get("status") not in _STATUSES:
            raise ValueError("record status must be open, in-progress or verified")
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or any(
            not isinstance(name, str) for name in evidence
        ):
            raise ValueError("record evidence must be a list of strings")
        if (place is None or record["place"] == place) and (
            status is None or record["status"] == status
        ):
            selected.append(record)
    return selected
