#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


SCHEMA_VERSION = "1"
SIGNATURE_DEFAULTS = {
    "signature_format": "placeholder-v1",
    "signature_key_id": "aegis-placeholder-migrated",
    "signature_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "signature_value": "UNSIGNED_PLACEHOLDER",
}
CORE_REQUIRED = ["name", "version", "summary", "license", "source", "dependencies"]
PROFILE_REQUIRED = ["profile", "description", "packages"]


def parse_simple_yaml(path):
    data = {}
    order = []
    current_list_key = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            if current_list_key is None:
                raise ValueError(f"{path}: list item without parent key")
            data.setdefault(current_list_key, []).append(stripped[2:].strip())
            continue
        if ":" not in line:
            raise ValueError(f"{path}: invalid line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key not in data:
            order.append(key)
        if value == "":
            current_list_key = key
            data.setdefault(key, [])
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if inner == "":
                data[key] = []
            else:
                data[key] = [item.strip() for item in inner.split(",") if item.strip()]
            current_list_key = None
        else:
            data[key] = value
            current_list_key = None
    return data, order


def dump_simple_yaml(data, order):
    lines = []
    written = set()
    for key in order:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
        written.add(key)
    for key, value in data.items():
        if key in written:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def detect_kind(data):
    if "name" in data and "dependencies" in data:
        return "core"
    if "profile" in data and "packages" in data:
        return "profile"
    return "unknown"


def migrate_doc(data, kind):
    out = dict(data)
    changed = False

    if str(out.get("schema_version", "")).strip() != SCHEMA_VERSION:
        out["schema_version"] = SCHEMA_VERSION
        changed = True

    for k, v in SIGNATURE_DEFAULTS.items():
        if k not in out or not str(out.get(k, "")).strip():
            out[k] = v
            changed = True

    required = CORE_REQUIRED if kind == "core" else PROFILE_REQUIRED
    missing = [k for k in required if k not in out]
    if missing:
        return None, changed, "missing required keys: " + ",".join(missing)

    list_key = "dependencies" if kind == "core" else "packages"
    if not isinstance(out.get(list_key), list):
        return None, changed, f"{list_key} must be a list"
    return out, changed, "ok"


def migrate_file(path, out_dir, dry_run):
    raw, order = parse_simple_yaml(path)
    kind = detect_kind(raw)
    if kind == "unknown":
        return {"file": path.name, "status": "failed", "reason": "unrecognized manifest kind"}

    migrated, changed, reason = migrate_doc(raw, kind)
    if migrated is None:
        return {"file": path.name, "status": "failed", "reason": reason}

    if not dry_run:
        out_text = dump_simple_yaml(migrated, order)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_dir.joinpath(path.name).write_text(out_text, encoding="utf-8", newline="\n")
    return {
        "file": path.name,
        "kind": kind,
        "status": "migrated" if changed else "already_current",
        "reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description="Migrate package/profile YAML manifests to current schema.")
    parser.add_argument("--input-dir", required=True, help="Directory containing .yaml manifests")
    parser.add_argument("--output-dir", required=True, help="Output directory for migrated manifests")
    parser.add_argument("--summary-json", help="Optional JSON summary output path")
    parser.add_argument("--dry-run", action="store_true", help="Plan migration without writing files")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    files = sorted(input_dir.glob("*.yaml"))
    summary = {
        "total": len(files),
        "migrated": 0,
        "already_current": 0,
        "failed": 0,
        "dry_run": 1 if args.dry_run else 0,
        "results": [],
    }

    for path in files:
        try:
            result = migrate_file(path, output_dir, args.dry_run)
        except Exception as exc:
            result = {"file": path.name, "status": "failed", "reason": str(exc)}
        summary[result["status"]] += 1
        summary["results"].append(result)

    print(
        f"total={summary['total']} migrated={summary['migrated']} "
        f"already_current={summary['already_current']} failed={summary['failed']}"
    )
    if args.summary_json:
        Path(args.summary_json).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 2 if summary["failed"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
