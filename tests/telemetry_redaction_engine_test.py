import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "telemetry_redaction_engine.py"

spec = importlib.util.spec_from_file_location("telemetry_redaction_engine", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TelemetryRedactionEngineTest(unittest.TestCase):
    def test_redact_log_line_patterns(self):
        stats = module.RedactionStats()
        line = "user=alice@example.com ip=10.0.0.5 token=ghp_ABCDEF1234567890 jwt=eyJabcde12345.ABCDEFGHIJ.KLMNOPQRST"
        red = module.redact_log_line(line, stats)
        self.assertIn("[REDACTED_EMAIL]", red)
        self.assertIn("[REDACTED_IP]", red)
        self.assertIn("[REDACTED_TOKEN]", red)
        self.assertIn("[REDACTED_JWT]", red)
        self.assertGreaterEqual(stats.total(), 4)

    def test_redact_metrics_and_sensitive_keys(self):
        payload = {
            "request_count": 10,
            "password": "secret123",
            "nested": {"email": "a@b.com", "note": "contact +919988776655"},
        }
        red, stats = module.redact_metrics_payload(payload)
        self.assertEqual(red["password"], "[REDACTED]")
        self.assertEqual(red["nested"]["email"], "[REDACTED]")
        self.assertIn("[REDACTED_PHONE]", red["nested"]["note"])
        self.assertGreaterEqual(stats.redacted_sensitive_key, 2)

    def test_redact_trace_payload_recursive(self):
        payload = [
            {"span": "db", "attributes": {"ip": "172.16.1.7", "token": "hf_ABCDEF1234567890"}},
            {"span": "api", "message": "billing card 4111 1111 1111 1111"},
        ]
        red, stats = module.redact_trace_payload(payload)
        self.assertEqual(red[0]["attributes"]["ip"], "[REDACTED]")
        self.assertEqual(red[0]["attributes"]["token"], "[REDACTED]")
        self.assertIn("[REDACTED_CARD]", red[1]["message"])
        self.assertGreater(stats.total(), 0)

    def test_bundle_redaction_summary(self):
        bundle = {
            "logs": [
                "email one@test.com",
                "token sk-ABCDEFGH12345678 ip 8.8.8.8",
            ],
            "metrics": {"authorization": "Bearer abc", "region": "us"},
            "traces": [{"attrs": {"phone": "9876543210"}}],
        }
        out = module.redact_telemetry_bundle(bundle)
        self.assertEqual(out["schema_version"], 1)
        self.assertEqual(out["metrics"]["authorization"], "[REDACTED]")
        self.assertEqual(out["traces"][0]["attrs"]["phone"], "[REDACTED]")
        self.assertGreater(out["redaction_summary"]["total_redactions"], 0)

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "in.json"
            out = Path(tmp) / "out.json"
            inp.write_text(
                json.dumps(
                    {
                        "logs": ["mail me at shiroonigami23@gmail.com"],
                        "metrics": {"api_key": "abc"},
                        "traces": [],
                    }
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["python", str(SCRIPT), "--input", str(inp), "--output", str(out)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=True,
            )
            summary = json.loads(proc.stdout.strip())
            self.assertGreater(summary["total_redactions"], 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("[REDACTED_EMAIL]", payload["logs"][0])
            self.assertEqual(payload["metrics"]["api_key"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
