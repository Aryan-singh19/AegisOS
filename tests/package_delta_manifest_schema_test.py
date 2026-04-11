import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_packages.py"

spec = importlib.util.spec_from_file_location("validate_packages", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackageDeltaManifestSchemaTest(unittest.TestCase):
    def _write_manifest(self, path: Path, lines) -> None:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _base_manifest_lines(self):
        return [
            "schema_version: 1",
            "name: aegis-update-service",
            "version: 0.1.0",
            "summary: update service",
            "license: Apache-2.0",
            "source: userland/",
            "signature_format: placeholder-v1",
            "signature_key_id: aegis-placeholder-core",
            "signature_digest: sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "signature_value: UNSIGNED_PLACEHOLDER",
            "dependencies: []",
        ]

    def test_delta_metadata_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yaml"
            lines = self._base_manifest_lines() + [
                "delta_base_version: 0.0.9",
                "delta_payload_digest: sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "delta_payload_url: https://updates.aegisos.example/delta/update.delta",
                "delta_fallback_full_digest: sha256:2222222222222222222222222222222222222222222222222222222222222222",
            ]
            self._write_manifest(path, lines)
            manifest = module.validate_core_manifest(str(path))
            self.assertEqual(manifest["delta_base_version"], "0.0.9")

    def test_delta_metadata_incomplete_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yaml"
            lines = self._base_manifest_lines() + [
                "delta_base_version: 0.0.9",
                "delta_payload_digest: sha256:1111111111111111111111111111111111111111111111111111111111111111",
            ]
            self._write_manifest(path, lines)
            with self.assertRaises(ValueError):
                module.validate_core_manifest(str(path))

    def test_delta_url_and_digest_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yaml"
            lines = self._base_manifest_lines() + [
                "delta_base_version: 0.0.9",
                "delta_payload_digest: md5:abc",
                "delta_payload_url: ftp://bad",
                "delta_fallback_full_digest: sha256:2222222222222222222222222222222222222222222222222222222222222222",
            ]
            self._write_manifest(path, lines)
            with self.assertRaises(ValueError):
                module.validate_core_manifest(str(path))


if __name__ == "__main__":
    unittest.main()
