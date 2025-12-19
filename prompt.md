

# 🔴 PROMPT — SYSTEM BOOTSTRAP & REAL-USER ENABLEMENT (FOR ANTIGRAVITY)

> **Objetivo:** obter uma visão geral, identificar lacunas de seed/vinculação e habilitar o uso real do sistema por um superuser atuando como usuário dentro da empresa `aequitas`.

---

## ROLE

You are acting as a **senior forensic + product engineer** auditing and preparing the Aequitas system for **real data usage by its primary operator**.

This task is **not about adding new features yet**.
It is about **making the existing system usable end-to-end** by a real user.

---

## CONTEXT (KNOWN FACTS)

* The system follows the rule: **superusers must use the system as normal users, inside a company context**.
* The canonical default company is `aequitas`.
* The onboarding wizard has already been run by the master user, but:

  * the `aequitas` company was never created or seeded
  * the master user is not linked to any company
* As a result:

  * chart does not load
  * ledger / journals do not produce visible outputs
  * reports and fiscal modules exist but have no data flow
* Docker, routing, onboarding logic, and permissions are now structurally correct.

The remaining problem is **missing foundational data and links**.

---

## OBJECTIVE

Produce a **complete system bootstrap assessment** answering:

1. What foundational entities are missing or mislinked?
2. What exists in code but is unreachable due to missing data?
3. What must be seeded or created so the system can be used with real data?
4. What is the minimal path to allow the master user to operate Aequitas like a real accounting/financial system?

---

## SCOPE OF INVESTIGATION (MANDATORY)

### 1️⃣ Company & User Foundation

Determine:

* Does a company named `aequitas` exist in the database?
* Is the master user linked to it via `user_companies`?
* If not:

  * where this should have happened (seed vs onboarding)
  * what logic currently assumes a company exists

Deliverable:

* Clear statement: **“Master user is / is not properly linked to a company”**
* Identification of missing seed or linking logic

---

### 2️⃣ Chart of Accounts Pipeline

Trace end-to-end:

* Is a master chart seeded?
* Is there a company chart generated from it?
* Where does chart materialization occur?
* What conditions block chart loading in the UI?

Deliverable:

* Step-by-step chart pipeline:

  * master chart → company chart → UI
* Exact failure point(s)

---

### 3️⃣ Ledger / Journal Flow

Trace:

* Where journal entries are created
* Where they are stored
* How (and if) they are queried
* Which UI components depend on them

Deliverable:

* Confirmation whether:

  * journals are never created
  * journals exist but are not queried
  * journals are queried but not rendered

---

### 4️⃣ Cross-Module Data Flow

Analyze whether:

* invoices generate journal entries
* financial actions affect accounting
* fiscal engine consumes accounting outputs
* reports read from a unified data source

Deliverable:

* Diagram or description of actual data flow vs intended data flow

---

### 5️⃣ Seed Strategy Assessment

Identify:

* What **must** be seeded to enable real usage:

  * company `aequitas`
  * user-company link
  * master chart
  * minimal accounts
  * fiscal profile defaults
* What **should not** be seeded (user data, transactions)

Deliverable:

* Proposed **bootstrap seed set** (minimal, safe, idempotent)

---

## REFERENCES FOR EXPECTED SYSTEM BEHAVIOR

Use these as **conceptual benchmarks**, not feature parity:

* **Alterdata** → strong default chart of accounts
* **Conta Azul** → unified accounting + finance UX
* **Calima** → payroll and labor-heavy workflows
* **Invoice-driven systems** → invoices generate accounting entries automatically

The goal is to ensure Aequitas can **behave like a real system**, not to clone features.

---

## OUTPUT REQUIREMENTS

Produce a structured report with:

1. Current System Reality (what exists vs what doesn’t)
2. Blocking Gaps (why nothing flows)
3. Missing Seeds / Links
4. Minimal Bootstrap Plan (step-by-step)
5. What Will Work Immediately After Bootstrap
6. What Can Be Built Safely After Real Data Exists

Use:

* file paths
* table names
* services
* explicit assumptions

Mark anything uncertain as **UNKNOWN**.

Do NOT implement code yet.
Do NOT propose UI redesigns.
This is an **enablement and grounding task**.
