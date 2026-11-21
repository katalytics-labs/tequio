# Contributing

Tequio is experimental. Keep changes bounded, explain the intended behavior and alternatives, and add meaningful tests for changed lifecycle/installer guarantees.

## Source layout

- src/tequio/: standard-library runtime, installation, lifecycle, orientation, optional Git isolation, evidence reporting and specialist factory.
- skills/: sixteen workflow skills (including optional briefing preparation and routing control); roles/: four generic agent briefing contracts.
- templates/ and profiles/generic.md: reusable project-neutral inputs.
- tests/: deterministic contract/failure tests; examples/: quickstart, bounded existing-project correction and integrated-build replay.
- docs/: current architecture and operation references.

After changing shipped Python/skills/templates, run `python3 tools/build_bundle.py` and `python3 -m unittest discover -s tests -v`. Run the quickstart after lifecycle changes. Do not add a prebuilt stack-specialist catalog or product-specific profiles: projects generate their own packages. Preserve MIT notices in copied/installed distributions.

Keep credentials, private project data, local task databases, transcripts, prompt/session records and machine-specific logs out of contributions. Public documentation should describe current behavior and limits rather than internal progress notes. Do not include private data in issue reports or reproductions. No global agent configuration or network service is required by the runtime.

Before preparing a candidate, run all three example runners and review [validation](docs/validation.md). Keep deterministic replay distinct from actual live-agent evidence. Changes to scoped freshness, Git paths or evidence presentation need negative safety cases, not only a passing happy path.

The package version constant supplies installer release metadata. Keep public version claims and installed metadata consistent; the installed-license regression also verifies that metadata uses the current executing release.

For recovery changes, include real disposable-process interruption/ownership tests and persistence fault cases; do not equate expired leases or a free lock with complete process death. Keep context/health diagnostics read-only and policy digests separate from authorization.

Journal changes must retain exact-SHA identity, consecutive-only observation deduplication, damaged-state refusal, current-owner reconfirmation and evidence publication ordering. Tests that simulate review actors must remain clearly synthetic; actual independent review cannot be invented for examples.

## Development checkout and future public exports

The canonical development checkout is the only place to edit and commit product code. A separate private records folder stores archived development evidence; active CLI state remains in the checkout's ignored `.tequio/` until an external state backend is explicitly supported. Read the development checkout's root AGENTS.md when present; that local workflow document is intentionally omitted from source-only public exports.

In a configured development checkout, `python3 tools/check_checkout.py` performs read-only root/origin/branch/version/records-path checks. It reports existing changes without approving or discarding them; missing or mismatched identity is never repaired automatically. Machine-specific identity belongs in local Git configuration, not tracked product files.

`python3 tools/public_inventory.py --commit FULL_COMMIT_SHA` inspects the file inventory and content hashes for a possible future source-only export. It creates no destination and transfers no Git history or author metadata. Unknown/private/generated paths and nonregular source entries are refused. A passing inventory is not a content/secret review, owner approval or publication authorization. Generate any future export from the exact reviewed commit; fix source in the canonical checkout and regenerate rather than editing an export separately. Keep public Git history independent from private development history.

Recorded release qualification counts describe the qualified release revision. Additional development-tool cases in tests/test_development_tools.py exercise housekeeping safeguards; they do not change the runtime release or certify conversational behavior/privacy.
