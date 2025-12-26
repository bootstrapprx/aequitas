# Post-Activation Dashboard UX

**Purpose:** Define what a user sees immediately after activation, so they understand what is protected, what they can do, and what the system will never do for them.

**Authority:** Canon I (Accounting Truth), Canon II (Authority and Power)
**Date:** 2025-12-24
**Status:** UX Copy & Structure Design

---

## Design Principles

1. **Neutral, calm, factual language** — No urgency, no sales pitch
2. **Clarity over brevity** — Users must understand boundaries
3. **Explicit non-actions** — State what the system will NOT do
4. **Human authority** — User is in control, system is servant

---

## First-Day Dashboard

### Dashboard Header

```
┌─────────────────────────────────────────────────────────────────┐
│ Welcome to Aequitas                                             │
│ Your accounting system is active and ready.                     │
└─────────────────────────────────────────────────────────────────┘
```

---

### Section 1: Your Protected Foundation

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔒 Protected Structure                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Your chart of accounts is protected by the Kernel 2025.2       │
│ accounting standard.                                            │
│                                                                 │
│ This ensures:                                                   │
│   • Your books can always balance                               │
│   • Fiscal periods can be closed                                │
│   • Financial reports will be accurate                          │
│                                                                 │
│ Protected accounts include:                                     │
│   • Cash & Banking                                              │
│   • Receivables & Payables                                      │
│   • Equity & Retained Earnings                                  │
│   • Core Revenue & Expenses                                     │
│                                                                 │
│ These accounts cannot be deleted or renamed.                    │
│                                                                 │
│ [View Chart of Accounts]                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Tone:** Informative, protective, non-technical

---

### Section 2: What You Can Do Now

```
┌─────────────────────────────────────────────────────────────────┐
│ ✅ Available Actions                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Journal Entries                                                 │
│   Record transactions using double-entry bookkeeping.           │
│   All entries require your review before posting.               │
│   [Create Entry]                                                │
│                                                                 │
│ Chart of Accounts                                               │
│   View your full chart, add custom accounts, or organize        │
│   categories. Core accounts are protected.                      │
│   [Manage Chart]                                                │
│                                                                 │
│ Financial Reports                                               │
│   Generate Balance Sheet, Income Statement, Trial Balance,      │
│   and other reports. Reports reflect posted transactions only.  │
│   [View Reports]                                                │
│                                                                 │
│ Fiscal Periods                                                  │
│   Open or close accounting periods. Closing a period locks      │
│   past transactions and requires your explicit approval.        │
│   [Manage Periods]                                              │
│                                                                 │
│ Sandbox (Practice Mode)                                         │
│   Test transactions in a sandbox environment before posting     │
│   to your real ledger. Sandbox entries do NOT affect your       │
│   financial statements.                                         │
│   [Open Sandbox]                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tone:** Enabling, clear boundaries, action-oriented

---

### Section 3: What We Will NOT Do

```
┌─────────────────────────────────────────────────────────────────┐
│ 🛡️  System Boundaries                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Aequitas will NEVER:                                            │
│                                                                 │
│   ❌ Post transactions without your approval                    │
│      Every journal entry requires human review and consent.     │
│                                                                 │
│   ❌ Modify or delete posted entries                            │
│      History is permanent. You can reverse errors with new      │
│      entries, but the original entry remains in the ledger.     │
│                                                                 │
│   ❌ Automatically close fiscal periods                         │
│      Period closing is a significant accounting event that      │
│      requires your explicit approval and review.                │
│                                                                 │
│   ❌ Move sandbox entries to your real ledger                   │
│      Sandbox is isolated. You control what becomes real.        │
│                                                                 │
│   ❌ Change your chart of accounts without permission           │
│      You can add custom accounts, but protected accounts        │
│      remain fixed.                                              │
│                                                                 │
│ You are in control. The system is your tool, not your          │
│ decision-maker.                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tone:** Protective, explicit, trust-building

---

### Section 4: Next Steps (Optional Guidance)

```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 Suggested Next Steps                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Review your chart of accounts                                │
│    Familiarize yourself with the protected structure.           │
│    [View Chart]                                                 │
│                                                                 │
│ 2. Set up your first fiscal period                              │
│    Define your accounting period (monthly, quarterly, annual).  │
│    [Create Fiscal Period]                                       │
│                                                                 │
│ 3. Record your opening balances (if applicable)                 │
│    If migrating from another system, record initial balances.   │
│    [Create Opening Entry]                                       │
│                                                                 │
│ 4. Try the sandbox                                              │
│    Practice creating entries in sandbox mode before posting     │
│    real transactions.                                           │
│    [Open Sandbox]                                               │
│                                                                 │
│ These steps are optional. You can start anywhere.               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tone:** Helpful, non-prescriptive, low-pressure

---

## Allowed Actions (Detailed)

### 1. Journaling

**What User Can Do:**
- Create new journal entries (debits and credits must balance)
- Select accounts from their chart
- Add notes and attachments
- Save as draft (not posted)
- Review and post (makes entry permanent)

**What System Does:**
- Validates double-entry balance (debits = credits)
- Checks fiscal period status (open/closed)
- Prevents posting to closed periods
- Records posted entries permanently

**What System Does NOT Do:**
- Auto-suggest accounts (user must select)
- Auto-fill amounts (user must enter)
- Auto-post drafts (user must approve)

**UI Copy:**
```
Create Journal Entry

A journal entry records a financial transaction using double-entry
bookkeeping. All entries must balance (debits = credits).

You must review and approve before posting.
Once posted, entries cannot be deleted (only reversed).

[Create Draft Entry]
```

---

### 2. Viewing Reports

**What User Can Do:**
- Generate Balance Sheet (Assets = Liabilities + Equity)
- Generate Income Statement (Revenue - Expenses)
- Generate Trial Balance (all account balances)
- Filter by date range
- Export to PDF or CSV

**What System Does:**
- Aggregates posted transactions only
- Applies GAAP classification rules
- Shows real-time balances

**What System Does NOT Do:**
- Modify balances for display
- Hide or adjust accounts
- Predict future balances

**UI Copy:**
```
Financial Reports

Reports show posted transactions only.
Sandbox entries are not included.

All reports follow US GAAP standards.
Balances are real-time and accurate.

[Generate Report]
```

---

### 3. Adding Custom Accounts

**What User Can Do:**
- Add custom detail accounts
- Assign to categories (Asset, Liability, Revenue, Expense)
- Set account codes (must not conflict with protected codes)
- Mark as active/inactive

**What User Cannot Do:**
- Delete protected kernel accounts
- Rename protected kernel accounts
- Change category of protected accounts

**UI Copy:**
```
Add Custom Account

You can add custom accounts to track specific items
(e.g., "AWS Hosting Expense" or "Client Retainer Account").

Custom accounts must:
  • Have unique account codes
  • Be assigned to a valid category
  • Not conflict with protected accounts

Protected kernel accounts cannot be deleted or renamed.

[Add Account]
```

---

### 4. Managing Fiscal Periods

**What User Can Do:**
- Create new fiscal periods
- Open a period (allow posting)
- Close a period (lock past transactions)
- View period status

**What User Cannot Do:**
- Delete closed periods
- Modify locked periods
- Post to closed periods

**UI Copy:**
```
Fiscal Period Management

Fiscal periods define your accounting timeframes
(e.g., monthly, quarterly, annual).

Closing a period:
  • Locks all transactions in that period
  • Prevents future posting to past dates
  • Transfers net income to Retained Earnings

Closing is permanent and requires your explicit approval.

[Create Period] [Close Period]
```

---

### 5. Using the Sandbox

**What User Can Do:**
- Create practice journal entries
- Test account structures
- Experiment with reporting
- Clear sandbox anytime

**What Sandbox Does NOT Do:**
- Affect real ledger
- Appear in financial reports
- Persist after clearing

**UI Copy:**
```
Sandbox Mode

The sandbox is an isolated practice environment.

You can:
  • Test journal entries
  • Experiment with accounts
  • See how reports would look

Sandbox entries:
  • Do NOT affect your real ledger
  • Do NOT appear in financial reports
  • Can be cleared at any time

To make an entry real, you must create it in the ledger
(outside sandbox).

[Enter Sandbox]
```

---

## Protected Concepts

### 1. History (Immutable)

**User Understanding:**
> "Once a transaction is posted, it cannot be deleted or modified.
> If you made a mistake, you create a reversing entry.
> This ensures audit trail integrity."

**System Behavior:**
- Posted entries have `is_posted = true`
- No UPDATE or DELETE allowed on posted entries
- Reversal creates new entry with opposite signs

---

### 2. Fiscal Periods (Closable)

**User Understanding:**
> "Closing a period locks past transactions.
> You can still view historical data, but you cannot post new
> entries to closed periods."

**System Behavior:**
- Closed periods have `status = 'CLOSED'`
- Posting validation checks period status
- Period closing transfers net income to Retained Earnings

---

### 3. Chart Structure (Protected Core)

**User Understanding:**
> "Your chart includes 20 protected accounts required for
> accounting compliance. These cannot be deleted or renamed.
> You can add custom accounts around them."

**System Behavior:**
- Kernel accounts have `is_system = true`
- DELETE blocked on system accounts
- UPDATE blocked on `code`, `category` for system accounts

---

## Explicit Non-Actions

### What The System Will NEVER Do

1. **Auto-Post Transactions**
   - No background jobs that create journal entries
   - No AI-suggested postings that bypass user review
   - No automated period closing

2. **Modify History**
   - No retroactive changes to posted entries
   - No deletion of historical transactions
   - No balance adjustments without journal entries

3. **Make Accounting Decisions**
   - No auto-classification of expenses
   - No auto-categorization of revenue
   - No predictive postings

4. **Move Sandbox → Ledger Automatically**
   - Sandbox is isolated
   - User must explicitly recreate entries in ledger

5. **Hide or Mask Balances**
   - All reports show actual balances
   - No "smoothing" or "adjustments"
   - Transparency is absolute

---

## Tone & Voice Guidelines

### Do Use:
- ✅ "You can..."
- ✅ "You must review..."
- ✅ "This requires your approval..."
- ✅ "Aequitas will never..."
- ✅ "History is permanent..."

### Do NOT Use:
- ❌ "Let Aequitas handle this..."
- ❌ "Automatically optimize..."
- ❌ "Smart suggestions..."
- ❌ "AI-powered..."
- ❌ "Just click here..." (without explanation)

### Examples

**Good:**
> "You can close this fiscal period. Closing will lock all transactions
> for this period and transfer net income to Retained Earnings.
> This action requires your explicit approval."

**Bad:**
> "Close period now! Our AI will optimize your books automatically."

---

## Dashboard Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Header: Welcome + Company Name                                  │
├─────────────────────────────────────────────────────────────────┤
│ Protected Structure (always visible)                            │
├─────────────────────────────────────────────────────────────────┤
│ Available Actions (expandable cards)                            │
├─────────────────────────────────────────────────────────────────┤
│ System Boundaries (always visible)                              │
├─────────────────────────────────────────────────────────────────┤
│ Next Steps (collapsible, dismissible)                           │
└─────────────────────────────────────────────────────────────────┘
```

**Priority:**
1. Protected Structure (top) — Users must know what's fixed
2. Available Actions (middle) — Users must know what they can do
3. System Boundaries (bottom-middle) — Users must know what system won't do
4. Next Steps (bottom) — Optional guidance

---

## Mobile Adaptation

On mobile, use accordions:

```
📱 Mobile View

┌───────────────────────────┐
│ Welcome to Aequitas       │
├───────────────────────────┤
│ 🔒 Protected Structure ▼  │
│ ✅ Available Actions ▼    │
│ 🛡️  System Boundaries ▼   │
│ 📋 Next Steps ▼           │
└───────────────────────────┘
```

Tap to expand each section.

---

## Accessibility

- All UI copy must have ARIA labels
- Color is NOT the only indicator (use icons + text)
- Focus states visible for keyboard navigation
- Screen reader friendly (semantic HTML)

---

## Localization Notes

When translating:
- Preserve legal/accounting precision
- "Double-entry bookkeeping" → Use local GAAP term
- "Fiscal period" → Use local regulatory term
- "Journal entry" → May need context (not diary entry)

---

## Success Criteria

User understanding is successful when they can answer:

1. **What is protected?**
   → "My core chart of accounts and posted transactions."

2. **What can I do?**
   → "Record entries, view reports, manage periods, use sandbox."

3. **What will the system NOT do?**
   → "Post without my approval, delete history, auto-close periods."

4. **Who is in control?**
   → "I am. The system is my tool."

---

**Authority:** This UX design conforms to Canon I (truth boundaries) and Canon II (human authority).
**Prepared By:** Aequitas UX Architecture
**Date:** 2025-12-24
**Status:** UX Copy Design (No Code)
