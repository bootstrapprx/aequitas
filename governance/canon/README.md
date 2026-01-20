# Aequitas Constitution

This directory contains the **canonical constitutional documents** of the Aequitas system.

## Purpose

The Constitution is versioned with Governance by design. This enables:

- **Full System Replication**: Possession of this folder provides complete architectural intent
- **Historical Context**: Constitutional changes are tracked alongside implementation phases
- **AI Agent Context**: Agents can read Canon to understand system principles
- **Separation of Concerns**: Constitutional truth is separated from application code

## Structure

```
canon/
├── CANON_I_ACCOUNTING_TRUTH.md          # Double-entry bookkeeping, GAAP
├── CANON_II_AUTHORITY_AND_POWER.md      # Permissions, roles, data ownership
├── CANON_III_EVOLUTION_AND_STATE.md     # Immutability, audit trails
├── CANON_IV_INTELLIGENCE_AND_GUIDANCE.md # Dexter, Observer mode, disclaimers
├── kernels/                              # Versioned implementation kernels
│   └── kernel_2025.2.md                  # Current kernel specification
└── protocols/                            # Operational protocols (future)
```

## Canon Overview

### Canon I: Accounting Truth
- Double-entry bookkeeping is inviolable
- Debits must equal credits
- Fiscal periods enforce temporal boundaries
- Posted entries are immutable

### Canon II: Authority and Power
- Company data ownership
- User permissions and roles
- Multi-tenancy separation
- Superuser constraints

### Canon III: Evolution and State
- State machines govern entity lifecycles
- Audit trails preserve history
- Immutability after posting
- Remediation over deletion

### Canon IV: Intelligence and Guidance
- Dexter Observer operates in read-only mode
- AI provides advisory intelligence, not commands
- Disclaimers are mandatory for projections
- Intelligence augments, never replaces, human judgment

## Usage

### For AI Agents
When working on Aequitas:
1. Read Canon to understand system principles
2. Check Kernel for current implementation rules
3. Respect constitutional boundaries in all changes
4. Never mutate Canon without explicit user authorization

### For Developers
- Canon defines **what must be true**
- Kernel defines **how to make it true**
- Application code implements Kernel specifications
- Violations of Canon are architectural defects

## Versioning

Canon documents are **rarely changed**. When they are:
- Changes are additive (new sections) or clarifying (reworded principles)
- Breaking changes require new Canon versions (e.g., CANON_I_v2.md)
- Kernel versions track implementation epochs (e.g., kernel_2025.2.md)

## Security Note

This is **security-by-separation**, not security-by-obscurity.

The Constitution is intentionally versioned and readable because:
- Transparency enables trust
- Replication enables disaster recovery
- Historical context enables debugging
- AI agents require constitutional awareness

The Constitution contains **no secrets**, only **principles and rules**.

---

*Last Updated: 2025-12-28*
*Governance Version: Phase 7 (Intelligence)*
