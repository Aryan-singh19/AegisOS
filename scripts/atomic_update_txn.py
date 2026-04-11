#!/usr/bin/env python3
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List


class TxnState(str, Enum):
  IDLE = "idle"
  PREPARED = "prepared"
  COMMITTED = "committed"
  ROLLED_BACK = "rolled_back"


@dataclass
class AtomicUpdateTransaction:
  state: TxnState = TxnState.IDLE
  transaction_id: str = ""
  manifest_hash: str = ""
  staged_packages: List[str] = field(default_factory=list)
  rollback_reason: str = ""

  def begin(self, transaction_id: str, manifest_hash: str) -> None:
    if self.state != TxnState.IDLE:
      raise ValueError("transaction already active")
    if not transaction_id or not manifest_hash:
      raise ValueError("transaction_id and manifest_hash are required")
    self.state = TxnState.PREPARED
    self.transaction_id = transaction_id
    self.manifest_hash = manifest_hash
    self.staged_packages = []
    self.rollback_reason = ""

  def stage_package(self, package_name: str) -> None:
    if self.state != TxnState.PREPARED:
      raise ValueError("can stage only in prepared state")
    if not package_name:
      raise ValueError("package_name is required")
    if package_name not in self.staged_packages:
      self.staged_packages.append(package_name)

  def commit(self) -> None:
    if self.state != TxnState.PREPARED:
      raise ValueError("can commit only in prepared state")
    if not self.staged_packages:
      raise ValueError("cannot commit transaction with no staged packages")
    self.state = TxnState.COMMITTED

  def rollback(self, reason: str) -> None:
    if self.state not in (TxnState.PREPARED, TxnState.COMMITTED):
      raise ValueError("can rollback only prepared or committed transaction")
    self.state = TxnState.ROLLED_BACK
    self.rollback_reason = reason or "rollback_requested"

  def reset(self) -> None:
    self.state = TxnState.IDLE
    self.transaction_id = ""
    self.manifest_hash = ""
    self.staged_packages = []
    self.rollback_reason = ""

  def summary_json(self) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "state": self.state.value,
            "transaction_id": self.transaction_id,
            "manifest_hash": self.manifest_hash,
            "staged_count": len(self.staged_packages),
            "staged_packages": list(self.staged_packages),
            "rollback_reason": self.rollback_reason,
        },
        separators=(",", ":"),
    )

  def load_from_json(self, payload: str) -> None:
    data = json.loads(payload)
    if not isinstance(data, dict):
      raise ValueError("payload must be a JSON object")
    if data.get("schema_version") != 1:
      raise ValueError("unsupported schema_version")
    state = data.get("state")
    if state not in {s.value for s in TxnState}:
      raise ValueError("invalid transaction state")
    transaction_id = data.get("transaction_id", "")
    manifest_hash = data.get("manifest_hash", "")
    rollback_reason = data.get("rollback_reason", "")
    staged_packages = data.get("staged_packages", [])
    staged_count = data.get("staged_count", len(staged_packages))
    if not isinstance(transaction_id, str) or not isinstance(manifest_hash, str):
      raise ValueError("transaction_id and manifest_hash must be strings")
    if not isinstance(rollback_reason, str):
      raise ValueError("rollback_reason must be a string")
    if not isinstance(staged_packages, list) or not all(isinstance(x, str) and x for x in staged_packages):
      raise ValueError("staged_packages must be a list of non-empty strings")
    if not isinstance(staged_count, int) or staged_count < 0:
      raise ValueError("staged_count must be a non-negative integer")
    deduped = []
    for pkg in staged_packages:
      if pkg not in deduped:
        deduped.append(pkg)
    if state == TxnState.PREPARED.value and (not transaction_id or not manifest_hash):
      raise ValueError("prepared transaction requires transaction_id and manifest_hash")
    if staged_count != len(deduped):
      raise ValueError("staged_count mismatch with staged_packages")
    if state == TxnState.COMMITTED.value:
      if not transaction_id or not manifest_hash or not deduped:
        raise ValueError("committed transaction requires id/hash/staged packages")
    if state == TxnState.IDLE.value:
      if transaction_id or manifest_hash or deduped or rollback_reason:
        raise ValueError("idle transaction must not contain active fields")
    self.state = TxnState(state)
    self.transaction_id = transaction_id
    self.manifest_hash = manifest_hash
    self.staged_packages = deduped
    self.rollback_reason = rollback_reason

  def save_to_file(self, path: str) -> None:
    if not path:
      raise ValueError("path is required")
    target = Path(path)
    if target.exists() and target.is_dir():
      raise ValueError("path must be a file path, not a directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = self.summary_json()
    envelope = json.dumps(
        {
            "schema_version": 1,
            "checksum": "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "payload": json.loads(payload),
        },
        separators=(",", ":"),
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(target.parent),
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
      tmp.write(envelope)
      temp_path = tmp.name
    os.replace(temp_path, target)

  def load_from_file(self, path: str) -> None:
    if not path:
      raise ValueError("path is required")
    source = Path(path)
    if not source.exists() or source.is_dir():
      raise ValueError("path must point to an existing file")
    raw = source.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
      raise ValueError("invalid transaction file envelope")
    checksum = data.get("checksum", "")
    payload = data.get("payload")
    if not isinstance(checksum, str) or not checksum.startswith("sha256:"):
      raise ValueError("invalid transaction file checksum")
    if not isinstance(payload, dict):
      raise ValueError("invalid transaction file payload")
    payload_text = json.dumps(payload, separators=(",", ":"))
    actual = "sha256:" + hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    if actual != checksum:
      raise ValueError("transaction file checksum mismatch")
    self.load_from_json(payload_text)


@dataclass
class RollbackIndexStore:
  state_path: str
  _state: dict = field(default_factory=lambda: {"schema_version": 1, "channels": {}})

  def _load_envelope(self) -> None:
    path = Path(self.state_path)
    if not path.exists():
      self._state = {"schema_version": 1, "channels": {}}
      return
    if path.is_dir():
      raise ValueError("rollback index path must be a file")
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
      raise ValueError("invalid rollback index envelope")
    checksum = data.get("checksum", "")
    payload = data.get("payload")
    if not isinstance(checksum, str) or not checksum.startswith("sha256:"):
      raise ValueError("invalid rollback index checksum")
    if not isinstance(payload, dict):
      raise ValueError("invalid rollback index payload")
    payload_text = json.dumps(payload, separators=(",", ":"))
    actual = "sha256:" + hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    if actual != checksum:
      raise ValueError("rollback index checksum mismatch")
    if payload.get("schema_version") != 1:
      raise ValueError("unsupported rollback index schema_version")
    channels = payload.get("channels", {})
    if not isinstance(channels, dict):
      raise ValueError("invalid rollback index channels")
    self._state = payload

  def _save_envelope(self) -> None:
    path = Path(self.state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(self._state, separators=(",", ":"))
    envelope = json.dumps(
        {
            "schema_version": 1,
            "checksum": "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "payload": json.loads(payload),
        },
        separators=(",", ":"),
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
      tmp.write(envelope)
      temp_path = tmp.name
    os.replace(temp_path, path)

  def _channel_state(self, channel: str) -> dict:
    if not channel:
      raise ValueError("channel is required")
    channels = self._state.setdefault("channels", {})
    if channel not in channels:
      channels[channel] = {
          "current_index": 0,
          "last_transaction_id": "",
          "last_manifest_hash": "",
          "updated_at_epoch": 0,
          "history": [],
      }
    entry = channels[channel]
    if not isinstance(entry, dict):
      raise ValueError("invalid channel state")
    history = entry.get("history", [])
    if not isinstance(history, list):
      raise ValueError("invalid rollback history")
    if "current_index" not in entry:
      entry["current_index"] = 0
    if "last_transaction_id" not in entry:
      entry["last_transaction_id"] = ""
    if "last_manifest_hash" not in entry:
      entry["last_manifest_hash"] = ""
    if "updated_at_epoch" not in entry:
      entry["updated_at_epoch"] = 0
    return entry

  def assert_monotonic(self, channel: str, candidate_index: int) -> None:
    self._load_envelope()
    if not isinstance(candidate_index, int) or candidate_index < 0:
      raise ValueError("candidate_index must be a non-negative integer")
    entry = self._channel_state(channel)
    current = int(entry.get("current_index", 0))
    if candidate_index < current:
      raise ValueError("rollback index regression detected")

  def advance(self,
              channel: str,
              candidate_index: int,
              transaction_id: str,
              manifest_hash: str,
              now_epoch: int = 0) -> None:
    if not transaction_id or not manifest_hash:
      raise ValueError("transaction_id and manifest_hash are required")
    if not isinstance(now_epoch, int) or now_epoch < 0:
      raise ValueError("now_epoch must be a non-negative integer")
    self._load_envelope()
    self.assert_monotonic(channel, candidate_index)
    entry = self._channel_state(channel)
    entry["current_index"] = candidate_index
    entry["last_transaction_id"] = transaction_id
    entry["last_manifest_hash"] = manifest_hash
    entry["updated_at_epoch"] = now_epoch
    history = entry.setdefault("history", [])
    history.append(
        {
            "index": candidate_index,
            "transaction_id": transaction_id,
            "manifest_hash": manifest_hash,
            "updated_at_epoch": now_epoch,
        }
    )
    if len(history) > 128:
      entry["history"] = history[-128:]
    self._save_envelope()

  def summary_json(self) -> str:
    self._load_envelope()
    return json.dumps(self._state, separators=(",", ":"))


@dataclass
class ReleaseChannelPolicyStore:
  state_path: str
  _state: dict = field(
      default_factory=lambda: {
          "schema_version": 1,
          "pinned_channel": "stable",
          "allow_downgrade": 0,
          "allowed_channels": ["stable", "beta", "nightly"],
          "updated_at_epoch": 0,
      }
  )

  def _load(self) -> None:
    path = Path(self.state_path)
    if not path.exists():
      self._state = {
          "schema_version": 1,
          "pinned_channel": "stable",
          "allow_downgrade": 0,
          "allowed_channels": ["stable", "beta", "nightly"],
          "updated_at_epoch": 0,
      }
      return
    if path.is_dir():
      raise ValueError("release policy path must be a file")
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
      raise ValueError("invalid release policy envelope")
    checksum = data.get("checksum", "")
    payload = data.get("payload")
    if not isinstance(checksum, str) or not checksum.startswith("sha256:"):
      raise ValueError("invalid release policy checksum")
    if not isinstance(payload, dict):
      raise ValueError("invalid release policy payload")
    payload_text = json.dumps(payload, separators=(",", ":"))
    actual = "sha256:" + hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    if actual != checksum:
      raise ValueError("release policy checksum mismatch")
    self._state = payload

  def _save(self) -> None:
    path = Path(self.state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(self._state, separators=(",", ":"))
    envelope = json.dumps(
        {
            "schema_version": 1,
            "checksum": "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "payload": json.loads(payload),
        },
        separators=(",", ":"),
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
      tmp.write(envelope)
      temp_path = tmp.name
    os.replace(temp_path, path)

  def set_policy(self,
                 pinned_channel: str,
                 allow_downgrade: bool = False,
                 allowed_channels: List[str] | None = None,
                 now_epoch: int = 0) -> None:
    if pinned_channel not in ("stable", "beta", "nightly"):
      raise ValueError("invalid pinned channel")
    if allowed_channels is None:
      allowed_channels = ["stable", "beta", "nightly"]
    if not isinstance(allowed_channels, list) or not allowed_channels:
      raise ValueError("allowed_channels must be a non-empty list")
    clean_channels = []
    for channel in allowed_channels:
      if channel not in ("stable", "beta", "nightly"):
        raise ValueError("invalid channel in allowed_channels")
      if channel not in clean_channels:
        clean_channels.append(channel)
    if pinned_channel not in clean_channels:
      raise ValueError("pinned_channel must exist in allowed_channels")
    if not isinstance(now_epoch, int) or now_epoch < 0:
      raise ValueError("now_epoch must be a non-negative integer")
    self._load()
    self._state["pinned_channel"] = pinned_channel
    self._state["allow_downgrade"] = 1 if allow_downgrade else 0
    self._state["allowed_channels"] = clean_channels
    self._state["updated_at_epoch"] = now_epoch
    self._save()

  def validate_target(self,
                      current_channel: str,
                      target_channel: str,
                      current_version: int,
                      target_version: int) -> None:
    self._load()
    if current_channel not in ("stable", "beta", "nightly") or target_channel not in (
        "stable", "beta", "nightly"
    ):
      raise ValueError("invalid channel")
    if not isinstance(current_version, int) or not isinstance(target_version, int):
      raise ValueError("version must be integer")
    if current_version < 0 or target_version < 0:
      raise ValueError("version must be non-negative")
    pinned_channel = self._state.get("pinned_channel", "stable")
    allowed_channels = self._state.get("allowed_channels", ["stable", "beta", "nightly"])
    allow_downgrade = int(self._state.get("allow_downgrade", 0))
    if target_channel not in allowed_channels:
      raise ValueError("target channel blocked by policy")
    if target_channel != pinned_channel:
      raise ValueError("target channel violates pinned policy")
    if allow_downgrade == 0 and target_version < current_version:
      raise ValueError("downgrade blocked by release policy")

  def summary_json(self) -> str:
    self._load()
    return json.dumps(self._state, separators=(",", ":"))


def demo() -> int:
  txn = AtomicUpdateTransaction()
  txn.begin("demo-txn", "sha256:demo")
  txn.stage_package("aegis-kernel")
  txn.stage_package("aegis-security-core")
  txn.commit()
  rollback_store = RollbackIndexStore("build/demo/rollback-index.json")
  rollback_store.advance(
      channel="stable",
      candidate_index=1,
      transaction_id=txn.transaction_id,
      manifest_hash=txn.manifest_hash,
      now_epoch=1,
  )
  channel_policy = ReleaseChannelPolicyStore("build/demo/channel-policy.json")
  channel_policy.set_policy("stable", allow_downgrade=False, now_epoch=1)
  channel_policy.validate_target("stable", "stable", 10, 11)
  print(txn.summary_json())
  return 0


if __name__ == "__main__":
  raise SystemExit(demo())
