# Local release-candidate checklist

- Explicit product file allowlist, output destination and source revision/content provenance.
- No private Git ancestry, toolkit/workspace assets, prompts/session/memory/instructions or copied excerpts; review source, packages and metadata, not only names.
- Required licences/notices/corresponding source and contributor attribution.
- Inspect intended removals, actual exported diff and complete resulting product.
- Run relevant setup/build/tests on exported contents; record evidence privately.
- Document limitations, supported install/update path and product architecture rationale publicly as appropriate.
- Keep candidate preparation distinct from publication. No push/tag/PR/deploy without applicable authorization.

- Import a `kind: release`, `risk: security` task with explicit assessment and concrete project-side candidate paths covered by resources.
- Review actual candidate inventory, dependency manifests/locks, configuration/defaults and privacy/secret/export boundaries with current independent security coverage; explain not-applicable areas and gaps.
- Use release-security-report.json and existing review receipts. See ../skills/tequio-tasks/references/security-workflow.md for precise schema and external-copy limitations.
