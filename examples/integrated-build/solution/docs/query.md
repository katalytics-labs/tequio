# Record queries

`siteledger.query.select_records(records, place=None, status=None)` returns a
new list of validated record mappings in original input order. Pass an iterable
of mappings; each record needs a nonempty string `id`, a nonempty string `place`,
a `status` of `open`, `in-progress` or `verified`, and `evidence` as a list of
strings. Empty evidence lists are valid. Additional record fields are preserved.

```python
from siteledger.query import select_records

rows = [{"id": "visit-1", "place": "North", "status": "open", "evidence": []}]
selected = select_records(rows, place="North", status="open")
```

Filters compare exact values, including case. `None` disables that filter; no
matches returns an empty list. An unknown requested status raises `ValueError`,
even when the input is empty. Malformed records also raise `ValueError`, including
records a filter would exclude; a noniterable record collection raises
`ValueError`. No partial list is returned on failure.

The helper never changes input records, their evidence lists, or the input
collection. The result contains the original mappings, not deep copies; callers
that later edit a returned record will therefore also edit that original record.
