# packages

Package metadata for AegisOS base components.

- `core/` fundamental base-system package definitions.
- `profiles/` install bundles for desktop/server/minimal variants.

Core package groups:

- Kernel and scheduling: `aegis-kernel`, `aegis-scheduler`
- Security stack: `aegis-security-core`, `aegis-sandbox-engine`
- System services: `aegis-userland-base`, `aegis-update-service`
- UX and dev: `aegis-desktop-shell`, `aegis-developer-sdk`

Profile targets:

- `minimal`: lowest-resource install base.
- `desktop`: default end-user profile.
- `developer`: desktop plus SDK bundle.
- `server`: hardened non-desktop profile.

Validation command:

- `python scripts/validate_packages.py`
  - also exports graph files:
    - `packages/dependency-graph.json`
    - `packages/dependency-graph.dot`

Manifest note:

- `schema_version: 1` is required in each core/profile manifest.
