# Metatheos

**Version:** 2.0.0 (Consolidation Release)
**Status:** Production Ready ✅

A local-first, deterministic governance engine for the Aequitas project.

## Overview

Metatheos operates on markdown files in the `/governance` folder as its single source of truth, with an optional SurrealDB read-cache for performance. It provides:

- **Governance validation** — Enforce invariants, detect gaps, surface inconsistencies
- **Goal management** — Query, filter, and update goals by status/phase
- **Daily workflow** — Create and manage daily notes with templates
- **Phase tracking** — Monitor phase coherence and transitions
- **Canon boundary enforcement** — Read-only access to canonical documents
- **Desktop GUI** — Full-featured Tauri app with real-time updates
- **CLI Tools** — Command-line interface for automation and scripting
- **SurrealDB Caching** — Optional high-performance read cache (markdown remains authoritative)

## Quick Start

### Prerequisites

**For CLI:**
- Rust 1.92 or later
- Cargo package manager

**For GUI (additional):**
- Node.js 18+ and npm
- Tauri prerequisites ([see guide](https://tauri.app/v2/guides/prerequisites/))

### Build from Source

```bash
# Clone repository (if not already)
cd /path/to/aequitas/metatheos

# Build CLI
cargo build --release

# Build GUI
cd metatheos-gui
npm install
npm run build
cargo tauri build
```

**Binaries:**
- CLI: `metatheos/metatheos-cli/target/release/metatheos`
- GUI: `metatheos/metatheos-gui/src-tauri/target/release/metatheos-gui`

### Create Alias (Recommended)

Add to `.bashrc` or `.zshrc`:

```bash
alias metatheos="/path/to/aequitas/metatheos/metatheos-cli/target/release/metatheos --root /path/to/aequitas/governance"
```

Or symlink:

```bash
sudo ln -s /path/to/aequitas/metatheos/metatheos-cli/target/release/metatheos /usr/local/bin/metatheos
```

## Architecture

```
metatheos/
├── metatheos-core/    # Core library (models, parser, validator, store)
├── metatheos-cli/     # Command-line interface
└── metatheos-gui/     # Desktop GUI (Tauri + Svelte)
    ├── src-tauri/     # Rust backend
    └── src/           # Svelte frontend
```

**Philosophy:** Markdown Authoritative, DB Read-Cache
- Markdown files are the single source of truth
- SurrealDB provides fast read-cache (optional)
- All writes go to filesystem first, then DB async

**Built with:**
- **Core:** Rust, Serde, SurrealDB
- **CLI:** Clap, Comfy-table, Tokio
- **GUI:** Tauri 2, Svelte 5, Vite 6, Tailwind CSS, D3.js

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** — Daily workflows and command usage
- **[Architecture](docs/ARCHITECTURE.md)** — Technical design and persistence strategy
- **[Contributing](docs/CONTRIBUTING.md)** — Development guidelines
- **[Changelog](docs/CHANGELOG.md)** — Version history and migration notes

## Key Features

### CLI Commands

```bash
# Validate governance integrity
metatheos scan

# List and filter goals
metatheos goals --status active
metatheos goals --phase 4

# Update goal status
metatheos goal set G-042 done

# Create/open today's daily note
metatheos today

# Phase management
metatheos phase current
metatheos phase list

# Migrate markdown → SurrealDB cache
metatheos migrate
```

### Desktop GUI

- **Aequitas Dashboard** — Real-time project completion and health metrics
- **Goal Explorer** — Browse, filter, update goal statuses with live refresh
- **Audit Viewer** — Validation results with errors and warnings
- **File Browser** — Navigate governance folder with syntax highlighting
- **Write Operations** — Full CRUD for goals, phases, audits, prompts, daily notes
- **Toast Notifications** — User-friendly feedback for all operations

### Governance Folder Structure

```
governance/
├── 00_MASTER/              # Master charts and canon
├── 01_DAILY/               # Daily notes (YYYY-MM-DD.md)
├── 02_PHASES/              # Phase definitions
├── 03_GOALS_EPICS/         # Goals (G-XXX_*.md)
├── 04_DECISIONS/           # Decisions (D-XXX_*.md)
├── 05_AUDITS/              # Audit records
└── 06_PROMPTS/             # LLM prompts and logs
```

## Philosophy

**Data Outlives the Tool**
- Markdown is the authoritative source of truth
- Database is a high-performance read cache
- External edits to markdown are respected
- Tool failure never corrupts governance data

**Local-First**
- No network requests or telemetry
- No cloud services or auth
- Works offline completely
- Fast, deterministic, reproducible

**Calm Technology**
- Professional, architect-focused interface
- Keyboard-driven workflows
- No distractions or animations
- Dark mode optimized for long sessions

## Non-Goals

Metatheos explicitly does **NOT**:
- Act as a general-purpose note-taking app
- Support multi-user collaboration
- Provide autonomous AI "insights" without governance
- Replace architect's judgment
- Support arbitrary governance schemas
- Provide web access or mobile apps
- Auto-modify Canon documents

## Roadmap

### Phase 1 ✅ Complete (Foundation)
- Core engine + CLI
- Governance validation
- Desktop GUI with read/write operations
- SurrealDB caching
- Dual-write persistence pattern

### Phase 2 (Real-Time Sync - Weeks 3-4)
- File watcher for external markdown edits
- Dashboard live updates
- Dependency graph visualization
- Conflict resolution

### Phase 3 (Dev Experience - Weeks 5-6)
- Comprehensive test coverage
- Documentation cleanup
- Error message improvements
- Developer tooling

### Phase 4 (Intelligence - Weeks 7-8)
- Ollama integration for reasoning
- Prompt logging and governance
- Context assembly for AI
- Canon-aligned LLM advisor

### Phase 5 (Polish - Weeks 9-10)
- Performance optimization
- UX refinements
- Final documentation
- v2.0 release

## License

MIT

## Contributing

This is an internal Aequitas governance tool. See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

**Built for architects, not casual users.**
**Calm. Precise. Local-first.**
