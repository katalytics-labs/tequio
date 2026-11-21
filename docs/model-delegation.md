# Optional model delegation and routing control

Tequio validates an optional private `model_delegation` run-policy block and observes its complete-policy digest. It also provides portable `$tequio-routing on|off|status` backed by `python3 bin/tequio --project ROOT --workspace NAME routing on|off|status`; omitted action is read-only status. It does not select or launch models, intercept host tools, authenticate model metadata, compare actual models or enforce diversity in review/complete.

The complete exact schema, caps, safe persistence, defaults, response fields and host fallback/provenance instructions live in [the shipped Routing skill](../skills/tequio-routing/SKILL.md). Installed projects receive that contract and the optional [delegation record](../templates/delegation-record.json); no source docs checkout is required. Skills guide the host; CLI transitions retain their existing guarantees and limits.

## Deliberate workspace adoption

Use explicit project/workspace and owner intent for changes. On enables saved valid preferences or adds enabled empty-choice advisory defaults; off preserves all saved settings. Missing-block off and repeated settings are byte-preserved no-ops. Missing workspace status creates nothing; missing workspace mutation refuses. Missing-policy on creates conservative next-chunk/empty-task/no-Git/one-writer checkpoint defaults whose scope grants no execution permission. Malformed policy or disabled-invalid block refuses mutation instead of repair. Existing optional-key conflicts require deliberate reconciliation.

Status returns only fixed version/workspace/configured/enabled/policy-state/change/digest fields; mutations add previous digest. Invalid/unreadable enabled is null, not false; configured false does not prove absence. Reads are bounded regular-file/no-follow/nonblocking observations; mutation uses project coordination, replacement checks and atomic same-directory publication with preserved existing mode/new 0600. Status creates no lock; an already-observed valid no-op may avoid coordination and rewriting. Arbitrary host writers are outside this coordination; uncertain publication calls for status inspection, not a claimed rollback. Checkpoint drift follows the existing full policy digest; no checkpoint is silently rewritten.

## Honest host decisions

Use scripts first and delegate useful work by uncertainty, consequence and checkability. Choose only authorized real host options, respecting pinned models/budget and avoiding escalation/retry storms. Empty choices support hosts without selection control. No price/capability/superiority conclusion follows from a choice label.

Distinct actors are required independently of diverse models. Required different-model review needs sufficient actual underlying-model observations relative to the author/implementer; aliases, requested selectors, providers, actor names and agent self-reports do not establish verified difference. Unknown required diversity remains host review-pending. Preferred fallback records same/unknown or pending per policy. An explicit owner off suspends this optional workspace preference, including its required setting, without certifying prior diversity or waiving mandatory current proof/actors or higher-priority rules.

Keep meaningful delegation records private, requested/observed/source distinct, unknown values null and family informational. An agent header is agent-report; alias-only host metadata is not actual backend identity. Reported diversity labels are not authenticated. Existing reports may cite records; receipt/task history and schemas stay intact. No prompts, credentials, endpoints, environment dumps or case data belong in shipped assets.

No provider integration, benchmark, managed ledger, model catalogue, billing measurement, global setting or target installation is included. Version 0.14.0 includes this capability; installation and host-discovery refresh require their own authorization.
