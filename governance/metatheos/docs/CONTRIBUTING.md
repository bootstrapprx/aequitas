# Contributing to Metatheos

**Status**: Internal Tool
**Audience**: Aequitas Core Team

This document provides guidelines for contributing to Metatheos, the Aequitas governance engine.

## Philosophy

Metatheos is an **internal governance tool**, not a general-purpose application. Contributions must:

1. **Align with Canon** — Respect governance principles defined in `governance/docs/canonical/`
2. **Maintain Simplicity** — Prefer clarity over cleverness
3. **Preserve Local-First** — No network dependencies, no telemetry, no cloud services
4. **Respect Markdown Authority** — Markdown files are always the source of truth

## Development Setup

### Prerequisites

- **Rust 1.92+** with cargo
- **Node.js 18+** with npm (for GUI development)
- **Git** for version control
- **Tauri Prerequisites** ([installation guide](https://tauri.app/v2/guides/prerequisites/))

### Clone and Build

```bash
# Clone repository
git clone <repository-url>
cd metatheos

# Build core + CLI
cargo build

# Build GUI
cd metatheos-gui
npm install
cargo tauri dev
```

### Run Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test goal_status_transitions

# Run tests in specific crate
cargo test --package metatheos-core
```

### Development Workflow

```bash
# Format code
cargo fmt

# Lint code
cargo clippy

# Check compilation without building
cargo check

# Build release binaries
cargo build --release
```

## Project Structure

```
metatheos/
├── metatheos-core/        # Core library
│   ├── src/
│   │   ├── domain/       # Domain models
│   │   ├── parser/       # Markdown parsing
│   │   ├── writer/       # Markdown generation
│   │   ├── validator/    # Invariant enforcement
│   │   ├── query/        # Query interface
│   │   ├── store/        # SurrealDB integration
│   │   ├── dashboard/    # Dashboard calculation
│   │   └── governance.rs # Top-level orchestration
│   └── tests/            # Integration tests
│
├── metatheos-cli/         # CLI tool
│   ├── src/
│   │   ├── commands/     # CLI commands
│   │   ├── output/       # Formatters
│   │   └── main.rs       # Entry point
│   └── tests/            # CLI tests
│
└── metatheos-gui/         # Desktop GUI
    ├── src-tauri/        # Rust backend
    │   └── src/
    │       ├── commands.rs      # Read operations
    │       ├── commands_crud.rs # Write operations
    │       ├── state.rs         # App state
    │       └── main.rs          # Tauri init
    └── src/              # Svelte frontend
        ├── lib/          # Components
        └── App.svelte    # Root component
```

## Code Style

### Rust

Follow standard Rust conventions:

```rust
// Good: Descriptive names, early returns
pub fn update_goal_status(goal_id: &str, new_status: GoalStatus) -> Result<()> {
    let goal = load_goal(goal_id)?;

    if !goal.status.can_transition_to(&new_status) {
        return Err(MetaError::ValidationError(
            format!("Cannot transition from {:?} to {:?}", goal.status, new_status)
        ));
    }

    save_goal(&goal)?;
    Ok(())
}

// Bad: Nested ifs, unclear names
pub fn upd(id: &str, s: GoalStatus) -> Result<()> {
    let g = load_goal(id)?;
    if g.status.can_transition_to(&s) {
        save_goal(&g)?;
        Ok(())
    } else {
        Err(MetaError::ValidationError("bad transition".to_string()))
    }
}
```

**Guidelines**:
- Use `rustfmt` for formatting
- Use `clippy` for linting
- Prefer explicit types over inference in public APIs
- Use `?` operator for error propagation
- Write descriptive error messages
- Avoid `unwrap()` in production code (use `?` or `.ok()`)

### TypeScript/Svelte

```typescript
// Good: Type-safe, clear
interface GoalUpdate {
    goal_id: string;
    status: string;
    title?: string;
}

async function updateGoal(update: GoalUpdate): Promise<void> {
    try {
        await invoke('update_goal', { goalId: update.goal_id, request: update });
        showToast('Goal updated successfully', 'success');
    } catch (error) {
        showToast(`Failed to update goal: ${error}`, 'error');
    }
}

// Bad: No types, poor error handling
async function update(data) {
    await invoke('update_goal', data);
}
```

**Guidelines**:
- Use TypeScript for all `.ts` files
- Define interfaces for Tauri command parameters
- Handle errors gracefully with user-friendly messages
- Use Svelte 5 runes (`$state`, `$derived`, `$effect`)
- Prefer composition over inheritance

## Testing Requirements

### What to Test

**Required**:
- ✅ Domain model validation logic
- ✅ Status transition rules
- ✅ Parser edge cases (malformed files)
- ✅ Writer output correctness

**Nice to Have**:
- Integration tests for full workflows
- GUI component tests
- Performance benchmarks

### Writing Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_goal_status_transition_valid() {
        let current = GoalStatus::Active;
        let target = GoalStatus::Done;
        assert!(current.can_transition_to(&target));
    }

    #[test]
    fn test_goal_status_transition_invalid() {
        let current = GoalStatus::Done;
        let target = GoalStatus::Planned;
        assert!(!current.can_transition_to(&target));
    }
}
```

**Test Naming**: `test_<component>_<scenario>_<expected_outcome>`

### Running Tests

```bash
# All tests
cargo test

# With timing
cargo test -- --nocapture --test-threads=1

# Specific test
cargo test test_goal_status
```

## Git Workflow

### Branches

- `main` — Production-ready code
- `feature/<name>` — New features
- `fix/<name>` — Bug fixes
- `docs/<name>` — Documentation changes

### Commit Messages

```
feat: Add file watcher for real-time sync
fix: Correct goal status transition validation
docs: Update architecture with persistence strategy
refactor: Simplify dashboard calculation logic
test: Add tests for phase coherence validation
```

**Format**: `<type>: <description>`

**Types**:
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation
- `refactor` — Code restructuring
- `test` — Test additions/changes
- `chore` — Build/tooling changes

### Pull Requests

1. Create feature branch from `main`
2. Make changes with clear commits
3. Run tests: `cargo test`
4. Run linter: `cargo clippy`
5. Format code: `cargo fmt`
6. Push and create PR
7. Wait for review

**PR Template**:
```markdown
## Summary
Brief description of changes

## Motivation
Why is this change needed?

## Testing
How was this tested?

## Checklist
- [ ] Tests passing
- [ ] Code formatted (`cargo fmt`)
- [ ] Linter clean (`cargo clippy`)
- [ ] Documentation updated
```

## Adding New Features

### New CLI Command

1. Create command file: `metatheos-cli/src/commands/mycommand.rs`
2. Implement command logic
3. Register in `commands/mod.rs`
4. Add to args enum in `args.rs`
5. Update CLI help text
6. Add tests
7. Update `docs/USER_GUIDE.md`

### New Tauri Command

1. Add function to `metatheos-gui/src-tauri/src/commands.rs` (read) or `commands_crud.rs` (write)
2. Mark with `#[tauri::command]` attribute
3. Register in `main.rs` invoke handler
4. Implement frontend call in Svelte component
5. Add error handling and toast notifications
6. Test manually in GUI
7. Update documentation

### New Domain Entity

1. Define model in `metatheos-core/src/domain/`
2. Add parser in `metatheos-core/src/parser/markdown.rs`
3. Add writer in `metatheos-core/src/writer/`
4. Add SurrealDB table in `metatheos-core/src/store/`
5. Add migration logic in `metatheos-core/src/store/migration.rs`
6. Add validation rules
7. Add tests
8. Update documentation

## Code Review Guidelines

### As a Reviewer

Look for:
- ✅ Tests cover the changes
- ✅ Code follows style guidelines
- ✅ Error messages are user-friendly
- ✅ No `unwrap()` in production code
- ✅ Markdown authority is preserved (no DB-first writes)
- ✅ Canon boundary is respected
- ✅ Documentation is updated

### As an Author

Before requesting review:
- ✅ All tests pass
- ✅ Code is formatted and linted
- ✅ Commit messages are clear
- ✅ PR description explains changes
- ✅ Documentation is updated
- ✅ No commented-out code

## Common Patterns

### Error Handling

```rust
// Prefer: Result with proper error type
pub fn load_goal(goal_id: &str) -> Result<Goal> {
    let path = find_goal_file(goal_id)?;
    MarkdownParser::parse_goal(&path)
}

// Avoid: panic! or unwrap()
pub fn load_goal(goal_id: &str) -> Goal {
    let path = find_goal_file(goal_id).unwrap(); // ❌ Bad
    MarkdownParser::parse_goal(&path).unwrap()    // ❌ Bad
}
```

### Dual-Write Pattern

Always write markdown first, then DB:

```rust
// Write to markdown (source of truth)
writer.write_entity(&entity)?;

// Async DB update (non-blocking, fire-and-forget)
if let Some(store) = state.db.lock().unwrap().as_ref() {
    let store = store.clone();
    tauri::async_runtime::spawn(async move {
        let _ = store.get_db().create(("table", id)).content(entity).await;
    });
}
```

**Never**:
- ❌ Write to DB first
- ❌ Make DB write blocking
- ❌ Fail operation if DB write fails

### Canon Boundary

```rust
// Check if path is in canon folder
fn is_canon_path(path: &Path) -> bool {
    path.to_string_lossy().contains("docs/canonical/") ||
    path.to_string_lossy().contains("00_MASTER/")
}

// Reject writes to canon
if is_canon_path(&goal.file_path) {
    return Err(MetaError::ValidationError(
        "Cannot modify canon files".to_string()
    ));
}
```

## Debugging

### Rust

```bash
# Run with debug logs
RUST_LOG=debug cargo run

# Run specific test with output
cargo test test_name -- --nocapture

# Use rust-analyzer in VSCode for inline errors
```

### Tauri/GUI

```bash
# Open DevTools in GUI
# macOS: Cmd+Option+I
# Linux/Windows: Ctrl+Shift+I

# View Rust logs in terminal
cargo tauri dev
```

### SurrealDB

```rust
// Log query results
let goals: Vec<Goal> = store.get_all_goals().await?;
eprintln!("Loaded {} goals", goals.len());
```

## Performance Guidelines

- Profile before optimizing
- Avoid unnecessary clones (use references)
- Use iterators instead of collecting to Vec
- Batch DB operations when possible
- Async DB writes should not block UI

## Documentation Requirements

All public APIs must have doc comments:

```rust
/// Updates a goal's status with validation.
///
/// # Arguments
///
/// * `goal_id` - The goal identifier (e.g., "G-042")
/// * `new_status` - Target status
///
/// # Returns
///
/// * `Ok(())` if status updated successfully
/// * `Err(MetaError::ValidationError)` if transition is invalid
///
/// # Examples
///
/// ```
/// update_goal_status("G-042", GoalStatus::Done)?;
/// ```
pub fn update_goal_status(goal_id: &str, new_status: GoalStatus) -> Result<()> {
    // ...
}
```

## Release Process

1. Update version in `Cargo.toml` files
2. Update `CHANGELOG.md`
3. Run full test suite: `cargo test`
4. Build release binaries: `cargo build --release`
5. Test binaries manually
6. Tag release: `git tag v2.0.0`
7. Push: `git push && git push --tags`

## Questions?

For questions about:
- **Architecture** → See `docs/ARCHITECTURE.md`
- **Usage** → See `docs/USER_GUIDE.md`
- **Governance Philosophy** → See `governance/docs/canonical/`

---

**Remember**: This is a governance tool for architects. Prioritize correctness over convenience, clarity over cleverness, and local-first over cloud features.
