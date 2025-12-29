# FINANCIAL EVENT TAXONOMY

**Aequitas Canonical Specification — Zone B**

---

## 0️⃣ Purpose of the Taxonomy

The taxonomy answers **one question only**:

> *What kinds of financial reality can exist before accounting?*

Each event type represents a **real-world occurrence**, not an accounting construct.

---

## 1️⃣ Top-Level Classification

All Financial Events fall into **exactly one** of these domains:

| Domain                | Meaning                                      |
| --------------------- | -------------------------------------------- |
| Exchange Events       | Value exchanged between parties              |
| Obligation Events     | Creation of duties or claims                 |
| Transformation Events | Change in form of value                      |
| Measurement Events    | Periodic valuation of existing value         |
| Settlement Events     | Fulfillment or extinguishment of obligations |

This prevents category confusion later.

---

## 2️⃣ Canonical Event Families

### I. EXCHANGE EVENTS

> “Something was acquired or delivered.”

These are **document-backed** events (invoice, receipt, contract).

#### 1. Vendor Invoice Received

**Event Type:** `VENDOR_INVOICE`

Represents:
A third party issued a claim against the company.

Payload:

* Vendor
* Invoice document
* Amount(s)
* Currency
* Dates
* Line items (raw)

Contextual questions (mandatory):

* Is this:

  * Expense?
  * Asset acquisition?
  * Inventory acquisition?
* Payment method:

  * Cash
  * Card
  * Bank transfer
  * Loan
* If loan:

  * Which loan?
  * New or existing?

Produces (downstream):

* AP obligation
* Asset identity *or* expense
* Optional inventory units

---

#### 2. Customer Invoice Issued

**Event Type:** `CUSTOMER_INVOICE`

Represents:
The company asserts a claim against a customer.

Payload:

* Customer
* Invoice document
* Amount(s)
* Currency
* Service/product description

Contextual questions:

* Revenue recognition timing?
* Is this deferred?
* Tax applicability?

Produces:

* AR claim
* Revenue (timed)
* Tax liability (if applicable)

---

### II. OBLIGATION EVENTS

> “A duty now exists.”

These create **claims**, not movement.

#### 3. Loan Contracted

**Event Type:** `LOAN_OR_DEBT_CREATED`

Represents:
A financing agreement comes into existence.

Payload:

* Lender
* Principal
* Interest terms
* Schedule (raw)

Contextual:

* Classification (short/long term)
* Linked assets (if any)

Produces:

* Liability identity
* Future settlement expectations

---

#### 4. Payroll Obligation Incurred

**Event Type:** `PAYROLL_OBLIGATION`

Represents:
Employees earned compensation.

Payload:

* Period
* Gross amounts
* Employee list (abstracted)

Contextual:

* Tax regimes
* Benefits
* Payment timing

Produces:

* Payroll liability
* Tax obligations
* Future cash settlement

---

### III. TRANSFORMATION EVENTS

> “Value changed form.”

These do **not** introduce new value.

#### 5. Asset Capitalized

**Event Type:** `ASSET_CAPITALIZED`

Represents:
An item becomes a recognized asset.

Payload:

* Asset description
* Acquisition source (invoice, internal)
* Cost basis

Contextual:

* Depreciation method
* Useful life
* Residual value

Produces:

* Asset identity
* Depreciation schedule (dynamic)

---

#### 6. Inventory Consumed / Produced

**Event Type:** `INVENTORY_MOVEMENT`

Represents:
Stock changes form or ownership.

Payload:

* SKU / description
* Quantity
* Location (optional)

Contextual:

* Consumption vs production
* Costing method (FIFO, AVG)

Produces:

* Inventory delta
* COGS implication

---

### IV. MEASUREMENT EVENTS

> “We reassess value over time.”

These are **non-cash**, **non-exchange**.

#### 7. Depreciation Run

**Event Type:** `DEPRECIATION_MEASUREMENT`

Represents:
Periodic consumption of asset value.

Payload:

* Asset reference
* Period

Contextual:

* Method (locked from asset)
* Adjustments (rare, explicit)

Produces:

* Expense recognition
* Asset book value update

⚠️ This is the **only** recurring Financial Event allowed by the system.

---

#### 8. Tax Assessment

**Event Type:** `TAX_ASSESSMENT`

Represents:
A tax obligation is calculated.

Payload:

* Jurisdiction
* Basis (income, payroll, sales)
* Period

Contextual:

* Authority (estimate vs official)
* Payment schedule

Produces:

* Tax liability
* Optional sandbox comparison

---

### V. SETTLEMENT EVENTS

> “An obligation is fulfilled.”

#### 9. Payment Made

**Event Type:** `PAYMENT_MADE`

Represents:
Cash (or equivalent) leaves the company.

Payload:

* Amount
* Currency
* Method
* Date

Contextual:

* What is being settled?

  * Vendor invoice
  * Payroll
  * Loan
  * Tax

Produces:

* Cash reduction
* Obligation reduction

---

#### 10. Payment Received

**Event Type:** `PAYMENT_RECEIVED`

Represents:
Cash enters the company.

Payload:

* Amount
* Source
* Date

Contextual:

* Which receivable?
* Advance vs settlement?

Produces:

* Cash increase
* AR reduction *or* deferred revenue

---

## 3️⃣ Explicitly Forbidden “Events”

These will **never** exist:

❌ “Journal Entry Event”
❌ “Accounting Adjustment Event”
❌ “Correction Event”
❌ “Reclassification Event”

Corrections are **new events**, never edits.

---

## 4️⃣ Relationship to Accounting (Hard Rule)

| Event State  | Ledger Interaction |
| ------------ | ------------------ |
| DRAFT        | None               |
| CONFIRMED    | None               |
| MATERIALIZED | One-way posting    |

Ledger entries:

* Are *derived*
* Are *linked*
* Are *immutable*

---

## 5️⃣ Why This Taxonomy Scales

With this structure you can:

* Add invoicing without breaking accounting
* Add assets without hacks
* Add inventory without ERP creep
* Add payroll safely
* Integrate banks cleanly
* Simulate futures separately

All without violating:

* Canon I (Zone separation)
* Canon II (Human authority)
* Canon III (Immutable history)
* Canon IV (Advisory intelligence)

---

## 6️⃣ One-Sentence Canonical Definition

> **A Financial Event is a structured representation of a real-world financial occurrence whose accounting consequences are derived deterministically only after human intent and context are fully resolved.**

