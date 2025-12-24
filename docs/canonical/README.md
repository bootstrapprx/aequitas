# Aequitas Canon — The Constitutional Core

> *"Code must conform to contracts, not vice-versa."*

## 🏛️ Purpose and Authority

This directory (`/docs/canonical`) contains the **Supreme Law** of the Aequitas system. Unlike standard technical documentation which describes *how* the system works, the Canon describes *what* the system is allowed to be.

**These documents are authoritative.**
If the implementation conflicts with the Canon, the implementation is **buggy by definition**, regardless of whether it "works" or not.

## 📜 The Four Canons

 The constitutional core is divided into four immutable pillars:

### [I. Accounting Truth & Structure](./CANON_I_ACCOUNTING_TRUTH.md)
*Governs: What is real.*
*   **Concept Over Fact:** The specific (users, banks) must never pollute the generic (master chart).
*   **Double-Entry:** Invariants are partially enforced by physics, fully enforced by code.
*   **The Master Chart:** A single, versioned, immutable source of financial truth.

### [II. Authority, Boundaries & Power](./CANON_II_AUTHORITY_AND_POWER.md)
*Governs: Who may act.*
*   **Backend Supremacy:** The UI is a view, not an authority.
*   **API as Law:** Contracts are binding treaties between the frontend and backend.
*   **No "God Mode":** Even admins cannot violate accounting truth (see Canon III).

### [III. Evolution, State & Time](./CANON_III_EVOLUTION_AND_STATE.md)
*Governs: How things change.*
*   **Points of No Return:** Activation is irreversible.
*   **Immutable History:** The past is read-only. We append corrections; we never rewrite.
*   **Guided Onboarding:** State machines prevent invalid partial existences.

### [IV. Intelligence, Guidance & Human Protection](./CANON_IV_INTELLIGENCE_AND_GUIDANCE.md)
*Governs: The role of AI.*
*   **Dexter as Observer:** AI suggests, humans decide.
*   **No Hallucinated Debt:** AI cannot create obligations or alter the ledger autonomously.
*   **Conscious Choice:** The system must never use coercive defaults to trap users.

## 🌉 Relationship to Implementation

The code in `backend/` and `frontend/` is the **Executive Branch**. It executes the will of the Canon.
This directory is the **Judicial Branch**. It interprets the laws that the code must follow.

### Compliance Audits
System audits (like the one performed by Antigravity) are measured against these documents.
- ✅ **Compliant:** The code matches the law.
- 🔴 **Non-Compliant:** The code breaks a fundamental accounting or authority rule.
- 🟡 **Fragile:** The code relies on implicit behavior where explicit law is required.

---
*For technical implementation details, see the main [README.md](../../README.md).*
