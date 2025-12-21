# ONBOARDING CANON

**Status:** AUTHORITATIVE
**Version:** 1.1
**Last Updated:** 2025-12-20
**Maintainer:** Aequitas Product & Engineering Team
**Changelog:**
- v1.1: Added Information Retention & Expansion Rule (§1.3)
- v1.1: Extended Field Classification Matrix with Blocking/Skippable/Enrichment dimensions (§3.2)

---

## 1. Philosophy

### 1.1 Core Principle

> **Onboarding is a deterministic state machine with a narrative layer.**

**Deterministic layer (Wizard Engine):**
- Controls state transitions
- Enforces validation rules
- Manages data persistence
- Never negotiable, never conversational

**Narrative layer (Dexter):**
- Explains context
- Refines user input
- Warns about consequences
- Never authoritative, never commits

### 1.2 The Separation

```
┌─────────────────────────────────────────┐
│   NARRATIVE LAYER (Dexter)              │
│   - Suggests                            │
│   - Corrects form                       │
│   - Explains                            │
│   - Warns                               │
└─────────────────────────────────────────┘
                 ↓ (proposals)
┌─────────────────────────────────────────┐
│   DETERMINISTIC LAYER (Wizard Engine)   │
│   - Validates                           │
│   - Commits                             │
│   - Transitions state                   │
│   - Enforces rules                      │
└─────────────────────────────────────────┘
                 ↓ (truth)
┌─────────────────────────────────────────┐
│   DATABASE (Source of Truth)            │
└─────────────────────────────────────────┘
```

**CRITICAL RULE:**
Logic is **never** conversational.
Conversation is **never** authoritative.

### 1.3 Information Retention & Expansion Rule

> **Onboarding is an information amplification phase, not a filtering phase.**

**CANONICAL PRINCIPLE (Frozen):**

**No information currently collected by onboarding may be removed.**
**Onboarding may only expand, never contract.**

This is the moment where:
- The user is most engaged
- The system can learn the most
- Future automation becomes possible

Therefore:
- **Optional ≠ useless**
- **Skippable ≠ discardable**
- **Accessory ≠ ignorable**

**Classification of onboarding data:**

All data is welcome. Some is required. Some is deferred. Some is enrichment.

**The UX goal is not *less data* — it's *less friction*.**

**Rules:**
- ✅ Fields may be reclassified as **skippable**
- ✅ Fields may be moved to **enrichment** (Dexter conversational collection)
- ✅ Fields may be **deferred** (collected post-activation)
- ❌ Fields may **never** be removed once introduced
- ✅ All collected data is stored, even if unused initially
- ✅ Skipped fields must remain available post-activation

**Dexter's role under this rule:**
- Dexter **never discourages** providing information
- Dexter **never frames optional data as unnecessary**
- Dexter frames enrichment as: *"This helps me prepare better defaults later."*

**Incorrect Dexter phrasing:**
```
❌ "You can skip this if you want." (dismissive)
```

**Correct Dexter phrasing:**
```
✅ "This isn't required, but it helps later."
✅ "This helps me understand your business better."
```

---

## 2. State Machine (Frozen)

### 2.1 Onboarding States

| State | Description | User Can Exit? | Reversible? |
|-------|-------------|----------------|-------------|
| **DRAFT** | Company exists, onboarding not started | ✅ Yes | ✅ Yes |
| **TEMPLATE_SELECTED** | Template chosen, chart not materialized | ✅ Yes | ✅ Yes (re-select) |
| **CHART_READY** | Accounts created from template | ⚠️ With warning | ⚠️ Via reset only |
| **CHART_FINALIZED** | Accounts reviewed, fiscal periods set | ⚠️ With warning | ⚠️ Via reset only |
| **ACTIVE** | Accounting live, onboarding complete | ❌ No | ❌ Never |

### 2.2 State Transition Rules

**CRITICAL INVARIANTS (Database-enforced):**

```
DRAFT → TEMPLATE_SELECTED
  Requires: country, currency, timezone, legal_nature, economic_activity
  Irreversible: No (can re-select)

TEMPLATE_SELECTED → CHART_READY
  Requires: template_id, confirmed=true
  Triggers: Atomic chart materialization
  Irreversible: Yes (chart created)

CHART_READY → CHART_FINALIZED
  Requires: finalized=true
  Irreversible: Yes (accounting structure locked)

CHART_FINALIZED → ACTIVE
  Requires: fiscal_periods created, at least one OPEN period
  Triggers: onboarding_completed_at timestamp
  Irreversible: **Absolutely** (point of no return)
```

### 2.3 Step Progression

| Step | Name | State Transition | Dexter Role |
|------|------|------------------|-------------|
| 0 | Welcome | None | Set expectations |
| 1 | Company Details | → DRAFT (started) | Normalize capitalization |
| 2 | Type & Activity | → (DRAFT continues) | Classify activity |
| 3 | Template Selection | → TEMPLATE_SELECTED | Warn about lock |
| 4 | Modules | → (stays TEMPLATE_SELECTED) | Suggest based on activity |
| 5 | Organization Scope | → (stays TEMPLATE_SELECTED) | Explain consolidation |
| 6 | Chart Materialization | → CHART_READY | Silent (system operation) |
| 7 | Account Review | → CHART_FINALIZED | Validate custom accounts |
| 8 | Fiscal Periods | → (stays CHART_FINALIZED) | Validate dates |
| 9 | Activation | → ACTIVE | Final warning |

---

## 3. Field Classification Matrix

### 3.1 Field Mutability Levels

| Level | Description | Example Fields | Can Change After Step |
|-------|-------------|----------------|---------------------|
| **EDITABLE** | Always modifiable | `trade_name`, `email`, `phone` | Always (unless ACTIVE) |
| **STRUCTURAL** | Locked after step N | `country`, `currency` | Before template selection |
| **IRREVERSIBLE** | Locked after first use | `template_id`, `chart structure` | Never after materialization |
| **ACCOUNTING-CRITICAL** | Immutable after activation | `fiscal_year_start`, `base_currency` | Never after ACTIVE |

### 3.2 Per-Field Classification (Extended)

**Matrix dimensions:**
- **Type:** EDITABLE / STRUCTURAL / IRREVERSIBLE / ACCOUNTING-CRITICAL
- **Blocking:** Is this field required to proceed?
- **Skippable:** Can user skip without blocking progress?
- **Enrichment:** Is this collected conversationally for future intelligence?

| Field | Type | Blocking | Skippable | Enrichment | Lock Point | Dexter Must Warn? | Rationale |
|-------|------|----------|-----------|------------|------------|-------------------|-----------|
| **name** | STRUCTURAL | Yes | No | No | After ACTIVE | No | Legal name change requires audit |
| **trade_name** | EDITABLE | No | Yes | No | Never | No | DBA can change anytime |
| **country** | STRUCTURAL | Yes | No | No | After template selection | Yes | Affects GAAP/IFRS rules |
| **currency** | STRUCTURAL | Yes | No | No | After template selection | Yes | Affects chart structure |
| **timezone** | EDITABLE | Yes | No | No | Never | No | Display preference only |
| **legal_nature** | STRUCTURAL | No | Yes | Yes | After template selection | No | Used for template recommendation |
| **economic_activity** | STRUCTURAL | No | Yes | Yes | After template selection | No | Used for module suggestions |
| **email** | EDITABLE | No | Yes | No | Never | No | Contact information |
| **phone** | EDITABLE | No | Yes | No | Never | No | Contact information |
| **template_id** | IRREVERSIBLE | Yes | No | No | After materialization | **Yes** | Cannot change chart structure |
| **is_standalone** | ACCOUNTING-CRITICAL | No | Yes | Yes | After ACTIVE | Yes | Affects consolidation |
| **fiscal_year_start** | ACCOUNTING-CRITICAL | Yes | No | No | After ACTIVE | Yes | Affects period structure |
| **companies_managed_count** | ENRICHMENT | No | Yes | Yes | Never | No | Future intelligence (consolidation planning) |
| **current_consolidation_method** | ENRICHMENT | No | Yes | Yes | Never | No | Future intelligence (workflow design) |

**Legend:**
- **Blocking = Yes:** User cannot proceed without providing this field
- **Skippable = Yes:** User can skip and continue (may be soft-nudged by Dexter)
- **Enrichment = Yes:** Field primarily collected for future automation and intelligence

**Classification rules:**
1. **REQUIRED (Blocking):** `Blocking=Yes, Skippable=No` → Cannot proceed without this
2. **STRONGLY RECOMMENDED:** `Blocking=No, Skippable=Yes, Enrichment=Yes` → Dexter soft-nudges
3. **OPTIONAL:** `Blocking=No, Skippable=Yes, Enrichment=No` → Fully silent skip
4. **ENRICHMENT-ONLY:** `Blocking=No, Skippable=Yes, Enrichment=Yes` → Dexter conversational collection

### 3.3 Lock Enforcement

**Backend enforcement:**
```python
if company.onboarding_status == OnboardingStatus.ACTIVE:
    if field in ACCOUNTING_CRITICAL_FIELDS:
        raise ValidationError(f"{field} cannot be changed after activation.")

if company.onboarding_current_step >= 3:  # Template selected
    if field in STRUCTURAL_FIELDS:
        raise ValidationError(f"{field} cannot be changed after template selection.")
```

**Dexter enforcement:**
```
Before user submits:
  If field is STRUCTURAL and lock point passed:
    Show: "This field is locked. To change it, restart onboarding."

  If field is IRREVERSIBLE and approaching lock:
    Show: "This cannot be changed after the next step."
```

---

## 4. Dexter Integration Points

### 4.1 Step-by-Step Dexter Behavior

#### **Step 0: Welcome**
**Dexter appears:** Once, then silent.

**Script:**
```
"I'll stay with you while this is set up.
Nothing becomes final until the end."
```

**Rules:**
- No follow-up unless user asks
- Set expectation: reversible until activation

---

#### **Step 1: Company Details**

**System prompt:**
```
"What is the company's legal name?"
```

**Dexter intervention (only if user pauses or hesitates):**
```
"This should match official registrations."
```

**After user input: `acme holdings llc`**

**Dexter preprocessing:**
```
User input: "acme holdings llc"
Dexter suggests: "Acme Holdings LLC"
Confidence: 0.95

Dexter displays:
"I've standardized the capitalization to Acme Holdings LLC for consistency."
"Does this reflect the legal name?"

Buttons: [Confirm] [Edit]
```

**If user edits manually:**
Dexter remains silent.

---

#### **Step 2: Type & Activity**

**System prompt:**
```
"What does the company primarily do?"
```

**If user types natural language:**
```
User: "We develop real estate properties"

Dexter waits, then:
"I would classify this as Real Estate Development."
"Proceed with this classification?"

Buttons: [Yes] [Adjust]
```

**No explanation unless user asks why.**

---

#### **Step 3: Template Selection**

**System prompt:**
```
"Choose an accounting structure."
```

**Dexter (before user selects):**
```
"This defines account naming, codes, and hierarchy."
(Pause)
"It becomes difficult to change after activation."
```

**After user selects, before confirmation:**
```
"This choice affects how transactions are recorded."
"Confirm template: US-GAAP Standard?"

Buttons: [Confirm] [Go Back]
```

**This is one of the few steps where Dexter MUST warn.**

---

#### **Step 4: Modules**

**System prompt:**
```
"Select additional modules."
```

**Dexter (after user selection):**
```
"Accounting is always active."
```

**If Dexter suggests modules based on activity:**
```
"Based on your activity, these modules usually apply."
(No insistence. No urgency.)
```

---

#### **Step 5: Organization Scope**

**System prompt:**
```
"Is this company standalone or part of a group?"
```

**Dexter:**
```
"This affects future consolidation."
(Silence.)
```

---

#### **Step 6: Chart Materialization (System-Controlled)**

**Dexter:** Silent.

**System shows progress:**
```
Creating accounts... 15/338
```

**On completion:**
```
"Chart created successfully. You can now review accounts."
```

**Dexter does not narrate. Cats don't announce walking.**

---

#### **Step 7: Account Review**

**System prompt:**
```
"Review and customize your accounts."
```

**Dexter (only if user attempts invalid action):**
```
User tries to disable mandatory account:
"This account is required by the template and cannot be disabled."
```

**Dexter stays silent for valid customizations.**

---

#### **Step 8: Fiscal Periods**

**System prompt:**
```
"Define your fiscal periods."
```

**Dexter (only if user creates overlapping periods):**
```
"Fiscal periods cannot overlap. Adjust the dates."
```

**Dexter stays silent for valid period definitions.**

---

#### **Step 9: Activation**

**System prompt:**
```
"Review your configuration."
```

**Dexter (final intervention):**
```
"After activation, the accounting structure is locked."
(Pause)
"Descriptive details remain editable."
```

**On activation button click:**
```
"This creates the accounting backbone."
(Then silence.)
```

---

### 4.2 Global Correction & Enforcement Phrases

**These are reusable and always phrased the same:**

| Situation | Canonical Phrase |
|-----------|-----------------|
| **Capitalization** | "I standardize capitalization for consistency." |
| **Ambiguity** | "I'm not fully confident about this classification." |
| **Irreversible choice** | "This affects core accounting behavior." |
| **Naming conflict** | "This name already exists elsewhere. Internal identifiers will remain unique." |

**No variations. Consistency builds trust.**

---

## 5. Session Management

### 5.1 Session Locking

**Purpose:** Prevent concurrent editing of onboarding.

**Rules:**
- One active session per company at a time
- Lock expires after 30 minutes of inactivity
- Lock released on completion or explicit exit

**UX:**
```
Session A: Currently editing
Session B attempts to enter wizard:

  "Another session is currently completing onboarding for this company.
   Wait for them to finish or contact your administrator."
```

### 5.2 Resume Functionality

**Auto-save after each step:**
```
company.onboarding_current_step = N
company.onboarding_status = STATE
db.commit()
```

**On resume:**
```
Wizard loads at step N
Dexter: (Silent — no "Welcome back!" messages)
```

### 5.3 Abandonment Handling

**If user exits mid-wizard:**
- Progress saved automatically
- Dashboard shows banner:
  ```
  "Finish setting up accounting for [Company Name]"
  [Resume Setup]
  ```

**No nagging. No urgency. Just availability.**

---

## 6. Error Handling Standards

### 6.1 Error Message Philosophy

All errors must be:
- **Human-readable** (no error codes shown to user)
- **Actionable** (tell user what to do next)
- **Non-technical** (no database or API terms)

### 6.2 Error Message Examples

**Bad:**
```
"ONBOARDING_STATUS_INVALID"
```

**Good:**
```
"This step cannot be completed because [specific reason].
Please [specific action]."
```

**Bad:**
```
"Constraint violation on fiscal_periods.date_range"
```

**Good:**
```
"Fiscal periods cannot overlap.
Adjust the end date of Period 1 or the start date of Period 2."
```

### 6.3 Dexter's Role in Errors

**Dexter does NOT:**
- Show stack traces
- Apologize excessively
- Blame the system

**Dexter DOES:**
- Explain the rule that was violated
- Suggest a fix
- Maintain calm tone

**Example:**
```
User tries to activate without fiscal periods:

"At least one fiscal period must be defined before activation.
Return to Step 8 to create periods."
```

---

## 7. Audit Trail Requirements

### 7.1 Onboarding Corrections Log

**Table:** `onboarding_corrections`

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID | Primary key |
| `company_id` | UUID (FK) | Company being onboarded |
| `step` | INTEGER | Step number where correction occurred |
| `field_name` | VARCHAR | Field being corrected |
| `user_input` | TEXT | Original user input |
| `dexter_suggestion` | TEXT | Dexter's suggested value |
| `user_accepted` | BOOLEAN | Did user accept Dexter's suggestion? |
| `final_value` | TEXT | Final committed value |
| `correction_type` | VARCHAR | Type: capitalization, classification, etc. |
| `created_at` | TIMESTAMP | When correction occurred |

**Purpose:**
- Audit trail for all Dexter interventions
- Training data for improving suggestions
- Accountability for normalization decisions

**Privacy rule:**
- User input is preserved verbatim
- No silent modifications without audit entry

---

## 8. Testing Requirements

### 8.1 State Machine Tests

**Must verify:**
- ✅ State transitions are irreversible where specified
- ✅ Backend rejects invalid state transitions
- ✅ Locked fields cannot be modified
- ✅ Activation requires all prerequisites

### 8.2 Dexter Behavior Tests

**Must verify:**
- ✅ Dexter suggests normalization for capitalization
- ✅ Dexter warns before irreversible steps
- ✅ Dexter stays silent when no value added
- ✅ Dexter never commits without confirmation
- ✅ All corrections logged in audit trail

### 8.3 Edge Case Tests

**Must handle:**
- Network failure mid-materialization (rollback + retry)
- Browser close mid-wizard (resume from saved state)
- Concurrent session attempt (lock enforcement)
- Permission revoked mid-wizard (graceful freeze)

---

## 9. Handoff to Phase 6

### 9.1 Post-Activation State

**When `onboarding_status = ACTIVE`:**
- Wizard becomes **read-only**
- Dashboard access **enabled**
- Accounting rules **enforced**
- Immutability constraints **active**

### 9.2 What Changes

| Before ACTIVE | After ACTIVE |
|--------------|--------------|
| Chart can be re-materialized | Chart structure locked |
| Accounts can be deleted | Accounts lock after first transaction |
| Periods can be deleted | Periods lock after entries posted |
| Template can be changed (via reset) | Template immutable |

### 9.3 Reset (Destructive Operation)

**Only available before ACTIVE:**
```
POST /api/v1/onboarding/{company_id}/reset

Deletes:
- All company accounts
- All fiscal periods
- Template usage records

Resets:
- onboarding_status → DRAFT
- onboarding_current_step → 0
```

**After ACTIVE:**
Reset is **not allowed**. Company must be archived and recreated.

---

## 10. Canonical Acceptance Criteria

Onboarding is **complete and canonical** when:

- ✅ State machine transitions are deterministic and enforced
- ✅ Dexter interventions are logged and auditable
- ✅ All fields have defined mutability levels
- ✅ Irreversible steps have explicit warnings
- ✅ Users cannot violate accounting rules via UI
- ✅ Abandonment and resume work reliably
- ✅ Activation results in ACTIVE state with valid chart + periods
- ✅ Error messages are human-readable and actionable
- ✅ Session locking prevents concurrent edits
- ✅ Dexter never commits data without confirmation

---

## 11. Governance

### 11.1 Canon Authority

This document is **AUTHORITATIVE** and binds:
- Backend onboarding service implementation
- Frontend wizard UI components
- Dexter onboarding prompt templates
- Database schema (onboarding fields + audit tables)

### 11.2 Modification Process

To modify onboarding behavior:
1. **Propose change** with justification
2. **Review against state machine** — does it preserve determinism?
3. **Update this document** with version increment
4. **Implement in code** to match updated canon
5. **Update tests** to verify new behavior

### 11.3 What Cannot Be Modified

**Frozen elements:**
- ❌ State machine structure (DRAFT → TEMPLATE_SELECTED → CHART_READY → CHART_FINALIZED → ACTIVE)
- ❌ Irreversibility of activation
- ❌ Separation of narrative and deterministic layers
- ❌ Requirement for audit trail

**Modifiable elements:**
- ✅ Dexter scripts per step (additive improvements)
- ✅ Field classification (with justification)
- ✅ Error message phrasing
- ✅ UI/UX polish (within canonical bounds)

---

## Final Note

Onboarding is not a feature. It is the **foundation of accounting integrity**.

When done right, users won't remember filling forms.
They'll remember that **the system understood them**.

Dexter is the guide. The wizard is the law. The database is the truth.

**Always in that order.**

---

**End of Onboarding Canon v1.0**
