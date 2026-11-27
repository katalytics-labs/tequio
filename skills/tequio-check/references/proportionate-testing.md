# Proportionate testing

Use affected behaviour and risk to choose useful feedback and plan final coverage. This is agent guidance, not automatic test selection or a CLI waiver. Project/CI rules and every declared mandatory command still apply, with fresh checks, current documentation and actual applicable independent review.

## Select feedback and final scope

During development, start with the nearest meaningful checks for changed behaviour, dependencies and failure paths. A passing nearby unit test may miss a changed shared contract: expand to relevant integration and adverse-path checks for authentication, persistence, APIs, security and other shared boundaries. Uncertain impact warrants broader coverage. A small isolated change can use focused iteration without a mandatory suite audit.

When authoring a task, put a brief reason for final check scope in its existing acceptance/checks or handoff prose, where useful. Consider affected dependencies and risk alongside project/CI requirements. A full suite remains appropriate when required, cheap enough to run, or boundaries are unclear; periodic CI/release qualification still has its place. Do not impose fixed test counts, ratios or timing quotas, or create a separate rationale form.

Keep development feedback distinct from final verification of the stable integrated candidate. Execute every currently declared mandatory command; a passing subset cannot replace it. Failed, flaky, unavailable or skipped required checks remain acceptance gaps. Investigate failures and report limitations instead of substituting easy checks, cached PASS records or earlier receipts. Material changes require current affected proof under existing freshness rules.

If an imported task has an unnecessarily broad check contract, use a supported reviewed revision/replan with new task definitions where required before changing that contract. Until then its existing checks remain mandatory. Never edit stored historical bodies/receipts to reduce execution. Proportionality does not waive documentation reconciliation or genuine independent correctness/security review.

## Maintain coverage when there is a reason

Consider bounded maintenance when relevant tests are being edited or observed growth, slowness, flakiness or brittle setup causes friction. Do not launch repository-wide cleanup merely because the suite is large or during unrelated work without such a reason. Investigate expensive setup and flaky causes; use existing safe timing or parallel execution tools when appropriate, without introducing a new selection service.

Compare behaviours and failure paths before consolidating duplicate setup or coverage. Similar test code and distinct parameterized cases are not automatically duplicates. Preserve unique regression, security, adverse-path and integration coverage. A test is obsolete only when its requirement was deliberately removed; current implementation failure does not make the requirement obsolete.

Any consolidation, quarantine or removal needs explicit justified scope and actual review, explaining retained coverage and remaining gaps. Never delete or skip a failing check to turn acceptance green. Quarantine is an unresolved coverage gap, not passing proof; required acceptance stays open until resolved through the reviewed contract and current evidence. Larger cleanup belongs in separately scoped work. No new mandatory maintenance artifact or audit is required.
