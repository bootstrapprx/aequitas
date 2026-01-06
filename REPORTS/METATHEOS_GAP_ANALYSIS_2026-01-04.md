# Metatheos Gap Analysis: Proposed vs Actual State

**Date:** 2026-01-04
**Context:** Re-verification after consequence engine patch
**Finding:** System detects but doesn't surface

---

## Executive Summary

**Status:** Consequence engine EXISTS, events are GENERATED, but outcomes are INVISIBLE to users.

Metatheos has a **functional backend** for detecting completion cascades, but has **zero UI** to surface these insights. The system knows when things are ready to complete, but never tells you.

---

## What's Actually Implemented

### ✅ Backend: Consequence Detection (Exists)

**Files:**
- [metatheos-core/src/store/consequences.rs](metatheos/metatheos-core/src/store/consequences.rs) - Consequence engine implementation
- [metatheos-core/src/store/queries.rs](metatheos/metatheos-core/src/store/queries.rs) - Aggregation queries

**Hooks wired in:**
1. ✅ **Task completion** → Goal readiness check ([commands.rs:2568-2573](metatheos/metatheos-gui/src-tauri/src/commands.rs#L2568-L2573))
2. ✅ **Goal status change** → Phase progress update ([commands.rs:1088-1091](metatheos/metatheos-gui/src-tauri/src/commands.rs#L1088-L1091))
3. ✅ **Day creation** → Required goal evaluation ([commands.rs:4125-4128](metatheos/metatheos-gui/src-tauri/src/commands.rs#L4125-L4128))

**Events generated:**
- ✅ `goal_ready_to_complete` - All tasks for a goal are done
- ✅ `phase_progress_updated` - Phase completion stats
- ✅ `phase_ready_to_close` - All goals in phase are done
- ✅ `day_success` - All required goals completed
- ✅ `day_progress` - Partial required goal completion

---

## What's Missing

### ❌ Frontend: Event Consumption (Does Not Exist)

**No UI to:**
- Display system-generated events
- Show completion prompts
- Surface phase progress
- Indicate day success/failure
- Present any insights from consequence engine

**Evidence:**
```bash
# Search for event consumption in UI
grep -r "goal_ready_to_complete\|phase_ready_to_close\|day_success" metatheos/metatheos-gui/src/lib/*.svelte
# Result: No matches found
```

**No commands to:**
```bash
# Search for event retrieval commands
grep -r "get_events\|list_events\|fetch_events" metatheos/metatheos-core/src/store/mod.rs
# Result: No matches found
```

**Result:** Events are logged to database but never retrieved or displayed.

---

## The Disconnect

### Backend Says:
> "I detected that all tasks for Goal G-042 are complete. I logged an event suggesting the user should mark the goal as done."

### Frontend Says:
> "Here's your goal list. Click buttons to update stuff. Good luck figuring out what needs attention."

### User Experiences:
> "I have no idea if my goals are ready to complete. I have to manually count tasks."

---

## Specific Gaps

### 1. No Notification System

**What's missing:**
- Notification panel/widget
- Badge counts for pending actions
- Toast messages for system insights
- Alert when goals/phases are ready to close

**Impact:** User never sees consequence engine output

### 2. No Progress Aggregation Display

**What backend calculates:**
```rust
// queries.rs computes:
pub async fn get_phase_progress(store, phase_id) -> (total_goals, done_goals)
pub async fn get_goal_task_completion(store, goal_id) -> (total_tasks, done_tasks)
pub async fn get_day_required_goal_status(store, day_id) -> (required, done)
```

**What UI shows:**
- ❌ Phase progress bars (nowhere)
- ❌ Goal completion percentages (nowhere)
- ❌ Day outcome badges (nowhere)

**Impact:** No visual feedback on progress

### 3. No Event Timeline/Feed

**What's logged:**
```json
{
  "entity_type": "goal",
  "entity_id": "G-042",
  "action": "update",
  "actor": "system",
  "payload": {
    "type": "goal_ready_to_complete",
    "reason": "all_tasks_done",
    "total_tasks": 5,
    "done_tasks": 5
  },
  "created_at": "2026-01-04T..."
}
```

**What's displayed:**
- ❌ Nothing

**Impact:** Events are write-only data

### 4. No Action Prompts

**What should happen:**
When all tasks are done → Show banner:
> ✅ **Goal G-042 is ready to complete**
> All 5 tasks are done. [Mark as Done]

**What actually happens:**
- Nothing
- User manually counts tasks
- User manually checks if goal should be marked done

**Impact:** System intelligence is invisible

### 5. No Dashboard Insights

**What backend knows:**
- Phase 1: 5/7 goals done (71%)
- Phase 2: 0/5 goals done (0%)
- Day 2026-01-04: 2/2 required goals done (success)
- 3 goals ready to complete
- 1 phase ready to close

**What dashboard shows:**
- Generic goal list
- No aggregation
- No completion stats
- No actionable insights

**Impact:** Dashboard is information-poor

---

## Proposed vs Actual State

### What Metatheos README Claims:

> "A local-first, deterministic governance engine for the Aequitas project."
> **Status:** Production Ready ✅

**Promises:**
- ✅ "Governance validation — Enforce invariants, detect gaps, surface inconsistencies"
- ✅ "Goal management — Query, filter, and update goals by status/phase"
- ✅ "Daily workflow — Create and manage daily notes with templates"
- ✅ "Phase tracking — Monitor phase coherence and transitions"
- ❌ **"Real-time updates"** - Events not shown
- ❌ **"Surface inconsistencies"** - Events not surfaced

### What's Actually True:

**Backend (COMPLETE):**
- ✅ Detects completion cascades
- ✅ Generates consequence events
- ✅ Logs all system intelligence

**Frontend (INCOMPLETE):**
- ❌ Doesn't show events
- ❌ Doesn't display progress aggregation
- ❌ Doesn't surface insights
- ❌ Doesn't prompt user actions

**Verdict:** Backend is production-ready. Frontend is data-blind.

---

## What Users Actually Need

### Minimal Viable UI (1-2 days)

**1. Notification Badge** (2-3 hours)
- Count of pending system events
- Click to expand event list
- Shows: goal/phase ready to complete, day outcomes

**Implementation:**
```rust
// New command:
#[tauri::command]
pub async fn get_recent_events(
    limit: usize,
    entity_type: Option<String>,
    state: State<'_, AppState>
) -> Result<Vec<Event>, String> {
    let store = get_store(state)?;
    let mut response = store.db.query(
        "SELECT * FROM event
         WHERE (entity_type = $etype OR $etype IS NONE)
         ORDER BY created_at DESC
         LIMIT $limit"
    )
    .bind(("etype", entity_type))
    .bind(("limit", limit))
    .await?;

    let events: Vec<Event> = response.take(0)?;
    Ok(events)
}
```

```svelte
<!-- NotificationBadge.svelte -->
<script>
  let pendingEvents = [];

  async function loadEvents() {
    pendingEvents = await invoke("get_recent_events", {
      limit: 10,
      entityType: null
    });
  }

  onMount(() => {
    loadEvents();
    setInterval(loadEvents, 30000); // Poll every 30s
  });
</script>

{#if pendingEvents.length > 0}
  <div class="notification-badge">
    <span>{pendingEvents.length}</span>
    <div class="event-list">
      {#each pendingEvents as event}
        <EventItem {event} />
      {/each}
    </div>
  </div>
{/if}
```

**2. Progress Indicators** (3-4 hours)

**Phase Progress:**
```svelte
<!-- PhaseProgressBar.svelte -->
<script>
  async function loadProgress(phaseId) {
    const events = await invoke("get_recent_events", {
      limit: 1,
      entityType: "phase"
    });

    const progressEvent = events.find(e =>
      e.payload.type === "phase_progress_updated" &&
      e.entity_id === phaseId
    );

    if (progressEvent) {
      return {
        total: progressEvent.payload.total_goals,
        done: progressEvent.payload.done_goals,
        pct: (done / total * 100).toFixed(0)
      };
    }
  }
</script>

<div class="progress-bar">
  <div class="fill" style="width: {pct}%"></div>
  <span>{done}/{total} goals ({pct}%)</span>
</div>
```

**Goal Completion Prompt:**
```svelte
<!-- GoalCompletionPrompt.svelte -->
{#if goalReadyEvent}
  <div class="completion-banner">
    ✅ <strong>{goalReadyEvent.entity_id} is ready to complete</strong>
    <p>All {goalReadyEvent.payload.total_tasks} tasks are done.</p>
    <button on:click={completeGoal}>Mark as Done</button>
    <button on:click={dismiss}>Dismiss</button>
  </div>
{/if}
```

**3. Day Outcome Badge** (1-2 hours)

```svelte
<!-- DayOutcomeBadge.svelte -->
<script>
  async function checkDayOutcome(dayId) {
    const events = await invoke("get_recent_events", {
      limit: 1,
      entityType: "day"
    });

    const outcome = events.find(e =>
      e.entity_id === dayId &&
      (e.payload.type === "day_success" || e.payload.type === "day_progress")
    );

    return outcome;
  }
</script>

{#if outcome}
  {#if outcome.payload.type === "day_success"}
    <div class="badge success">
      ✅ Success ({outcome.payload.required_goals}/{outcome.payload.required_goals})
    </div>
  {:else}
    <div class="badge in-progress">
      ⏳ In Progress ({outcome.payload.completed_required_goals}/{outcome.payload.required_goals})
    </div>
  {/if}
{/if}
```

---

## Implementation Priority

### Phase 1: Event Retrieval (2 hours)
1. Add `get_recent_events` command to fetch events from DB
2. Add `get_events_by_entity` command for entity-specific events
3. Wire commands into Tauri

### Phase 2: Notification System (3 hours)
1. Create NotificationBadge component
2. Add to Dashboard/CurrentDay views
3. Show count of pending actions

### Phase 3: Progress Display (4 hours)
1. Add PhaseProgressBar to PhaseManager
2. Add GoalCompletionPrompt to GoalDetail
3. Add DayOutcomeBadge to CurrentDay

### Phase 4: Event Timeline (3 hours)
1. Create EventFeed component
2. Show chronological system events
3. Filter by entity type/action

---

## Success Criteria

After implementation, users should:

1. ✅ **See completion prompts**: "Goal X ready - all tasks done"
2. ✅ **See progress stats**: "Phase 1: 71% complete (5/7 goals)"
3. ✅ **See day outcomes**: "Day 2026-01-04: ✅ Success"
4. ✅ **See pending actions**: "3 goals ready to complete"
5. ✅ **See system events**: Timeline of what the system detected

---

## Bottom Line

**What's implemented:** Detection engine ✅
**What's missing:** Display layer ❌

**Effort to fix:** ~12-14 hours of UI work
**Impact:** System goes from "data-blind" to "insight-driven"

**Current state:**
- Backend: 100% functional
- Frontend: 0% connected

**Gap:** The last mile of showing users what the system already knows.

---

## Recommendation

**Priority: HIGH**

The consequence engine is complete but **invisible**. Users can't benefit from system intelligence if they never see it.

**Next action:** Implement Phase 1 (event retrieval commands) to unblock UI development.

---

**Status:** Gap Identified
**Blocker:** No event retrieval API
**Fix path:** Add 4 commands, 3 UI components, wire them up
