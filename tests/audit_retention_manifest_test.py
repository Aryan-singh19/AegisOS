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


if __name__ == "__main__":
    unittest.main()
