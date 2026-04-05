# Package Profile Compatibility Matrix

This matrix maps AegisOS package profiles to target hardware classes so contributors can align
feature scope, defaults, and test expectations.

## Matrix

| Profile | Target Hardware Class | CPU/RAM Envelope | Graphics Expectation | Primary Use Case |
|---|---|---|---|---|
| `minimal` | Legacy and resource-constrained systems | Dual-core class, 2-4 GB RAM | No compositor required | Recovery systems, kiosks, old hardware |
| `desktop` | Mainstream laptops and desktops | Quad-core class, 8+ GB RAM | Integrated GPU baseline | Daily end-user workstation |
| `developer` | High-throughput engineering systems | Quad-core+, 16+ GB RAM | Integrated or discrete GPU | SDK/toolchain, debugging, local builds |
| `server` | Headless server and VM fleets | Quad-core class, 8+ GB RAM | Headless/no desktop stack | Service hosting and infra nodes |

## Compatibility Notes

- `minimal` avoids desktop shell and developer SDK to preserve memory and disk footprint.
- `desktop` optimizes for balanced UX + security defaults on commodity hardware.
- `developer` extends `desktop` with SDK/tooling for local platform development.
- `server` excludes desktop UX components and biases toward hardened headless operation.

## Validation Guidance

- Keep `packages/profiles/*.yaml` aligned with this matrix.
- If profile package composition changes, update this matrix in the same PR.
- Validate with `python scripts/validate_packages.py`.
