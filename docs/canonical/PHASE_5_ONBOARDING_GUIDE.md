

# 🚀 Phase 5 — Company Onboarding Guide

**(Company → Template → Accounts → Periods → Activation)**

## Status

* **Phase:** 5
* **Purpose:** Make accounting usable *without allowing users to break accounting*
* **Audience:** Product, Frontend, Backend, QA
* **Authority Level:** Canonical (binds implementation)

---

## 1. Phase 5 Philosophy

### Core Principle

> **Onboarding is a guided state machine, not a configuration screen.**

Users never “design accounting.”
They **instantiate**, **review**, and **activate** a canonical system.

### Non-Goals

* No free-form chart creation
* No early transaction entry
* No bypassing irreversible decisions
* No accounting jargon unless necessary

---

## 2. Onboarding State Machine (System Truth)

| State               | Description                                | User Can Exit?  |
| ------------------- | ------------------------------------------ | --------------- |
| `DRAFT`             | Company exists, accounting not initialized | ✅ Yes           |
| `TEMPLATE_SELECTED` | Template chosen, not materialized          | ✅ Yes           |
| `CHART_READY`       | Accounts created from template             | ⚠️ With warning |
| `CHART_FINALIZED`   | Accounts reviewed                          | ⚠️ With warning |
| `ACTIVE`            | Accounting live                            | ❌ No            |

These states **must** be persisted and enforced backend-side.

---

## 3. Wizard Steps (UX Mapping)

### Step 0 — Welcome

Purpose: Set expectations and reduce fear.

**Edge UX Rules**

* User may exit safely
* Progress is saved
* No irreversible actions here

---

### Step 1 — Company Details

**Edge Cases**

* ❗ User leaves mid-form → draft saved
* ❗ User changes jurisdiction later → allowed *only before template selection*
* ❗ Currency mismatch warning if user later selects incompatible template

**UX Rule**

> Company identity is editable until template is selected.

---

### Step 2 — Choose Accounting Template

**Critical UX Moment**

**Edge Cases**

* ❗ User clicks “Back” after selecting template
  → Allowed until accounts are materialized
* ❗ User attempts to change template later
  → Blocked with explanation
* ❗ No template available for jurisdiction
  → Show “Contact Admin” / “Request Template”

**UX Safeguard**

* Mandatory confirmation modal
* Clear “cannot change later” warning

---

### Step 3 — Build Your Chart (Materialization)

**System-Controlled Step**

**Edge Cases**

* ❗ Network failure mid-process
  → Rollback transaction, retry allowed
* ❗ User closes browser
  → On resume, system detects incomplete materialization and resumes or restarts safely
* ❗ Partial failure
  → Entire operation rolled back (atomic)

**UX Rule**

> This step is never partially visible. Either “in progress” or “complete.”

---

### Step 4 — Review & Customize Accounts

**Allowed Actions**

* Rename accounts
* Add custom accounts
* Disable non-mandatory accounts

**Edge Cases**

* ❗ User disables too many accounts
  → Soft warning (“You can re-enable later”)
* ❗ User attempts to delete mandatory account
  → Disabled with tooltip
* ❗ User adds custom account with conflicting type
  → Blocked (template consistency)

**UX Rule**

> “Flexible but bounded.”

---

### Step 5 — Set Fiscal Periods

**Edge Cases**

* ❗ User creates overlapping dates
  → Visual block + explanation
* ❗ User creates no OPEN period
  → Block progression
* ❗ User chooses odd fiscal year start
  → Allowed, but preview shown

**UX Rule**

> Periods must *visually* show why overlap is invalid.

---

### Step 6 — Activate Accounting (Point of No Return)

**Critical UX Moment**

**Edge Cases**

* ❗ User clicks Activate accidentally
  → Confirmation checkbox required
* ❗ User lacks permission
  → Button disabled + explanation
* ❗ Backend validation fails
  → Clear error (“Fix highlighted steps before activation”)

**UX Rule**

> Activation must feel intentional, not casual.

---

## 4. Post-Activation UX

### Completion Screen

* Clear success message
* No technical jargon
* Suggest next steps

### Edge Cases

* ❗ User tries to reopen wizard
  → Read-only summary view
* ❗ User tries to rematerialize chart
  → Blocked, explanation shown

---

## 5. Global UX Edge Cases (Cross-Step)

### 5.1 Abandonment

* Wizard progress auto-saved
* Resume banner shown on dashboard:

  > “Finish setting up accounting”

### 5.2 Multi-Tab / Multi-Session

* Detect concurrent onboarding
* Lock wizard to one active session
* Show “Another session is editing setup”

### 5.3 Permission Changes Mid-Wizard

* If user loses superuser role:

  * Freeze wizard
  * Show explanation
  * Require authorized user to continue

### 5.4 Data Drift

* If backend state changes externally:

  * Wizard reloads from system state
  * UI reconciles automatically

---

## 6. UX Error Handling Standards

All errors must be:

* Human-readable
* Actionable
* Non-technical

**Bad**

> “LOCKED_ACCOUNT”

**Good**

> “This account is locked because it has been used in a transaction.”

---

## 7. What Phase 5 Explicitly Does NOT Do

* ❌ No journal entry creation
* ❌ No report generation
* ❌ No account locking yet
* ❌ No audit-heavy workflows

Phase 5 ends when:

> **The company can safely start accounting.**

---

## 8. Phase 5 Acceptance Criteria (UX + System)

Phase 5 is **complete** when:

* ✅ User can onboard without accounting knowledge
* ✅ Irreversible steps are clearly communicated
* ✅ No backend invariant can be violated via UI
* ✅ Abandon/resume works reliably
* ✅ Errors guide the user forward
* ✅ Activation results in `ACTIVE` state with:

  * Chart
  * Periods
  * Zero transactions

---

## 9. Phase 5 → Phase 6 Handoff

After Phase 5:

* Phase 6 begins with **Operational Accounting**
* All locks, immutability, and audit trails become active
* Wizard becomes read-only reference

---

## Final Note (Important)

This guide is not “just UX.”
It is **the user-facing expression of your accounting invariants**.

If frontend follows this guide faithfully:

* Backend will never be abused
* Accounting integrity will survive user behavior
* Support load will be dramatically lower

