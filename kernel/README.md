# kernel

Kernel direction, interfaces, and implementation notes live here.

## Current Modules

- `aegis_scheduler_t`: weighted round-robin scheduler with priority-aware dispatch.
  - includes dispatch metrics: total dispatches, high-watermark queue depth, and per-process counts.
  - includes timer-tick preemption simulation hooks with configurable quantum.
  - includes structured metrics snapshot API for observability integration.
  - includes tick-based wait-time and last-latency counters per process.
