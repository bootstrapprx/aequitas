# Metatheos Optimization Plan

**Version:** 0.4.0 (Optimization Phase)
**Date:** 2025-12-31
**Status:** Draft

---

## Core Mission Alignment

**Metatheos exists to:**

1. **Finish Aequitas** ← Primary objective
2. **Leave a Trace** ← Governance, decisions, audit trail
3. **Continue Evolution** ← Ongoing assistance and upgrades after Aequitas ships

Everything else is secondary to these three pillars.

---

## Current State Assessment

### What Works ✅

- **Core Domain Models**: Goal, Decision, Phase, DailyNote, Audit, Prompt
- **Parser & Validator**: Frontmatter parsing, governance invariants checking
- **CLI Commands**: `meta audit`, `meta goals`, `meta today`, `meta phase`
- **Basic GUI**: Dashboard, Goal Explorer, Audit Viewer (read-only mostly functional)
- **Tauri Bridge**: 46 commands defined across CRUD, AI, and Git operations

### What's Disconnected 🔴

Based on user confirmation and codebase analysis:

1. **LLM/AI Reasoning Integration**
   - `reasoner/` module exists (engine, ingestion, intent, materializer, validation)
   - `llm/` module exists (Claude, Ollama clients, context builder, logger)
   - **Problem**: Not fully wired to GUI workflows or CLI commands
   - **Impact**: AI-assisted governance features are non-functional

2. **SurrealDB Persistence**
   - Database schema defined (`store/mod.rs`)
   - Tables: `daily_notes`, `goals` (SCHEMALESS)
   - **Problem**: Migration from markdown → SurrealDB incomplete
   - **Impact**: System still relies on markdown files; DB layer unused
   - **Risk**: Dual state management (markdown + DB) leads to inconsistency

3. **Git Integration Commands**
   - Commands exist: `get_governance_git_status`, `commit_governance_changes`, `get_file_history`
   - **Problem**: May not be fully tested or integrated into workflows
   - **Impact**: "Leave a Trace" objective compromised if git tracking unreliable

4. **GUI Component Data Flows**
   - Components exist: `Assistant.svelte`, `GoalEditor.svelte`, `PhaseEditor.svelte`, `DailyEditor.svelte`
   - **Problem**: Some components may not have proper two-way data binding with backend
   - **Impact**: User edits may not persist or UI may show stale data

### Information Fragmentation 📚

**Scattered Documentation** (User wants consolidated):
- `README.md` (9,275 bytes)
- `AI_SETUP_GUIDE.md` (9,482 bytes)
- `IMPLEMENTATION.md` (10,590 bytes)
- `OLLAMA_SETUP.md` (7,389 bytes)
- `OLLAMA_PRIVATE_GPT_ARCHITECTURE.md` (11,187 bytes)
- `GOVERNANCE_INTERFACE_COMPLETE.md` (13,691 bytes)
- `INTERACTIVE_FEATURES.md` (12,708 bytes)
- `INFORMATION_ENRICHMENT.md` (9,821 bytes)
- `ICONS_SETUP.md` (11,450 bytes)
- `FOLDER_CLEANUP.md` (8,314 bytes)

**Total**: ~104 KB of docs across 10+ files
**Problem**: No single source of truth, information duplicated/outdated
**Impact**: Hard to onboard, unclear system state

---

## Optimization Strategy

### Phase 1: Stabilize Core (Priority: HIGH)

**Objective**: Make existing goal/phase/daily workflows rock-solid

#### 1.1 Markdown-First Persistence (Immediate)
- **Decision**: Keep markdown as primary source of truth for now
- **Action**: Remove or deprecate SurrealDB layer until core workflows stable
- **Rationale**: Dual state management is causing complexity; focus on one reliable backend
- **Alternative**: If SurrealDB is critical, complete migration fully (test round-trip: markdown → DB → markdown)

#### 1.2 Core Workflow Testing
- **Audit Workflow**: `meta audit` must catch all invariant violations
- **Goal Workflow**: Create → Update Status → Archive (test all transitions)
- **Phase Workflow**: Define phases → Assign goals → Validate coherence
- **Daily Workflow**: `meta today` → Edit → Parse frontmatter correctly

#### 1.3 Git Integration Verification
- **Test**: `git status` tracking of governance/ changes
- **Test**: `commit_governance_changes` creates proper commits
- **Test**: `get_file_history` returns accurate file change history
- **Fix**: Wire git commands to GUI components (show status in sidebar, commit from GUI)

#### 1.4 GUI Data Flow Audit
- **Components to verify**:
  - `GoalEditor.svelte` ← → Tauri `update_goal` command
  - `DailyEditor.svelte` ← → Tauri `update_daily_note` command
  - `PhaseEditor.svelte` ← → Tauri `update_phase` command
- **Ensure**: Two-way binding works (edit in UI → persists to file → reload shows change)
- **Ensure**: Toast notifications fire on success/error

### Phase 2: Aequitas Completion Dashboard (Priority: HIGH)

**Objective**: Build custom dashboard to track "Finish Aequitas" mission

#### 2.1 Dashboard Metrics
- **Aequitas Completion Percentage**: Based on Goals marked `done` vs `total`
- **Current Phase Status**: What phase is Aequitas in? (e.g., Phase 4: Accounting Engine Integration)
- **Active Blockers**: Goals with `blocked` status + why they're blocked
- **Recent Progress**: Daily notes from last 7 days showing velocity
- **Critical Path**: Goals with most reverse dependencies (blocking other goals)

#### 2.2 Dashboard Data Sources
- **Input**: Governance folder (`02_PHASES/`, `03_GOALS/`, `01_DAILY/`)
- **Parser**: Extract phase definitions, goal dependencies, daily references
- **Calculator**: Compute completion %, identify critical path, aggregate blockers
- **Output**: JSON payload to GUI dashboard component

#### 2.3 Dashboard GUI Component
- **Location**: `metatheos-gui/src/lib/AequitasDashboard.svelte`
- **Layout**:
  - Top: Big number (e.g., "Aequitas: 67% Complete")
  - Left: Phase progress bars
  - Center: Critical path graph
  - Right: Blockers list with actions
  - Bottom: Recent activity feed (daily notes)
- **Interactivity**: Click on blocker → opens GoalEditor with suggested fixes

### Phase 3: Information Consolidation (Priority: MEDIUM)

**Objective**: Single source of truth documentation

#### 3.1 Consolidate into README.md
- **Structure**:
  1. **Overview & Mission** (keep existing)
  2. **Architecture** (merge IMPLEMENTATION.md)
  3. **Installation** (keep existing)
  4. **Usage** (keep existing + add AI setup from AI_SETUP_GUIDE.md)
  5. **AI Integration** (merge OLLAMA_SETUP.md, OLLAMA_PRIVATE_GPT_ARCHITECTURE.md)
  6. **Development** (merge GOVERNANCE_INTERFACE_COMPLETE.md, INTERACTIVE_FEATURES.md)
  7. **Roadmap** (update with optimization phases)
  8. **Contributing** (keep existing)

#### 3.2 Archive Historical Docs
- **Move to**: `metatheos/docs/archive/`
- **Keep**:
  - `FOLDER_CLEANUP.md` → archive
  - `ICONS_SETUP.md` → archive
  - `INFORMATION_ENRICHMENT.md` → archive
- **Delete** (if fully merged): Original .md files after consolidation

#### 3.3 Create `/docs` for Design Docs
- `/docs/architecture.md` (high-level system design)
- `/docs/ai-integration.md` (LLM/reasoner design when Phase 4 starts)
- `/docs/aequitas-bridge.md` (data exchange protocol, translation layer)

### Phase 4: AI Integration (Priority: LOW - Future)

**Defer until Phase 1 & 2 complete**

Reasoner and LLM modules exist but should only be wired up after:
- Core workflows are stable
- Aequitas dashboard is functional
- Documentation is consolidated

When ready:
- Wire `ReasoningEngine` to CLI command (`meta reason <query>`)
- Connect `AIService` to GUI Assistant component
- Implement governed prompts (stored in `06_PROMPTS/`)

---

## Immediate Next Steps (Week 1)

### Day 1-2: Persistence Decision ✅ COMPLETED (2025-12-31)
- [x] **Decision**: Markdown-only (SurrealDB deferred to Phase 4+)
- [x] Commented out SurrealDB initialization in `main.rs` and `state.rs`
- [x] Simplified `get_daily_note()` to read directly from markdown
- [x] Created `PERSISTENCE_STRATEGY.md` documenting decision
- [x] Created `SURREALDB_MIGRATION.md` for future Phase 4 migration design

### Day 3-4: Core Workflow Testing
- [ ] Write integration tests for `meta audit`, `meta goals`, `meta today`
- [ ] Test all goal status transitions in CLI and GUI
- [ ] Verify git commands work end-to-end

### Day 5-6: Aequitas Dashboard Design
- [ ] Design dashboard data model (JSON schema)
- [ ] Implement dashboard calculator in `metatheos-core`
- [ ] Create Tauri command `get_aequitas_dashboard`
- [ ] Wire up to GUI component

### Day 7: Documentation Consolidation
- [ ] Merge all .md files into README.md
- [ ] Create `/docs` folder for design docs
- [ ] Archive historical docs

---

## Success Metrics

**Phase 1 Complete** when:
- ✅ All CLI commands run without errors
- ✅ GUI can CRUD goals/phases/daily notes reliably
- ✅ Git integration tracks changes and commits properly
- ✅ Zero known data corruption or inconsistency issues

**Phase 2 Complete** when:
- ✅ Aequitas dashboard shows accurate completion percentage
- ✅ Critical path and blockers update in real-time
- ✅ Architect can answer "How far along is Aequitas?" in <5 seconds

**Phase 3 Complete** when:
- ✅ README.md is the single source of truth (<20 KB)
- ✅ No duplicate or outdated information in repo
- ✅ New contributors can onboard from README alone

---

## Alignment with Core Mission

| Mission Pillar | Optimization Support |
|----------------|----------------------|
| **Finish Aequitas** | Aequitas Dashboard tracks progress, identifies blockers, shows critical path |
| **Leave a Trace** | Git integration + Daily notes ensure all decisions/work is recorded |
| **Continue Evolution** | Stable core → future AI integration → ongoing assistance after Aequitas ships |

---

## Open Questions

1. ~~**SurrealDB**: Keep or deprecate?~~ **RESOLVED (2025-12-31)**: Markdown-first, SurrealDB deferred to Phase 4+
2. **Reasoner Module**: When should this be activated? (Deferred to Phase 4)
3. **Aequitas Data Exchange**: How should crash logs/tickets be ingested? (Design needed for Phase 2)
4. **Phase Transitions**: Should metatheos enforce phase transitions or just track them? (To be decided in Phase 2)

---

**Next Review**: After Week 1 (Day 7)
**Responsible**: Architect + Claude
**Output**: Updated OPTIMIZATION_PLAN.md with Phase 1 results
