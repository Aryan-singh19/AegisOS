# EXPLAIN

Auto-updated project explainer for contributors.
Last generated: 2026-04-05 10:24:53Z

## What AegisOS Is Building

AegisOS is a security-first operating system designed to combine the strongest traits of major platforms in one coherent product:

- iOS: secure defaults, trusted update path, cohesive platform behavior.
- Linux: customization, openness, privacy-first control.
- Windows: practical compatibility strategy for apps and workflows.
- macOS: polish, consistency, and efficiency.
- Android: broad device profile flexibility.

## How We Build It

We implement in vertical slices:

1. Core kernel and scheduler primitives.
2. Security controls (capabilities, sandbox policies, enforcement engine).
3. Packaging and update integrity.
4. UX and compatibility layers.
5. Observability, reliability, and contributor scale-out.

## Current Technical Baseline

- Kernel simulation target with round-robin scheduler skeleton and tests.
- Capability token lifecycle (`issue`, `revoke`, authorization checks).
- Sandbox policy schema validator and test suite.
- CI/docs workflows and contributor-ready GitHub templates.

## Live Backlog Snapshot

### Priority P0
- none

### Priority P1
- none

### Security
- none

### Kernel
- none

### Good First Task
- none

### Other
- none

## Recent Engineering Changes

- `6a7a49c` (2026-04-05): docs: auto-update explain and changelog
- `886b81c` (2026-04-05): Add_symlink_resolution_rules_for_filesystem_scope_checks
- `4523e6b` (2026-04-05): docs: auto-update explain and changelog
- `ef5dd0b` (2026-04-05): Add_network_scope_enforcement_host_port_protocol_rules
- `306b2e4` (2026-04-05): docs: auto-update explain and changelog
- `44e7fac` (2026-04-05): Add_clang_matrix_workflow_for_core_module_tests
- `e0f7189` (2026-04-05): docs: auto-update explain and changelog
- `abdd8fa` (2026-04-05): Add_path_scoped_filesystem_enforcement_with_deny_override
- `7b72999` (2026-04-05): docs: auto-update explain and changelog
- `7ce10dc` (2026-04-05): Add_package_manifest_validator_and_ci_workflow
- `e3d506e` (2026-04-05): docs: auto-update explain and changelog
- `613b123` (2026-04-05): Add_auto_docs_workflow_and_sandbox_policy_engine_mvp
- `242200b` (2026-04-05): Add_sandbox_policy_schema_validator_and_tests
- `cccdb53` (2026-04-05): Add_capability_token_lifecycle_issue_revoke_access_checks
- `64be98e` (2026-04-05): Add_round_robin_scheduler_skeleton_with_tests
