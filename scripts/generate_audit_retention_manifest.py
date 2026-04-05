#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def sink_name(prefix: str, chunk_id: int) -> str:
    return f"{prefix}-{chunk_id:04d}.log"


def build_manifest(prefix: str, latest_chunk_id: int, retention_window_chunks: int):
    if retention_window_chunks <= 0:
        raise ValueError("retention_window_chunks must be > 0")
    keep_from_chunk_id = 0
    if retention_window_chunks <= latest_chunk_id + 1:
        keep_from_chunk_id = latest_chunk_id - retention_window_chunks + 1

    keep_chunk_ids = list(range(keep_from_chunk_id, latest_chunk_id + 1))
    prune_chunk_ids = list(range(0, keep_from_chunk_id))

    return {
        "manifest_schema_version": 1,
        "prefix": prefix,
        "latest_chunk_id": latest_chunk_id,
        "retention_window_chunks": retention_window_chunks,
        "keep_from_chunk_id": keep_from_chunk_id,
        "keep_to_chunk_id": latest_chunk_id,
        "prune_chunk_count": len(prune_chunk_ids),
        "keep_chunk_ids": keep_chunk_ids,
        "prune_chunk_ids": prune_chunk_ids,
        "keep_files": [sink_name(prefix, cid) for cid in keep_chunk_ids],
        "prune_files": [sink_name(prefix, cid) for cid in prune_chunk_ids],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate audit sink retention manifest with keep/prune chunk lists."
    )
    parser.add_argument("--prefix", required=True, help="Audit sink file prefix")
    parser.add_argument("--latest-chunk-id", required=True, type=int, help="Latest chunk id")
    parser.add_argument(
        "--retention-window-chunks",
        required=True,
        type=int,
        help="Number of most recent chunks to retain",
    )
    parser.add_argument("--manifest-json", required=True, help="Output manifest json file path")
    args = parser.parse_args()

    manifest = build_manifest(args.prefix, args.latest_chunk_id, args.retention_window_chunks)
    out_path = Path(args.manifest_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"manifest_schema_version={manifest['manifest_schema_version']} "
        f"keep={len(manifest['keep_chunk_ids'])} prune={manifest['prune_chunk_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
