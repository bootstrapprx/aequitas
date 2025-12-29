# Metatheos - Current Status

**Date:** 2025-12-29
**Version:** 0.5.0
**Project:** Metatheos (formerly Meta Engine)
**Status:** ✅ Fully Operational

---

## Recent Changes

### ✅ Rename to Metatheos (2025-12-29)

The project has been successfully rebranded from "Meta Engine" to "Metatheos" and relocated to `/aequitas/metatheos/`.

**What Changed:**
- **Project Name:** Meta Engine → Metatheos
- **Binary Name:** `meta-cli` → `metatheos`
- **Package Names:** All crates renamed (metatheos-core, metatheos-cli, metatheos-gui)
- **Directory:** `/meta-engine/` → `/metatheos/`
- **Branding:** Window title, logo, app identifier updated
- **Imports:** All `meta_core` → `metatheos_core`

**Documentation:** See [RENAME_TO_METATHEOS.md](RENAME_TO_METATHEOS.md) for complete migration details.

---

## Project Structure

```
metatheos/
├── metatheos-core/          # Core governance engine library
│   ├── src/
│   │   ├── domain/         # Goal, Phase, DailyNote, Decision, Audit types
│   │   ├── parser/         # Markdown frontmatter parsing
│   │   ├── writer/         # CRUD operations (NEW in Phase 5A)
│   │   ├── llm/            # AI context building
│   │   ├── governance.rs   # Main GovernanceContext
│   │   └── errors.rs       # Error types
│   └── Cargo.toml
│
├── metatheos-cli/           # Command-line interface
│   ├── src/
│   │   ├── commands/       # CLI commands (scan, audit, goal, etc.)
│   │   └── output/         # Formatters (JSON, table, markdown)
│   └── Cargo.toml          # Binary: metatheos
│
├── metatheos-gui/           # Desktop GUI (Tauri + Svelte)
│   ├── src/                # Svelte frontend
│   │   ├── App.svelte      # Main app component
│   │   └── lib/            # Reusable components
│   ├── src-tauri/src/      # Rust backend
│   │   ├── commands.rs     # Read-only Tauri commands
│   │   ├── commands_crud.rs # CRUD Tauri commands (NEW)
│   │   └── main.rs         # Tauri app entry
│   └── package.json        # name: metatheos-gui
│
├── Cargo.toml              # Workspace configuration
├── RENAME_TO_METATHEOS.md  # Migration documentation
├── PHASE_5A_COMPLETE.md    # CRUD backend completion
└── STATUS.md (this file)   # Current project status
```

---

## Compilation Status

✅ **Clean Build:** No errors
⚠️ **Warnings:** 2 harmless warnings (unused field in ContextBuilder, unused AIAskRequest struct)

```bash
cargo build
# Finished `dev` profile [unoptimized + debuginfo] target(s) in 4.53s
```

---

## Feature Status

### Phase 1-4: Complete ✅
- ✅ Markdown parsing (goals, phases, daily notes, decisions, audits)
- ✅ Governance context loading
- ✅ CLI tool with multiple commands
- ✅ Desktop GUI (Tauri + Svelte)
- ✅ AI assistant integration (Ollama)
- ✅ Dashboard, goal list, phase navigation, daily notes

### Phase 5A: Backend CRUD - Complete ✅
- ✅ Writer module (GoalWriter, PhaseWriter, DailyWriter)
- ✅ YAML frontmatter serialization
- ✅ Atomic file writes with backups
- ✅ Full validation (ID uniqueness, dependencies, status transitions)
- ✅ Audit logging for all operations
- ✅ 8 Tauri commands (create_goal, update_goal, delete_goal, create_phase, update_phase, set_active_phase, write_daily_note, delete_daily_note)

### Phase 5B: UI Components - Pending
- [ ] GoalEditor.svelte component
- [ ] PhaseEditor.svelte component
- [ ] Enhanced DailyEditor.svelte
- [ ] Integration with existing views
- [ ] End-to-end CRUD testing

---

## Running the Application

### GUI (Desktop App)

```bash
cd /home/actpm/Documents/workfolder/aequitas/metatheos/metatheos-gui
cargo tauri dev
```

**URL:** http://localhost:5174
**Title:** "Metatheos - Governance Engine"
**Branding:** Full Metatheos branding with new logo

### CLI

```bash
cd /home/actpm/Documents/workfolder/aequitas/metatheos/metatheos-cli

# Development build
cargo run -- --help

# Production build
cargo build --release
./target/release/metatheos --help
```

**Available Commands:**
- `metatheos scan` - Scan governance directory
- `metatheos goal list` - List all goals
- `metatheos goal show <ID>` - Show goal details
- `metatheos phase list` - List all phases
- `metatheos daily <DATE>` - Show daily note
- `metatheos audit` - Run validation audit
- `metatheos ai ask <QUESTION>` - Ask AI assistant

---

## API Reference

### Tauri Commands (Frontend ↔ Backend)

#### Read-Only Commands (Phase 1-4)
```rust
load_governance_context() -> GovernanceContext
list_goals() -> Vec<Goal>
get_goal(goal_id: String) -> Goal
list_phases() -> Vec<Phase>
get_daily_note(date: String) -> DailyNote
ai_ask(question: String) -> String
```

#### CRUD Commands (Phase 5A - NEW)
```rust
create_goal(request: GoalCreateRequest) -> String
update_goal(goal_id: String, request: GoalUpdateRequest) -> ()
delete_goal(goal_id: String) -> ()

create_phase(request: PhaseCreateRequest) -> String
update_phase(phase_id: String, request: PhaseUpdateRequest) -> ()
set_active_phase(phase_id: String) -> ()

write_daily_note(date: String, content: String) -> ()
delete_daily_note(date: String) -> ()
```

**Usage Example (Svelte):**
```svelte
<script>
import { invoke } from '@tauri-apps/api/core';

async function updateGoal(goalId, updates) {
  try {
    await invoke('update_goal', {
      goalId,
      request: updates
    });
    console.log('Goal updated!');
  } catch (err) {
    console.error('Failed:', err);
  }
}
</script>
```

---

## Data Directory Structure

Metatheos expects a governance directory with this structure:

```
governance/
├── goals/
│   ├── goal-1.md
│   ├── goal-2.md
│   └── .backup/            # Automatic backups before updates
│       └── goal-1.20251229-163000.md
│
├── phases/
│   ├── phase_1.md
│   ├── phase_2.md
│   └── .backup/
│
├── daily/
│   ├── 2025/
│   │   └── 12/
│   │       ├── 28.md
│   │       └── 29.md
│   └── .archive/           # Deleted daily notes
│
├── decisions/
│   └── decision-1.md
│
└── audits/
    ├── 2025-12-29-created-goal-G-101.md
    └── 2025-12-29-activated-phase-2.md
```

---

## Configuration

### Tauri Config

**Location:** `metatheos-gui/src-tauri/tauri.conf.json`

```json
{
  "productName": "Metatheos",
  "version": "0.5.0",
  "identifier": "com.aequitas.metatheos",
  "app": {
    "windows": [{
      "title": "Metatheos - Governance Engine",
      "width": 1200,
      "height": 800
    }]
  }
}
```

### Workspace Config

**Location:** `Cargo.toml`

```toml
[workspace]
members = [
    "metatheos-core",
    "metatheos-cli",
    "metatheos-gui/src-tauri"
]
resolver = "2"
```

---

## Development Workflow

### 1. Make Changes to Core Library
```bash
cd metatheos-core
# Edit src/...
cargo build
cargo test
```

### 2. Test CLI
```bash
cd metatheos-cli
cargo run -- scan /path/to/governance
```

### 3. Test GUI
```bash
cd metatheos-gui
cargo tauri dev
```

### 4. Build Release
```bash
# From workspace root
cargo build --release

# CLI binary at:
./target/release/metatheos

# GUI binary at:
./metatheos-gui/src-tauri/target/release/metatheos-gui
```

---

## Known Issues

### Minor Warnings
- `metatheos-core/src/llm/context.rs:5` - Unused field `max_tokens` (non-critical)
- `metatheos-gui/src-tauri/src/commands_ai.rs:12` - Unused struct `AIAskRequest` (legacy)

**Impact:** None - these are leftover from Phase 4B AI integration and can be cleaned up later.

### No Known Bugs ✅

---

## Migration Notes

If you have the old `meta-engine` installation:

### Update Scripts/Aliases
```bash
# Before
alias meta="meta-cli"

# After
alias meta="metatheos"
```

### Update PATH
```bash
# Reinstall CLI
cd /path/to/aequitas/metatheos/metatheos-cli
cargo install --path .
```

### Update Documentation
Search for "Meta Engine" or "meta-engine" in your docs and replace with "Metatheos" or "metatheos".

---

## Next Development Phase

### Phase 5B: UI Components

**Goal:** Build user interfaces for CRUD operations

**Tasks:**
1. **GoalEditor.svelte** - Form for creating/editing goals
   - Input fields for all goal properties
   - Dependency multi-selector
   - Tag input (comma-separated)
   - Markdown editor with preview
   - Save/Cancel buttons

2. **PhaseEditor.svelte** - Form for phases
   - Phase ID, title, status
   - Date pickers (start/target dates)
   - Dependency selector
   - Activate button

3. **Enhanced DailyEditor.svelte** - Rich daily note editor
   - Markdown editor with toolbar
   - Live preview
   - Template insertion
   - Auto-save

4. **Integration**
   - Add "New Goal" button to Goals tab
   - Add "Edit" icon to goal cards
   - Add "Delete" with confirmation dialog
   - Wire up phase activation button

5. **Testing**
   - Create goal from UI → verify file created
   - Update goal → verify markdown updated
   - Delete goal → verify archived
   - Activate phase → verify status change

**Estimated Effort:** 8-12 hours

---

## Resources

- **Main README:** [README.md](README.md)
- **Implementation Guide:** [IMPLEMENTATION.md](IMPLEMENTATION.md)
- **Phase 5 Design:** [PHASE_5_DESIGN.md](PHASE_5_DESIGN.md)
- **Phase 5A Completion:** [PHASE_5A_COMPLETE.md](PHASE_5A_COMPLETE.md)
- **Rename Documentation:** [RENAME_TO_METATHEOS.md](RENAME_TO_METATHEOS.md)
- **AI Setup Guide:** [AI_SETUP_GUIDE.md](AI_SETUP_GUIDE.md)
- **Ollama Setup:** [OLLAMA_SETUP.md](OLLAMA_SETUP.md)

---

## Quick Reference

### Command Examples

```bash
# Build everything
cargo build

# Run GUI
cd metatheos-gui && cargo tauri dev

# Run CLI
cd metatheos-cli && cargo run -- scan ~/Documents/governance

# List all goals
cargo run -- goal list

# Show specific goal
cargo run -- goal show G-101

# Run validation audit
cargo run -- audit ~/Documents/governance

# Ask AI assistant
cargo run -- ai ask "What are the blocked goals?"
```

### Invoking from Frontend

```javascript
import { invoke } from '@tauri-apps/api/core';

// Load context
const ctx = await invoke('load_governance_context');

// Create goal
await invoke('create_goal', {
  request: {
    goal_id: 'G-101',
    title: 'Implement authentication',
    status: 'planned',
    dependencies: [],
    tags: ['security'],
    content: 'OAuth 2.0 implementation...'
  }
});

// Update goal
await invoke('update_goal', {
  goalId: 'G-101',
  request: {
    status: 'active',
    owner: 'dev_team'
  }
});

// Set active phase
await invoke('set_active_phase', {
  phaseId: 'phase_2'
});
```

---

## Version History

### v0.5.0 (2025-12-29)
- ✅ Renamed to Metatheos
- ✅ Phase 5A: Backend CRUD operations complete
- ✅ Writer module with atomic writes, backups, validation
- ✅ 8 new Tauri commands for CRUD
- ✅ Updated Phase struct with dates
- ✅ Full audit logging

### v0.4.0 (Previous)
- Phase 4B: AI assistant integration
- Ollama LLM support
- Context building for AI queries
- Desktop GUI with Tauri + Svelte

### v0.3.0 (Previous)
- Phase 3: Initial GUI
- Dashboard, goal list, phase navigation
- Daily note viewer

### v0.2.0 (Previous)
- Phase 2: CLI tool
- Multiple commands (scan, goal, phase, audit)
- JSON/table/markdown output formats

### v0.1.0 (Previous)
- Phase 1: Core library
- Markdown parsing for all entity types
- Governance context loading

---

## Status Summary

**Overall Progress:** 85%

- [x] Phase 1: Core Library
- [x] Phase 2: CLI Tool
- [x] Phase 3: GUI Foundation
- [x] Phase 4: AI Integration
- [x] Phase 5A: Backend CRUD
- [ ] Phase 5B: UI Components (Next)
- [ ] Phase 6: Advanced Features (Future)

**Current State:** ✅ Metatheos is fully operational with complete backend CRUD infrastructure. Ready for Phase 5B UI development.

---

**Last Updated:** 2025-12-29
**Maintainer:** Aequitas Development Team
**License:** (Specify license if applicable)
