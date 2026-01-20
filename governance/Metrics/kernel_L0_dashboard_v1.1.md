# KERNEL DASHBOARD v1.0 → v1.1

## DELTA DOCUMENT (Controlled Evolution)

**Status:** Proposed, not active
**Baseline:** Kernel Dashboard v1.0 (frozen)
**Purpose:** Extend clarity without violating the Kernel
**Core Rule:** v1.1 may add *context*, never *authority*

---

## 1. What a Delta Is (and Is Not)

A **delta** is:

* additive,
* optional,
* non-breaking,
* explicitly scoped.

A delta is **not**:

* a redesign,
* a reinterpretation,
* a behavior change,
* a silent upgrade.

Kernel Dashboard v1.0 remains valid, complete, and sufficient after v1.1.

---

## 2. Guiding Constraint for v1.1

> v1.1 may help the user *understand faster*,
> but must not help the user *decide faster*.

If a feature reduces thinking time at the cost of judgment, it is forbidden.

---

## 3. Additions Allowed in v1.1

### 3.1 Narrative Context Layer (NEW)

**What is added**
A lightweight, optional **narrative explanation layer** attached to metrics.

**What it does**

* Explains *patterns*, not actions
* Uses neutral language
* Focuses on cause-and-effect

**Example (allowed)**

> “Operating income increased primarily due to higher gross margin, while payroll remained stable.”

**Example (forbidden)**

> “You should reduce payroll to improve margins.”

**Rules**

* Off by default
* User-invoked
* One paragraph maximum per metric
* No verbs implying action

---

### 3.2 Time Compression Views (NEW)

**What is added**
Predefined time comparisons:

* Current vs prior period
* Rolling averages
* Simple trend indicators

**Why**
Reduce cognitive friction without adding inference.

**Rules**

* No forecasting
* No smoothing that hides volatility
* Raw values always accessible

---

### 3.3 Metric Relationship Highlights (NEW)

**What is added**
Explicit links between related metrics.

**Example**

* DSO highlighted when cash declines
* Payroll ratio highlighted when operating margin shifts

**Rules**

* Highlight ≠ alert
* No color escalation
* No prioritization language

Purpose:

> “These moved together,” not “This caused that.”

---

### 3.4 Diagnostic Entry Shortcuts (NEW)

**What is added**
Contextual paths into Tier 3 diagnostics.

**Example**

* From declining cash → “View profit vs cash diagnostics”

**Rules**

* User must click
* Diagnostics still open in Tier 3 mode
* No auto-expansion

---

## 4. What Is Explicitly NOT Added in v1.1

The following remain forbidden:

* Recommendations
* Scores
* Health labels
* Industry benchmarks
* Peer comparisons
* AI opinions
* Risk ratings
* Automation triggers

These require a **separate Canon**, not a delta.

---

## 5. Metric System Changes

### Metrics Added

❌ None

### Metrics Modified

❌ None

### Metrics Reclassified

❌ None

This is intentional.

v1.1 changes **how metrics are read**, not **what metrics exist**.

---

## 6. Layout Changes (Minor, Non-Disruptive)

### Allowed

* Collapsible explanations
* Inline “why this changed” text
* Slight spacing adjustments for readability

### Forbidden

* New panels on landing screen
* New default sections
* Cross-tier blending

Tier order remains sacred.

---

## 7. Role-Based Behavior Changes

### Founder

* Narrative layer available but hidden
* Diagnostics still hidden by default

### Accountant / CFO

* Narrative layer visible by default
* Diagnostic shortcuts enabled

### Auditor

* Narrative layer optional
* Diagnostics unchanged
* Simulations still disabled

Roles still change **visibility only**, never logic.

---

## 8. Onboarding Delta

v1.1 onboarding adds **one additional acknowledgment**:

> “Explanations are interpretations, not instructions.”

No other onboarding changes allowed.

---

## 9. Backward Compatibility Guarantee

A system running v1.1 must be able to:

* disable all v1.1 features,
* revert to pure v1.0 behavior,
* without data loss or semantic change.

If this is not possible, the feature is invalid.

---

## 10. Definition of Done for v1.1

v1.1 is complete when:

* All v1.1 features can be toggled off
* No metric produces different values than v1.0
* No new decision pressure is introduced
* An auditor agrees that v1.1 adds clarity but no bias

---

## 11. Forward Boundary After v1.1

Any of the following **require v2.0**, not v1.2:

* Benchmarks
* Scoring
* Alerts
* AI-generated insights
* Optimization suggestions
* Prescriptive analytics

v1.x is an **interpretation refinement line only**.

---

## Closing Statement

v1.0 told the truth.
v1.1 helps the truth be understood.

Nothing more.

If understanding turns into instruction,
the line has been crossed.

---


