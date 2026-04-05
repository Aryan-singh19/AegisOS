import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate_package_manifests.py"


class MigratePackageManifestsTest(unittest.TestCase):
    def test_migrate_legacy_core_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inp = base / "in"
            out = base / "out"
            summary = base / "summary.json"
            inp.mkdir()
            inp.joinpath("kernel.yaml").write_text(
                "\n".join(
                    [
                        "name: aegis-kernel",
                        "version: 0.0.1",
                        "summary: kernel",
                        "license: Apache-2.0",
                        "source: kernel/",
                        "dependencies: []",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            rc = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--input-dir",
                    str(inp),
                    "--output-dir",
                    str(out),
                    "--summary-json",
                    str(summary),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertEqual(rc, 0)
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["migrated"], 1)
            rendered = (out / "kernel.yaml").read_text(encoding="utf-8")
            self.assertIn("schema_version: 1", rendered)
            self.assertIn("signature_format: placeholder-v1", rendered)
            self.assertIn("signature_value: UNSIGNED_PLACEHOLDER", rendered)

    def test_already_current_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inp = base / "in"
            out = base / "out"
            summary = base / "summary.json"
            inp.mkdir()
            inp.joinpath("desktop.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        "profile: desktop",
                        "description: Desktop profile",
                        "signature_format: placeholder-v1",
                        "signature_key_id: aegis-placeholder-profile",
                        "signature_digest: sha256:0000000000000000000000000000000000000000000000000000000000000000",
                        "signature_value: UNSIGNED_PLACEHOLDER",
                        "packages:",
                        "  - aegis-kernel",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            rc = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--input-dir",
                    str(inp),
                    "--output-dir",
                    str(out),
                    "--summary-json",
                    str(summary),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertEqual(rc, 0)
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["already_current"], 1)

    def test_invalid_manifest_kind_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            inp = base / "in"
            out = base / "out"
            inp.mkdir()
            inp.joinpath("bad.yaml").write_text("schema_version: 1\nfoo: bar\n", encoding="utf-8")
            rc = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "--input-dir",
                    str(inp),
                    "--output-dir",
                    str(out),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            ).returncode
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
