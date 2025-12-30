# Interactive Features — Relationship Navigation & Daily Cross-References

**Date:** 2025-12-29
**Status:** ✅ Complete
**Goal:** Enable interactive exploration of governance relationships

## Overview

Building on the Information Enrichment foundation, these features make the governance interface fully interactive — allowing users to navigate dependency graphs, explore relationships, and view daily note cross-references through intuitive UI interactions.

## Implemented Features

### 1. Relationship Highlighting (Hover)

**Trigger:** Mouse hover over any goal card

**Behavior:**
- **Hovered goal:** Highlighted with primary blue ring (`ring-2 ring-primary-500`)
- **Dependencies (→):** Highlighted with blue ring and background (`ring-2 ring-blue-400 bg-blue-50`)
- **Reverse dependencies (←):** Highlighted with green ring and background (`ring-2 ring-green-400 bg-green-50`)

**Visual Example:**
```
[Hover on goal-p5-api]
  → Dependencies: goal-p4-db, goal-p3-auth ← highlighted in BLUE
  ← Reverse deps: goal-p6-frontend ← highlighted in GREEN
  → Hovered goal: goal-p5-api ← highlighted in PRIMARY
```

**Implementation:**
```javascript
function handleGoalHover(goal) {
  hoveredGoalId = goal.goal_id
  highlightedDependencies = new Set(goal.dependencies)
  highlightedReverseDeps = new Set(goal.reverse_dependencies)
}

function getHighlightClass(goalId) {
  if (hoveredGoalId === goalId) {
    return 'ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/20'
  }
  if (highlightedDependencies.has(goalId)) {
    return 'ring-2 ring-blue-400 bg-blue-50 dark:bg-blue-900/20'
  }
  if (highlightedReverseDeps.has(goalId)) {
    return 'ring-2 ring-green-400 bg-green-50 dark:bg-green-900/20'
  }
  return ''
}
```

**Use Case:**
When planning work, hover over a goal to instantly see:
- What it depends on (must be done first)
- What depends on it (will be unblocked when done)

---

### 2. Dependency Navigation (Click to Scroll)

**Trigger:** Click on any dependency badge in the relationship info row

**Behavior:**
- Smooth scrolls to the target goal (even across phase boundaries)
- Flashes a primary ring for 2 seconds to highlight the target
- Works for both forward dependencies (→) and reverse dependencies (←)

**UI Elements:**

**Forward Dependencies (→):**
```svelte
{#each goal.dependencies.slice(0, 3) as depId}
  <button
    class="px-1 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800/40 transition-colors"
    on:click|stopPropagation={() => scrollToGoal(depId)}
    title="Click to scroll to {depId}"
  >
    {depId}
  </button>
{/each}
{#if goal.dependencies.length > 3}
  <span>+{goal.dependencies.length - 3}</span>
{/if}
```

**Reverse Dependencies (←):**
```svelte
{#each goal.reverse_dependencies.slice(0, 2) as revDepId}
  <button
    class="px-1 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-800/40 transition-colors"
    on:click|stopPropagation={() => scrollToGoal(revDepId)}
  >
    {revDepId}
  </button>
{/each}
```

**Display Logic:**
- Shows first 3 dependencies (forward) with clickable badges
- Shows first 2 reverse dependencies with clickable badges
- Displays "+N" for additional items beyond the limit
- Color-coded: Blue for dependencies, Green for reverse dependencies

**Implementation:**
```javascript
function scrollToGoal(goalId) {
  const element = document.getElementById(`goal-${goalId}`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    // Flash the element briefly
    element.classList.add('ring-2', 'ring-primary-500')
    setTimeout(() => {
      element.classList.remove('ring-2', 'ring-primary-500')
    }, 2000)
  }
}
```

**Use Case:**
When reviewing a blocked goal:
1. See "⛔ Blocked by 2" warning
2. Click on blocker badge (e.g., `goal-p4-db`)
3. Instantly scroll to that goal
4. Check its status and timeline
5. Navigate dependency chain as needed

---

### 3. Daily Note Cross-References (Modal)

**Trigger:** Click on "📅 N daily note(s)" badge

**Behavior:**
- Opens modal showing all daily notes that reference this goal
- Dates are sorted newest first (reverse chronological)
- Modal has dark overlay with click-to-close behavior
- Each date is displayed with calendar icon

**Modal UI:**
```
┌────────────────────────────────────────────────┐
│  Daily Notes Referencing goal-p5-api        ✕  │
├────────────────────────────────────────────────┤
│  This goal is referenced in the following      │
│  daily notes:                                  │
│                                                │
│  📅 2025-12-29                                 │
│  📅 2025-12-28                                 │
│  📅 2025-12-27                                 │
│  📅 2025-12-20                                 │
│                                                │
│                                    [Close]      │
└────────────────────────────────────────────────┘
```

**Implementation:**
```svelte
{#if goal.daily_references.length > 0}
  <button
    class="flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-0.5 rounded transition-colors"
    on:click|stopPropagation={() => openDailyRefsModal(goal)}
    title="Click to see daily notes"
  >
    <span class="text-gray-600 dark:text-gray-400">📅</span>
    <span class="text-gray-700 dark:text-gray-300 underline decoration-dotted">
      {goal.daily_references.length} daily note(s)
    </span>
  </button>
{/if}

<!-- Modal -->
{#if showDailyRefsModal && selectedGoalForDailyRefs}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" on:click={closeDailyRefsModal}>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6" on:click|stopPropagation>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold">
          Daily Notes Referencing {selectedGoalForDailyRefs.goal_id}
        </h3>
        <button on:click={closeDailyRefsModal}>✕</button>
      </div>

      <div class="space-y-2 max-h-96 overflow-y-auto">
        {#each selectedGoalForDailyRefs.daily_references.sort().reverse() as date}
          <div class="flex items-center gap-2 p-2 rounded bg-gray-50 dark:bg-gray-700">
            📅 <span class="font-mono">{date}</span>
          </div>
        {/each}
      </div>
    </div>
  </div>
{/if}
```

**Use Case:**
When investigating goal status:
1. See "📅 12 daily note(s)"
2. Click to open modal
3. Review dates: "This has been actively worked on for 2 weeks"
4. Identify gaps: "No activity Dec 20-27"

---

### 4. Done Status Lock

**Visual Indicator:** 🔒 icon appears in status badge for done goals

**Behavior:**
- Status change menu button is disabled when `goal.status === 'done'`
- Tooltip shows: "Done goals are locked"
- Prevents accidental regression from completed state
- Still allows editing via Edit button (for content updates)

**Implementation:**
```svelte
<!-- Status badge with lock icon -->
<span class="badge {getStatusBadge(goal.status)}">
  {#if goal.status === 'done'}
    🔒
  {/if}
  {goal.status}
</span>

<!-- Status change button with lock logic -->
<button
  on:click={() => toggleStatusMenu(goal.goal_id)}
  disabled={updatingGoalId === goal.goal_id || devMode || goal.status === 'done'}
  title={goal.status === 'done' ? 'Done goals are locked' : 'Change status'}
>
  ⋮
</button>

<!-- Menu only opens if not done -->
{#if showStatusMenu === goal.goal_id && goal.status !== 'done'}
  <div class="status-menu">...</div>
{/if}
```

**Design Intent:**
Per governance best practices:
- Done = Delivered and verified
- Should not regress without explicit action (via Edit → change frontmatter)
- Prevents accidental clicks from undoing completed work

---

## State Management

**Relationship Highlighting:**
```javascript
let hoveredGoalId = null
let highlightedDependencies = new Set()
let highlightedReverseDeps = new Set()
```

**Daily References Modal:**
```javascript
let showDailyRefsModal = false
let selectedGoalForDailyRefs = null
```

**Event Handlers:**
```javascript
on:mouseenter={() => handleGoalHover(goal)}
on:mouseleave={handleGoalLeave}
on:click|stopPropagation={() => scrollToGoal(depId)}
on:click|stopPropagation={() => openDailyRefsModal(goal)}
```

---

## User Experience Improvements

### Before (Information Enrichment Only)
```
→ Depends: 3  ← 2 depend on this  📅 5 daily note(s)
```
- Shows counts
- No way to see what the dependencies are
- No way to navigate to them
- Can't see which daily notes

### After (Interactive Features)
```
→ Depends: 3  [goal-p4-db] [goal-p3-auth] [goal-p2-schema] +0
← 2 depend on this  [goal-p6-api] [goal-p7-ui] +0
📅 5 daily note(s) ← click to see dates
```
- Shows actual dependency IDs as clickable badges
- Click to navigate directly to dependency
- Hover to highlight entire relationship graph
- Click daily count to see all dates

---

## Accessibility Notes

The implementation includes several accessibility warnings from Svelte (ARIA roles, keyboard handlers). These are noted but not critical for the MVP:

- `<div>` with mouseenter/mouseleave should have ARIA role
- Click handlers should have keyboard equivalents
- Buttons should have aria-label

These can be addressed in a future accessibility pass without affecting functionality.

---

## Integration with Enrichment Data

These interactive features directly consume the enriched data from the backend:

**Backend provides:**
```rust
pub struct EnrichedGoalDto {
    pub dependencies: Vec<String>,           // → navigation targets
    pub reverse_dependencies: Vec<String>,   // ← navigation targets
    pub daily_references: Vec<String>,       // 📅 modal content
    pub blocked_by: Vec<String>,             // ⛔ shown inline
    pub completion_blocked: bool,            // 🚫 blocking indicator
    // ... other fields
}
```

**Frontend consumes:**
- `dependencies` → Blue clickable badges
- `reverse_dependencies` → Green clickable badges
- `daily_references` → Modal with dates
- `completion_blocked` → Disable done regression

---

## Testing Checklist

✅ **Relationship Highlighting:**
- [x] Hover on goal highlights self, deps, and reverse deps
- [x] Mouse leave clears all highlights
- [x] Correct color coding (primary/blue/green)

✅ **Dependency Navigation:**
- [x] Click on dependency badge scrolls to target
- [x] Scroll centers target in viewport
- [x] Flash effect draws attention to target
- [x] Works across phase boundaries

✅ **Daily References Modal:**
- [x] Click opens modal with dates
- [x] Dates sorted newest first
- [x] Click overlay closes modal
- [x] Click close button closes modal
- [x] Scrollable when many dates

✅ **Done Status Lock:**
- [x] 🔒 icon appears on done goals
- [x] Status menu button disabled for done
- [x] Tooltip explains "locked"
- [x] Edit button still works

---

## Next Steps (Optional Enhancements)

While the core governance interface is now complete, future enhancements could include:

1. **Dependency Graph Visualization**
   - Visual graph view of entire dependency tree
   - Click node to navigate to goal

2. **Daily Note Deep Links**
   - Click date in modal to open daily note
   - Highlight goal references in daily note content

3. **Batch Operations**
   - Multi-select goals
   - Bulk status updates

4. **Timeline View**
   - Gantt chart based on dependencies
   - Critical path highlighting

5. **Accessibility Improvements**
   - Keyboard navigation for all interactions
   - Screen reader support
   - Focus management

---

## Conclusion

The governance interface is now fully interactive and achieves the "control room" design intent:

✅ **Phase state understandable in seconds** — Summary panels
✅ **Blockers obvious without clicking** — Inline ⛔ warnings
✅ **Dependencies feel real** — Clickable badges, hover highlighting
✅ **Daily work is visible** — Cross-reference counts and modal
✅ **Navigation is effortless** — Click to scroll, smooth transitions

The combination of Information Enrichment (computed data) and Interactive Features (navigation/exploration) transforms Metatheos from a passive viewer into an active governance command center.
