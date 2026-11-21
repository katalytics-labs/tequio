---
name: tequio-pickup
description: "Reconcile a saved handoff with actual files, input freshness, receipts and live work before continuing a workspace."
---

# Tequio Pickup

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Run `resume --summary`; compare checkpoint with current status, files and evidence. Inspect genuine live agent/process handles before interpreting expired claims. If work is live, reconnect/wait; if it is confirmed stopped, release using the owner token or use `recover --reason <evidence>` on expired/blocked work. Recovery never kills/restarts a process automatically.

If inputs changed, re-analyze/replan relevant work. Explain the reconciliation and next ready action. Resume itself is read-only; when the user's request authorizes execution, follow `$tequio-build` after reconciliation rather than asking routine permission again.

## Run-context reconciliation

Checkpoint version 1 records policy validity/digest and recorded task definitions separately from progress. On pickup/build, inspect `policy_changed`, `task_scope_changed`, `context_unknown` and `checkpoint_issue`, plus current private run policy and approved task IDs. Reconcile changed or unknown context against persistent/current user authorization before dependent continuation; current user instructions remain authoritative and a digest never grants permission. Continue already explicitly authorized work without routine permission requests. Missing/invalid policy is not an approved backlog. Legacy or damaged checkpoints require orientation from healthy current status, files, receipts and actual live handles; resume preserves bytes and makes no repair. At handoff explicitly checkpoint the reconciled context and describe unresolved scope/authorization gaps privately. See `docs/run-context.md` for hash boundaries and limits.


## Exact-commit integration recovery

When using registered Git lanes, the integration owner pins the selected full commit SHA with internal `integration plan TASK --token TOKEN --lane NAME --commit FULL_SHA --branch BRANCH` from the original controller and explicit workspace before native integration. Follow `docs/integration-journal.md` for identity, scope and recovery constraints. The journal observes Git and never performs or authorizes a merge. Resume the immutable intent; do not substitute a moved branch tip or infer squash/cherry-pick equivalence.

Inspect `integration status TASK` after interruption. If exact SHA is integrated but unrecorded, run `integration reconcile TASK` before authoritative verification. Preserve dirty/conflicted/mismatched/rewritten state and inspect the blocker. A new owner authenticates the identical plan retry before continuation. After durable integration/reconfirmation, obtain genuinely new current checks, documentation reconciliation and required independent reviews; readiness is not lifecycle completion. Status/history never authorize work or certify semantic coverage. Journal-free shared-folder work remains supported.

For routine pickup use internal `resume --summary`, retaining full default resume for targeted private inspection. The compact response preserves changed/unknown policy,scope,progress/project flags, same-read checkpoint reference and bounded active-operation observations/omissions; it is not permission to resume/recover. Inspect omitted/unknown work and original evidence before acting, never guess by recency.

## Outcome and revision reconciliation

Inspect any prepared/applied revision and current effective dependencies/input bindings; unchanged stored bodies do not imply unchanged acceptance. Preserve raw historical evidence and completed nodes. An exact applied digest records an operation, not later readiness. Downgrade of overlay workspaces to old runtimes is unsupported; inspect backup/explicit upgrade state before continuation.

Resume with the usable product outcome, remaining acceptance/findings, next useful slice and cumulative checkpoint/correction observations. Reuse investigation already supported by current evidence. Do not restart an experiment without a concrete gap; missing inputs/budget remains unqualified. Unknown token/billing usage stays unknown; reconcile material changes before required proof.

## Optional model-delegation policy

Reconcile optional enabled model policy and policy_changed with actual host controls, pinned choices, authorization and saved private delegation records. Read `.tequio/skills/tequio-routing/SKILL.md` for the complete installed contract; do not enable/disable silently or opportunistically bypass required diversity. Distinguish requested selectors from actual observations and truthful unknown/fallback. Required unknown remains host review-pending while enabled; explicit owner off suspends only this optional workspace preference, not mandatory evidence/actors or higher-priority rules. CLI validity/drift does not dispatch/authenticate models or enforce diversity.
