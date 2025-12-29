---
type: phase
phase_id: "P2"
status: done
depends_on: []
owner: you
updated: 2025-12-28


## What it means
- Account mapping between company charts and master chart, plus API contracts.

## Status
- ✅ Done

## What's Done
- Account mapping system: Company accounts → Master Chart
- AI-powered mapping suggestions with confidence scoring
- Manual mapping confirmation/rejection workflow
- Semantic search with pgvector embeddings (optional)
- Mapping statistics and coverage tracking
- API contracts: Pydantic schemas in backend, TypeScript types in frontend
- QuickBooks Online integration: OAuth, account import, staging pipeline
- Integration jobs and normalization audit trail
- UI: Mapping interface with auto-mapping capability
- `/chartofaccounts/mapping` page with master-to-company visualization

## What's Missing
- Full TypeScript type generation from Pydantic (currently manual)
- Additional integration sources beyond QuickBooks

## Goals
- [[GOAL — Integrations foundation]] (partial)
