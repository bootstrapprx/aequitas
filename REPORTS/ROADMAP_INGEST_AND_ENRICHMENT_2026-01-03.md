# Roadmap Ingest & Enrichment (2026-01-03)

## What Was Ingested
- Parsed `governance/aequitas_roadmap.md` into canonical DB tables (`phase`, `goal`) with deterministic IDs and ordering (P0–P9).
- Added per-phase goals derived from “What exists” bullets with open status to keep them actionable.
- Logged ingestion origin in phase descriptions (`created_from: roadmap_ingest`) and via event payload.

## Learning Enrichment Added
- Per-phase annotations (type-tagged in content) for:
  - learning_objectives
  - concepts_to_study
  - prerequisites
  - why_this_is_hard
  - mental_models
- Goals and annotations are marked as `(enrichment)` to distinguish them from operational data.

## Event Logged
- `event` record with `payload.type = roadmap_ingested_and_enriched`, `source = aequitas_roadmap.md`, `philosophy = learning-first` to capture the one-time ingest.

## How to Run
- Tauri command: `ingest_roadmap` (idempotent). Re-runs update phases/goals and only append missing annotations; event logs once.

## Verification Checklist
- Phases `P0..P9` exist in `phase` table with correct titles/order.
- Goals `G-P{N}-XX` exist under matching `phase_id` with status `open`.
- `annotation` table contains per-phase learning/mental-model entries.
- `event` table contains the single roadmap ingestion event (no duplicates on re-run).

## Ambiguities / Notes
- Goal descriptions are synthesized from the roadmap “What exists” bullets to keep scope aligned; refine text if future roadmap updates add more detail.
- `order_index` for goals is encoded via tags (`order:NN`) because the canonical goal schema does not currently include an order field.
