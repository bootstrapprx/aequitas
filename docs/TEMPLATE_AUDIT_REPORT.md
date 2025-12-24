# Accounting Template Audit Report

**Date:** 2025-12-24
**Auditor:** Antigravity (Senior Accounting Systems Auditor)
**Scope:** `seed_chart_templates.py`, `MasterAccount` model, Onboarding Logic

## Executive Summary

The current accounting templates used in onboarding are **STRUCTURALLY UNSAFE** and violate the Aequitas Accounting Canon.

- **US GAAP Standard**: Contains only **6 accounts**. Missing entire accounting categories (Equity, Taxes, most Liabilities).
- **US GAAP Simplified**: Contains only **5 accounts**. Identical structural failures.
- **IFRS Standard**: Contains **0 active accounts**. The template references IFRS-style codes (e.g., `1.10.10.10`) which **do not exist** in the Master Chart (which uses 5-digit GAAP codes).

**Verdict:** The system currently allows companies to onboard with broken Charts of Accounts that cannot support double-entry bookkeeping, fiscal closing, or valid reporting.

---

## 1. Canonical Completeness Audit

### A) Kernel Presence

| Kernel Category | US GAAP Standard (Current) | Status | Master Chart Availability |
| :--- | :--- | :--- | :--- |
| **Assets** | Cash, AR | ❌ **FAIL** (Missing Fixed Assets, Prepaid, etc.) | Available (345 accounts) |
| **Liabilities** | AP | ❌ **FAIL** (Missing Taxes, Accrued, Debt) | Available |
| **Equity** | **NONE** | 🛑 **CRITICAL VIOLATION** (No RE, No Capital) | Available |
| **Revenue** | Sales Revenue | ⚠️ **PARTIAL** (No Other Income) | Available |
| **Expenses** | COGS, Utilities | ❌ **FAIL** (Missing Payroll, Taxes, Depr.) | Available |

**Findings:**
- The US GAAP templates are missing **Equity**, which makes the Accounting Equation ($Assets = Liabilities + Equity$) unsolvable.
- The IFRS template fails completely because its account codes are orphaned (no Master Account linkage).

---

## 2. "Simplified" vs "Standard" Test

The current differentiation is cosmetic and structurally unsound.

- **Standard**: 6 Accounts
- **Simplified**: 5 Accounts (Removed COGS)

**Verdict:** ❌ **UNACCEPTABLE**.
Removing COGS is a valid simplification for service businesses, but since the "Standard" parent is already missing 95% of the kernel, the "Simplified" version is a "fragment of a fragment". It is not a pruned kernel; it is non-functional.

---

## 3. GAAP vs IFRS Differentiation Audit

**Current State:**
- **US GAAP**: Uses 5-digit codes (e.g., `10069`).
- **IFRS**: Uses dot-notation codes (e.g., `1.10.10.10`).

**Findings:**
- The Master Chart (Zone A) only contains 5-digit codes.
- **Result:** The IFRS template tries to seed accounts that do not exist in the Master Chart.
- **Root Cause:** Aequitas currently lacks a "Translation Layer" or "Multi-Standard Mapping" in the Master Chart. It enforces US GAAP codes as the universal key, but the IFRS template tries to use a different key without mapping.

**Verdict:** ❌ **FAKE DIVERGENCE**. The IFRS template is broken code that produces an empty chart.

---

## 4. Model Integrity & Risk Assessment

| Risk Area | Severity | Impact |
| :--- | :--- | :--- |
| **Journaling** | 🛑 Critical | **Impossible.** Any entry involving tax, equity, or unlisted expenses cannot be posted. |
| **Fiscal Periods** | 🛑 Critical | **Impossible.** Closing entries require `Retained Earnings` and `Current Period Result` accounts, which are missing. |
| **Reporting** | 🛑 Critical | Balance Sheet will not balance. P&L will be nonsensical. |
| **DEXTER** | 🔴 High | AI will hallucinate or fail to categorize transactions due to lack of standard buckets. |
| **Onboarding** | 🟠 Medium | Users will complete onboarding but immediately hit "Setup Failed" or functional blocks. |

**Can a company safely operate?** **NO.**

---

## 5. Canonical Recommendation

| Template | Recommendation | Action |
| :--- | :--- | :--- |
| **US GAAP Standard** | **REBUILD** | Expand to full Kernel (~150 accounts) derived from Master Chart. |
| **US GAAP Simplified** | **REBUILD** | Prune the Rebuilt Standard (hide complex sub-ledgers, keep high-level buckets). |
| **IFRS Standard** | **DEPRECATE** | Disable until Master Chart supports IFRS mapping or multiple coding schemes. |

---

## 6. Proposed Canonical Fix (Design)

We must define a **Universal Kernel** that is seeded into every company.

### Rule 1: The "Must-Have" Kernel (Zone A)
Every template must include these **System Accounts** at a minimum:

1.  **Equity Core** (MANDATORY)
    - `30000` Owners Equity / Common Stock
    - `32000` Retained Earnings (System Default for Closing)
    - `39999` Current Year Earnings (System Calculated)

2.  **Cash Core**
    - `10000` Operating Cash
    - `10100` Undeposited Funds / Clearing

3.  **Revenue Core**
    - `40000` General Revenue
    - `49000` Refunds / Allowances

4.  **Expense Core** (Broad Buckets required for Simplified)
    - `60000` General Operating Expense
    - `70000` Payroll Expense
    - `80000` Tax Expense

### Rule 2: Coding Standardization
- **Adhere to 5-digit GAAP codes** for now (as per Master Chart).
- Do not use dot-notation for IFRS until the Master Chart supports `regulatory_mapping` lookups.

### Rule 3: Size Targets
- **Standard Kernel**: ~140 Accounts (Granular expense categories, specific asset types).
- **Simplified Kernel**: ~50 Accounts (Rolled up "General" buckets, but structurally complete).

### Action Plan
1.  **Update `seed_chart_templates.py`**:
    - Remove the hardcoded 6-account lists.
    - Select a robust subset of ~140 accounts from the 345 Master Accounts.
    - Ensure ALL "Must-Have" accounts are included.
2.  **Disable IFRS**:
    - Remove the IFRS option from frontend/backend until Master Chart support is fixed.
3.  **Reseed**:
    - Flush existing broken templates and re-seed with the robust definitions.
