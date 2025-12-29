# Aequitas Meta Engine

**Version:** 0.2.0 (Phase 2 - GUI Foundation)
**Status:** Functional with Desktop UI

A local-first, deterministic governance tool for the Aequitas project.

## Overview

The Meta Engine operates on the `/governance` folder as its source of truth. It provides:

- **Governance validation** — Enforce invariants, detect gaps, surface inconsistencies
- **Goal management** — Query, filter, and update goals by status/phase
- **Daily workflow** — Create and manage daily notes
- **Phase tracking** — Monitor phase coherence and transitions
- **Canon boundary enforcement** — Read-only access to canonical documents

## Architecture

```
meta-engine/
├── meta-core/       # Core library (domain models, parser, validator, query)
├── meta-cli/        # Command-line interface
└── meta-gui/        # Desktop GUI (Tauri + Svelte)
    ├── src-tauri/   # Rust backend
    └── src/         # Svelte frontend
```

**Built with:**
- **Core:** Rust 1.92+, Serde, Walkdir
- **CLI:** Clap, Comfy-table
- **GUI:** Tauri 2, Svelte 5, Vite 6, Tailwind CSS

## Installation

### Prerequisites

**For CLI:**
- Rust 1.92 or later
- Cargo package manager

**For GUI (additional):**
- Node.js 18+ and npm
- System dependencies for Tauri (see [Tauri Prerequisites](https://tauri.app/v2/guides/prerequisites/))

### Build CLI from Source

```bash
cd meta-engine
cargo build --release
```

The CLI binary will be at: `target/release/meta-cli`

### Build GUI from Source

```bash
cd meta-engine/meta-gui

# Install npm dependencies
npm install

# Run in development mode
npm run dev

# Or build for production
npm run build
cargo tauri build
```

The desktop app will be in: `src-tauri/target/release/`

### Create Alias (Recommended)

Add to your `.bashrc` or `.zshrc`:

```bash
alias meta="/path/to/aequitas/meta-engine/target/release/meta-cli --root /path/to/aequitas/governance"
```

Or create a symlink:

```bash
sudo ln -s /path/to/aequitas/meta-engine/target/release/meta-cli /usr/local/bin/meta
```

## Usage

### Commands

#### `meta audit`

Validate governance integrity.

```bash
# Run audit with markdown output
meta audit

# JSON output
meta audit --format json

# Table output
meta audit --format table

# Treat warnings as errors
meta audit --strict
```

**Exit codes:**
- `0` — No errors
- `1` — Errors found (or warnings in strict mode)

#### `meta goals`

List goals with filtering.

```bash
# List all goals
meta goals

# Filter by status
meta goals --status active
meta goals --status blocked
meta goals --status completed

# Filter by phase
meta goals --phase 4

# Filter by tag
meta goals --tag backend

# Combine filters
meta goals --status active --phase 4

# Output formats
meta goals --format table   # default
meta goals --format markdown
meta goals --format json
```

#### `meta goal <action>`

Operate on individual goals.

```bash
# Show goal details
meta goal show G-042

# Update goal status
meta goal set G-042 completed
meta goal set G-043 blocked

# Show dependency tree
meta goal deps G-042
```

**Valid status transitions:**
- `active` → `blocked`, `completed`, `archived`
- `blocked` → `active`, `archived`
- `completed` → `archived`

#### `meta today`

Initialize or open today's daily note.

```bash
# Create/open today's note in $EDITOR
meta today

# Show path without opening
meta today --show
```

**Template created:**
```markdown
---
date: 2025-12-28
phase:
---

# Daily Log — 2025-12-28

## Goals Worked
-

## Decisions Made
-

## Divergences Noted
-
```

#### `meta phase <action>`

Phase information and management.

```bash
# Show current active phase
meta phase current

# List all phases with goal counts
meta phase list

# Validate phase coherence
meta phase validate
```

### Global Flags

```bash
--root <PATH>     # Path to governance folder (default: ./governance)
-v, --verbose     # Enable verbose output
-q, --quiet       # Suppress non-error output
-h, --help        # Print help
-V, --version     # Print version
```

## Governance Folder Structure

The Meta Engine expects this structure:

```
governance/
├── 00_MASTER/
├── 01_DAILY/
│   └── YYYY-MM-DD.md
├── 02_PHASES/
│   └── PHASE_N_*.md
├── 03_GOALS_EPICS/
│   └── G-XXX_*.md
├── 04_DECISIONS/
│   └── D-XXX_*.md
├── 05_AUDITS/
│   └── AUDIT_*.md
├── 06_PROMPTS/
│   └── PROMPT_*.md
└── docs/
    └── canonical/
        ├── CANON_I_*.md
        ├── CANON_II_*.md
        ├── CANON_III_*.md
        ├── CANON_IV_*.md
        └── KERNEL_*.md
```

## Frontmatter Requirements

### Goals (03_GOALS_EPICS/)

**Required:**
```yaml
goal_id: G-XXX
status: active | blocked | completed | archived
```

**Optional:**
```yaml
title: "Goal title"
phase: 4
owner: "architect"
dependencies: [G-001, G-002]
tags: [backend, frontend]
```

### Decisions (04_DECISIONS/)

**Required:**
```yaml
decision_id: D-XXX
status: active | superseded | abandoned
date: YYYY-MM-DD
```

**Optional:**
```yaml
title: "Decision title"
rationale: "Why this decision was made"
```

### Daily Notes (01_DAILY/)

**Required:**
```yaml
date: YYYY-MM-DD
```

**Optional:**
```yaml
phase: 4
goals_worked: [G-042, G-043]
decisions_made: [D-015]
divergences: []
```

## Validation Invariants

The Meta Engine enforces:

### Structural Invariants
1. Goal IDs match pattern `G-XXX`
2. Decision IDs match pattern `D-XXX`
3. Status values are valid
4. All required frontmatter fields present

### Logical Invariants
5. Goal dependencies reference existing goals
6. Goal status transitions are valid
7. Phase coherence (warning if active goals in wrong phase)

### Canon Boundary
8. Files under `docs/canonical/` are read-only
9. Canon cannot be modified via Meta Engine
10. Canon can only be referenced, not interpreted

## Examples

### Daily Workflow

```bash
# Morning: Create today's note
meta today

# Check current work
meta goals --status active

# Update goal status
meta goal set G-042 completed

# Validate governance
meta audit
```

### Goal Management

```bash
# Find blocked goals
meta goals --status blocked

# Check dependencies
meta goal deps G-042

# Move goal forward
meta goal set G-042 active
```

### Phase Transitions

```bash
# Check current phase
meta phase current

# Validate coherence
meta phase validate

# List phase distribution
meta phase list
```

## Development

### Run Tests

```bash
cargo test
```

### Build Debug Version

```bash
cargo build
./target/debug/meta-cli --help
```

### Lint and Format

```bash
cargo clippy
cargo fmt
```

## Desktop GUI

### Features

**Phase 2 includes a native desktop application with:**

- **Dashboard** — Overview of current phase, active/blocked goals, governance health
- **Goal Explorer** — Browse and filter all goals by status, phase, or tags
- **Audit Viewer** — Real-time validation results with errors, warnings, and info

### Launch GUI

```bash
cd meta-engine/meta-gui
npm run dev
```

Or run the built application:
```bash
./meta-engine/meta-gui/src-tauri/target/release/meta-gui
```

### GUI Screenshots

The GUI provides a calm, professional interface optimized for architects:
- Dark mode support
- Keyboard navigation
- Real-time data from governance folder
- No network requests or telemetry

## Roadmap

### Phase 1 ✅ (Complete)
- Core engine + CLI
- Commands: audit, goals, goal, today, phase
- Validation engine
- Output formatters (markdown, JSON, table)

### Phase 2 ✅ (Current)
- Tauri GUI foundation
- Dashboard view (read-only)
- Goal explorer (read-only)
- Audit viewer (read-only)

### Phase 3 (Future)
- Write operations from GUI
- Daily note editor
- Goal status updates

### Phase 4 (Future)
- LLM integration
- Prompt logging
- Context assembly
- Governed AI advisor

## Non-Goals

This tool explicitly does **NOT**:
- Act as a general-purpose note-taking app
- Support multi-user collaboration
- Provide autonomous AI "insights"
- Replace architect's judgment
- Support arbitrary governance schemas
- Provide web access or mobile apps
- Auto-modify Canon documents

## License

MIT

## Contributing

This is an internal Aequitas governance tool. Changes must align with Canon and Kernel requirements.

Before contributing:
1. Read `governance/docs/canonical/`
2. Run `meta audit` to ensure compliance
3. Never modify Canon documents
4. Respect governance invariants

---

**Built for architects, not casual users.**
**Calm. Precise. Local-first.**
