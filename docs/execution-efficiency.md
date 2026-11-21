# Bounded execution and coordination observations

The host should make a useful bounded change, then obtain independent acceptance of a stable candidate. Development feedback and focused finding rechecks are valuable when they answer a concrete question; they are not mandatory full correctness/security cycles after every intermediate edit. Final independent correctness and security reviews remain mandatory where the current task contract requires them. Source-only or partial development reports do not satisfy final acceptance.

## Optional policy

```json
"execution_checkpoints": {
  "version": 1,
  "wall_minutes": 30,
  "max_verifications_per_task": 3
}
```

All three keys are required and no others are accepted in this object. Version must be integer1; the other values must be positive integers, not booleans/floats. A missing object retains legacy policy validity and is explicitly unbudgeted. A malformed supplied object makes the policy invalid. No old task, receipt or checkpoint is migrated automatically. The entire policy remains digest-bound, including unrelated private fields.

These are host reporting checkpoints, not token/cost estimates, hard spending guards or permission. Declare the batch's actual time/correction limits before prolonged work. If real usage is unavailable, report it as unknown, run one bounded chunk and report results/open scope before extending. At a repeated-correction checkpoint, distinguish useful outcomes from acceptance still open; do not hide cumulative cycles by writing another checkpoint. Existing user authorization governs continuation; elapsed time, silence and a template default grant nothing.

## Read-only progress

`python3 bin/tequio --workspace NAME progress [TASK]` reads a consistent SQLite snapshot of task IDs/status and selected lifecycle event publications. It counts published verifications (failed publications included), published successes, documentation records, correctness/security review records and completion records. Task closure counts remain recorded lifecycle facts, not whole-product or criterion-level acceptance. Unknown task fails in an existing workspace; an absent workspace returns the usual read-only intake guidance. Git lanes route observations to their original controller.

Counters are historical publications, not current checks/reviews or every launched attempt. Aborted/unpublished verification, arbitrary agent feedback, unregistered reports, external emails and other side effects are not counted. Correctness/security counts describe recorded kinds, not authenticated reviewer independence. No report or receipt file is parsed to make a count; raw task bodies, policy prose, tokens, commands, outputs, findings and actors are omitted. Malformed observed data produces an explicit incomplete-observation diagnostic, not a silent within-budget conclusion. This is a local operator view, not a certified public export. Use proof for current evidence.

A version1 checkpoint with a structurally healthy saved context, matching current valid policy state/digest and finite nonnegative time not in the future supplies the elapsed-wall-time anchor. Missing/legacy/damaged/future/policy-drifted checkpoints give unknown elapsed time. Wall time is not active work, model time or billing. Unfinished tasks reaching the configured historical publication count request a checkpoint; the count does not reset on a checkpoint or reclaim. Closed/superseded tasks are not loop warnings. Missing limits, invalid policy, unknown time or incomplete observation are visible reasons for host reconciliation. None of these advisories block claim/verify/review/complete, reuse evidence or certify scope authorization.

Token and cost fields are null with source unavailable in this batch. If the host obtains genuine usage data, distinguish its provider/source and host-reported nature in the private handoff. The CLI does not infer such data from time or task counts.

## Stable candidate and expensive effects

Read applicable source and decisions initially. Subsequent assignments should carry compact references, exact changed scope, evidence, open findings, limits and next action. Re-read changed or uncertain inputs; avoid replaying project history by default. Assess task qualification surface—fixtures, dependencies, failure controls and costly effects—not just its title or code size. Prefer coherent complete slices, with final integration evidence, rather than sprawling qualification tasks or trivial microtasks. Preserve all agreed requirements.

Prepare implementation, maintained docs, configuration and check inputs before authoritative verification. Use cheap development checks first, then deliberately authorize/run costly current-behavior checks when prerequisites and resource limits are stable. Record private documentation reconciliation and reviews afterward without editing the already bound source just to narrate progress. Final independent reviewers inspect that actual candidate, checks, docs and limits.

A material correction still requires current evidence and matching required review. Existing global/scoped-v1 freshness rules are unchanged: Markdown can change a contract, declared dependencies matter, and stale security evidence cannot pass. Focus review attention on the changed finding and its relevant effects, but retain all required final coverage. Use existing scoped-v1 only after a supported dependency assessment; otherwise retain conservative global revalidation. Do not edit immutable stored checks, exempt files, parse oldPASS output as execution, or automatically repeat external effects to chase unrelated notes. If an expensive result is invalidated, make a deliberate current revalidation decision within authorization. Separate expensive checks into another coherent reviewed task only when dependency/freshness semantics really support it.

For example, an orchestrator handling several authorization/transaction/integration surfaces would first identify coherent proof boundaries, set a time/loop checkpoint and use focused development feedback. It would stabilize the local candidate/docs before costly external checks and arrange final independent review against current evidence. An unfinished task accumulating publications would trigger a visible checkpoint rather than more silent qualification expansion. This describes intended host behavior, not a measured efficiency gain or evidence that a CLI controls model choices.

## Proposed rollout; not performed here

Version 0.10.0 is qualified as a source release; deployment into any existing project remains separate. Before a project rollout, exercise an isolated fresh snapshot with synthetic data: legacy policy, configured checkpoints, deliberate failures, corruption, read-only status and normal acceptance refusal. Review changed owned assets before a real project upgrade; preserve modified skills/policies and existing evidence instead of overwriting them. Adding checkpoint limits is an explicit policy edit, not approval of more scope or reuse of old receipts. Existing immutable tasks retain their gates and historical evidence. Obtain project-specific authorization and reconcile live handles/paused state before any future upgrade. No automatic installation, paused-project resumption, task mutation or public release follows from this framework change.


## Checkpoint advice in Status

Existing-workspace `status` also returns additive top-level `execution_checkpoints` and `usage` objects, reusing the exact `progress` field shapes and semantics. It does not duplicate progress task lists/counters. Existing workflow.next, lifecycle readiness, intake and lane routing are unchanged. In-repo consumers accept these additive fields; external closed-schema consumers may need adaptation.

A failed checkpoint observation yields a fixed unavailable envelope: state/clock `unavailable`, limits/elapsed_wall_seconds null, checkpoint_required true and reasons `[{"reason":"observation-incomplete"}]`. Usage is `{tokens:null,cost:null,source:unavailable}`. No private exception text, policy prose or automatic repair is included. Observations are sequential, not atomic across files/database. This fallback concerns checkpoint observation; it does not promise arbitrary corrupted workspace state is readable.

The Status agent surfaces a configured due checkpoint or material invalid/unavailable observation while keeping one immediate action. Missing/legacy limits and unknown usage remain unknown, without mandatory owner budget questions. If a configured policy has no usable time anchor, the next authorized Build may record its baseline internally; Status stays read-only. Advice never stops a live operation, releases ownership, changes acceptance or grants authorization. Full progress/proof details remain optional internal inspection.


## Compact verification delivery

`verify TASK --token TOKEN --summary` runs the same checks and retains the full private receipt. Default CLI JSON and `Workspace.verify(tid, token, timeout)` are unchanged. The opt-in JSON has exactly `schema_version` (1), `task`, `passed`, `stable`, `checks` (`executed`, `passed`, `failed`), `receipt` (`path`, `hash`), `diagnostics` and `omitted_diagnostics`. Counts describe executed result entries; nonzero/null exits count as failed. Instability can fail overall verification even when every check exited zero.

Diagnostic entries contain only `check` (one-based index, or null for snapshot instability) and `code`: `check-nonzero`, `check-timeout`, `check-launch-failed` or `snapshot-unstable`. Failed checks appear in execution order, then instability; only the first three entries are displayed and the omitted count reports the remainder. Codes come from execution branches, not arbitrary output/error text. No raw argv/stdout/stderr/error strings are included. Summary size does not grow with captured command output; output capture/storage limits are unchanged.

An internal opt-in envelope captures the exact newly published receipt path/hash while the verification operation guard is held. Rendering never reads a later mutable latest-check pointer. Passed verification returns exit 0, published failure/instability exit 1, and infrastructure/preflight/publication refusal the existing exit 2 error behavior with no summary. Failure paths never substitute an old PASS. Existing error reporting is not globally sanitized by this flag. Task IDs and receipt references remain private metadata, not an automatic public export. Inspect the referenced full evidence and current documentation/reviews before acceptance; compact delivery does not relax execution, cleanup, freshness or review gates.


## Opt-in compact pickup

`resume --summary` delivers version1 fixed context without duplicated saved/current task arrays or saved prose. Default CLI/Workspace.resume output remains unchanged. The compact object includes workflow reason codes, lifecycle counts, changed/unknown flags, context digests, checkpoint issue/reference, optional next-task focus, active count/first3items/omitted count, checkpoint advice with first3reasons/omissions and unknown usage. Normal long-prose/many-history fixtures stay below8KiB; this is delivery volume, not parsing-memory/cost measurement.

A no-follow regular checkpoint acquisition happens before Status/progress; the same immutable bytes are injected through private clock helpers and hashed for the reference. Replacement cannot bind a later file to earlier parsed content or follow an external symlink indirectly. Unsafe/missing/unreadable/invalid/legacy/unsupported context remains explicit; no authority or liveness is inferred. Malformed projected enums/IDs become invalid/unknown, not raw private text. Existing-workspace summary preserves sequential-observation limits. Missing workspace in summary mode returns existing intake/selection guidance without creating state; default resume still refuses it. Git lanes read the original controller. Summary is private operator metadata, not a public export or execution authorization.

Compact acquisition pins no-follow directory descriptors from the canonical project anchor. If the workspace parent is unsafe, it returns unavailable context without inspecting aliased current state; active count/omissions are null because they are unknown, not zero. This does not alter the default full-resume parser.


## Explicit bounded verification capture

New task/release templates opt into `capture:{version:1,mode:"bounded-v1",max_bytes:1048576}`. Exact keys, integer version1 and byte limit1..16777216; booleans/unknown supplied fields are invalid even on new drafts. The budget is shared across both streams/all check attempts, never reset per check. Absence preserves legacy task/API/receipt/timeout behavior; imported history is not migrated. This is capture policy for reviewed task commands, not a global tool sandbox or automatic security classifier.

Bounded mode concurrently drains nonblocking pipes in chunks at most64KiB. Exactly the budget followed by EOF completes; an additional byte terminates the owned group and aborts unattempted checks. Timeout/read failure likewise retains captured prefix and stops later checks. Human-readable UTF-8 replacement strings and base64 raw prefixes are stored privately. Budget bounds retained raw payload, not all task metadata/host memory. observed_bytes stops at terminal capture decision; subsequent cleanup bytes have separate accounting. No truncation may yield a full-evidence PASS, including a process that already exited zero.

Bounded receipts use schema_version2 and include policy, retained/observed/cleanup byte accounting, capture state/completeness, planned/attempted/executed counts and ordered skipped indexes. Results contain attempts, original indexes, launched booleans, actual observed exit codes, previews and exact stream byte/base64 counts. Launch failure remains an attempted result with no child; ordinary failures do not stop subsequent checks. Limit/timeout/capture failure skips only never-attempted checks. Version-aware readers validate policy, lengths, counts, raw/preview consistency and outcome before trusting passed. Unknown/inconsistent versions are invalid; valid incomplete capture is failed. Acceptance still requires current source/input hashes, docs and actual required independent reviews.

Only bounded summaries use schema_version2: existing top-level summary fields plus capture `{state,complete,max_bytes,retained_bytes,planned}`; checks is `{attempted,executed,passed,failed,skipped}`. attempted counts result entries, executed counts spawned children; passed+failed=attempted. New fixed codes capture-limit-exceeded/capture-failed join existing nonzero/timeout/launch/instability codes; first3diagnostics plus omission count remain. No raw/base64/argv/error prose is included. Legacy summaries remain version1 unchanged. Metadata is private operator data, not a public export.

Bounded receipt readers/writers enforce `8*max_bytes+1048576` serialized bytes, including size checks before JSON/base64 decode. Oversize metadata or publication failure attaches no result; an older PASS cannot substitute. Successful complete verification exits0, published failure exits1 and infrastructure/uncertain cleanup exits2. Exact path/hash publication stays under the operation guard. No spooling, automatic retention/deletion, global rollout or specialist/Git-command capture change is included.

## Small experiments and review handoffs

Use [experiment.md](../templates/experiment.md) when an uncertainty blocks useful product work. Record reuse, minimal complete positive/adverse observations, real effects and stop limits before spending on a second harness. A cheap faithful parser/import/child-initialization boundary check can expose a defect before an expensive integration effect. Run actual product-path code; fixture success alone does not establish integration. Supported/unsuitable needs sufficient completed observations; unavailable prerequisites and exhausted budget stay unqualified.

Keep development feedback, focused finding rechecks, stable independent correctness/security review and combined milestone qualification distinct. A local finding correction may receive a focused recheck; materially changed authorization, privacy, interface, process or runtime configuration requires current affected checks/docs/review. All mandatory final coverage remains. Historical reports, synthetic reviewer labels and progress counts cannot certify genuine independence or substitute for current execution. Repeat broad or expensive checks when changed surfaces, failures or unresolved concerns justify them.

Handoff the usable outcome, exact delta/evidence, open acceptance/findings, actual cumulative elapsed/checkpoint/correction observations and next concrete value. Unknown token/billing usage stays unknown. Reaching a limit calls for a visible scope/value reassessment within existing authorization; another checkpoint does not reset the correction history or grant more work. This is host guidance, not measured cost savings or spending enforcement.

## Optional host model choices

[Model delegation](model-delegation.md) adds optional private preferences and portable workspace on/off/status, not a dispatcher or spending gate. Use deterministic tools first, then delegate useful independent work by uncertainty, consequences and checkability. Real available controls and pinned-model/budget authorization govern; no fixed cheap/strong role mapping, automatic costlier escalation or quota retry storm is justified.

Record one meaningful selection/fallback using the optional private template, requested versus observed identity/source/unknown intact. Missing telemetry stays unknown; no savings or diversity-quality claim is measured here. Required unknown actual-model diversity stays host review-pending; off requires explicit owner intent and cannot waive mandatory proof/actors or higher-priority rules. Optional later comparisons need separately bounded authorization and cannot infer general superiority from one run.

## Avoiding unrelated work without weakening proof

For installation-only questions, opt-in `doctor --installation-only [--source PATH]` delivers `{installation_health: ...}` and avoids workspace status/task history and live lane inventory. Registered controller resolution remains necessary; existing installation asset/source scanning and bounded incomplete/unsafe observations remain intact. This reduces unrelated delivery and computation, not the cost of inspecting required asset bytes. Default doctor remains compatible. No task state, configuration, installation or source is repaired or initialized.

Build guidance distinguishes known runner capability restrictions from product failures. Before expensive checks in a changed/restricted environment, a justified cheap capability observation can select an already-authorized capable executor. Neither capable means pending acceptance. Record runner provenance and cumulative attempts; no automatic permission widening, model substitution, skipped tests or reused PASS. Optional focused content feedback precedes stable full qualification where useful, without a new mandatory review cycle. Concise delta handoffs and meaningful process waits retain actual handles, responsiveness and checkpoints. These are host instructions, not CLI scheduling enforcement or measured token savings. Freshness hashing and every current acceptance gate remain unchanged.
