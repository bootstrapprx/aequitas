# Kernel 2025.2 Implementation Index

**Status:** Design Complete
**Date:** 2025-12-24
**Authority:** All documents conform to Kernel 2025.2 (frozen, immutable)

---

## Overview

This index provides links to all four implementation tracks for Kernel 2025.2.

All documents are **design-only** and require review and approval before implementation.

---

## Implementation Tracks

### Track 1: Master Chart Reseed Plan
**File:** [MASTER_CHART_RESEED_PLAN.md](./MASTER_CHART_RESEED_PLAN.md)

**Purpose:** Bring the database Master Chart into conformity with Kernel 2025.2

**Contents:**
- Current state assessment (database vs kernel mismatch)
- Three reseed strategies (fresh, additive, dual-track)
- Migration safety rules
- Verification checklist

**Status:** ✅ Design Complete — Awaiting Strategy Selection

---

### Track 2: Existing Company Remediation
**File:** [EXISTING_COMPANY_REMEDIATION.md](./EXISTING_COMPANY_REMEDIATION.md)

**Purpose:** Fix companies onboarded under incomplete templates

**Contents:**
- Detection logic (identify non-compliant companies)
- Two remediation paths (auto-add vs guided wizard)
- Forbidden operations (explicit prohibitions)
- Audit guarantees (history preservation)

**Status:** ✅ Design Complete — Depends on Track 1

---

### Track 3: Post-Activation UX
**File:** [POST_ACTIVATION_UX.md](./POST_ACTIVATION_UX.md)

**Purpose:** Define first-day user experience and system boundaries

**Contents:**
- Dashboard copy (protected structure, available actions)
- System boundaries (explicit non-actions)
- Tone & voice guidelines
- Mobile adaptation

**Status:** ✅ Design Complete — Ready for Frontend Implementation

---

### Track 4: Dexter Observer Mode
**File:** [DEXTER_OBSERVER_MODE.md](./DEXTER_OBSERVER_MODE.md)

**Purpose:** Reintroduce Dexter as non-authoritative observer

**Contents:**
- What Dexter may/may not do
- Tone & positioning (advisory, optional, never urgent)
- Example messages (approved + forbidden)
- Interaction modes (passive, interactive, disabled)

**Status:** ✅ Design Complete — Ready for Backend Implementation

---

## Canonical Compliance

All four tracks conform to:
- ✅ **Canon I** (Accounting Truth) — Zone boundaries preserved
- ✅ **Canon II** (Authority and Power) — Human authority maintained
- ✅ **Canon III** (Evolution and State) — History immutable, changes additive
- ✅ **Canon IV** (Intelligence and Guidance) — Dexter is advisory only

**Global Prohibitions Respected:**
- ❌ No kernel modifications
- ❌ No new accounting concepts
- ❌ No IFRS enablement
- ❌ No automation bypassing human intent
- ❌ No shortcuts weakening auditability

---

## Dependencies

```
Kernel 2025.2 (FROZEN)
    ↓
Track 1: Master Chart Reseed
    ↓
Track 2: Existing Company Remediation

(Parallel, independent of Track 1 & 2:)
Track 3: Post-Activation UX
Track 4: Dexter Observer Mode
```

---

## Implementation Sequence

### Phase 1: Review & Approval
- [ ] Canonical authority reviews all four documents
- [ ] Select reseed strategy (Track 1: A/B/C)
- [ ] Select remediation path (Track 2: A/B)
- [ ] Approve UX copy (Track 3)
- [ ] Approve Dexter constraints (Track 4)

### Phase 2: Database Operations (Sequential)
- [ ] **Track 1:** Execute Master Chart Reseed (2-4 hours)
- [ ] **Track 2:** Execute Company Remediation (4-6 hours)
- [ ] Verify kernel compliance audit passes

### Phase 3: Frontend & AI (Parallel)
- [ ] **Track 3:** Implement Post-Activation UX (6-8 hours)
- [ ] **Track 4:** Implement Dexter Observer Mode (8-12 hours)

**Total Estimated Time:** 20-30 hours

---

## Success Criteria

Implementation is successful when:

1. ✅ All companies have L0 kernel (20 accounts)
2. ✅ System accounts (`32000`, `39999`) present
3. ✅ Fiscal period closing enabled
4. ✅ Users understand system boundaries (UX clarity)
5. ✅ Dexter provides insights without coercion
6. ✅ Kernel compliance audit passes

---

## Related Documents

### Kernel Freeze Artifacts
- [kernel_2025.2.json](./kernels/kernel_2025.2.json) — Authoritative definition
- [kernel_2025.2.md](./kernels/kernel_2025.2.md) — Human-readable documentation
- [kernel_2025.2.checksum](./kernels/kernel_2025.2.checksum) — Integrity hash
- [Kernels README](./kernels/README.md) — Directory guide

### Canonical Documents
- [Canon I: Accounting Truth](./CANON_I_ACCOUNTING_TRUTH.md)
- [Canon II: Authority and Power](./CANON_II_AUTHORITY_AND_POWER.md)
- [Canon III: Evolution and State](./CANON_III_EVOLUTION_AND_STATE.md)
- [Canon IV: Intelligence and Guidance](./CANON_IV_INTELLIGENCE_AND_GUIDANCE.md)

### Audit & History
- [Template Audit Report](../TEMPLATE_AUDIT_REPORT.md) — Problem statement
- [Data Dictionary](./DATA_DICTIONARY.md) — Schema reference

---

## Contact & Escalation

**For Questions:**
- Review canonical documents first
- Check this index for relevant design doc
- Escalate to canonical authority if conflict arises

**For Conflicts:**
- Kernel 2025.2 is authoritative (never modify)
- Database/templates must conform to kernel
- Design docs can be updated (with approval)

---

**Last Updated:** 2025-12-24
**Maintained By:** Aequitas Systems Architecture
**Status:** Design Complete — Ready for Implementation
