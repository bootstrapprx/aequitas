

# Aequitas Accounting System

## Canonical Data Dictionary (Post-Phase 2B)

**Database Authority:** PostgreSQL
**Schema Status:** Production-ready
**Canonical Version:** 2024.1
**Source of Truth:** Database (constraints + triggers)

---

## 1. Core Accounting Philosophy (Locked)

* The database **enforces accounting truth**
* Application code **cannot bypass invariants**
* Templates define *structure*, companies define *instantiation*
* Draft ≠ Posted (semantically and technically)
* Reconciliation **never violates balance**

---

## 2. Master Reference Layer (Global, Immutable)

### 2.1 `master_accounts`

**Purpose**
Defines the canonical Chart of Accounts reference used by all templates and companies.
This table is **never company-specific**.

**Lifecycle**

* Seeded via migration
* Append-only across versions
* Historical versions preserved

**Key Characteristics**

* Hierarchical
* Versioned
* Immutable once published

**Columns**

| Column             | Type           | Nullable | Meaning                                                 |
| ------------------ | -------------- | -------- | ------------------------------------------------------- |
| `id`               | UUID           | ❌        | Primary key                                             |
| `code`             | VARCHAR        | ❌        | Canonical account code                                  |
| `description`      | VARCHAR        | ❌        | Short label                                             |
| `long_description` | TEXT           | ✅        | Detailed accounting meaning                             |
| `type`             | ENUM           | ❌        | HEADER or DETAIL                                        |
| `category`         | ENUM           | ❌        | ASSET, LIABILITY, EQUITY, REVENUE, COGS, EXPENSE, OTHER |
| `normal_balance`   | ENUM           | ❌        | DEBIT or CREDIT                                         |
| `level`            | INTEGER        | ❌        | Hierarchy depth                                         |
| `parent_id`        | UUID (FK self) | ✅        | Hierarchical parent                                     |
| `fs_mapping`       | JSONB          | ✅        | Financial statement placement                           |
| `tags`             | TEXT[]         | ✅        | Classification tags                                     |
| `default_vendors`  | TEXT[]         | ✅        | Optional defaults                                       |
| `version`          | VARCHAR(10)    | ❌        | Canonical release version                               |
| `start_date`       | DATE           | ❌        | Validity start                                          |
| `end_date`         | DATE           | ✅        | Validity end                                            |

**Invariants**

* Parent must exist
* Level must increase by 1
* Version is immutable
* Codes are unique per version

---

## 3. Template Layer (Structural Models)

### 3.1 `chart_templates`

**Purpose**
Defines reusable account structures by jurisdiction or industry.

Examples:

* US-GAAP Standard
* IFRS
* Small Business
* Non-Profit

**Columns**

| Column         | Type    | Nullable | Meaning                     |
| -------------- | ------- | -------- | --------------------------- |
| `id`           | UUID    | ❌        | Primary key                 |
| `name`         | VARCHAR | ❌        | Template name               |
| `jurisdiction` | VARCHAR | ❌        | IFRS, US-GAAP, BR-GAAP      |
| `version`      | VARCHAR | ❌        | Template version            |
| `is_active`    | BOOLEAN | ❌        | Available for new companies |
| `notes`        | TEXT    | ✅        | Description                 |

---

### 3.2 `chart_template_accounts`

**Purpose**
Defines the **account structure blueprint** for companies.

This table answers:

> “If a company uses this template, what accounts must exist?”

**Columns**

| Column                     | Type           | Nullable | Meaning                      |
| -------------------------- | -------------- | -------- | ---------------------------- |
| `id`                       | UUID           | ❌        | Primary key                  |
| `template_id`              | UUID (FK)      | ❌        | Chart template               |
| `code`                     | VARCHAR        | ❌        | Account code                 |
| `name`                     | VARCHAR        | ❌        | Account name                 |
| `account_type`             | ENUM           | ❌        | ASSET, LIABILITY, etc        |
| `normal_balance`           | ENUM           | ❌        | DEBIT / CREDIT               |
| `parent_id`                | UUID (FK self) | ✅        | Template hierarchy           |
| `mapped_master_account_id` | UUID (FK)      | ❌        | Canonical reference          |
| `is_mandatory`             | BOOLEAN        | ❌        | Cannot be deleted in company |
| `is_active`                | BOOLEAN        | ❌        | Template visibility          |

**Invariants**

* Must map to `master_accounts`
* Mandatory accounts must exist in company instantiation
* Structure defines allowed hierarchy

---

## 4. Company Layer (Operational Accounting)

### 4.1 `company_accounts`

**Purpose**
Company-specific instantiation of the chart.

This is **where accounting happens**, but structure is inherited.

**Columns**

| Column                     | Type            | Nullable | Meaning              |
| -------------------------- | --------------- | -------- | -------------------- |
| `id`                       | UUID            | ❌        | Primary key          |
| `company_id`               | UUID            | ❌        | Owning company       |
| `code`                     | VARCHAR         | ❌        | Company account code |
| `name`                     | VARCHAR         | ❌        | Display name         |
| `description`              | TEXT            | ✅        | Optional             |
| `account_type`             | ENUM            | ✅        | Derived or custom    |
| `normal_balance`           | ENUM            | ❌        | Required             |
| `parent_id`                | UUID (FK self)  | ✅        | Hierarchy            |
| `mapped_master_account_id` | UUID (FK)       | ✅        | Canonical mapping    |
| `is_active`                | BOOLEAN         | ❌        | Soft delete          |
| `is_locked`                | BOOLEAN         | ❌        | Prevents mutation    |
| `locked_by`                | UUID (FK users) | ✅        | Who locked it        |
| `currency`                 | VARCHAR         | ❌        | ISO currency         |

**Invariants**

* Locked accounts cannot be modified
* Accounts with posted entries cannot be deleted
* Mandatory template accounts cannot be removed

---

## 5. Transaction Layer (Double Entry)

### 5.1 `journal_entries`

**Purpose**
Represents an accounting event.

**Columns**

| Column        | Type      | Nullable | Meaning         |
| ------------- | --------- | -------- | --------------- |
| `id`          | UUID      | ❌        | Primary key     |
| `company_id`  | UUID      | ❌        | Owner           |
| `entry_date`  | DATE      | ❌        | Accounting date |
| `status`      | ENUM      | ❌        | DRAFT / POSTED  |
| `description` | TEXT      | ✅        | Memo            |
| `posted_at`   | TIMESTAMP | ✅        | Lock moment     |
| `created_by`  | UUID      | ❌        | Author          |

**Invariants**

* POSTED entries are immutable
* Balance enforced **only when POSTED**

---

### 5.2 `journal_entry_lines`

**Purpose**
Implements double-entry accounting.

**Columns**

| Column             | Type      | Nullable | Meaning          |
| ------------------ | --------- | -------- | ---------------- |
| `id`               | UUID      | ❌        | Primary key      |
| `journal_entry_id` | UUID (FK) | ❌        | Parent entry     |
| `account_id`       | UUID (FK) | ❌        | Affected account |
| `debit`            | NUMERIC   | ✅        | Debit amount     |
| `credit`           | NUMERIC   | ✅        | Credit amount    |

**Invariants (DB-enforced)**

* Debit XOR Credit
* Amount > 0
* SUM(debits) = SUM(credits) **when POSTED**

---

## 6. Fiscal Control Layer

### 6.1 `fiscal_periods`

**Purpose**
Defines legal accounting periods.

**Columns**

| Column       | Type | Nullable | Meaning                |
| ------------ | ---- | -------- | ---------------------- |
| `id`         | UUID | ❌        | Primary key            |
| `company_id` | UUID | ❌        | Owner                  |
| `start_date` | DATE | ❌        | Period start           |
| `end_date`   | DATE | ❌        | Period end             |
| `status`     | ENUM | ❌        | OPEN / CLOSED / LOCKED |

**Invariants**

* No overlapping periods (EXCLUDE constraint)
* LOCKED periods reject new POSTED entries

---

## 7. Reconciliation (Conceptual Boundary)

**Important Rule (Locked)**

> Reconciliation **never** allows unbalanced POSTED entries.

Reconciliation is implemented via:

* Clearing accounts
* Temporary DRAFT entries
* Semantic matching (future phase)

**Database does not permit imbalance as a state.**

---

## 8. Application Obligations (Non-Negotiable)

### Backend MUST:

* Respect immutability
* Use UUIDs, not codes
* Never bypass status transitions
* Treat DB errors as fatal

### Frontend MUST:

* Reflect locked/mandatory status
* Prevent illegal user actions
* Display hierarchy from DB, not assumptions

---

## 9. Phase Mapping

| Phase    | Responsibility               |
| -------- | ---------------------------- |
| Phase 1  | Accounting truth enforcement |
| Phase 2A | Structural normalization     |
| Phase 2B | Optimization & cleanup       |
| Phase 3A | Model alignment              |
| Phase 3B | API & services               |
| Phase 3C | UI adaptation                |

---

## Status

✅ **Schema Canonicalized**
✅ **Accounting-sound**
✅ **Template-driven**
✅ **International-ready**

---
