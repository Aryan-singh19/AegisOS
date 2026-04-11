import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "atomic_update_txn.py"

spec = importlib.util.spec_from_file_location("atomic_update_txn", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

AtomicUpdateTransaction = module.AtomicUpdateTransaction
TxnState = module.TxnState
RollbackIndexStore = module.RollbackIndexStore
ReleaseChannelPolicyStore = module.ReleaseChannelPolicyStore


class AtomicUpdateTxnTest(unittest.TestCase):
    def test_happy_path_commit(self):
        txn = AtomicUpdateTransaction()
        txn.begin("txn-1", "sha256:abc")
        txn.stage_package("aegis-kernel")
        txn.stage_package("aegis-security-core")
        txn.commit()
        self.assertEqual(txn.state, TxnState.COMMITTED)
        payload = json.loads(txn.summary_json())
        self.assertEqual(payload["state"], "committed")
        self.assertEqual(payload["staged_count"], 2)

    def test_reject_commit_without_stage(self):
        txn = AtomicUpdateTransaction()
        txn.begin("txn-2", "sha256:def")
        with self.assertRaises(ValueError):
            txn.commit()

    def test_rollback_paths(self):
        txn = AtomicUpdateTransaction()
        txn.begin("txn-3", "sha256:ghi")
        txn.stage_package("aegis-kernel")
        txn.rollback("verification_failed")
        self.assertEqual(txn.state, TxnState.ROLLED_BACK)
        self.assertEqual(txn.rollback_reason, "verification_failed")
        txn.reset()
        self.assertEqual(txn.state, TxnState.IDLE)
        with self.assertRaises(ValueError):
            txn.rollback("bad_state")

    def test_resume_from_json(self):
        txn = AtomicUpdateTransaction()
        txn.begin("txn-4", "sha256:jkl")
        txn.stage_package("aegis-kernel")
        txn.stage_package("aegis-security-core")
        snapshot = txn.summary_json()

        resumed = AtomicUpdateTransaction()
        resumed.load_from_json(snapshot)
        self.assertEqual(resumed.state, TxnState.PREPARED)
        self.assertEqual(resumed.transaction_id, "txn-4")
        self.assertEqual(resumed.manifest_hash, "sha256:jkl")
        self.assertEqual(resumed.staged_packages, ["aegis-kernel", "aegis-security-core"])
        resumed.commit()
        self.assertEqual(resumed.state, TxnState.COMMITTED)

    def test_resume_rejects_bad_payload(self):
        txn = AtomicUpdateTransaction()
        with self.assertRaises(ValueError):
            txn.load_from_json('{"schema_version":2,"state":"prepared"}')
        with self.assertRaises(ValueError):
            txn.load_from_json('{"schema_version":1,"state":"prepared","transaction_id":"","manifest_hash":"","staged_packages":[],"rollback_reason":""}')
        with self.assertRaises(ValueError):
            txn.load_from_json('{"schema_version":1,"state":"committed","transaction_id":"txn","manifest_hash":"sha256:x","staged_count":0,"staged_packages":[],"rollback_reason":""}')
        with self.assertRaises(ValueError):
            txn.load_from_json('{"schema_version":1,"state":"prepared","transaction_id":"txn","manifest_hash":"sha256:x","staged_count":2,"staged_packages":["aegis-kernel"],"rollback_reason":""}')
        with self.assertRaises(ValueError):
            txn.load_from_json('{"schema_version":1,"state":"idle","transaction_id":"txn","manifest_hash":"","staged_count":0,"staged_packages":[],"rollback_reason":""}')

    def test_file_roundtrip_and_atomic_save(self):
        txn = AtomicUpdateTransaction()
        txn.begin("txn-file", "sha256:file")
        txn.stage_package("aegis-kernel")
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state" / "txn.json"
            txn.save_to_file(str(state_file))
            raw = state_file.read_text(encoding="utf-8")
            self.assertIn('"checksum":"sha256:', raw)
            resumed = AtomicUpdateTransaction()
            resumed.load_from_file(str(state_file))
            self.assertEqual(resumed.state, TxnState.PREPARED)
            self.assertEqual(resumed.transaction_id, "txn-file")
            self.assertEqual(resumed.staged_packages, ["aegis-kernel"])

    def test_file_helpers_reject_invalid_paths(self):
        txn = AtomicUpdateTransaction()
        with tempfile.TemporaryDirectory() as tmp:
            as_dir = Path(tmp) / "as_dir"
            as_dir.mkdir()
            with self.assertRaises(ValueError):
                txn.save_to_file(str(as_dir))
            with self.assertRaises(ValueError):
                txn.load_from_file(str(as_dir))
            missing = Path(tmp) / "missing.json"
            with self.assertRaises(ValueError):
                txn.load_from_file(str(missing))

    def test_file_checksum_tamper_detection(self):
        txn = AtomicUpdateTransaction()
        txn.begin("txn-file-2", "sha256:file2")
        txn.stage_package("aegis-kernel")
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "txn.json"
            txn.save_to_file(str(state_file))
            data = json.loads(state_file.read_text(encoding="utf-8"))
            data["payload"]["staged_packages"] = ["aegis-kernel", "aegis-extra"]
            state_file.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            with self.assertRaises(ValueError):
                txn.load_from_file(str(state_file))

    def test_rollback_index_monotonic_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx_file = Path(tmp) / "rollback-index.json"
            store = RollbackIndexStore(str(idx_file))
            store.advance(
                channel="stable",
                candidate_index=5,
                transaction_id="txn-1",
                manifest_hash="sha256:a",
                now_epoch=100,
            )
            store.assert_monotonic("stable", 5)
            store.assert_monotonic("stable", 6)
            with self.assertRaises(ValueError):
                store.assert_monotonic("stable", 4)

    def test_rollback_index_channels_are_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx_file = Path(tmp) / "rollback-index.json"
            store = RollbackIndexStore(str(idx_file))
            store.advance("stable", 7, "txn-stable", "sha256:s", 200)
            store.advance("beta", 2, "txn-beta", "sha256:b", 210)
            payload = json.loads(store.summary_json())
            self.assertEqual(payload["channels"]["stable"]["current_index"], 7)
            self.assertEqual(payload["channels"]["beta"]["current_index"], 2)
            with self.assertRaises(ValueError):
                store.assert_monotonic("beta", 1)

    def test_rollback_index_checksum_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx_file = Path(tmp) / "rollback-index.json"
            store = RollbackIndexStore(str(idx_file))
            store.advance("stable", 3, "txn-3", "sha256:c", 300)
            raw = json.loads(idx_file.read_text(encoding="utf-8"))
            raw["payload"]["channels"]["stable"]["current_index"] = 9
            idx_file.write_text(json.dumps(raw, separators=(",", ":")), encoding="utf-8")
            with self.assertRaises(ValueError):
                store.summary_json()

    def test_rollback_index_history_trims_to_128(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx_file = Path(tmp) / "rollback-index.json"
            store = RollbackIndexStore(str(idx_file))
            for i in range(140):
                store.advance("stable", i, f"txn-{i}", f"sha256:{i}", i)
            payload = json.loads(store.summary_json())
            history = payload["channels"]["stable"]["history"]
            self.assertEqual(len(history), 128)
            self.assertEqual(history[0]["index"], 12)
            self.assertEqual(history[-1]["index"], 139)

    def test_release_channel_policy_happy_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_file = Path(tmp) / "channel-policy.json"
            policy = ReleaseChannelPolicyStore(str(policy_file))
            policy.set_policy(
                pinned_channel="stable",
                allow_downgrade=False,
                allowed_channels=["stable", "beta"],
                now_epoch=123,
            )
            policy.validate_target("stable", "stable", 10, 11)
            payload = json.loads(policy.summary_json())
            self.assertEqual(payload["pinned_channel"], "stable")
            self.assertEqual(payload["allow_downgrade"], 0)
            self.assertEqual(payload["allowed_channels"], ["stable", "beta"])

    def test_release_channel_policy_rejects_channel_and_downgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_file = Path(tmp) / "channel-policy.json"
            policy = ReleaseChannelPolicyStore(str(policy_file))
            policy.set_policy(
                pinned_channel="beta",
                allow_downgrade=False,
                allowed_channels=["beta", "nightly"],
                now_epoch=55,
            )
            with self.assertRaises(ValueError):
                policy.validate_target("beta", "stable", 10, 11)
            with self.assertRaises(ValueError):
                policy.validate_target("beta", "beta", 11, 10)
            with self.assertRaises(ValueError):
                policy.validate_target("beta", "nightly", 10, 11)

    def test_release_channel_policy_allows_downgrade_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_file = Path(tmp) / "channel-policy.json"
            policy = ReleaseChannelPolicyStore(str(policy_file))
            policy.set_policy(
                pinned_channel="nightly",
                allow_downgrade=True,
                allowed_channels=["nightly"],
                now_epoch=88,
            )
            policy.validate_target("nightly", "nightly", 15, 10)

    def test_release_channel_policy_checksum_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy_file = Path(tmp) / "channel-policy.json"
            policy = ReleaseChannelPolicyStore(str(policy_file))
            policy.set_policy("stable", False, ["stable"], 1)
            raw = json.loads(policy_file.read_text(encoding="utf-8"))
            raw["payload"]["pinned_channel"] = "nightly"
            policy_file.write_text(json.dumps(raw, separators=(",", ":")), encoding="utf-8")
            with self.assertRaises(ValueError):
                policy.summary_json()


if __name__ == "__main__":
    unittest.main()
