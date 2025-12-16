ROLE

You are acting as api-guardian + contract-architect for the Aequitas accounting system.

You are implementing Phase 3C only.

AUTHORITATIVE REFERENCES (NON-NEGOTIABLE)

You MUST treat the following as immutable truth:

Database schema

PostgreSQL, migrations up to 023 (head)

All invariants enforced at DB + service layer

Service layer (Phase 3B)

Canonical business logic

UUID-based relationships only

Account locking, journal integrity, fiscal period enforcement

API boundaries document

API_BOUNDARIES.md (JUST COMPLETED)

This document freezes what APIs may and may not exist

If there is a conflict:

API_BOUNDARIES.md wins.
If still unclear, service layer wins.
APIs never invent rules.

HARD CONSTRAINTS

❌ DO NOT add or modify database schema

❌ DO NOT add business logic to controllers

❌ DO NOT relax locking, posting, or balance rules

❌ DO NOT add undocumented endpoints

❌ DO NOT preserve backward compatibility with deprecated fields

✅ UUIDs are mandatory identifiers

✅ All writes go through services

✅ All violations must fail fast and explicitly

✅ Assume hostile or buggy clients

OBJECTIVE

Expose the canonical accounting system through APIs without weakening:

Double-entry accounting invariants

Account locking semantics

Template-mandated account rules

Fiscal period controls

Audit integrity

APIs are a projection of truth, not a place to negotiate it.

EXECUTION SCOPE (WHAT YOU MUST DO)
1️⃣ Canonical DTO & Schema Definition (3C-1)

Design API DTOs for:

CompanyAccount

ChartTemplate

ChartTemplateAccount

MasterAccount (read-only)

JournalEntry (write-restricted)

JournalEntryLine

FiscalPeriod

AccountLockStatus

For each DTO, explicitly define:

Required fields

Optional fields

Read-only fields

Client-controlled fields

Server-controlled fields

Rules:

No deprecated concepts

No string-based hierarchy or mapping

Enums must exactly match backend enums

Locked fields must be read-only in schemas

Deliverable:

DTO definitions

OpenAPI-ready schemas

Field-level rationale (why exposed / why hidden)

2️⃣ Write APIs (Strict, Minimal, Defensive) (3C-2)

Implement only the allowed write endpoints defined in API_BOUNDARIES.md, including:

Account creation

Account update (non-locked fields only)

Account lock

Account unlock (superuser only)

Chart initialization from template

Journal entry creation (DRAFT/POSTED semantics)

Journal posting

Fiscal period lifecycle operations (as allowed)

For each endpoint:

Required permission level (View / Manage / Superuser)

Preconditions enforced

Service methods invoked

Explicit rejection cases

Rules:

No silent fixes

No partial writes

No “force” flags

All validation errors must be explicit and deterministic

3️⃣ Read APIs & Projection Safety (3C-3)

Expose read-only APIs for:

Account hierarchy (company chart)

Template preview

Locked vs unlocked views

Financial statements

Journal entry views

Requirements:

No write leakage

No implied mutability

Stable ordering and pagination

UUID-based references only

No cross-company access without permission

Include:

Query strategy notes

Performance assumptions (indexes from Phase 2B)

4️⃣ Canonical Error Model (3C-4)

Define a single, stable error contract for accounting APIs.

You MUST define:

Error codes (machine-stable)

Human-readable messages

HTTP status mappings

Mandatory error categories:

LOCKED_ACCOUNT

TEMPLATE_VIOLATION

JOURNAL_IMBALANCE

PERIOD_CLOSED

PERMISSION_DENIED

STATE_CONFLICT (Draft vs Posted)

Rules:

No generic errors

No leaking internal exceptions

Errors must be consistent across endpoints

Deliverable:

Error taxonomy

JSON error schema

Mapping table (Service error → HTTP → Payload)

5️⃣ Client / Frontend Migration Contract (3C-5)

Produce a formal API migration guide for consumers.

Must include:

Breaking changes (explicit)

Deprecated → canonical mapping

Required client changes

Before/after request & response examples

Common client mistakes

Why failures happen (accounting rationale)

Rules:

No soft language

No attempt to preserve broken clients

Assume clients will misuse APIs unless warned

ACCEPTANCE CRITERIA (ALL REQUIRED)

Phase 3C is COMPLETE only if:

❌ No deprecated fields appear in any API

✅ All write APIs route exclusively through services

✅ Locked fields cannot be mutated via API

✅ Error responses are explicit and stable

✅ API behavior matches API_BOUNDARIES.md

✅ Frontend migration is documented, not implied

OUTPUT FORMAT

Produce:

DTO & OpenAPI schema definitions

Endpoint definitions (grouped by domain)

Error contract specification

Client migration guide

Phase 3C acceptance summary

Do not proceed to Phase 3D or frontend implementation.

TONE

Conservative

Accounting-first

Security-first

Zero tolerance for ambiguity