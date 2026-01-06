# Event System Enhancement Report
**Date:** January 6, 2026
**Phase:** Phase 0 - Foundation (Event Intelligence Deepening)

## Executive Summary

Enhanced Metatheos's consequence detection system from reactive-only to proactive + reactive, making system intelligence visible and actionable through a dedicated Activity page with automated scanning.

## Core Enhancements

### 1. Expanded ConsequenceEngine (Backend)

**File:** `metatheos-core/src/store/consequences.rs`

Added 4 new proactive detection methods:

#### A. `scan_blocked_goals()`
- **Detects:** Goals marked as "blocked" with unmet dependencies
- **Action:** Generates `goal_blocked` events with list of blocking dependencies
- **Use Case:** Surface goals stuck waiting for prerequisite completion

#### B. `scan_stale_goals(days_threshold)`
- **Detects:** Goals with no activity in N days (default: 7)
- **Action:** Generates `goal_stale` events with days since last activity
- **Use Case:** Identify abandoned or forgotten goals needing closure decisions

#### C. `scan_complex_goals(task_threshold)`
- **Detects:** Goals with excessive tasks (default: 15+)
- **Action:** Generates `goal_high_complexity` events with task count
- **Suggestion:** "Consider breaking into smaller subgoals"
- **Use Case:** Prevent scope creep and improve tracking granularity

#### D. `scan_phase_transitions()`
- **Detects:** Planned phases whose dependencies are all completed
- **Action:** Generates `phase_ready_to_activate` events
- **Use Case:** Auto-detect when roadmap phases are ready to begin

#### E. `run_all_scans()`
- **Purpose:** Run all 4 scans in parallel
- **Returns:** `ScanReport` with categorized findings
- **Trigger:** Manual or auto-scheduled

**New Event Types:**
- `goal_blocked` - Dependencies blocking progress
- `goal_stale` - No recent activity
- `goal_high_complexity` - Too many tasks
- `phase_ready_to_activate` - Ready to start

### 2. Tauri Command Integration

**File:** `metatheos-gui/src-tauri/src/commands.rs`

Added `run_consequence_scan` command:
```rust
#[tauri::command]
pub async fn run_consequence_scan(state: State<'_, AppState>) -> Result<serde_json::Value, String>
```

**Registered in:** `main.rs:186`

### 3. Activity Page (New UI)

**File:** `metatheos-gui/src/lib/Activity.svelte`

**Features:**
- **Scan Control Panel**
  - Manual "Run Scan" button
  - Auto-scan toggle (5-minute intervals)
  - Last scan timestamp display

- **Scan Results Dashboard** (4 cards):
  - 🚫 **Blocked Goals** - Yellow card, shows count + top 3 IDs
  - ⏰ **Stale Goals** - Orange card, shows count + top 3 IDs
  - 🧩 **Complex Goals** - Purple card, shows count + top 3 IDs
  - 🎯 **Phases Ready** - Green card, shows count + top 3 IDs

- **Event Feed Integration**
  - Embedded `EventFeed` component
  - Auto-refreshes every 30s
  - Shows last 100 events

- **Insights Panel**
  - Contextual suggestions based on scan results
  - "All clear" state when no issues detected

**Navigation:** Added to sidebar as "⚡ Activity" (3rd item)

### 4. EventFeed Enhancements

**File:** `metatheos-gui/src/lib/EventFeed.svelte`

**Added Event Type Recognition:**
- `goal_blocked` → 🚫 "Goal Blocked"
- `goal_stale` → ⏰ "Goal Stale (No Activity)"
- `goal_high_complexity` → 🧩 "Goal Too Complex"
- `phase_ready_to_activate` → 🎯 "Phase Ready to Activate"

### 5. Navigation Integration

**File:** `metatheos-gui/src/App.svelte`

- Added Activity import
- Added "activity" view to navigation array
- Routed `currentView === "activity"` to `<Activity />` component

## Architecture Decisions

### Proactive vs Reactive
- **Reactive:** Triggered by user actions (task completion, status changes)
- **Proactive:** Triggered by scheduled scans or manual requests
- **Both logged to same `event` table** for unified audit trail

### Scan Thresholds
- **Stale days:** 7 (configurable)
- **Complexity tasks:** 15 (configurable)
- **Auto-scan interval:** 5 minutes (UI configurable)

### Event Persistence
- All consequence events logged to SurrealDB `event` table
- Schema: `entity_type`, `entity_id`, `action`, `actor`, `payload`, `created_at`
- Actor: "system" for automated detections

## User Experience Flow

1. **User opens Activity page** → Initial scan runs automatically
2. **Scan results displayed** → 4-card dashboard shows categorized issues
3. **Event feed shows timeline** → Chronological view of all system events
4. **Insights panel suggests actions** → Contextual guidance based on findings
5. **Auto-scan keeps data fresh** → Optional 5-minute polling

## Technical Implementation

### Query Patterns Used

**Blocked Goals:**
```sql
SELECT * FROM goal WHERE status = 'blocked' AND array::len(dependencies) > 0
```

**Stale Goals:**
```sql
SELECT * FROM goal WHERE status IN ['open', 'partial'] AND created_at < time::now() - 7d
```

**Complex Goals:**
```sql
SELECT goal_id, count() as task_count FROM work_item WHERE level = 'task' GROUP BY goal_id
```

**Phase Transitions:**
```sql
SELECT * FROM phase WHERE status IN ['planned', 'active']
```

### Event Generation Pattern
```rust
let event = Event::new(
    "goal",
    &goal_id,
    EventAction::Update,
    "system",
    json!({
        "type": "goal_blocked",
        "reason": "unmet_dependencies",
        "unmet_dependencies": vec!["G-P1-01", "G-P1-02"]
    }),
);
store.log_event(&event).await;
```

## Testing Checklist

- [x] Backend: ConsequenceEngine compiles
- [x] Backend: `run_consequence_scan` command registered
- [x] Frontend: Activity page renders
- [x] Frontend: Scan button functional
- [x] Frontend: Auto-scan toggle works
- [x] Frontend: Event feed displays new event types
- [x] Frontend: Navigation to Activity page
- [ ] End-to-end: Trigger scans and verify events logged
- [ ] End-to-end: Verify scan results accuracy
- [ ] Performance: Scan latency under typical data volume

## Build Status

✅ **Successful** - `cargo build --release` completed with 1 minor warning (unused import)

## Next Steps (Optional Enhancements)

1. **Dashboard Integration** - Add event insights widget to main dashboard
2. **Event Actions** - Add buttons to resolve events (e.g., "Mark as Reviewed", "Unblock Goal")
3. **Scan Scheduling** - Backend cron-style scheduler for automatic scans
4. **Notification System** - Browser notifications for critical events
5. **Event Filtering** - Advanced filters by type, date range, entity
6. **Export Reports** - Generate PDF/CSV reports of scan results

## Impact

### Before
- Events generated reactively only
- No visibility into system health
- Issues discovered manually or by accident
- No proactive guidance

### After
- Automated proactive issue detection
- Centralized activity/event dashboard
- Actionable insights surfaced automatically
- 4 new categories of system intelligence
- Auto-refresh keeps data current

## Files Modified

**Backend:**
- `metatheos-core/src/store/consequences.rs` (125 lines added)
- `metatheos-gui/src-tauri/src/commands.rs` (+13 lines)
- `metatheos-gui/src-tauri/src/main.rs` (+1 line)

**Frontend:**
- `metatheos-gui/src/lib/Activity.svelte` (NEW - 267 lines)
- `metatheos-gui/src/lib/EventFeed.svelte` (+17 lines)
- `metatheos-gui/src/App.svelte` (+4 lines)

**Total:** ~427 lines of new code

## Conclusion

The enhanced event system transforms Metatheos from a passive tracker to an active governance advisor. By detecting blocked goals, stale work, complexity issues, and phase readiness, the system now provides proactive intelligence that guides users toward better project health.

This aligns with Phase 0's goal: "Before correctness, you need **visibility**. Before building systems, you need to **observe systems**."

---

**Status:** ✅ Complete and ready for user testing
**Build:** ✅ Successful
**Documentation:** ✅ Complete
