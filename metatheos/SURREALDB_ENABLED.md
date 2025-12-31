# SurrealDB Enabled - Phase 1 Critical Infrastructure

**Date:** 2025-12-31
**Status:** ✅ ENABLED (Migration Ready)
**Rationale:** Dashboard requires dynamic, cached data for performance

---

## Strategic Decision

**Original Plan:** Defer SurrealDB to Phase 4
**New Plan:** Enable SurrealDB NOW as critical caching layer for Phase 1

**Reason:**
- Dashboard calculator recalculates from 59 markdown files on every request
- No caching = performance bottleneck as data grows
- SurrealDB provides indexed queries for fast dashboard metrics

---

## Architecture

```
Markdown Files (source of truth)
      ↓
  Migration
      ↓
SurrealDB (read-only cache)
      ↓
  Fast Queries
      ↓
Dashboard (dynamic data)
```

**Key Principles:**
1. **Markdown remains source of truth** - never written to by DB
2. **SurrealDB is a performance cache** - populated from markdown
3. **GUI writes markdown** - migration updates DB
4. **File watcher** (Phase 2) - keeps DB synchronized

---

## Implementation Progress

### ✅ Phase 1: Enablement

1. **Fixed Compilation Errors**
   - Added missing `parent_id` and `level` fields to Goal test structs
   - [frontmatter.rs:116-117](metatheos-core/src/writer/frontmatter.rs#L116)
   - [goal_writer.rs:297-298](metatheos-core/src/writer/goal_writer.rs#L297)

2. **Re-enabled SurrealDB Initialization**
   - Uncommented initialization code in [main.rs:34-72](metatheos-gui/src-tauri/src/main.rs#L34)
   - Re-enabled AppState.db field in [state.rs:9](metatheos-gui/src-tauri/src/state.rs#L9)
   - Updated comments to reflect "Phase 1 Critical" status

3. **Updated Migration Code**
   - Fixed directory paths: `03_GOALS` → `03_GOALS_EPICS`
   - Fixed phase source: `00_MASTER` → `02_PHASES`
   - Removed unnecessary parentheses from `.create()` calls
   - [migration.rs](metatheos-core/src/store/migration.rs)

**Migration Coverage:**
- ✅ Daily Notes (01_DAILY/*.md → daily_notes:YYYY-MM-DD)
- ✅ Goals (03_GOALS_EPICS/*.md → goals:G-xxx)
- ✅ Phases (02_PHASES/PHASE*.md → phases:Px)
- ✅ Audits (05_AUDITS/*.md → audits:filename)

---

## Current State

**Build Status:**
```bash
$ cargo build
✓ metatheos-core compiled
✓ metatheos-gui compiled
✓ metatheos-cli compiled
✓ Finished in 1m 09s
```

**Startup Flow:**
1. App launches → SurrealDB initializes at `governance/.metatheos.db/`
2. Migration runs → Parses 59 markdown files → Populates DB tables
3. DB state available → Ready for queries

**On First Launch:**
```
Initializing SurrealDB at "/path/to/governance/.metatheos.db"
Running SurrealDB migration...
Migration complete - DB cache ready
SurrealDB initialized and state updated.
Metatheos GUI started (SurrealDB caching mode)
```

---

## Next Steps

### 🔄 Phase 2: Dashboard Integration

1. **Create SurrealStore Query Methods** (IN PROGRESS)
   - `count_goals_by_status() -> HashMap<GoalStatus, usize>`
   - `get_blocked_goals_with_impact() -> Vec<(Goal, usize)>`
   - `get_goals_by_reverse_deps() -> Vec<(Goal, usize)>`
   - `get_phase_by_id(phase_id) -> Option<Phase>`
   - `count_recent_completions(days: i64) -> usize`

2. **Update DashboardCalculator**
   - Accept `&SurrealStore` instead of `&GovernanceContext`
   - Use DB queries instead of markdown parsing
   - Measure performance improvement

3. **Performance Testing**
   - Benchmark: markdown parsing vs DB queries
   - Measure dashboard load time (target: <100ms)
   - Verify accuracy matches markdown-based calculator

### 📋 Phase 3: File Watcher (Deferred)

- Monitor governance folder for changes
- Re-run migration on file modifications
- Ensure DB stays synchronized with markdown

---

## Files Modified

### Created:
- `SURREALDB_ENABLED.md` (this file)

### Modified:
- [metatheos-gui/src-tauri/src/main.rs](metatheos-gui/src-tauri/src/main.rs#L34-72) - Re-enabled initialization
- [metatheos-gui/src-tauri/src/state.rs](metatheos-gui/src-tauri/src/state.rs#L1-20) - Re-enabled db field
- [metatheos-core/src/store/migration.rs](metatheos-core/src/store/migration.rs#L40-72) - Fixed paths
- [metatheos-core/src/writer/frontmatter.rs](metatheos-core/src/writer/frontmatter.rs#L110-124) - Fixed test
- [metatheos-core/src/writer/goal_writer.rs](metatheos-core/src/writer/goal_writer.rs#L291-305) - Fixed test

---

## Testing Checklist

- [x] Compilation succeeds
- [x] Migration code updated for correct directories
- [ ] Launch app and verify SurrealDB initializes
- [ ] Verify migration populates DB tables
- [ ] Verify dashboard queries work
- [ ] Measure performance improvement

---

**Next:** Implement SurrealStore query methods for dashboard metrics
