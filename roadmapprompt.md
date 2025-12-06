
# 📌 **PROMPT PARA CLAUDE CODE — “Aequitas Roadmap Master Document”**

*(pronto para copiar e colar)*

---

You are the lead engineer responsible for completing **Aequitas**, a full accounting hub designed as a superior alternative to QuickBooks for multi-company management.

Below is the complete **context**, **current status**, **missing components**, and the **precise roadmap** you must follow.
Your task is to transform this into actionable engineering steps, resolve missing implementations, fix incomplete logic, refactor legacy pieces, and produce clean, production-grade code.

---

# 🔷 **1. Project Background — Read Carefully**

(A summary of **backstory.txt**, written to guide your decisions)

Aequitas originated from a real consulting case.

The client — “Bob” (name anonymized) — owns 8+ companies across management, holding, and real-estate development.
He hired an accountant but suffered from **lack of communication, poor categorization, and no consistency**.

During an assessment, the following was discovered:

* None of Bob’s companies shared a standardized Chart of Accounts.
* QuickBooks cannot show multi-company data on a single screen.
* Reviewing all companies individually is inefficient and error-prone.
* Bob has OCD-level expectations for consistency — capitalization, naming, codes, and structure must be standardized.

This led to:

1. Creation of the **US_GAAP_Accounting_Workbook.xlsx**
2. Consolidation of all his companies’ charts into one **standard master chart**
3. Generation of **enriched_master_chart.csv**, now ~70% complete
4. Development of **ChartForge**, a visual interface to maintain and map charts
5. Expansion of the idea into **Aequitas**, a full enterprise accounting hub designed to be:

   * Multi-company
   * Standardized
   * AI-assisted
   * More ergonomic and centralized than QuickBooks
   * Capable of showing consolidated operations on dashboards

Aequitas is now a working prototype visually, but the **backend business logic is incomplete**, some services are partial, and QuickBooks-equivalent functionalities are missing.

Your job is to **complete the product**.

---

# 🔷 **2. What We Already Have**

## ✔ Backend

* **FastAPI application fully scaffolded**
* Auth system (JWT)
* Company management + UCID generation
* User/company associations and permissions
* Master chart data (US-GAAP, 345 accounts)
* Enriched chart CSV + import routines
* Partial Mapping Engine (fuzzy matching + manual overrides)
* Organizer AI: ingest, classify, memory, feedback
* Dexter: natural language query engine
* QBO integration scaffold (OAuth + basic sync)
* Snapshot system
* Template system
* Audit logs
* Database models are ~95% complete

### Significant services present

* `master_chart_service.py`
* `company_service.py`
* `mapping_engine.py` + `mapping_service.py`
* `organizer_ai/*`
* `dexter/*`
* `quickbooks_service.py`
* `snapshot_service.py`
* `database_service.py`

---

## ✔ Frontend

* Complete React + TS + Vite + Tailwind + shadcn/ui environment
* Full routing structure
* ChartForge UI:

  * Interactive tree
  * Master chart pages
  * Import/export
  * Manual mapping
  * Template editor
* Company CRUD
* User & permission management
* QBO integration views
* Organizer AI pages
* Dashboard skeleton
* Accountancy pages (Journal, Ledger, Trial Balance) **started**
* Reports module scaffolded

---

## ✔ DevOps

* Docker Compose dev/prod
* Postgres + pgvector
* Ollama
* Nginx reverse proxy
* Makefile workflows

---

# 🔷 **3. What Is Missing — The REAL GAP**

This is where Claude must act decisively.

## 🔻 **A. Full Master Chart Engine Completion**

* Generation of codes by rules for ALL accounts
* Enforcement of naming standards
* Validation pipeline
* Bulk import from enriched CSV → DB with full hierarchy
* Round-trip edits from UI to DB to export
* Reconciliation of enriched chart with US-GAAP root

## 🔻 **B. Full Mapping Engine**

* Confidence aggregation
* Cluster-based matching
* Conflict resolver
* Multi-company unified mapping view
* Mapping propagation rules
* Auto-suggestions with “learning memory”

## 🔻 **C. Company Chart Generator**

For each company:

* Generate company chart using:

  * Standard master chart
  * Exceptions
  * Rules
* Ensure hierarchy + codes remain valid
* Detect missing accounts
* Detect duplicated accounts
* Update QBO imports into structure

## 🔻 **D. QuickBooks Routine Parity**

Aequitas must replicate basic functionalities of QuickBooks:

### Essential Features Missing

1. **Journal Entry system**
2. **Ledger & posting**
3. **Trial Balance auto calculation**
4. **Automatic closing entry routine**
5. **Financial Statements:**

   * Balance Sheet
   * P&L
   * Cash Flow (indirect method)
6. **Multi-company consolidated view**
7. **Standardized reporting based on master chart**

These are critical.

## 🔻 **E. Dashboard Engine**

* Consolidated KPIs
* Company-level KPIs
* Data normalization layer
* Period comparisons
* QBO sync visual state

## 🔻 **F. Hardening Missing**

* Error handling
* Input sanitation
* Idempotent imports
* Retry logic in integrations
* Unit tests for core modules

---

# 🔷 **4. The Required Roadmap (Meticulous)**

Claude must follow this order.
NOTHING should be done out of sequence.

---

## **Phase 1 — Foundation Hardening**

1. Review all backend services
2. Identify unused, duplicate or outdated modules
3. Ensure all models match actual logic
4. Finalize MasterAccount and CompanyAccount relationships
5. Implement a MasterChartValidator class
6. Create a MasterChartNormalizer class
7. Ensure enriched_master_chart.csv → JSON → DB migration is deterministic

**Output:**
The master chart becomes **canonical**, **validated**, **100% reliable**.

---

## **Phase 2 — Mapping Engine Completion**

1. Finalize confidence scoring
2. Add cluster-level semantic matching
3. Resolve multi-mapping conflicts
4. Add memory-based suggestions
5. Create a mapping audit log per company
6. Produce mapping quality scoring

**Output:**
Every company can be mapped in minutes, not hours.

---

## **Phase 3 — Company Chart Generator**

1. Generate standardized charts
2. Auto-create missing accounts
3. Recode malformed accounts
4. Build mapping preview pages
5. Allow selective adoption of master chart changes

**Output:**
All companies share a standard, enforced Chart of Accounts.

---

## **Phase 4 — Accounting Engine**

Implement a minimal QuickBooks-equivalent backend:

### Ledger Layer

* Double-entry validation
* Posting routines
* Period locking
* Correction entries

### Core financial modules

1. Journal Entry API
2. Ledger queries
3. Trial Balance generator
4. Financial Statement generators
5. Consolidation layer

**Output:**
Full accounting backbone.

---

## **Phase 5 — QBO Integration Expansion**

1. Full import of accounts, journal entries, and balances
2. Detection of divergences from Aequitas standard
3. Sync engine with conflict resolution
4. View diffs

---

## **Phase 6 — Dashboard Engine**

1. Normalization layer
2. Multi-company consolidation
3. KPIs
4. Period filtering
5. Financial charts

---

## **Phase 7 — Frontend Finalization**

1. Complete all pages
2. Add missing forms
3. Ensure consistent capitalization (Bob request!)
4. Add loading states, skeletons
5. Add multi-company navigation

---

## **Phase 8 — Testing & Hardening**

* Unit tests
* Integration tests
* Snapshot tests for API
* Schema validation test suite
* Frontend e2e tests

---

# 🔷 **5. Deliverables Expected from You (Claude Code)**

### **A. List of all missing pieces**

### **B. Clean, maintainable implementations**

### **C. A sequenced plan of PRs**

### **D. Refactoring where needed**

### **E. Documentation updates**

### **F. Automated tests**

### **G. Scripts for importing legacy data**

---

# 🔷 **6. Your Operating Rule**

> Always maintain backward compatibility with existing master chart logic, until explicitly instructed to break it.

---

# 🔷 **7. Project Goal**

Deliver a **fully functional accounting hub**, capable of replacing QuickBooks for:

* Multi-company operations
* Standardized chart of accounts
* Automated mapping
* Financial statements
* Dashboards
* AI-assisted classification
* QBO synchronization

---

# 🔷 **End of Prompt**

