# Kernel L0 Dashboard — Acceptance Checklist

**Version:** v1.0
**Applies to:** Kernel Dashboard v1.0 (Tier 1 Core Metrics)
**Audience:** assistants, auditors, future maintainers
**Purpose:** Ensure math, accounting, onboarding, and wiring are correct *before* code is considered valid

---

## 0. Acceptance Philosophy

A Kernel feature is **not accepted** because:

* it renders,
* it compiles,
* or it looks correct.

It is accepted **only if financial truth is preserved under all valid states**, including zero, negative, and undefined conditions.

---

## 1. Repository & File Structure

### 1.1 Canonical Documents Present

Verify the following files exist and are committed:

* `canon/CANON_I_ACCOUNTING_TRUTH.md`
* `canon/CANON_IV_INTELLIGENCE_AND_GUIDANCE.md`
* `canon/CANON_KERNEL_L0_DASHBOARD_INTELLIGENCE.md`
* `metrics/kernel L0/kernel_L0_dashboard_intelligence.md`
* `metrics/kernel L0/kernel_L0_dashboard_math_examples.md`
* `metrics/kernel L0/kernel_L0_dashboard_test_vectors.md`
* `metrics/kernel L0/kernel_L0_dashboard_acceptance_checklist.md`

**Pass if:** all files exist and are not empty
**Fail if:** any file is missing or contradicted by code comments

---

## 2. Kernel Account Integrity

### 2.1 Kernel L0 Accounts Exist

Onboarding must guarantee the existence of **all Kernel L0 accounts**, even with zero balance.

**Pass if:**

* A brand-new company has all Kernel L0 accounts created
* No metric errors due to missing accounts

**Fail if:**

* Any metric depends on conditional account creation

---

### 2.2 No Enriched Accounts Used

**Pass if:**

* All dashboard queries reference **only** Kernel L0 accounts

**Fail if:**

* Any enriched, semantic, vendor, customer, or bank-specific account is referenced

---

## 3. Metric Correctness (Math)

### 3.1 Test Vector Compliance

Run **all test vectors** from:

```
kernel_L0_dashboard_test_vectors.md
```

**Pass if:**

* Every metric output matches expected values exactly
* Rounding rules are consistent
* N/A is returned only when mathematically undefined

**Fail if:**

* Any mismatch occurs
* Any test requires “interpretation” to justify

---

### 3.2 Zero-State Behavior

**Pass if:**
A brand-new company shows:

* Total Cash = 0
* Net Revenue = 0
* Operating Income = 0
* Net Working Capital = 0
* Current Ratio = N/A

**Fail if:**

* Any metric errors, crashes, or shows placeholders instead of values

---

### 3.3 Negative & Edge Case Handling

**Pass if:**

* Negative cash displays correctly
* Negative operating income displays correctly
* Refunds exceeding revenue produce negative net revenue
* Division by zero produces N/A, not Infinity or error

**Fail if:**

* Any clamping, hiding, or forced positivity occurs

---

## 4. Period Awareness

### 4.1 Correct Period Scoping

**Pass if:**

* Income statement accounts are aggregated by period
* Balance sheet accounts use period-end balances
* Switching periods updates all metrics consistently

**Fail if:**

* Period changes affect some metrics but not others

---

### 4.2 Delta Logic

**Pass if:**

* Delta = Current − Prior
* Delta is null when either side is N/A
* Delta never drives logic or visibility

**Fail if:**

* Delta is inferred, smoothed, or used to label behavior

---

## 5. Onboarding Integration

### 5.1 Metric Availability Post-Onboarding

**Pass if:**

* Immediately after onboarding + company activation:

  * Dashboard renders all Tier 1 metrics
  * Values are correct (even if zero)

**Fail if:**

* Dashboard requires manual refresh, re-login, or dummy data

---

### 5.2 No Silent Defaults

**Pass if:**

* Metrics show real computed values (including zero)
* No fake seed data is injected

**Fail if:**

* Placeholder values masquerade as computed results

---

## 6. Canon Compliance

### 6.1 No Decision Authority

**Pass if:**

* No recommendations
* No “should”
* No health scores
* No alerts
* No rankings

**Fail if:**

* Any UI or backend logic implies action or judgment

---

### 6.2 Tier Isolation

**Pass if:**

* Only Tier 1 metrics are computed and shown
* Tier 2 and Tier 3 logic is not partially implemented

**Fail if:**

* Any advanced or diagnostic logic leaks into v1.0

---

## 7. Auditability

### 7.1 Manual Reproducibility

**Pass if:**
An accountant can:

1. Extract the relevant account balances
2. Apply the math from `kernel_L0_dashboard_math_examples.md`
3. Arrive at the same dashboard values

**Fail if:**

* Hidden transformations or undocumented logic exist

---

### 7.2 Explainability

**Pass if:**

* Each metric can list the accounts it uses
* Each value can be explained without code inspection

**Fail if:**

* “Because the system says so” is the only explanation

---

## 8. Regression Safety

### 8.1 v1.0 Freeze Integrity

**Pass if:**

* No v1.1 features are required for correctness
* Disabling all future feature flags preserves behavior

**Fail if:**

* v1.0 behavior depends on v1.1 scaffolding

---

## 9. Final Acceptance Criteria

Kernel Dashboard v1.0 is **ACCEPTED** if and only if:

* All checklist items pass
* All test vectors pass
* No Canon is violated
* No “helpful” behavior sneaks in

If two humans disagree on what the dashboard *means*,
but agree on what it *shows* —
**the system is correct**.

---

## Acceptance Statement (to be signed mentally)

> This dashboard explains financial reality derived from Kernel L0 accounts.
> It does not decide reality, recommend actions, or replace judgment.


