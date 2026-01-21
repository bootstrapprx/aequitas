Alright. If you want “better than hybrid,” the move is **dual-track** documentation:

* **Track A — GAAP-style narrative** (semantic intent, definitions, inclusions/exclusions)
* **Track B — formal mathematical notation** (symbols, sets, functions, domain rules)

And we rewrite `metrics/kernel L0/kernel_L0_dashboard_math_examples.md` to be exactly that: **prose first, math second, then worked examples**.

Below is a complete rewrite you can paste in as the new file.

---

## `metrics/kernel L0/kernel_L0_dashboard_math_examples.md`

# Kernel L0 Dashboard — Mathematical Definitions & Worked Examples (Tier 1)

**Version:** v1.0
**Scope:** Kernel L0 Dashboard, Tier 1 Core Metrics only
**Objective:** Provide (i) GAAP-style narrative definitions and (ii) formal mathematical notation, with worked examples and auditable steps.

---

## 0. Accounting Narrative: Basis and Constraints

### 0.1 Basis of Preparation

The dashboard is prepared on an **accrual basis**. It presents computed metrics derived exclusively from Kernel L0 accounts and does not constitute financial statements.

### 0.2 Scope Limitation

The dashboard:

* uses **only Kernel L0 accounts**,
* is **read-only** (no entries are created),
* provides **no projections**, recommendations, or scoring,
* is **period-aware** as defined in Section 1.

### 0.3 Presentation Polarity

Balances and totals used in computations are in **reporting polarity**:

* Assets and expenses are treated as positive magnitudes.
* Liabilities are treated as positive magnitudes of obligations.
* Revenues are treated as positive magnitudes.
* Refunds/allowances are treated as positive magnitudes reducing revenue.

If the ledger stores debits/credits with sign conventions, those must be transformed into reporting polarity *before* applying the definitions below.

---

## 1. Mathematical Preliminaries

### 1.1 Sets of Accounts

Let the Kernel L0 account identifiers be elements of a finite set ( \mathcal{A} ).

Define the following subsets:

* Cash set
  [
  \mathcal{A}_{cash} = {10000, 10100}
  ]

* Revenue set
  [
  \mathcal{A}_{rev} = {40000}
  ]

* Refund set
  [
  \mathcal{A}_{ref} = {49000}
  ]

* Operating cost sets
  [
  \mathcal{A}*{cogs} = {50000},\quad
  \mathcal{A}*{opex} = {60000},\quad
  \mathcal{A}*{pay} = {61000},\quad
  \mathcal{A}*{dep} = {62000}
  ]

* Current assets (Kernel approximation)
  [
  \mathcal{A}_{CA} = {10000, 10100, 12000, 14000}
  ]

* Current liabilities (Kernel approximation)
  [
  \mathcal{A}_{CL} = {20000, 21000, 22000, 23000}
  ]

### 1.2 Period Model

Let ( p ) denote a fiscal period (e.g., month, quarter, year) selected by the user.

Define:

* ( p^{-} ): the immediately preceding fiscal period to ( p ) (prior period).

### 1.3 Two Measurement Functions

Because balance sheet accounts are **stock** measures and income statement accounts are **flow** measures, define two functions:

* Period-end balance function (stock):
  [
  B(a, p) \in \mathbb{R}
  ]
  meaning the period-end balance (in reporting polarity) of account ( a ) at the close of period ( p ).

* Period activity function (flow):
  [
  T(a, p) \in \mathbb{R}
  ]
  meaning the total activity (in reporting polarity) of income statement account ( a ) over period ( p ).

### 1.4 Delta Operator

For any metric ( M(p) ), define the prior-period delta:
[
\Delta M(p) = M(p) - M(p^{-})
]
If ( M(p) ) or ( M(p^{-}) ) is undefined, then ( \Delta M(p) ) is undefined.

---

## 2. Core Metric Definitions (Narrative + Formal)

### 2.1 Total Cash

#### Accounting Narrative

Total Cash represents immediate liquidity available, comprising operating cash and undeposited funds. It is a balance-sheet derived metric based on period-end balances.

#### Mathematical Definition

[
\text{TotalCash}(p) = \sum_{a \in \mathcal{A}_{cash}} B(a, p)
]

#### Domain Notes

TotalCash is defined for all ( p ). Negative values are permitted.

---

### 2.2 Net Revenue

#### Accounting Narrative

Net Revenue represents recognized revenue reduced by refunds and allowances. It is a period activity metric and uses income statement totals for the selected period.

#### Mathematical Definition

[
\text{NetRevenue}(p) = \sum_{a \in \mathcal{A}*{rev}} T(a, p) - \sum*{a \in \mathcal{A}_{ref}} T(a, p)
]
Given the sets above, this simplifies to:
[
\text{NetRevenue}(p) = T(40000, p) - T(49000, p)
]

#### Domain Notes

NetRevenue is defined for all ( p ). Negative values are permitted.

---

### 2.3 Operating Income

#### Accounting Narrative

Operating Income represents profit from core operations, computed as net revenue less cost of goods sold and operating expenses (including payroll and depreciation). It explicitly excludes taxes, interest, and financing effects.

#### Mathematical Definition

Let:
[
\text{OpCosts}(p) = \sum_{a \in \mathcal{A}*{cogs}\cup \mathcal{A}*{opex}\cup \mathcal{A}*{pay}\cup \mathcal{A}*{dep}} T(a, p)
]
Then:
[
\text{OperatingIncome}(p) = \text{NetRevenue}(p) - \text{OpCosts}(p)
]
Expanded:
[
\text{OperatingIncome}(p) = \left(T(40000,p) - T(49000,p)\right) - \left(T(50000,p)+T(60000,p)+T(61000,p)+T(62000,p)\right)
]

#### Domain Notes

OperatingIncome is defined for all ( p ). Negative values are permitted.

---

### 2.4 Net Working Capital (Kernel Approximation)

#### Accounting Narrative

Net Working Capital represents short-term financial buffer, computed as current assets less current liabilities, using the Kernel-defined approximation sets. Inventory and other non-kernel current accounts are intentionally excluded.

#### Mathematical Definition

[
\text{CurrentAssets}(p) = \sum_{a \in \mathcal{A}*{CA}} B(a,p)
]
[
\text{CurrentLiabilities}(p) = \sum*{a \in \mathcal{A}_{CL}} B(a,p)
]
[
\text{NWC}(p) = \text{CurrentAssets}(p) - \text{CurrentLiabilities}(p)
]

#### Domain Notes

NWC is defined for all ( p ). Negative values are permitted.

---

### 2.5 Current Ratio (Kernel Approximation)

#### Accounting Narrative

Current Ratio is a liquidity indicator computed as current assets divided by current liabilities, using the Kernel-defined approximation sets. If current liabilities are zero, the ratio is undefined and must be presented as N/A.

#### Mathematical Definition

[
\text{CurrentRatio}(p) =
\begin{cases}
\dfrac{\text{CurrentAssets}(p)}{\text{CurrentLiabilities}(p)}, & \text{if } \text{CurrentLiabilities}(p) \neq 0 \
\text{undefined}, & \text{if } \text{CurrentLiabilities}(p) = 0
\end{cases}
]

#### Domain Notes

* Division by zero is not permitted.
* If undefined, the dashboard must display N/A (or equivalent null rendering).

---

## 3. Worked Examples (Auditable)

> In all examples below, inputs are already in reporting polarity.

### Example 1 — Empty Company (Baseline)

**Inputs (period ( p ))**
All ( B(a,p)=0 ) and all ( T(a,p)=0 ).

**Outputs**

* ( \text{TotalCash}(p)=0 )
* ( \text{NetRevenue}(p)=0 )
* ( \text{OperatingIncome}(p)=0 )
* ( \text{NWC}(p)=0 )
* ( \text{CurrentRatio}(p)=\text{undefined} \Rightarrow \text{N/A} )

**Audit steps**

1. Verify all kernel balances and totals are zero.
2. Apply definitions in Section 2.

---

### Example 2 — Cash Only

**Inputs**

* ( B(10000,p)=10{,}000 )
* all others ( B(\cdot,p)=0 ), ( T(\cdot,p)=0 )

**Outputs**

* ( \text{TotalCash}(p)=10{,}000 )
* ( \text{NWC}(p)=10{,}000 )
* ( \text{CurrentRatio}(p)=\text{undefined} \Rightarrow \text{N/A} )
* Income metrics are 0.

---

### Example 3 — Revenue with Refunds

**Inputs**

* ( T(40000,p)=50{,}000 )
* ( T(49000,p)=8{,}000 )

**Outputs**

* ( \text{NetRevenue}(p)=50{,}000-8{,}000=42{,}000 )
* If all costs are zero, ( \text{OperatingIncome}(p)=42{,}000 )

---

### Example 4 — Full Operating Stack (Profit)

**Inputs**

* ( T(40000,p)=100{,}000 )
* ( T(49000,p)=5{,}000 )
* ( T(50000,p)=40{,}000 )
* ( T(60000,p)=20{,}000 )
* ( T(61000,p)=25{,}000 )
* ( T(62000,p)=3{,}000 )

**Outputs**

* ( \text{NetRevenue}(p)=95{,}000 )
* ( \text{OpCosts}(p)=88{,}000 )
* ( \text{OperatingIncome}(p)=7{,}000 )

---

### Example 5 — Working Capital (Positive)

**Inputs**

* ( B(10000,p)=20{,}000 )
* ( B(10100,p)=500 )
* ( B(12000,p)=12{,}000 )
* ( B(14000,p)=1{,}500 )
* ( B(20000,p)=8{,}000 )
* ( B(21000,p)=2{,}000 )
* ( B(22000,p)=3{,}000 )
* ( B(23000,p)=6{,}000 )

**Outputs**

* ( \text{CurrentAssets}(p)=34{,}000 )
* ( \text{CurrentLiabilities}(p)=19{,}000 )
* ( \text{NWC}(p)=15{,}000 )
* ( \text{CurrentRatio}(p)=34{,}000/19{,}000 \approx 1.78947 )
  Presentation: round per UI standard (e.g., 2 decimals → 1.79).

---

### Example 6 — Division by Zero (Ratio Undefined)

**Inputs**

* ( \text{CurrentAssets}(p)=5{,}000 )
* ( \text{CurrentLiabilities}(p)=0 )

**Outputs**

* ( \text{NWC}(p)=5{,}000 )
* ( \text{CurrentRatio}(p)=\text{undefined} \Rightarrow \text{N/A} )

---

## 4. Delta Examples

### Example 7 — Delta with Defined Values

If ( \text{TotalCash}(p^{-})=9{,}000 ) and ( \text{TotalCash}(p)=13{,}700 ), then:
[
\Delta \text{TotalCash}(p) = 13{,}700 - 9{,}000 = 4{,}700
]

### Example 8 — Delta with Undefined Values

If ( \text{CurrentRatio}(p^{-}) ) is undefined (liabilities = 0) and ( \text{CurrentRatio}(p) ) is defined, then:

* ( \Delta \text{CurrentRatio}(p) ) is **undefined** and must be rendered as null (no delta).

---

## 5. Auditability Statement

Each metric in Section 2 is manually reproducible by:

1. extracting ( B(a,p) ) and ( T(a,p) ) for the listed accounts,
2. applying the corresponding summation and arithmetic definitions, and
3. reconciling the result to the dashboard output.

If manual reproduction is not possible for any metric, the implementation is invalid.

---

If you want, I can also rewrite `kernel_L0_dashboard_intelligence.md` to match this **dual-track style** (Narrative + Notation), so the whole metrics folder has a single consistent language.
