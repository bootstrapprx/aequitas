# 📘 `CANON_KERNEL_L0_DASHBOARD_INTELLIGENCE.md`

## 1. Purpose

This document defines the **mathematical and accounting truth layer** for the Kernel L0 Dashboard.

It specifies:

* which Kernel L0 accounts participate in metrics,
* how values are mathematically derived,
* which accounting assumptions are explicitly allowed,
* and which are forbidden.

This Canon is **upstream of code** and **downstream of the Kernel**.

---

## 2. Scope Boundaries (Non-Negotiable)

The Kernel L0 Dashboard:

* uses **only Kernel L0 accounts**
* performs **read-only calculations**
* produces **no journal entries**
* contains **no projections**
* contains **no recommendations**
* contains **no enriched or semantic accounts**

If a metric cannot be computed with L0 accounts alone, it **does not exist**.

---

## 3. Accounting Basis

* Accrual accounting
* Period-aware
* No cash-flow statement reconstruction
* No inventory assumptions
* No financing or equity analytics

This dashboard answers **“what is”**, not **“what should be”**.

---

## 4. Kernel L0 Account Map (Authoritative)

### Assets

* `10000` Operating Cash
* `10100` Undeposited Funds
* `12000` Accounts Receivable
* `14000` Prepaid Expenses

### Long-Term Assets

* `15000` Fixed Assets
* `15900` Accumulated Depreciation (contra-asset)

---

### Liabilities

* `20000` Accounts Payable
* `21000` Accrued Liabilities
* `22000` Taxes Payable
* `23000` Deferred Revenue

---

### Equity (System)

* `30000` Owners Capital
* `32000` Retained Earnings
* `39999` Current Period Earnings

---

### Income & Costs

* `40000` General Operating Revenue
* `49000` Refunds / Allowances
* `50000` Cost of Goods Sold
* `60000` General Operating Expenses
* `61000` Payroll Expense
* `62000` Depreciation Expense
* `69000` Tax Expense *(not used in Tier 1)*

---

## 5. Metric Mathematics (Tier 1 Only)

### 5.1 Total Cash

**Concept**
Immediate liquidity available.

**Accounts Used**

* 10000
* 10100

**Math**

```
Total Cash = Operating Cash + Undeposited Funds
```

**Accounting Notes**

* Zero balance is valid
* Never inferred from transactions
* Always absolute

---

### 5.2 Net Revenue

**Concept**
Recognized revenue after direct reductions.

**Accounts Used**

* 40000
* 49000

**Math**

```
Net Revenue = Revenue − Refunds
```

**Accounting Notes**

* Period-based
* Refunds are treated as reductions, not expenses
* No accrual interpretation

---

### 5.3 Operating Income

**Concept**
Profit from core operations.

**Accounts Used**

* 40000
* 49000
* 50000
* 60000
* 61000
* 62000

**Math**

```
Operating Income =
Net Revenue
− COGS
− General Operating Expenses
− Payroll Expense
− Depreciation Expense
```

**Explicit Exclusions**

* Taxes
* Interest
* Financing effects

---

### 5.4 Net Working Capital (Kernel Approximation)

**Concept**
Short-term financial buffer.

**Current Assets**

* 10000
* 10100
* 12000
* 14000

**Current Liabilities**

* 20000
* 21000
* 22000
* 23000

**Math**

```
Net Working Capital =
(Current Assets) − (Current Liabilities)
```

**Accounting Notes**

* This is a **kernel approximation**
* Inventory is intentionally excluded
* Deferred revenue is treated as a liability

---

### 5.5 Current Ratio (Kernel Approximation)

**Concept**
Liquidity stress indicator.

**Math**

```
Current Ratio =
Current Assets / Current Liabilities
```

**Edge Cases**

* If Current Liabilities = 0 → result is `N/A`
* Never divide by zero
* Never label as “good” or “bad”

---

## 6. Delta Computation (All Tier 1 Metrics)

**Concept**
Each metric may optionally expose a delta vs prior period.

**Math**

```
Delta = Current Period Value − Prior Period Value
```

**Rules**

* No percentage deltas required
* No trend inference
* No alerts based on delta

---

## 7. Forbidden Accounting Behaviors

The Kernel L0 Dashboard must never:

* infer cash flow from income
* smooth values
* normalize by industry
* annualize partial periods
* project forward
* attribute causality

---

## 8. Auditability Rule

Every metric must be manually reproducible by:

1. Extracting balances of listed accounts
2. Applying the math exactly as written
3. Reconciling to the dashboard value

If this fails, the implementation is invalid.

---

## 9. Relationship to Other Documents

This Canon:

* implements **CANON I (Accounting Truth)**
* respects **CANON IV (Intelligence & Guidance)**
* is constrained by **Kernel 2025.x**

It must never conflict with them.

---

## 10. Freeze Statement

This document is **frozen for Kernel Dashboard v1.0**.

Any change requires:

* a Delta Document
* explicit scope justification
* version bump

