# scripts

Helper scripts for local development and automation live here.

- `migrate_policies_batch.py`: batch-migrates legacy sandbox policy JSON files, supports `--dry-run` and per-file `--diff-preview`, emits summary, and returns non-zero exit code when any file fails migration.
- `generate_audit_retention_manifest.py`: emits machine-readable keep/prune chunk manifest and supports `--prev-manifest-json` incremental diff output for retention automation.
