---
name: tequio-package
description: "Prepare and inspect a local release candidate from explicitly selected product files without publishing it or exposing private development state."
---

# Tequio Package

## Runtime and context

Use `python3 bin/tequio --project <absolute-project> --workspace <name> ...`. Select workspace explicitly from the user's task or the default `main`; never pick by modification time. Installed instructions/assets are under `.tequio/`. Read `.tequio/roles/orchestrator.md` and only relevant specialist skills. User/host instructions govern; this toolkit does not override authorization or grant tools. Keep task tokens, evidence, prompts and working notes private. Do not print secrets in summaries.

## Procedure

Read product release requirements and current completion/evidence state. Obtain an explicit list of intended product files and a fresh destination outside the working repository. Use `.tequio/templates/release-checklist.md`. Assemble reviewed contents without private development history; include required notices and source obligations, preserve legitimate contributor attribution, inspect deletions and verify the exported product itself.

Exclude private agent instructions, prompts/sessions, workspace state, environment credentials, private tests/data and derived copies. Filename scanning is not proof that copied private text is absent. Fail on unknown/unreviewed material; do not emit matching secrets/private excerpts to public logs. Record candidate provenance privately and public-facing rationale separately. No remote push, PR, visibility change, tag, deployment or publication is authorized by this skill alone.

## Security workflow

Represent the integrated candidate review as `kind: release`, with declared project-side candidate paths and security assessment. Read [security workflow](../tequio-tasks/references/security-workflow.md) and use release-task.json and release-security-report.json. Review and verify the project-side candidate before any external copy; compare that copy exactly and retain private provenance. The runtime does not bind external destination contents.
