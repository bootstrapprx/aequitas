# Phase 3C-1: Canonical DTO & Schema Definition
## API Data Transfer Object Specifications

**Document Version:** 1.0
**Date:** 2025-12-16
**Status:** CANONICAL - Phase 3C-1
**Authority:** api-guardian + contract-architect

---

## Document Purpose

This document defines the **canonical API DTOs** for Aequitas accounting system. Every field is explicitly classified as REQUIRED, OPTIONAL, READ_ONLY, SERVER_CONTROLLED, or CLIENT_CONTROLLED.

**Hard Rules:**
- UUID-based relationships only
- No deprecated fields
- No string-based hierarchy or mapping references
- Enums match backend exactly (case-sensitive)
- Locked fields are READ_ONLY in schemas

---

## DTO Inventory

### Core DTOs (8 Total)

1. **CompanyAccountDTO** - Company-specific chart of accounts
2. **ChartTemplateDTO** - Template definitions (jurisdiction-specific)
3. **ChartTemplateAccountDTO** - Accounts within templates
4. **MasterAccountDTO** - US-GAAP master chart (read-only)
5. **JournalEntryDTO** - Journal entry headers
6. **JournalEntryLineDTO** - Journal entry debit/credit lines
7. **FiscalPeriodDTO** - Accounting periods
8. **AccountLockStatusDTO** - Account lock metadata (nested/embedded)

---

## Field Classification Legend

| Classification | Meaning | Who Controls | Mutability |
|---|---|---|---|
| **REQUIRED** | Must be provided by client on create | Client | Varies |
| **OPTIONAL** | May be provided by client on create | Client | Varies |
| **READ_ONLY** | Never writable via API | Server | Immutable via API |
| **SERVER_CONTROLLED** | Server generates/manages | Server | Server only |
| **CLIENT_CONTROLLED** | Client provides, server stores | Client | Client can update |

**Additional Tags:**
- **IMMUTABLE_WHEN_LOCKED** - Cannot change when `is_locked = true`
- **IMMUTABLE_WHEN_POSTED** - Cannot change when `status = POSTED`
- **IMMUTABLE_WHEN_CLOSED** - Cannot change when fiscal period ≠ OPEN

---

## 1. CompanyAccountDTO

**Purpose:** Represents a single account in a company's chart of accounts.

**Database Model:** `CompanyAccount` ([company_account.py:29-260](backend/app/db/models/company_account.py#L29-L260))

### Field Classification Table

| Field Name | Type | Classification | Tags | Rationale |
|---|---|---|---|---|
| `id` | UUID | READ_ONLY, SERVER_CONTROLLED | - | Primary key, server-generated |
| `company_id` | UUID | REQUIRED | IMMUTABLE_ALWAYS | Account ownership, cannot transfer |
| `parent_id` | UUID \| null | OPTIONAL | IMMUTABLE_WHEN_LOCKED | Hierarchy structure, locked after first transaction |
| `mapped_master_account_id` | UUID \| null | OPTIONAL | IMMUTABLE_WHEN_LOCKED | Master chart mapping, locked after first transaction |
| `template_account_id` | UUID \| null | READ_ONLY | - | Source template reference, historical tracking |
| `locked_by` | UUID \| null | READ_ONLY, SERVER_CONTROLLED | - | Audit trail for manual locks |
| `code` | string | REQUIRED | IMMUTABLE_WHEN_LOCKED | Account identifier within company, locked after first transaction |
| `name` | string \| null | REQUIRED | CLIENT_CONTROLLED | Display name, always editable |
| `description` | string | REQUIRED | CLIENT_CONTROLLED | Account description, always editable |
| `type` | string(1) | EXCLUDED | **DEPRECATED** | **DO NOT EXPOSE** - Use `account_type` instead |
| `account_type` | AccountType enum | REQUIRED | IMMUTABLE_WHEN_LOCKED | Asset/Liability/Equity/Revenue/Expense, locked after first transaction |
| `normal_balance` | NormalBalance enum | REQUIRED | IMMUTABLE_WHEN_LOCKED | Debit/Credit, locked after first transaction |
| `is_active` | boolean | READ_ONLY, SERVER_CONTROLLED | - | Soft delete flag, managed by delete endpoint |
| `is_locked` | boolean | READ_ONLY, SERVER_CONTROLLED | - | Lock status, managed by lock/unlock endpoints |
| `locked_at` | timestamp \| null | READ_ONLY | - | Lock timestamp, audit trail |
| `locked_reason` | LockedReason enum \| null | READ_ONLY | - | FirstTransaction/PeriodClose/Manual |
| `currency` | string(3) | OPTIONAL, CLIENT_CONTROLLED | - | ISO currency code, defaults to USD, always editable |
| `json_data` | JSONB \| null | OPTIONAL, CLIENT_CONTROLLED | - | Custom metadata, always editable |
| `embedding` | EXCLUDED | - | **INTERNAL ONLY** | **DO NOT EXPOSE** - pgvector semantic search, not client-facing |
| `created_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |
| `updated_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |

### Create Request DTO: `CompanyAccountCreate`

```typescript
{
  company_id: UUID              // REQUIRED
  code: string                  // REQUIRED - unique within company
  name: string                  // REQUIRED
  description: string           // REQUIRED
  account_type: AccountType     // REQUIRED - Asset|Liability|Equity|Revenue|Expense
  normal_balance: NormalBalance // REQUIRED - Debit|Credit
  parent_id?: UUID | null       // OPTIONAL - hierarchy parent
  mapped_master_account_id?: UUID | null  // OPTIONAL - master chart mapping
  currency?: string             // OPTIONAL - defaults to "USD"
  json_data?: object | null     // OPTIONAL - custom metadata
}
```

### Update Request DTO: `CompanyAccountUpdate`

```typescript
{
  // ALWAYS ALLOWED (not locked)
  name?: string
  description?: string
  currency?: string
  json_data?: object | null

  // ONLY ALLOWED when is_locked = false
  code?: string
  account_type?: AccountType
  normal_balance?: NormalBalance
  parent_id?: UUID | null
  mapped_master_account_id?: UUID | null
}
```

**Validation Rules:**
- If `is_locked = true`, changes to `code`, `account_type`, `normal_balance`, `parent_id`, `mapped_master_account_id` MUST be rejected with error code `LOCKED_ACCOUNT`
- Service layer enforces these rules, API MUST NOT bypass

### Response DTO: `CompanyAccountResponse`

```typescript
{
  id: UUID
  company_id: UUID
  code: string
  name: string | null
  description: string
  account_type: AccountType
  normal_balance: NormalBalance
  parent_id: UUID | null
  mapped_master_account_id: UUID | null
  template_account_id: UUID | null
  is_active: boolean
  is_locked: boolean
  locked_at: timestamp | null
  locked_reason: "FirstTransaction" | "PeriodClose" | "Manual" | null
  locked_by: UUID | null
  currency: string
  json_data: object | null
  created_at: timestamp
  updated_at: timestamp
}
```

**Excluded Fields:**
- `type` - **DEPRECATED**, clients must use `account_type`
- `embedding` - Internal pgvector data, not exposed to clients

---

## 2. ChartTemplateDTO

**Purpose:** Represents a chart of accounts template (jurisdiction-specific).

**Database Model:** `ChartTemplate` ([chart_template.py:17-56](backend/app/db/models/chart_template.py#L17-L56))

### Field Classification Table

| Field Name | Type | Classification | Tags | Rationale |
|---|---|---|---|---|
| `id` | UUID | READ_ONLY, SERVER_CONTROLLED | - | Primary key, server-generated |
| `name` | string | REQUIRED | CLIENT_CONTROLLED | Template name (e.g., "US GAAP Standard") |
| `jurisdiction` | string | REQUIRED | IMMUTABLE_ALWAYS | Jurisdiction code (e.g., "US", "CA"), cannot change after creation |
| `version` | string | REQUIRED | IMMUTABLE_ALWAYS | Template version (e.g., "1.0"), immutable |
| `description` | string \| null | OPTIONAL | CLIENT_CONTROLLED | Detailed description |
| `is_active` | boolean | READ_ONLY, SERVER_CONTROLLED | - | Active flag, managed by activation endpoints |
| `created_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |
| `updated_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |

### Create Request DTO: `ChartTemplateCreate`

```typescript
{
  name: string                  // REQUIRED - template name
  jurisdiction: string          // REQUIRED - "US", "CA", "UK", etc.
  version: string               // REQUIRED - "1.0", "2023-Q4", etc.
  description?: string | null   // OPTIONAL - detailed description
}
```

### Response DTO: `ChartTemplateResponse`

```typescript
{
  id: UUID
  name: string
  jurisdiction: string
  version: string
  description: string | null
  is_active: boolean
  created_at: timestamp
  updated_at: timestamp
}
```

**Note:** Templates are effectively immutable after creation. `jurisdiction` and `version` cannot be changed. To modify a template, create a new version.

---

## 3. ChartTemplateAccountDTO

**Purpose:** Represents an account within a chart template.

**Database Model:** `ChartTemplateAccount` ([chart_template.py:59-118](backend/app/db/models/chart_template.py#L59-L118))

### Field Classification Table

| Field Name | Type | Classification | Tags | Rationale |
|---|---|---|---|---|
| `id` | UUID | READ_ONLY, SERVER_CONTROLLED | - | Primary key, server-generated |
| `template_id` | UUID | REQUIRED | IMMUTABLE_ALWAYS | Template ownership, cannot change |
| `master_account_id` | UUID | REQUIRED | IMMUTABLE_ALWAYS | Master account reference, immutable |
| `parent_id` | UUID \| null | OPTIONAL | IMMUTABLE_ALWAYS | Template hierarchy, immutable |
| `code` | string | REQUIRED | IMMUTABLE_ALWAYS | Template account code, immutable |
| `name` | string | REQUIRED | CLIENT_CONTROLLED | Account name, editable |
| `is_mandatory` | boolean | REQUIRED | CLIENT_CONTROLLED | If true, must exist in company charts using this template |
| `allow_custom_children` | boolean | OPTIONAL | CLIENT_CONTROLLED | If true, companies can add children under this account |
| `sort_order` | integer | REQUIRED | CLIENT_CONTROLLED | Display order within parent |
| `created_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |

### Create Request DTO: `ChartTemplateAccountCreate`

```typescript
{
  template_id: UUID             // REQUIRED - owning template
  master_account_id: UUID       // REQUIRED - master chart reference
  parent_id?: UUID | null       // OPTIONAL - template hierarchy
  code: string                  // REQUIRED - account code
  name: string                  // REQUIRED - account name
  is_mandatory: boolean         // REQUIRED - enforcement flag
  allow_custom_children?: boolean  // OPTIONAL - defaults to false
  sort_order: integer           // REQUIRED - display order
}
```

### Update Request DTO: `ChartTemplateAccountUpdate`

```typescript
{
  // ONLY these fields can be updated
  name?: string
  is_mandatory?: boolean
  allow_custom_children?: boolean
  sort_order?: integer
}
```

**Immutable Fields:**
- `template_id`, `master_account_id`, `parent_id`, `code` - Cannot change after creation
- To change these, delete and recreate the template account

### Response DTO: `ChartTemplateAccountResponse`

```typescript
{
  id: UUID
  template_id: UUID
  master_account_id: UUID
  parent_id: UUID | null
  code: string
  name: string
  is_mandatory: boolean
  allow_custom_children: boolean
  sort_order: integer
  created_at: timestamp
}
```

---

## 4. MasterAccountDTO

**Purpose:** Represents a master chart account (US-GAAP reference). **READ-ONLY API.**

**Database Model:** `MasterAccount` ([master_account.py:26-279](backend/app/db/models/master_account.py#L26-L279))

### Field Classification Table

| Field Name | Type | Classification | Tags | Rationale |
|---|---|---|---|---|
| `id` | UUID | READ_ONLY | - | Primary key |
| `code` | string | READ_ONLY | - | Canonical account code (e.g., "1.10.10.10") |
| `description` | string | READ_ONLY | - | Short label |
| `long_description` | string \| null | READ_ONLY | - | GAAP explanation |
| `type` | string(1) | READ_ONLY | - | 'H' (Header) or 'D' (Detail) |
| `category` | string | READ_ONLY | - | ASSET/LIABILITY/EQUITY/REVENUE/COGS/EXPENSE/OTHER |
| `normal_balance` | string \| null | READ_ONLY | - | "Debit" or "Credit" |
| `level` | integer | READ_ONLY | - | Hierarchy depth |
| `parent_id` | UUID \| null | READ_ONLY | - | UUID parent reference |
| `parent_code` | string \| null | EXCLUDED | **DEPRECATED** | **DO NOT EXPOSE** - Use `parent_id` instead |
| `fs_mapping` | string \| null | READ_ONLY | - | Financial statement placement |
| `cash_flow_classification` | string \| null | READ_ONLY | - | Operating/Investing/Financing |
| `tags` | string[] \| null | READ_ONLY | - | AI keywords |
| `default_vendors` | string[] \| null | READ_ONLY | - | Vendor associations |
| `regulatory_mapping` | JSONB \| null | READ_ONLY | - | IFRS/IAS/ASC references |
| `cost_center` | string \| null | READ_ONLY | - | Default cost center |
| `version` | string | READ_ONLY | - | Release version |
| `start_date` | date | READ_ONLY | - | Validity start |
| `end_date` | date \| null | READ_ONLY | - | Validity end (null = active) |
| `notes` | string \| null | READ_ONLY | - | Implementation guidance |
| `embedding` | EXCLUDED | **INTERNAL ONLY** | **DO NOT EXPOSE** | pgvector data |

### Response DTO: `MasterAccountResponse`

```typescript
{
  id: UUID
  code: string
  description: string
  long_description: string | null
  type: "H" | "D"
  category: string
  normal_balance: "Debit" | "Credit" | null
  level: integer
  parent_id: UUID | null
  fs_mapping: string | null
  cash_flow_classification: string | null
  tags: string[] | null
  default_vendors: string[] | null
  regulatory_mapping: object | null
  cost_center: string | null
  version: string
  start_date: date
  end_date: date | null
  notes: string | null
}
```

**No Create/Update DTOs:** Master chart is read-only via API. Modifications happen through database migrations only.

**Excluded Fields:**
- `parent_code` - **DEPRECATED**, use `parent_id` for relationships
- `embedding` - Internal pgvector data

---

## 5. JournalEntryDTO

**Purpose:** Represents a journal entry header (double-entry transaction).

**Database Model:** `JournalEntry` ([journal_entry.py:16-92](backend/app/db/models/journal_entry.py#L16-L92))

### Field Classification Table

| Field Name | Type | Classification | Tags | Rationale |
|---|---|---|---|---|
| `id` | UUID | READ_ONLY, SERVER_CONTROLLED | - | Primary key, server-generated |
| `company_id` | UUID | REQUIRED | IMMUTABLE_ALWAYS | Company ownership, cannot change |
| `fiscal_period_id` | UUID | REQUIRED | IMMUTABLE_WHEN_POSTED | Fiscal period assignment, locked when posted |
| `entry_number` | string | READ_ONLY, SERVER_CONTROLLED | - | Auto-generated (e.g., "JE-2024-001") |
| `entry_date` | date | REQUIRED | IMMUTABLE_WHEN_POSTED | Transaction date, locked when posted |
| `description` | string | REQUIRED | CLIENT_CONTROLLED (draft only) | Entry description, editable in draft |
| `reference` | string \| null | OPTIONAL | CLIENT_CONTROLLED (draft only) | External reference, editable in draft |
| `entry_type` | EntryType enum | OPTIONAL | IMMUTABLE_WHEN_POSTED | STANDARD/ADJUSTING/CLOSING/REVERSING/OPENING |
| `status` | EntryStatus enum | READ_ONLY, SERVER_CONTROLLED | - | DRAFT/POSTED/VOID, managed by post/void endpoints |
| `created_by` | UUID | READ_ONLY, SERVER_CONTROLLED | - | Audit trail |
| `created_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |
| `updated_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |
| `posted_at` | timestamp \| null | READ_ONLY, SERVER_CONTROLLED | - | Post timestamp |
| `posted_by` | UUID \| null | READ_ONLY, SERVER_CONTROLLED | - | User who posted |
| `voided_at` | timestamp \| null | READ_ONLY, SERVER_CONTROLLED | - | Void timestamp |
| `voided_by` | UUID \| null | READ_ONLY, SERVER_CONTROLLED | - | User who voided |
| `void_reason` | string \| null | READ_ONLY (set via void endpoint) | - | Void reason, provided when voiding |
| `reverses_entry_id` | UUID \| null | OPTIONAL | IMMUTABLE_WHEN_POSTED | Links to original entry if reversing |
| `reversed_by_entry_id` | UUID \| null | READ_ONLY, SERVER_CONTROLLED | - | Links to reversing entry |

### Create Request DTO: `JournalEntryCreate`

```typescript
{
  company_id: UUID              // REQUIRED
  fiscal_period_id: UUID        // REQUIRED - must be OPEN
  entry_date: date              // REQUIRED - must be within period
  description: string           // REQUIRED
  reference?: string | null     // OPTIONAL - invoice #, check #, etc.
  entry_type?: EntryType        // OPTIONAL - defaults to STANDARD
  reverses_entry_id?: UUID | null  // OPTIONAL - for reversing entries
  lines: JournalEntryLineCreate[]  // REQUIRED - minimum 2 lines
}
```

**Validation Rules:**
- `lines` must have at least 2 entries
- Sum of debits must equal sum of credits (exact decimal precision)
- `fiscal_period_id` must reference an OPEN period
- `entry_date` must be within fiscal period bounds
- All `company_account_id` in lines must belong to `company_id`

### Update Request DTO: `JournalEntryUpdate`

**Only allowed when `status = DRAFT`**

```typescript
{
  entry_date?: date             // Must be within fiscal period
  description?: string
  reference?: string | null
  entry_type?: EntryType
  lines?: JournalEntryLineCreate[]  // Replaces ALL lines
}
```

**Validation Rules:**
- Rejected if `status != DRAFT` with error code `STATE_CONFLICT`
- If `lines` provided, all existing lines replaced (atomic operation)
- Double-entry validation still applies

### Post Request DTO: `JournalEntryPost`

```typescript
{
  // No fields - posting is an action, not a data change
}
```

**Side Effects:**
- `status` → POSTED
- `posted_at` → current timestamp
- `posted_by` → current user ID
- Account balances updated in ledger
- Accounts may be locked (FirstTransaction reason)

### Void Request DTO: `JournalEntryVoid`

**Only allowed when `status = POSTED`**

```typescript
{
  void_reason: string           // REQUIRED - audit justification
}
```

**Side Effects:**
- `status` → VOID
- `voided_at` → current timestamp
- `voided_by` → current user ID
- `void_reason` → stored
- **Note:** Voiding does NOT reverse balances, create reversing entry for that

### Response DTO: `JournalEntryResponse`

```typescript
{
  id: UUID
  company_id: UUID
  fiscal_period_id: UUID
  entry_number: string
  entry_date: date
  description: string
  reference: string | null
  entry_type: EntryType
  status: "DRAFT" | "POSTED" | "VOID"
  created_by: UUID
  created_at: timestamp
  updated_at: timestamp
  posted_at: timestamp | null
  posted_by: UUID | null
  voided_at: timestamp | null
  voided_by: UUID | null
  void_reason: string | null
  reverses_entry_id: UUID | null
  reversed_by_entry_id: UUID | null
  lines: JournalEntryLineResponse[]
  total_debit: Decimal          // Computed from lines
  total_credit: Decimal         // Computed from lines
}
```

---

## 6. JournalEntryLineDTO

**Purpose:** Represents a single debit or credit line within a journal entry.

**Database Model:** `JournalEntryLine` ([journal_entry_line.py:9-66](backend/app/db/models/journal_entry_line.py#L9-L66))

### Field Classification Table

| Field Name | Type | Classification | Tags | Rationale |
|---|---|---|---|---|
| `id` | UUID | READ_ONLY, SERVER_CONTROLLED | - | Primary key, server-generated |
| `journal_entry_id` | UUID | REQUIRED | IMMUTABLE_ALWAYS | Parent entry, cannot change |
| `company_account_id` | UUID | REQUIRED | IMMUTABLE_WHEN_POSTED | Account reference, locked when posted |
| `line_number` | integer | REQUIRED | CLIENT_CONTROLLED (draft only) | Display order (1, 2, 3...) |
| `description` | string \| null | OPTIONAL | CLIENT_CONTROLLED (draft only) | Line-level description |
| `debit_amount` | Decimal(15,2) | REQUIRED | CLIENT_CONTROLLED (draft only) | Debit amount (0 if credit line) |
| `credit_amount` | Decimal(15,2) | REQUIRED | CLIENT_CONTROLLED (draft only) | Credit amount (0 if debit line) |
| `created_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |
| `updated_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |

### Create Request DTO: `JournalEntryLineCreate`

**Nested within `JournalEntryCreate`**

```typescript
{
  company_account_id: UUID      // REQUIRED
  line_number: integer          // REQUIRED - 1, 2, 3...
  description?: string | null   // OPTIONAL
  debit_amount: Decimal         // REQUIRED - 0 if credit line
  credit_amount: Decimal        // REQUIRED - 0 if debit line
}
```

**Validation Rules:**
- Exactly one of `debit_amount` or `credit_amount` must be non-zero
- Cannot have both non-zero (rejected with `JOURNAL_IMBALANCE`)
- Cannot have both zero (rejected with `JOURNAL_IMBALANCE`)
- Amounts cannot be negative
- Precision: 15 digits total, 2 decimal places

### Response DTO: `JournalEntryLineResponse`

```typescript
{
  id: UUID
  journal_entry_id: UUID
  company_account_id: UUID
  line_number: integer
  description: string | null
  debit_amount: Decimal
  credit_amount: Decimal
  created_at: timestamp
  updated_at: timestamp
}
```

---

## 7. FiscalPeriodDTO

**Purpose:** Represents an accounting period for a company.

**Database Model:** `FiscalPeriod` ([fiscal_period.py:16-54](backend/app/db/models/fiscal_period.py#L16-L54))

### Field Classification Table

| Field Name | Type | Classification | Tags | Rationale |
|---|---|---|---|---|
| `id` | UUID | READ_ONLY, SERVER_CONTROLLED | - | Primary key, server-generated |
| `company_id` | UUID | REQUIRED | IMMUTABLE_ALWAYS | Company ownership, cannot change |
| `period_type` | PeriodType enum | REQUIRED | IMMUTABLE_ALWAYS | MONTH/QUARTER/YEAR, immutable |
| `period_number` | string | REQUIRED | IMMUTABLE_ALWAYS | "2024-01", "2024-Q1", "2024", immutable |
| `start_date` | date | REQUIRED | IMMUTABLE_ALWAYS | Period start, immutable |
| `end_date` | date | REQUIRED | IMMUTABLE_ALWAYS | Period end, immutable |
| `status` | PeriodStatus enum | READ_ONLY, SERVER_CONTROLLED | - | OPEN/CLOSED/LOCKED, managed by close/reopen endpoints |
| `closed_at` | timestamp \| null | READ_ONLY, SERVER_CONTROLLED | - | Close timestamp |
| `closed_by` | UUID \| null | READ_ONLY, SERVER_CONTROLLED | - | User who closed |
| `created_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |
| `updated_at` | timestamp | READ_ONLY, SERVER_CONTROLLED | - | Audit timestamp |

### Create Request DTO: `FiscalPeriodCreate`

```typescript
{
  company_id: UUID              // REQUIRED
  period_type: PeriodType       // REQUIRED - MONTH|QUARTER|YEAR
  period_number: string         // REQUIRED - "2024-01", "2024-Q1", "2024"
  start_date: date              // REQUIRED
  end_date: date                // REQUIRED - must be >= start_date
}
```

**Validation Rules:**
- `end_date` must be >= `start_date`
- Period dates must not overlap with existing periods for same company
- `period_number` format must match `period_type`

### Close Request DTO: `FiscalPeriodClose`

```typescript
{
  // No fields - closing is an action, not data
}
```

**Validation Rules:**
- Period must have `status = OPEN`
- All journal entries in period must be POSTED (no drafts)
- Requires `can_manage_company` permission

**Side Effects:**
- `status` → CLOSED
- `closed_at` → current timestamp
- `closed_by` → current user ID
- Accounts may be locked (PeriodClose reason)

### Reopen Request

**No DTO - endpoint only**

**Validation Rules:**
- Period must have `status = CLOSED` (not LOCKED)
- Requires **superuser privileges**
- Creates audit trail

**Side Effects:**
- `status` → OPEN
- `closed_at` → null
- `closed_by` → null
- Accounts remain locked (unlock separately if needed)

### Response DTO: `FiscalPeriodResponse`

```typescript
{
  id: UUID
  company_id: UUID
  period_type: "MONTH" | "QUARTER" | "YEAR"
  period_number: string
  start_date: date
  end_date: date
  status: "OPEN" | "CLOSED" | "LOCKED"
  closed_at: timestamp | null
  closed_by: UUID | null
  created_at: timestamp
  updated_at: timestamp
}
```

---

## 8. AccountLockStatusDTO

**Purpose:** Nested/embedded DTO for account lock metadata. Not a standalone entity.

**Context:** Embedded in `CompanyAccountResponse` or returned by lock/unlock endpoints.

### Response DTO: `AccountLockStatusResponse`

```typescript
{
  is_locked: boolean
  locked_at: timestamp | null
  locked_reason: "FirstTransaction" | "PeriodClose" | "Manual" | null
  locked_by: UUID | null
}
```

**Usage:**
- Embedded in `CompanyAccountResponse`
- Returned by `/lock` and `/unlock` endpoints
- Read-only, managed by lock/unlock operations

### Lock Request DTO: `AccountLockRequest`

```typescript
{
  reason: "FirstTransaction" | "PeriodClose" | "Manual"  // REQUIRED
  user_id?: UUID               // REQUIRED if reason = "Manual"
}
```

### Unlock Request DTO: `AccountUnlockRequest`

```typescript
{
  // No fields - unlock reason tracked in audit log
}
```

**Validation Rules:**
- Unlock requires **superuser privileges**
- Cannot unlock if posted transactions exist in current period
- Audit trail records unlock operation

---

## Step 3: Lock & Immutability Overlay

### Immutability Rules Matrix

| DTO | Condition | Immutable Fields |
|---|---|---|
| **CompanyAccount** | `is_locked = true` | `code`, `account_type`, `normal_balance`, `parent_id`, `mapped_master_account_id` |
| **CompanyAccount** | Always | `company_id`, `template_account_id` |
| **JournalEntry** | `status = POSTED` | `entry_date`, `description`, `reference`, `entry_type`, `fiscal_period_id`, `lines` |
| **JournalEntry** | `status = VOID` | ALL fields (cannot modify voided entries) |
| **JournalEntry** | Always | `company_id`, `entry_number`, `status` |
| **JournalEntryLine** | Parent `status = POSTED` | ALL fields (lines inherit entry immutability) |
| **JournalEntryLine** | Always | `journal_entry_id` |
| **FiscalPeriod** | Always | `company_id`, `period_type`, `period_number`, `start_date`, `end_date`, `status` |
| **ChartTemplate** | Always | `jurisdiction`, `version` |
| **ChartTemplateAccount** | Always | `template_id`, `master_account_id`, `parent_id`, `code` |
| **MasterAccount** | Always | ALL fields (read-only API) |

### Enforcement Strategy

**Service Layer Responsibility:**
- `CompanyChartService.update_account()` checks `is_locked` before allowing changes
- `JournalEntryService.update_journal_entry()` checks `status != POSTED`
- `FiscalPeriodService.reopen_fiscal_period()` checks superuser privileges

**API Layer Responsibility:**
- Return `400 Bad Request` with specific error code
- Error codes: `LOCKED_ACCOUNT`, `STATE_CONFLICT`, `PERMISSION_DENIED`
- Do NOT bypass validation

---

## Step 4: OpenAPI-Ready Schema Definitions

### Enum Definitions

```yaml
AccountType:
  type: string
  enum: [Asset, Liability, Equity, Revenue, Expense]

NormalBalance:
  type: string
  enum: [Debit, Credit]

LockedReason:
  type: string
  enum: [FirstTransaction, PeriodClose, Manual]

EntryStatus:
  type: string
  enum: [DRAFT, POSTED, VOID]

EntryType:
  type: string
  enum: [STANDARD, ADJUSTING, CLOSING, REVERSING, OPENING]

PeriodStatus:
  type: string
  enum: [OPEN, CLOSED, LOCKED]

PeriodType:
  type: string
  enum: [MONTH, QUARTER, YEAR]
```

### CompanyAccount Schemas

```yaml
CompanyAccountCreate:
  type: object
  required:
    - company_id
    - code
    - name
    - description
    - account_type
    - normal_balance
  properties:
    company_id:
      type: string
      format: uuid
    code:
      type: string
      maxLength: 50
    name:
      type: string
      maxLength: 255
    description:
      type: string
    account_type:
      $ref: '#/components/schemas/AccountType'
    normal_balance:
      $ref: '#/components/schemas/NormalBalance'
    parent_id:
      type: string
      format: uuid
      nullable: true
    mapped_master_account_id:
      type: string
      format: uuid
      nullable: true
    currency:
      type: string
      pattern: '^[A-Z]{3}$'
      default: USD
    json_data:
      type: object
      nullable: true

CompanyAccountUpdate:
  type: object
  properties:
    name:
      type: string
      maxLength: 255
    description:
      type: string
    currency:
      type: string
      pattern: '^[A-Z]{3}$'
    json_data:
      type: object
      nullable: true
    # Following fields only allowed when is_locked = false
    code:
      type: string
      maxLength: 50
    account_type:
      $ref: '#/components/schemas/AccountType'
    normal_balance:
      $ref: '#/components/schemas/NormalBalance'
    parent_id:
      type: string
      format: uuid
      nullable: true
    mapped_master_account_id:
      type: string
      format: uuid
      nullable: true

CompanyAccountResponse:
  type: object
  required:
    - id
    - company_id
    - code
    - description
    - account_type
    - normal_balance
    - is_active
    - is_locked
    - currency
    - created_at
    - updated_at
  properties:
    id:
      type: string
      format: uuid
      readOnly: true
    company_id:
      type: string
      format: uuid
      readOnly: true
    code:
      type: string
    name:
      type: string
      nullable: true
    description:
      type: string
    account_type:
      $ref: '#/components/schemas/AccountType'
    normal_balance:
      $ref: '#/components/schemas/NormalBalance'
    parent_id:
      type: string
      format: uuid
      nullable: true
    mapped_master_account_id:
      type: string
      format: uuid
      nullable: true
    template_account_id:
      type: string
      format: uuid
      nullable: true
      readOnly: true
    is_active:
      type: boolean
      readOnly: true
    is_locked:
      type: boolean
      readOnly: true
    locked_at:
      type: string
      format: date-time
      nullable: true
      readOnly: true
    locked_reason:
      $ref: '#/components/schemas/LockedReason'
      nullable: true
      readOnly: true
    locked_by:
      type: string
      format: uuid
      nullable: true
      readOnly: true
    currency:
      type: string
      pattern: '^[A-Z]{3}$'
    json_data:
      type: object
      nullable: true
    created_at:
      type: string
      format: date-time
      readOnly: true
    updated_at:
      type: string
      format: date-time
      readOnly: true
```

### JournalEntry Schemas

```yaml
JournalEntryCreate:
  type: object
  required:
    - company_id
    - fiscal_period_id
    - entry_date
    - description
    - lines
  properties:
    company_id:
      type: string
      format: uuid
    fiscal_period_id:
      type: string
      format: uuid
    entry_date:
      type: string
      format: date
    description:
      type: string
    reference:
      type: string
      nullable: true
    entry_type:
      $ref: '#/components/schemas/EntryType'
      default: STANDARD
    reverses_entry_id:
      type: string
      format: uuid
      nullable: true
    lines:
      type: array
      minItems: 2
      items:
        $ref: '#/components/schemas/JournalEntryLineCreate'

JournalEntryLineCreate:
  type: object
  required:
    - company_account_id
    - line_number
    - debit_amount
    - credit_amount
  properties:
    company_account_id:
      type: string
      format: uuid
    line_number:
      type: integer
      minimum: 1
    description:
      type: string
      nullable: true
    debit_amount:
      type: number
      format: decimal
      minimum: 0
    credit_amount:
      type: number
      format: decimal
      minimum: 0

JournalEntryResponse:
  type: object
  properties:
    id:
      type: string
      format: uuid
      readOnly: true
    company_id:
      type: string
      format: uuid
      readOnly: true
    fiscal_period_id:
      type: string
      format: uuid
    entry_number:
      type: string
      readOnly: true
    entry_date:
      type: string
      format: date
    description:
      type: string
    reference:
      type: string
      nullable: true
    entry_type:
      $ref: '#/components/schemas/EntryType'
    status:
      $ref: '#/components/schemas/EntryStatus'
      readOnly: true
    created_by:
      type: string
      format: uuid
      readOnly: true
    created_at:
      type: string
      format: date-time
      readOnly: true
    updated_at:
      type: string
      format: date-time
      readOnly: true
    posted_at:
      type: string
      format: date-time
      nullable: true
      readOnly: true
    posted_by:
      type: string
      format: uuid
      nullable: true
      readOnly: true
    voided_at:
      type: string
      format: date-time
      nullable: true
      readOnly: true
    voided_by:
      type: string
      format: uuid
      nullable: true
      readOnly: true
    void_reason:
      type: string
      nullable: true
      readOnly: true
    reverses_entry_id:
      type: string
      format: uuid
      nullable: true
    reversed_by_entry_id:
      type: string
      format: uuid
      nullable: true
      readOnly: true
    lines:
      type: array
      items:
        $ref: '#/components/schemas/JournalEntryLineResponse'
    total_debit:
      type: number
      format: decimal
      readOnly: true
    total_credit:
      type: number
      format: decimal
      readOnly: true
```

### FiscalPeriod Schemas

```yaml
FiscalPeriodCreate:
  type: object
  required:
    - company_id
    - period_type
    - period_number
    - start_date
    - end_date
  properties:
    company_id:
      type: string
      format: uuid
    period_type:
      $ref: '#/components/schemas/PeriodType'
    period_number:
      type: string
      pattern: '^\d{4}-(0[1-9]|1[0-2]|Q[1-4])$|^\d{4}$'
    start_date:
      type: string
      format: date
    end_date:
      type: string
      format: date

FiscalPeriodResponse:
  type: object
  properties:
    id:
      type: string
      format: uuid
      readOnly: true
    company_id:
      type: string
      format: uuid
      readOnly: true
    period_type:
      $ref: '#/components/schemas/PeriodType'
      readOnly: true
    period_number:
      type: string
      readOnly: true
    start_date:
      type: string
      format: date
      readOnly: true
    end_date:
      type: string
      format: date
      readOnly: true
    status:
      $ref: '#/components/schemas/PeriodStatus'
      readOnly: true
    closed_at:
      type: string
      format: date-time
      nullable: true
      readOnly: true
    closed_by:
      type: string
      format: uuid
      nullable: true
      readOnly: true
    created_at:
      type: string
      format: date-time
      readOnly: true
    updated_at:
      type: string
      format: date-time
      readOnly: true
```

---

## Ambiguities & Design Decisions

### 1. Template Model Discrepancy

**Discovery:** Two template models exist:
- `Template` (old, simple JSONB storage)
- `ChartTemplate` + `ChartTemplateAccount` (new, normalized)

**Decision:** Use **ChartTemplate** for DTOs. The old `Template` model is deprecated and should not be exposed via Phase 3C APIs.

**Rationale:** Normalized template structure enables proper enforcement of `is_mandatory` and `allow_custom_children` flags.

### 2. CompanyAccount `type` Field

**Discovery:** `type` field (H/D) exists alongside `account_type` enum (Asset/Liability/etc.)

**Decision:** `type` is **DEPRECATED**, exclude from DTOs. Clients must use `account_type`.

**Rationale:** `account_type` provides richer classification needed for financial statements.

### 3. MasterAccount `parent_code` Field

**Discovery:** Both `parent_id` (UUID FK) and `parent_code` (string) exist.

**Decision:** `parent_code` is **DEPRECATED**, exclude from DTOs. Clients must use `parent_id` for hierarchy.

**Rationale:** UUID-based relationships are mandatory per Phase 3C requirements.

### 4. Embedding Fields

**Discovery:** Both `CompanyAccount` and `MasterAccount` have `embedding` columns for pgvector semantic search.

**Decision:** **EXCLUDE** from all DTOs. Embeddings are internal implementation details.

**Rationale:** Clients have no use for raw 384-dimension vectors. Semantic search exposed through dedicated endpoints.

### 5. JournalEntry Line Replacement

**Discovery:** Update endpoint could partially update lines or replace all.

**Decision:** `JournalEntryUpdate` with `lines` field **replaces ALL lines** (atomic operation).

**Rationale:** Partial line updates create complexity. Atomic replacement ensures double-entry validation always succeeds.

### 6. AccountLockStatus as DTO

**Discovery:** Lock status fields spread across `CompanyAccount`.

**Decision:** Create **nested DTO** `AccountLockStatusResponse` for clarity, but not a separate entity.

**Rationale:** Lock status is account metadata, not a separate resource. Nested DTO improves API documentation clarity.

---

## Field Exclusion Rationale

### Fields EXCLUDED from DTOs

| Model | Field | Reason |
|---|---|---|
| CompanyAccount | `type` | DEPRECATED - Use `account_type` |
| CompanyAccount | `embedding` | Internal pgvector data |
| MasterAccount | `parent_code` | DEPRECATED - Use `parent_id` |
| MasterAccount | `embedding` | Internal pgvector data |
| All models | `__relationships__` | Not serialized in DTOs |

---

## Phase 3C-1 Completion Summary

### Deliverables

✅ **DTO Inventory (8 DTOs)**
- CompanyAccountDTO
- ChartTemplateDTO
- ChartTemplateAccount DTO
- MasterAccountDTO
- JournalEntryDTO
- JournalEntryLineDTO
- FiscalPeriodDTO
- AccountLockStatusDTO

✅ **Field Classification Tables**
- Every field tagged: REQUIRED/OPTIONAL/READ_ONLY/SERVER_CONTROLLED/CLIENT_CONTROLLED
- Immutability conditions documented

✅ **Lock & Immutability Overlay**
- Immutability matrix created
- Conditional rules defined (LOCKED, POSTED, CLOSED)

✅ **OpenAPI-Ready Schemas**
- Complete YAML schemas for all DTOs
- Enums defined matching backend exactly
- Validation rules embedded (minLength, pattern, etc.)

### Ambiguities Resolved

1. **Template model choice** → ChartTemplate (normalized)
2. **Deprecated fields** → Excluded (type, parent_code)
3. **Internal fields** → Excluded (embedding)
4. **Line update semantics** → Atomic replacement
5. **Lock status** → Nested DTO
6. **Read-only API** → MasterAccount (no mutations)

### Next Steps

Ready to proceed to **Phase 3C-2: Write APIs** implementation.

---

**Document Authority:** api-guardian + contract-architect
**Status:** CANONICAL - Phase 3C-1 COMPLETE
**Next Phase:** 3C-2 (Write APIs)
