# Timeline View Implementation Report

**Date:** 2026-01-03
**Feature:** Timeline View - Read-only observational surface
**Status:** ✅ Complete

---

## Executive Summary

The Timeline View has been successfully implemented as a **read-only, observational surface** that merges Events and Annotations into a single chronological stream. This feature provides forensic and reflective capabilities, answering the question: **"What actually happened over time, and what was said about it?"**

The implementation strictly adheres to the DB-first architecture and introduces **no schema changes, migrations, or new domain abstractions**.

---

## Purpose

The Timeline View serves as a **non-authoritative, contextual layer** that:

1. **Observes** changes to entities over time via the `event` table
2. **Surfaces** human and AI commentary via the `annotation` table
3. **Merges** both streams into a chronological view
4. **Complements** (not replaces) the dashboard, goal views, and work item management

### What Timeline Is NOT

- ❌ Not a task manager
- ❌ Not an editor
- ❌ Not a dashboard replacement
- ❌ Not authoritative (events and annotations are append-only)
- ❌ Does not trigger AI or summarization
- ❌ Does not modify data

---

## Scope

### Read-Only Operations

The Timeline View provides **four scoped read-only commands**:

1. **`get_timeline_for_day(day_id)`** - View events and annotations for a specific day
2. **`get_timeline_for_goal(goal_id)`** - View events and annotations for a specific goal
3. **`get_timeline_for_work_item(work_item_id)`** - View events and annotations for a specific work item
4. **`get_timeline_for_phase(phase_id)`** - View events and annotations for a specific phase

### Data Sources

Timeline queries pull from **two canonical tables**:

- **`event`** - Audit trail of all mutations (create, update, complete, reopen, link, delete)
- **`annotation`** - Free-form notes attached to any entity (user or AI authored)

### Display Format

Timeline items are returned as a normalized DTO:

```rust
pub struct TimelineItemDto {
    pub kind: String,       // "event" or "annotation"
    pub timestamp: String,  // RFC3339 timestamp
    pub title: String,      // Summary for events, first line for annotations
    pub body: String,       // Payload for events, full content for annotations
    pub entity_type: String,
    pub entity_id: String,
    pub author: Option<String>, // "user", "system", or "ai"
}
```

Items are **sorted by timestamp descending** (newest first).

---

## Implementation Details

### Backend Changes

#### 1. Tauri Commands ([commands.rs:3311-3613](metatheos-gui/src-tauri/src/commands.rs#L3311-L3613))

Added four read-only commands:

- `get_timeline_for_day`
- `get_timeline_for_goal`
- `get_timeline_for_work_item`
- `get_timeline_for_phase`

Each command:
1. Fetches events from the `event` table filtered by `entity_type` and `entity_id`
2. Fetches annotations using the existing `store.get_annotations()` method
3. Normalizes both into `TimelineItemDto` format
4. Sorts by timestamp descending
5. Returns the merged list

#### 2. Command Registration ([main.rs:181-185](metatheos-gui/src-tauri/src/main.rs#L181-L185))

Registered the timeline commands in the Tauri invoke handler:

```rust
// Timeline Commands (Phase 5) - Read-only observational surface
commands::get_timeline_for_day,
commands::get_timeline_for_goal,
commands::get_timeline_for_work_item,
commands::get_timeline_for_phase,
```

### Frontend Changes

#### 1. Timeline Component ([Timeline.svelte](metatheos-gui/src/lib/Timeline.svelte))

Created a new Svelte component following the existing `AnnotationPanel.svelte` pattern:

**Features:**
- Collapsible panel with configurable heading
- Visual distinction between events (🧱 blue) and annotations (📝 purple)
- Displays timestamp, author badge (User/AI), and scope metadata
- Expandable body for annotations
- Read-only (no add/edit/delete functionality)
- Maximum height with scroll overflow
- Loading and error states

**Props:**
- `scopeType`: "day", "goal", "work_item", or "phase"
- `scopeId`: ID of the entity
- `heading`: Custom panel heading (default: "Timeline")
- `collapsedInitially`: Whether to start collapsed (default: false)
- `compact`: Compact mode flag (default: false)

#### 2. Day Dashboard Integration ([CurrentDay.svelte:7,249-251](metatheos-gui/src/lib/CurrentDay.svelte#L7,L249-L251))

Added Timeline to the Day Dashboard below the daily note editor:

```svelte
<Timeline
  scopeType="day"
  scopeId={date}
  heading="Day Timeline"
  collapsedInitially={true}
/>
```

#### 3. Goal Detail Integration ([GoalDetail.svelte:6,159-164](metatheos-gui/src/lib/GoalDetail.svelte#L6,L159-L164))

Added Timeline to the Goal Detail page, positioned after the Annotation Panel:

```svelte
<Timeline
  heading="Goal Timeline"
  scopeType="goal"
  scopeId={detail.goal.id}
  collapsedInitially={true}
/>
```

---

## Why Timeline is Non-Authoritative

The Timeline View is **observational only** because:

1. **Events** are logged by the system automatically—they are immutable facts
2. **Annotations** are additive commentary—they do not change the underlying data
3. **Timeline queries** do not write, update, or delete anything
4. **Timeline display** does not infer meaning, collapse records, or auto-link entities
5. **AI content** only appears if already stored in `annotation` or `ai_run` tables

The Timeline **complements authoritative views** (Dashboard, Goals, Work Items) by providing:
- **Context** for why changes were made
- **Forensics** for debugging state transitions
- **Reflection** for understanding project history

---

## How Timeline Complements Existing Views

| View | Purpose | Timeline's Role |
|------|---------|-----------------|
| **Dashboard** | Current state, metrics, active goals | Shows historical context of how current state was reached |
| **Goal Explorer** | Browse and filter goals | Provides audit trail of goal changes and notes |
| **Goal Detail** | Work item execution tree | Shows why decisions were made and what changed when |
| **Day Wizard** | Daily execution planning | Reveals past day activities and annotations |

Timeline **does not replace** any existing functionality—it adds **temporal and contextual depth**.

---

## Design Constraints Adhered To

✅ **No schema changes** - Uses existing `event` and `annotation` tables
✅ **No migrations** - No database structure modifications
✅ **No new domain abstractions** - Reuses `Event` and `Annotation` types
✅ **No markdown export** - Timeline is view-only, no file operations
✅ **No async side effects** - Read-only queries, no writes or triggers
✅ **No AI triggering** - Timeline passively displays existing data
✅ **Non-blocking** - Timeline loads asynchronously, never blocks navigation

---

## Testing Guidance

### Manual Testing Steps

1. **Day Timeline:**
   - Navigate to "Current Day" view
   - Scroll to the Timeline panel (collapsed by default)
   - Expand to see events and annotations for today's date
   - Verify events show create/update actions
   - Verify annotations show user/AI notes

2. **Goal Timeline:**
   - Navigate to "Goal Explorer"
   - Select any goal to open Goal Detail
   - Scroll to Timeline panel (below annotations)
   - Expand to see goal-specific events and annotations
   - Verify timeline shows goal status changes

3. **Empty State:**
   - View timeline for a brand new day or goal
   - Verify "No timeline entries yet" message appears
   - Verify no errors are thrown

4. **Error Handling:**
   - Test with invalid IDs (should gracefully handle)
   - Test with database connection issues (should show error message)

### Expected Behavior

- Timeline should load **independently** without blocking other UI
- Items should be **sorted newest first**
- Events should display action + entity type (e.g., "create day 2026-01-03")
- Annotations should show full content with author badge
- Timestamps should be formatted in local time

---

## Files Modified

### Backend (Rust)
1. [metatheos-gui/src-tauri/src/commands.rs](metatheos-gui/src-tauri/src/commands.rs) - Added 4 timeline commands
2. [metatheos-gui/src-tauri/src/main.rs](metatheos-gui/src-tauri/src/main.rs) - Registered timeline commands

### Frontend (Svelte)
3. [metatheos-gui/src/lib/Timeline.svelte](metatheos-gui/src/lib/Timeline.svelte) - New component (created)
4. [metatheos-gui/src/lib/CurrentDay.svelte](metatheos-gui/src/lib/CurrentDay.svelte) - Added Timeline to day view
5. [metatheos-gui/src/lib/GoalDetail.svelte](metatheos-gui/src/lib/GoalDetail.svelte) - Added Timeline to goal detail

---

## Future Enhancements (Out of Scope)

The following were **intentionally excluded** from this implementation per design constraints:

- ❌ Timeline filtering/search (could be added later)
- ❌ Export to markdown (violates read-only constraint)
- ❌ Inline editing of annotations (violates read-only constraint)
- ❌ AI summarization of timeline (violates passive observation rule)
- ❌ Cross-entity timeline (e.g., all events for a phase + its goals)

---

## Conclusion

The Timeline View successfully provides a **forensic and reflective tool** for understanding "what happened and why" across days, goals, work items, and phases. It strictly adheres to the DB-first architecture, maintains non-authoritative status, and complements (rather than replaces) existing views.

The implementation is **production-ready** and requires no schema changes or data migrations.

---

**End of Report**
