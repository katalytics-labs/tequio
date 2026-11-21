---
name: tequio-design
description: "Turn reviewed analysis and requirements into architecture, complete scope, dependency waves and qualification experiments."
---

# Tequio Design

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Read the brief, current analysis/specs and relevant code. Confirm analysis receipt is current using `status`. Write workspace `plans/` Markdown: intended architecture, complete in-scope outcomes, dependency order, coherent milestones/waves, acceptance evidence, qualification experiments, integration ownership, risks and explicit later/deferred scope. Map every requirement to an outcome; later milestones remain provisional but visible.

Choose boundaries that preserve complete customer workflows. Avoid arbitrary technology silos or copying speculative abstractions into contractual requirements. Describe trade-offs and current choices clearly; surface material unresolved decisions while continuing independent work. Respect prior user authorization instead of requiring repeated approval for routine actions.

Review coverage and call `record plan`. A recorded plan is a content receipt, not an authorization token or proof of good design. Next use `$tequio-tasks`; no implementation starts here.

## Specialist coverage

Before execution-ready task creation, inspect relevant project-owned skills and `specialists list`. Use tequio-specialists when stack coverage is missing or materially changed. Reuse existing guidance first; do not create a specialist for every dependency. Generated skills require current exercise-tested qualification for ready task use. Read the resolved package path from task specialist bindings; research-only specialists require research tasks. Missing qualification stays draft/blocked rather than being invented.

## Proportionate change plan

For an existing-project fix, plan the complete requested delta rather than redesigning the whole product. A single `plans/change.md` can map the focused requirements/spec to affected files, the chosen correction, compatibility boundaries, acceptance checks, documentation impact and one integration owner. Reference existing architecture decisions and explain only material changes. One wave and one task are sufficient when they form a coherent verified outcome; do not invent milestones or qualification experiments without a real uncertainty.

Retain explicit exclusions and unresolved risks. A newly discovered shared contract or broader scope requires reconciliation before tasks become ready. Use the normal current analysis and plan receipts.

## Experiment, product slice and combined proof

Separate a necessary uncertainty probe from the implementation outcome and final combined qualification. Reuse existing code/evidence; plan cheap faithful boundary observations before expensive integration, with effects, ceilings, stop decision and next product slice. Use optional experiment.md only where useful; no extra runtime task kind/status is implied. Missing prerequisites/budget cannot establish unsuitability.

For new scoped-v1 work, review actual disjoint policy/functional read/write resources and make final integration depend on both. Shared runtime/configuration, semantic contracts, parent-directory overlap and genuine dependencies remain proof inputs. Global/mixed histories remain conservative; no Markdown/.gitignore exemption, installer change or cached PASS is implied. Plan current policy checks and explicit reviewed successors for changed completed work.
