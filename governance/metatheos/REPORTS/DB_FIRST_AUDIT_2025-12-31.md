# DB-First Architecture Audit Report

**Date**: 2025-12-31
**Scope**: Metatheos v2.0 Codebase Analysis
**Objective**: Assess current state before DB-first pivot

---

## Executive Summary

Metatheos currently operates in a **hybrid markdown+DB mode** with significant architectural inconsistencies:
- **Tokio runtime panic**: Blocking the app from starting
- **Phase loading failure**: No Tauri command to fetch phases
- **Goal hierarchy missing**: No work_item/subgoal/task tree implemented
- **Direct Ollama writes**: No draft gating system
- **Markdown dependency**: Many commands still scan filesystem

**Critical Path**: Fix tokio panic → Implement DB-first schema → Add phase/day/work_item models → Build UI

---

## 1. Current Sources of Truth

### 1.1 Read Paths (Where Data Comes From)

| Entity | Source | Evidence |
|--------|--------|----------|
| **Goals** | DB (hybrid fallback) | `store::get_all_goals()` at store/mod.rs:265 |
| **Phases** | DB (hybrid fallback) | `store::get_all_phases()` at store/mod.rs:350 |
| **Decisions** | DB only | `store::get_all_decisions()` at store/mod.rs:410 |
| **Audits** | DB only | `store::get_all_audits()` at store/mod.rs:430 |
| **Prompts** | DB only | `store::get_all_prompts()` at store/mod.rs:460 |
| **Daily Notes** | DB only | `store::get_all_daily_notes()` at store/mod.rs:480 |
| **Canon** | Filesystem only | `GovernanceScanner::scan_canon()` at governance.rs:301 |
| **Protocols** | Filesystem only | `GovernanceScanner::scan_protocols()` at governance.rs:302 |

### 1.2 Write Paths (Where Data Goes)

| Entity | Markdown Writer | DB Store | Evidence |
|--------|----------------|----------|----------|
| **Goals** | ✅ GoalWriter | ✅ Dual-write | commands_crud.rs:74,163 |
| **Phases** | ✅ PhaseWriter | ✅ Dual-write | commands_crud.rs:252,311 |
| **Audits** | ✅ File write | ✅ Dual-write | commands_crud.rs:465,532 |
| **Prompts** | ✅ File write | ✅ Dual-write | commands_crud.rs:638,708 |
| **Daily Notes** | ✅ DailyWriter | ✅ Dual-write | commands_crud.rs:391,412 |
| **Decisions** | ⚠️ Legacy | ⚠️ Not implemented | N/A |

**Conclusion**: The app is in **transition state**. Dual-write pattern exists but creates complexity. File writers are still called, meaning markdown is still considered authoritative for edits.

---

## 2. Tokio Runtime Panic (CRITICAL BUG)

### 2.1 Root Cause

**Location**: `metatheos-core/src/governance.rs:279-287`

```rust
// PROBLEM: Creates nested runtime
let rt = tokio::runtime::Builder::new_current_thread()
    .enable_all()
    .build()
    .map_err(|e| crate::errors::MetaError::SystemError(format!("Runtime error: {}", e)))?;

rt.block_on(async {  // ← PANIC HERE when called from async context
    let store = crate::store::SurrealStore::init(db_path).await?;
    Self::from_store(&store, root_path).await
})
```

### 2.2 Call Chain

```
Tauri Command (async)
  → GovernanceContext::load() [SYNC]
    → Runtime::new() + block_on() [PANIC]
```

**Examples**:
- `commands.rs:427`: `get_all_goals` → `GovernanceContext::load()`
- `commands.rs:442`: `get_enriched_goals` → `GovernanceContext::load()`
- `commands.rs:595-1636`: 15+ other commands call `::load()`

### 2.3 Impact

**App cannot start**. Any Tauri command calling `GovernanceContext::load()` will panic with:
```
"Cannot start a runtime from within a runtime"
```

### 2.4 Solution Required

**Option A** (Recommended): Make `GovernanceContext::load()` async
```rust
pub async fn load(root: impl AsRef<Path>) -> Result<Self> {
    let root_path = root.as_ref().to_path_buf();
    let db_path = root_path.join(".metatheos.db");

    let store = crate::store::SurrealStore::init(db_path).await?;
    Self::from_store(&store, root_path).await
}
```

Then update all Tauri commands to be async and await `::load()`.

**Option B**: Use `tauri::async_runtime::spawn()` wrapper (more complex, less clean)

---

## 3. Current SurrealDB Schema

### 3.1 Tables Defined

**Location**: `metatheos-core/src/store/mod.rs:26-48`

| Table | Schema Type | Fields Defined | Record ID Format |
|-------|-------------|----------------|------------------|
| `daily_notes` | SCHEMALESS | date, content | `"YYYY-MM-DD"` |
| `goals` | SCHEMALESS | (all dynamic) | `goal_id` string |
| `phases` | SCHEMALESS | (all dynamic) | `phase_id` string |
| `decisions` | SCHEMALESS | (all dynamic) | `decision_id` string |
| `audits` | SCHEMALESS | (all dynamic) | title slug |
| `prompts` | SCHEMALESS | (all dynamic) | prompt_id string |

**Note**: SCHEMALESS allows flexible frontmatter storage but provides no validation.

### 3.2 Missing Tables (Required for DB-First)

| Table | Purpose | Why Needed |
|-------|---------|------------|
| `work_item` | Subgoals/tasks/subtasks | Goal hierarchy not implemented |
| `day` | Day records | No "Begin Day" workflow |
| `day_log` | Daily notes/divergences | Structured logging missing |
| `annotation` | Universal notes/evidence | Not implemented |
| `event` | Audit trail | No mutation tracking |
| `ai_run` | Ollama run history | No draft gating |
| `prompt_template` | Curated prompts | Hardcoded in code |
| `meta` | Settings/active_phase | No app-level state |

### 3.3 Actual DB Contents

**Location**: `~/.metatheos.db` or `governance/.metatheos.db`

**Status**: Cannot inspect without running app (blocked by panic).

**Assumption**: Likely empty or has minimal seed data from previous runs.

---

## 4. UI Gaps

### 4.1 Phase Selector Missing

**Problem**: No Tauri command to fetch phases for UI dropdowns.

**Evidence**:
- Searched for `fn get_phases`, `fn get_all_phases` in `metatheos-gui` → **0 results**
- Frontend has no phase selector component
- Dashboard shows phase but doesn't allow selection

**Required**:
```rust
#[tauri::command]
async fn get_all_phases(state: State<'_, AppState>) -> Result<Vec<Phase>, String> {
    // Fetch from DB
}
```

### 4.2 Goal Page Status

**Location**: `metatheos-gui/src/lib/GoalExplorer.svelte`

**What Exists**:
- List view of all goals
- Filter by status
- Status update dropdown
- Dependencies visualization

**What's Missing**:
- ❌ Individual goal detail page (no `/goals/:id` route)
- ❌ Work item tree (subgoals/tasks/subtasks)
- ❌ Add work item modal
- ❌ Annotations panel
- ❌ Scoped audits
- ❌ AI context actions

**Conclusion**: Only a **list view** exists. No detail page with hierarchy management.

### 4.3 Begin Day Wizard

**Status**: **Not implemented**

**Evidence**: Searched for "Begin Day", "start day", "day wizard" → 0 results

**What's Needed**:
1. Route: `/begin-day`
2. Steps:
   - Choose day_type (light/heavy/review/ad-hoc)
   - Choose phase
   - Choose goals (filtered by phase)
   - Create day record
3. Validation:
   - Heavy day MUST have exactly 2 goals
   - Goals must belong to selected phase

### 4.4 Broken Links Table

| UI Expectation | Backend/DB Path | Status |
|----------------|-----------------|--------|
| Phase selector shows phases | `get_all_phases` Tauri command | ❌ Missing |
| Begin Day wizard | Route + multi-step component | ❌ Missing |
| Goal detail page | `/goals/:id` route + component | ❌ Missing |
| Work item tree | `work_item` table + CRUD commands | ❌ Missing |
| Day record | `day` table + CRUD commands | ❌ Missing |
| Day logs panel | `day_log` table + CRUD commands | ❌ Missing |
| Annotations | `annotation` table + CRUD commands | ❌ Missing |
| Event audit trail | `event` table + auto-logging | ❌ Missing |
| AI draft preview | `ai_run` table + apply flow | ❌ Missing |
| Ollama settings | Settings page + `meta:settings` | ❌ Missing |

---

## 5. Ollama Integration Status

### 5.1 Port Configuration

**Status**: ✅ **CORRECT** (Port 11435)

**Evidence**:
- `llm/runtime.rs:33`: Default `http://127.0.0.1:11435`
- `llm/client.rs:112,123`: Uses 11435
- `Assistant.svelte:260`: Displays 11435

**Why 11435?**
- Main Aequitas app uses 11434
- Meta Engine (Metatheos) uses 11435
- Avoids port conflicts

### 5.2 Model Selection

**Current Default**: `qwen2.5:7b-instruct` (from runtime.rs)

**Problem**: 7b model may be heavy for i5-1145G7 CPU with 16GB RAM.

**Recommendation**: Switch to lighter model
- `qwen2.5:3b-instruct` (preferred)
- `llama3.2:3b-instruct` (alternative)

**Missing**: Model picker UI that calls `/api/tags`

### 5.3 Error Surfacing

**Current**: Errors logged to console, some shown in UI

**Evidence**: `Assistant.svelte` shows error messages from Ollama failures

**Gap**: No structured error handling for:
- Model not found
- Server unreachable
- Invalid JSON response

### 5.4 Direct Write Risk

**Problem**: Ollama can potentially write directly via commands.

**Evidence**: No draft gating layer found. AI responses can trigger mutations.

**Required**:
1. All AI outputs go to `ai_run` table
2. UI shows draft preview
3. User clicks "Apply Draft" to commit
4. ID validation before apply

---

## 6. File Watcher Confusion

**Status**: File watcher exists from Phase 2 but conflicts with DB-first approach.

**Evidence**:
- `metatheos-core/src/watcher/mod.rs`: Watches markdown files
- `watcher_handler.rs`: Re-parses markdown on change → updates DB
- Purpose: Keep DB in sync with external edits

**Problem for DB-First**:
- If DB is canonical, file watcher is unnecessary
- Causes confusion about source of truth
- Adds complexity

**Recommendation**:
- **Disable file watcher** for DB-first mode
- Make markdown **export-only** (one-way: DB → markdown)
- Or: Keep watcher but mark markdown as read-only backup

---

## 7. Dependency Graph

### Current Architecture

```
┌─────────────────────────────────────────────────┐
│          Tauri Commands (src-tauri)             │
│   ┌───────────────────────────────────────┐    │
│   │  GovernanceContext::load()            │    │
│   │  ↓                                     │    │
│   │  Runtime::new() + block_on() ← PANIC  │    │
│   └───────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          metatheos-core (library)               │
│                                                 │
│  ┌──────────────┐    ┌──────────────┐         │
│  │ GoalWriter   │    │ SurrealStore │         │
│  │ PhaseWriter  │    │ (DB ops)     │         │
│  │ DailyWriter  │    │              │         │
│  └──────────────┘    └──────────────┘         │
│         ↓                    ↓                 │
│  ┌────────────────────────────────────┐       │
│  │  Dual-Write Pattern (Phase 1)      │       │
│  │  1. Write markdown                 │       │
│  │  2. Update DB cache (async)        │       │
│  └────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          File System & Database                 │
│                                                 │
│  governance/                 ~/.metatheos.db   │
│  ├── 02_PHASES/             ├── goals          │
│  ├── 03_GOALS_EPICS/        ├── phases         │
│  ├── 04_DECISIONS/          ├── decisions      │
│  ├── 05_AUDITS/             ├── audits         │
│  ├── 06_PROMPTS/            ├── prompts        │
│  └── docs/canonical/        └── daily_notes    │
└─────────────────────────────────────────────────┘
```

### Required Architecture (DB-First)

```
┌─────────────────────────────────────────────────┐
│          Svelte UI (metatheos-gui/src)          │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐           │
│  │ Begin Day    │  │ Goal Detail  │           │
│  │ Wizard       │  │ + Work Tree  │           │
│  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│       Tauri Commands (async, no panic)          │
│                                                 │
│  get_phases(), get_goals(), create_work_item() │
│  begin_day(), apply_ai_draft()                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          metatheos-core (async library)         │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ SurrealStore (canonical source of truth) │  │
│  │                                           │  │
│  │ Tables:                                   │  │
│  │ - phase, goal, work_item                 │  │
│  │ - day, day_log                           │  │
│  │ - annotation, event, ai_run              │  │
│  │ - audit, prompt_template, meta           │  │
│  └──────────────────────────────────────────┘  │
│                    ↓                            │
│  ┌──────────────────────────────────────────┐  │
│  │ Event Logger (all mutations tracked)     │  │
│  └──────────────────────────────────────────┘  │
│                    ↓                            │
│  ┌──────────────────────────────────────────┐  │
│  │ ID Validator (pre-display, pre-apply)    │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          SurrealDB (~/.metatheos.db)            │
│                                                 │
│  Canonical state for all governance data       │
│  (Markdown becomes optional export backup)     │
└─────────────────────────────────────────────────┘
```

---

## 8. Code Locations Summary

### Critical Files to Modify

| File | Line | Issue | Fix Required |
|------|------|-------|--------------|
| `governance.rs` | 279-287 | Tokio panic | Make `load()` async |
| `commands.rs` | 427+ | Calls sync `::load()` | Make commands async |
| `commands_crud.rs` | 74+ | Calls sync `::load()` | Make commands async |
| `commands_ai.rs` | 125+ | Calls sync `::load()` | Make commands async |
| `store/mod.rs` | 26-50 | Schema incomplete | Add missing tables |
| `App.svelte` | N/A | No phase selector | Add phase dropdown |
| `GoalExplorer.svelte` | N/A | No detail page | Create goal detail route |

### Files to Create

| File | Purpose |
|------|---------|
| `store/schema.rs` | DB schema definitions |
| `store/migrate.rs` | Migration system |
| `models/work_item.rs` | Work item struct |
| `models/day.rs` | Day record struct |
| `models/event.rs` | Event log struct |
| `gui/src/routes/BeginDay.svelte` | Day wizard UI |
| `gui/src/routes/GoalDetail.svelte` | Goal page with tree |
| `gui/src/lib/PhaseSelector.svelte` | Phase dropdown |
| `OPERATING_RULES.md` | Safety/authorization rules |

---

## 9. Risk Assessment

### High Risk (Blockers)

- ❌ **Tokio panic**: App cannot start
- ❌ **No phase loading**: Core workflow broken
- ❌ **No work item model**: Goal hierarchy impossible

### Medium Risk (Major Gaps)

- ⚠️ **No Begin Day flow**: Can't scope work
- ⚠️ **No event logging**: No audit trail
- ⚠️ **No AI draft gating**: Safety concern

### Low Risk (Quality Issues)

- ⚠️ **File watcher confusion**: Architectural clarity
- ⚠️ **No model picker**: UX gap
- ⚠️ **SCHEMALESS tables**: No validation

---

## 10. Recommendations

### Immediate (Sprint 1 - Days 1-3)

1. **Fix tokio panic** (4 hours)
   - Make `GovernanceContext::load()` async
   - Update all Tauri commands to async

2. **Implement DB schema** (6 hours)
   - Create `schema.rs` with all tables
   - Add migration system
   - Seed minimal data

3. **Add phase loading** (2 hours)
   - Create `get_all_phases` command
   - Add phase selector UI

### Near-term (Sprint 1 - Days 4-7)

4. **Implement day/work_item models** (8 hours)
   - Create structs + DB methods
   - Add CRUD commands

5. **Build Begin Day wizard** (6 hours)
   - Multi-step Svelte component
   - Validation logic

6. **Create Goal detail page** (8 hours)
   - Route + component
   - Work item tree
   - Add/edit/complete flows

### Follow-up (Sprint 2 - Week 2)

7. **Event logging** (4 hours)
8. **AI draft gating** (6 hours)
9. **Ollama settings page** (4 hours)
10. **ID validation layer** (4 hours)

---

## 11. Acceptance Criteria for DB-First Pivot

✅ **Must Have** (MVP):
- [ ] App starts without tokio panic
- [ ] Phases load in UI selector
- [ ] Begin Day wizard creates day records
- [ ] Goal page shows work item tree
- [ ] All mutations create event records
- [ ] Ollama uses draft+apply pattern
- [ ] Port 11435 confirmed working

⚠️ **Should Have** (Polish):
- [ ] ID validation with warnings
- [ ] Model picker with size warnings
- [ ] Markdown export (DB → files)
- [ ] Factory reset with backup

🔮 **Nice to Have** (Future):
- [ ] Import markdown (files → DB)
- [ ] Conflict detection
- [ ] Dependency graph viz

---

## 12. Migration Path

### Phase 1: Foundation (Days 1-3)
- Fix tokio panic
- Implement complete DB schema
- Add migration system
- Seed test data

### Phase 2: Core Workflows (Days 4-7)
- Phase/day/work_item models
- Begin Day wizard
- Goal detail page with tree

### Phase 3: Safety & Intelligence (Days 8-10)
- Event logging
- AI draft gating
- ID validation
- Ollama settings

### Phase 4: Data Migration (Days 11-12)
- Optional markdown import tool
- Export functionality
- Archive old markdown

---

## Appendix A: Search Commands Used

```bash
# Tokio panic search
grep -r "block_on\|Runtime::new" metatheos/

# Phase loading search
grep -r "get_all_phases\|fn get_phases" metatheos-gui/

# Ollama port search
grep -r "11434\|11435\|OLLAMA_HOST" metatheos/

# Goal page search
find metatheos-gui/src -name "*[Gg]oal*"

# Store methods search
grep "get_all_\|save_\|create_" metatheos-core/src/store/mod.rs
```

---

**Audit Complete**: 2025-12-31
**Next Step**: Begin implementation (Commit 1: Runtime panic fix)
**Estimated Total Effort**: 60-80 hours for complete DB-first pivot
