# Freshness contracts

Tasks without `freshness`, or with `{"mode":"global"}`, retain whole-phase input and whole-project evidence fingerprints. Existing records and IDs are not rewritten. Phase recording and task import still require current global analysis and plan receipts. Final integrated testing remains necessary: resource declarations coordinate work and scope evidence, but do not sandbox arbitrary writes or prove that undeclared dependencies are absent.

An author may explicitly assess independence and opt a new immutable task into this contract:

```json
"freshness": {
  "mode": "scoped-v1",
  "independent": true,
  "shared_contracts": ["src/interfaces"],
  "config": ["pyproject.toml"],
  "mandatory_context": ["analysis/architecture.md"]
}
```

All three arrays are required, even when empty. Shared contracts and configuration are concrete project-relative files or directories. Mandatory context is workspace-relative and restricted to phase-source directories. Globs, traversal, reserved toolkit paths and symlink roots are refused by the existing resource safety checks. Directory resources cover their entire content, including new files. Missing project resources are fingerprinted as absent, so creating one changes evidence. Use explicit reads for imports, runtime configuration, check scripts and other external project dependencies; command arguments alone do not discover these dependencies. Document why the declared boundary is sufficient during independent review. If that cannot be established, use global mode.

Scoped task inputs bind the task definition (including checks, sources, acceptance and documentation policy), controller workspace configuration, current specialist qualification bindings, all mandatory briefs and specifications, each referenced source file and explicit mandatory context. Source fragments select an entire file conservatively. An unreferenced new analysis or future-plan file is independent; a new brief or specification is mandatory and invalidates affected work. Referenced source edits always invalidate inputs. Scoped lifecycle operations may continue through unrelated global phase drift; status still reports the actual global phase staleness and workflow orientation conservatively recommends reconciliation. New imports cannot bypass this global gate.

Check, documentation and review evidence use one consistent task snapshot: inputs plus declared reads, writes, shared contracts, configuration and documentation paths, together with recursive dependency state, outputs and snapshots. Changes in those resources stale affected evidence; unrelated project files and unrelated task additions do not. Shared contracts, configuration and documentation paths also participate as reads in active-task resource conflict checks. Checks must see a stable snapshot before and after execution. Completion requires the usual fresh checks, documentation reconciliation, report integrity and distinct required reviewers. An active task also refuses verification or closure when a completed prerequisite or transitive prerequisite is stale, incomplete, or has changed outputs. Legacy prerequisites retain their conservative global input semantics; completed scoped prerequisites require their recorded result snapshot.

To migrate unfinished global work, inspect actual owners, release active claims deliberately, reconcile and record phases, then import new task IDs with reviewed scope. Do not edit database bodies, retrofit historical receipts, or claim old checks satisfy the new fingerprint. History remains intact. No automatic migration, integrated-test exemption or inferred independence is provided. Scope errors require review and replan; they cannot be detected reliably from filenames alone.

Declared directory resources and scoped phase/context directory trees refuse symlink descendants, including links introduced after review. Linked targets cannot be silently treated as unchanged inputs. Reserved toolkit resources are checked after path normalization, including dot-prefixed spellings.

## Revision and explicit policy separation

[Reviewed revision](revision.md) records effective dependencies and a new current input binding separately from immutable definitions. Rebound unfinished consumers need new checks/docs/reviews in all freshness modes; identical source bytes cannot revive earlier proof. Completed historical edges remain untouched and may block later unfinished dependents. No overlay leaves existing fingerprints unchanged. Broad replan retains its documented semantics with effective edges accounted for.

For new work, assess disjoint scoped-v1 policy and functional ownership/read resources, then make final integration depend on both. Policy checks execute against exact current protection bytes; changed policy proof blocks integrated acceptance while genuinely independent functional proof may stay current. Functional source, runtime/shared configuration, semantic interface documentation, overlapping ancestor paths and real transitive dependencies still invalidate affected functional/security proof. File extensions and `.gitignore` have no exemption. Global/mixed histories stay conservative; migrate through reviewed new successors and new current checks, never cached PASS or a generic reconciliation waiver. No installer layout/default change follows from this authoring pattern.
