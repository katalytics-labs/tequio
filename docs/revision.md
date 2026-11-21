# Reviewed backlog revision

Use Redirect/Tasks to refine a bounded part of a current backlog. Broad `replan --reason TEXT` remains available when the remaining plan needs replacement: it supersedes unfinished work and invalidates phase receipts. Revision preserves unaffected definitions and uses explicit per-consumer dependency changes. It does not infer semantic compatibility or waive current acceptance.

Installed projects use the standalone revision reference in `.tequio/skills/tequio-tasks/SKILL.md`; the source `docs/` tree is not an installed payload.

## Proposal and commands

All commands use `python3 bin/tequio --project ROOT --workspace NAME` before the command below. Proposal/report paths are workspace-relative JSON files.

```text
revise preview --proposal tasks/refinement.json
revise prepare --proposal tasks/refinement.json --author AUTHOR
revise review REVISION --actor CORRECTNESS_REVIEWER --kind correctness --report reviews/revision-correctness.json
revise review REVISION --actor REDTEAM_REVIEWER --kind redteam --report reviews/revision-redteam.json
revise status REVISION
revise apply --revision DIGEST
```

Preview and status are read-only: they do not initialize revision schema, locks or attempts. Preparation returns `revision` plus preview fields; use that exact identity to review/apply. Status distinguishes `review-required`, `reviewed` and `applied`. Apply returns `revision`, `superseded`, `imported` and `rebound`; a validated repeat also reports `already_applied`. Author, correctness reviewer and red-team reviewer must be distinct actual actors. Review uses the existing task-review report coverage and binds the revision operation, proposal, prospective graph and current context. Reports contain exactly `operation: "revision"`, `revision: DIGEST`, a substantive `summary` (at least 80 characters), normal task-review `coverage` and `findings`. Use the maintained task-review coverage areas and no unresolved findings; do not submit an import report with a renamed identity. Ordinary import reviews cannot authorize revision. Identity fields are local audit metadata, not authentication.

Version 1 accepts exactly these keys:

```json
{
  "version": 1,
  "reason": "Split one producer while retaining its unchanged consumer",
  "supersede": ["PRODUCER"],
  "replacements": {"PRODUCER": ["PRODUCER-A", "PRODUCER-B"]},
  "tasks": [],
  "rebindings": [{"consumer": "CONSUMER", "from": ["PRODUCER"], "to": ["PRODUCER-A", "PRODUCER-B"]}]
}
```

This illustrates the envelope only: `tasks` must contain full valid new definitions for both replacement IDs before submission. Reason must be nonblank. Selected old IDs and new IDs are unique; every selected old ID maps to a nonempty unique list of newly defined IDs, and every new definition is covered. Replacement relations record lineage; they create no implicit graph edges. New tasks declare their own dependencies and pass normal source, readiness, specialist, documentation and security validation.

Each rebinding has exactly `consumer`, `from`, `to`. Dependency vectors are ordered unique ID arrays; `from` must equal the current effective vector. Cover every unfinished incoming edge to superseded work. Duplicate edges, missing/superseded targets, cycles, self-dependencies, reused IDs and empty material changes refuse. For a rebind-only proposal, `supersede`, `replacements` and `tasks` are empty and `rebindings` is nonempty. Add-only work uses ordinary reviewed import, followed by a rebind-only revision if needed.

## Identity, evidence and impact

Only definition-unchanged, unowned unfinished ready/draft/eligible blocked consumers can be rebound. Changed acceptance, checks or contracts require new task IDs. Preview exposes supersessions/new IDs, old/new dependency vectors, affected unfinished descendants, completed historical consumers, retained identities, digests and blockers; it omits tokens and task/report prose.

SQLite retains original definitions, including original `depends_on`, and raw checks/docs/reviews/events. Append-only revision intent, review, application and dependency/input-binding history support a separate current projection. Lifecycle, recursive freshness, reporting, integration and later import validation resolve effective dependencies centrally. A rebound consumer retains its ID and definition but receives a new input binding salted by the revision in every freshness mode. Affected unfinished descendants also receive refreshed current input bindings so they can execute against the revised graph; their earlier proof is stale. Only explicitly listed direct consumer edges change; downstream input rebinding creates no implicit task alias or extra graph edge. Old checks/docs/reviews remain historical and cannot satisfy current acceptance, even with identical project bytes. Obtain new current checks, reconciliation and required actual reviews.

Done nodes cannot be rebound or superseded. A completed consumer keeps its historic edge/body/result; if its prerequisite becomes superseded, that dependency acceptance is noncurrent for unfinished downstream work. Continuing it requires a reviewed new task. For completed policy work needing change, import a reviewed successor normally, then explicitly rebind unfinished integration consumers; never rewrite or inherit historical approval.

With no overlay, existing hashes/read behavior remain unchanged. Unaffected evidence survives only where its actual declared resources, sources, phases and dependencies remain current. Revision neither edits phase files nor refreshes/deletes approvals. Required analysis/plan receipts must already be current; requirement/source changes still invalidate affected proof normally.

## Atomic application and recovery

Prepared identity binds exact proposal content/canonical meaning, prospective graph, phase/source/task-review context, relevant task state/ownership/results/edges/input bindings and report hashes. Apply revalidates under existing operation-guard-before-database ordering, project claim coordination and sorted nonblocking affected operation guards. Affected transitive unfinished descendants are included. Running/review/owner-bearing tasks, held/live/unknown verification and unresolved blocked attempts refuse, including expired leases. Inspect genuine handles; revision never kills/reassigns agents or disturbs unrelated active work.

Before revision, an ordinary owner release now clears owner/token/lease and current checks/reviews, retaining the claimed actor in event history. If an older controller left a released-ready owner, use supported `recover` only after inspecting actual activity: the row must be ready with a nonempty owner and null token, lease, checks and reviews. This normalization does not require fresh execution dependencies. It refuses ordinary unowned-ready or inconsistent rows and held/live/unknown verification even with a stopped-check acknowledgement. A known absent recorded group may be reconciled through the existing guard. Revision continues to reject every owner-bearing row; it never clears ownership or weakens that refusal itself. Normal recovery of running/review/blocked work, current dependency/phase requirements and independent revision review still apply. Never edit a workspace database or remove a lock file to normalize ownership.

One immediate SQLite transaction applies supersessions, new tasks, bindings and application event together or rolls back. No postcommit per-ID task-file writes are required; stored proposal/intent remain inspectable after refusal/failure. Retry an exact already-applied digest returns its recorded outcome after integrity checks without duplicate mutation. Changed content/context/report requires reconciliation and fresh preparation/review. A recorded application is distinct from later workspace readiness and qualification. Do not repair state by editing SQLite.

Mutations run only at the original controller; linked-lane mutation refuses and read-only observations follow controller routing. Revision schema is lazy/versioned; supported entry points reject unsupported capability versions/corruption. Back up and explicitly upgrade the controller before first apply. Downgrade of an overlay workspace is unsupported: an old 0.12 runtime cannot automatically enforce a future capability marker. Do not open a revised workspace with it or mutate historical runtime snapshots to pretend protection exists.

## Stale completed prerequisite recovery

See [supported successor recovery](prerequisite-recovery.md). Add reviewed fresh successors through normal import/lifecycle, then explicitly rebind unfinished consumers; completed bodies/results remain historical. Revision context still hashes historical sources/state but excludes completed specialist bindings from live resolution. Current new/unfinished tasks retain qualification checks. Snapshot-only drift does not waive fresh acceptance, and exact historical changed paths cannot be reconstructed from aggregate hashes alone.
