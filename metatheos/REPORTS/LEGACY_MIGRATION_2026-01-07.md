# Legacy Migration Report — Goals & Work Items

**Date**: 2026-01-07

## Scope
- One-time migration to align legacy goals/work_items with canonical `work_item` SCHEMAFULL table.
- Ensures every goal has a root `work_item` (level=goal) and migrates legacy items.

## What was implemented
- `migrate_legacy_work_items(dry_run)` Tauri command (manual invocation).
- Root seeding for each goal (status mapping: planned→open, active→active, blocked→blocked, partial→active, done→done).
- Legacy work_items migration with duplicate detection and parent resolution to the goal root.
- Order index normalization and completion timestamp fix for `done` items.
- Validation and warnings in `MigrationReport`.
- Legacy work_item command block marked as legacy only; all writes route through canonical handlers.

## How to run
```
# Dry run (no writes): invoke from Tauri frontend/CLI
invoke("migrate_legacy_work_items", { dryRun: true })

# Execute migration
invoke("migrate_legacy_work_items", { dryRun: false })
```

## MigrationReport fields
- `goals_scanned`
- `root_items_created`
- `legacy_items_migrated`
- `items_skipped`
- `warnings[]`

## Post-conditions
- Each goal has exactly one root `work_item` (parent_id null, level=goal).
- Legacy work_items are copied into canonical storage; no deletions performed.
- Order indices normalized per parent; `completed_at` set when status=done and missing.

## Notes
- Migration is idempotent (duplicate detection by goal_id+title+level+parent_id).
- Legacy write paths are retained only as shims and are explicitly marked "LEGACY — DO NOT USE".
