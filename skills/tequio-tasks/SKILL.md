---
name: tequio-tasks
description: "Write detailed dependency-aware executable task shards from a current analysis and plan, keeping complete scope visible."
---

# Tequio Tasks

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Read current brief/analysis/specs/plan and `status`. Read `.tequio/templates/task.json` and `.tequio/templates/task-contract.md`. Produce a JSON task array in workspace tasks/ for `import-tasks <file>`. Every task needs a testable outcome, scope/exclusions, actual workspace-relative source sections, concrete project-relative read/write resources, acceptance criteria, executable argv checks, dependencies, specialists, risk and durable handoff expectations.

Keep the entire agreed scope represented. Mark not-yet-ready work `stage: draft`; do not encode unresolved product decisions as executable instructions. An execution-ready shard must fit one bounded agent pass with a coherent outcome. Split when cross-cutting reasoning or simultaneous invariants make verification unreliable, not to hide missing scope. Name integration checks explicitly; a rendered component with fake data is not an integrated outcome.

Finish specifying every agreed task within the current Tasks pass. Resolve routine agent-owned interface, schema, check and test choices from the current contracts; a ready starter does not justify parking the remainder. Preserve genuine unresolved product, security or authorization decisions rather than guessing them. For each remaining draft, supply the sourced decision record described in [task review](references/task-review.md), with a concrete resolution action. A fully specified task waiting on dependencies can be ready; dependency waiting alone does not imply draft. An empty specialist registry does not prove ordinary work needs a generated specialist. Order tasks by dependencies and user value. Include testing, docs and relevant failure paths in outcomes. Use file/directory prefixes (no glob) as ownership boundaries; overlapping writes or read/write dependencies serialize. Shared contracts have one owner. Also check sequential downstream writes against completed prerequisite evidence: serialized writes can still invalidate ancestor hashes; plan supported reconciliation or different boundaries. Before import, obtain a distinct correctness review and red-team review of the exact batch. The author, correctness reviewer and red-team reviewer must be different actual actors; never invent reports. Use internal prepare-tasks/review-tasks, then import. Import enforces current content/context/report receipts as well as schema/dependencies. See [task review](references/task-review.md) for report coverage; the installed templates are under .tequio/templates/. Do not implement during todo writing.

## Specialist coverage

Before execution-ready task creation, inspect relevant project-owned skills and `specialists list`. Use tequio-specialists when stack coverage is missing or materially changed. Reuse existing guidance first; do not create a specialist for every dependency. Generated skills require current exercise-tested qualification for ready task use. Read the resolved package path from task specialist bindings; research-only specialists require research tasks. Missing qualification stays draft/blocked rather than being invented.

Every ready task declares `documentation`: update concrete owned paths and explain impact, or explicitly justify `not-needed`. Include source reconciliation and current documentation in acceptance/review. Shared docs must have clear ownership; split/serialize writes rather than send multiple agents to the same document.

## One bounded existing-project task

A small bug or feature may use a single task covering the real correction, regression tests and current docs. Link the exact focused brief/analysis/spec/plan files in `sources`; use actual file or directory ownership prefixes and declare relevant read dependencies, including preserved shared contracts. Keep acceptance observable: the reproducer now passes, nearby behavior remains valid, and affected failure paths behave as specified. Use real executable argv checks; a zero-exit placeholder is not evidence.

Do not require a whole-product backlog for excluded work. Preserve all agreed change scope, source-linked nonempty artifacts, dependency/ownership rules and documentation declaration. Reuse qualified existing specialists where relevant; an empty specialist list is appropriate when no additional specialist is needed, not a substitute for missing expertise. Import through the normal contract.

## Security workflow

Declare an explicit security assessment for each ready task and challenge its classification. Use `kind: release` and candidate paths for integrated release work. Read [security workflow](../tequio-tasks/references/security-workflow.md) for the finite categories, ready/draft contract and legacy migration; use release-task.json when applicable.

## Task-authoring review commands

Run `prepare-tasks <workspace-task-array> --author <actual-author>` to obtain the exact batch ID. Give the actual candidate and relevant source context to separate correctness and red-team reviewers. Reports use `.tequio/templates/task-review-correctness.json` and `task-review-redteam.json`. Record each with `review-tasks <batch> --actor <actual-reviewer> --kind correctness|redteam --report <workspace-relative-json>`. Resolve findings and re-review changed batches before `import-tasks`. This is agent orchestration, not another owner approval loop; it does not authorize Build. Missing actual reviewers means retain the explicit review gap, not fabricated passing receipts.

## Qualification surface and execution cost

Before declaring a task bounded, inventory its distinct acceptance surfaces, dependencies, fixtures, failure controls and expensive external effects. A single title or short implementation does not make a task with many independent qualification surfaces a one-pass chunk. Prefer coherent executable workflow slices with meaningful integration ownership; preserve the complete agreed requirements and final integrated proof. Avoid both one sprawling qualification task and dozens of microtasks paying the full lifecycle for trivial edits. Explain any deliberately large slice and its intermediate checkpoints.

Separate cheap development checks from expensive/live acceptance where a reviewed dependency and freshness boundary actually supports that separation. Plan candidate/docs stabilization before external effects, reserve resource/usage headroom for material corrections, and keep run limits/checkpoints explicit. Do not move mandatory proof out of scope to make progress look better or assume hidden provider telemetry. Planning review should challenge an open task accumulating review/verification cycles without a path to closure.


New task/release templates declare `capture:{version:1,mode:bounded-v1,max_bytes:1048576}`: one retained raw-byte budget across stdout/stderr and all checks. Existing tasks without this field keep legacy behavior; never retrofit imported definitions. Consider output volume and actual effects while authoring; supplied limits must be integers1..16777216. Limit/timeout/capture failure retains a bounded private prefix and fails rather than accepting truncated evidence. Use supported replan when a policy truly needs changing; no automatic retries of expensive effects or old-PASS reuse.

Bounded receipts/summaries use version2 with attempted versus actually executed counts and explicit skipped checks. Failed launch is an attempt, not an executed child or skipped check. Inspect exact private receipt evidence on failure; raw/base64 output never belongs in compact delivery. Unknown cleanup requires actual handle inspection, not inferred process death. Capture policy does not grant command authorization or automatically classify every project task as security-sensitive.

## Reviewed bounded revision

For selected unfinished producer refinement, use the `revise` family below. The complete source documentation is `docs/revision.md`; installed projects use this skill as their standalone reference. Strict version1 proposal keys are `version,reason,supersede,replacements,tasks,rebindings`. Explicit ordered `from`/`to` vectors rebind only definition-unchanged unowned unfinished consumers; changed checks/acceptance/contracts require new IDs. Preview old/new edges, descendants, completed historical impact and retained branches. Prepare with an actual author; obtain separate actual correctness/redteam revision reviews, then apply the exact digest. Import review cannot authorize revision. Rebind-only uses empty supersede/replacements/tasks; add-only successors use ordinary reviewed import first. Completed bodies/results remain untouched and stale historical prerequisites cannot support new acceptance. Broad replan remains available.

New effective input bindings stale old consumer checks/docs/reviews even when bytes match. Do not alter phase files just to narrate mechanical refinement; actual source changes still need current phases/proof. Require backup/explicit runtime upgrade before overlays; old-runtime downgrade is unsupported.

Use optional experiment.md for genuine uncertainty: product blockage, reuse, faithful positive/adverse observations, effects, limits, decision and next slice. Keep it out of mandatory task schema. Declare policy/functional boundaries using actual disjoint scoped-v1 resources, with final acceptance depending on both; overlap/shared contracts/legacy histories stay conservative.

### Standalone revision reference

Use the explicit controller/project/workspace arguments from Runtime above. Proposal/report paths are workspace-relative; read-only preview/status do not initialize state. Commands:

```text
revise preview --proposal tasks/refinement.json
revise prepare --proposal tasks/refinement.json --author AUTHOR
revise review REVISION --actor REVIEWER --kind correctness --report reviews/correctness.json
revise review REVISION --actor OTHER_REVIEWER --kind redteam --report reviews/redteam.json
revise status REVISION
revise apply --revision DIGEST
```

Prepare returns the exact `revision` digest; author and both actual reviewers must differ. A proposal is an exact-key JSON object `{ "version": 1, "reason": "Explain the bounded refinement", "supersede": ["OLD"], "replacements": {"OLD": ["NEW"]}, "tasks": [FULL_NEW_TASK_DEFINITION], "rebindings": [{"consumer": "UNCHANGED", "from": ["OLD"], "to": ["NEW"]}] }`. Substitute full normal task definitions, not placeholder text. Every selected ID is unfinished, each replacement ID is new and covered, every unfinished incoming edge is explicitly handled, and vectors are ordered unique lists matching the current effective graph. Unknown keys, duplicate edges, missing/superseded targets, cycles, changed definitions disguised as rebindings and empty material changes refuse. Rebind-only uses empty supersede/tasks arrays and empty replacements object with nonempty rebindings; add-only uses ordinary reviewed import.

Revision reports have exactly `operation`, `revision`, `summary`, `coverage`, `findings`: operation is `revision`, revision is the exact digest, summary is substantive (at least80characters), findings is an explicit string list, and coverage has exactly the same areas as the installed task-review templates. Correctness areas: requirements, readiness, dependencies, ownership, checks. Redteam areas: failure-cases, security-classification, privacy-export, workflow-traps. Every area needs at least30trimmed characters explaining actual evidence/limits. Both actual reports must remain unchanged and have no unresolved findings; an ordinary task-import review cannot authorize revision.

Inspect preview blockers and actual handles. Apply refuses affected running/review/owned/live/unknown operations and stale context/reports, preserves completed/superseded history and unrelated rows, and atomically records new tasks/supersession/effective bindings or none. Explicit direct consumer edges change; downstream unfinished input bindings are refreshed separately and all affected old evidence becomes stale. Current checks/docs/required reviews are still necessary. No-overlay behavior stays compatible. Back up/upgrade before first overlay; old-runtime downgrade is unsupported. Never edit stored definitions or receipts to recover. Recorded `applied` or repeat `already_applied` is history, not current product acceptance.

## Optional model-delegation policy

When planning genuine delegation/review, read the payload-resident `.tequio/skills/tequio-routing/SKILL.md` contract. Optional model preferences are private host instructions, not task/model capability proof or spending authorization. Preserve mandatory distinct author/reviewer actors and current acceptance independently of model diversity. Required actual-model identity unknown remains host review-pending; actor names/request aliases/provider changes cannot establish difference. Do not add model metadata to immutable task/review schemas or invent model labels, extra agents for deterministic commands or provider benchmarks.

## Stale completed prerequisites

Completed evidence can become stale after a legitimate read-context change even when owned outputs and task inputs match. Inspect the named causal prerequisite from Status/claim. Preserve old completion/receipts; use ordinary reviewed fresh successor tasks covering the stale chain, then a reviewed rebind-only revision for the unfinished consumer. No old-PASS reuse, implicit aliases or historical body resets. New successors require fresh checks/docs and actual applicable independent reviews; subsequent drift blocks again. Changed outputs/requirements need actual successor correction/acceptance, not a context-only waiver. Source checkout details: `docs/prerequisite-recovery.md`; standalone projects use the successor import/lifecycle and rebind commands in Tasks. Historical unrelated specialists are not live revision work, but specialist freshness still applies to new/unfinished dispatched work.
