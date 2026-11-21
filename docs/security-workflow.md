# Security workflow

The maintained [security contract](../skills/tequio-tasks/references/security-workflow.md) documents task assessment categories, risk/reviewer rules, integrated release candidate scope and coverage reports, evidence freshness, historical migration and external-copy limitations. This reference is installed with the existing task skill so project-local agents can read the same contract without retaining the source checkout.

Implementation: `src/tequio/security.py` centralizes assessment, required reviews and structured release coverage; `core.py` applies lifecycle gates; `freshness.py` binds candidate and release resources; status, orientation, integration diagnostics and proof expose migration state. Tests in `tests/test_security.py` exercise malformed/draft assessment, release scope, coverage, current review/closure, ignored-resource drift and legacy read/recovery paths. No additional skill, role, scanner or generic specialist catalog is introduced.
