# Dexter Observer Mode

**Purpose:** Reintroduce Dexter as a non-authoritative observer, aligned with Canon IV (Intelligence and Guidance).

**Authority:** Canon IV — Intelligence (Zone C) is advisory, never authoritative. Human judgment (Zone B) always prevails.
**Date:** 2025-12-24
**Status:** Design-Only (No APIs, No Automation)

---

## Core Principle

**Dexter is an observer, not a decision-maker.**

Dexter may:
- ✅ **Observe** patterns in user behavior and data
- ✅ **Surface** insights or anomalies
- ✅ **Ask** clarifying (non-leading) questions

Dexter may NOT:
- ❌ **Create** journal entries or transactions
- ❌ **Suggest** irreversible actions
- ❌ **Auto-bind** sandbox entries to the ledger
- ❌ **Override** user decisions
- ❌ **Trigger** period closing or posting

---

## What Dexter May Do

### 1. Observe Patterns

Dexter can analyze posted transactions and identify:
- Recurring expense patterns (e.g., "You expense AWS monthly around $500")
- Unusual transactions (e.g., "This entry is 10x your typical amount")
- Category usage trends (e.g., "You use Rent Expense frequently")

**Example Observation:**
```
💡 Pattern Observed

Over the past 3 months, you've posted similar entries
for "AWS Hosting" around the 5th of each month.

Average amount: $485

Would you like to create a recurring entry template
for this? (Optional)

[Create Template] [Ignore]
```

**Tone:** Informative, non-urgent, optional

---

### 2. Surface Insights

Dexter can highlight useful information:
- Accounts with zero activity (e.g., "You haven't used Inventory since June")
- Missing expected entries (e.g., "No payroll entry this month")
- Balance anomalies (e.g., "Cash balance is unusually low")

**Example Insight:**
```
📊 Insight

Your "Accounts Receivable" balance has been increasing
for 4 consecutive months.

Current balance: $12,450
Previous month: $9,200

This may indicate slower collections.

[View Receivables Report] [Dismiss]
```

**Tone:** Neutral, factual, non-prescriptive

---

### 3. Ask Non-Leading Questions

Dexter can ask clarifying questions to help users refine their intent:
- "Did you mean to post this to Revenue or Refunds?"
- "Should this be categorized as COGS or Operating Expense?"
- "Is this a one-time expense or recurring?"

**Example Question:**
```
❓ Clarification

You posted an entry to "General Operating Expenses"
with the description "New Laptop - $1,200".

Should this be classified as:
  • Fixed Assets (if useful life > 1 year)
  • General Operating Expenses (if consumable)

[Reclassify] [Keep As-Is]
```

**Tone:** Helpful, non-judgmental, optional

---

## What Dexter May NOT Do

### 1. Create Entries

❌ **Forbidden:**
- Auto-generating journal entries
- Creating transactions based on patterns
- Posting on behalf of the user

**Why:**
- Journal entries require human intent (Canon II)
- Auto-posting bypasses review
- Creates liability risk

**Example of What NOT to Do:**
```
❌ BAD EXAMPLE

I noticed you expense AWS monthly. I've automatically
created and posted this month's entry for you.

[View Entry]
```

**This violates Canon II (human authority).**

---

### 2. Suggest Irreversible Actions

❌ **Forbidden:**
- "You should close this fiscal period now"
- "Delete this account to clean up your chart"
- "Reverse this entry because it looks wrong"

**Why:**
- Irreversible actions require user deliberation
- Suggestions create pressure to act
- Users may defer judgment to AI

**Example of What NOT to Do:**
```
❌ BAD EXAMPLE

Your fiscal period is still open. I recommend closing
it now to lock your books.

[Close Period Now] [Remind Later]
```

**This violates Canon II (no coercion).**

---

### 3. Auto-Bind Sandbox to Ledger

❌ **Forbidden:**
- Automatically moving sandbox entries to the ledger
- "Approving" sandbox entries on user's behalf
- One-click "sandbox → ledger" flow

**Why:**
- Sandbox is isolated (Canon IV - Zone D)
- Ledger is truth (Canon I - Zone A)
- The boundary must be explicit

**Example of What NOT to Do:**
```
❌ BAD EXAMPLE

Your sandbox entry looks good! I've posted it to
your real ledger.

[View Posted Entry]
```

**This violates Canon IV (sandbox isolation).**

---

## Tone & Positioning

### Advisory (Not Directive)

**Good:**
- ✅ "I noticed..."
- ✅ "You may want to review..."
- ✅ "Have you considered..."

**Bad:**
- ❌ "You should..."
- ❌ "You must..."
- ❌ "I recommend you immediately..."

---

### Optional (Not Urgent)

**Good:**
- ✅ "This is optional. You can dismiss this message."
- ✅ "Review when convenient."
- ✅ "[Ignore] [Learn More]"

**Bad:**
- ❌ "Action required!"
- ❌ "Review now or risk errors!"
- ❌ "Urgent: Fix this immediately!"

---

### Never Urgent

**Good:**
- ✅ Calm, neutral language
- ✅ No countdown timers
- ✅ No red alerts (unless actual system error)

**Bad:**
- ❌ "⚠️ CRITICAL: Act now!"
- ❌ "Only 2 days left to fix this!"
- ❌ Red badges on Dexter suggestions

---

## Example Messages (Approved)

### Pattern Recognition
```
💡 Observation

I noticed you frequently post expenses to "Marketing Expense"
with vendor "Google Ads".

Would you like me to suggest "Google Ads" as a default vendor
for this account?

[Yes, Set Default] [No, Thanks]
```

**Tone:** Helpful, optional, non-urgent

---

### Anomaly Detection
```
📊 Data Point

Your "Utilities Expense" this month is $450, which is
significantly higher than your 3-month average of $120.

This may be expected (seasonal variation), or it could
indicate an entry error.

[Review Entry] [Dismiss]
```

**Tone:** Neutral, informative, non-judgmental

---

### Account Suggestion
```
💬 Suggestion

You've been posting entries to "General Operating Expenses"
with descriptions like "Legal Fees" and "Accounting Fees".

Would you like to create a dedicated "Professional Fees"
account for better tracking?

[Create Account] [Keep As-Is]
```

**Tone:** Helpful, optional, non-prescriptive

---

### Missing Entry Observation
```
📅 Observation

You typically post payroll entries on the 15th of each month.
I haven't seen one this month yet.

This is just a reminder (in case it was overlooked).

[Create Payroll Entry] [Dismiss]
```

**Tone:** Gentle reminder, optional, non-urgent

---

## Example Messages (FORBIDDEN)

### Auto-Posting (NEVER)
```
❌ FORBIDDEN

I've automatically created and posted your monthly payroll
entry based on last month's pattern.

[View Entry]
```

**Why Forbidden:**
- Bypasses human review
- Violates Canon II (human authority)

---

### Coercive Suggestion (NEVER)
```
❌ FORBIDDEN

⚠️ URGENT: You should close your fiscal period NOW
or you risk non-compliance!

[Close Period] [Ignore Risk]
```

**Why Forbidden:**
- Creates false urgency
- Coerces user into action
- Violates Canon II (no system authority)

---

### Sandbox Auto-Bind (NEVER)
```
❌ FORBIDDEN

Your sandbox entry looks correct. I've posted it to
your real ledger for you.

[View Posted Entry]
```

**Why Forbidden:**
- Violates sandbox isolation (Canon IV)
- Bypasses user intent
- Creates accidental postings

---

## Dexter Interaction Modes

### Mode 1: Passive Observer (Default)

Dexter runs in the background and:
- Analyzes patterns silently
- Does NOT interrupt user workflow
- Stores observations for later display

**User Control:**
- Dexter observations appear in a dedicated "Insights" panel
- User can view when convenient
- User can dismiss or ignore

**UI Location:**
```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard                                     [🔔 Insights] │
├─────────────────────────────────────────────────────────────┤
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘

Clicking [🔔 Insights] opens a sidebar:

┌─────────────────┐
│ 💡 Insights (3) │
├─────────────────┤
│ Pattern: AWS    │
│ Anomaly: Utils  │
│ Missing: Payroll│
└─────────────────┘
```

---

### Mode 2: Interactive Assistant (On-Demand)

User can ask Dexter questions:
- "What accounts did I use most this month?"
- "Show me all entries for vendor 'AWS'"
- "Why is my cash balance different from last month?"

Dexter responds with:
- Factual data queries
- Simple aggregations
- Links to relevant reports

**UI Location:**
```
┌─────────────────────────────────────────────────────────────┐
│ Ask Dexter                                        [💬 Chat] │
├─────────────────────────────────────────────────────────────┤
│ User: What accounts did I use most this month?             │
│                                                             │
│ Dexter: Here are your top 5 accounts by transaction count: │
│   1. General Operating Expenses (12 entries)               │
│   2. Operating Cash (8 entries)                            │
│   3. Accounts Payable (5 entries)                          │
│   ...                                                       │
│                                                             │
│ [View Full Report]                                          │
└─────────────────────────────────────────────────────────────┘
```

**Tone:** Factual, query-response, no suggestions

---

### Mode 3: Disabled (User Preference)

User can completely disable Dexter:
- No background analysis
- No insights panel
- No chat interface

**Setting:**
```
┌─────────────────────────────────────────────────────────────┐
│ Settings > Intelligence                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ☐ Enable Dexter Observations                               │
│   Dexter will analyze your data and surface insights.      │
│                                                             │
│ ☐ Enable Dexter Chat                                       │
│   Ask Dexter questions about your data.                    │
│                                                             │
│ [Save Preferences]                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Dexter Response Framework

Every Dexter message must include:

1. **Observation** (What Dexter noticed)
2. **Context** (Why it might matter)
3. **Optional Action** (User can choose)
4. **Dismiss** (Always available)

**Template:**
```
💡 [Observation Type]

[What I noticed]

[Why this might be relevant]

[Optional action] [Dismiss]
```

**Example:**
```
💡 Recurring Pattern

I noticed you post to "AWS Hosting" monthly around the 5th.

This may indicate a subscription expense.

[Create Template] [Dismiss]
```

---

## Dexter Constraints (Technical)

### No Direct Write Access

- Dexter has **READ-ONLY** access to:
  - Posted journal entries
  - Company chart of accounts
  - Fiscal period status
  - Sandbox entries (isolated)

- Dexter has **NO WRITE** access to:
  - Journal entries
  - Chart modifications
  - Period closing
  - User settings (except Dexter preferences)

---

### No Autonomous Actions

- Dexter CANNOT trigger:
  - Background jobs
  - Auto-posting scripts
  - Period closing workflows
  - Account creation

- All actions require:
  - User click/approval
  - Explicit consent
  - Confirmation step

---

### No Sandbox → Ledger Flow

- Dexter can observe sandbox entries
- Dexter can suggest improvements
- Dexter CANNOT move sandbox → ledger
- User must manually recreate entries

---

## Audit & Accountability

### Dexter Suggestion Logging

All Dexter suggestions must be logged for audit:

**Log Schema:**
```python
class DexterSuggestion(Base):
    __tablename__ = "dexter_suggestions"

    id = Column(UUID, primary_key=True, default=uuid4)
    company_id = Column(UUID, ForeignKey("companies.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)

    suggestion_type = Column(String)  # 'pattern', 'anomaly', 'missing_entry'
    suggestion_text = Column(Text)
    context = Column(JSONB)  # Related data (account codes, amounts, etc.)

    user_action = Column(String)  # 'accepted', 'dismissed', 'ignored'
    created_at = Column(DateTime, default=datetime.utcnow)
    actioned_at = Column(DateTime, nullable=True)
```

**Example Log Entry:**
```json
{
  "id": "uuid",
  "company_id": "company-uuid",
  "user_id": "user-uuid",
  "suggestion_type": "recurring_pattern",
  "suggestion_text": "Create template for AWS Hosting",
  "context": {
    "account_code": "60000",
    "vendor": "AWS",
    "frequency": "monthly",
    "avg_amount": 485
  },
  "user_action": "accepted",
  "created_at": "2025-12-24T20:00:00Z",
  "actioned_at": "2025-12-24T20:05:00Z"
}
```

---

### User Feedback Loop

Users can rate Dexter suggestions:
```
💡 Observation: [Message]

[Accept] [Dismiss] [👍 Helpful] [👎 Not Helpful]
```

Feedback is logged for model improvement.

---

## Dexter Lifecycle

### Phase 1: Passive Observer (Launch)
- Read-only access to data
- Insights panel (optional)
- No proactive notifications

### Phase 2: Interactive Assistant (Future)
- Chat interface
- Natural language queries
- Factual responses only

### Phase 3: Advanced Patterns (Future)
- Multi-company benchmarking (opt-in)
- Industry comparisons (anonymized)
- Still advisory, never authoritative

---

## Success Criteria

Dexter is successful when:

1. ✅ Users find insights helpful (feedback score > 70%)
2. ✅ Zero auto-posted transactions (compliance check)
3. ✅ Users feel in control (survey: "Dexter respects my authority")
4. ✅ Dismissal rate < 50% (suggestions are relevant)
5. ✅ No reported instances of coercion or pressure

---

## Failure Modes & Recovery

### If Dexter Suggests Irreversible Actions

**Detection:**
- User reports coercive messaging
- Internal audit flags suggestion type

**Response:**
1. Immediately disable that suggestion type
2. Review all similar suggestions
3. Update Dexter constraints
4. Notify affected users

---

### If Dexter Auto-Posts (Critical Violation)

**Detection:**
- Journal entry created without user click
- Audit log shows no user action

**Response:**
1. ❌ **EMERGENCY:** Disable Dexter entirely
2. Reverse auto-posted entry (if possible)
3. Investigate root cause
4. Report to canonical authority
5. Do NOT re-enable until fixed and audited

---

## Integration Points (Design Only)

### Frontend
- Insights panel (React component)
- Chat interface (optional)
- Settings page (Dexter preferences)

### Backend
- READ-ONLY API endpoints for Dexter queries
- Suggestion logging service
- User feedback collection

### Database
- `dexter_suggestions` table
- `dexter_user_preferences` table

**No background jobs, no automation, no autonomous actions.**

---

**Authority:** This design conforms to Canon IV (Intelligence as advisory, not authoritative).
**Prepared By:** Aequitas AI Architecture
**Date:** 2025-12-24
**Status:** DESIGN-ONLY (No APIs, No Automation)
