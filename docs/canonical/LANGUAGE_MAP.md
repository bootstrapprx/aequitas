# 🧭 Aequitas — Official Language Map (Canonical)

> **Canonical document**
> This file defines the *official, non-negotiable* language boundaries of the Aequitas platform.
> Any architectural decision that violates this map is considered **invalid by default**.

---

## 🎯 Purpose

Aequitas is a **financial-grade accounting system**. Its architecture must prioritize:

- Determinism
- Auditability
- Performance at scale
- Clear authority boundaries
- Long-term maintainability

This document ensures that:

- Each programming language has a **single, exclusive purpose**
- No language competes with another
- Core accounting logic remains protected
- The system can scale without architectural drift

---

## 🧱 Layered Architecture Overview

Aequitas is structured into **strict layers**, each governed by a specific language.

```
[ UX / Visualization ]        → TypeScript (React)
[ Validation / Simulation ]   → WASM (future)
[ Data & Aggregation ]        → PostgreSQL (SQL)
[ Integrations & Jobs ]       → Go
[ High-Performance Engines ]  → Rust
[ Intelligence & Semantics ]  → Python
[ Accounting Core Authority ] → Python
```

**Authority always flows downward. Execution flows upward.**

---

## 🐍 Python — Accounting Core Authority (IMMUTABLE)

### Status
🔒 **Sovereign / Non-replaceable**

### Responsibilities
- Double-entry accounting rules
- Journal entries lifecycle
- General ledger logic
- Trial balance validation
- Financial statements (BS, P&L, CF)
- Fiscal period management
- Closing and carry-forward rules
- GAAP / IFRS semantic correctness
- Final validation of all financial facts

### Absolute Rules
- No other language may implement or override accounting rules
- No other language may decide whether data is *accounting-valid*
- Python is the **final judge** of truth

> Python does not compete. It governs.

---

## 🧠 Python — Intelligence & Semantics Layer

### Responsibilities
- Dexter (LLM orchestration)
- Organizer AI
- Prompt logic and explanation generation
- Semantic reasoning over accounts
- Integration with vector memory (pgvector)

### Constraint
- AI **never invents accounting rules**
- AI explanations must reference accounting core outcomes

> Intelligence advises. Accounting decides.

---

## 🦀 Rust — High-Performance Engines

### Status
⚠️ **Strategic / Isolated**

### Responsibilities
- Mapping Engine v2 (clustering, similarity)
- Large-scale consolidation computations
- Heavy batch processing
- CPU-intensive analytics

### Hard Restrictions
- Rust does NOT know GAAP
- Rust does NOT validate accounting truth
- Rust does NOT write final financial records

### Interaction Pattern
- Rust computes
- Python validates and persists

> Rust calculates fast. Python decides correctly.

---

## 🐹 Go — Integrations & Background Jobs

### Status
🟢 **Operational / Infrastructure**

### Responsibilities
- External integrations (QuickBooks, banks, ERPs)
- Webhook receivers
- Long-running sync jobs
- Import pipelines
- Retry-safe, idempotent processing

### Explicit Limits
- No accounting validation
- No financial decision logic
- No ledger manipulation

> Go moves data. It never interprets it.

---

## 🐘 PostgreSQL — Data & Deterministic Computation

### Status
🔒 **Critical Infrastructure**

### Responsibilities
- Source of historical truth
- Views and materialized views
- Trial balance base aggregations
- Consolidated balances
- KPI computation
- Audit-friendly data modeling
- Vector storage (pgvector)

### Principle
> Anything deterministic, repeatable, and auditable belongs in SQL.

---

## ⚛️ TypeScript (React) — User Experience Layer

### Status
🔒 **Exclusive UX Authority**

### Responsibilities
- Dashboards
- ChartForge UI
- Wizards and flows
- Visualization of financial data
- Client-side UX validation

### Prohibitions
- No accounting calculations
- No rule enforcement
- No consolidation logic

> The frontend displays truth — it does not define it.

---

## 🧩 WebAssembly (WASM) — Controlled Future Expansion

### Status
🔵 **Planned / Experimental**

### Possible Uses
- Offline validation
- What-if simulations
- Client-side performance boosts

### Absolute Rule
- WASM never becomes authoritative

---

## 🔐 Authority Matrix

| Decision / Action                         | Authority |
|-----------------------------------------|-----------|
| Debit equals credit                     | Python    |
| Period can be closed                    | Python    |
| Consolidate 100+ companies              | Rust + SQL|
| Import transactions                     | Go        |
| Generate dashboard visuals              | TypeScript|
| Explain accounting decisions            | Python    |
| Semantic similarity                     | Rust      |
| Store historical truth                  | PostgreSQL|

---

## 🚨 Fundamental Law of Aequitas

> **No language may exist without a unique, non-overlapping purpose.**

If two languages:
- solve the same problem
- validate the same rule
- decide the same truth

➡️ one of them is architecturally wrong.

---

## 📌 Governance

- This document is **canonical**
- Changes require architectural justification
- Violations must be refactored, not justified

---

**Aequitas Architecture Principle**

> Correctness before cleverness.  
> Authority before speed.  
> Accounting before everything.
