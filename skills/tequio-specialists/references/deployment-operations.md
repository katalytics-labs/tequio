# Deployment and operations reference

Use when the project produces artifacts, manages environment configuration or secrets, or needs rollout/recovery practices — including local or single-machine distribution. Skip only when none of these concerns apply; a local rollout is still a rollout. Shared source, execution and qualification rules: [coverage guide](coverage-guide.md). Preparing deployment guidance never authorizes an actual deployment, cloud effect or paid service.

## Questions the agent resolves from project context

- Artifacts and environments: what is built, how is configuration separated per environment, and where do secrets live (never in the artifact or repo)?
- CI/CD and approval: which steps are automated, which need explicit human approval, and what stops an unauthorized release?
- Health and readiness: what checks distinguish "process started" from "ready to serve", including dependency readiness?
- Migrations and rollout: how do schema changes interact with old/new versions running together? Destructive migrations are not assumed reversible — require a recovery strategy (backup/restore, expand-contract, forward fix) suited to the actual data and schema constraints.
- Rollback limits: what can genuinely be reverted, and what cannot (dropped columns, transformed data, external side effects)? State the realistic limit.
- Observability and recovery: what signals detect failure, and what backup/restore/recovery path has actually been exercised?

## Sources

The selected host/platform/CI system's exact primary docs are authoritative. Keep simple deployments simple: static hosting, a single service or a local process need no forced cloud, Kubernetes or GitOps. Optional candidates, accessed 2026-11-17: [OpenGitOps](https://opengitops.dev/) (Principles v1.0.0: declarative, versioned/immutable, pulled automatically, continuously reconciled) only when GitOps actually fits; the [Google SRE Workbook](https://sre.google/workbook/table-of-contents/) index (observed chapters include SLOs, monitoring, configuration, canarying, incident response and overload recovery — retrieve the applicable chapter before substantive claims). Neither is a general deployment requirement.

## Exercise considerations

Realistic exercises include a failed rollout with a realistic recovery decision and an irreversible migration where "just roll back" must be rejected in favor of a viable recovery path. Cover expected and denied/failure behavior; no live cloud mutation is implied.
