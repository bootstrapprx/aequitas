# Kernel L0 Dashboard — Test Vectors

**Version:** v1.0
**Scope:** Tier 1 (Core Metrics only)
**Purpose:** Deterministic validation of math & accounting logic
**Audience:** Codex, reviewers, auditors, future-you

This document defines **explicit input states** (account balances by period) and the **only valid outputs** for Kernel L0 Dashboard Core Metrics.

If implementation output differs, the implementation is wrong.

---

## 0. Conventions (Binding)

* All balances below are **already normalized to reporting polarity**
* Balance Sheet accounts = ending balances for the period
* Income Statement accounts = period totals
* Currency units are irrelevant (assume USD)

Metrics validated:

* Total Cash
* Net Revenue
* Operating Income
* Net Working Capital
* Current Ratio

---

## TEST VECTOR 01 — Empty Company (Baseline)

### Input (Current Period)

All Kernel L0 accounts = 0

### Expected Output

* Total Cash = 0
* Net Revenue = 0
* Operating Income = 0
* Net Working Capital = 0
* Current Ratio = N/A

### Notes

* This must work immediately after onboarding
* Zero is a valid value, not missing data

---

## TEST VECTOR 02 — Cash Only

### Input

* 10000 Operating Cash = 10,000
* All other accounts = 0

### Expected Output

* Total Cash = 10,000
* Net Revenue = 0
* Operating Income = 0
* Net Working Capital = 10,000
* Current Ratio = N/A (no liabilities)

---

## TEST VECTOR 03 — Simple Revenue, No Costs

### Input

* 40000 Revenue = 25,000
* All others = 0

### Expected Output

* Total Cash = 0
* Net Revenue = 25,000
* Operating Income = 25,000
* Net Working Capital = 0
* Current Ratio = N/A

### Notes

* Accrual reality: profit exists even without cash

---

## TEST VECTOR 04 — Revenue With Refunds

### Input

* 40000 Revenue = 50,000
* 49000 Refunds = 8,000

### Expected Output

* Net Revenue = 42,000
* Operating Income = 42,000

All other metrics unchanged (0 / N/A).

---

## TEST VECTOR 05 — Full Operating Stack (Profit)

### Input

* 40000 Revenue = 100,000
* 49000 Refunds = 5,000
* 50000 COGS = 40,000
* 60000 OpEx = 20,000
* 61000 Payroll = 25,000
* 62000 Depreciation = 3,000

### Expected Output

* Net Revenue = 95,000
* Operating Income = 7,000

---

## TEST VECTOR 06 — Full Operating Stack (Loss)

### Input

* 40000 Revenue = 30,000
* 49000 Refunds = 0
* 50000 COGS = 15,000
* 60000 OpEx = 12,000
* 61000 Payroll = 10,000
* 62000 Depreciation = 1,000

### Expected Output

* Net Revenue = 30,000
* Operating Income = -8,000

---

## TEST VECTOR 07 — Working Capital (Positive)

### Input — Assets

* 10000 Cash = 20,000
* 10100 Undeposited = 500
* 12000 AR = 12,000
* 14000 Prepaids = 1,500

### Input — Liabilities

* 20000 AP = 8,000
* 21000 Accrued = 2,000
* 22000 Taxes = 3,000
* 23000 Deferred Revenue = 6,000

### Expected Output

* Net Working Capital = 15,000
* Current Ratio = 1.79 (rounded to 2 decimals)

---

## TEST VECTOR 08 — Working Capital (Negative)

### Input

Assets total = 10,000
Liabilities total = 25,000

### Expected Output

* Net Working Capital = -15,000
* Current Ratio = 0.40

---

## TEST VECTOR 09 — Deferred Revenue Dominance

### Input

* 10000 Cash = 50,000
* 23000 Deferred Revenue = 70,000

### Expected Output

* Net Working Capital = -20,000
* Current Ratio = 0.71

### Notes

* High cash does NOT imply positive working capital
* This is an intentional truth-revealing case

---

## TEST VECTOR 10 — Division by Zero (Ratio)

### Input

* Assets total = 5,000
* Liabilities total = 0

### Expected Output

* Current Ratio = N/A
* Net Working Capital = 5,000

---

## TEST VECTOR 11 — Negative Cash

### Input

* 10000 Cash = -2,000
* 10100 Undeposited = 300

### Expected Output

* Total Cash = -1,700

Other metrics unchanged.

---

## TEST VECTOR 12 — Period Delta (Cash Increase)

### Prior Period

* Total Cash = 9,000

### Current Period

* Total Cash = 13,700

### Expected Delta

* Delta = +4,700

### Rule

If either side is N/A, delta must be null.

---

## 11. Global Assertions (Must Hold)

Across **all** test vectors:

* No metric contradicts another
* No metric infers intent or health
* Zero is treated as valid data
* N/A is used only for undefined math
* No enriched accounts are referenced
* Results are reproducible manually

---

## 12. Definition of Pass / Fail

**PASS**
All outputs match exactly (within rounding rules).

**FAIL**
Any deviation indicates:

* wrong account inclusion,
* wrong sign handling,
* wrong period logic,
* or Canon violation.

---

### Status

This document is **authoritative for Kernel Dashboard v1.0**.

Any future change requires:

* a delta document,
* updated test vectors,
* and version bump.

---
