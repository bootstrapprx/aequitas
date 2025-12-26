# Kernel 2025.2 — Frozen Canonical Chart of Accounts

**Status:** FROZEN
**Effective From:** 2025-12-24
**GAAP Basis:** US GAAP
**Version:** 2025.2

---

## Purpose

This document defines **Kernel 2025.2**, the first canon-complete accounting kernel used in Aequitas onboarding.

A kernel is an immutable, versioned set of accounts that guarantees:

1. **Completeness** — The accounting equation can be satisfied
2. **Functionality** — Double-entry journaling is supported
3. **Closability** — Fiscal periods can be closed
4. **Universality** — No company-specific or factual accounts

Kernel 2025.2 replaces the broken onboarding templates identified in the December 2024 audit, which seeded only 5-6 accounts and violated canon integrity.

---

## Problem Solved

**Before Kernel 2025.2:**
- Onboarding templates contained only 5-6 accounts
- Missing critical accounts: Equity, Retained Earnings, Taxes Payable
- Companies could not perform fiscal period closing
- Balance sheets could not balance
- IFRS templates referenced non-existent account codes

**After Kernel 2025.2:**
- All companies receive a structurally complete chart
- L0 kernel ensures universal accounting operations
- L1 provides full GAAP granularity
- L2 provides simplified UX without sacrificing integrity

---

## Kernel Layers

Aequitas defines three kernel layers:

### L0 — Universal Kernel (Non-Negotiable)

**Count:** 20 accounts
**Required:** Yes

L0 is the minimal set of accounts that MUST be present in every company, regardless of jurisdiction or complexity.

#### System Accounts (Equity Core)
- `30000` — Owners Equity / Capital
- `32000` — Retained Earnings *(system default for closing)*
- `39999` — Current Period Earnings *(system calculated)*

#### Cash Core
- `10000` — Operating Cash
- `10100` — Undeposited Funds

#### Receivables & Payables
- `12000` — Accounts Receivable
- `20000` — Accounts Payable

#### Revenue Core
- `40000` — General Operating Revenue
- `49000` — Refunds / Allowances

#### Expense Core
- `60000` — General Operating Expenses
- `61000` — Payroll Expense
- `62000` — Depreciation Expense
- `69000` — Tax Expense

#### Other Core Accounts
- `14000` — Prepaid Expenses
- `15000` — Fixed Assets
- `15900` — Accumulated Depreciation
- `21000` — Accrued Liabilities
- `22000` — Taxes Payable
- `23000` — Deferred Revenue
- `50000` — Cost of Goods Sold

**Guarantee:** Any company with L0 can:
- Record cash transactions
- Track receivables and payables
- Close fiscal periods
- Generate a valid Balance Sheet and Income Statement

---

### L1 — US GAAP Standard Kernel

**Count:** 35 accounts
**Required:** No
**Derived From:** Master Chart (345 accounts)

L1 is the **standard GAAP kernel** for companies requiring granular expense tracking, multiple revenue streams, and detailed asset/liability classification.

**Important:** Templates may extend beyond L1 by including additional Master Chart accounts. Such extensions are template-level expansions and are not part of the kernel. They are not governed by kernel guarantees or frozen in this specification.

#### What L1 Adds to L0:
- **Savings & Investment Accounts** (11000+)
- **Inventory Tracking** (13000)
- **Intangible Assets** (16000)
- **Debt Accounts** (Short-term: 24000, Long-term: 25000)
- **Partner/Shareholder Accounts** (31000)
- **Detailed Revenue Streams** (Service: 41000, Product: 42000)
- **COGS Breakdowns** (Materials: 51000, Labor: 52000)
- **Granular Expense Categories**
  - Rent (63000)
  - Utilities (64000)
  - Insurance (65000)
  - Marketing (66000)
  - Professional Fees (67000)

**Use Case:** Companies with:
- Complex expense structures
- Multiple revenue streams
- Inventory or manufacturing
- Professional accountants or bookkeepers

---

### L2 — US GAAP Simplified Kernel

**Count:** 20 accounts
**Required:** No
**Derived From:** L1 (collapsed)

L2 is a **simplified, UX-optimized kernel** for small businesses or startups that want cleaner account lists without sacrificing structural integrity.

#### How L2 Differs from L1:
- **Preserved:** All L0 accounts (equity, system accounts, core structure)
- **Collapsed:** Detailed expense accounts roll up into L0 buckets
  - `63000`, `64000`, `65000`, `66000`, `67000` → `60000` (General Operating Expenses)
- **Removed:** Granular COGS and revenue subcategories

**Use Case:** Companies with:
- Simple business models (consulting, SaaS, services)
- Non-accounting users
- Preference for fewer, broader categories

**Collapse Rule:** `ROLLUP`
When a transaction is posted to a child account in L1 (e.g., `63000 Rent`), it rolls up to the parent L2 account (`60000 General Operating Expenses`) for simplified reporting.

---

## Guarantees

Kernel 2025.2 provides the following immutable guarantees:

1. **Accounting Equation Satisfiable**
   Assets = Liabilities + Equity is always solvable.

2. **Double-Entry Journaling Supported**
   All accounts have defined normal balances (Debit/Credit).

3. **Fiscal Period Closing Supported**
   Retained Earnings (`32000`) and Current Period Earnings (`39999`) enable period-end closing.

4. **No Factual or Entity-Specific Accounts**
   The kernel is universal. Company-specific accounts (e.g., "Amazon AWS Expense") are added by the company, not the kernel.

5. **Kernel is Canon-Complete**
   All accounts required for US GAAP compliance are present or derivable.

---

## Immutability Rule

**Kernel 2025.2 is frozen.**

- It may be **referenced** (e.g., "Onboard using Kernel 2025.2")
- It may be **instantiated** (e.g., seed a company with this kernel)
- It may be **audited** (e.g., verify a company has the L0 kernel)

**It may NOT be modified.**

Any change to the kernel structure, account codes, or guarantees requires a new kernel version (e.g., Kernel 2025.3, Kernel 2026.1).

---

## Authority Declaration

**The kernel is authoritative.**

The Master Chart, chart templates, and database state MUST conform to the kernel. The kernel is never altered to match an existing database state.

When discrepancies exist between the kernel specification and the database:
- The kernel definition is canonical
- The database must be corrected to match the kernel
- The kernel specification remains unchanged

This ensures that frozen kernels remain stable, auditable, and reproducible across all environments.

---

## How Future Kernels Are Introduced

When a kernel change is needed:

1. **Propose** — Document the change (e.g., "Add IFRS support" or "Modify L1 structure")
2. **Increment Version** — Create `kernel_2025.3.json` (or next semantic version)
3. **Freeze** — Generate new freeze artifacts (JSON, MD, checksum)
4. **Migrate** — Update onboarding logic to reference the new kernel
5. **Preserve** — Old kernels remain frozen and auditable

**Never delete or modify a frozen kernel.**

---

## Versioning Scheme

- **Year.Iteration** (e.g., 2025.2)
- **Year** = Calendar year of freeze
- **Iteration** = Incremental number within that year

Examples:
- `2025.1` — Initial kernel (unreleased)
- `2025.2` — Current frozen kernel (this document)
- `2025.3` — Next iteration (if needed before 2026)
- `2026.1` — First kernel of 2026

---

## Checksum

**SHA-256:** `6a84b95b61d45d37...` (see `kernel_2025.2.checksum`)

The checksum is generated by:
1. Sorting all `master_account_id` values per layer (L0, L1, L2)
2. Concatenating them deterministically
3. Hashing with SHA-256

This allows mechanical drift detection. If the kernel structure changes, the checksum will change.

---

## Audit Usage

Auditors can use this freeze to verify:

1. **Onboarding Integrity**
   Did a company receive the full L0 kernel during onboarding?

2. **Kernel Completeness**
   Does the company's chart contain all 20 L0 accounts?

3. **Drift Detection**
   Has the kernel definition been altered since the freeze?

**Audit Command:**
```bash
# Extract company's L0 accounts
SELECT code, description FROM company_accounts WHERE code IN (
  '10000', '10100', '12000', '14000', '15000', '15900',
  '20000', '21000', '22000', '23000',
  '30000', '32000', '39999',
  '40000', '49000', '50000',
  '60000', '61000', '62000', '69000'
);

# Verify count = 20
```

---

## Related Documents

- [Canon I: Accounting Truth](../CANON_I_ACCOUNTING_TRUTH.md) — Defines Zone A (truth) vs Zone C (intelligence)
- [Canon II: Authority and Power](../CANON_II_AUTHORITY_AND_POWER.md) — Defines ownership and mutation rights
- [Canon III: Evolution and State](../CANON_III_EVOLUTION_AND_STATE.md) — Defines versioning and state transitions
- [Template Audit Report](../../TEMPLATE_AUDIT_REPORT.md) — Documents the problem Kernel 2025.2 solves
- [Master Chart Data Dictionary](../DATA_DICTIONARY.md) — Full 345-account reference

---

## Questions & Answers

**Q: Can I add custom accounts to a company's chart after onboarding?**
A: Yes. The kernel defines the *minimum* structure. Companies can extend their chart with custom accounts.

**Q: Can I remove an L0 account from a company?**
A: No. L0 accounts are required for system operations (fiscal closing, reporting). Removing them breaks canon.

**Q: What if my business doesn't use COGS?**
A: Use the L2 (Simplified) kernel. COGS accounts will be present but unused.

**Q: Can I use IFRS with Kernel 2025.2?**
A: No. Kernel 2025.2 is US GAAP only. IFRS support requires a future kernel version with proper regulatory mapping.

**Q: How do I know which kernel a company is using?**
A: Check the `ChartTemplate.version` field in the database. It will reference `2025.2-kernel`.

---

**Kernel 2025.2 is now frozen and auditable.**

Generated: 2025-12-24
Frozen By: Aequitas Canon Authority
Next Review: Q1 2026 (or as needed)
