---
name: tequio-redirect
description: "Revise affected architecture and detailed work after requirements, decisions or experimental evidence change."
---

# Tequio Redirect

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Inspect the cause and map affected requirements/tasks/contracts. Preserve completed work and evidence; do not silently overwrite claimed tasks. Reconcile live agents and choose broad replan or bounded revision below; never alter ownership based on lease expiry alone.

For broad requirements/architecture changes, release reconciled active tasks, then use `replan --reason ...`; it supersedes unfinished records and invalidates phase receipts while retaining history. Update analysis/specs/plans with the real changed decision and rationale. Record fresh analysis/plan receipts; author replacement task IDs with source links, full remaining scope, dependencies, current ownership and acceptance. Review what remains valid versus invalid; no requirement is dropped merely because a previous implementation made it inconvenient.

## Bounded revision

When only selected unfinished producers change, use the standalone revision reference in `.tequio/skills/tequio-tasks/SKILL.md`: write the strict version1 proposal with explicit replacement lineage and unchanged-consumer old/new dependency vectors; `revise preview --proposal PATH`, then `revise prepare --proposal PATH --author ACTOR`. Obtain distinct actual correctness/redteam reviews with `revise review REVISION --actor ACTOR --kind correctness|redteam --report PATH`, inspect `revise status REVISION`, then `revise apply --revision DIGEST`. Report uncovered incoming edges, completed historical consumers, affected descendants and preserved branches. Ordinary import review cannot authorize revision.

Changed consumer acceptance/checks/contracts requires new IDs. Rebind-only proposals have empty supersede/replacements/tasks; import add-only successors normally first. Done nodes remain untouched; their stale/superseded prerequisite cannot support later unfinished work. New bindings require new checks/docs/reviews. Mechanical revision does not edit phase files or repair approvals; actual source changes still invalidate proof. Apply refuses uncertain/live affected operations and is atomic; inspect/retry rather than edit SQLite. Back up and explicitly upgrade before overlays; old-runtime downgrade is unsupported.

Use completed experiment observations to revise direction; missing prerequisite/budget is unqualified and cannot justify declaring a technology unsuitable. Retain product outcome, open acceptance, checkpoint limits and concrete next value.
