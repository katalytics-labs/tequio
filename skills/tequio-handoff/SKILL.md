---
name: tequio-handoff
description: "Save a concise durable handoff with evidence, current state and a concrete next action for another session."
---

# Tequio Handoff

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Reconcile current files, task status and evidence first. Call `checkpoint --summary <what changed, checks, limitations> --next <specific next action>`. Put larger decision/experiment records in workspace journal/ and reference them. Include genuine live agent/process handles when relevant without secrets. Do not copy full private chat transcripts or declare a process stopped based on a lease. A checkpoint does not mark tasks complete.

## Run-context reconciliation

Checkpoint version 1 records policy validity/digest and recorded task definitions separately from progress. On pickup/build, inspect `policy_changed`, `task_scope_changed`, `context_unknown` and `checkpoint_issue`, plus current private run policy and approved task IDs. Reconcile changed or unknown context against persistent/current user authorization before dependent continuation; current user instructions remain authoritative and a digest never grants permission. Continue already explicitly authorized work without routine permission requests. Missing/invalid policy is not an approved backlog. Legacy or damaged checkpoints require orientation from healthy current status, files, receipts and actual live handles; resume preserves bytes and makes no repair. At handoff explicitly checkpoint the reconciled context and describe unresolved scope/authorization gaps privately. See `docs/run-context.md` for hash boundaries and limits.


## Exact-commit integration recovery

When using registered Git lanes, the integration owner pins the selected full commit SHA with internal `integration plan TASK --token TOKEN --lane NAME --commit FULL_SHA --branch BRANCH` from the original controller and explicit workspace before native integration. Follow `docs/integration-journal.md` for identity, scope and recovery constraints. The journal observes Git and never performs or authorizes a merge. Resume the immutable intent; do not substitute a moved branch tip or infer squash/cherry-pick equivalence.

Inspect `integration status TASK` after interruption. If exact SHA is integrated but unrecorded, run `integration reconcile TASK` before authoritative verification. Preserve dirty/conflicted/mismatched/rewritten state and inspect the blocker. A new owner authenticates the identical plan retry before continuation. After durable integration/reconfirmation, obtain genuinely new current checks, documentation reconciliation and required independent reviews; readiness is not lifecycle completion. Status/history never authorize work or certify semantic coverage. Journal-free shared-folder work remains supported.

For routine pickup use internal `resume --summary`, retaining full default resume for targeted private inspection. The compact response preserves changed/unknown policy,scope,progress/project flags, same-read checkpoint reference and bounded active-operation observations/omissions; it is not permission to resume/recover. Inspect omitted/unknown work and original evidence before acting, never guess by recency.

## Optional model-delegation policy

Keep meaningful delegation provenance private using `.tequio/templates/delegation-record.json` when useful, not per command. Separate requested choice from observed provider/model/family and host-metadata/agent-report/unknown source; unknown values stay null, family informational. Preserve actual fallback and pending required-diversity gaps instead of claiming the original request executed. Cite private refs without prompts/keys/endpoints/environment dumps. Read `.tequio/skills/tequio-routing/SKILL.md` for the complete installed contract. Policy digests/records do not certify models, authorization or current review acceptance.
