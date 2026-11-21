# Recovering stale completed prerequisite evidence

A completed task is immutable history, not a perpetual guarantee. Dispatch still requires current prerequisite inputs, owned outputs and (for scoped work) context snapshots, recursively. A legitimate edit in a declared read directory can stale acceptance without changing owned outputs. Status/claim identify the first causal prerequisite in dependency order: incomplete/missing, inputs changed, owned outputs changed, context snapshot changed or evidence unavailable. Old aggregate snapshots do not contain per-path historical hashes, so context-only diagnostics identify the category, not a fabricated changed filename. Inspect the actual change and source history before choosing recovery.

## Existing successor model, no completion reset

Use fresh ordinary tasks and an explicit reviewed dependency rebind. Do not edit completed bodies, result hashes, receipts, statuses, old checks or specialist records. Do not make a fresh successor depend on the stale evidence it is replacing. It may depend on other current prerequisites, including the accepted task that caused the legitimate change, when that reflects the real contract.

1. Inspect the stale chain and classify changed inputs, writes and context. If outputs/requirements changed, design the successor for the actual changed behavior; do not label it harmless context-only recovery. Missing/unknown evidence remains blocked.
2. Author new task IDs representing all required acceptance scope, including transitive stale producers. Preserve concrete reads/writes/shared configuration, source/requirement coverage, checks and security classification, and remap their dependencies to current successors. Avoid a broad “check everything” successor without explicit coverage. Do not silently discard a stale ancestor obligation. Original completed tasks remain done and historical.
3. Evidence-only successors may use a justified `documentation: not-needed` declaration when maintained behavior/docs are actually unchanged, subject to real review. If docs/behavior need changes, declare and own those updates; downstream edits must not invalidate already accepted successor proof. New tasks still need source reconciliation. Use current qualified specialists for these new tasks; unrelated completed specialist bindings are not a requirement to revise another branch.
4. Obtain actual independent correctness and red-team task-design reviews; import normally. Execute in dependency order with fresh checks, current documentation reconciliation and actual independent correctness plus security review where required, then complete. A failed, stale or unchecked successor supplies no acceptance; never attach a previous receipt as a new PASS.
5. Rebind the affected unfinished/unowned consumer from old completed IDs to the completed current successor IDs with a rebind-only revision. Obtain distinct actual correctness/red-team revision reviews of that exact graph change. Do not rebind completed history. The consumer's old proof becomes stale through supported effective bindings. Other unfinished descendants receive refreshed input bindings; they still need their own normal execution/checks/docs/reviews.

You may prepare/apply the explicit rebind before running successors, but the consumer remains blocked until all fresh prerequisites are accepted. Subsequent relevant drift still blocks. Independently accepted change tasks do not automatically requalify all impacted historical results.

## Supported command sequence (synthetic IDs)

Paths below are workspace-relative except task-array arguments, which are filesystem paths. `NEW-A` and `NEW-B` are reviewed full new definitions, not aliases or copies of old receipts. Review report files must be authored by actual distinct reviewers, not copied from these examples.

```sh
python3 bin/tequio --workspace feature prepare-tasks .tequio/workspaces/feature/tasks/recovery.json --author AUTHOR
python3 bin/tequio --workspace feature review-tasks BATCH --actor CORRECTNESS --kind correctness --report reviews/recovery-correctness.json
python3 bin/tequio --workspace feature review-tasks BATCH --actor REDTEAM --kind redteam --report reviews/recovery-redteam.json
python3 bin/tequio --workspace feature import-tasks .tequio/workspaces/feature/tasks/recovery.json
python3 bin/tequio --workspace feature claim --task NEW-A --owner WORKER
python3 bin/tequio --workspace feature verify NEW-A --token TOKEN --summary
python3 bin/tequio --workspace feature record-docs NEW-A --token TOKEN --report reviews/new-a-docs.json
python3 bin/tequio --workspace feature review NEW-A --token TOKEN --actor REVIEWER --kind correctness --report reviews/new-a-correctness.md
# Security-risk tasks also require a separate actual security review:
python3 bin/tequio --workspace feature review NEW-A --token TOKEN --actor SECURITY --kind security --report reviews/new-a-security.md
python3 bin/tequio --workspace feature complete NEW-A --token TOKEN --summary 'Fresh checks and applicable independent reviews accepted current scope'
```

Repeat the actual lifecycle for each successor; substitute its returned private token and real reports. Resolve findings rather than recording an empty finding list by default. Keep real subprocess/resource limits and no automatic retries of expensive or external effects.

Rebind-only proposal, assuming the current effective vector is exactly `["OLD-B"]`:

```json
{"version":1,"reason":"Current reviewed successor evidence replaces stale historical prerequisite for unfinished consumer.","supersede":[],"replacements":{},"tasks":[],"rebindings":[{"consumer":"CONSUMER","from":["OLD-B"],"to":["NEW-B"]}]}
```

```sh
python3 bin/tequio --workspace feature revise preview --proposal tasks/recovery-rebind.json
python3 bin/tequio --workspace feature revise prepare --proposal tasks/recovery-rebind.json --author AUTHOR
python3 bin/tequio --workspace feature revise review REVISION --actor CORRECTNESS --kind correctness --report reviews/rebind-correctness.json
python3 bin/tequio --workspace feature revise review REVISION --actor REDTEAM --kind redteam --report reviews/rebind-redteam.json
python3 bin/tequio --workspace feature revise apply --revision REVISION
python3 bin/tequio --workspace feature status
python3 bin/tequio --workspace feature claim --task CONSUMER --owner WORKER
```

Revision context retains historical source hashes and task/graph state but does not re-resolve completed specialist bindings as live revision work. Unfinished/new ready tasks and dispatched work still require current specialist bindings. This does not forgive an unavailable specialist on an actual prerequisite used for dispatch. Plan deliberate specialist/context reconciliation where required; no registry edits or forged qualification.
