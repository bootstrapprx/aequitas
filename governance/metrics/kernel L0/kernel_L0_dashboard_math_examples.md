# Kernel L0 Dashboard — Math Examples (Tier 1 Core Metrics)

**Version:** v1.0
**Scope:** Tier 1 only (Core Metrics)
**Inputs:** Kernel L0 account balances, period-aware
**Outputs:** Metric values (+ optional delta vs prior period)

This document contains **worked examples** and **auditable steps** for each Core Metric.

---

## 0) Conventions

### 0.1 Signs

* Assets typically have debit balances (positive in reports).
* Liabilities and income typically have credit balances.
* For dashboard math, we use **normalized “reporting polarity”**:

  * Asset balances are used as positive amounts.
  * Liability balances are used as positive obligations.
  * Revenue is positive.
  * Expenses/COGS/Refunds are treated as positive reductions (subtractions).

If your ledger stores raw debits/credits, you must map them into **reporting polarity** before applying these examples.

### 0.2 Period Awareness

Every metric is computed for:

* **Current Period** (selected fiscal period)
* optionally **Prior Period** (immediately preceding fiscal period)

Delta is:

* Delta = Current − Prior

### 0.3 Null Handling

* “N/A” means mathematically undefined (e.g., division by zero), not missing data.
* $0 is a valid computed result.

---

## 1) Total Cash

### Definition

Immediate liquidity available to the company.

### Accounts

* 10000 Operating Cash
* 10100 Undeposited Funds

### Formula (conceptual)

Total Cash = Cash + Undeposited Funds

---

### Example A (Normal)

**Current Period Balances**

* 10000 = 12,500
* 10100 = 1,200

**Calculation**

* Total Cash = 12,500 + 1,200 = **13,700**

**Audit Steps**

1. Pull balances for 10000 and 10100 for the period end
2. Sum them
3. Compare to dashboard

---

### Example B (Zero company)

* 10000 = 0
* 10100 = 0
  Total Cash = **0**

This is valid and must display as $0.

---

### Example C (Negative cash)

* 10000 = -2,000
* 10100 = 300
  Total Cash = -2,000 + 300 = **-1,700**

Negative cash is allowed (overdraft / negative bank).

---

## 2) Net Revenue

### Definition

Recognized revenue net of direct reductions.

### Accounts

* 40000 General Operating Revenue
* 49000 Refunds / Allowances

### Formula (conceptual)

Net Revenue = Revenue − Refunds

---

### Example A (Normal)

**Current Period**

* 40000 = 50,000
* 49000 = 2,500

Net Revenue = 50,000 − 2,500 = **47,500**

**Audit Steps**

1. Pull period totals for 40000 and 49000
2. Subtract refunds from revenue
3. Compare to dashboard

---

### Example B (Refund spike)

* 40000 = 10,000
* 49000 = 12,000

Net Revenue = 10,000 − 12,000 = **-2,000**

Negative net revenue is valid (more refunds than sales).

---

### Example C (No activity)

* 40000 = 0
* 49000 = 0
  Net Revenue = **0**

---

## 3) Operating Income

### Definition

Profit from core operations, excluding taxes and financing.

### Accounts

* 40000 Revenue
* 49000 Refunds
* 50000 COGS
* 60000 General Operating Expenses
* 61000 Payroll Expense
* 62000 Depreciation Expense

### Conceptual Formula

Operating Income = Net Revenue − COGS − OpEx − Payroll − Depreciation

---

### Example A (Normal)

**Current Period**

* Revenue (40000) = 100,000
* Refunds (49000) = 5,000
* COGS (50000) = 40,000
* OpEx (60000) = 20,000
* Payroll (61000) = 25,000
* Depreciation (62000) = 3,000

**Step 1: Net Revenue**

* Net Revenue = 100,000 − 5,000 = 95,000

**Step 2: Operating Income**

* Operating Income = 95,000 − 40,000 − 20,000 − 25,000 − 3,000
* Operating Income = 95,000 − 88,000 = **7,000**

**Audit Steps**

1. Compute Net Revenue (Section 2)
2. Subtract 50000, 60000, 61000, 62000 totals
3. Compare to dashboard

---

### Example B (Loss)

* Net Revenue = 30,000
* COGS = 15,000
* OpEx = 12,000
* Payroll = 10,000
* Depreciation = 1,000

Operating Income = 30,000 − 15,000 − 12,000 − 10,000 − 1,000
Operating Income = **-8,000**

---

### Example C (No depreciation recorded)

Depreciation = 0 is allowed.
Operating Income simply excludes it.

---

## 4) Net Working Capital (Kernel Approximation)

### Definition

Short-term buffer: current assets minus current liabilities (kernel-defined set).

### Current Assets (Kernel)

* 10000 Operating Cash
* 10100 Undeposited Funds
* 12000 Accounts Receivable
* 14000 Prepaid Expenses

### Current Liabilities (Kernel)

* 20000 Accounts Payable
* 21000 Accrued Liabilities
* 22000 Taxes Payable
* 23000 Deferred Revenue

### Conceptual Formula

NWC = (Cash + Undeposited + AR + Prepaids) − (AP + Accrued + Taxes + Deferred Rev)

---

### Example A (Normal)

**Current Period Balances**
Assets:

* 10000 = 20,000
* 10100 = 500
* 12000 = 12,000
* 14000 = 1,500

Liabilities:

* 20000 = 8,000
* 21000 = 2,000
* 22000 = 3,000
* 23000 = 6,000

**Step 1: Current Assets**

* 20,000 + 500 + 12,000 + 1,500 = 34,000

**Step 2: Current Liabilities**

* 8,000 + 2,000 + 3,000 + 6,000 = 19,000

**Step 3: NWC**

* 34,000 − 19,000 = **15,000**

**Audit Steps**

1. Pull balances for the 4 asset accounts and sum
2. Pull balances for the 4 liability accounts and sum
3. Subtract liabilities total from assets total

---

### Example B (Negative working capital)

Assets total = 10,000
Liabilities total = 25,000
NWC = 10,000 − 25,000 = **-15,000**

This is valid and must display as a negative value.

---

### Example C (Deferred revenue drives negative NWC)

Even if cash is strong, deferred revenue can make NWC negative. That’s valid: it reflects obligations to deliver.

---

## 5) Current Ratio (Kernel Approximation)

### Definition

Liquidity stress indicator: current assets divided by current liabilities (kernel-defined set).

### Conceptual Formula

Current Ratio = Current Assets / Current Liabilities

---

### Example A (Normal)

Current Assets = 34,000
Current Liabilities = 19,000

Current Ratio = 34,000 / 19,000 = **1.789...**
Display rule: round to a reasonable precision (e.g., 2 decimals): **1.79**

**Audit Steps**

1. Reuse totals from NWC calculation
2. Divide Assets by Liabilities
3. Compare rounded result to dashboard

---

### Example B (Division by zero → N/A)

Current Assets = 5,000
Current Liabilities = 0

Current Ratio is undefined → display **N/A** (or null that UI renders as N/A).
Never display Infinity. Never crash.

---

### Example C (Tiny liabilities)

Assets = 10,000
Liabilities = 1

Ratio = 10,000
Still valid, but watch rounding and formatting.

---

## 6) Delta Examples (Optional but Supported)

Delta is computed for each metric as:
Delta = Current Period Value − Prior Period Value

---

### Example A (Total Cash Delta)

**Prior Period**

* Total Cash = 9,000

**Current Period**

* Total Cash = 13,700

Delta = 13,700 − 9,000 = **+4,700**

---

### Example B (Current Ratio Delta with N/A)

Prior: liabilities = 0 → ratio = N/A
Current: liabilities = 19,000 → ratio = 1.79

Delta is not meaningful across N/A.
Rule: if either side is N/A, delta should be **null** (not computed).

---

## 7) Minimum Acceptance Set (Math Only)

A brand-new company with no entries must yield:

* Total Cash = 0
* Net Revenue = 0
* Operating Income = 0
* Net Working Capital = 0
* Current Ratio = N/A (because liabilities total = 0)

This is not optional.

---

## 8) Manual Audit Checklist (Per Metric)

For any period:

1. Confirm the fiscal period boundaries
2. Pull account totals (income statement accounts) or balances (balance sheet accounts) for that period
3. Normalize signs to reporting polarity
4. Apply the math from Sections 1–5
5. Compare to dashboard value
6. If mismatch: verify period mapping, sign normalization, and included accounts

---

