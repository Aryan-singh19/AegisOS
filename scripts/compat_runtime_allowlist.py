#!/usr/bin/env python3
import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ViolationEvent:
  timestamp_epoch: int
  runtime_name: str
  syscall_id: int
  reason: str


@dataclass
class RuntimeEntry:
  runtime_name: str
  allowed_syscalls: Dict[int, int] = field(default_factory=dict)
  checks: int = 0
  allows: int = 0
  denies: int = 0


@dataclass
class CompatibilityRuntimeAllowlist:
  runtimes: Dict[str, RuntimeEntry] = field(default_factory=dict)
  violations: List[ViolationEvent] = field(default_factory=list)
  max_violations: int = 1024

  def register_runtime(self, runtime_name: str, syscall_ids: List[int]) -> None:
    if not runtime_name:
      raise ValueError("runtime_name is required")
    if not isinstance(syscall_ids, list):
      raise ValueError("syscall_ids must be a list")
    allowed: Dict[int, int] = {}
    for syscall_id in syscall_ids:
      if not isinstance(syscall_id, int) or syscall_id <= 0:
        raise ValueError("syscall_ids must contain positive integers")
      allowed[syscall_id] = 1
    self.runtimes[runtime_name] = RuntimeEntry(runtime_name=runtime_name, allowed_syscalls=allowed)

  def _record_violation(self, timestamp_epoch: int, runtime_name: str, syscall_id: int, reason: str) -> None:
    event = ViolationEvent(
        timestamp_epoch=timestamp_epoch,
        runtime_name=runtime_name,
        syscall_id=syscall_id,
        reason=reason,
    )
    self.violations.append(event)
    if len(self.violations) > self.max_violations:
      self.violations = self.violations[-self.max_violations :]

  def check_syscall(self, runtime_name: str, syscall_id: int, timestamp_epoch: int = 0) -> bool:
    if not isinstance(syscall_id, int) or syscall_id <= 0:
      raise ValueError("syscall_id must be a positive integer")
    if not isinstance(timestamp_epoch, int) or timestamp_epoch < 0:
      raise ValueError("timestamp_epoch must be a non-negative integer")
    entry = self.runtimes.get(runtime_name)
    if entry is None:
      self._record_violation(timestamp_epoch, runtime_name, syscall_id, "runtime_not_registered")
      return False
    entry.checks += 1
    if entry.allowed_syscalls.get(syscall_id, 0) == 1:
      entry.allows += 1
      return True
    entry.denies += 1
    self._record_violation(timestamp_epoch, runtime_name, syscall_id, "syscall_not_allowlisted")
    return False

  def add_syscall(self, runtime_name: str, syscall_id: int) -> None:
    if runtime_name not in self.runtimes:
      raise ValueError("runtime not registered")
    if not isinstance(syscall_id, int) or syscall_id <= 0:
      raise ValueError("syscall_id must be a positive integer")
    self.runtimes[runtime_name].allowed_syscalls[syscall_id] = 1

  def remove_syscall(self, runtime_name: str, syscall_id: int) -> None:
    if runtime_name not in self.runtimes:
      raise ValueError("runtime not registered")
    if syscall_id in self.runtimes[runtime_name].allowed_syscalls:
      del self.runtimes[runtime_name].allowed_syscalls[syscall_id]

  def violation_export_json(self) -> str:
    payload = {
        "schema_version": 1,
        "count": len(self.violations),
        "violations": [
            {
                "timestamp_epoch": v.timestamp_epoch,
                "runtime_name": v.runtime_name,
                "syscall_id": v.syscall_id,
                "reason": v.reason,
            }
            for v in self.violations
        ],
    }
    return json.dumps(payload, separators=(",", ":"))

  def summary_json(self) -> str:
    payload = {
        "schema_version": 1,
        "runtime_count": len(self.runtimes),
        "violation_count": len(self.violations),
        "runtimes": [],
    }
    for runtime_name in sorted(self.runtimes.keys()):
      entry = self.runtimes[runtime_name]
      payload["runtimes"].append(
          {
              "runtime_name": entry.runtime_name,
              "allowlisted_syscall_count": len(entry.allowed_syscalls),
              "checks": entry.checks,
              "allows": entry.allows,
              "denies": entry.denies,
          }
      )
    return json.dumps(payload, separators=(",", ":"))


def demo() -> int:
  allowlist = CompatibilityRuntimeAllowlist()
  allowlist.register_runtime("win32-compat", [1, 2, 3, 9, 10, 42])
  print(allowlist.check_syscall("win32-compat", 3, 1))
  print(allowlist.check_syscall("win32-compat", 77, 2))
  print(allowlist.summary_json())
  print(allowlist.violation_export_json())
  return 0


if __name__ == "__main__":
  raise SystemExit(demo())
