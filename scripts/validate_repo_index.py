#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_simple_yaml(path):
  data = {}
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
  return data


def validate_signature_fields(item, key_prefix, sig_format, where):
  for field in ["signature_format", "signature_key_id", "signature_digest", "signature_value"]:
    if field not in item or not str(item[field]).strip():
      raise ValueError(f"{where}: missing {field}")
  if item["signature_format"] != sig_format:
    raise ValueError(f"{where}: signature_format mismatch")
  if not str(item["signature_key_id"]).startswith(key_prefix):
    raise ValueError(f"{where}: signature_key_id must start with {key_prefix}")
  if not str(item["signature_digest"]).startswith("sha256:"):
    raise ValueError(f"{where}: signature_digest must start with sha256:")


def validate_index(index_path):
  payload = json.loads(Path(index_path).read_text(encoding="utf-8"))
  if int(payload.get("schema_version", 0)) != 1:
    raise ValueError("repository index schema_version must be 1")
  if "repository" not in payload or "generated_at" not in payload:
    raise ValueError("repository index missing repository/generated_at")
  policy = payload.get("signing_policy", {})
  key_prefix = policy.get("required_key_id_prefix", "aegis-placeholder-")
  sig_format = policy.get("required_signature_format", "placeholder-v1")
  packages = payload.get("packages", [])
  if not isinstance(packages, list) or not packages:
    raise ValueError("repository index must contain packages list")

  seen = set()
  for i, item in enumerate(packages):
    where = f"packages[{i}]"
    for field in ["name", "version", "manifest_path"]:
      if field not in item or not str(item[field]).strip():
        raise ValueError(f"{where}: missing {field}")
    validate_signature_fields(item, key_prefix, sig_format, where)
    key = (item["name"], item["version"])
    if key in seen:
      raise ValueError(f"{where}: duplicate name/version entry")
    seen.add(key)
    manifest_path = ROOT / str(item["manifest_path"])
    if not manifest_path.exists():
      raise ValueError(f"{where}: manifest_path not found: {manifest_path}")
    manifest = parse_simple_yaml(manifest_path)
    if manifest.get("name") != item["name"] or manifest.get("version") != item["version"]:
      raise ValueError(f"{where}: manifest name/version mismatch")
    validate_signature_fields(manifest, key_prefix, sig_format, f"{where}:manifest")
  return len(packages)


def main():
  parser = argparse.ArgumentParser(description="Validate repository index trust policy and signatures.")
  parser.add_argument(
      "--index-json",
      default=str(ROOT / "packages" / "repository-index.json"),
      help="Path to repository index json",
  )
  args = parser.parse_args()
  count = validate_index(args.index_json)
  print(f"Validated repository index entries: {count}")
  return 0


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except (ValueError, json.JSONDecodeError) as exc:
    print(f"Validation failed: {exc}")
    raise SystemExit(1)
