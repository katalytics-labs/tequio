# Evidence CSV CLI

Run from the package directory with Python and no extra dependencies:

```sh
python -m siteledger.cli sample.json
python -m siteledger.cli sample.json --place "North hall" --status verified
```

`INPUT_JSON` is a UTF-8 JSON file containing an array of record objects. Each
record has nonempty string `id` and `place`, `status` equal to `open`,
`in-progress`, or `verified`, and an `evidence` array of string filenames.

The CLI composes `query.select_records` and `export.evidence_csv`. Optional place
and status filters match exactly and combine together. Every input record is
validated, including records excluded by filters. It leaves the input file
unchanged and preserves matching record order.

Success returns 0 and writes CSV only to stdout, with columns
`id,place,status,evidence`. Evidence filenames are joined with semicolons; CSV
quoting preserves commas, quotes and embedded newlines. Empty input or no matches
produces the header alone. Redirect stdout to save the CSV.

Missing or unreadable files, invalid UTF-8 or JSON, malformed records and unknown
requested statuses return 2 with a concise `siteledger:` message on stderr, no
traceback and no stdout. CSV is prepared completely before any output is written,
so validation errors cannot leave partial CSV output. Invalid command syntax uses
argparse's usage message and exit 2; `--help` shows usage and exits 0.
