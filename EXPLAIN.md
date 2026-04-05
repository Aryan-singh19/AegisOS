# EXPLAIN

Auto-updated project explainer for contributors.
Last generated: 2026-04-05 10:07:18Z

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

- Open issues are tracked on GitHub and loaded during CI automation runs.

## Recent Engineering Changes

- `242200b` (2026-04-05): Add_sandbox_policy_schema_validator_and_tests
- `cccdb53` (2026-04-05): Add_capability_token_lifecycle_issue_revoke_access_checks
- `64be98e` (2026-04-05): Add_round_robin_scheduler_skeleton_with_tests
- `594b792` (2026-04-05): Add_capability_security_module_and_execution_plan
- `2c02b03` (2026-04-05): Initialize_AegisOS_scaffold
