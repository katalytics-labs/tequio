# Validation and limits

## Current 0.18.0 qualification

Version 0.18.0 has 395 passing framework tests on macOS with CPython 3.14.5. The older multi-version results below are historical qualification, not a new test claim for this release. Three deterministic example runners and standalone snapshot installation are also exercised. Run from the source folder:

```sh
python3 tools/build_bundle.py
python3 -m unittest discover -s tests -v
python3 examples/quickstart/run_demo.py
python3 examples/existing-project/run_demo.py
python3 examples/integrated-build/run_demo.py
```

The current bundle records 65 runtime/skill/role/template/profile/licence payload paths. It contains sixteen workflow skills (including optional briefing preparation and routing control), four generic role profiles and a specialist factory; no prebuilt project/stack specialists ship. Test counts include inherited lifecycle cases exercised again under scoped policy, not wholly independent product scenarios.

Coverage includes installation/upgrade/removal, current installer version metadata and MIT retention, source bundle integrity/collisions, dependency/resource/concurrent claims, global fallback and opt-in scoped freshness, recursive prerequisites, nested-symlink/reserved-path refusal, real command checks, docs/review gates, read-only proof with malformed/tampered/stale/history cases, guarded local verification/recovery/acceptance and ownership-independent heartbeat, checkpoint policy/scope/progress and damaged-state diagnostics, optional Git/non-Git paths, dirty/collision/partial-failure preservation, lane controller routing and actual branch/root/common-dir/index/worktree/operation health, orientation and project-owned specialist qualification/discovery.

The quickstart and existing-project example execute real code/checks and refuse closure without genuine independent review. The integrated replay runs a curated 25-test query/export/CLI application, independent concurrent claims, A evidence through B writes, fresh-process checkpoint inspection, missing-review refusal and changed-source invalidation. All replay code is prebuilt; it does not simulate model discovery or authenticated review. Live-agent observations and version-specific limits are in [compatibility](compatibility.md) and the [walkthrough](../examples/integrated-build/README.md).

## Evidence boundaries

- Format, phase, receipt and content checks do not establish semantic requirement coverage, source authority, prose correctness or product readiness. Proof's source/acceptance associations are declarations.
- Reviewer IDs are audit metadata, not authenticated identities. A distinct string is insufficient: the host workflow must supply genuine delivered review.
- CLI guards constrain their own transitions; they do not sandbox arbitrary edits or authorize external/destructive/publication actions.
- Concurrency is single-machine project-local SQLite/POSIX coordination. Worktree files are isolated when enabled, but central claims remain authoritative. No distributed/network-filesystem qualification is made.
- Explicit scoped freshness depends on complete declared reads/contracts/config/context; global fallback is conservative. Undeclared dependencies require engineering review and final integration checks. Global phase orientation remains conservative even when scoped work can continue.
- Ordinary process groups are cleaned up; deliberately detached services require live-handle reconciliation. Failed/expired claims do not prove all processes stopped.
- Installer preflights hashes and owned paths/modes; it is not transactional against power loss, disk exhaustion or hostile concurrent mutation.
- Git partial failure preserves reported work for inspection. No automatic destructive rollback, cleanup, commit, merge or push is implemented by the helper. Authorized native Git integration is performed by the host agent under the run policy.
- A backlog run policy guides that host, not a background scheduler or enforced permission service. Session limits/blockers require checkpoints and actual host continuation.
- Specialists are qualified for recorded bounded versions/context/exercises. Format-valid is not expert; material or evidence changes require refresh.
- Proof omits tokens/raw output/private prose but displays local source/file references; it is not an automatic safe public export.

## Unqualified configurations

Linux, Python 3.11, Windows, native graphical skill discovery/automatic selection quality, other harnesses and general host-agent crash recovery remain unqualified. Windows is unsupported. No matched-control benchmark, adoption study, measured general speedup or guarantee of overnight product completion is claimed. Model-provider billing was not independently measured. Runtime/tests/replays need no provider key or third-party package; actual live-agent observations used existing host authentication.

Machine-local conversations, raw logs, databases, prompts, generated project specialists and private reports are excluded from this distribution. Reproduce current checks with the included tests/examples.

Curated distribution validation excludes generated Python caches and checks the complete file/hash inventory, relative documentation links and generic-only asset boundary before promotion. A content scan supplements these path checks; a path allowlist alone cannot certify privacy.

## Recovery and continuity cases

Nine focused verification/recovery tests and independent actual CLI-process probes cover check/recover/acceptance overlap across lease expiry, a killed controller with surviving child, duplicate verification, stopped acknowledgement limits, stale-input heartbeat, invalid caller/evidence preservation and metadata/database persistence faults. Twelve focused run-context cases cover canonical policy drift, task import vs progress, read-only/no-private-prose output, legacy and damaged checkpoint handling. Nine lane-health tests and independent linked-worktree probes cover actual mismatches and operation markers without registry/index mutation. These counts are included in 200, not additional to it. Reproduce focused cases using `python3 -m unittest discover -s tests -p test_verification_recovery.py -v` (or test_resume_context.py / test_lane_health.py).

Structural policy validity does not prove a referenced task exists or authorize its execution; actual ready-task/dependency/freshness gates and host scope reconciliation still apply. Local operation observations are conservative, do not authenticate liveness and do not cover detached/remote workers, PID reuse, malicious state edits or network filesystems. See the exact [local recovery](check-recovery.md) and [run-context](run-context.md) contracts before making broader claims.

## Integration journal qualification

Twenty-four integration cases are included in200. They cover the actual merge/evidence lifecycle through fresh CLI observations, exact immutable intent inspection, owner epochs, post-boundary lifecycle publications, target HEAD drift, nested ownership/rename checks, missing objects/source lanes, dirty/conflicted/detached/rewritten states, deduplication and recurring history, primary-DB rollback, malformed/orphan records and preserved Git/index/registry state. Synthetic reviewer labels inside unit tests are fixtures, not claims of independent model review.

Independent source/security reviews and a separate actual fresh-agent synthetic project exercise are retained privately. After a real merge the new agent observed integrated-unrecorded, reconciled to needs-checks, and made no Git mutation. Actual tests/docs and its genuinely delivered review preceded closure and accepted observation. This is not a production or performance benchmark. Root-independent final qualification checks the complete source/public hashes, MIT/generic assets, links/private boundaries and standalone installed journal/context APIs. No raw conversations/tokens/private reports or specialist packages are distributed.

Journal evidence is trusted local audit metadata. Deleting/editing local databases, replacing repositories, detached external activity and concurrent native Git mutations are not sandboxed. Status can be unknown or blocked; it is not permission to retry a merge. A historically accepted task may require a new explicit milestone qualification after later target/context drift.

## Security workflow qualification

Eight focused security cases and an additional integration migration regression cover explicit assessments, malformed drafts, release scope/report requirements, distinct review kinds, missing output, candidate/dependency/configuration drift in both freshness modes, legacy unfinished migration and historical readability. Counts are included in200. Genuine independent correctness and adversarial reviews found and resolved diagnostic and freshness gaps; actual separate actors exercised an installed normal task and sensitive task through completion, including an observed missing-security refusal. A release fixture had current independent correctness/security receipts; changing candidate configuration then correctly refused completion. Its deliberately changed state is retained as a blocked negative fixture, not a released product.

The integrated candidate must be inside the controlled project. External copy comparison remains a host procedure; runtime does not bind remote destinations. Declared surface/scope completeness, report meaning and actual reviewer independence require engineering judgment. No vulnerability scan, exhaustive fuzzing or production security certification is claimed.

## 0.8.0 task-authoring review qualification

New batches, including drafts, require distinct correctness and red-team reports before import. Tests cover absent reviews, author/reviewer separation, open findings, wrong batch/report coverage, canonical task content, phase and cited-source drift, ready-specialist binding drift, tampering/deletion and report replacement between read and receipt. Historical task state is not retroactively changed. The report race found in independent review was fixed by parsing and hashing the same byte buffer; source-context drift was fixed by including every cited source and ready-specialist bindings.

Unit/demonstration receipts are explicitly synthetic and do not qualify actual reviewer independence. Source correctness and adversarial reviews were performed separately; their two concrete binding findings were corrected and re-reviewed. Import binding is not continuous authentication after import, and actor strings cannot prove identities.

## 0.9.0 briefing preparation

The optional briefing skill adds focused intent discovery before the four development phases. Installation/default-prefix discovery and a synthetic prior-inventory upgrade are exercised; no-workspace status remains read-only and an existing workspace still enters Explore. The bundle includes the new skill, and installer release metadata continues to come from the package version constant. The complete framework suite and all three examples are run for this release; examples preserve their documented synthetic-review limitations.

Independent correctness and adversarial review inspect the conversational stopping rule, private drafts, authorization boundary, research ownership and current release candidate. These are instruction and integration checks, not evidence that a fresh unseeded real-user briefing conversation has been exercised. Research completeness, useful questions and semantic brief quality remain host-agent responsibilities; CLI receipts do not certify them.

## 0.10.0 execution-efficiency qualification

Version 0.10.0 adds optional checkpoint policy validation and read-only progress observations with ten fresh synthetic/real-check regression cases. The prior 0.9.0 release recorded 231 framework tests; seven development-tool cases and these ten new cases bring the current suite to 248. The payload inventory has 52 paths, including the new observation module. Tests exercise legacy/malformed policy, missing/damaged/future/policy-drift clocks, recorded failed/successful verification and reviewer-kind counts, privacy/read-only behavior, lane/intake routing and preserved acceptance gates. Reproduce with `python3 -m unittest discover -s tests -p test_execution_progress.py -v`, then run the full suite and all three examples. All 248 framework tests pass on the three listed local CPython versions, and all three examples pass. Separate actual correctness and release security reviews inspect the current source, documentation and candidate inventory. This source qualification does not establish token savings, useful host behavior, billing measurements or installation into another product. Project-specific rollout remains separately authorized.


## 0.11.0 workflow usability and readiness qualification

This release combines source-checkout installation, sourced draft decisions, damaged-proof/prefixed-instruction repairs, additive Status checkpoint advice and opt-in compact verification. The suite grows from 248 to 269 tests: four source-install cases, six readiness cases, three proof/prefix cases, two Status cases and six summary cases. Existing lifecycle fixtures explicitly declare synthetic draft decisions; they do not manufacture live independent review.

Tests exercise preserved launcher/ownership/upgrade/removal boundaries, malformed first/later proof bodies and neighboring observations, private-safe journal fallback, prefixed discovery/reference instructions and CRLF handling, fixed draft category/type/source/action validation at preparation/review/import, legacy imported history, and ready tasks waiting on dependencies. Status reuses progress semantics without changing readiness, intake/lane routing or authorization; unavailable observations have a fixed envelope and unknown usage.

Summary qualification covers default CLI/API compatibility, fixed codes/counts/three-item diagnostic cap, private output omission, invalid UTF-8, timeouts/launch failures/instability, exact receipt references despite a later verification and no old-PASS fallback after refusal/publication failure. An isolated installed launcher produced 46,482 default JSON bytes versus 340 summary bytes for a 2,000-line check, retaining all 44,001 stdout bytes in its private receipt. This is an output-volume observation, not a token/cost or latency benchmark; capture/storage bounds remain unchanged.

One fresh agent in a synthetic prefixed installation surfaced overdue checkpoint advice and the correct next command without requiring the owner to learn progress. All preexisting/state bytes were preserved; Python generated 13 runtime bytecode caches, so total-directory equality is not claimed. This bounded observation does not certify universal host usability or semantic task quality. Sourced draft metadata validates structure, not the truth of its justification; actual reviewers still challenge every draft and preserve genuine unknowns.

The complete current suite, all three examples and source inventory/bundle checks qualify the integrated candidate. Actual independent correctness and structured release security reviews cover the source candidate, dependencies, configuration and private-data boundaries. Private records and installed snapshots are excluded from committed product files. Source qualification and an authorized private development push do not authorize public export/publication, real-project upgrades or global configuration changes.

## 0.12.0 status, health, pickup and bounded capture

This release adds clearer next-evidence prerequisites and draft blockers, on-demand installation health with explicit source comparison, opt-in compact pickup with same-read checkpoint provenance, and opt-in attempt-wide bounded verification capture. New task templates select a 1MiB capture budget; existing tasks without a capture policy retain legacy execution and receipt behavior. Bounded capture distinguishes attempts, launched checks and skipped checks, retains raw prefixes privately, and refuses acceptance when capture or cleanup is incomplete.

The historical 0.12.0 331-test suite and all three examples pass on the local macOS/CPython configuration above. Focused tests cover unsafe paths and bounded health scans, compact resume privacy and damaged checkpoints, real dual-pipe capture, exact/excess budgets, timeout evidence, cleanup uncertainty, receipt corruption and publication failures. A disposable installed prefixed CLI confirms bounded schema2 success/failure, legacy schema1 success and publication refusal without raw/base64 output in summaries. Distinct actual correctness and security reviews cover the combined implementation. These controlled fixtures do not establish general model behavior, OS containment, token savings or production security certification.

## 0.13.0 proportional-workflow qualification

Version 0.13.0 introduces the reviewed proportional-workflow changes. The combined suite has363 passing tests on local macOS/CPython3.14.5 and all three maintained examples pass. The historical 0.13.0 bundle contains56 payload paths; no extra workflow skill or runtime dependency is introduced. Existing multi-version/platform results remain historical.

Eighteen revision-engine and five CLI tests cover strict reviewed proposals, effective dependency/input bindings, actual operation guards, transaction rollback/retry, immutable history, independent proof preservation and installed-controller routing. Four policy cases execute current-byte privacy controls and successor migration, with source/config/interface/overlap/global negatives. Five proportional-flow cases measure actual task churn and operation events, current correctness/security gate refusal, fresh-process adapter boundary checks, adverse observations and unqualified missing/budget paths. New fixtures avoid inheriting or rediscovering a second copy of the lifecycle suite. Counts still include older inherited cases elsewhere and are not363 independent product scenarios.

The before/after fixture supersedes6 versus1 old IDs, authors7 versus2 definitions and uses7 versus4 refinement operations after common setup. Both paths use review gates. These deterministic counts establish neither token savings nor model behavior. Experiment classifications remain host guidance, not a new runtime subsystem. The child test verifies module import/parser/context selection, not actual worker startup; the effect sentinel is local, not a service.

Actual distinct implementation correctness/security reviews assess current combined source, documentation and evidence; synthetic actors in tests demonstrate only gate mechanics. Required final checks run current commands rather than parsing earlier PASS records. Private evidence stays outside shipped assets. Source qualification authorizes no rollout, version bump, commit/push, export or publication. Reproduce the two focused files above, then the full suite and all three examples listed at the top.


## 0.14.0 model delegation and routing control

Current source adds the sixteenth optional workflow skill, Routing, plus optional model-policy validation, deterministic workspace on/off/status and private provenance guidance/templates. Version 0.14.0 qualification covers 386 tests and all three maintained examples on local macOS/CPython3.14.5, with 58 current bundle payloads. Current check receipts and actual independent reviews qualify these release bytes; historical release/platform results do not.

Required qualification covers exact schema/caps/disabled-invalid/legacy behavior, canonical policy digests and checkpoint drift, private compact output, bounded safe routing IO/no-op/concurrent replacement/publication failures, ordinary/security lifecycle gates, actual default/prefixed installed commands and payload-resident references. Synthetic identity fixtures demonstrate mechanics only. Actual independent correctness/security review must assess unknown alias, request-versus-observed fallback, no selection control, quota fallback, pinned models, explicit off and required pending scenarios.

The CLI neither launches/authenticates/compares models nor enforces required diversity in review/complete. Tests cannot establish model-selection quality, authenticated provenance, genuine reviewer independence or cost savings. No provider benchmark, target installation, global configuration or release is implied. See [model delegation](model-delegation.md) for the complete boundary.

## 0.15.0 specialist reference foundations

The factory includes optional source-selection guidance for UI/UX/frontend, backend/data, APIs/messaging/integration, agentic systems and deployment/operations, with the existing modern web reference retained. Areas are overlapping discovery prompts, not built-in specialists or new workflow commands. Source, authorization, privacy and qualification boundaries remain explicit; local persistence and local deployment concerns are included when relevant.

Release qualification covers 386 framework tests and all three maintained deterministic examples on local macOS/CPython 3.14.5, with 64 bundle payload files. Relative reference links and bundle hashes are inspected alongside independent correctness and security review. Private instruction walkthroughs assess the guidance; they do not prove autonomous agent compliance, model savings, generated-specialist expertise or live deployment recovery. No runtime schema/API, new dependency or automatic installation/deployment behavior is added. Earlier version-specific sections are historical qualification records.

## 0.16.0 focused diagnostics and check placement

Opt-in `doctor --installation-only` preserves existing installation-health facts and registered-controller resolution while avoiding workspace status and live lane inventory. Default doctor stays unchanged. Five added regression tests cover source choices, missing/damaged workspace, registered controller and invalid pointer handling, unsafe observations, read-only behavior and synthetic history delivery. Build/Status guidance improves runner capability selection, focused feedback and compact coordination without weakening acceptance, authorization, freshness or independent review.

Release qualification: 391 tests and all three maintained examples on local macOS/CPython3.14.5; 64 bundle payload files. A synthetic300-history fixture delivered171473 versus586 JSON bytes with identical installation health; this is bounded delivery evidence, not general timing/token savings. Actual independent correctness/security release review complements deterministic checks. No target installation refresh or automatic privilege/model change is included.

## 0.17.0 milestone-aware Status

Status guidance adds adaptive outcome overview and evidence-backed milestone docket, using existing plans/task/evidence and preserving short/intake responses. No CLI schema or milestone store changes. Local qualification covers391 framework tests and all three examples, with65 bundle payloads. Actual independent reviewers assess private synthetic Markdown response scenarios for legacy/successor scope, backend/client gaps, design/owner approval, synthetic/device limits, changed bindings, blocked prerequisites, brevity and unattended/parallel authority. These authored instruction scenarios are not autonomous host trials or proof of semantic compliance. No real-project records enter reusable guidance; downstream snapshot refresh remains separate.

## 0.18.0 completed prerequisite evidence recovery

Dependency refusal/status diagnostics identify the first causal stale prerequisite and distinguish changed inputs, owned outputs, scoped context or unavailable evidence. Context-only aggregate snapshots do not establish exact changed historical paths. Existing reviewed fresh successors and explicit unfinished-consumer dependency rebind provide supported recovery without rewriting completed history, reusing old receipts or introducing an evidence alias/lifecycle. Scoped revision retains historical sources/state while resolving live specialist bindings only for unfinished/new work; dispatch freshness remains enforced.

Qualification covers395 framework tests and all three maintained examples on local macOS/CPython3.14.5,65 bundle payloads, and actual independent correctness/security review. Four added synthetic recovery tests cover transitive context drift and fresh reviewed successor recovery, immutable historical rows/receipts, failed output checks/subsequent drift, completed versus live specialist context and fail-closed unavailable diagnostics. Private project-specific recovery instructions do not ship in the distribution. No downstream project mutation, automatic recovery or task migration is included.
