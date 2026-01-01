# Metatheos Architecture

**Version:** 2.0.0
**Status:** Production
**Updated:** 2025-12-31

## Overview

Metatheos is a local-first governance engine built on three architectural principles:

1. **Markdown Authoritative** — Markdown files are the single source of truth
2. **DB Read-Cache** — SurrealDB provides optional high-performance caching
3. **Local-First** — No network, no cloud, no dependencies on external services

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                      │
├───────────────────┬─────────────────────────────────────┤
│   metatheos-cli   │        metatheos-gui (Tauri)        │
│   (Terminal)      │    (Desktop App: Rust + Svelte)     │
└───────────────────┴───────────────┬─────────────────────┘
                                    │
            ┌───────────────────────┴───────────────┐
            │                                       │
            ▼                                       ▼
    ┌────────────────┐                    ┌────────────────┐
    │ metatheos-core │                    │   Tauri        │
    │                │                    │   Commands     │
    │ • Parser       │                    └────────────────┘
    │ • Validator    │                            │
    │ • Domain       │◄───────────────────────────┘
    │ • Query        │
    │ • Writer       │
    │ • Store        │
    └────────┬───────┘
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
┌──────────┐    ┌──────────┐
│Markdown  │    │SurrealDB │
│Files     │    │(Cache)   │
│(Truth)   │    │(Optional)│
└──────────┘    └──────────┘
```

## Persistence Strategy

### Philosophy: Markdown Authoritative, DB Read-Cache

**Core Principle**: Data outlives the tool. Markdown files are canonical.

```
READ PATH:
  User Request
      ↓
  Check SurrealDB cache (if available)
      ↓ (cache miss or disabled)
  Parse markdown files
      ↓
  Return data

WRITE PATH:
  User Request
      ↓
  Validate operation
      ↓
  1. Write to markdown FIRST ✅
      ↓
  2. Async update to SurrealDB cache (non-blocking)
      ↓
  Return success (don't wait for DB)
```

### Dual-Write Pattern

Every write operation follows this pattern:

```rust
// 1. Write to markdown (source of truth)
writer.write_entity(&entity)?;

// 2. Async DB cache update (non-blocking)
if let Some(store) = state.db.lock().unwrap().as_ref() {
    let store = store.clone();
    let entity_clone = entity.clone();
    tauri::async_runtime::spawn(async move {
        let _ = store.get_db()
            .create(("table", id.as_str()))
            .content(entity_clone)
            .await;
    });
}
```

**Key Properties**:
- Markdown write is **synchronous** and **blocking**
- DB update is **asynchronous** and **fire-and-forget**
- Failure to update DB **never** blocks or fails the operation
- External markdown edits are respected (markdown wins)

## Module Structure

### metatheos-core

Core library providing all domain logic and data access.

#### `/src/domain/`
Domain models representing governance entities:
- `goal.rs` — Goal with status, dependencies, phase
- `phase.rs` — Phase with status transitions
- `decision.rs` — Decision records
- `audit.rs` — Audit records
- `daily.rs` — Daily notes
- `prompt.rs` — LLM prompts

#### `/src/parser/`
Markdown parsing layer:
- `markdown.rs` — Main parser (`MarkdownParser`)
- `frontmatter.rs` — YAML frontmatter extraction
- `links.rs` — Wikilink and reference extraction

Handles:
- YAML frontmatter parsing
- Markdown content extraction
- Error recovery for malformed files

#### `/src/writer/`
Markdown generation layer:
- `goal_writer.rs` — Goal CRUD operations
- `phase_writer.rs` — Phase CRUD operations
- `audit_writer.rs` — Audit CRUD operations
- `prompt_writer.rs` — Prompt CRUD operations
- `daily_writer.rs` — Daily note operations
- `frontmatter.rs` — YAML frontmatter serialization

Ensures:
- Atomic writes via temp files
- Frontmatter consistency
- Proper markdown formatting

#### `/src/validator/`
Governance invariant enforcement:
- `goal_validator.rs` — Goal-specific rules
- `invariants.rs` — Cross-entity invariants

Validates:
- Structural requirements (IDs, statuses)
- Logical consistency (dependencies exist)
- Phase coherence
- Canon boundary (read-only enforcement)

#### `/src/query/`
High-level query interface:
- `goal_queries.rs` — Fluent goal filtering API

#### `/src/store/`
SurrealDB integration:
- `mod.rs` — `SurrealStore` implementation
- `migration.rs` — One-time markdown → DB migration

**Tables**:
- `goals` — Goal records
- `phases` — Phase records
- `daily_notes` — Daily note records
- `audits` — Audit records
- `decisions` — Decision records
- `prompts` — Prompt records

#### `/src/governance.rs`
Top-level orchestration:
- `GovernanceContext` — Loads all governance data
- `from_store()` — Load from SurrealDB cache
- `load()` — Load from markdown files

#### `/src/dashboard/`
Dashboard calculation engine:
- `mod.rs` — `AequitasDashboard` and `DashboardCalculator`

Computes:
- Completion metrics (percentage, goal counts)
- Phase status (goals per phase, completion)
- Blockers (goals blocking others)
- Critical path (goals with most reverse dependencies)
- Recent activity (velocity, daily notes)
- Health metrics (orphaned goals, missing dependencies)

### metatheos-cli

Command-line interface built with Clap.

#### `/src/commands/`
- `scan.rs` — Governance audit command
- `goals.rs` — List goals with filtering
- `goal.rs` — Individual goal operations (show, set, deps)
- `today.rs` — Daily note management
- `phase.rs` — Phase information
- `audit.rs` — Audit listing
- `migrate.rs` — Markdown → SurrealDB migration

#### `/src/output/`
- `markdown.rs` — Markdown formatter
- `json.rs` — JSON formatter
- `table.rs` — Table formatter (comfy-table)

### metatheos-gui

Desktop application built with Tauri 2 + Svelte 5.

#### `/src-tauri/src/` (Rust Backend)

**`commands.rs`** — Read-only Tauri commands:
- `get_all_goals()` — Load all goals
- `get_enriched_goals()` — Goals with computed fields
- `get_dashboard_data()` — Dashboard overview
- `get_aequitas_dashboard()` — Aequitas-specific dashboard
- `get_daily_context()` — Daily note context
- `get_governance_tree()` — File browser data

**`commands_crud.rs`** — Write operations:
- Goals: `create_goal`, `update_goal`, `delete_goal`
- Phases: `create_phase`, `update_phase`, `set_active_phase`
- Audits: `create_audit`, `update_audit`, `delete_audit`
- Prompts: `create_prompt`, `update_prompt`, `delete_prompt`
- Daily Notes: `write_daily_note`, `delete_daily_note`

**`state.rs`** — Application state:
- `AppState` — Shared state (governance root, SurrealDB store)

**`main.rs`** — Tauri initialization:
- Command registration
- State initialization
- SurrealDB initialization

#### `/src/` (Svelte Frontend)

**Components**:
- `Dashboard.svelte` — Overview page
- `AequitasDashboard.svelte` — Project completion tracker
- `GoalExplorer.svelte` — Goal browser with filters
- `GoalEditModal.svelte` — Goal editing dialog
- `FileExplorer.svelte` — Governance folder browser
- `AuditViewer.svelte` — Validation results

**Stores** (Svelte 5 Runes):
- Reactive state management with `$state()` runes
- No external store libraries needed

## Data Flow

### Goal Status Update (Example)

```
1. User clicks "Mark as Done" in GUI
       ↓
2. Frontend calls update_goal(goal_id, status: "done")
       ↓
3. Tauri command validates transition (done ← active ✓)
       ↓
4. GoalWriter updates markdown file
       ↓
5. Markdown write completes successfully
       ↓
6. Spawn async task to update SurrealDB
       ↓
7. Return success to frontend (don't wait for DB)
       ↓
8. Frontend shows success toast
       ↓
9. Frontend refreshes goal list
       ↓
10. (Background) SurrealDB update completes
```

**Total latency**: ~10-50ms (markdown write only)
**DB latency**: ~5-20ms (async, doesn't block UI)

## Performance Characteristics

### Filesystem Operations

- **Read (parse)**: 0.5-2ms per goal
- **Write (serialize)**: 1-5ms per goal
- **Scan directory**: 5-20ms for 100 files

### SurrealDB Operations

- **Query (cached)**: 0.1-1ms per goal
- **Insert/Update**: 1-5ms per goal
- **Migration (100 files)**: 200-500ms

### Dashboard Calculation

- **From filesystem**: 50-200ms (100 goals)
- **From SurrealDB**: 10-50ms (100 goals)
- **Speedup**: 5-10x with caching

## Technology Stack

### Core Dependencies

```toml
serde = "1.0"           # Serialization
serde_yaml = "0.9"      # YAML frontmatter
walkdir = "2.5"         # Directory traversal
chrono = "0.4"          # Date/time handling
surrealdb = "2.2"       # Embedded database
```

### CLI Dependencies

```toml
clap = "4.5"            # CLI argument parsing
comfy-table = "7.1"     # Table formatting
tokio = "1.0"           # Async runtime
```

### GUI Dependencies

**Rust** (src-tauri/Cargo.toml):
```toml
tauri = "2.1"           # Desktop framework
```

**TypeScript** (package.json):
```json
"svelte": "^5.0",
"vite": "^6.0",
"tailwindcss": "^3.4",
"d3": "^7.9"
```

## Security Model

### Canon Boundary

Files under `governance/00_MASTER/` and `governance/docs/canonical/` are **read-only**:
- Parser can read canon files
- Writer rejects writes to canon paths
- GUI marks canon files as non-editable
- Validation enforces canon immutability

### Input Validation

- Goal IDs must match `G-XXX` pattern
- Decision IDs must match `D-XXX` pattern
- Status values must be in enum
- Dates must parse as valid ISO 8601
- Dependencies must reference existing goals

### File System Safety

- Writes use atomic temp file → rename pattern
- Backups created before destructive operations
- Archive rather than delete (moves to `90_ARCHIVE/`)

## Error Handling

### Error Types

```rust
pub enum MetaError {
    ParseError(String),     // Malformed markdown
    ValidationError(String), // Invariant violation
    IoError(std::io::Error), // Filesystem failure
    SystemError(String),     // Database/runtime error
}
```

### Recovery Strategies

- **Parse errors**: Skip malformed files, log warnings
- **Validation errors**: Reject operation, return user-friendly message
- **IO errors**: Retry once, then fail with error message
- **DB errors**: Log warning, continue (markdown is truth)

## Testing Strategy

### Unit Tests

- Domain model validation
- Parser edge cases
- Writer output formatting
- Query filtering logic

### Integration Tests

- Full governance folder parsing
- CRUD operations end-to-end
- Migration consistency
- Status transition workflows

### Current Status

As of Phase 1.1:
- ✅ Goal status transition tests passing
- ⏭️ Comprehensive test coverage needed (Phase 3)

## Future Architecture

### Phase 2: Real-Time Sync

```
File Watcher (notify crate)
      ↓
Detect markdown change
      ↓
Re-parse changed file
      ↓
Update SurrealDB cache
      ↓
Emit Tauri event
      ↓
Frontend updates UI
```

### Phase 4: LLM Integration

```
User Query
      ↓
Assemble Context (from governance)
      ↓
Ollama Reasoning (local LLM)
      ↓
Validate against Canon
      ↓
Log Prompt + Response
      ↓
Return governed answer
```

## Design Decisions

### Why Markdown?

- **Human-readable**: Can edit with any text editor
- **Version control**: Works seamlessly with git
- **Portable**: No vendor lock-in or binary formats
- **Future-proof**: Markdown will outlive Metatheos

### Why SurrealDB?

- **Embedded**: No separate server process needed
- **Multi-model**: Graph queries for dependencies
- **ACID**: Transactional guarantees
- **Rust-native**: Excellent SDK integration

### Why Tauri?

- **Rust backend**: Share code with CLI
- **Small binaries**: <15MB for full app
- **Native performance**: No Electron overhead
- **Cross-platform**: Linux, macOS, Windows

### Why Svelte 5?

- **No virtual DOM**: Fast, direct updates
- **Runes**: Simpler reactivity than stores
- **Small runtime**: <5KB overhead
- **TypeScript**: Full type safety

## Migration Notes

### From v1.x to v2.0

v2.0 introduces SurrealDB caching but maintains full backward compatibility with v1.x markdown files.

**Breaking Changes**: None

**New Features**:
- SurrealDB read-cache (optional)
- Dual-write persistence
- Aequitas dashboard

**Migration Path**:
```bash
# Delete old DB (if exists)
rm -rf governance/.metatheos.db

# Rebuild cache
metatheos migrate
```

---

**Last Updated**: 2025-12-31
**Next Review**: Phase 2 (File Watcher Implementation)
