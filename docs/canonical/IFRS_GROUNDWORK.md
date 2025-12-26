# IFRS Groundwork (Preparation Only)

## 1️⃣ Problem Statement
- Aequitas cannot support IFRS today because the regulatory mapping layer does not exist and the presentation/reporting engine only understands the US GAAP canonical structure.
- Prior dot-notation account experiments failed because they attempted to replace canonical 5-digit GAAP codes with non-canonical keys, creating divergence and validation gaps.
- Maintaining “separate charts per standard” is incorrect; it creates data duplication, drift, and broken reconciliation.
- **IFRS is not a different chart of accounts; it is a different regulatory interpretation of the same economic concepts.**

## 2️⃣ What Is Missing

### A) Regulatory Mapping Layer
- A dedicated `regulatory_mapping` table is required to hold per-standard metadata.
- Each row must map `master_account_id` → `IFRS_code` (or other standards) and support:
  - One-to-many mappings (one master account can map to multiple IFRS presentations).
  - Many-to-one mappings (several master accounts can roll up to one IFRS presentation code).
- No mappings exist today; therefore IFRS cannot be expressed without inventing non-canonical codes.

### B) Presentation Layer Differences
- IFRS differences are primarily presentation and disclosure:
  - OCI routing vs retained earnings handling.
  - Equity presentation (e.g., share premium, reserves) differs in grouping, not in economic truth.
  - Disclosure granularity differs at report/output level, not at base account level.
- These differences require a presentation model, not a new chart.

### C) Reporting Translation (Not Data Duplication)
- The ledger and postings remain the same; only reporting views change.
- No dual-posting and no parallel ledgers are needed; translation happens at reporting time using mappings.
- Reports must consume master accounts + regulatory mapping to render IFRS statements; until that exists, IFRS output is not possible.
- Regulatory mapping must never affect journal validation, period closing, or balance enforcement

## 3️⃣ Canon-Safe Future Model (Conceptual)
```
MasterAccount (canonical, GAAP-based)
        |
        +-- RegulatoryMapping
              - standard: 'IFRS'
              - external_code: '1.10.10.10'
              - presentation_group
```
- MasterAccount remains the single canonical source of accounting truth.
- Regulatory codes are metadata layered on top; they do not replace 5-digit GAAP codes.
- Accounting truth is never duplicated; only interpretive metadata is added.

## 4️⃣ Activation Rules (Hard Guardrails)
- Kernel Freeze exists (no mutable kernels during rollout).
- Regulatory mapping coverage ≥ 95% of active master accounts.
- Reporting layer supports alternate presentation (IFRS views) without changing ledger data.
- Onboarding validation updated to require IFRS mappings before offering the template.
- Until all are true: **IFRS remains intentionally disabled.**

## 5️⃣ Anti-Patterns (Do Not Do)
- Do not create a separate IFRS master chart.
- Do not use dot-notation as the primary key.
- Do not maintain dual journals or parallel ledgers.
- Do not auto-convert historical data.

## 6️⃣ Status Declaration
IFRS Status: NOT IMPLEMENTED  
This document defines prerequisites only.  
No code path enables IFRS at this time.
Any attempt to enable IFRS without satisfying Section 4 is a canon violation