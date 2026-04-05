import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_repo_index.py"
INDEX = ROOT / "packages" / "repository-index.json"


class RepositoryIndexTrustPolicyTest(unittest.TestCase):
    def test_repository_index_valid(self):
        rc = subprocess.run(
            ["python", str(SCRIPT), "--index-json", str(INDEX)],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        ).returncode
        self.assertEqual(rc, 0)

    def test_repository_index_rejects_bad_key_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-index.json"
            payload = json.loads(INDEX.read_text(encoding="utf-8"))
            payload["packages"][0]["signature_key_id"] = "wrong-prefix"
            bad.write_text(json.dumps(payload), encoding="utf-8")
            rc = subprocess.run(
                ["python", str(SCRIPT), "--index-json", str(bad)],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertEqual(rc, 1)

    def test_repository_index_rejects_manifest_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-index.json"
            payload = json.loads(INDEX.read_text(encoding="utf-8"))
            payload["packages"][0]["version"] = "9.9.9"
            bad.write_text(json.dumps(payload), encoding="utf-8")
            rc = subprocess.run(
                ["python", str(SCRIPT), "--index-json", str(bad)],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
