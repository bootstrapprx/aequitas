---
type: audit
date: 2025-12-28
risk: Medium
auditor: Governance Reconciliation
scope: Module enumeration vs implementation status
---

# AUDIT: Ghost Modules and Headless Systems

## Scope
Audit of all modules defined in `ModuleType` enum versus actual backend and frontend implementation status.

## Findings

### 1. Ghost Modules (Enum-Only, No Implementation)

The following modules are **defined in code** but have **no models, services, or API endpoints**:

| Module | Backend Status | Frontend Status | User Impact |
|--------|----------------|-----------------|-------------|
| **INVOICING** | 🔴 Enum only | 🔴 Missing | Module selector shows option, but no functionality |
| **PAYROLL** | 🔴 Enum only | 🔴 Missing | Module selector shows option, but no functionality |
| **INVENTORY** | 🔴 Enum only | 🔴 Missing | Not exposed in UI |
| **CONTRACTS** | 🔴 Enum only | 🔴 Missing | Not exposed in UI |

**User Experience Impact**:
- Users can select INVOICING or PAYROLL during onboarding (Step 4: Module Selection)
- Selection is stored in `CompanyModule` table
- No functionality exists after selection
- This creates a **false promise** in the onboarding flow

### 2. Headless Systems (Backend Operational, No UI)

The following systems are **fully functional in backend** but have **no user-facing interface**:

| System | Backend Status | Frontend Status | User Impact |
|--------|----------------|-----------------|-------------|
| **Sandbox Engine** | ✅ Operational | 🔴 No dashboard | Mentioned in post-activation guidance, not accessible |
| **Fiscal Engine (Tax)** | ✅ Operational | 🔴 No dashboard | Tax calculations API functional, no UI |

**User Experience Impact**:
- Post-activation guidance mentions "Explore Sandbox scenarios" but no UI exists
- Tax calculation capabilities exist but are inaccessible to users
- Backend engineers can use API directly, but end-users cannot

### 3. Partial Module (Assets)

| Module | Backend Status | Frontend Status | User Impact |
|--------|----------------|-----------------|-------------|
| **ASSETS** | 🟡 Partial | 🟡 Partial | Asset accounts exist, no depreciation or lifecycle tracking |

**Implementation Details**:
- Asset account types exist in Chart of Accounts
- Asset section appears in Balance Sheet
- No dedicated asset tracking, depreciation schedules, or lifecycle management
- No fixed asset register

## Evidence

### Module Enum Definition
- File: `backend/app/models/company_module.py`
- Enum values: ACCOUNTING, FISCAL, INVOICING, CONTRACTS, INVENTORY, PAYROLL

### Onboarding Module Selection
- File: `frontend/src/pages/Onboarding/steps/ModuleSelectionStep.tsx`
- Users presented with ACCOUNTING, INVOICING, PAYROLL options
- Selection stored but no post-activation functionality

### Sandbox Backend
- API: `/api/v1/sandbox` (fully functional)
- Service: `SandboxService`
- Models: `Scenario`, `Projection`, `Binding`
- Schema: Isolated sandbox schema (Migration 033-034)

### Fiscal Engine Backend
- API: `/api/v1/fiscal` (fully functional)
- Services: `ProfileService`, `CalculationService`, `ConsolidationService`
- Models: `TaxRun`, `TaxFact`, `TaxPosition`

## Risk

**Medium**

### User Trust Risk
- Ghost modules create false expectations during onboarding
- Users may select modules expecting functionality
- No clear indication that modules are "Coming Soon"

### Technical Debt Risk
- Headless systems represent investment without user value realization
- API contracts exist but may drift without UI to exercise them

### Documentation Risk
- Governance documents previously understated implementation status
- Phase 7 marked "planned" when Dexter Observer and Fiscal Engine were operational

## Recommendations

### Immediate Actions (UX Truth)

1. **Module Selection Honesty**:
   - Add "(Coming Soon)" suffix to INVOICING and PAYROLL in module selector
   - Add tooltip: "Module framework ready, operational features planned"
   - OR: Remove from onboarding selector until implemented

2. **Post-Activation Guidance**:
   - Remove "Explore Sandbox scenarios" link until UI exists
   - OR: Replace with "Sandbox API available (UI coming soon)"

3. **Documentation Clarity**:
   - Update any user-facing docs to reflect current module status
   - Clearly distinguish between "module framework" and "operational module"

### Future Actions (Implementation)

4. **Sandbox UI** (High Priority):
   - Backend fully functional, highest ROI for frontend development
   - See [[GOAL — Sandbox UI]]

5. **Fiscal Engine UI** (Medium Priority):
   - Tax calculation capabilities exist, need dashboard for user access
   - Tax report visualization needed

6. **Operational Modules** (Long-term):
   - INVOICING: See [[GOAL — Invoicing Module]]
   - PAYROLL: See [[GOAL — Payroll Module]]
   - ASSETS: See [[GOAL — Assets Module]]

## Next Actions

- [ ] Update module selector UI to show "Coming Soon" for unimplemented modules
- [ ] Audit post-activation guidance for references to inaccessible features
- [ ] Create [[DECISION — Module Roadmap Communication]] for user-facing honesty policy
- [ ] Prioritize Sandbox UI implementation (backend proven, high user value)
- [ ] Create [[GOAL — Fiscal Engine UI]] for tax dashboard

## Related Documents

- [[Phase 6 — Operational Modules]]
- [[Phase 7 — Intelligence (Dexter)]]
- [[GOAL — Sandbox UI]]
- [[GOAL — Invoicing Module]]
- [[GOAL — Assets Module]]
- [[GOAL — Payroll Module]]

---

**Audit Conclusion**: The system has significant implementation depth (backend functional for Sandbox and Fiscal), but UX does not reflect this truth. Ghost modules create false expectations. Recommend immediate UX honesty updates and prioritized Sandbox UI development.
