# Aequitas Dashboard Design

**Purpose:** Track "Finish Aequitas" mission progress
**Date:** 2025-12-31
**Status:** IN_PROGRESS

---

## Objective

Build a custom dashboard that answers the question: **"How far along is Aequitas?"** in <5 seconds.

The dashboard serves the **primary mission**: **Finish Aequitas**.

---

## Data Model (JSON Schema)

```typescript
interface AequitasDashboard {
  // Overall Progress
  completion: {
    percentage: number;           // 0-100: % of goals marked 'done'
    total_goals: number;          // Total goal count
    done_goals: number;           // Goals with status 'done'
    active_goals: number;         // Goals with status 'active'
    blocked_goals: number;        // Goals with status 'blocked'
    planned_goals: number;        // Goals with status 'planned'
  };

  // Current Phase Status
  current_phase: {
    phase_number: number | null;  // e.g., 4
    phase_title: string | null;   // e.g., "Phase 4: Accounting Engine"
    phase_status: string | null;  // e.g., "active", "complete"
    goals_in_phase: number;       // Goals tagged with this phase
    done_in_phase: number;        // Done goals in this phase
    phase_completion: number;     // % complete for this phase
  };

  // Active Blockers
  blockers: Array<{
    goal_id: string;              // e.g., "G-042"
    title: string;                // Goal title
    reason: string | null;        // Why blocked (extracted from content)
    blocked_since: string | null; // Date (if trackable)
    blocking_count: number;       // How many goals depend on this
  }>;

  // Critical Path (Goals blocking others)
  critical_path: Array<{
    goal_id: string;              // e.g., "G-010"
    title: string;                // Goal title
    status: string;               // Current status
    reverse_dependencies: number; // Count of goals depending on this
    phase: string | null;         // Phase this goal belongs to
  }>;

  // Recent Progress (Last 7 days)
  recent_activity: {
    days_tracked: number;         // Number of days with daily notes
    goals_completed: number;      // Goals marked done in last 7 days
    goals_started: number;        // Goals moved to 'active' in last 7 days
    velocity: number;             // Goals/day completion rate
    daily_notes: Array<{
      date: string;               // YYYY-MM-DD
      goals_worked: string[];     // Goal IDs mentioned
      decisions_made: string[];   // Decision IDs mentioned
    }>;
  };

  // Health Indicators
  health: {
    blocked_percentage: number;   // % of goals blocked
    orphaned_goals: number;       // Goals with no phase or canon reference
    missing_dependencies: number; // Count of broken dependency links
    audit_errors: number;         // Count of governance audit errors
  };

  // Metadata
  generated_at: string;           // ISO timestamp
  governance_root: string;        // Path to governance folder
}
```

---

## Calculation Logic

### 1. Completion Percentage

```rust
completion_percentage = (done_goals / total_goals) * 100
```

**Counting Rules:**
- Include all goals with `goal_id` matching `G-XXX` pattern
- Count status: `done` → done_goals
- Count status: `active` → active_goals
- Count status: `blocked` → blocked_goals
- Count status: `planned` → planned_goals
- Total = sum of all statuses

### 2. Current Phase Detection

**Algorithm:**
1. Look for most recent phase file with `status: active` in frontmatter
2. If none active, find highest phase number with goals
3. Extract phase number, title, status
4. Count goals with `phase: N` field matching current phase
5. Calculate phase completion: (done_in_phase / total_in_phase) * 100

### 3. Active Blockers

**Algorithm:**
1. Find all goals with `status: blocked`
2. For each blocked goal:
   - Extract title
   - Parse content for blocker reason (look for "Blocked by:" or similar)
   - Count reverse dependencies (how many goals list this as dependency)
   - Sort by reverse_dependencies DESC (most critical first)

### 4. Critical Path

**Algorithm:**
1. Build dependency graph (goal_id → dependencies[])
2. For each goal, count reverse dependencies (how many goals depend on it)
3. Filter goals with reverse_dependencies > 0
4. Sort by reverse_dependencies DESC
5. Return top 10 critical goals

### 5. Recent Progress

**Algorithm:**
1. Load daily notes from last 7 days
2. Count notes with content (days_tracked)
3. For each note:
   - Extract `goals_worked` array from frontmatter
   - Extract `decisions_made` array from frontmatter
4. Aggregate:
   - Count unique goals marked 'done' in last 7 days (check `updated` field)
   - Count unique goals moved to 'active' in last 7 days
   - Calculate velocity: goals_completed / 7

### 6. Health Indicators

**Algorithm:**
- `blocked_percentage` = (blocked_goals / total_goals) * 100
- `orphaned_goals` = count goals with no `phase` AND no `canon` field
- `missing_dependencies` = count dependency IDs that don't match any goal
- `audit_errors` = run governance validator, count errors (not warnings)

---

## UI Layout (AequitasDashboard.svelte)

```
┌─────────────────────────────────────────────────────────┐
│  AEQUITAS PROGRESS                                      │
│                                                         │
│  ███████████████░░░░░  67%                             │
│  67 of 100 goals complete                              │
│                                                         │
│  Active: 20  |  Blocked: 10  |  Planned: 3            │
└─────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────────────┐
│ CURRENT PHASE        │  │ BLOCKERS (10)                │
│                      │  │                              │
│ Phase 4              │  │ 🔴 G-042 Database Migration │
│ Accounting Engine    │  │    Blocking 5 goals          │
│                      │  │                              │
│ ████████░░  80%      │  │ 🔴 G-037 API Refactor       │
│ 16 of 20 complete    │  │    Blocking 3 goals          │
└──────────────────────┘  └──────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ CRITICAL PATH (Goals blocking others)                  │
│                                                         │
│ 1. G-010 Chart of Accounts Schema    [active]  →  8    │
│ 2. G-015 Journal Entry Validation    [active]  →  6    │
│ 3. G-023 Fiscal Period Management    [blocked] →  5    │
└─────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────────────┐
│ RECENT ACTIVITY      │  │ HEALTH                       │
│ Last 7 days          │  │                              │
│                      │  │ ✅ Audit: No errors          │
│ ✅ 5 goals completed │  │ ⚠️  Blocked: 10% (high)      │
│ 📝 6 days tracked    │  │ ⚠️  Orphaned: 2 goals        │
│ 📈 0.7 goals/day     │  │ ✅ Dependencies: All valid   │
└──────────────────────┘  └──────────────────────────────┘
```

**Design Principles:**
- Information density (Architect-grade)
- Dark mode default
- Monospaced data where appropriate
- No animations or gamification
- Clear visual hierarchy (most important at top)

---

## Implementation Plan

### Step 1: Dashboard Calculator (metatheos-core)

**File:** `metatheos-core/src/dashboard/mod.rs`

```rust
pub struct DashboardCalculator {
    ctx: GovernanceContext,
}

impl DashboardCalculator {
    pub fn new(ctx: GovernanceContext) -> Self { ... }

    pub fn calculate(&self) -> AequitasDashboard { ... }

    fn calculate_completion(&self) -> CompletionMetrics { ... }
    fn detect_current_phase(&self) -> PhaseStatus { ... }
    fn find_blockers(&self) -> Vec<Blocker> { ... }
    fn build_critical_path(&self) -> Vec<CriticalGoal> { ... }
    fn analyze_recent_activity(&self) -> RecentActivity { ... }
    fn calculate_health(&self) -> HealthMetrics { ... }
}
```

### Step 2: Tauri Command

**File:** `metatheos-gui/src-tauri/src/commands.rs`

```rust
#[tauri::command]
pub fn get_aequitas_dashboard(state: State<AppState>) -> Result<AequitasDashboard, String> {
    let root = state.governance_root.lock().unwrap();
    let ctx = GovernanceContext::load(&*root).map_err(|e| e.to_string())?;
    let calculator = DashboardCalculator::new(ctx);
    Ok(calculator.calculate())
}
```

### Step 3: Svelte Component

**File:** `metatheos-gui/src/lib/AequitasDashboard.svelte`

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';

  let dashboard: AequitasDashboard | null = null;
  let loading = true;

  async function loadDashboard() {
    loading = true;
    try {
      dashboard = await invoke('get_aequitas_dashboard');
    } catch (e) {
      console.error('Failed to load dashboard:', e);
    } finally {
      loading = false;
    }
  }

  onMount(loadDashboard);
</script>

<!-- UI implementation -->
```

### Step 4: Integration

**File:** `metatheos-gui/src/App.svelte` or router

Add dashboard as main view or accessible tab.

---

## Testing Strategy

1. **Unit Tests** (`metatheos-core/src/dashboard/mod.rs`):
   - Test completion calculation with known goal counts
   - Test phase detection with various phase statuses
   - Test blocker extraction and sorting
   - Test critical path construction

2. **Integration Test**:
   - Load actual governance folder
   - Generate dashboard
   - Verify all metrics are reasonable
   - Verify JSON serialization

3. **Manual UI Test**:
   - Start GUI
   - Navigate to dashboard
   - Verify all widgets display correctly
   - Verify data updates on refresh

---

## Success Criteria

- [x] Data model designed and documented
- [ ] Dashboard calculator implemented
- [ ] Tauri command created
- [ ] Svelte component built
- [ ] Dashboard accessible in GUI
- [ ] Architect can answer "How far along is Aequitas?" in <5 seconds
- [ ] Metrics update in real-time (on governance file changes)

---

## Next Steps

1. Implement `DashboardCalculator` in `metatheos-core`
2. Add unit tests for calculator
3. Create Tauri command
4. Build Svelte component
5. Wire to main GUI

---

**Estimated Effort:** 4-6 hours
**Priority:** HIGH (Core Mission: Finish Aequitas)
**Blocked By:** None (all dependencies ready)
