# Integration intent and recovery

The internal integration journal records a selected worker commit and observes native Git after interruption. The host remains responsible for serial local integration, authorization, conflict handling and final review. The journal never runs a merge, changes refs, resolves conflicts, creates repositories or publishes changes.

Use the original controller and explicit workspace:

```sh
python3 bin/tequio --project /absolute/controller --workspace feature integration plan TASK --token OWNER_TOKEN --lane worker --commit FULL_SHA --branch main
python3 bin/tequio --project /absolute/controller --workspace feature integration status TASK
python3 bin/tequio --project /absolute/controller --workspace feature integration reconcile TASK
```

`FULL_SHA` is an explicit 40 or 64 character lowercase hexadecimal commit object ID. Branch names, abbreviated IDs and annotated tag objects are refused. The source commit must be reachable from the registered lane's current HEAD when planned. The target must be the controller's currently checked-out local branch in the expected repository. A controller inside a repository subdirectory is supported: the complete repository delta must remain inside that project and its declared task writes. Rename source and destination paths are both checked. Private toolkit paths are refused.

An intent pins the controller, workspace, task definition and source-input binding, lane identity, exact commit, target repository/worktree/branch, and original target HEAD. One task has one immutable intent. An identical current-owner retry returns it without adding events. A different commit or identity requires an explicit replan and new task. Source branch movement never substitutes another SHA. A newly claimed owner must authenticate an identical plan retry to reconfirm the intent; observation-only reconciliation cannot reconfirm ownership.

Intent and observation tables are created lazily in the primary workspace SQLite database during the first valid plan transaction. Invalid plans and interrupted transactions preserve existing task/journal state. Status uses a read-only connection and creates neither tables nor evidence. Reconcile appends observations and deduplicates consecutive identical facts, preserving repeated transitions such as clean to dirty to clean using the same task operation guard as verification and acceptance. It requires no owner token because it records facts, and cannot review, complete or authorize work. The database is trusted local audit state, not a cryptographic signature or filesystem sandbox.

## Recovery states

`pending-integration` means the pinned commit is not an ancestor of the actual target HEAD. It does not authorize repeating a merge: inspect Git and the intended integration method. The journal does not infer cherry-pick, squash or rebase equivalence.

`integrated-unrecorded` means Git contains the exact SHA but no durable first integrated observation exists. Run reconcile before verification; do not merge again merely because the journal was interrupted. The first clean, identity-matching integrated observation atomically captures the existing checks, documentation and review references and a monotonic lifecycle-event barrier.

`needs-checks`, `needs-docs` and `needs-review` identify the next missing current evidence. Checks require a successful stable current receipt published after the integration barrier and bound to the observed exact commit, current target HEAD and current owner epoch. Target HEAD movement after checks requires new checks even when scoped file snapshots remain unchanged. Documentation and required review records must also be current, differ from the original baseline, and have matching lifecycle publication events after the barrier. Reconfirmed owners establish a new barrier. Restoring an old receipt from history does not make it new. Review events bind the actual current review reference; actor names alone are not proof of independence.

`ready-for-closure` means the integration gates and current evidence are satisfied while lifecycle completion remains outstanding. Only an actually completed task with current evidence is `accepted`. Historical accepted observations can become stale as inputs, target state or evidence change. Status, resume and proof provide diagnostics, never scheduling or authorization.

`blocked` includes dirty/conflicted target state, native operations, target repository/branch mismatches, rewritten original target ancestry, missing objects, changed task bindings and an unreconfirmed new owner. Files, conflicts and native operations are preserved. The `integrated` fact is `null` when Git/object availability prevents determining ancestry, `false` only after a successful non-ancestor observation, and `true` when exact ancestry is observed even if another blocker prevents acceptance. A missing or moved source lane blocks pending integration; after the exact commit is integrated it is a warning so disappearance cannot erase target Git truth. Partial/malformed journal state, malformed observation objects and orphaned intent/event references fail closed before any journal-free lifecycle fallback.

## Evidence and observation limits

Verification for a journaled task requires durable observed integration and clean matching target facts. It observes again before publishing the checks receipt and refuses a changed observation, including target HEAD motion. Completion retains existing owner, dependency, input, documentation, review, snapshot and verification-operation guards and adds the journal evidence ordering gate. Journal-free and non-Git workflows retain their existing lifecycle.

Git inspection uses bounded argv subprocesses with inherited `GIT_*` overrides removed, optional locks disabled, replacement objects disabled, and external diff/text conversion disabled for scope inspection. No shell is used. Read-only snapshots can race external Git activity; Git and SQLite do not form a distributed transaction. Host integration ownership and a fresh final preflight remain necessary. The journal establishes selected identities, recorded ordering and observed facts; it does not certify semantic coverage or authenticate independent reviewers.

Inspection includes an `intent` projection with the immutable original lane, selected commit, target branch/repository, base and workspace/controller identity. This supports a fresh owner reconfirming the exact same request without manual database access. Raw evidence baselines, owner tokens and task/private policy prose are omitted. This is a local operator report, not an automatically safe public export.
