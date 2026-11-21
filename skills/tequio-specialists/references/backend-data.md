# Backend and data reference

Use when the project has services, persistence, schema migrations or concurrent access — including local embedded persistence such as a SQLite file. Skip only when none of these concerns apply; locality alone is not a skip reason. Shared source, execution and qualification rules: [coverage guide](coverage-guide.md).

## Questions the agent resolves from project context

- Validation and authorization: where are inputs validated and callers authorized, at every trust boundary rather than only the edge? What does the selected framework enforce versus the application?
- Transactions and consistency: which operations must be atomic, what isolation/consistency does the actual database provide, and what happens on partial failure?
- Concurrency: how are duplicate requests and concurrent writes to the same record handled — constraints, locking, optimistic versioning or queues?
- Migrations: what is the failure mode of each schema change mid-run, and what recovery fits the actual data constraints? Destructive changes are not assumed reversible.
- Idempotency and retries: which operations are safe to repeat, and where are retries bounded with timeouts instead of unbounded loops?

## Sources

The selected framework's and database's exact-version primary documentation is the implementation authority; choose it from the actual manifest/lockfile, not from this page. Candidate starting points, not mandates: the [AWS Builders' Library](https://builder.aws.com/learn/topics/builders-library) collection for distributed-system tradeoffs (index accessed 2026-11-17; article list is client-rendered and individual articles were not retrieved in that pass — access any article before relying on it), and [Google AIP](https://google.aip.dev/general) for API-facing resource/design decisions (general index accessed 2026-11-17; no page version stated; its content/code license terms were not re-verified in that pass — inspect before reuse). Neither is a cloud or stack requirement.

## Exercise considerations

Realistic exercises include a duplicate request and a concurrent write to the same record, plus a failed or interrupted migration with an explicit recovery path. Expected and denied/failure behavior both need evidence from the actual project fixture; this page supplies prompts, not answers.
