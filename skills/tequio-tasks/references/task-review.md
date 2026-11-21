# Reviewing task design before import

Task correctness review and red teaming are distinct from reviews of implemented code. Every new batch, including drafts, must have both before `import-tasks` succeeds. The agent arranges this work; the owner does not approve each task or operate the internal lifecycle.

1. Write the complete task array. Complete routine agent-owned specification choices for every agreed task, not only a starting set. Retain only justified drafts with the sourced decision below; do not mark everything draft solely because future dependencies are incomplete. Ready means the task is specified, not that all dependencies have finished. Assess whether a specialist is actually needed rather than treating an empty registry as a universal blocker.
2. `prepare-tasks tasks/backlog.json --author AUTHOR` validates declarations and records a batch ID bound to canonical task content and current brief/analysis/spec/plan inputs, every cited source file (including evidence outside those directories), and ready-task specialist bindings. It does not import or execute tasks.
3. A different correctness reviewer inspects source requirements, readiness, dependencies, ownership and executable checks. A separate red-team reviewer challenges failure cases, security classification, privacy/export and workflow traps. Both must be distinct from the author and each other. Use the two task-review JSON templates. Include actual open findings in `findings`; a form or score alone is insufficient.
4. Record reports with `review-tasks BATCH --actor REVIEWER --kind correctness|redteam --report reviews/REPORT.json`.
5. `task-review-status tasks/backlog.json` inspects whether the exact batch has current passing reports. Then `import-tasks tasks/backlog.json` refuses missing reviews, open findings, altered/missing reports or changed planning/task content.

Changed tasks/planning inputs require preparation and reviews of the new batch. Whitespace/key-order-only task formatting preserves canonical identity. The author cannot reassign the same batch to a different author. New reports on an unchanged batch can resolve findings, but reviewers must actually reassess the stated evidence. A batch ID is not authorization to build, publish or send anything.

Imported tasks remain immutable. Reviews before import do not replace task verification, documentation reconciliation, correctness review, security review where required or integrated release candidate checks. Existing task history and claims are not retroactively invalidated by this new authoring gate. New/replacement imports use it; normal replan remains necessary for replacing stored definitions. No task data is migrated or rewritten automatically.

## What reviewers must catch

- Missing work, superficial checks, fake integration and unbounded tasks.
- Every draft, including drafts beside a ready starter: challenge its source, category, reason and resolution action. Routine implementation choices, later waves and dependency waiting are not reasons to park specified work.
- A consumer scheduled before its producer.
- Simultaneous write conflicts and sequential downstream edits that invalidate a completed prerequisite's output hashes. Serialization alone does not resolve the latter; change the task boundaries or plan explicit current-state reconciliation.
- Understated security surfaces, omitted candidate contents, dependencies/configuration and private-data export.
- Confusion between unresolved product decisions, routine implementation details and dependency waiting.

## Limits

The CLI enforces content/context/report binding, separate actor strings, structured coverage and explicit findings. It cannot authenticate independence, prove report truth or infer missing product requirements. A local operator can assert identities or fabricate reports; reviewers and host behaviour remain essential. This is an import-time gate, not continuous authentication of prior review documents after import. Do not manufacture reviewer actors/reports to move live work forward.

The deterministic demos and unit tests use explicitly labelled pre-authored synthetic review receipts to test gate mechanics. They are not evidence of actual independent planning review; the demos still stop without genuine implementation review. These fixture helpers are not shipped as production commands.

## Sourced draft decisions

New proposals with `stage: draft` require exactly this additional object:

```json
"draft": {
  "version": 1,
  "category": "unresolved-product-decision",
  "reason": "Explain the actual unresolved decision or prerequisite in at least 30 trimmed characters.",
  "next_action": "State a concrete action to resolve it in at least 30 trimmed characters.",
  "source": "plans/delivery.md"
}
```

Categories are `unresolved-product-decision`, `external-prerequisite`, `missing-specialist-qualification`, and `explicit-deferral`. The source must exactly match one of the task's existing `sources` and is hash-bound with them. Qualification drafts must name the required specialist in `specialists`; an empty registry alone is insufficient. Explicit deferral must reflect an actual sourced scope decision, not an excuse to stop authoring. Ready tasks need no new object. Ready describes specification readiness; dependency and ownership checks separately control dispatch.

Preparation returns ready/draft counts and draft ID/category pairs, without reason, next-action or source prose. The CLI validates this structure at preparation, review of prepared records and import, including proposals prepared before this contract. It cannot determine whether a cited reason is true or the category justified: actual reviewers must inspect the sources and challenge every draft. Do not treat metadata as permission or proof.

Already imported legacy drafts remain readable, immutable and unclaimable; nothing promotes them automatically. Unimported old proposals need the new declaration and fresh preparation/review as needed. Replace imported definitions through supported replan and new task IDs, preserving history.
