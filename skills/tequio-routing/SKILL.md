---
name: tequio-routing
description: "Inspect or explicitly enable/disable optional workspace model-routing preferences without selecting or launching models."
---

# Tequio Routing

Use `$tequio-routing status`, `$tequio-routing on` or `$tequio-routing off` when supported by the host. Omitted action means status, never toggle. Resolve the explicit project/workspace from the request; never choose by recency. Execute `python3 bin/tequio --project ROOT --workspace NAME routing on|off|status` (global options first). A host may supply its own menu/slash entry; universal discovery is not promised.

The CLI validates configuration, changes its enabled flag and observes policy drift. It does not select/launch/intercept models, compare/authenticate underlying identity or enforce diversity in review/complete. This optional workspace preference is not a spending permission or model-capability guarantee. Mandatory current checks/docs and genuinely independent reviewers remain required.

## Control and safe persistence

Status is read-only, creates/locks nothing and reports missing workspace as unconfigured/disabled. On/off needs explicit owner intent or current authorization; do not switch off opportunistically to evade quota or required review. Missing-workspace mutation refuses. Lane status follows the original controller; lane mutation refuses.

On enables a valid saved block, adding defaults only when absent. Off retains every saved choice/preference/diversity/fallback; absent-block off creates nothing. Repeated settings preserve raw policy bytes/formatting. A malformed base or supplied block refuses mutation, including a disabled invalid block. Never reset/repair it silently. A reserved-key collision requires explicit reconciliation.

If policy itself is absent, on creates conservative next-chunk defaults: empty tasks, routing-configuration-only scope granting no execution permission, no Git/merge/push, one writer and 30-minute/three-verification checkpoints. It neither selects nor claims work. Existing unrelated valid base fields are preserved.

Policy reads accept regular non-symlink files up to 1MiB using no-follow/nonblocking checks. Mutations coordinate through the project claim lock, detect external byte/mode replacement and atomically publish a same-directory temporary file; new mode is 0600, existing mode is preserved. Validated no-op may return without a lock/rewrite, with no guarantee against subsequent change. Cooperating CLI coordination does not constrain arbitrary host writes or create a filesystem/SQLite transaction. On an uncertain publication failure, inspect read-only status; never claim unobserved success or impossible rollback. No automatic checkpoint rewrite or database ledger exists.

The exact response fields are `schema_version` (1), `workspace` (name/null), `configured` (boolean), `enabled` (boolean/null), `policy_state` (missing/valid/invalid/unreadable), `changed` (boolean), `policy_digest` (digest/null); mutations additionally include `previous_policy_digest`. Configured means a valid complete policy and valid present block, not actual model availability. Missing policy/block gives false/false; invalid/unreadable gives false/null and does not prove absence. No choice IDs, rationale or raw policy are returned. Complete-policy digests/checkpoint `policy_changed` observe changes; they do not grant authorization.

## Optional private policy contract

Workspace `run-policy.json` may contain exactly this versioned `model_delegation` block:

```json
{
  "version": 1,
  "enabled": true,
  "available_choices": [],
  "routing_preferences": [],
  "review_diversity": {
    "basis": "different-model",
    "correctness": "optional",
    "security": "preferred"
  },
  "fallback": {
    "unavailable_choice": "host-default",
    "unmet_preferred_diversity": "record-and-continue"
  }
}
```

All shown keys and nested keys are exact and required when supplied. Version is integer 1, not boolean; enabled is boolean. Disabled blocks still validate fully and remain digest-bound. Absence retains legacy behavior with no extra requirement; malformed/null/unsupported blocks invalidate policy observations. Other top-level private keys retain existing semantics and complete-JSON digest binding; no parser migration is introduced.

Both arrays have at most 32 entries. Choice IDs are unique case-sensitive nonblank printable strings of at most 256 Unicode characters, without surrounding whitespace. They are host option identifiers, not a provider catalogue or proof of backend identity. Preference entries have exactly `work`, `choice`, `reason`: work/reason are nonblank printable strings at most 1024 Unicode characters; work descriptors are unique and choice references a declared ID. Reusing one choice for different work is valid; empty lists support hosts with no selection control. Controls, unknown nested keys, wrong types/enums/references and cap violations are invalid.

Diversity basis is exactly `different-model`; correctness/security each use optional/preferred/required. Unavailable-choice fallback is host-default/stop; unmet-preferred fallback is record-and-continue/review-pending. Required unmet diversity always remains host review-pending, with no fallback override. New defaults are optional correctness/preferred security and host-default/record-and-continue. Configuration is structurally validated, not an assessment of sufficient quality or actual availability.

## Host selection, independent review and fallback

When the block is absent or disabled, its saved model-selection/diversity preferences are inactive. Load this guidance when applicable and reuse it while current; reconcile changed policy instead of rereading the full contract for every script or delegation. Mandatory actual review and higher-priority instructions still apply.

Use deterministic scripts/tools first for deterministic work; do not delegate a hash command merely to select a model. Delegate only useful independent work, expertise or review. Consult real available authorized host controls and select by uncertainty, consequence and checkability, not fixed cheap/strong labels. Respect user-pinned models, budgets, higher-priority instructions and reserve/checkpoints. Availability does not authorize spending. Do not infer quality gains from tiers/families, escalate to costlier options automatically or create quota retry storms. For unavailable choice, use the configured bounded host-default alternative or stop within authorization.

Independent actors and diverse models are separate. Same-model distinct actors may meet existing actor independence; different-model self-review cannot. Optional diversity adds no constraint. Preferred attempts justified available/authorized diversity, then records same/unknown fallback or leaves review-pending per policy. Required needs sufficient observed identity evidence that the reviewer underlying model differs from the relevant author/implementer; the two reviewers need not differ from each other. Unknown/aliased/request-only identity leaves required review-pending. The CLI does not enforce this host instruction.

Different selector, actor name, provider, endpoint or family is not proof of a different actual model. Host metadata containing only an alias/default/request is insufficient. An agent-written header is agent-report, not host-verified identity. Off under explicit owner request suspends this optional workspace routing/diversity policy, including its required preference; it neither certifies historical diversity nor waives mandatory actors/checks/docs or higher-priority diversity/security/pinned-model rules.

## Minimal private provenance

Use `.tequio/templates/delegation-record.json` for a meaningful delegated selection/fallback decision, not every command. Save it under the explicit private workspace, with actual task/actor/work and requested choice separate from observed provider/model/family. Unknown observed values stay null; source is host-metadata/agent-report/unknown. Family is informational, never inferred. Report diversity as different-model-reported/same-model-reported/unknown/not-requested with a reason; these labels are reported observations, not authentication. Preserve later actual fallback honestly rather than the original request; retain prior observations when needed.

Review reports may cite private records without changing receipt schemas/history. Records are optional guidance, not a managed/validated ledger. Keep prompts, keys, endpoints, provider request bodies, environment dumps and private project/case details out of shipped assets and summaries. Return only usable outcome, known/unknown identity/source/fallback where relevant, pending acceptance, next value and genuine usage/checkpoint limits. No measured savings or model superiority follows from this policy.
