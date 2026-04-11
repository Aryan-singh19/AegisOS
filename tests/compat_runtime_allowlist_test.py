import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compat_runtime_allowlist.py"

spec = importlib.util.spec_from_file_location("compat_runtime_allowlist", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CompatibilityRuntimeAllowlist = module.CompatibilityRuntimeAllowlist


class CompatRuntimeAllowlistTest(unittest.TestCase):
    def test_register_and_allow(self):
        allowlist = CompatibilityRuntimeAllowlist()
        allowlist.register_runtime("win32-compat", [1, 2, 3, 9])
        self.assertTrue(allowlist.check_syscall("win32-compat", 3, 100))
        summary = json.loads(allowlist.summary_json())
        self.assertEqual(summary["runtime_count"], 1)
        self.assertEqual(summary["runtimes"][0]["allows"], 1)

    def test_violation_for_non_allowlisted_syscall(self):
        allowlist = CompatibilityRuntimeAllowlist()
        allowlist.register_runtime("linux-compat", [10, 11])
        self.assertFalse(allowlist.check_syscall("linux-compat", 99, 200))
        violations = json.loads(allowlist.violation_export_json())
        self.assertEqual(violations["count"], 1)
        self.assertEqual(violations["violations"][0]["reason"], "syscall_not_allowlisted")

    def test_violation_for_missing_runtime(self):
        allowlist = CompatibilityRuntimeAllowlist()
        self.assertFalse(allowlist.check_syscall("unknown-runtime", 50, 300))
        violations = json.loads(allowlist.violation_export_json())
        self.assertEqual(violations["count"], 1)
        self.assertEqual(violations["violations"][0]["reason"], "runtime_not_registered")

    def test_mutate_allowlist(self):
        allowlist = CompatibilityRuntimeAllowlist()
        allowlist.register_runtime("android-compat", [5, 6])
        self.assertFalse(allowlist.check_syscall("android-compat", 7, 1))
        allowlist.add_syscall("android-compat", 7)
        self.assertTrue(allowlist.check_syscall("android-compat", 7, 2))
        allowlist.remove_syscall("android-compat", 7)
        self.assertFalse(allowlist.check_syscall("android-compat", 7, 3))

    def test_violation_ring_buffer_limit(self):
        allowlist = CompatibilityRuntimeAllowlist(max_violations=8)
        allowlist.register_runtime("strict-runtime", [1])
        for i in range(20):
            allowlist.check_syscall("strict-runtime", 99, i)
        violations = json.loads(allowlist.violation_export_json())
        self.assertEqual(violations["count"], 8)
        self.assertEqual(violations["violations"][0]["timestamp_epoch"], 12)
        self.assertEqual(violations["violations"][-1]["timestamp_epoch"], 19)

    def test_invalid_registration_inputs(self):
        allowlist = CompatibilityRuntimeAllowlist()
        with self.assertRaises(ValueError):
            allowlist.register_runtime("", [1, 2, 3])
        with self.assertRaises(ValueError):
            allowlist.register_runtime("bad-runtime", [0, 2, 3])
        with self.assertRaises(ValueError):
            allowlist.check_syscall("bad-runtime", -1, 0)


if __name__ == "__main__":
    unittest.main()
