# Task evidence report

Run the internal CLI from the installed project, selecting the same workspace used for implementation:

```sh
python3 bin/tequio --workspace feature-one proof
python3 bin/tequio --workspace feature-one proof TASK-01
```

`proof` is a read-only command, not a skill. It lists recorded tasks in identifier order or selects one task. An unknown task in an existing workspace is an error. Without an existing workspace it returns intake or explicit workspace-selection guidance and creates nothing. In a registered Git lane it reads the original controller, like status; integrate lane changes before authoritative verification.

Each task reports its lifecycle separately from evidence. Numbered acceptance requirements map to the task's declared source references and implementation files, with check, documentation and required review evidence alongside. These associations are task declarations, not an inferred per-requirement coverage analysis or semantic certification. Workspace-relative receipt/report references allow local inspection without including their contents. Check totals summarize actual stored executions; receipt and report hashes identify validated records. Documentation lists its declared files. Review kinds follow the task's required correctness/security policy.

Dependency evidence checks the authoritative recursive completion/freshness contract, including lifecycle changes in transitive prerequisites even for legacy global tasks.

Evidence states distinguish:

- `missing`: no record or a referenced file is absent.
- `failed`: an actual check failed (including timeout/launch failure), or review findings remain.
- `stale`: integrity is intact but current inputs, implementation, documentation or prerequisite evidence differ.
- `invalid`: malformed data, unsafe references or mismatching receipt/report hashes.
- `current`: required records validate against current files and inputs.
- `historical`: a previously closed task lacks complete current evidence. Its component states still explain the gap; a stored `done` status does not establish current correctness.

An unfinished task with incomplete evidence has aggregate `incomplete`; malformed task evidence has aggregate `invalid`. Missing documentation and reviews cannot produce aggregate `current`. Closure with all evidence still valid may report `current`, independently of lifecycle.

The report uses SQLite `mode=ro` and does not run checks, write events, renew leases, alter evidence or create workspaces. Stored task rows, ownership tokens, baselines, raw check arguments/output, private report text and finding prose are omitted. Source and declared file references remain visible: this is a local operator report, not an automatic public export. Hashes establish local integrity, not authentication of reviewer independence. Changes concurrent with a read can invalidate its observation; refresh after integration.

Regression coverage includes CLI selection and no-workspace behavior, read-only SQLite access and unchanged workspace bytes, missing/failed/tampered/malformed records, redaction, current evidence and drift after historical closure.

Malformed JSON or non-object task bodies produce a fixed invalid item with security unavailable, without partial fields or neighboring state. Integration observations remain separate: an unreadable journal reports invalid/unavailable rather than crashing proof. No record is repaired and no invalid observation authorizes acceptance.


## Compact verification delivery

`verify TASK --token TOKEN --summary` runs the same checks and retains the full private receipt. Default CLI JSON and `Workspace.verify(tid, token, timeout)` are unchanged. The opt-in JSON has exactly `schema_version` (1), `task`, `passed`, `stable`, `checks` (`executed`, `passed`, `failed`), `receipt` (`path`, `hash`), `diagnostics` and `omitted_diagnostics`. Counts describe executed result entries; nonzero/null exits count as failed. Instability can fail overall verification even when every check exited zero.

Diagnostic entries contain only `check` (one-based index, or null for snapshot instability) and `code`: `check-nonzero`, `check-timeout`, `check-launch-failed` or `snapshot-unstable`. Failed checks appear in execution order, then instability; only the first three entries are displayed and the omitted count reports the remainder. Codes come from execution branches, not arbitrary output/error text. No raw argv/stdout/stderr/error strings are included. Summary size does not grow with captured command output; output capture/storage limits are unchanged.

An internal opt-in envelope captures the exact newly published receipt path/hash while the verification operation guard is held. Rendering never reads a later mutable latest-check pointer. Passed verification returns exit 0, published failure/instability exit 1, and infrastructure/preflight/publication refusal the existing exit 2 error behavior with no summary. Failure paths never substitute an old PASS. Existing error reporting is not globally sanitized by this flag. Task IDs and receipt references remain private metadata, not an automatic public export. Inspect the referenced full evidence and current documentation/reviews before acceptance; compact delivery does not relax execution, cleanup, freshness or review gates.


## Evidence-aware Status prerequisites

Status adds per-task `checks:{state}` with current, missing, failed, stale, invalid, unavailable or not-observed. It uses the existing check-evidence validator for unfinished tasks without returning raw arguments/output/errors or invoking full proof; done/superseded history is not-observed. This is a sequential advisory observation, not acceptance or a changed-file explanation.

For an otherwise review-stage task without current checks, workflow stage `verification-required` recommends existing Build: finish outstanding implementation/docs edits, then verify the stable candidate before recording reconciliation or obtaining review. Consumers matching a closed workflow-stage list must allow the new stage. All existing fields remain; live/uncertain operations, migration, stale phases and integration reconciliation retain priority. Current checks then lead to reconciliation, required review, findings correction or closure as appropriate. A status read never launches checks, recovers ownership or grants scope.

Draft rows add `draft_readiness:{state,category}`: recorded, legacy-unknown, invalid or not-applicable, with a known existing category or null. Draft-only guidance names the first relevant task in recorded order. It omits blocker reason/action/source prose; the agent privately inspects the sourced resolution action and judges whether owner input is actually needed. Metadata is not semantic truth. No imported history is rewritten, no draft is promoted and fully specified dependency-waiting work stays ready.

A durable stopped verification attempt still requires result reconciliation: an older otherwise-current PASS does not remove that guard. Integration journal needs-checks/needs-docs/needs-review states likewise require fresh post-integration evidence even when ordinary receipt fields look current. Status recommends inspecting that context rather than announcing closure.


## Explicit bounded verification capture

New task/release templates opt into `capture:{version:1,mode:"bounded-v1",max_bytes:1048576}`. Exact keys, integer version1 and byte limit1..16777216; booleans/unknown supplied fields are invalid even on new drafts. The budget is shared across both streams/all check attempts, never reset per check. Absence preserves legacy task/API/receipt/timeout behavior; imported history is not migrated. This is capture policy for reviewed task commands, not a global tool sandbox or automatic security classifier.

Bounded mode concurrently drains nonblocking pipes in chunks at most64KiB. Exactly the budget followed by EOF completes; an additional byte terminates the owned group and aborts unattempted checks. Timeout/read failure likewise retains captured prefix and stops later checks. Human-readable UTF-8 replacement strings and base64 raw prefixes are stored privately. Budget bounds retained raw payload, not all task metadata/host memory. observed_bytes stops at terminal capture decision; subsequent cleanup bytes have separate accounting. No truncation may yield a full-evidence PASS, including a process that already exited zero.

Bounded receipts use schema_version2 and include policy, retained/observed/cleanup byte accounting, capture state/completeness, planned/attempted/executed counts and ordered skipped indexes. Results contain attempts, original indexes, launched booleans, actual observed exit codes, previews and exact stream byte/base64 counts. Launch failure remains an attempted result with no child; ordinary failures do not stop subsequent checks. Limit/timeout/capture failure skips only never-attempted checks. Version-aware readers validate policy, lengths, counts, raw/preview consistency and outcome before trusting passed. Unknown/inconsistent versions are invalid; valid incomplete capture is failed. Acceptance still requires current source/input hashes, docs and actual required independent reviews.

Only bounded summaries use schema_version2: existing top-level summary fields plus capture `{state,complete,max_bytes,retained_bytes,planned}`; checks is `{attempted,executed,passed,failed,skipped}`. attempted counts result entries, executed counts spawned children; passed+failed=attempted. New fixed codes capture-limit-exceeded/capture-failed join existing nonzero/timeout/launch/instability codes; first3diagnostics plus omission count remain. No raw/base64/argv/error prose is included. Legacy summaries remain version1 unchanged. Metadata is private operator data, not a public export.

Bounded receipt readers/writers enforce `8*max_bytes+1048576` serialized bytes, including size checks before JSON/base64 decode. Oversize metadata or publication failure attaches no result; an older PASS cannot substitute. Successful complete verification exits0, published failure exits1 and infrastructure/uncertain cleanup exits2. Exact path/hash publication stays under the operation guard. No spooling, automatic retention/deletion, global rollout or specialist/Git-command capture change is included.
