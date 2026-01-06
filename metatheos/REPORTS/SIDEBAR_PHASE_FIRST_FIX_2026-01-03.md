# Sidebar Phase-First Fix

**Date:** 2026-01-03
**Type:** Critical Architectural Fix
**Status:** ✅ Complete

---

## Executive Summary

The sidebar has been refactored from a **goal-centric** navigation model to a **phase-first** model, aligning the UI with the canonical database architecture where **Phases → Goals → Work Items → Days**. This fixes a systemic bug where the interface contradicted the data model, creating mental model drift and confusion.

---

## Problem Statement

### What Was Wrong

The sidebar previously treated **Goals as a top-level concept**, presenting them independently of phases:

```javascript
// BEFORE (Wrong)
const views = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "explorer", label: "Explorer", icon: "📁" },
  { id: "daily", label: "Daily", icon: "📅" },
  { id: "current-day", label: "Current Day", icon: "☀️" },
  { id: "goals", label: "Goals", icon: "🎯" },  // ← Implied top-level!
  { id: "audits", label: "Audits", icon: "🔍" },
  { id: "prompts", label: "Prompts", icon: "💡" },
  { id: "assistant", label: "Assistant", icon: "🤖" },
];
```

**This was architecturally wrong because:**

1. **Goals exist only within phases** (enforced by DB schema: `goal.phase_id`)
2. **Work items exist only within goals** (enforced by `work_item.goal_id`)
3. **Days activate a phase + subset of goals** (enforced by Day Wizard)
4. **The sidebar implied goals were independent**, contradicting the canonical hierarchy

### Consequences

- Users saw "Goals" without understanding they were phase-scoped
- Mental model: "Goals are primary" (incorrect)
- Empty or confusing views when no active phase existed
- Cognitive dissonance between UI labels and system behavior
- Violated the canonical rule: **Phases define scope**

---

##Solution Applied

### Changes Made

#### 1. Phase-First Sidebar Navigation ([App.svelte:31-41](metatheos-gui/src/App.svelte#L31-L41))

**BEFORE:**
```javascript
const views = [
  { id: "goals", label: "Goals", icon: "🎯" },  // Top-level, no context
];
```

**AFTER:**
```javascript
const views = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "current-day", label: "Current Day", icon: "☀️" },
  { id: "phases", label: "Phases", icon: "📐", section: "structure" },
  { id: "goals", label: "Phase Goals", icon: "🎯", section: "structure" },  // ← Now scoped!
  { id: "explorer", label: "Files", icon: "📁", section: "tools" },
  { id: "daily", label: "Daily Notes", icon: "📅", section: "tools" },
  { id: "audits", label: "Audits", icon: "🔍", section: "tools" },
  { id: "prompts", label: "Prompts", icon: "💡", section: "tools" },
  { id: "assistant", label: "Assistant", icon: "🤖", section: "tools" },
];
```

**Key changes:**
- ✅ Added **"Phases"** view as first-class navigation
- ✅ Renamed "Goals" → **"Phase Goals"** to make scoping explicit
- ✅ Renamed "Explorer" → **"Files"** (clearer purpose)
- ✅ Renamed "Daily" → **"Daily Notes"** (clearer scope)
- ✅ Organized views into logical sections (`structure` vs `tools`)
- ✅ Reordered to put **Phases first** in the structure section

#### 2. Active Phase Context Display ([App.svelte:197-220](metatheos-gui/src/App.svelte#L197-L220))

Added a prominent **Active Phase badge** in the sidebar showing:
- Current phase title
- Current phase status
- Visual indication when no phase is active

```svelte
<div class="px-6 py-3 mb-2">
  <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 font-semibold mb-1">
    Active Phase
  </p>
  {#if activePhase}
    <div class="phase-badge">
      <span class="phase-badge-icon">📐</span>
      <div class="flex-1 min-w-0">
        <div class="font-semibold text-sm text-gray-900 dark:text-white truncate">
          {activePhase.title}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">
          {activePhase.status}
        </div>
      </div>
    </div>
  {:else}
    <div class="text-sm text-gray-400 dark:text-gray-500 italic">
      No active phase
    </div>
  {/if}
</div>
```

#### 3. Phase Manager Component ([PhaseManager.svelte](metatheos-gui/src/lib/PhaseManager.svelte))

Created a new **Phases** view that:
- Displays all phases as selectable cards
- Shows which phase is currently active
- Allows users to switch the active phase
- Explains phase-first architecture with educational copy

**Features:**
- Grid layout of phase cards
- Active phase highlighting
- Status badges (active, planned, closed)
- Click to set active phase
- Educational banner explaining "Phase-First Architecture"

#### 4. State Management ([App.svelte:28-29,112-134,162-177](metatheos-gui/src/App.svelte#L28-L29,L112-L134,L162-L177))

Added phase state management:

```javascript
let activePhase = null;
let allPhases = [];

async function initializeState() {
  // Load all phases
  allPhases = await invoke("get_all_phases");
  if (allPhases && allPhases.length > 0) {
    // Get or set active phase
    activePhase = await invoke("get_active_phase", { date: null });
    if (!activePhase) {
      const best = pickBestPhase(allPhases);
      if (best) {
        await invoke("set_active_phase_db", { phaseId: best.phase_id });
        activePhase = best;
      }
    }
  } else {
    activePhase = null;
  }
}

function handlePhaseChanged(event) {
  activePhase = event.detail.phase;
  // Optionally switch to goals view after selecting a phase
  if (currentView === "phases") {
    currentView = "goals";
  }
}
```

#### 5. Visual Section Dividers ([App.svelte:222-226,436-440](metatheos-gui/src/App.svelte#L222-L226,L436-L440))

Added section dividers in the sidebar to visually group related views:

```svelte
{#each views as view, i}
  {#if !sidebarCollapsed && i > 0 && views[i - 1].section !== view.section}
    <div class="nav-divider"></div>
  {/if}
  ...
{/each}
```

Dividers separate:
- **Core views** (Dashboard, Current Day)
- **Structure views** (Phases, Phase Goals)
- **Tools** (Files, Daily Notes, Audits, Prompts, Assistant)

---

## Assumptions Removed

### ❌ Old (Incorrect) Assumptions

1. **"Goals are top-level entities"** — Removed
2. **"Users can browse goals without phase context"** — Removed
3. **"The sidebar is just a flat list of views"** — Removed
4. **"Phase is an implementation detail"** — Removed

### ✅ New (Correct) Assumptions

1. **Phases are the structural spine**
2. **Goals always belong to a phase**
3. **Users must understand phase context to work effectively**
4. **Sidebar should reflect the canonical data hierarchy**

---

## How Phase-First is Enforced

### 1. **Sidebar Structure**

The sidebar now visually reinforces the hierarchy:
```
📊 Dashboard           (Overview)
☀️ Current Day         (Daily execution)
────────────────────── (section divider)
📐 Phases              (Structural spine - FIRST!)
🎯 Phase Goals         (Scoped by phase)
────────────────────── (section divider)
📁 Files              (Tools)
📅 Daily Notes
🔍 Audits
💡 Prompts
🤖 Assistant
```

### 2. **Active Phase Display**

The active phase is shown **immediately below the logo**, making it impossible to miss:
- Always visible in unexpanded sidebar
- Shows phase name + status
- Updates reactively when changed
- Shows "No active phase" as a clear signal

### 3. **Label Semantics**

Changed labels to reflect scoping:
- "Goals" → **"Phase Goals"** (explicit scope)
- "Explorer" → **"Files"** (clearer purpose)
- "Daily" → **"Daily Notes"** (clearer scope)

### 4. **Goal Explorer Behavior** (Already Correct)

The `GoalExplorer` component already enforces phase context:

```javascript
// From GoalExplorer.svelte:105-127
let activePhase = await invoke("get_active_phase", { date: null });
if (!activePhase) {
  const phases = await invoke("get_all_phases");
  if (phases && phases.length > 0) {
    activePhase = phases[0];
  }
}

if (activePhase) {
  const result = await invoke("get_goals_by_phase", {
    phase: activePhase.phase_id,  // ← Always phase-scoped!
  });
  goals = result;
} else {
  goals = [];
  toastMessage = "No phase available in DB.";
}
```

**This was already correct** — the fix was making the UI **visually communicate** what the backend was already enforcing.

### 5. **Phase Manager as Entry Point**

Users can now:
1. Click **"Phases"** in sidebar
2. See all available phases
3. Select a phase to set as active
4. Automatically navigate to **"Phase Goals"**
5. Work within that phase context

---

## Mental Model Alignment

### Before (Broken)

```
User sees:    Goals → (where's the phase?)
Data model:   Phase → Goal → WorkItem
Result:       Confusion, mismatch
```

### After (Fixed)

```
User sees:    Active Phase → Phase Goals → Work Items
Data model:   Phase → Goal → WorkItem
Result:       ✅ Aligned!
```

---

## Files Modified

### Frontend (Svelte)
1. [metatheos-gui/src/App.svelte](metatheos-gui/src/App.svelte)
   - Added phase state (`activePhase`, `allPhases`)
   - Reordered and renamed sidebar views
   - Added active phase display
   - Added section dividers
   - Added phase change handler
   - Updated `initializeState` to load phases
   - Added routing for "phases" view
   - Updated styles for phase badge and dividers

2. [metatheos-gui/src/lib/PhaseManager.svelte](metatheos-gui/src/lib/PhaseManager.svelte) — **NEW**
   - Phase selection interface
   - Grid of phase cards
   - Active phase highlighting
   - Educational copy about phase-first architecture

### Backend
**None** — This was purely a UI fix to align with existing backend behavior.

---

## Testing Guidance

### Manual Test Steps

1. **Start the application**
   - Verify "Active Phase" badge appears in sidebar
   - Verify phase title and status are shown
   - Verify sidebar shows "Phases" before "Phase Goals"

2. **Navigate to Phases view**
   - Click "Phases" in sidebar
   - Verify all phases are displayed as cards
   - Verify active phase is highlighted
   - Verify clicking a phase sets it as active
   - Verify automatic navigation to "Phase Goals" after selection

3. **Navigate to Phase Goals**
   - Verify label says "Phase Goals" (not just "Goals")
   - Verify goals are loaded for the active phase
   - Verify toast shows "Loaded goals for [Phase Name]"

4. **Test with no phase**
   - Remove all phases from DB (or use fresh install)
   - Verify "No active phase" message in sidebar
   - Verify "Phase Goals" view shows appropriate empty state

5. **Test section dividers**
   - Verify divider appears between "Current Day" and "Phases"
   - Verify divider appears between "Phase Goals" and "Files"
   - Verify dividers disappear when sidebar is collapsed

### Expected Behavior

- **Phase context is always visible** when sidebar is open
- **Labels reflect scoping** ("Phase Goals" not "Goals")
- **Navigation hierarchy** matches data hierarchy
- **No confusion** about what scope the user is working in

---

## Impact Assessment

### What Changed
- Sidebar navigation order
- View labels and semantics
- Active phase display
- Phase selection interface

### What Did NOT Change
- ❌ Database schema (no changes)
- ❌ Backend API commands (no changes)
- ❌ Goal loading logic (already correct)
- ❌ Day Wizard (already phase-aware)
- ❌ Any data or business logic

### Breaking Changes
**None** — This is a UI-only refactor that aligns the interface with existing backend behavior.

---

## Philosophy Enforced

This fix enforces the canonical Metatheos philosophy:

> **Phases define scope.**
> **Goals are commitments within phases.**
> **Work items execute goals.**
> **Days activate a phase and subset of goals.**

The sidebar now **visually and semantically reflects this hierarchy**, eliminating the mental model drift that occurred when the UI suggested goals were top-level entities.

---

## Future Considerations (Out of Scope)

The following were intentionally excluded:

- ❌ Phase editing/creation UI (use existing CRUD)
- ❌ Inline phase switching from Goal view
- ❌ Phase-based dashboard filtering
- ❌ Hierarchical sidebar (expandable phase → goals tree)

These could be added later but are not required to fix the core architectural issue.

---

## Conclusion

The sidebar is now **phase-first**, matching the DB architecture and enforcing the canonical mental model:

**Phase → Goal → WorkItem → Day**

Users now **see phases prominently**, understand that **goals belong to phases**, and cannot accidentally work in a phase-less context.

This eliminates the systemic bug where the UI contradicted the data model.

---

**End of Report**
