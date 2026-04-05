# userland

Core userspace services, shell tools, and runtime components live here.

## Current Modules

- `capability`: capability validation plus lifecycle operations (issue, revoke, access check).
  - includes token expiry (TTL) and rotation APIs.
  - includes in-memory audit event pipeline for allow/deny/issue/rotate/revoke.
- `sandbox_policy`: policy schema validation for filesystem/network/device permissions.
- `sandbox_engine`: action-level enforcement using policy gates + capability tokens.
  - includes path-level filesystem scopes (`deny`, `read-only`, `read-write`) with deny override behavior.
  - supports simple wildcard patterns (`*`) in filesystem scope rules.
  - includes network scopes (host/port/protocol rules with explicit allow/deny).
  - network rule precedence is deterministic: most specific match wins; tie -> deny.
  - includes symlink mapping resolution before filesystem scope checks.
