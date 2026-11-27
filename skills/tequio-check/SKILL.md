---
name: tequio-check
description: "Run a claimed task\u2019s declared checks and inspect whether acceptance, wiring and documentation have actually been demonstrated."
---

# Tequio Check

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Read the task and acceptance criteria, inspect current integration and durable evidence. Execute `verify <task> --token <token> --summary`; this runs argument vectors in the project root with a timeout and records private output plus current content/input hashes. Do not replace failed commands with easy checks that prove a narrower outcome. Tests must exercise the required behavior, not just match implementation wording.

Inspect receipt output and identify which acceptance criteria it does and does not support. Manual/visual evidence can supplement executable checks and should be linked in the review report. A green command does not prove omitted requirements. Changed files/inputs invalidate earlier evidence. Return observed result and gaps; do not mark done without independent review.

Use the compact response for routine delivery; inspect the exact private receipt path/hash for acceptance evidence and relevant failed-check details. The summary omits raw commands/output/errors, caps diagnostic items at three and reports omissions. It does not truncate stored evidence, certify privacy/publication or replace actual review. Default CLI JSON and direct verify API remain available unchanged. Refusal/infrastructure errors produce no summary and must not be replaced with an older PASS.


New task/release templates declare `capture:{version:1,mode:bounded-v1,max_bytes:1048576}`: one retained raw-byte budget across stdout/stderr and all checks. Existing tasks without this field keep legacy behavior; never retrofit imported definitions. Consider output volume and actual effects while authoring; supplied limits must be integers1..16777216. Limit/timeout/capture failure retains a bounded private prefix and fails rather than accepting truncated evidence. Use supported replan when a policy truly needs changing; no automatic retries of expensive effects or old-PASS reuse.

Bounded receipts/summaries use version2 with attempted versus actually executed counts and explicit skipped checks. Failed launch is an attempt, not an executed child or skipped check. Inspect exact private receipt evidence on failure; raw/base64 output never belongs in compact delivery. Unknown cleanup requires actual handle inspection, not inferred process death. Capture policy does not grant command authorization or automatically classify every project task as security-sensitive.

## Proportionate testing

Focused feedback does not replace any mandatory final command, fresh evidence, current docs or actual applicable independent review. See [proportionate testing](references/proportionate-testing.md) for affected-behaviour coverage and bounded suite maintenance. Imported check-contract changes require supported reviewed revision/replan; never edit historical definitions or substitute old PASS.

## Cheap feedback and current proof

Cheap faithful boundary checks should precede costly integration effects during development. Feedback is not a registered acceptance receipt; final verification still executes every declared mandatory check against a stable current candidate. Repeat expensive effects for changed surfaces, failures or a concrete current-proof need within authorization, rather than to chase unrelated notes. A material boundary/configuration correction requires current affected evidence. Rebound effective dependencies invalidate earlier checks/docs/reviews even with unchanged source bytes.

For an experiment, inspect whether positive/adverse observations are complete enough for its bounded decision. Missing prerequisite or budget exhaustion is unqualified, not unsupported technology. Return the observed usable result, open acceptance and exact private evidence references.

## Optional model-delegation policy

Use deterministic scripts for computations and declared checks; an extra model is not needed merely to run them. Optional workspace routing does not change mandatory commands, current evidence/docs or independent-review gates. Read `.tequio/skills/tequio-routing/SKILL.md` when delegation policy is relevant. Configuration/records are not actual model authentication or runtime diversity enforcement; do not call unknown/request-only identity verified or a synthetic gate test proof of model behavior.
