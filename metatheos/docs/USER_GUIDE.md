# Metatheos User Guide

**Version:** 2.0.0
**Last Updated:** 2025-12-31

Complete guide to using Metatheos for daily governance workflows.

## Table of Contents

1. [Installation](#installation)
2. [Daily Workflows](#daily-workflows)
3. [CLI Reference](#cli-reference)
4. [GUI Reference](#gui-reference)
5. [Governance Folder Structure](#governance-folder-structure)
6. [Common Tasks](#common-tasks)
7. [Tips and Tricks](#tips-and-tricks)
8. [Troubleshooting](#troubleshooting)

## Installation

### Building from Source

```bash
# Navigate to metatheos directory
cd /path/to/aequitas/metatheos

# Build CLI
cargo build --release

# CLI binary location
./metatheos-cli/target/release/metatheos
```

### Creating an Alias

Add to `.bashrc` or `.zshrc`:

```bash
export GOVERNANCE_ROOT="/path/to/aequitas/governance"
alias metatheos="/path/to/aequitas/metatheos/metatheos-cli/target/release/metatheos --root $GOVERNANCE_ROOT"
```

Reload shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

Test:
```bash
metatheos --version
```

### Installing GUI

```bash
cd /path/to/aequitas/metatheos/metatheos-gui

# Install dependencies (first time only)
npm install

# Build and run
cargo tauri dev

# Or build production binary
cargo tauri build
```

## Daily Workflows

### Morning Routine

```bash
# 1. Create or open today's daily note
metatheos today

# 2. Check current phase
metatheos phase current

# 3. List active goals
metatheos goals --active

# 4. Check for blockers
metatheos goals --status blocked
```

### During Work

**Update goal status as you work:**

```bash
# Start working on a goal
metatheos goal set G-042 active

# Mark goal as done when complete
metatheos goal set G-042 done

# If blocked
metatheos goal set G-042 blocked
```

**Or use the GUI:**
1. Open Metatheos GUI
2. Navigate to Goals tab
3. Find your goal
4. Click status dropdown → select new status
5. Changes save automatically

### End of Day

```bash
# 1. Update today's daily note with:
#    - Goals worked on
#    - Decisions made
#    - Divergences noted
metatheos today

# 2. Run governance audit
metatheos scan

# 3. Check completion progress
# (Open GUI Dashboard tab)
```

## CLI Reference

### Global Flags

```bash
--root <PATH>     # Path to governance folder
-v, --verbose     # Enable verbose output
-q, --quiet       # Suppress non-error output
-h, --help        # Show help
-V, --version     # Show version
```

### Commands

#### `metatheos scan`

Validate governance integrity.

```bash
# Basic audit
metatheos scan

# Treat warnings as errors
metatheos scan --strict
```

**Output:**
- Errors (red): Must fix
- Warnings (yellow): Should address
- Info (blue): For awareness

**Exit codes:**
- `0` — No errors
- `1` — Errors found (or warnings in strict mode)

---

#### `metatheos goals [OPTIONS]`

List goals with filtering.

```bash
# List all goals
metatheos goals

# Filter by status
metatheos goals --status active
metatheos goals --status blocked
metatheos goals --status done

# Quick filter for active
metatheos goals --active

# Filter by phase
metatheos goals --phase 4

# Filter by tag
metatheos goals --tag backend
metatheos goals --tag frontend

# Combine filters
metatheos goals --status active --phase 4 --tag backend

# Change output format
metatheos goals --format table      # default
metatheos goals --format markdown
metatheos goals --format json
```

**Status values:**
- `planned` — Not started
- `active` — In progress
- `blocked` — Waiting on something
- `partial` — Partially complete
- `done` — Completed
- `archived` — Historical

---

#### `metatheos goal <ACTION>`

Operate on individual goals.

**Show goal details:**
```bash
metatheos goal show G-042
```

**Update goal status:**
```bash
metatheos goal set G-042 done
metatheos goal set G-043 blocked
metatheos goal set G-044 active
```

**Valid transitions:**
- `planned` → `active`, `blocked`, `partial`, `done`
- `active` → `blocked`, `partial`, `done`
- `blocked` → `active`, `partial`, `done`
- `partial` → `active`, `blocked`, `done`
- `done` → `active`, `partial`, `blocked`, `archived`
- `archived` → `done`

**Show dependency tree:**
```bash
metatheos goal deps G-042
```

---

#### `metatheos today [OPTIONS]`

Create or open today's daily note.

```bash
# Open in $EDITOR (default: vim)
metatheos today

# Show path without opening
metatheos today --show
```

**Template created:**
```markdown
---
date: 2025-12-31
phase:
---

# Daily Log — 2025-12-31

## Goals Worked
-

## Decisions Made
-

## Divergences Noted
-
```

---

#### `metatheos phase <ACTION>`

Phase information and management.

**Show current active phase:**
```bash
metatheos phase current
```

**List all phases:**
```bash
metatheos phase list
```

Output shows:
- Phase ID
- Title
- Status (active/complete/planned)
- Goal count

**Validate phase coherence:**
```bash
metatheos phase validate
```

Checks:
- Active goals in correct phase
- Phase transitions are valid
- No orphaned phases

---

#### `metatheos audit [OPTIONS]`

List governance audits.

```bash
# Table format
metatheos audit --format table

# Markdown format
metatheos audit --format markdown

# JSON format
metatheos audit --format json
```

---

#### `metatheos migrate`

Migrate markdown files to SurrealDB cache.

```bash
metatheos migrate
```

**When to run:**
- After fresh checkout
- If database becomes corrupted
- To rebuild cache after many manual markdown edits

**What it does:**
1. Deletes existing `.metatheos.db` folder (if exists)
2. Creates new embedded SurrealDB
3. Parses all markdown files
4. Populates database tables
5. Reports success/failure counts

**Duration**: 200-500ms for 100 files

---

## GUI Reference

### Launching the GUI

```bash
cd metatheos/metatheos-gui
cargo tauri dev
```

### Dashboard Tab

**Shows:**
- Current phase and progress
- Total goals / done / active / blocked
- Completion percentage
- Recent activity (7 days)

**Actions:**
- Click "Create Daily Note" → Opens today's note
- View phase breakdown by clicking phase cards

### Aequitas Dashboard Tab

**Real-time project tracker:**
- Overall completion (X% of Y goals)
- Phase-specific completion
- Critical path (goals blocking others)
- Blockers (blocked goals)
- Recent activity (velocity, daily notes)
- Health metrics (orphaned goals, missing dependencies)

**Useful for:**
- Sprint planning
- Identifying bottlenecks
- Tracking velocity
- Spotting governance issues

### Goals Tab

**Features:**
- Browse all goals
- Filter by status/phase/tag
- Search by title or ID
- Sort by various fields

**Actions:**
1. Click goal row → Opens detail modal
2. Edit goal details
3. Update status via dropdown
4. Save changes (auto-syncs to markdown + DB)

**Keyboard shortcuts:**
- `Escape` — Close modal
- `Enter` — Save changes

### Audits Tab

**Shows:**
- All audit records
- Scope, risk, status
- Evidence and findings

### Files Tab

**Governance folder browser:**
- Tree view of all files
- Click file → View contents
- Read-only for canon files
- Editable for governance files

**File types:**
- 🔵 Goals (G-XXX)
- 🟢 Phases
- 🟡 Decisions (D-XXX)
- 🟣 Audits
- 🔴 Canon (read-only)

## Governance Folder Structure

```
governance/
├── 00_MASTER/                    # Master charts (read-only)
│   └── CHART_OF_ACCOUNTS.md
│
├── 01_DAILY/                     # Daily notes
│   ├── 2025-12-30.md
│   └── 2025-12-31.md
│
├── 02_PHASES/                    # Phase definitions
│   ├── PHASE_1_*.md
│   ├── PHASE_2_*.md
│   └── ...
│
├── 03_GOALS_EPICS/               # Goals
│   ├── G-001_setup.md
│   ├── G-042_dashboard.md
│   └── ...
│
├── 04_DECISIONS/                 # Decision records
│   ├── D-001_architecture.md
│   └── ...
│
├── 05_AUDITS/                    # Audit records
│   └── AUDIT_*.md
│
├── 06_PROMPTS/                   # LLM prompts
│   ├── library/
│   └── sessions/
│
├── 90_ARCHIVE/                   # Archived files
│   └── goals/
│
└── docs/
    └── canonical/                # Canon (read-only)
        ├── CANON_I_*.md
        ├── CANON_II_*.md
        ├── CANON_III_*.md
        ├── CANON_IV_*.md
        └── KERNEL_*.md
```

## Common Tasks

### Creating a New Goal

**Option 1: Manual (recommended for control)**

1. Create file: `governance/03_GOALS_EPICS/G-XXX_title.md`
2. Add frontmatter:
```yaml
---
goal_id: G-XXX
title: "Goal title"
status: planned
phase: 4
dependencies: []
tags: []
---

# Goal Description

Content here...
```

3. Run migration: `metatheos migrate`

**Option 2: Via GUI (coming in Phase 2)**

1. Open GUI → Goals tab
2. Click "New Goal" button
3. Fill form
4. Save

### Updating Goal Status

**CLI:**
```bash
metatheos goal set G-042 done
```

**GUI:**
1. Goals tab → Find goal
2. Click goal row
3. Select new status from dropdown
4. Click "Save"

**Manual:**
1. Open `governance/03_GOALS_EPICS/G-042_*.md`
2. Change `status:` field in frontmatter
3. Save file
4. Run `metatheos migrate` (optional, for GUI)

### Checking Dependencies

```bash
# Show dependency tree
metatheos goal deps G-042

# Find goals blocking G-042
metatheos goals --format json | jq '.[] | select(.dependencies[] == "G-042")'
```

### Finding Blocked Work

```bash
# List all blocked goals
metatheos goals --status blocked

# Check blockers in GUI
# Dashboard tab → Blockers section
```

### Phase Transitions

**When moving to next phase:**

1. Mark all phase goals as done:
```bash
metatheos goals --phase 3 --status active
# Manually update each one
```

2. Update phase file:
```bash
# Edit governance/02_PHASES/PHASE_3_*.md
# Change status: complete
```

3. Validate:
```bash
metatheos phase validate
```

## Tips and Tricks

### Faster Goal Updates

Create shell function:

```bash
# Add to .bashrc/.zshrc
gdone() {
    metatheos goal set "$1" done
}

gblock() {
    metatheos goal set "$1" blocked
}

gactive() {
    metatheos goal set "$1" active
}
```

Usage:
```bash
gdone G-042
gblock G-043
gactive G-044
```

### Batch Operations

```bash
# Mark multiple goals as done
for goal in G-042 G-043 G-044; do
    metatheos goal set $goal done
done
```

### JSON Queries

```bash
# Get all active goals with dependencies
metatheos goals --status active --format json | \
  jq '.[] | select(.dependencies | length > 0)'

# Count goals by status
metatheos goals --format json | \
  jq 'group_by(.status) | map({status: .[0].status, count: length})'
```

### Git Integration

```bash
# Commit after goal updates
metatheos goal set G-042 done && \
git add governance/03_GOALS_EPICS/G-042* && \
git commit -m "Mark G-042 as done"
```

### Daily Note Templates

Customize template by editing:
`metatheos-core/src/writer/daily_writer.rs`

### Keyboard-Driven Workflow

```bash
# Alias for common commands
alias mg="metatheos goals --active"
alias mt="metatheos today"
alias ms="metatheos scan"

# Use in sequence
mt && mg && ms
```

## Troubleshooting

### Database Issues

**Problem**: GUI shows stale data

**Solution**:
```bash
# Rebuild database cache
metatheos migrate
```

---

**Problem**: Database corruption

**Solution**:
```bash
# Delete database
rm -rf governance/.metatheos.db

# Rebuild
metatheos migrate
```

---

### Parse Errors

**Problem**: `meta scan` shows parse errors

**Solution**:
1. Check frontmatter YAML syntax
2. Ensure required fields are present
3. Validate YAML with `yamllint` or online checker
4. Fix and re-run scan

---

### Goal Not Found

**Problem**: `metatheos goal show G-042` returns "not found"

**Solution**:
1. Check file exists in `governance/03_GOALS_EPICS/`
2. Verify `goal_id` in frontmatter matches
3. Ensure filename contains goal ID
4. Run `metatheos migrate` if using GUI

---

### Permission Denied

**Problem**: Cannot write to governance folder

**Solution**:
```bash
# Check permissions
ls -la governance/

# Fix if needed
chmod -R u+w governance/
```

---

### Canon Modification Rejected

**Problem**: "Cannot modify canon files"

**Solution**: This is intentional. Canon files are read-only. To change:
1. Use governance/04_DECISIONS/ to override
2. Or manually edit canon (outside tool)

---

## Advanced Usage

### Scripting with CLI

```bash
#!/bin/bash
# Daily standup report

echo "=== Active Goals ==="
metatheos goals --active

echo ""
echo "=== Blockers ==="
metatheos goals --status blocked

echo ""
echo "=== Today's Note ==="
metatheos today --show
```

### Custom Queries

```bash
# Find goals without dependencies
metatheos goals --format json | \
  jq '.[] | select(.dependencies | length == 0) | .goal_id'

# Find orphaned goals (no phase)
metatheos goals --format json | \
  jq '.[] | select(.phase == null) | .goal_id'
```

### Integration with Other Tools

**VS Code**: Open daily note
```bash
code $(metatheos today --show)
```

**Vim**: Quick edit
```bash
vim $(metatheos today --show)
```

**Tmux**: Split pane workflow
```tmux
# Left pane: GUI
cargo tauri dev

# Right pane: CLI
metatheos goals --active | watch -n 60
```

---

## Getting Help

- **Architecture**: See `docs/ARCHITECTURE.md`
- **Contributing**: See `docs/CONTRIBUTING.md`
- **Changelog**: See `docs/CHANGELOG.md`
- **Canon**: See `governance/docs/canonical/`

**Command help:**
```bash
metatheos --help
metatheos goals --help
metatheos goal --help
```

---

**Last Updated**: 2025-12-31
**Next Review**: Phase 2 Release
