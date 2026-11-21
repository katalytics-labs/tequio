# Architecture

Tequio uses four layers:

1. **Skills**: recognizable workflow entry points and composable stack expertise. They teach the host agent to do substantive analysis, planning, editing and review; they are not an autonomous model runtime.
2. **Role profiles**: orchestrator, implementer, correctness reviewer and adversarial reviewer contracts loaded into available host delegation tools. No fictional native agent type is registered. Delegation follows current host/user authorization and capacity; serial fallback is explicit.
3. **Python standard-library CLI**: portable installer, explicit workspaces, phase/input hashes, detailed task validation, SQLite atomic claims, resource/dependency scheduling, executed check receipts, review receipts and guarded completion/checkpoint/recovery. No API keys or runtime packages required.
4. **Optional adapters**: host-neutral session audit JSON entry point, callable manually or by a separately configured host hook. No implicit global hooks, permission changes or AGENTS.md overwrite.

Install layout: `.tequio/runtime/`, `.tequio/skills/` references, `.tequio/workspaces/<name>/`, `.tequio/manifest.json`, `bin/tequio`, project `.agents/skills/<workflow-and-specialists>/`. Add exact private paths to .gitignore only in a marked owned block; do not assume ignore removes tracked/history/copied private content. Existing AGENTS.md/config stays intact; skills carry entry context and explicit runtime commands. Source launcher uses source module; installed launcher uses copied runtime. Installation is a snapshot, not a dependency on this checkout.

Workspace layout: briefs/, analysis/, plans/, specs/, tasks/, evidence/, reviews/, journal/, verification/, state.sqlite3 and checkpoint.json. SQLite stores workspace state; a project-level POSIX file lock coordinates claim transactions across workspaces. This is single-machine coordination, not a distributed task service. Tasks are JSON (human-readable structured detail), analysis/spec/plan artifacts Markdown. State and evidence remain private. Global mode binds whole-phase inputs and project evidence, including permission modes and documented generated/dependency exclusions. Explicit scoped-v1 tasks bind declared sources/resources/shared contracts/configuration, mandatory brief/spec context, specialist bindings and recursive prerequisite state. Nested symlinks in scoped trees/resources are refused. Changed relevant inputs or prerequisite outputs block dependent operations; unrelated writes can preserve qualified scoped evidence. Completed results remain historical if their current dependencies or content drift. See [freshness](freshness.md) for opt-in, fallback and migration limits. No host hook can make SQLite records trustworthy against a malicious local owner.

Use argument-vector subprocess checks with bounded timeout and POSIX process-group cleanup, no shell interpolation. Deliberately detached children are outside the no-sandbox guarantee. Check output stays in private evidence. Checks are authorized project commands from reviewed task files, not untrusted external documents. CLI state guards constrain CLI transitions; they do not sandbox arbitrary tools or certify that reviewer identities are independent. The skill requires a distinct reviewer where delegation is available and reports unavailable review instead of inventing it.

## Project-specific specialist factory

The tequio-specialists workflow authors packages from actual project stack/context and primary references. specialists.py stores project-owned immutable revisions separately from installer-owned skills, validates declarations, runs bounded isolated exercises and binds structured independent review to the exact receipt/captured material. Readiness is explicit; generated task bindings track exact revision/files/qualification. Candidate research guidance cannot silently become implementation authority. Full contract and private discovery/retention behavior: specialist-factory.md.

The factory includes an optional [coverage guide](../skills/tequio-specialists/references/coverage-guide.md) linking five overlapping discovery areas: frontend (via the preserved conditional [modern web reference](../skills/tequio-specialists/references/modern-web-guidance.md)), backend/data, API/messaging/integration, agentic systems and deployment/operations. These are reference-selection prompts for the existing coverage inventory, not roles, registry categories or quotas; they retain project UX judgment, shared primary-source/execution boundaries and normal exercise/review qualification. Unrelated projects can skip them. They add no specialist catalog, runtime dependency, automatic retrieval/installation or CLI enforcement of agent behavior.

## Generic distribution boundary

The distribution contains only workflow skills, generic role profiles/templates and the specialist factory. All stack-specific expertise and product profiles are project-owned assets outside the framework checkout. Task specialist IDs resolve to qualified project packages, never to workflow entry points. The bundle builder rejects undeclared skill directories and project profiles so accidental additions do not silently enter a release payload. This is a path/inventory guard; public-source review must still inspect content.

## Small user interface, integrated documentation

Optional `$tequio-briefing` precedes the four development phases. It shapes product intent through a few adaptive questions and stops when problem, users, main use case, initial scope and major constraints are clear enough to investigate, retaining uncertainty. It saves private drafts/resume notes under `.tequio/intake/<name>/` before workspace creation; this is agent guidance, not a new CLI phase or managed intake state. Existing usable briefs bypass it. Explore owns proportionate research, reusing supplied evidence or investigating material gaps. User review establishes intent rather than implementation authorization. No-workspace orientation recommends briefing and the existing-brief bypass without writing state; existing workspace readiness remains unchanged.

The everyday surface is `$tequio-explore` → `$tequio-design` → `$tequio-tasks` → `$tequio-build`, with status for orientation/help. Supporting skills are modular internals/advanced entry points; documentation and guide behavior do not add skills. Orientation reads SQLite without an execution-state transaction, reports recorded phases/tasks and recommends a next action; it does not create workspaces, recover claims or certify live processes.

Ready task documentation impact is explicit. Claim preserves an initial doc-content baseline. After implementation/docs and fresh checks, a private source-to-actual reconciliation receipt captures current inputs/project state/report hash. Update paths must be owned and materially changed; not-needed requires a reason. Correctness review binds the current receipt. Completion rejects missing/stale/altered receipts or older review. Stored task JSON carries this metadata without changing the SQLite schema. Legacy unfinished tasks without a policy need explicit replan. This enforces recorded evidence, not semantic documentation truth.

## Optional Git isolation and host orchestration

Read-only status detects an existing Git repository, including linked worktrees; no hosting provider is required. Explicit opt-in enables sibling branch/worktree lanes. Default shared-folder coordination remains supported with or without Git. Lane pointers reference the original authoritative controller; lifecycle mutation from a lane is refused, and read-only status/proof reads the original controller. Claims do not automatically synchronize separate databases, sandbox edits or establish task-to-lane identity. See [Git isolation](git-isolation.md).

The host orchestrator selects and dispatches agents. A private workspace run-policy can authorize a bounded backlog and local worker commits plus serial orchestrator merges. These are agent instructions with native Git, not a CLI-enforced permission service, background daemon, automatic scheduler or continuation guarantee. The integrated result needs actual current verification, documentation and independent review. Push/publication remains separately authorized.

## Read-only evidence inspection

`proof [TASK]` reads authoritative records through SQLite read-only access and returns allowlisted source/file/evidence references, check totals and current/missing/failed/stale/invalid/historical state. Dependencies are checked recursively. It omits raw commands, outputs, task tokens and private report prose; it is a local operator report, not an automatic public export. Declared acceptance associations are not semantic coverage or authenticated independence. See [evidence reporting](evidence-report.md).

Installation metadata records the executing installer release from the package version constant; runtime/skill payloads retain independently validated path hashes. There is no separate hardcoded release string in the installer.

## Local verification operations and run context

`verification.py` holds a per-task POSIX operation lock across check execution and result attachment. Versioned private attempt observations retain controller/child/process-group information across interruption. Recovery/release/reassignment and acceptance operations consult this guard; expired lease is not permission to overlap a known live check. Same-token liveness renewal is separate from execution freshness. There is no watchdog or automatic recovery kill. Unknown launch state and stale group identity remain deliberately conservative. See [the exact recovery contract](check-recovery.md).

An explicit owner release clears current owner, token and lease together; claimed-actor history remains in events. Supported inspected recovery also normalizes an older released-ready row only when it retains a nonempty owner but token, lease, checks and reviews are all null. This metadata-only path does not require current execution dependencies and cannot adopt an ordinary unowned-ready task. Held/live/unknown verification still refuses it, including unknown state with a stopped-check acknowledgement; known absent recorded groups retain normal reconciliation. Existing running/review/blocked recovery rules and fresh claim/acceptance requirements remain unchanged.

`run_context.py` snapshots canonical policy content and immutable stored task definitions separately from progress. Versioned checkpoint/resume reports changed policy/scope/progress, legacy unknown context and damaged-state diagnostics without repairing files. Policy structural validity and digests are observations, not approval, semantic run-scope validation or authenticated authorization. The host still reconciles current user instructions. See [run context](run-context.md). Git lane inspections now compare actual checkout/common directory/branch/HEAD and index/worktree/operation state with registry expectations; they neither choose an accepted commit nor perform integration.

## Exact-commit integration journal

`integration.py` lazily creates immutable intent and append-only observation tables in the existing workspace SQLite database. Owner-token-authenticated planning binds one task/lane/full SHA to a local target branch/repository/base. Observation-only reconciliation cannot reconfirm a replacement owner or mutate Git. Consecutive unchanged observations deduplicate; repeated state transitions remain in history. No journal is created by read-only inspection or journal-free work.

The first valid integrated observation captures baseline references and a monotonic lifecycle-event barrier. Verification and closure consult current Git facts and require new matching evidence publications afterward; receipts bind the commit, target HEAD and owner epoch. Core operation locks and task/receipt integrity guards remain mandatory. Status/resume/proof include safe current diagnostics and the original immutable identity. This is trusted local audit data, not a cryptographic signature, semantic coverage certificate, automatic Git engine or atomic Git/filesystem/SQLite transaction. [Exact contract](integration-journal.md).

## Task batch authoring review

`task_review.py` binds a canonical proposed batch and current phase inputs to its author plus distinct correctness/redteam report receipts in existing workspace metadata/events. Import requires both reports with no findings and unchanged bytes. No new public skill, background service or task-body mutation is introduced. Historical tasks are not retroactively reassessed. Identity/semantic limits and the separate implementation review gates are documented in task-review.md.

## Execution checkpoint observations

Optional version1 execution_checkpoints policy adds structural validation and host-guided time/loop boundaries. Internal progress reads task lifecycle labels and allowlisted event publications in a read-only SQLite snapshot, plus matching checkpoint/policy observations. It emits fixed counters and diagnostics without task/report/policy prose. It does not verify acceptance, count all host activity, measure tokens/billing, enforce spending or alter freshness/reviewer gates. Missing/corrupt/drifted observations stay unknown. [Contract and limits](execution-efficiency.md).

## Installing into the Tequio source checkout

Run `python3 bin/tequio install /absolute/path/to/this-checkout` from reviewed source to add project-local skills and private runtime/reference snapshots to the same directory. Resolved source and target must be identical for `source-checkout` mode. The existing safe regular source `bin/tequio` remains untouched, including permissions, and is never installer-owned or newly ignored. Installation refuses to convert a manifest that already owns that launcher. Ordinary different-source collisions and modified-owned-file refusals remain unchanged. Uninstall removes only owned private assets and retains the source launcher and workspace evidence.

In this mode `bin/tequio` deliberately continues executing current `src/` code; copied runtime/assets and skill discovery are installation snapshots. This is not a frozen execution controller. After reviewed changes, rebuild the source bundle and explicitly reinstall to refresh snapshots; a new agent session discovers the installed project-local skills. No global hooks/settings, external project upgrades or automatic live-state migrations are implied.


## On-demand installation health

`doctor [--source PATH]` preserves task/intake/git observations and adds version1 `installation_health` even without a workspace. Its execution, installation, owned and source_comparison objects distinguish executing layout/version, recorded snapshot metadata, owned byte/mode drift and an explicitly selected source. An intact older snapshot can coexist with live source; equal versions do not imply equal payload. Exit0 means observations were delivered, not pristine assets or permission to upgrade.

Ordinary Status/hook/resume never scan owned assets. Doctor never repairs, fetches, imports selected source, creates a workspace or changes launcher/ignore/metadata. Unsafe manifest paths yield null-path diagnostics and are not read/echoed; only installer namespaces/known workflow discovery assets are eligible. Manifests are capped at4MiB, paths10000 and asset bytes256MiB per observation; limit exhaustion is incomplete, not intact. Issues/differences cap10 with total/omitted counts. Missing, invalid and unavailable states stay distinct. Source comparison captures and validates bounded bytes before pure prefix rendering and parses the version constant with AST. It is sequential local evidence, not atomic/authenticated ownership or public-safe metadata. Existing collision/modified-owned/refusal/removal protections remain unchanged; real snapshot refresh is a separate action.

## Reviewed revision projection

[Revision](revision.md) adds an advanced prepare/review/apply operation to existing Tasks/Redirect. Immutable task definitions and raw evidence stay intact; append-only SQLite revision and per-consumer binding history feed a current effective-dependency/input projection shared by lifecycle, recursive freshness, reporting, integration and graph validation. Rebinding stales prior proof; it never aliases completed results. Apply revalidates current context and affected operation guards and commits the entire change atomically. No-overlay hashes retain existing behavior. Capability checks protect supported runtimes only; overlay-workspace downgrade to old runtimes is unsupported.

Small experiments use optional guidance/templates and ordinary task acceptance. They add no runtime task kind, experiment manager, semantic freshness exemption or billing subsystem.

## Optional model-policy control

The optional version1 model_delegation block extends existing run-context structural validity/full-policy digest observations. `routing on|off|status` is a deterministic bounded workspace configuration control, with no new database ledger or review/complete schema. The sixteenth portable workflow skill carries the complete installed contract; [model-delegation.md](model-delegation.md) explains source adoption and limits. No provider SDK/model runtime, scheduler, authentication or actual-model comparison is introduced. Required diversity is a host instruction, not a CLI acceptance guarantee; mandatory independent actors and current evidence remain unchanged.

## Focused installation diagnosis

`doctor --installation-only [--source PATH]` returns only the existing `installation_health` object. It resolves a registered lane’s controller identity but bypasses workspace construction/status and live lane inventory. Missing or corrupt task state does not obstruct this installation observation. Asset/source scans, privacy limits, omissions and exit semantics remain unchanged; exit0 reports observations, not pristine health or permission to repair. Default doctor output is preserved.

## Milestone-aware Status guidance

The Status skill composes a short outcome overview and, for substantial scope, a compact milestone docket from existing plans/handoffs plus targeted current task/evidence reads. It distinguishes historical completion, integration, qualification and owner/device acceptance; superseded envelopes and successor coverage are reconciled without a new ledger. Tiny/explicitly brief requests remain short. Requested unattended/parallel suggestions retain dependencies, ownership, setup and authorization limits. CLI status/schema and read-only behavior are unchanged; agent-written orientation is not deterministic semantic verification. No project-private example data ships.

## Current prerequisite evidence and recovery

Dependency checks traverse effective prerequisites root-first and report the first causal incomplete/invalid/changed input, output or scoped-context result. Context-only snapshot diagnostics do not invent historical component diffs. Existing reviewed successors plus explicit unfinished-consumer rebind provide [history-preserving recovery](prerequisite-recovery.md); no completion reset, evidence alias or new lifecycle table is added. Revision context retains history/source hashes without treating completed specialist bindings as live work. Current dispatch and successor qualification remain conservative.
