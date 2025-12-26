# Kernel Freeze Archive

This directory contains **frozen kernel definitions** for the Aequitas accounting system.

---

## What is a Kernel?

A **kernel** is an immutable, versioned set of accounts that guarantees structural completeness for accounting operations.

Think of a kernel as the "minimal operating system" for a company's chart of accounts. Just as an OS kernel provides essential system calls, an accounting kernel provides essential account structures.

**Key Properties:**
- **Immutable** — Once frozen, never modified
- **Versioned** — Each kernel has a unique version identifier
- **Complete** — Satisfies the accounting equation and supports all core operations
- **Universal** — Contains no company-specific or factual accounts

---

## Why Freeze Kernels?

Freezing kernels provides:

1. **Audit Trail** — Prove what kernel was used during onboarding
2. **Drift Detection** — Verify kernel definitions haven't been altered
3. **Version Control** — Track kernel evolution over time
4. **Compliance** — Demonstrate GAAP/IFRS adherence at the kernel level
5. **Debugging** — Understand historical onboarding behavior

**Without frozen kernels:** You cannot prove what accounts were seeded, when, or why.

**With frozen kernels:** Every onboarding is traceable, auditable, and reproducible.

---

## Directory Structure

```
kernels/
├── README.md                      # This file
├── kernel_2025.2.json             # Authoritative kernel definition (machine-readable)
├── kernel_2025.2.md               # Human-readable documentation
├── kernel_2025.2.checksum         # SHA-256 integrity checksum
└── (future kernel versions...)
```

Each kernel version consists of **three files**:

1. **`.json`** — Authoritative data structure (accounts, metadata, guarantees)
2. **`.md`** — Human-readable explanation (purpose, guarantees, usage)
3. **`.checksum`** — Integrity hash for drift detection

---

## How to Read Kernel Files

### 1. JSON Structure

The `.json` file contains:

#### A) Metadata
```json
{
  "metadata": {
    "kernel_version": "2025.2",
    "status": "FROZEN",
    "effective_from": "2025-12-24",
    "gaap_basis": "US_GAAP",
    "supports_ifrs": false,
    "notes": "..."
  }
}
```

#### B) Kernel Layers
Each kernel defines three layers:

- **L0** (Universal Kernel) — Mandatory 20 accounts required for all companies
- **L1** (Standard Kernel) — Full GAAP chart (~130-150 accounts)
- **L2** (Simplified Kernel) — Collapsed chart (~40-60 accounts)

```json
{
  "kernels": {
    "L0": {
      "name": "Universal Kernel",
      "accounts": [
        {
          "layer": "L0",
          "master_account_id": "uuid",
          "code": "32000",
          "name": "Retained Earnings",
          "category": "EQUITY",
          "required": true
        }
      ]
    }
  }
}
```

#### C) Counts & Guarantees
```json
{
  "counts": {
    "L0": 20,
    "L1": 35,
    "L2": 20
  },
  "guarantees": [
    "Accounting equation satisfiable",
    "Double-entry journaling supported",
    "Fiscal period closing supported",
    "No factual or entity-specific accounts",
    "Kernel is canon-complete"
  ]
}
```

### 2. Markdown Documentation

The `.md` file explains:

- **What problem the kernel solves**
- **What guarantees it provides**
- **How to use it in onboarding**
- **How to audit it**
- **Immutability rules**

Read this file first to understand the kernel's purpose and design.

### 3. Checksum File

The `.checksum` file contains:

```
6a84b95b61d45d37... (SHA-256 hash)
# Generated: 2025-12-24T00:00:00Z
# Method: SHA-256 of sorted master_account_id values across L0, L1, L2
```

**Purpose:** Detect drift.

If someone modifies the kernel JSON (accidentally or maliciously), the checksum will no longer match.

**Verification:**
```bash
# Regenerate checksum from JSON
python3 -c "
import json, hashlib
with open('kernel_2025.2.json') as f:
    data = json.load(f)
ids = []
for layer in ['L0', 'L1', 'L2']:
    for acc in data['kernels'][layer]['accounts']:
        ids.append(acc['master_account_id'])
ids.sort()
print(hashlib.sha256(''.join(ids).encode()).hexdigest())
"

# Compare with frozen checksum
cat kernel_2025.2.checksum
```

If the checksums match, the kernel is intact. If they differ, the kernel has been altered.

---

## How Auditors Use Kernels

### Audit Use Case 1: Verify Onboarding Integrity

**Question:** Did Company XYZ receive the full L0 kernel during onboarding?

**Procedure:**
1. Check the company's `ChartTemplate.version` field → `2025.2-kernel`
2. Read `kernel_2025.2.json` to get the L0 account codes
3. Query the company's `company_accounts` table:
   ```sql
   SELECT code FROM company_accounts
   WHERE company_id = 'xyz'
   AND code IN ('10000', '10100', '12000', ..., '69000');
   ```
4. Verify count = 20 L0 accounts

**Verdict:** If the company has all 20 L0 accounts, onboarding was complete. If not, it failed.

---

### Audit Use Case 2: Detect Kernel Drift

**Question:** Has the kernel definition been altered since the freeze?

**Procedure:**
1. Read the frozen checksum from `kernel_2025.2.checksum`
2. Regenerate the checksum from `kernel_2025.2.json` (see verification script above)
3. Compare the two checksums

**Verdict:** Match = intact, Mismatch = altered.

---

### Audit Use Case 3: Understand Historical Behavior

**Question:** What accounts were available during Q4 2025 onboarding?

**Procedure:**
1. Check which kernel was active in Q4 2025 → `kernel_2025.2`
2. Read `kernel_2025.2.md` to understand the kernel's structure
3. Read `kernel_2025.2.json` to get exact account codes

**Verdict:** You now have a complete record of what was seeded during that period.

---

## Kernel Lifecycle

### 1. Proposal
A new kernel is proposed when:
- GAAP/IFRS standards change
- Audit identifies missing accounts
- User research suggests simplification
- New business types require different structures

**Example:** "We need to add cryptocurrency asset accounts to the kernel."

### 2. Design
The kernel designer:
- Defines the account structure
- Ensures canon compliance (accounting equation, double-entry, etc.)
- Documents guarantees and use cases

### 3. Freeze
The kernel is frozen by:
1. Generating `kernel_X.json` (authoritative data)
2. Writing `kernel_X.md` (human explanation)
3. Computing `kernel_X.checksum` (integrity hash)
4. Adding all three files to this directory

### 4. Activation
The kernel is activated by:
- Updating `seed_chart_templates.py` to reference the new kernel
- Reseeding the `chart_templates` table
- Updating onboarding logic to offer the new kernel

### 5. Preservation
Old kernels are **never deleted**.

If `kernel_2025.3` replaces `kernel_2025.2`, both remain in this directory.

**Why?** Auditors need to verify historical onboardings. Deleting old kernels destroys the audit trail.

---

## Immutability Rule

**Frozen kernels are immutable.**

Once a kernel is frozen and added to this directory:

- ✅ **You MAY:** Reference it, instantiate it, audit it
- ❌ **You MAY NOT:** Modify it, delete it, or change its checksum

**If you need to change a kernel:**
1. Create a new version (e.g., `kernel_2025.3`)
2. Freeze the new version
3. Update onboarding to use the new version
4. Leave the old version intact

**Never alter a frozen kernel.**

---

## Current Kernels

| Version | Status | Effective From | GAAP | IFRS | L0 Count | L1 Count | L2 Count |
|---------|--------|----------------|------|------|----------|----------|----------|
| 2025.2  | FROZEN | 2025-12-24     | ✅   | ❌   | 20       | 35       | 20       |

*(Future kernels will be listed here as they are frozen.)*

---

## Checksum Method

All kernels use the same checksum method for consistency:

1. **Extract** all `master_account_id` values from the kernel JSON
2. **Sort** them per layer (L0, then L1, then L2)
3. **Concatenate** them into a single string
4. **Hash** with SHA-256
5. **Store** the hash in the `.checksum` file

**Why this method?**
- **Deterministic** — Same kernel always produces same checksum
- **Order-Independent** — Sorting ensures consistency
- **Layer-Aware** — Changes to any layer are detected
- **Standard** — SHA-256 is widely supported and cryptographically secure

---

## FAQ

**Q: Can I edit a kernel JSON file?**
A: No. Frozen kernels are immutable. If you need changes, create a new kernel version.

**Q: What if I find a bug in a frozen kernel?**
A: Create a new kernel version with the fix. Document the bug in the new kernel's `notes` field.

**Q: Can I delete old kernels?**
A: No. They are part of the audit trail. Companies may still be using old kernels, and auditors need to verify historical onboardings.

**Q: How do I propose a new kernel?**
A: Open an issue or PR with:
1. Proposed kernel structure (JSON draft)
2. Rationale (what problem does it solve?)
3. Impact analysis (who is affected?)

**Q: Can I use kernels outside of Aequitas?**
A: Yes! The kernel JSON format is open and reusable. You can use it to seed your own accounting systems.

---

## Related Canon Documents

- [Canon I: Accounting Truth](../CANON_I_ACCOUNTING_TRUTH.md)
- [Canon II: Authority and Power](../CANON_II_AUTHORITY_AND_POWER.md)
- [Canon III: Evolution and State](../CANON_III_EVOLUTION_AND_STATE.md)
- [Data Dictionary](../DATA_DICTIONARY.md)

---

**Frozen kernels are the foundation of accounting integrity in Aequitas.**

By preserving kernel definitions as immutable artifacts, we ensure auditability, reproducibility, and trust.

Last Updated: 2025-12-24
Maintained By: Aequitas Canon Authority
