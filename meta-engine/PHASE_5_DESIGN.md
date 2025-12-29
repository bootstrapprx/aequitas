# Phase 5: Full CRUD Operations - Design Document

## Overview

Phase 5 adds complete Create, Read, Update, Delete (CRUD) capabilities to the Meta Engine, transforming it from a read-only governance viewer into a full-featured governance management tool.

**Status:** Design Phase
**Target:** Phase 5A - Writers and Commands
**Next:** Phase 5B - UI Components

## Goals

1. **Edit Goals** - Create, update, delete goals with markdown persistence
2. **Edit Phases** - Manage phase metadata and transitions
3. **Edit Daily Notes** - Full markdown editing with preview
4. **Maintain Governance Integrity** - Validate all changes, preserve structure
5. **Full Audit Trail** - Log all modifications
6. **Markdown-First** - All changes reflected in markdown files immediately

## Architecture

### Current State (Read-Only)

```
┌─────────────┐
│   Svelte    │
│     UI      │
└──────┬──────┘
       │ invoke(read commands)
       ▼
┌─────────────┐
│   Tauri     │
│  Commands   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ meta-core   │
│   Parser    │──────► Read markdown files
└─────────────┘
```

### Phase 5 Architecture (Full CRUD)

```
┌─────────────┐
│   Svelte    │
│     UI      │
│             │
│ - Editors   │
│ - Validators│
│ - Previews  │
└──────┬──────┘
       │ invoke(read/write commands)
       ▼
┌─────────────┐
│   Tauri     │
│  Commands   │
│             │
│ - CRUD ops  │
│ - Validation│
│ - Audit log │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│         meta-core               │
│                                 │
│  Parser ◄────► Writer           │
│    │              │             │
│    ▼              ▼             │
│  Goals         Goals            │
│  Phases        Phases           │
│  Daily         Daily            │
│                                 │
│  Validator ──► Checks integrity │
└─────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Markdown   │
│   Files     │
│             │
│ 01_GOALS/   │
│ 02_PHASES/  │
│ 03_DAILY/   │
└─────────────┘
```

## Phase 5A: Backend (Writers and Commands)

### 1. Writer Module

**Location:** `meta-core/src/writer/`

**Modules:**
- `mod.rs` - Export writer components
- `goal_writer.rs` - Write goal markdown files
- `phase_writer.rs` - Write phase markdown files
- `daily_writer.rs` - Write daily note markdown files
- `frontmatter.rs` - Serialize YAML frontmatter

**Key Traits:**

```rust
pub trait MarkdownWriter {
    fn write(&self, path: &Path, content: &str) -> Result<()>;
    fn backup(&self, path: &Path) -> Result<PathBuf>;
    fn validate(&self, content: &str) -> Result<()>;
}
```

### 2. Goal Writer

**Operations:**

```rust
pub struct GoalWriter {
    governance_root: PathBuf,
}

impl GoalWriter {
    // Create new goal
    pub fn create_goal(&self, goal: &Goal) -> Result<PathBuf> {
        // 1. Validate goal ID uniqueness
        // 2. Generate markdown with frontmatter
        // 3. Write to 01_GOALS/{goal_id}.md
        // 4. Create audit entry
    }

    // Update existing goal
    pub fn update_goal(&self, goal: &Goal) -> Result<()> {
        // 1. Backup existing file
        // 2. Validate changes
        // 3. Write updated markdown
        // 4. Create audit entry
    }

    // Delete goal
    pub fn delete_goal(&self, goal_id: &str) -> Result<()> {
        // 1. Check no goals depend on this
        // 2. Archive file (move to .archive/)
        // 3. Create audit entry
    }

    // Serialize goal to markdown
    fn to_markdown(&self, goal: &Goal) -> Result<String> {
        // YAML frontmatter + markdown content
    }
}
```

**Markdown Format:**

```markdown
---
goal_id: goal-authentication-system
title: "User Authentication System"
status: active
phase: P7
owner: "@alice"
dependencies:
  - goal-database-setup
  - goal-user-model
canon:
  - authentication-rfc.md
  - security-requirements.md
tags:
  - security
  - backend
  - critical
updated: 2025-12-29
---

# User Authentication System

## Overview

Implement secure user authentication using JWT tokens.

## Acceptance Criteria

- [ ] User registration endpoint
- [ ] Login/logout endpoints
- [ ] Password hashing with bcrypt
- [ ] JWT token generation
- [ ] Token refresh mechanism
- [ ] Rate limiting on auth endpoints

## Implementation Notes

- Use Argon2 for password hashing
- JWT secret stored in environment variable
- Tokens expire after 24 hours
- Refresh tokens valid for 30 days

## Dependencies

This goal depends on:
- `goal-database-setup` - Database must be ready
- `goal-user-model` - User model must exist

## References

- [RFC: Authentication Design](../04_CANON/authentication-rfc.md)
- [Security Requirements](../04_CANON/security-requirements.md)
```

### 3. Phase Writer

**Operations:**

```rust
pub struct PhaseWriter {
    governance_root: PathBuf,
}

impl PhaseWriter {
    pub fn create_phase(&self, phase: &Phase) -> Result<PathBuf>;
    pub fn update_phase(&self, phase: &Phase) -> Result<()>;
    pub fn set_active_phase(&self, phase_id: &str) -> Result<()>;
    fn to_markdown(&self, phase: &Phase) -> Result<String>;
}
```

**Markdown Format:**

```markdown
---
phase_id: P7
title: "AI Integration & Governance Tools"
status: active
start_date: 2025-12-15
target_date: 2026-01-15
dependencies:
  - P6
---

# Phase 7: AI Integration & Governance Tools

## Objectives

1. Integrate AI assistant for governance queries
2. Build meta-engine desktop app
3. Implement prompt logging and context assembly

## Goals

- goal-ai-assistant-ui
- goal-prompt-logger
- goal-context-builder
- goal-ollama-integration

## Success Criteria

- [ ] AI assistant functional in Meta Engine
- [ ] All AI interactions logged
- [ ] Local LLM option available
- [ ] Full CRUD operations for governance

## Timeline

- Week 1: AI assistant backend
- Week 2: UI integration
- Week 3: Testing and refinement
- Week 4: Documentation and rollout
```

### 4. Daily Writer

**Operations:**

```rust
pub struct DailyWriter {
    governance_root: PathBuf,
}

impl DailyWriter {
    pub fn create_daily_note(&self, date: NaiveDate, content: &str) -> Result<PathBuf>;
    pub fn update_daily_note(&self, date: NaiveDate, content: &str) -> Result<()>;
    pub fn delete_daily_note(&self, date: NaiveDate) -> Result<()>;
}
```

**Already partially implemented in Phase 3, needs enhancement.**

### 5. Tauri Commands

**Location:** `meta-gui/src-tauri/src/commands_crud.rs`

```rust
// Goals
#[tauri::command]
pub fn create_goal(goal_data: GoalCreateRequest, state: State<AppState>) -> Result<String, String>;

#[tauri::command]
pub fn update_goal(goal_id: String, goal_data: GoalUpdateRequest, state: State<AppState>) -> Result<(), String>;

#[tauri::command]
pub fn delete_goal(goal_id: String, state: State<AppState>) -> Result<(), String>;

// Phases
#[tauri::command]
pub fn create_phase(phase_data: PhaseCreateRequest, state: State<AppState>) -> Result<String, String>;

#[tauri::command]
pub fn update_phase(phase_id: String, phase_data: PhaseUpdateRequest, state: State<AppState>) -> Result<(), String>;

#[tauri::command]
pub fn set_active_phase(phase_id: String, state: State<AppState>) -> Result<(), String>;

// Daily Notes (enhanced)
#[tauri::command]
pub fn delete_daily_note(date: String, state: State<AppState>) -> Result<(), String>;
```

**Request/Response Types:**

```rust
#[derive(Deserialize)]
pub struct GoalCreateRequest {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<String>,
    pub owner: Option<String>,
    pub dependencies: Vec<String>,
    pub canon: Vec<String>,
    pub tags: Vec<String>,
    pub content: String,
}

#[derive(Deserialize)]
pub struct GoalUpdateRequest {
    pub title: Option<String>,
    pub status: Option<String>,
    pub phase: Option<String>,
    pub owner: Option<String>,
    pub dependencies: Option<Vec<String>>,
    pub canon: Option<Vec<String>>,
    pub tags: Option<Vec<String>>,
    pub content: Option<String>,
}
```

### 6. Validation

**Rules:**

1. **Goal ID Validation**
   - Must be unique
   - Format: `goal-*` or `G-###`
   - Cannot conflict with existing IDs

2. **Dependency Validation**
   - Referenced goals must exist
   - No circular dependencies
   - Status transitions respect dependencies

3. **Phase Validation**
   - Only one phase can be active
   - Phase transitions preserve history
   - Goals reference valid phases

4. **Content Validation**
   - Markdown parses correctly
   - Frontmatter is valid YAML
   - Required fields present

## Phase 5B: Frontend (UI Components)

### 1. Goal Editor Component

**Location:** `meta-gui/src/lib/GoalEditor.svelte`

**Features:**

```svelte
<script>
  export let goal_id = null // null = create mode, string = edit mode

  let formData = {
    goal_id: '',
    title: '',
    status: 'planned',
    phase: '',
    owner: '',
    dependencies: [],
    canon: [],
    tags: [],
    content: ''
  }

  let errors = {}
  let saving = false
  let showPreview = false

  async function save() {
    // Validate
    // Call create_goal or update_goal
    // Show success toast
    // Refresh goal list
  }
</script>

<div class="goal-editor">
  <!-- Form fields -->
  <input bind:value={formData.goal_id} placeholder="goal-authentication" />
  <input bind:value={formData.title} placeholder="User Authentication System" />

  <select bind:value={formData.status}>
    <option value="planned">Planned</option>
    <option value="active">Active</option>
    <option value="blocked">Blocked</option>
    <option value="partial">Partial</option>
    <option value="done">Done</option>
  </select>

  <!-- Dependencies -->
  <TagInput bind:values={formData.dependencies} placeholder="Add dependency..." />

  <!-- Markdown editor with preview -->
  <div class="editor-container">
    <textarea bind:value={formData.content} />
    {#if showPreview}
      <div class="preview">{@html markdownToHtml(formData.content)}</div>
    {/if}
  </div>

  <button on:click={save} disabled={saving}>
    {goal_id ? 'Update Goal' : 'Create Goal'}
  </button>
</div>
```

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ Goal Editor                          [Preview] [✓]  │
├─────────────────────────────────────────────────────┤
│ Goal ID: [goal-authentication              ]        │
│ Title:   [User Authentication System       ]        │
│ Status:  [Active ▼]  Phase: [P7 ▼]                 │
│ Owner:   [@alice                           ]        │
│                                                     │
│ Dependencies:                                       │
│ [goal-database-setup] [x]                          │
│ [goal-user-model] [x]                              │
│ [+ Add dependency]                                 │
│                                                     │
│ Tags:                                              │
│ [security] [x] [backend] [x] [critical] [x]        │
│ [+ Add tag]                                        │
│                                                     │
│ Canon References:                                   │
│ [authentication-rfc.md] [x]                        │
│ [+ Add reference]                                  │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ # User Authentication System                   │ │
│ │                                                │ │
│ │ ## Overview                                    │ │
│ │ Implement secure user authentication...       │ │
│ │                                                │ │
│ │ ## Acceptance Criteria                        │ │
│ │ - [ ] User registration endpoint              │ │
│ │ ...                                           │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ [Cancel]                         [Save Goal]        │
└─────────────────────────────────────────────────────┘
```

### 2. Phase Editor Component

**Location:** `meta-gui/src/lib/PhaseEditor.svelte`

Similar structure to GoalEditor but for phases:
- Phase ID, title, status
- Start/target dates
- Dependencies
- Associated goals
- Objectives and success criteria

### 3. Enhanced Daily Editor

**Current:** Basic textarea
**Enhanced:** Full markdown editor with:
- Syntax highlighting
- Live preview
- Template insertion
- Goal quick-links
- Save/auto-save

### 4. UI Integration

**Goal Explorer Updates:**

```svelte
<!-- Add "New Goal" button -->
<button on:click={createNewGoal}>
  + New Goal
</button>

<!-- Add edit button to each goal -->
<button on:click={() => editGoal(goal.goal_id)}>
  ✏️ Edit
</button>

<!-- Add delete button with confirmation -->
<button on:click={() => confirmDelete(goal.goal_id)}>
  🗑️ Delete
</button>
```

**Dashboard Updates:**

```svelte
<!-- Add "New Phase" button -->
<button on:click={createNewPhase}>
  + New Phase
</button>

<!-- Add phase transition controls -->
<button on:click={() => setPhaseActive('P8')}>
  Activate Phase P8
</button>
```

## Audit Trail

All write operations create audit entries:

```markdown
---
timestamp: 2025-12-29T16:30:00Z
action: goal_created
user: system
goal_id: goal-authentication-system
---

# Goal Created: goal-authentication-system

**Title:** User Authentication System
**Status:** planned
**Phase:** P7

Created new goal with 2 dependencies and 3 tags.
```

## File Structure

```
meta-engine/
├── meta-core/src/
│   ├── writer/
│   │   ├── mod.rs
│   │   ├── goal_writer.rs
│   │   ├── phase_writer.rs
│   │   ├── daily_writer.rs
│   │   └── frontmatter.rs
│   └── ...
├── meta-gui/
│   ├── src-tauri/src/
│   │   ├── commands_crud.rs  # NEW
│   │   └── ...
│   └── src/lib/
│       ├── GoalEditor.svelte  # NEW
│       ├── PhaseEditor.svelte # NEW
│       └── ...
└── Documentation:
    ├── PHASE_5_DESIGN.md (this file)
    ├── PHASE_5A_PROGRESS.md (TBD)
    └── PHASE_5B_PROGRESS.md (TBD)
```

## Security Considerations

1. **No Network Operations** - All operations local only
2. **File Backups** - Backup before every modification
3. **Validation** - Strict validation before writes
4. **Audit Logging** - Every change logged
5. **Atomic Operations** - Write operations are atomic (temp file + rename)

## Error Handling

```rust
pub enum WriterError {
    ValidationError(String),
    FileExists(PathBuf),
    DependencyNotFound(String),
    CircularDependency(Vec<String>),
    InvalidTransition(String, String),
    IoError(std::io::Error),
}
```

## Testing Strategy

1. **Unit Tests**
   - Goal writer creates valid markdown
   - Phase writer validates transitions
   - Daily writer handles edge cases

2. **Integration Tests**
   - Create → Update → Delete workflows
   - Validation prevents invalid states
   - Audit logs created correctly

3. **UI Tests**
   - Form validation works
   - Preview renders correctly
   - Save operations succeed

## Performance Considerations

- **Incremental Writes** - Only modified files are written
- **Debounced Auto-save** - Don't save on every keystroke
- **Background Operations** - Long operations don't block UI
- **Optimistic Updates** - UI updates immediately, async persistence

## Rollout Plan

### Phase 5A: Backend (Week 1)

1. ✅ Design document (this file)
2. ⏳ Implement writer modules
3. ⏳ Implement Tauri CRUD commands
4. ⏳ Add validation logic
5. ⏳ Write unit tests
6. ⏳ Integration testing

### Phase 5B: Frontend (Week 2)

1. ⏳ Build GoalEditor component
2. ⏳ Build PhaseEditor component
3. ⏳ Enhance DailyEditor
4. ⏳ Integrate with existing views
5. ⏳ Add UI validation
6. ⏳ User testing

### Phase 5C: Polish & Docs (Week 3)

1. ⏳ Error handling refinement
2. ⏳ Performance optimization
3. ⏳ User documentation
4. ⏳ Tutorial/demo
5. ⏳ Final testing
6. ⏳ Release v0.5.0

## Success Criteria

Phase 5 is complete when:

- [x] Design document approved
- [ ] Users can create new goals via UI
- [ ] Users can edit existing goals
- [ ] Users can delete goals (with safety checks)
- [ ] Users can create/edit phases
- [ ] Users can set active phase
- [ ] Daily editor has markdown preview
- [ ] All changes persist to markdown files
- [ ] All operations create audit entries
- [ ] Validation prevents invalid states
- [ ] UI provides clear error messages
- [ ] Documentation complete

## Next Steps

1. Review and approve this design
2. Begin Phase 5A implementation:
   - Create writer module structure
   - Implement GoalWriter
   - Add Tauri commands
   - Test end-to-end

---

**Phase 5 Design:** ✅ **COMPLETE**
**Implementation:** ⏳ **READY TO START**
**Target Release:** v0.5.0 (Phase 5C complete)
