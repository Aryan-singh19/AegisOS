import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_audit_retention_manifest.py"


class AuditRetentionManifestTest(unittest.TestCase):
    def test_manifest_keep_and_prune_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            rc = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--prefix",
                    "cap_audit",
                    "--latest-chunk-id",
                    "17",
                    "--retention-window-chunks",
                    "5",
                    "--manifest-json",
                    str(out),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["manifest_schema_version"], 1)
            self.assertEqual(data["keep_from_chunk_id"], 13)
            self.assertEqual(data["keep_to_chunk_id"], 17)
            self.assertEqual(data["prune_chunk_count"], 13)
            self.assertEqual(data["keep_files"][0], "cap_audit-0013.log")
            self.assertEqual(data["prune_files"][-1], "cap_audit-0012.log")

    def test_invalid_retention_window_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            rc = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--prefix",
                    "cap_audit",
                    "--latest-chunk-id",
                    "3",
                    "--retention-window-chunks",
                    "0",
                    "--manifest-json",
                    str(out),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertNotEqual(rc, 0)

    def test_manifest_incremental_diff_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            prev_manifest = base / "prev.json"
            out_manifest = base / "manifest.json"
            prev_manifest.write_text(
                json.dumps(
                    {
                        "manifest_schema_version": 1,
                        "prefix": "cap_audit",
                        "keep_chunk_ids": [10, 11, 12, 13, 14],
                        "prune_chunk_ids": list(range(0, 10)),
                    }
                ),
                encoding="utf-8",
            )
            rc = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--prefix",
                    "cap_audit",
                    "--latest-chunk-id",
                    "17",
                    "--retention-window-chunks",
                    "5",
                    "--prev-manifest-json",
                    str(prev_manifest),
                    "--manifest-json",
                    str(out_manifest),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertEqual(rc, 0)
            data = json.loads(out_manifest.read_text(encoding="utf-8"))
            inc = data["incremental_diff"]
            self.assertEqual(inc["added_keep_chunk_ids"], [15, 16, 17])
            self.assertEqual(inc["removed_keep_chunk_ids"], [10, 11, 12])
            self.assertEqual(inc["added_prune_chunk_ids"], [10, 11, 12])
            self.assertEqual(inc["removed_prune_chunk_ids"], [])


if __name__ == "__main__":
    unittest.main()
