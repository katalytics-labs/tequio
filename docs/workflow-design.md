# Workflow design

Tequio turns a brief into source-linked analysis, architecture and detailed bounded tasks, then coordinates implementation, verification, independent review and durable handoffs. Product requirements remain separate from reusable development machinery.

## Phase and artifact flow

| Stage | Artifacts and responsibility |
|---|---|
| Intake | Explicit workspace and copied brief; no selection by modification time. |
| Analysis | Source-linked requirements, current/intended behavior, risks, alternatives and domain contracts. Reuse relevant research while identifying dated or missing evidence. |
| Plan | Complete scope, coherent milestones, dependency order, integration ownership and qualification criteria. Later work stays visible but provisional. |
| Detailed todos | Immutable IDs, source references, acceptance, actual check commands, dependencies and read/write ownership. Draft work is not dispatchable. |
| Implementation | One bounded outcome by default; independent ready tasks can run in parallel within declared resources and host limits. Read source requirements and current code before edits. |
| Verification | Execute real commands; retain output, input fingerprints and project-content/mode snapshots. Failed or stale checks do not support closure. |
| Review | A distinct reviewer evaluates acceptance, integration and actual evidence; security-sensitive work additionally gets adversarial review. Missing reports are not clean. |
| Handoff | Explicit checkpoint, current state and next action. Resume reconciles actual files/evidence and genuine live handles before proceeding. |
| Learning | Update applicable guidance from demonstrated failures or useful patterns; avoid speculative rules and transcript duplication. |
| Release preparation | Assemble an explicitly allowlisted local candidate, inspect it and test exported contents. Publication remains a separate authorized action. |

## Design choices and trade-offs

Skills supply engineering procedures and composable expertise; role profiles support actual host delegation. A standard-library CLI enforces its own lifecycle transitions with SQLite workspace state and project-level claim coordination. No model SDK or external orchestration service is required.

Content fingerprints detect changed inputs even when timestamps are restored. Conservative snapshots may require re-verification after unrelated changes. Scoped completed-output fingerprints detect stale prerequisites without freezing the entire project forever. Declarations and semantic acceptance still require agent compliance and review.

Explicit read/write resources prevent conflicting CLI claims across a local project's workspaces. They do not sandbox arbitrary host edits. Review identity fields are declared audit metadata, not cryptographic authentication. A receipt establishes file/command state rather than the quality of analysis or correctness of a test suite.

Hooks are optional host adapters, not the basis for universal enforcement. The included read-only audit can be explicitly integrated by a host; it is not automatically registered. Details and qualified limits are in architecture.md, operator-guide.md and validation.md.

## Product-first uncertainty and assurance

Use a small experiment only for a named uncertainty blocking the next useful product outcome. Inventory reusable code/evidence before building a fixture; choose minimal faithful positive and adverse observations, actual effects, a time/correction/resource ceiling and a concrete decision/next slice. The optional [experiment template](../templates/experiment.md) is a short record, not a mandatory task schema or runtime status system. Complete sufficient evidence can support or rule out a bounded path; missing input/budget leaves it unqualified.

Order cheap boundary checks before expensive integration. Distinguish developer feedback, focused finding rechecks, stable independent correctness/security review and final combined qualification. Intermediate edits do not automatically require full dual review each time. Material authorization/privacy/interface/process/configuration corrections require current affected proof and actual independent review. Final acceptance still covers every agreed outcome, current docs/checks and required reviewers. [Revision](revision.md) can preserve unchanged backlog identities while explicitly invalidating affected proof; it does not reduce these gates.
