# Security Model

## Threat Model (v0)

- Malware from untrusted apps.
- Supply chain compromise in package/update path.
- Privilege escalation via kernel/service bugs.
- Data exfiltration through excessive permissions.

## Security Controls

- Verified boot from firmware to userspace.
- Mandatory app signing and reputation policy.
- Per-app sandbox with default deny filesystem/network scopes.
- Capability tokens instead of broad global privileges.
- Memory-safe language preference for new services.
- ASLR, CFI, W^X, stack protections, syscall filtering.

## Update Security

- Signed update manifests.
- Atomic A/B updates with rollback.
- Transparent update logs and reproducible build attestations.

## Privacy Defaults

- Telemetry off by default.
- Permission prompts are explicit and revocable.
- Local-first storage and encrypted user data at rest.

