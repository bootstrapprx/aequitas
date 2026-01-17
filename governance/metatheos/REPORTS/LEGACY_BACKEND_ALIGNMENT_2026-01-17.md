# Metatheos Backend Alignment Report

**Date:** 2026-01-17  
**Version:** 0.2.0

---

## Summary

Successfully aligned Metatheos backend with new React UI expectations. The backend now provides dedicated REST endpoints with normalized DTOs, graceful error handling, and a kill-switch for dual-read migration.

---

## Routes (Canonical)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with DB status |
| GET | `/api/context/overview` | Dashboard context (active phase, day, counts, DB health) |
| GET | `/api/phases` | List all phases |
| GET | `/api/phases/:id` | Get single phase |
| GET | `/api/goals` | List goals (`?phase_id=` optional) |
| GET | `/api/goals/:id` | Get single goal |
| GET | `/api/day/today` | Get today's day record |
| GET | `/api/day/:date` | Get day by date (YYYY-MM-DD) |
| GET | `/api/timeline` | Merged events + annotations (`?limit=&phase_id=&goal_id=`) |
| GET | `/api/prompts` | List prompts |
| GET | `/api/audits` | List audits |
| POST | `/api/auth/login` | Login with password |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current auth status |

### Deprecated

| Method | Endpoint | Notes |
|--------|----------|-------|
| POST | `/api/invoke/:command` | Returns `X-Metatheos-Deprecated: invoke-api` header. Logs WARN. |

---

## DTO Contract

DTOs are defined in `metatheos-core/src/dto.rs`. Key types:

- `PhaseDto` - id, title, status (planned/active/closed/archived), dates
- `GoalDto` - id, phase_id, title, status, priority, owner, tags, updated
- `DayDto` - id, phase_id, day_type (light/heavy/review/rest), created_at
- `TimelineItemDto` - kind (event/annotation), ts, id, summary, scope fields
- `ContextOverviewDto` - active_phase, current_day, counts, db status
- `AuthStatusDto` - authenticated, user role
- `ApiErrorDto` - error_code, message

### Enums (Normalized Lowercase)

- `PhaseStatus`: planned, active, closed, archived
- `DayTypeDto`: light, heavy, review, rest
- `GoalStatusDto`: open, active, blocked, partial, done, archived, unknown
- `TimelineKind`: event, annotation

---

## Read Mode Kill-Switch

**Meta key:** `read_mode`

| Value | Behavior |
|-------|----------|
| `canonical_only` | Read only from SCHEMAFULL tables (phase, goal, etc.) |
| `dual_read` (default) | Try canonical first, fallback to legacy (phases, goals, etc.) |
| `legacy_only` | Read only from SCHEMALESS legacy tables |

Mode is logged at startup. Set via: `store.set_meta("read_mode", "canonical_only")`

---

## What Was Fixed

1. **DTO Module Created** - Single source of truth for UI contract in `dto.rs`
2. **API Refactored** - Uses DTOs, added `get_context_overview()` and `get_timeline()` with stable sort
3. **Store Methods Added** - `get_phase_by_id`, `get_goal_by_id`, `get_goals_by_phase`, `get_recent_events`, `get_all_annotations_filtered`, count methods, `get_day`
4. **REST Routes Implemented** - Dedicated endpoints replacing invoke pattern
5. **Auth Stubs** - `METATHEOS_ADMIN_PASSWORD` env-based login
6. **Deprecated Invoke** - Kept with deprecation header and WARN log
7. **CORS Configured** - Cross-origin requests allowed
8. **Graceful Degradation** - Empty results on no-data, structured errors on failure

---

## What Remains Legacy

- `writer/` module (file-based writers) - Not removed, DB is source of truth
- `GovernanceContext::load()` - Deprecated, panics in async context
- Legacy SCHEMALESS tables (`phases`, `goals`, `daily_notes`, etc.) - Kept for migration
- Canon/Protocol scanning from filesystem - Hybrid approach retained

---

## What UI Can Rely On

✅ All `/api/*` endpoints return consistent JSON with `{ data: ... }` wrapper  
✅ Errors return `{ error_code, message }` with appropriate HTTP status  
✅ Timeline is stable-sorted (ts DESC, kind, id) - no flicker  
✅ Empty collections return `[]` not errors  
✅ ISO-8601 dates throughout  
✅ Enum values are lowercase strings  

---

## Known Limitations

1. **Auth is minimal** - Single admin user, password-based, no session persistence
2. **No mutations** - All endpoints are read-only except auth
3. **Dual-read indeterminism** - Until `read_mode` is set to `canonical_only`, data may come from either table
4. **No pagination** - Timeline uses limit only, no cursor/offset

---

## Files Modified

| File | Change |
|------|--------|
| `metatheos-core/src/dto.rs` | **NEW** - DTO module |
| `metatheos-core/src/api.rs` | Refactored to use DTOs |
| `metatheos-core/src/store/mod.rs` | Added new query methods |
| `metatheos-core/src/lib.rs` | Exported DTO module |
| `metatheos-core/Cargo.toml` | Added tracing dependency |
| `metatheos-server/src/main.rs` | Dedicated REST routes |
| `metatheos-server/Cargo.toml` | Added uuid dependency |
