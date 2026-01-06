# Metatheos Half-Baked Functionality Audit

**Date:** 2026-01-04
**Issue:** System is "just for show" - actions have no consequences
**Root Cause:** Data collection exists, but behavioral loops are missing

---

## Executive Summary

Metatheos can **record** many things but **does** almost nothing in response. The system is a write-only data graveyard with no closure loops.

### What Works (Data Collection)
✅ Can create work items
✅ Can mark work items done
✅ Can update goal status
✅ Can create days
✅ Can add annotations
✅ Can log events
✅ Can record AI runs

### What Doesn't Work (Consequences)
❌ Completing tasks doesn't affect goals
❌ Completing goals doesn't affect phases
❌ Completing day goals doesn't close days
❌ Annotations don't trigger anything
❌ Events aren't consumed by anything
❌ AI runs exist in isolation
❌ No aggregation, no rollup, no cascade

---

## Detailed Breakdown

### 1. Work Item Completion Has No Effect

**Location:** [commands.rs:2507-2539](metatheos/metatheos-gui/src-tauri/src/commands.rs#L2507-L2539)

**What happens when you mark a task done:**
```rust
pub async fn set_work_item_status(...) {
    // ... load work item
    item.status = new_status.clone();
    if matches!(new_status, WorkItemStatus::Done) {
        item.completed_at = Some(chrono::Utc::now());  // ✅ Sets timestamp
    }
    store.update_work_item(&item).await?;  // ✅ Saves to DB
    Ok(item.into())  // ✅ Returns to UI
}
```

**What SHOULD happen but doesn't:**
- ❌ Check if all sibling tasks are done → auto-complete parent subgoal
- ❌ Check if all subgoals are done → auto-complete goal
- ❌ Check if goal is linked to today's day → update day progress
- ❌ Generate completion event with cascade metadata
- ❌ Trigger any notification or insight

**Consequence:** Tasks are write-only. Completing them is performative.

---

### 2. Goal Status Updates Are Isolated

**Location:** [commands.rs:1049-1064](metatheos/metatheos-gui/src-tauri/src/commands.rs#L1049-L1064)

**What happens when you mark a goal done:**
```rust
pub async fn update_goal_status(goal_id, new_status, ...) {
    let ctx = GovernanceContext::load_async(&root).await?;
    let status_enum = parse_goal_status(&new_status)?;
    ctx.update_goal_status(&goal_id, status_enum)?;  // ✅ Validates transition
                                                       // ✅ Updates markdown
    Ok(format!("Updated {} to {}", goal_id, new_status))  // ✅ Returns message
}
```

**What happens in `ctx.update_goal_status`:**
```rust
pub fn update_goal_status(&self, goal_id: &str, new_status: GoalStatus) -> Result<()> {
    let goal = self.get_goal(goal_id)?;

    if !goal.status.can_transition_to(&new_status) {  // ✅ Validates
        return Err(invalid_transition);
    }

    // ✅ Updates frontmatter in markdown file
    frontmatter.insert("status", new_status.to_string());
    fs::write(&goal.file_path, new_content)?;

    Ok(())  // ✅ Done
}
```

**What SHOULD happen but doesn't:**
- ❌ Check if all goals in phase are done → auto-close phase
- ❌ Update phase completion percentage
- ❌ Mark dependent goals as unblocked
- ❌ Trigger phase transition check
- ❌ Generate phase progress report
- ❌ Sync status to DB (still markdown-only!)

**Consequence:** Goal completion is cosmetic. Phases don't react.

---

### 3. Day Creation Has No Follow-Through

**Location:** [commands.rs:3988-4087](metatheos/metatheos-gui/src-tauri/src/commands.rs#L3988-L4087)

**What happens when you create a day:**
```rust
pub async fn create_day(request: CreateDayRequest, ...) {
    // ✅ Validates day type constraints
    // ✅ Creates Day record in DB
    // ✅ Links goals to day via day_goal table
    // ✅ Emits event
    Ok(day_dto)
}
```

**What SHOULD happen but doesn't:**
- ❌ End-of-day check: were required goals completed?
- ❌ Day closure workflow
- ❌ Success/failure report generation
- ❌ Streak tracking
- ❌ Retrospective trigger
- ❌ Next-day planning prompt

**Current state:** Days are created but never closed. You can't tell if a day succeeded or failed.

---

### 4. Annotations Are Write-Only

**Location:** [commands.rs:2877-2928](metatheos/metatheos-gui/src-tauri/src/commands.rs#L2877-L2928)

**What happens when you add an annotation:**
```rust
pub async fn add_annotation(scope_type, scope_id, body, author, ...) {
    let item = Annotation {
        id: format!("ANN-{}", Uuid::new_v4()),
        entity_type: scope,
        entity_id: scope_id,
        content: body,
        author_type: user_or_ai,
        author_ref: None,
        created_at: chrono::Utc::now(),
    };

    store.add_annotation(&item).await?;  // ✅ Saves to DB

    // ✅ Logs event
    let event = Event::new("annotation", &item.id, EventAction::Create, "user", ...);
    store.log_event(&event).await;

    Ok(item)
}
```

**What SHOULD happen but doesn't:**
- ❌ Annotations with specific tags trigger workflows
- ❌ AI annotations could trigger review prompts
- ❌ Annotations on goals could auto-update blockers
- ❌ Annotation density could indicate goal complexity
- ❌ Annotations could be surfaced in retrospectives

**Consequence:** Annotations are just notes. They don't drive anything.

---

### 5. Events Are Logged But Never Consumed

**Location:** Throughout, especially [schema.rs:207-232](metatheos/metatheos-core/src/store/schema.rs#L207-L232)

**Event table exists:**
```rust
DEFINE TABLE event SCHEMAFULL
DEFINE FIELD entity_type ON TABLE event TYPE string
DEFINE FIELD entity_id ON TABLE event TYPE string
DEFINE FIELD action ON TABLE event TYPE string  // 'create', 'update', 'complete', ...
DEFINE FIELD actor ON TABLE event TYPE string  // 'user', 'system', 'ai'
DEFINE FIELD payload ON TABLE event TYPE object
DEFINE FIELD created_at ON TABLE event TYPE datetime DEFAULT time::now()
```

**Events are logged:**
- ✅ Goal status changes
- ✅ Work item creation
- ✅ Annotation creation
- ✅ Day creation
- ✅ Roadmap ingestion

**Events are consumed:**
- ❌ Never
- ❌ Nowhere
- ❌ By nothing

**What events COULD enable:**
- ❌ Timeline reconstruction
- ❌ Audit trail generation
- ❌ Progress velocity calculation
- ❌ Pattern detection
- ❌ Retrospective auto-generation
- ❌ Notification triggers

**Consequence:** Events are a perfect audit log that nobody reads.

---

### 6. AI Runs Exist in Isolation

**Location:** [schema.rs:259-283](metatheos/metatheos-core/src/store/schema.rs#L259-L283)

**AI Run table exists:**
```rust
DEFINE TABLE ai_run SCHEMAFULL
DEFINE FIELD provider ON TABLE ai_run TYPE string
DEFINE FIELD model ON TABLE ai_run TYPE string
DEFINE FIELD intent ON TABLE ai_run TYPE string  // 'summarize', 'expand', 'critique', ...
DEFINE FIELD context_ref ON TABLE ai_run TYPE object
DEFINE FIELD prompt ON TABLE ai_run TYPE string
DEFINE FIELD response ON TABLE ai_run TYPE string
DEFINE FIELD status ON TABLE ai_run TYPE string  // 'draft', 'applied', 'rejected'
```

**AI runs are recorded:**
- ✅ Full prompt and response captured
- ✅ Context linked (phase_id, goal_id, etc.)
- ✅ Status tracked (draft/applied/rejected)

**AI runs are used for:**
- ❌ Nothing
- ❌ Draft gating doesn't exist
- ❌ No apply/reject workflow
- ❌ No learning from patterns

**What AI runs COULD enable:**
- ❌ Review queue for drafts
- ❌ One-click apply/reject
- ❌ Pattern analysis (what prompts work?)
- ❌ Context-aware suggestions
- ❌ AI annotation source tracking

**Consequence:** AI data is collected but never actioned.

---

### 7. No Aggregation or Rollup Anywhere

**Missing queries:**

```sql
-- These queries DON'T EXIST but SHOULD:

-- Phase progress
SELECT phase_id,
       COUNT(*) as total_goals,
       COUNT(CASE WHEN status = 'done' THEN 1 END) as done_goals,
       (done_goals / total_goals * 100) as progress_pct
FROM goal
GROUP BY phase_id;

-- Day success check
SELECT day_id,
       COUNT(*) as required_goals,
       COUNT(CASE WHEN goal.status = 'done' THEN 1 END) as completed_goals,
       (completed_goals = required_goals) as day_success
FROM day_goal
WHERE required = true
GROUP BY day_id;

-- Work item cascade check
SELECT goal_id,
       COUNT(*) as total_tasks,
       COUNT(CASE WHEN status = 'done' THEN 1 END) as done_tasks,
       (done_tasks = total_tasks) as ready_to_complete_goal
FROM work_item
WHERE level = 'task'
GROUP BY goal_id;
```

**Consequence:** No summaries, no insights, no "you're ready to close X" prompts.

---

## What Makes a System "Real" vs "For Show"

### "For Show" (Current State)
- ✅ UI looks good
- ✅ Can create records
- ✅ Can update records
- ✅ Data validates
- ❌ **Nothing happens as a result**

### "Real" (Required State)
- ✅ UI looks good
- ✅ Can create records
- ✅ Can update records
- ✅ Data validates
- ✅ **Actions trigger consequences**
- ✅ **System responds to state changes**
- ✅ **Completion cascades upward**
- ✅ **Progress is tracked and surfaced**

---

## The Missing Layer: Consequence Engine

What's needed is a **consequence layer** that sits between user actions and the database:

```
User Action
    ↓
Command Handler (validates)
    ↓
Store Mutation (saves)
    ↓
[MISSING: Consequence Engine] ← THIS IS THE GAP
    ↓
Cascade Updates
Event Generation
Notification Triggers
State Recalculation
```

---

## Minimal Viable Consequences

### Phase 1: Task → Goal Cascade

**When:** All tasks in a goal are marked done
**Then:** Prompt user to mark goal as done
**Implementation:**
```rust
pub async fn check_goal_completion(goal_id: &str, store: &SurrealStore) -> Result<bool> {
    let work_items = store.get_work_items_by_goal(goal_id).await?;
    let all_done = work_items.iter().all(|item| matches!(item.status, WorkItemStatus::Done));

    if all_done {
        // Generate notification: "All tasks complete for {goal_id}. Mark goal as done?"
        store.log_event(&Event::new(
            "goal", goal_id, EventAction::Update,
            "system",
            json!({"type": "ready_to_complete", "reason": "all_tasks_done"})
        )).await?;
    }

    Ok(all_done)
}
```

### Phase 2: Goal → Phase Progress

**When:** Goal status changes
**Then:** Recalculate phase progress
**Implementation:**
```rust
pub async fn update_phase_progress(phase_id: &str, store: &SurrealStore) -> Result<PhaseProgress> {
    let mut response = store.db.query(
        "SELECT COUNT(*) as total,
                COUNT(CASE WHEN status = 'done' THEN 1 END) as done
         FROM goal WHERE phase_id = $phase"
    ).bind(("phase", phase_id)).await?;

    let stats: PhaseStats = response.take(0)?;
    let progress = PhaseProgress {
        phase_id: phase_id.to_string(),
        total_goals: stats.total,
        done_goals: stats.done,
        pct: (stats.done as f64 / stats.total as f64 * 100.0),
    };

    // Store in phase metadata
    store.db.update(("phase", phase_id))
        .merge(json!({"progress": progress}))
        .await?;

    Ok(progress)
}
```

### Phase 3: Day → Closure Check

**When:** End of day (manual or scheduled)
**Then:** Check if required goals were completed
**Implementation:**
```rust
pub async fn check_day_completion(day_id: &str, store: &SurrealStore) -> Result<DayOutcome> {
    let mut response = store.db.query(
        "SELECT day_goal.goal_id, goal.status
         FROM day_goal
         INNER JOIN goal ON day_goal.goal_id = goal.id
         WHERE day_goal.day_id = $day AND day_goal.required = true"
    ).bind(("day", day_id)).await?;

    let required_goals: Vec<DayGoalStatus> = response.take(0)?;
    let all_complete = required_goals.iter().all(|g| g.status == "done");

    let outcome = DayOutcome {
        day_id: day_id.to_string(),
        required_goals: required_goals.len(),
        completed_goals: required_goals.iter().filter(|g| g.status == "done").count(),
        success: all_complete,
        timestamp: Utc::now(),
    };

    // Store outcome
    store.db.update(("day", day_id))
        .merge(json!({"outcome": outcome, "closed_at": outcome.timestamp}))
        .await?;

    // Generate retrospective prompt if failed
    if !all_complete {
        store.log_event(&Event::new(
            "day", day_id, EventAction::Update,
            "system",
            json!({"type": "day_incomplete", "outcome": outcome})
        )).await?;
    }

    Ok(outcome)
}
```

---

## Proposed Implementation Plan

### Step 1: Add Consequence Hooks (1-2 hours)

**File:** `metatheos-core/src/store/consequences.rs` (NEW)

```rust
pub struct ConsequenceEngine {
    store: Arc<SurrealStore>,
}

impl ConsequenceEngine {
    pub async fn on_work_item_completed(&self, item_id: &str) -> Result<Vec<Consequence>> {
        // Check if goal is ready to complete
    }

    pub async fn on_goal_status_changed(&self, goal_id: &str) -> Result<Vec<Consequence>> {
        // Update phase progress
        // Check phase completion
    }

    pub async fn on_day_created(&self, day_id: &str) -> Result<Vec<Consequence>> {
        // Initialize day tracking
    }
}

pub enum Consequence {
    Notification { message: String, action: Option<String> },
    StateUpdate { entity_type: String, entity_id: String, field: String, value: Value },
    EventLog { event: Event },
}
```

### Step 2: Wire Consequence Engine into Commands (1 hour)

**Modify:** `metatheos-gui/src-tauri/src/commands.rs`

```rust
pub async fn set_work_item_status(...) {
    // Existing: validate, update, save
    store.update_work_item(&item).await?;

    // NEW: Check consequences
    if matches!(new_status, WorkItemStatus::Done) {
        let consequences = consequence_engine.on_work_item_completed(&item.id).await?;
        for consequence in consequences {
            // Emit to UI via events, update DB, etc.
        }
    }

    Ok(item.into())
}
```

### Step 3: Add Progress Queries (1 hour)

**File:** `metatheos-core/src/store/queries.rs` (NEW)

```rust
pub async fn get_phase_progress(phase_id: &str, db: &Surreal<Db>) -> Result<PhaseProgress> { ... }
pub async fn get_day_outcome(day_id: &str, db: &Surreal<Db>) -> Result<DayOutcome> { ... }
pub async fn get_goal_task_completion(goal_id: &str, db: &Surreal<Db>) -> Result<TaskCompletion> { ... }
```

### Step 4: Surface Consequences in UI (2 hours)

**Add to GUI:**
- Phase progress bars (X/Y goals complete, Z%)
- Day outcome badges (Success/Incomplete with details)
- Goal completion prompts ("All tasks done - complete goal?")
- Notification panel for system-generated insights

---

## Success Criteria

After implementing consequences, the system should:

1. ✅ **Auto-detect completion readiness**: "All tasks done, mark goal as complete?"
2. ✅ **Show progress aggregation**: "Phase 1: 5/7 goals done (71%)"
3. ✅ **Close days with outcomes**: "Day 2026-01-04: Success (2/2 required goals)"
4. ✅ **Surface blockers**: "Goal G-042 blocked by 3 incomplete dependencies"
5. ✅ **Generate insights from events**: "You've completed 12 tasks this week"

---

## Bottom Line

**Current state:** Metatheos is a data collection tool with no behavioral loop.
**Required state:** Metatheos is a governance engine that responds to reality.

**Effort to fix:** ~6-8 hours of focused work
**Impact:** System goes from "for show" to "real"

**Next action:** Implement Phase 1 (Task → Goal cascade) as proof of concept.

---

**Status:** Audit Complete
**Recommendation:** Implement consequences layer immediately
**Priority:** Critical - without this, the system has no value beyond data storage
