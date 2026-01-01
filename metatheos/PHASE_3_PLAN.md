# Phase 3: Dev Experience & Quality

**Timeline**: Weeks 5-6
**Status**: 🚧 PLANNING
**Dependencies**: Phase 2 Core Complete ✅

---

## Overview

Phase 3 focuses on developer experience, testing, and production readiness. With core functionality complete (Phases 1-2), it's time to ensure quality, maintainability, and ease of contribution.

**Goal**: Achieve production-grade quality with comprehensive testing, automation, and developer documentation.

---

## Architecture Vision

### Current State

```
✅ Core functionality works
✅ Real-time sync implemented
⚠️  Limited test coverage (~20-30%)
⚠️  Manual build and test process
⚠️  Basic error messages
⚠️  Scattered documentation
```

### Target State

```
✅ Comprehensive test coverage (>80%)
✅ Automated CI/CD pipeline
✅ Clear, actionable error messages
✅ Complete developer documentation
✅ Performance benchmarking
✅ Production-ready builds
```

---

## Implementation Plan

### 3.1: Test Coverage Expansion (Week 5, Days 1-3)

**Goal**: Achieve >80% test coverage across core modules

**Current Coverage Estimate**:
- `metatheos-core/src/watcher`: 100% (6 tests)
- `metatheos-core/src/parser`: ~40% (basic tests exist)
- `metatheos-core/src/validator`: ~30% (basic tests exist)
- `metatheos-core/src/governance`: ~20% (minimal tests)
- `metatheos-core/src/store`: 0% (no tests)
- `metatheos-gui/src-tauri`: ~10% (minimal tests)

**Tasks**:
1. Install `cargo-tarpaulin` for coverage reporting
2. Audit existing test coverage with `cargo tarpaulin`
3. Write unit tests for `store` module (SurrealDB operations)
4. Write unit tests for `governance` module (context loading)
5. Write integration tests for CRUD operations
6. Write integration tests for file watcher + DB sync
7. Write frontend tests for governance store (TypeScript)
8. Generate coverage report and identify gaps

**Technical Details**:

```bash
# Install tarpaulin
cargo install cargo-tarpaulin

# Generate coverage report
cargo tarpaulin --out Html --output-dir coverage/

# Target coverage
# - Core modules: >90%
# - Integration: >80%
# - Overall: >80%
```

**Test Categories**:

**Unit Tests** (fast, isolated):
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_surreal_store_create_goal() {
        // Test DB create operation
    }

    #[test]
    fn test_governance_context_load() {
        // Test context loading with fixtures
    }
}
```

**Integration Tests** (slower, realistic):
```rust
// tests/watcher_integration.rs
#[tokio::test]
async fn test_file_change_updates_db() {
    // Create temp governance folder
    // Start watcher
    // Modify goal file
    // Wait for event
    // Verify DB updated
    // Cleanup
}
```

**Deliverables**:
- [ ] `cargo-tarpaulin` installed
- [ ] Coverage baseline report
- [ ] Store module tests (10+ tests)
- [ ] Governance module tests (15+ tests)
- [ ] CRUD integration tests (8+ tests)
- [ ] Watcher integration tests (5+ tests)
- [ ] Frontend store tests (TypeScript/Vitest)
- [ ] Coverage report showing >80%

**Estimated Effort**: 12-16 hours

---

### 3.2: CI/CD Pipeline (Week 5, Days 4-5)

**Goal**: Automated testing and builds on every commit

**Tasks**:
1. Create `.github/workflows/ci.yml` for GitHub Actions
2. Set up Rust CI (build, test, clippy, fmt)
3. Set up Frontend CI (npm build, test, lint)
4. Add coverage reporting to CI
5. Set up release builds (artifacts)
6. Add branch protection rules
7. Configure PR checks (must pass CI)
8. Add status badges to README

**Technical Details**:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-rust:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable

      - name: Run tests
        run: cargo test --all

      - name: Check formatting
        run: cargo fmt --all -- --check

      - name: Run clippy
        run: cargo clippy --all -- -D warnings

      - name: Generate coverage
        run: cargo tarpaulin --out Xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: cd metatheos-gui && npm ci

      - name: Build frontend
        run: cd metatheos-gui && npm run build

      - name: Run tests
        run: cd metatheos-gui && npm test

  build-release:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4

      - name: Build release
        run: cargo build --release

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: metatheos-${{ matrix.os }}
          path: target/release/metatheos*
```

**Deliverables**:
- [ ] CI workflow file created
- [ ] Rust tests run on every PR
- [ ] Frontend builds verified
- [ ] Coverage reports uploaded
- [ ] Release artifacts built
- [ ] Status badges in README
- [ ] Branch protection enabled

**Estimated Effort**: 8-10 hours

---

### 3.3: Error Message Improvements (Week 6, Days 1-2)

**Goal**: Clear, actionable error messages with suggestions

**Current Issues**:
- Generic errors: "Failed to load governance context"
- No suggestions: What should the user do?
- Missing context: Which file? What line?
- Poor error propagation: Lost details in chain

**Tasks**:
1. Audit all error messages in codebase
2. Add context to errors (file paths, line numbers)
3. Add suggestions to common errors
4. Improve error types with `thiserror`
5. Add error codes for easy searching
6. Create error documentation
7. Test error scenarios

**Technical Details**:

```rust
// Before
return Err(anyhow!("Failed to parse goal"));

// After
return Err(MetaError::ParseError {
    path: path.to_path_buf(),
    line: Some(42),
    message: "Missing required field 'goal_id' in frontmatter".to_string(),
    suggestion: Some("Add 'goal_id: G-XXX' to the YAML frontmatter".to_string()),
    code: "E0101".to_string(),
})?;
```

**Error Categories**:

1. **Parse Errors** (E01XX):
   - E0101: Missing frontmatter field
   - E0102: Invalid YAML syntax
   - E0103: Invalid goal ID format

2. **Validation Errors** (E02XX):
   - E0201: Dependency not found
   - E0202: Invalid status transition
   - E0203: Circular dependency

3. **File System Errors** (E03XX):
   - E0301: Governance folder not found
   - E0302: Permission denied
   - E0303: File not found

4. **Database Errors** (E04XX):
   - E0401: Connection failed
   - E0402: Query failed
   - E0403: Migration failed

**Example Error Output**:

```
Error [E0101]: Failed to parse goal
  --> governance/03_GOALS_EPICS/G-042_test.md:3

  Missing required field 'goal_id' in frontmatter

  Suggestion: Add 'goal_id: G-XXX' to the YAML frontmatter

  Example:
    ---
    goal_id: G-042
    title: "Your goal title"
    status: planned
    ---

  For more information, see: docs/errors/E0101.md
```

**Deliverables**:
- [ ] Error type enum with codes
- [ ] Context added to all errors
- [ ] Suggestions for common errors
- [ ] Error documentation directory
- [ ] Error message tests
- [ ] User-facing error guide

**Estimated Effort**: 8-10 hours

---

### 3.4: Developer Documentation (Week 6, Days 3-4)

**Goal**: Complete onboarding and contribution guides

**Tasks**:
1. Write `docs/DEVELOPMENT.md` (setup, build, test)
2. Write `docs/TESTING.md` (test strategy, running tests)
3. Write `docs/ERRORS.md` (error codes reference)
4. Update `docs/ARCHITECTURE.md` with Phase 2 additions
5. Create `docs/CONTRIBUTING.md` improvements
6. Add inline code documentation (rustdoc)
7. Generate API documentation
8. Create troubleshooting guide

**Technical Details**:

```markdown
# docs/DEVELOPMENT.md

## Quick Start

### Prerequisites
- Rust 1.75+ (`rustup update`)
- Node.js 20+ (`nvm use 20`)
- SurrealDB (embedded, no install needed)

### Build
```bash
# Clone repo
git clone https://github.com/aequitas/metatheos
cd metatheos

# Build CLI
cargo build --release

# Build GUI
cd metatheos-gui
npm install
cargo tauri build
```

### Test
```bash
# Run all tests
cargo test --all

# Run specific module tests
cargo test --package metatheos-core watcher

# Generate coverage
cargo tarpaulin --out Html
```

### Development Workflow
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `cargo test --all`
4. Run linter: `cargo clippy --all`
5. Format code: `cargo fmt --all`
6. Commit with conventional commits: `git commit -m "feat: add X"`
7. Push and create PR
```

**Documentation Structure**:
```
docs/
├── DEVELOPMENT.md       # Setup, build, test
├── TESTING.md          # Test strategy and guide
├── ERRORS.md           # Error codes reference
├── ARCHITECTURE.md     # Technical design (updated)
├── CONTRIBUTING.md     # Contribution guidelines (updated)
├── TROUBLESHOOTING.md  # Common issues and fixes
├── API.md              # API documentation
└── errors/
    ├── E0101.md        # Parse error: Missing field
    ├── E0102.md        # Parse error: Invalid YAML
    └── ...
```

**Deliverables**:
- [ ] DEVELOPMENT.md created
- [ ] TESTING.md created
- [ ] ERRORS.md created
- [ ] ARCHITECTURE.md updated
- [ ] CONTRIBUTING.md updated
- [ ] TROUBLESHOOTING.md created
- [ ] Rustdoc comments added (>50% coverage)
- [ ] API docs generated

**Estimated Effort**: 10-12 hours

---

### 3.5: Performance Benchmarking (Week 6, Days 5-6)

**Goal**: Establish performance baselines and identify bottlenecks

**Tasks**:
1. Set up `criterion` for Rust benchmarks
2. Benchmark parser performance (goals, phases, audits)
3. Benchmark DB operations (create, read, update, delete)
4. Benchmark file watcher event processing
5. Benchmark governance context loading
6. Create performance regression tests
7. Document performance characteristics
8. Optimize identified bottlenecks (if any)

**Technical Details**:

```rust
// benches/parser_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use metatheos_core::parser::MarkdownParser;

fn bench_parse_goal(c: &mut Criterion) {
    let goal_path = "fixtures/G-042_test.md";

    c.bench_function("parse_goal", |b| {
        b.iter(|| {
            MarkdownParser::parse_goal(black_box(goal_path))
        })
    });
}

criterion_group!(benches, bench_parse_goal);
criterion_main!(benches);
```

**Benchmark Targets**:
- Parse goal: <5ms (target: <2ms)
- Parse phase: <3ms (target: <1ms)
- DB create: <20ms (target: <10ms)
- DB read: <5ms (target: <2ms)
- Context load (100 goals): <100ms (target: <50ms)
- File watcher event: <10ms (target: <5ms)

**Deliverables**:
- [ ] Criterion benchmarks set up
- [ ] Parser benchmarks (5+ scenarios)
- [ ] DB operation benchmarks (4+ operations)
- [ ] Context loading benchmarks (3+ sizes)
- [ ] Performance baseline report
- [ ] Regression test suite
- [ ] Optimization report (if needed)

**Estimated Effort**: 8-10 hours

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \    E2E Tests (5%)
      /----\   - Full application flow
     /      \
    /--------\ Integration Tests (25%)
   /          \ - Module interactions
  /------------\ Unit Tests (70%)
 /              \ - Individual functions
```

### Coverage Goals

| Module | Target | Priority |
|--------|--------|----------|
| Parser | >90% | HIGH |
| Validator | >90% | HIGH |
| Store | >85% | HIGH |
| Watcher | >90% | HIGH |
| Governance | >85% | HIGH |
| Writer | >80% | MEDIUM |
| Dashboard | >75% | MEDIUM |
| Commands | >70% | MEDIUM |

### Test Types

**Unit Tests** (fast, isolated):
- Pure functions
- Single module
- Mocked dependencies
- Run in <1s

**Integration Tests** (realistic):
- Multiple modules
- Real file system (temp dirs)
- Real database (in-memory)
- Run in <10s

**E2E Tests** (full flow):
- Complete user scenarios
- Real governance folder
- GUI + backend + DB
- Run in <30s

---

## Success Criteria

Phase 3 is complete when:

- [ ] Test coverage >80% (verified by tarpaulin)
- [ ] CI/CD pipeline passing on main branch
- [ ] All PRs require passing CI checks
- [ ] Error messages have context and suggestions
- [ ] Developer documentation complete
- [ ] Performance benchmarks established
- [ ] No performance regressions detected
- [ ] Release builds automated

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low test coverage remains | High | Incremental approach, focus on critical paths first |
| CI/CD complexity | Medium | Use GitHub Actions templates, start simple |
| Performance regressions | Medium | Automated benchmarks in CI |
| Documentation becomes stale | Low | Link docs to code, review in PRs |

---

## Dependencies

### New Tools

**Rust**:
```toml
[dev-dependencies]
criterion = "0.5"     # Benchmarking
cargo-tarpaulin       # Coverage (CLI tool)
```

**Frontend**:
```json
{
  "devDependencies": {
    "vitest": "^1.0",      // Testing framework
    "@testing-library/svelte": "^4.0"  // Svelte testing
  }
}
```

**CI/CD**:
- GitHub Actions (free for public repos)
- Codecov (free for open source)

---

## Timeline

### Week 5 (Days 1-5)
- Days 1-3: Test coverage expansion
- Days 4-5: CI/CD pipeline setup

### Week 6 (Days 1-6)
- Days 1-2: Error message improvements
- Days 3-4: Developer documentation
- Days 5-6: Performance benchmarking

### Week 6 (Day 7)
- Integration testing
- Bug fixes
- Documentation polish
- Phase 3 completion report

---

## Documentation Updates

After Phase 3:
- Update `README.md` with CI badges
- Update `docs/ARCHITECTURE.md` with test strategy
- Create `docs/DEVELOPMENT.md`
- Create `docs/TESTING.md`
- Create `PHASE_3_COMPLETE.md`

---

## Next Phase Preview

**Phase 4: Intelligence (Weeks 7-8)** - OPTIONAL
- Ollama integration for local LLM reasoning
- Prompt logging and governance
- Context assembly for AI queries
- Canon-aligned LLM advisor

**OR**

**Phase 5: Polish (Weeks 9-10)** - RECOMMENDED
- UX refinements based on usage
- Performance optimization
- Final documentation polish
- Release preparation

---

**Created**: 2025-12-31
**Status**: 🚧 Planning Phase
**Ready to Begin**: Pending approval
