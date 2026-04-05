# Architecture (Initial)

## High-Level Model

- Microkernel-inspired core with modular services in user space.
- Capability-based security model between components.
- Immutable base system + transactional updates.

## Layers

1. Boot & Trust Layer
   - Secure boot verification chain.
   - Measured boot and rollback protection.

2. Kernel Layer
   - Scheduling, memory, IPC, device primitives.
   - Hardened syscall surface and strict ABI versioning.

3. System Services Layer
   - Filesystem manager.
   - Network and policy engine.
   - Identity and credential service.
   - Package/update daemon.

4. Runtime & Compatibility Layer
   - Native app runtime.
   - Sandboxed compatibility runtime for legacy/foreign apps.

5. UX Layer
   - Compositor/window manager.
   - Settings and policy controls.
   - Accessibility and localization.

## Design Decisions

- Keep TCB small.
- Move risky functionality to isolated services.
- Ship secure defaults; allow advanced overrides.

