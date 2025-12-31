# SurrealDB Migration Plan

**Status:** DEFERRED (Phase 4+)
**Related:** PERSISTENCE_STRATEGY.md
**Last Updated:** 2025-12-31

---

## Overview

This document describes the **future migration** to SurrealDB as a read-only caching layer for metatheos.

**Current State (Phase 1-3):** Markdown files are the sole source of truth.

**Future State (Phase 4+):** SurrealDB acts as a read-only performance cache, with markdown remaining the write source.

---

## Architecture Design

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                     WRITE PATH                          │
│                                                         │
│  User Edit (GUI/CLI)                                   │
│         │                                               │
│         ├──> Validation (metatheos-core)               │
│         │                                               │
│         └──> Write to Markdown File (governance/)      │
│                     │                                   │
│                     ├──> Git Commit (audit trail)      │
│                     │                                   │
│                     └──> Invalidate SurrealDB Cache    │
│                            (trigger re-index)           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     READ PATH                           │
│                                                         │
│  User Query (GUI Dashboard, AI Reasoning)              │
│         │                                               │
│         ├──> Check SurrealDB Cache                     │
│         │         │                                     │
│         │         ├─ Hit? Return cached data           │
│         │         │                                     │
│         │         └─ Miss? Read from Markdown          │
│         │                    │                          │
│         │                    ├──> Parse & Validate     │
│         │                    │                          │
│         │                    └──> Update Cache          │
│         │                                               │
│         └──> Return Data to User                       │
└─────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Markdown = Source of Truth** (always)
2. **SurrealDB = Read Cache** (never authoritative)
3. **Write-Through Invalidation** (file change → cache invalidation)
4. **Rebuild on Startup** (load markdown → populate cache)
5. **Graceful Degradation** (if DB fails, fall back to markdown parsing)

---

## Schema Design

### Tables

#### `goals`
```sql
DEFINE TABLE goals SCHEMALESS;
DEFINE INDEX goal_id_idx ON TABLE goals COLUMNS goal_id;
DEFINE INDEX status_idx ON TABLE goals COLUMNS status;
DEFINE INDEX phase_idx ON TABLE goals COLUMNS phase;
```

**Fields** (from markdown frontmatter):
- `goal_id`: String (primary, indexed)
- `status`: String (indexed)
- `phase`: Option<String> (indexed)
- `title`: String
- `owner`: Option<String>
- `parent_id`: Option<String>
- `dependencies`: Vec<String>
- `canon`: Vec<String>
- `tags`: Vec<String>
- `updated`: Option<String>
- `file_path`: String (for cache invalidation)
- `file_hash`: String (MD5 of file content for change detection)

#### `daily_notes`
```sql
DEFINE TABLE daily_notes SCHEMALESS;
DEFINE INDEX date_idx ON TABLE daily_notes COLUMNS date;
```

**Fields**:
- `date`: String (YYYY-MM-DD, primary, indexed)
- `phase`: Option<String>
- `goals_worked`: Vec<String>
- `decisions_made`: Vec<String>
- `divergences`: Vec<String>
- `content`: String (full markdown content)
- `file_path`: String
- `file_hash`: String

#### `phases`
```sql
DEFINE TABLE phases SCHEMALESS;
DEFINE INDEX phase_num_idx ON TABLE phases COLUMNS phase_num;
```

**Fields**:
- `phase_num`: u8 (indexed)
- `title`: String
- `status`: String
- `description`: String
- `file_path`: String
- `file_hash`: String

#### `decisions`
```sql
DEFINE TABLE decisions SCHEMALESS;
DEFINE INDEX decision_id_idx ON TABLE decisions COLUMNS decision_id;
```

**Fields**:
- `decision_id`: String (primary, indexed)
- `status`: String
- `date`: String (YYYY-MM-DD)
- `title`: String
- `rationale`: String
- `file_path`: String
- `file_hash`: String

---

## Migration Implementation

### Step 1: Startup Indexing

**When:** On metatheos GUI/CLI startup

**Process:**
1. Check if `.metatheos.db/` exists
2. If not, or if `--rebuild-cache` flag: full rebuild
3. If exists: incremental update (check file hashes)

**Code Location:** `metatheos-core/src/store/indexer.rs`

```rust
pub async fn rebuild_cache(store: &SurrealStore, gov_root: &Path) -> Result<()> {
    // 1. Walk governance/ directory
    // 2. Parse all markdown files
    // 3. Insert into SurrealDB
    // 4. Store file hash for each record
}

pub async fn incremental_update(store: &SurrealStore, gov_root: &Path) -> Result<()> {
    // 1. Walk governance/ directory
    // 2. Check file hash vs DB record
    // 3. If changed: re-parse and update
    // 4. If new: insert
    // 5. If deleted: remove from DB
}
```

### Step 2: File Watcher (Optional)

**When:** Running GUI in development mode

**Process:**
1. Watch `governance/` folder for file changes (using `notify` crate)
2. On change: invalidate specific cache entry
3. Re-index changed file

**Code Location:** `metatheos-gui/src-tauri/src/watcher.rs`

```rust
use notify::{Watcher, RecursiveMode, watcher};

pub fn watch_governance(store: Arc<SurrealStore>, gov_root: PathBuf) {
    let (tx, rx) = channel();
    let mut watcher = watcher(tx, Duration::from_secs(1)).unwrap();
    watcher.watch(&gov_root, RecursiveMode::Recursive).unwrap();

    loop {
        match rx.recv() {
            Ok(event) => {
                // Invalidate cache for changed file
                // Re-index file
            }
            Err(e) => eprintln!("Watch error: {}", e),
        }
    }
}
```

### Step 3: Query Layer

**When:** GUI dashboard, AI reasoning, complex filters

**Process:**
1. Try SurrealDB first (fast)
2. If cache miss or stale: fall back to markdown parsing
3. Update cache after markdown read

**Code Location:** `metatheos-core/src/query/cached_queries.rs`

```rust
pub async fn get_goals_by_status(
    store: Option<&SurrealStore>,
    gov_root: &Path,
    status: GoalStatus
) -> Result<Vec<Goal>> {
    if let Some(db) = store {
        // Try cache first
        if let Ok(goals) = db.query_goals_by_status(status).await {
            if !goals.is_empty() {
                return Ok(goals);
            }
        }
    }

    // Fallback to markdown
    let ctx = GovernanceContext::load(gov_root)?;
    let query = GoalQuery::new(&ctx).with_status(status);
    Ok(query.execute())
}
```

---

## Performance Benefits

**Expected improvements** (for large governance datasets: >1000 goals):

| Operation | Markdown (current) | SurrealDB (future) | Speedup |
|-----------|-------------------|--------------------|---------|
| Load all goals | ~500ms | ~50ms | 10x |
| Filter by status | ~500ms (full scan) | ~5ms (indexed) | 100x |
| Dependency graph | ~1000ms (recursive parse) | ~100ms (graph query) | 10x |
| Dashboard load | ~2000ms (multiple reads) | ~200ms (single query) | 10x |

**Note:** Benefits only matter if governance dataset becomes large. For <100 goals, markdown parsing is fast enough.

---

## Testing Strategy

### Unit Tests
- `store/mod.rs`: Test SurrealDB CRUD operations
- `store/indexer.rs`: Test rebuild and incremental updates
- `store/migration.rs`: Test markdown → DB conversion

### Integration Tests
- Round-trip: Markdown → DB → Query → Verify data integrity
- Cache invalidation: Edit markdown → verify DB updates
- Fallback: Simulate DB failure → verify markdown fallback works

### Performance Tests
- Benchmark: Parse 1000 markdown files vs query from DB
- Measure: Dashboard load time (before/after SurrealDB)

---

## Rollback Plan

If SurrealDB causes issues:

1. **Immediate**: Comment out DB initialization (already done for Phase 1)
2. **Verify**: All workflows fall back to markdown parsing
3. **Debug**: Fix DB issues offline without blocking users
4. **Re-enable**: Only when tests pass and benefits are proven

---

## Open Questions

1. **Cache invalidation timing**: Real-time (file watcher) or on-demand (next read)?
2. **Multi-user**: Does cache need synchronization across multiple GUI instances?
3. **Graph queries**: Do we need SurrealDB's graph features for dependency trees?
4. **Backup strategy**: Should `.metatheos.db/` be gitignored or versioned?

**Recommendation**: `.metatheos.db/` should be gitignored (it's a cache, not source data)

---

## Next Steps (Phase 4)

When ready to activate SurrealDB:

1. Uncomment DB initialization in `main.rs`
2. Uncomment `state.db` field in `state.rs`
3. Implement `store/indexer.rs` (rebuild + incremental update)
4. Add file hash tracking to all parsers
5. Write integration tests (round-trip, cache invalidation)
6. Benchmark performance gains
7. Update documentation

---

**Status:** Design approved, implementation deferred
**Blocked by:** Phase 1 stabilization
**Estimated effort:** 2-3 weeks (when Phase 1 complete)
