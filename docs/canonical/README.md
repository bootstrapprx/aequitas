# Canonical Contracts

**Status:** AUTHORITATIVE
**Last Updated:** 2025-12-16
**Maintainer:** Aequitas Backend Team

---

## What Does "Canonical" Mean?

The documents in this folder are **authoritative contracts** that govern the behavior, structure, and boundaries of the Aequitas accounting system. They are:

- **Frozen specifications** - Code must conform to them, not vice-versa
- **Source of truth** - When code and docs disagree, docs win (then fix the code)
- **Non-negotiable** - Changes require formal review and versioning
- **Immutable by default** - Modifications are rare and deliberate

**These are NOT:**
- Implementation suggestions
- Aspirational goals
- Living documents that change with code
- Optional guidelines

**Philosophy:**
> "Documentation is law. Database is the final authority. APIs are contracts, not conveniences. Accounting correctness > developer comfort."

---

## Canonical Documents

### 1. [DATA_DICTIONARY.md](DATA_DICTIONARY.md)

**Purpose:** Database schema reference (Phase 1-2)

**Authority:** PostgreSQL schema at Alembic revision 023 (head)

**Contents:**
- Table definitions with field types
- Relationships (UUID foreign keys only)
- Constraints and indexes
- Enum type definitions
- Migration history

**When to consult:**
- Adding new database models
- Understanding table relationships
- Validating data integrity rules

---

### 2. [API_BOUNDARIES.md](API_BOUNDARIES.md)

**Purpose:** Frozen API surface definition

**Authority:** Phase 3C security & accounting requirements

**Contents:**
- Complete inventory of allowed operations
- Explicit list of forbidden operations
- Permission model (view / manage / superuser)
- Rate limiting strategy
- Security rationale for every boundary

**When to consult:**
- Implementing new API endpoints
- Reviewing security implications
- Understanding permission requirements
- Designing client integrations

**Key principle:** Assume hostile or buggy clients. Every endpoint must enforce invariants at the service layer.

---

### 3. [PHASE_3C1_DTO_SPECIFICATION.md](PHASE_3C1_DTO_SPECIFICATION.md)

**Purpose:** Canonical data transfer object definitions

**Authority:** Phase 3C-1 API contract design

**Contents:**
- 8 canonical DTOs with complete field specifications
- Field classification (REQUIRED / OPTIONAL / READ_ONLY / SERVER_CONTROLLED / CLIENT_CONTROLLED)
- Lock & immutability overlay (which fields freeze when)
- OpenAPI-ready schema definitions
- Excluded fields rationale (deprecated, internal-only)

**When to consult:**
- Creating Pydantic schemas
- Implementing API request/response handlers
- Understanding field mutability rules
- Generating API documentation

**Key principle:** No deprecated fields exposed. UUID-based relationships only. Locked fields are READ_ONLY.

---

### 4. [PHASE_3C2_WRITE_APIS.md](PHASE_3C2_WRITE_APIS.md)

**Purpose:** Complete write API specification

**Authority:** Phase 3C-2 write operations design

**Contents:**
- 17 write endpoint definitions
- Controller skeletons (thin, validation-only)
- Service layer method contracts
- Explicit rejection matrix (error codes for every failure mode)
- Audit hook requirements (who/when/what/why)
- Transaction safety patterns
- Rate limiting configuration

**When to consult:**
- Implementing write endpoints
- Understanding error handling
- Designing audit trails
- Validating immutability enforcement

**Key principle:** Defensive by default. No business logic in controllers. Explicit error codes for deterministic failures.

---

## Hierarchy of Authority

When conflicts arise, resolve in this order:

1. **PostgreSQL Schema** (Alembic revision 023)
   - Database is the final authority
   - If migration differs from docs, migration wins (then update docs)

2. **Canonical Contracts** (this folder)
   - API_BOUNDARIES.md → Security & operations
   - PHASE_3C1_DTO_SPECIFICATION.md → Data contracts
   - PHASE_3C2_WRITE_APIS.md → Endpoint behavior
   - DATA_DICTIONARY.md → Schema reference

3. **Service Layer Implementation**
   - Phase 3B services enforce business rules
   - Must align with contracts above

4. **API Layer Implementation**
   - FastAPI routers/controllers
   - Must delegate to services
   - Must not contain business logic

**If service layer and canonical contracts disagree:** Contracts win. Fix the service layer.

**If API layer and service layer disagree:** Service layer wins. Fix the API layer.

---

## Change Control Process

### To Modify a Canonical Document:

1. **Propose change** with justification (security, GAAP compliance, bug fix)
2. **Review with team** - Impacts on:
   - Database migrations
   - Service layer logic
   - API contracts
   - Client integrations
   - Accounting correctness
3. **Update document** with version number and changelog
4. **Implement change** in code to match updated contract
5. **Verify tests** confirm new contract is enforced

### ❌ Do NOT:
- Change code first, then update docs
- Make "temporary" changes
- Add undocumented endpoints
- Relax validation rules without updating contracts

---

## Using These Contracts

### For Backend Developers:

**Before implementing a new endpoint:**
1. Check `API_BOUNDARIES.md` - Is this operation allowed?
2. Check `PHASE_3C1_DTO_SPECIFICATION.md` - What DTOs are required?
3. Check `PHASE_3C2_WRITE_APIS.md` - What validation rules apply?
4. Implement service layer logic first
5. Implement thin controller that delegates to service
6. Return errors matching canonical error codes

**Before adding a database field:**
1. Check `DATA_DICTIONARY.md` - Does it align with schema?
2. Create Alembic migration
3. Update `DATA_DICTIONARY.md` if foundational change
4. Update DTOs if field should be exposed via API

### For Frontend Developers:

**Before calling an API endpoint:**
1. Check `API_BOUNDARIES.md` - Is this operation permitted?
2. Check `PHASE_3C1_DTO_SPECIFICATION.md` - What request/response shape?
3. Check `PHASE_3C2_WRITE_APIS.md` - What error codes can occur?
4. Handle all documented error codes
5. Never assume silent failure modes

**Before caching data:**
1. Check immutability rules in `PHASE_3C1_DTO_SPECIFICATION.md`
2. POSTED journal entries are immutable
3. LOCKED accounts have immutable fields
4. CLOSED fiscal periods may reopen (superuser only)

### For QA/Testing:

**Test that invariants actually hold:**
1. Locked accounts reject immutable field changes
2. POSTED entries cannot be edited
3. Journal entries must balance (debits = credits)
4. Fiscal periods cannot overlap
5. Error codes match specification

**Failure modes to test:**
1. Buggy client sends invalid data
2. Malicious client attempts to bypass validation
3. Race conditions (concurrent writes)
4. Permission boundary violations

---

## Accounting Correctness First

These contracts exist to ensure:
- **GAAP compliance** - Double-entry accounting rules enforced
- **Audit integrity** - Immutable records after posting
- **Fiscal period controls** - Period boundaries respected
- **Account locking** - Structural changes prevented after first transaction
- **Permission boundaries** - Superuser operations properly protected

**When in doubt:** Reject the request with an explicit error code.

**Never compromise** accounting correctness for:
- Developer convenience
- Performance optimization
- Client requests
- Backward compatibility

---

## Document Metadata

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| DATA_DICTIONARY.md | 1.0 | 2025-12-14 | Canonical |
| API_BOUNDARIES.md | 1.0 | 2025-12-16 | Frozen |
| PHASE_3C1_DTO_SPECIFICATION.md | 1.0 | 2025-12-16 | Canonical |
| PHASE_3C2_WRITE_APIS.md | 1.0 | 2025-12-16 | Canonical |

---

## Questions?

**"Can I add a new endpoint?"**
→ Check `API_BOUNDARIES.md` first. If not documented, assume forbidden.

**"Can I expose this field via API?"**
→ Check `PHASE_3C1_DTO_SPECIFICATION.md`. If not listed, assume internal-only.

**"Can I modify a POSTED journal entry?"**
→ No. `PHASE_3C2_WRITE_APIS.md` specifies POSTED entries are immutable (void only).

**"Can I skip double-entry validation for performance?"**
→ No. GAAP compliance is non-negotiable.

**"The client needs to bypass this validation..."**
→ No. Validation exists for accounting correctness, not developer convenience.

---

**Remember:** Code must conform to contracts. Contracts do not bend to code.
