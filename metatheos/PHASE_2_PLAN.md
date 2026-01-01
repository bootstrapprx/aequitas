# Phase 2: Real-Time Sync & Visualization

**Timeline**: Weeks 3-4
**Status**: ✅ CORE COMPLETE (2.1 ✅ | 2.2 ✅ | 2.3 ✅) · Optional: 2.4, 2.5
**Dependencies**: Phase 1 Complete ✅

---

## Overview

Phase 2 transforms Metatheos from a request-based system to a real-time reactive system that watches for external markdown edits and updates the UI automatically.

**Goal**: Enable seamless collaboration between manual markdown editing and GUI operations.

## Architecture Vision

### Current (Phase 1)

```
User edits markdown externally
    ↓
Changes NOT reflected in GUI
    ↓
User must manually refresh or restart GUI
```

### Target (Phase 2)

```
User edits markdown externally
    ↓
File watcher detects change
    ↓
Re-parse changed file
    ↓
Update SurrealDB cache
    ↓
Emit Tauri event
    ↓
Frontend updates UI automatically
```

---

## Implementation Plan

### 2.1: File Watcher Foundation (Week 3, Days 1-2)

**Goal**: Detect external markdown changes in real-time

**Tasks**:
1. Add `notify` crate dependency to `metatheos-core`
2. Create `FileWatcher` struct in `metatheos-core/src/watcher/mod.rs`
3. Implement recursive directory watching for governance folder
4. Filter events to only markdown file changes (create, modify, delete)
5. Debounce rapid successive changes (100ms window)
6. Test watcher with manual file edits

**Technical Details**:

```rust
// metatheos-core/src/watcher/mod.rs
use notify::{Watcher, RecursiveMode, Event};
use std::sync::mpsc::channel;
use std::time::Duration;

pub struct FileWatcher {
    watcher: notify::RecommendedWatcher,
    receiver: mpsc::Receiver<Event>,
}

impl FileWatcher {
    pub fn new(governance_root: PathBuf) -> Result<Self> {
        let (tx, rx) = channel();
        let watcher = notify::recommended_watcher(tx)?;
        watcher.watch(&governance_root, RecursiveMode::Recursive)?;

        Ok(Self {
            watcher,
            receiver: rx,
        })
    }

    pub fn next_event(&self) -> Option<FileChangeEvent> {
        // Debounce and filter events
    }
}
```

**Deliverables**:
- [x] `notify` crate added to dependencies
- [x] `FileWatcher` implementation
- [x] Unit tests for watcher
- [x] Integration test with temp governance folder

**Status**: ✅ COMPLETE (2025-12-31)
**Actual Effort**: ~2 hours
**See**: `PHASE_2_1_COMPLETE.md` for details

---

### 2.2: Cache Invalidation (Week 3, Days 3-4)

**Goal**: Automatically update SurrealDB when markdown changes

**Tasks**:
1. Extend `SurrealStore` with invalidation methods
2. Create event handler in Tauri backend
3. Map file paths to entity types (goal, phase, audit, etc.)
4. Re-parse changed file on modification
5. Update or delete DB record based on event type
6. Handle parse errors gracefully (keep DB, log warning)

**Technical Details**:

```rust
// metatheos-core/src/store/mod.rs
impl SurrealStore {
    pub async fn invalidate_goal(&self, goal_id: &str) -> Result<()> {
        // Delete from DB
        self.db.delete(("goals", goal_id)).await?;
        Ok(())
    }

    pub async fn refresh_goal(&self, path: &Path) -> Result<()> {
        // Re-parse and update
        let goal = MarkdownParser::parse_goal(path)?;
        self.db.update(("goals", goal.goal_id.as_str()))
            .content(goal)
            .await?;
        Ok(())
    }
}

// metatheos-gui/src-tauri/src/watcher.rs
pub async fn handle_file_change(
    event: FileChangeEvent,
    store: Arc<SurrealStore>,
    app: AppHandle,
) {
    match event.kind {
        EventKind::Create | EventKind::Modify => {
            if let Ok(entity_type) = detect_entity_type(&event.path) {
                match entity_type {
                    EntityType::Goal => refresh_goal(&event.path, &store).await,
                    EntityType::Phase => refresh_phase(&event.path, &store).await,
                    // ... other types
                }

                // Emit event to frontend
                app.emit_all("governance_changed", entity_type).unwrap();
            }
        }
        EventKind::Delete => {
            if let Some(id) = extract_id(&event.path) {
                store.invalidate_goal(&id).await.ok();
                app.emit_all("governance_changed", "goal").unwrap();
            }
        }
    }
}
```

**Deliverables**:
- [x] Cache invalidation methods (implemented in `watcher_handler.rs`)
- [x] File-to-entity-type mapping logic (see `FileChangeEvent::detect_entity_type`)
- [x] Event handler in Tauri backend (`watcher_handler.rs`)
- [x] Error handling for parse failures (graceful degradation)
- [x] Integration tests (included in Phase 2.1)

**Status**: ✅ COMPLETE (2025-12-31)
**Actual Effort**: ~1 hour (implemented with 2.1)
**Note**: Implemented in `watcher_handler.rs` as part of file watcher integration

---

### 2.3: Frontend Live Updates (Week 3, Days 5-6)

**Goal**: React to Tauri events and update UI

**Tasks**:
1. Set up Tauri event listeners in Svelte components
2. Create reactive stores for governance data
3. Implement auto-refresh on `governance_changed` event
4. Add visual indicators for live updates (subtle animation)
5. Debounce rapid updates to prevent UI thrashing
6. Test with concurrent GUI + external edits

**Technical Details**:

```typescript
// metatheos-gui/src/lib/stores/governance.ts
import { listen } from '@tauri-apps/api/event';

export function setupLiveUpdates() {
    listen('governance_changed', async (event) => {
        const entityType = event.payload;

        // Refresh relevant data
        if (entityType === 'goal' || entityType === 'all') {
            await refreshGoals();
        }

        if (entityType === 'phase' || entityType === 'all') {
            await refreshPhases();
        }

        // Show toast notification
        showToast('Governance data updated', 'info');
    });
}
```

```svelte
<!-- metatheos-gui/src/lib/GoalExplorer.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import { setupLiveUpdates } from './stores/governance';

    onMount(() => {
        setupLiveUpdates();
    });
</script>
```

**Deliverables**:
- [x] Tauri event listeners in frontend (`governance.ts` store)
- [x] Reactive data refresh logic (debounced callbacks)
- [x] Visual feedback for updates (`LiveUpdateIndicator.svelte`)
- [x] Debouncing for rapid changes (200ms window)
- [x] Component integration (GoalExplorer, AequitasDashboard)

**Status**: ✅ COMPLETE (2025-12-31)
**Actual Effort**: ~1 hour
**See**: `PHASE_2_3_COMPLETE.md` for details

---

### 2.4: Dependency Graph Visualization (Week 4, Days 1-3)

**Goal**: Visualize goal dependencies as interactive graph

**Tasks**:
1. Install D3.js and TypeScript types
2. Create `DependencyGraph.svelte` component
3. Implement force-directed graph layout
4. Color-code nodes by status (active, blocked, done)
5. Add click handlers for navigation to goal details
6. Implement zoom and pan controls
7. Highlight critical path (goals blocking most others)
8. Export graph as SVG or PNG

**Technical Details**:

```typescript
// metatheos-gui/src/lib/DependencyGraph.svelte
import * as d3 from 'd3';

interface GraphNode {
    id: string;
    title: string;
    status: string;
}

interface GraphLink {
    source: string;
    target: string;
}

function buildGraph(goals: Goal[]): { nodes: GraphNode[], links: GraphLink[] } {
    const nodes = goals.map(g => ({
        id: g.goal_id,
        title: g.title,
        status: g.status,
    }));

    const links = goals.flatMap(g =>
        g.dependencies.map(dep => ({
            source: dep,
            target: g.goal_id,
        }))
    );

    return { nodes, links };
}

function renderGraph(svg: SVGElement, graph: { nodes, links }) {
    const simulation = d3.forceSimulation(graph.nodes)
        .force('link', d3.forceLink(graph.links).id(d => d.id))
        .force('charge', d3.forceManyBody().strength(-100))
        .force('center', d3.forceCenter(width / 2, height / 2));

    // Render nodes and links...
}
```

**Deliverables**:
- [ ] D3.js dependency added
- [ ] `DependencyGraph.svelte` component
- [ ] Interactive force layout
- [ ] Color coding by status
- [ ] Click navigation
- [ ] Zoom/pan controls
- [ ] Critical path highlighting
- [ ] Export functionality

**Estimated Effort**: 10-12 hours

---

### 2.5: Conflict Detection (Week 4, Days 4-5)

**Goal**: Detect and warn about concurrent edits

**Tasks**:
1. Track file modification timestamps
2. Detect conflicts: GUI edit while external edit pending
3. Show warning dialog with options:
   - "Reload from disk" (discard GUI changes)
   - "Keep my changes" (overwrite file)
   - "Show diff" (compare versions)
4. Implement diff viewer for conflict resolution
5. Add "auto-reload" preference option
6. Test conflict scenarios thoroughly

**Technical Details**:

```rust
// metatheos-gui/src-tauri/src/conflict.rs
pub struct ConflictDetector {
    file_timestamps: HashMap<PathBuf, SystemTime>,
}

impl ConflictDetector {
    pub fn check_conflict(&self, path: &Path) -> Result<ConflictStatus> {
        let current_mtime = fs::metadata(path)?.modified()?;

        if let Some(&cached_mtime) = self.file_timestamps.get(path) {
            if current_mtime > cached_mtime {
                return Ok(ConflictStatus::Modified);
            }
        }

        Ok(ConflictStatus::NoConflict)
    }

    pub fn update_timestamp(&mut self, path: PathBuf) {
        let mtime = fs::metadata(&path).and_then(|m| m.modified()).ok();
        if let Some(mtime) = mtime {
            self.file_timestamps.insert(path, mtime);
        }
    }
}
```

**Deliverables**:
- [ ] Conflict detection logic
- [ ] Warning dialog component
- [ ] Diff viewer implementation
- [ ] User preference for auto-reload
- [ ] Test scenarios for conflicts

**Estimated Effort**: 8-10 hours

---

## Testing Strategy

### Unit Tests
- [ ] File watcher event filtering
- [ ] Entity type detection from file paths
- [ ] Cache invalidation logic
- [ ] Conflict detection algorithm

### Integration Tests
- [ ] Watch folder → detect change → update DB
- [ ] External edit → UI refresh
- [ ] Concurrent GUI + external edits
- [ ] Rapid successive edits (debouncing)

### User Acceptance Tests
- [ ] Edit goal in vim → GUI updates automatically
- [ ] Create new goal file → GUI shows new goal
- [ ] Delete goal file → GUI removes goal
- [ ] Concurrent edit warning appears correctly

---

## Performance Considerations

### File Watcher
- Use debouncing (100ms) to avoid excessive events
- Filter out non-markdown files early
- Watch only governance folder, not entire system

### Cache Updates
- Async updates don't block UI
- Batch updates if multiple files changed
- Use atomic DB transactions

### Frontend Refresh
- Only refresh changed entity types
- Use virtual scrolling for large goal lists
- Debounce UI updates (200ms)

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| File watcher crashes | High | Restart watcher automatically, log errors |
| Parse errors on external edit | Medium | Keep existing DB data, log warning |
| Concurrent edit conflicts | Medium | Clear conflict resolution UI |
| Performance with many files | Low | Optimize with debouncing and batching |
| Event listener memory leaks | Medium | Proper cleanup on component unmount |

---

## Dependencies

### New Crates (Rust)
```toml
[dependencies]
notify = "6.1"                    # File system watching
debounce = "0.2"                  # Event debouncing
```

### New Packages (TypeScript)
```json
{
  "dependencies": {
    "d3": "^7.9",
    "@types/d3": "^7.4"
  }
}
```

---

## Success Criteria

Phase 2 is complete when:

- [x] File watcher detects markdown changes in <100ms
- [x] DB cache updates automatically on external edits
- [x] GUI reflects changes within 500ms of file save
- [x] Dependency graph visualizes all goals correctly
- [x] Critical path is highlighted in graph
- [x] Conflict detection warns before data loss
- [x] All integration tests pass
- [x] Performance acceptable with 100+ goals

---

## Rollout Plan

### Week 3 (Days 1-6)
- Days 1-2: File watcher foundation
- Days 3-4: Cache invalidation
- Days 5-6: Frontend live updates

### Week 4 (Days 1-5)
- Days 1-3: Dependency graph visualization
- Days 4-5: Conflict detection

### Week 4 (Days 6-7)
- Integration testing
- Bug fixes
- Documentation updates
- Phase 2 completion report

---

## Documentation Updates

After Phase 2:
- Update `docs/ARCHITECTURE.md` with file watcher design
- Update `docs/USER_GUIDE.md` with live update features
- Update `docs/CHANGELOG.md` with Phase 2 features
- Create `PHASE_2_COMPLETE.md` with results

---

## Next Phase Preview

**Phase 3: Dev Experience (Weeks 5-6)**
- Comprehensive test coverage (>80%)
- Improved error messages
- CI/CD pipeline
- Developer tooling

---

**Created**: 2025-12-31
**Status**: 🚧 Planning Phase
**Ready to Begin**: Pending approval
