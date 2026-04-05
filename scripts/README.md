# scripts

Helper scripts for local development and automation live here.

- `migrate_policies_batch.py`: batch-migrates legacy sandbox policy JSON files, supports `--dry-run`, per-file `--diff-preview`, include/exclude filters, and shard execution mode for large rollouts.
- `generate_audit_retention_manifest.py`: emits machine-readable keep/prune chunk manifest and supports `--prev-manifest-json` incremental diff output for retention automation.
