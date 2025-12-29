---
type: decision
date: 2025-12-25
status: implemented
canon: [Canon IV]
phase: P7
---

# DECISION: Dexter Observer Mode (Read-Only Intelligence)

## Context

AI intelligence in an accounting system creates significant risk:
- Accounting truth must be immutable and human-controlled
- AI errors in financial data could create GAAP violations
- Users must trust that AI cannot corrupt ledger integrity
- Intelligence should augment, not replace, human judgment

**Problem**: How should Dexter (AI intelligence) interact with accounting data without risking data integrity?

## Options Considered

### 1. Full Read-Write Access (Rejected)
- Dexter could create/modify journal entries
- **Risk**: AI errors could corrupt ledger
- **Violates**: Canon I (Accounting Truth), Canon IV (Intelligence Guidance)

### 2. Read-Only Observer Mode (CHOSEN)
- Dexter has SELECT-only database permissions
- Provides insights, patterns, anomalies
- Cannot mutate any accounting data
- **Aligns with**: Canon IV ("Intelligence augments, never replaces")

### 3. Approval-Based Mutations (Rejected)
- Dexter suggests changes, user approves
- **Risk**: UX complexity, approval fatigue
- **Decision**: Start with Observer mode, revisit if needed

## Decision

**We chose: Read-Only Observer Mode**

Implementation:
- Database role `dexter_readonly` with SELECT-only permissions (Migration 035)
- `DexterObserverService` enforces read-only session
- All insights carry mandatory disclaimer: "Read-only observations, advisory only"
- Tone enforcement: Advisory language, never commands
- Pattern detection: Anomalies, trends, missing entries, account usage
- UI integration: Dismissible panels in dashboard and onboarding

## Consequences

### Positive
- **Trust**: Users can trust Dexter cannot corrupt data
- **Canon Compliance**: Fully aligned with Canon IV (Intelligence and Guidance)
- **Safety**: Database-level enforcement prevents accidental mutations
- **Transparency**: Clear boundary between observation and action
- **Composability**: Observer insights can inform human decisions without overriding them

### Negative
- **Limited Automation**: Dexter cannot perform actions, only suggest
- **UX Friction**: Users must manually act on insights (no one-click fixes)
- **Future Limitation**: If advanced workflows needed, must revisit architecture

### Mitigations
- Provide clear, actionable insights (not just observations)
- Design UI to make acting on insights easy (e.g., "Create Journal Entry" button with pre-filled values)
- Future: Consider approval-based mutations if user trust established

## Reversal Plan

If read-only mode proves too limiting:

1. **Phased Expansion**:
   - Phase 1: Observer mode (current)
   - Phase 2: Draft-only mutations (Dexter creates drafts, user posts)
   - Phase 3: Approval-based mutations (Dexter proposes, user approves)

2. **Technical Reversal**:
   - Create `dexter_draft_writer` role with INSERT on draft entries only
   - Maintain read-only for posted entries
   - Add approval workflow in UI

3. **Canon Amendment**:
   - If Phase 3 needed, update Canon IV to explicitly allow approved mutations
   - Preserve core principle: Intelligence augments, never replaces

## Canon Check

✅ **Compliant with Canon IV: Intelligence and Guidance**

> "Dexter Observer operates in read-only mode"
> "AI provides advisory intelligence, not commands"
> "Intelligence augments, never replaces, human judgment"

✅ **Preserves Canon I: Accounting Truth**
- Dexter cannot mutate ledger entries
- Accounting truth remains human-controlled
- AI errors cannot corrupt GAAP compliance

✅ **Respects Canon III: Evolution and State**
- Dexter observations do not alter entity state
- Audit trail remains human-action-only

## Implementation Evidence

- **Migration 035**: `create_dexter_readonly_role.py`
- **Service**: `app/services/dexter_observer.py` (read-only session enforcement)
- **API**: `/api/v1/dexter/observer` endpoints
- **UI**: `DexterInsightsPanel.tsx`, `DexterSidebar.tsx`
- **Database**: Read-only role applied to all Dexter queries

## Related Documents

- [[CANON_IV_INTELLIGENCE_AND_GUIDANCE]]
- [[Phase 7 — Intelligence (Dexter)]]
- [[GOAL — Dexter Observer]]
- [[AUDIT — 2025-12-28 Ghost Modules and Headless Systems]]

---

**Decision Status**: ✅ Implemented and operational (verified 2025-12-28)
