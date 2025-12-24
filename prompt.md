
Canon → Entity Responsibility Map
1) Company

Canon: II (Authority), III (Evolution)

Role: System container and lifecycle owner.

Stateful: Yes
Lifecycle States: DRAFT → TEMPLATE_SELECTED → CHART_READY → ACTIVE

Mutability Rules:

Pre-ACTIVE: Mutable (within onboarding rules)

ACTIVE: Structurally immutable

Allowed Actions:

Create (system)

Transition state (service-layer only)

Read (all roles with access)

Forbidden After ACTIVE:

Reset onboarding

Structural deletion of accounting data

Backward state transitions

Notes:
Company state gates all downstream mutability.

2) MasterAccount

Canon: I (Accounting Truth)

Layer: Root / Branch (global concepts & structure)

Stateful: Versioned (not mutable)

Mutability Rules:

Never mutable in-place

Changes only via versioned publication

Allowed Actions:

Read (global)

Map (CompanyAccount → MasterAccount)

Forbidden:

Embedding facts (vendors, banks, properties)

Company-specific customization

Post-publication mutation

Notes:
Advisory hints (e.g., vendor matches) do not belong here long-term.

3) CompanyAccount

Canon: I (Structure), III (Lifecycle)

Layer: Leaf (posting endpoint)

Stateful: Yes

Mutability Rules:

Pre-ACTIVE: Create / rename / enable-disable

ACTIVE:

Create (if explicitly allowed by policy)

Disable (with safeguards)

Never delete if referenced

Allowed Actions:

Map to exactly one MasterAccount

Receive postings

Forbidden:

Fact-encoded naming

Re-mapping historical postings

Deletion after use

Notes:
CompanyAccount is where structure ends and truth begins.

4) JournalEntry

Canon: I (Truth), II (Authority), III (Time)

Layer: Truth-bearing record

Stateful: Append-only

Mutability Rules:

Never mutable

Corrections only via new entries

Allowed Actions:

Create (service-layer validated)

Read (authorized roles)

Forbidden:

Update

Delete

Backdate without explicit policy

Notes:
This is the highest-integrity object in the system.

5) JournalEntryLine

Canon: I (Truth)

Layer: Atomic accounting fact

Mutability Rules:

Inherits JournalEntry immutability

Allowed Actions:

Create as part of balanced entry

Forbidden:

Standalone mutation

Partial edits

6) FiscalPeriod

Canon: III (Time)

Stateful: Yes

Mutability Rules:

Open: Limited configuration allowed

Closed: Fully immutable

Allowed Actions:

Open / close (policy-governed)

Enforce posting constraints

Forbidden:

Deletion after postings

Reopening without audit trail

Notes:
FiscalPeriod enforces time discipline across the ledger.

7) Mapping (CompanyAccount ↔ MasterAccount)

Canon: I (Structure), II (Authority)

Stateful: Yes (decision-tracked)

Mutability Rules:

Pre-ACTIVE: Editable

ACTIVE:

Changes require explicit decision records

Never retroactive

Allowed Actions:

Accept

Override (with reason)

Reject

Forbidden:

Silent remaps

Historical reinterpretation

Notes:
Mappings are interpretive, not destructive.

8) SandboxScenario

Canon: IV (Human Protection), III (State Separation)

Layer: Parallel, non-truth environment

Stateful: Yes (isolated)

Mutability Rules:

Fully mutable

Fully discardable

Allowed Actions:

Create

Modify

Compare

Delete

Forbidden:

Writing to real ledger

Creating obligations

Notes:
Sandbox is truth-adjacent, never truth-bearing.

9) Projection / Forecast Objects

Canon: IV (Guidance)

Layer: Analytical (Fruit-level)

Mutability Rules:

Fully mutable

Versionable

Allowed Actions:

Estimate

Bind (revenue ↔ expense)

Simulate scenarios

Forbidden:

Auto-commit to ledger

Implicit promotion to budget

10) Dexter Insight / Suggestion

Canon: IV (Intelligence Boundary)

Layer: Advisory only

Stateful: Optional (logged)

Mutability Rules:

Stateless or append-only logs

Allowed Actions:

Observe

Suggest

Ask

Forbidden:

Execute

Persist changes

Decide outcomes

Notes:
Dexter never crosses into authority.

11) User / Role / Permission

Canon: II (Authority)

Stateful: Yes

Mutability Rules:

Role assignment controlled

Permissions bounded by canon

Forbidden:

Canon override by role

“God mode” behaviors

STEP 1 — RESULT

You now have:

A complete entity responsibility map

Explicit immutability boundaries

Clear canon ownership per entity

Zero ambiguity about who can do what, when

This is the contract we will now enforce.



Step 2: Canon → Schema Invariants.

This step converts the responsibility map into mechanical impossibilities.
Goal: even bad code cannot violate the canon.

Below are explicit invariants, grouped by entity, with where they must be enforced (DB / Service / Both). No redesign—only enforcement.

STEP 2
Canon → Schema Invariants
A. Company (Lifecycle & Irreversibility)

Invariant A1 — Monotonic State

Rule: onboarding_status may only advance forward.

Enforce: Service + DB

Service: transition guard (already present)

DB: CHECK constraint or trigger preventing backward transitions

Invariant A2 — Activation Lock

Rule: Once onboarding_status = ACTIVE, structural data is immutable.

Enforce: Service + DB

Service: guards (patch applied)

DB: triggers rejecting deletes/updates on protected tables when company is ACTIVE

Invariant A3 — No Destructive Reset Post-ACTIVE

Rule: No deletion of accounting data for ACTIVE companies.

Enforce: DB

Triggers on DELETE for JournalEntry, JournalEntryLine, FiscalPeriod, CompanyAccount

Reject if parent company is ACTIVE

B. MasterAccount (Accounting Truth)

Invariant B1 — Immutability

Rule: No UPDATE or DELETE after publication.

Enforce: DB

Disable UPDATE/DELETE; allow INSERT only for new versions

Invariant B2 — Concept-Only

Rule: No fact-bearing fields (vendors, banks, properties).

Enforce: Schema

Remove or deprecate fact-like columns (or move to advisory tables)

NOT NULL constraints limited to conceptual fields only

Invariant B3 — Versioned Reads

Rule: Company mappings must reference a specific MasterAccount version.

Enforce: DB

FK includes master_account_version_id

C. CompanyAccount (Leaf / Posting Endpoint)

Invariant C1 — Single Master Mapping

Rule: Each CompanyAccount maps to exactly one MasterAccount.

Enforce: DB

NOT NULL FK

UNIQUE(company_id, company_account_id) → master_account_id

Invariant C2 — No Deletion After Use

Rule: If referenced by any JournalEntryLine, deletion is forbidden.

Enforce: DB

FK with RESTRICT

No CASCADE

Invariant C3 — Rename Without Reinterpretation

Rule: Renaming does not affect historical postings.

Enforce: Service

Prevent remapping on rename

No retroactive effects

D. JournalEntry & JournalEntryLine (Truth Records)

Invariant D1 — Append-Only Ledger

Rule: No UPDATE or DELETE.

Enforce: DB

Triggers rejecting UPDATE/DELETE

Invariant D2 — Balanced Entry

Rule: Sum(debits) = Sum(credits).

Enforce: Service

Validation before persistence

Invariant D3 — Period Locking

Rule: Cannot post to CLOSED periods.

Enforce: Service + DB

Service validation

Optional DB trigger referencing FiscalPeriod status

Invariant D4 — Atomicity

Rule: JournalEntry and lines persist together or not at all.

Enforce: DB

Transactional integrity

E. FiscalPeriod (Time Discipline)

Invariant E1 — Close Is Final

Rule: CLOSED periods are immutable.

Enforce: DB

Trigger rejecting UPDATE on CLOSED rows

Invariant E2 — No Deletion After Posting

Rule: If any JournalEntry exists, deletion is forbidden.

Enforce: DB

FK RESTRICT

Invariant E3 — No Overlaps

Rule: Periods may not overlap.

Enforce: DB

EXCLUDE constraint on date ranges (or equivalent)

F. Mapping Decisions (Interpretation Layer)

Invariant F1 — Decision Required

Rule: Mapping changes require explicit decision records.

Enforce: Service

No direct UPDATE without decision log

Invariant F2 — Non-Retroactivity

Rule: Mapping changes apply prospectively only.

Enforce: Service

Effective-date enforcement

G. Sandbox & Projections (Isolation)

Invariant G1 — Physical Isolation

Rule: Sandbox tables never FK into ledger tables.

Enforce: DB

Separate schema or database

Invariant G2 — No Promotion Without Explicit Action

Rule: Sandbox data cannot auto-create real objects.

Enforce: Service

Explicit promotion APIs only

H. Dexter (Intelligence Boundary)

Invariant H1 — No Write Access

Rule: Dexter code path cannot write to truth tables.

Enforce: Service + Permissions

Read-only DB role

Write access denied at connection level

Invariant H2 — Explainability

Rule: Every suggestion has a source.

Enforce: Service

Require rationale payloads

I. Cross-Cutting Safeguards

Invariant I1 — No CASCADE Deletes on Truth Tables

Rule: CASCADE is forbidden for accounting truth.

Enforce: Schema Review

Invariant I2 — Explicit Errors Only

Rule: Silent failures forbidden.

Enforce: Service

No try/except swallowing

STEP 2 — RESULT

You now have a mechanical safety net:

Canon violations become DB errors, not opinions

Service-layer guards align with schema constraints

Admin power is bounded by physics, not policy

History is structurally indestructible

NEXT STEP

Option 1 — Step 3: Canon → Lifecycle Constraints (State Transitions)

We’ll formalize:

exact transition matrices

allowed actions per state

enforcement points



STEP 3
Canon → Lifecycle Constraints (State Machine Contract)
1) Canonical States (Company.onboarding_status)

The company lifecycle is a deterministic state machine with these states:

DRAFT

TEMPLATE_SELECTED

CHART_READY

ACTIVE

Rule: States are monotonic (no backwards transitions).
Rule: ACTIVE is a Point of No Return.

2) Allowed Transitions (Only These)
From	To	Trigger
DRAFT	TEMPLATE_SELECTED	template chosen + company identity confirmed
TEMPLATE_SELECTED	CHART_READY	chart materialized successfully (idempotent)
CHART_READY	ACTIVE	activation endpoint succeeds

Forbidden transitions:

any backward move (e.g., ACTIVE → DRAFT)

skipping forward without satisfying prerequisites

Enforcement: Service-layer transition guard + DB-level monotonic enforcement (trigger/constraint).

3) State-Scoped Capabilities (What is allowed when)
A) DRAFT

Allowed

Create company

Edit company identity fields

Choose template

Abort/delete company (if no truth created)

Forbidden

Create fiscal periods

Create journal entries

Activate accounting

Enforcement

API: routes hidden/guarded

Service: hard checks for protected actions

B) TEMPLATE_SELECTED

Allowed

Save onboarding “scope” choices

Materialize chart (must be idempotent)

Review/prepare mappings

Configure pre-activation options

Forbidden

Create journal entries

Close periods

Activate without chart ready

Enforcement

Service: requires template selected for materialization

Materialization must return success if already done

C) CHART_READY

Allowed

Account review / customization (rename, enable/disable, add leaf accounts)

Setup fiscal periods (create/open periods)

Validate readiness for activation

Mapping review decisions (accept/override/reject) as needed

Forbidden

Posting journal entries unless explicitly allowed (recommend: forbidden)

Deleting required template accounts

Reset after truth creation (depends on policy; safest: allow reset only if no truth records exist)

Enforcement

Service validation of account edits

Period overlap and validity checks

Guard activation prerequisites

D) ACTIVE (Point of No Return)

Allowed

Post journal entries (append-only)

Close fiscal periods (with audit)

Create additional leaf accounts (policy-controlled)

Disable accounts (never delete) with safeguards

Add dimensions/fruits

Run reporting, analytics, consolidation

Use Sandbox mode (always isolated)

Forbidden (Absolute)

reset_onboarding

deletion of truth records (JournalEntry, lines)

deletion of fiscal periods with postings

backward onboarding transitions

reinterpreting history via remapping without prospective rules

any operation that rewrites accounting history

Enforcement

Service-level: state gating for all destructive endpoints

DB-level: triggers preventing UPDATE/DELETE on truth tables

Permission model cannot override this

4) Action Matrix (High Signal)

Legend: ✅ Allowed | 🟡 Allowed with constraints | ❌ Forbidden

Action	DRAFT	TEMPLATE_SELECTED	CHART_READY	ACTIVE
Choose template	✅	🟡 (change allowed until chart materialized)	❌	❌
Materialize chart	❌	✅ (idempotent)	🟡 (idempotent no-op)	❌
Customize accounts	❌	❌	✅	🟡 (no deletes; no history rewrite)
Create fiscal periods	❌	❌	✅	🟡 (strict rules; no overlaps)
Post journal entries	❌	❌	❌ (recommended)	✅
Close fiscal periods	❌	❌	❌	✅
Reset onboarding	✅ (if empty)	✅ (if no truth)	🟡 (only if no truth)	❌
Sandbox simulate	✅	✅	✅	✅

This matrix is the operational translation of Canon III.

5) Prerequisites (Hard Checks)
Activation prerequisites (CHART_READY → ACTIVE)

Must be true:

master chart materialized

required accounts exist and mapped

at least one fiscal period defined

onboarding steps complete (as per service rules)

company is in CHART_READY

Enforcement: Activation endpoint calls a single validator that returns explicit reasons.

6) Idempotency Requirements (No Deadlocks)

Certain actions must be idempotent to prevent onboarding lock traps:

Materialize chart
If already CHART_READY, return success (no error).

Setup fiscal periods
Repeated calls with identical inputs must not duplicate or corrupt.

Activation
Repeated calls after ACTIVE must return success or explicit “already active”.

Enforcement: Service-level idempotency + DB unique constraints.

7) Audit & Traceability Requirements (State Changes)

Every transition must produce:

actor identity

timestamp

from_state / to_state

reason / metadata

Enforcement: Service layer writes to audit log table.

8) Definition of Done for Step 3

This lifecycle contract is complete when:

Every major operation is tied to an allowed state

Forbidden actions are explicitly listed

ACTIVE is irreversible by design

Idempotent actions prevent onboarding traps

Enforcement points are identified


This is the last step 
Its purpose is simple and critical:

Define exactly where the system is allowed to grow — and where it never may.

After this, there is no ambiguity about:

where facts live,

where intelligence lives,

where projections live,

and where accounting truth is protected.

 STEP 4
Canon → Extension Boundaries (Zones of Growth)
1) The Fundamental Rule

Accounting truth is finite.
Interpretation, analysis, and simulation are infinite.

Growth is allowed only outside the truth-bearing core.

2) Canonical Zones of the System

The system is divided into four zones, each with explicit permissions.

ZONE A — TRUTH CORE (SEALED)

Governed by: Canon I, II, III
Entities include:

MasterAccount

CompanyAccount

JournalEntry

JournalEntryLine

FiscalPeriod

Company (post-ACTIVE)

Rules:

Append-only or versioned

No destructive operations

No fact embedding

No AI writes

No projections

No sandbox artifacts

Allowed Changes:

New JournalEntries (append-only)

Closing periods

Prospective structure additions (policy-bound)

Forbidden Forever:

Reinterpretation of history

Fact-based mutation

Silent normalization

Retroactive mapping

This zone never learns.
It only records.

ZONE B — STRUCTURAL EXTENSIONS (CONTROLLED)

Governed by: Canon I & III
Entities include:

CompanyAccount creation (leaf-level)

Branch-level organization (where applicable)

Mapping decision records

Rules:

Must map to existing MasterAccounts

Must never embed instances

Must never rewrite history

Changes are prospective only

Allowed Growth:

New leaf accounts

New branch groupings

New mapping decisions (with audit)

Forbidden:

Altering MasterAccounts

Retroactive effects

This zone grows slowly and deliberately.

ZONE C — INTERPRETATION & INTELLIGENCE (ADVISORY)

Governed by: Canon IV
Entities include:

Dexter insights

Pattern detection

Vendor suggestions

Category hints

Confidence scores

Explanation metadata

Rules:

Read-only access to Truth Core

No write access to accounting tables

Suggestions must be explainable

Must require human confirmation

Explicit Placement Rule (IMPORTANT):
Anything like:

default_vendors

matches_vendor

heuristic mappings

MUST live here, not in MasterAccount.

This resolves Audit Finding A1-01 cleanly.

This zone thinks.
It never acts.

ZONE D — SIMULATION & FUTURE (ISOLATED)

Governed by: Canon IV & III
Entities include:

SandboxScenario

Projections

Forecasts

What-if bindings (revenue ↔ expense)

Scenario comparisons

Rules:

Physically isolated schema or database

No foreign keys into Truth Core

No automatic promotion

Fully discardable

Allowed Growth:

Arbitrarily complex models

Scenario versioning

User experimentation

Dexter-assisted projections

Forbidden:

Writing truth

Creating obligations

Silent carryover to budget

This zone imagines.
It never commits.

3) Boundary Enforcement Summary
Boundary	Enforced By
Truth ↔ Intelligence	DB permissions + service guards
Truth ↔ Sandbox	Physical schema separation
Structure ↔ Facts	Schema design + naming rules
Intelligence ↔ Authority	Read-only roles
Sandbox ↔ Reality	Explicit promotion APIs only
4) Migration of Existing Leaks (Non-Destructive)

Any existing logic that:

embeds vendor hints in MasterAccount

mixes AI metadata with structure

stores projections alongside truth

must be relocated, not deleted.

Migration rules:

Move → Advisory tables

Preserve history

No reinterpretation

5) Final Extension Rule (Lock This In)

If a feature needs freedom,
it does not belong in the Truth Core.

This single rule will prevent:

chart pollution

AI overreach

retroactive chaos

future regret

