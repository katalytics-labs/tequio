# Evidence CSV export

`siteledger.export.evidence_csv(records)` returns a CSV string with columns
`id,place,status,evidence`, including the header for an empty iterable. It accepts
an iterable of mappings. Each mapping must contain a nonempty string `id` and
`place`, a status of `open`, `in-progress`, or `verified`, and an `evidence` list
of strings. Additional fields are ignored. Invalid records raise `ValueError`;
a noniterable records argument also raises `ValueError`.

```python
from siteledger.export import evidence_csv

text = evidence_csv([
    {"id": "r1", "place": "North", "status": "open",
     "evidence": ["photo.png", "inspection.pdf"]}
])
```

Rows retain input order. Evidence names are joined with `;`, then standard CSV
quoting handles commas, quotes and newlines in every column. Output uses CRLF
row endings. Empty evidence lists produce empty cells. Semicolons within names
are retained; the joined evidence cell is not a lossless filename-list encoding.
The helper does not modify the input mappings or evidence lists, including on
validation failure. It is independent of the query helper and uses only the
Python standard library.
