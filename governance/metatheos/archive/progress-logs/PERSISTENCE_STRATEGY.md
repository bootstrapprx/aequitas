# Persistence Strategy Decision

**Date:** 2025-12-31
**Status:** APPROVED
**Decision ID:** D-META-001

---

## Decision

**Adopt Markdown-First persistence strategy for Phase 1 (Stabilization).**

Defer SurrealDB migration to Phase 4 or later, after core workflows are stable and tested.

---

## Context

Metatheos currently has **dual state management**:
1. **Markdown files** in `/governance` folder (primary, working)
2. **SurrealDB embedded** in `metatheos-core/src/store/` (partially implemented)

**Problem**: Dual state creates inconsistency risk, adds complexity, and is blocking stabilization.

---

## Options Considered

### Option A: Markdown-Only (CHOSEN)
- **Pros**:
  - Already working and battle-tested
  - Zero migration risk
  - Simplifies codebase immediately
  - Enables rapid iteration on core workflows
  - Git-friendly (diffs, history, merge conflicts are human-readable)
- **Cons**:
  - Limited query performance at scale (acceptable for governance use case)
  - No built-in relationships or indexing

### Option B: Complete SurrealDB Migration
- **Pros**:
  - Better query performance
  - Built-in relationships and graph queries
  - Schema validation at database layer
- **Cons**:
  - Requires significant migration effort (write migration script, test round-trip)
  - Risk of data corruption during migration
  - Adds complexity before core is stable
  - Blocks Phase 1 stabilization

---

## Decision Rationale

**Markdown-first aligns with core principles**:
1. **Local-first**: Markdown files are the ultimate local-first format
2. **Deterministic**: Plain text files = deterministic, no hidden state
3. **Calm Design**: Architect can read/edit governance files in any text editor
4. **CLI-First**: CLI tools naturally work with files on disk
5. **Information Quality**: Markdown is human-readable, auditable, versionable

**SurrealDB is deferred, not abandoned**:
- Phase 1 focus: Stabilize core workflows with markdown
- Phase 4 (or later): Add SurrealDB as **optional caching/indexing layer**
- Future state: Markdown remains source of truth, SurrealDB provides performance

---

## Implementation Plan

### Immediate Actions (Week 1)

1. **Deprecate SurrealDB in current codebase**
   - Comment out `SurrealStore` initialization in GUI/CLI
   - Add `TODO` comments for future migration
   - Keep `store/` module code but mark as inactive

2. **Ensure all workflows use markdown**
   - Audit all Tauri commands to verify they read/write markdown files
   - Remove any DB queries that bypass markdown layer
   - Test round-trip: GUI edit → markdown file → reload GUI

3. **Document migration path**
   - Create `SURREALDB_MIGRATION.md` with future design
   - Specify: SurrealDB as read cache, markdown as write source
   - Design: On file change → invalidate cache → rebuild from markdown

### Future Migration (Phase 4+)

When core is stable, consider SurrealDB for:
- **Read Performance**: Index goals, phases, daily notes for fast queries
- **Graph Queries**: Dependency trees, reverse lookups, critical path
- **Caching**: Avoid re-parsing markdown on every read

**Migration Strategy**:
- Markdown remains **write source** (single source of truth)
- SurrealDB becomes **read cache** (rebuilt on file change)
- On startup: Load markdown → populate SurrealDB
- On file change: Invalidate cache → rebuild affected records
- Never write directly to SurrealDB (only through markdown)

---

## Success Criteria

**Phase 1 Complete** when:
- ✅ All CLI commands read/write markdown exclusively
- ✅ All GUI operations persist to markdown files
- ✅ Zero SurrealDB dependencies in active code paths
- ✅ Round-trip tests pass (create → edit → reload)

**Future Migration Ready** when:
- ✅ Markdown workflows are stable and tested
- ✅ Performance bottlenecks identified (if any)
- ✅ SurrealDB design specifies clear read-only caching role

---

## Notes

- **Backward Compatibility**: This decision is fully backward compatible (we're removing complexity, not changing formats)
- **Flexibility Preserved**: SurrealDB can be added later without breaking changes
- **Alignment with Mission**: Markdown-first supports "Leave a Trace" (human-readable audit trail)

---

**Approved by:** Architect
**Reviewed by:** Claude
**Next Review:** After Phase 1 completion
