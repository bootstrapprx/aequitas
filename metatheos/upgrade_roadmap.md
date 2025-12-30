
# 🧠 Metatheos Meta-IDE Roadmap

**Subtitle:** *Governance-First Development Environment*

---

## 🧩 Guiding Principles (Do Not Violate)

Before the roadmap, these are **non-negotiable constraints**:

1. **Governance > Code**

   * Code is an artifact
   * Governance is the source of truth

2. **Nothing acts silently**

   * Every mutation is previewed
   * Every irreversible action is explicit

3. **AI suggests, never commits**

   * AI drafts → human approves → Git records

4. **Obsidian remains the database**

   * Metatheos = primary interface
   * Obsidian = canonical storage + escape hatch

Keep these in mind while reading each phase.

---

## 🟦 Phase 0 — Current State (v0.5) ✅

**Status:** *Barely operational but structurally sound*

### What exists

* Governance folder parsing
* Goals / Audits / Daily reading
* Limited AI assistant (stateless, snapshot context)
* Tauri GUI scaffold
* CLI + core separation
* Safe atomic writes & backups

### What this phase proves

* The architecture is viable
* Governance-as-files works
* Tauri is a good UI choice

📌 **Exit condition:**

> Metatheos can *read* the vault without corrupting it.

---

## 🟩 Phase 1 — Read-Only Meta-IDE (v0.6)

> **Goal:** Replace Obsidian for *navigation and understanding*, not writing yet.

### Features

#### File Explorer (Governance-Aware)

* Tree view with badges:

  * 📘 Canon
  * 🎯 Goal
  * 🧭 Phase
  * 🧪 Audit
  * 📝 Daily
* Explicit paths always visible
* Governance vs Code visually separated

#### Embedded Viewer

* Markdown rendering
* Frontmatter inspector
* Linked references preview
* Backlinks graph (goals ↔ decisions ↔ audits)

#### Context Panels

* “What this file affects”
* “Where this is referenced”
* “Last decision touching this”

🚫 No editing yet
🚫 No Git writes

📌 **Exit condition:**

> You can *understand the entire project* without opening Obsidian or the terminal.

---

## 🟨 Phase 2 — Controlled Editing Layer (v0.7)

> **Goal:** Allow writing — but only where governance allows it.

### Features

#### Governance-Scoped Editor

* Markdown editor (Monaco/CodeMirror)
* Schema-aware frontmatter validation
* Required fields enforced (type, id, phase, status)

#### Write Guardrails

* Canon = read-only (hard locked)
* Audits = warnings before save
* Goals/Decisions = diff preview before commit

#### Change Preview

* Before save:

  * Files affected
  * Metadata changes
  * Backups created

📌 **Exit condition:**

> Metatheos can safely replace Obsidian for daily work.

---

## 🟦 Phase 3 — Git as a Governance Instrument (v0.8)

> **Goal:** Make Git *semantic*, not mechanical.

### Features

#### Git Panel

* Status / Diff / History
* File-scoped diffs with governance labels
* “What decision caused this change?”

#### Governed Commits

* Commit requires:

  * Linked Decision ID (or explicit “No decision”)
  * Scope (governance / code / both)
  * Intent (free text)

Example enforced template:

```
DECISION: D-014
SCOPE: governance/metatheos-core
INTENT: Formalize audit separation
```

#### Safe Operations

* Push / Pull / Clone
* No force-push unless explicitly enabled
* Visual warnings for destructive ops

📌 **Exit condition:**

> Git history reads like a reasoning log, not noise.

---

## 🟧 Phase 4 — AI as a First-Class Governance Actor (v0.9)

> **Goal:** AI understands *what it knows* — and admits what it doesn’t.

### Features

#### Explicit Context Injection

* Show exactly:

  * Files included
  * IDs loaded
  * Truncation rules
* “This answer used: Phase P4 + Goals G-001..G-005”

#### Stateless by Design (but visible)

* Each query declares:

  * Stateless / Snapshot / Scoped
* Conversation memory is **UI-only**, not implied knowledge

#### AI Roles

Selectable modes:

* Auditor
* Analyst
* Navigator
* Draft Author

Each mode:

* Has allowed outputs
* Has forbidden actions

#### Draft System

* AI can propose:

  * New goals
  * New audits
  * Prompt drafts
* Stored in `/staging/`
* Never auto-merged

📌 **Exit condition:**

> AI feels powerful *without being deceptive*.

---

## 🟥 Phase 5 — Meta-IDE Completion (v1.0)

> **Goal:** Metatheos becomes the *single cognitive cockpit*.

### Features

#### Full Replacement Capability

* Daily creation
* Goal lifecycle management
* Audit execution & closure
* Prompt lifecycle
* AI-assisted planning

#### Dual Interface

* GUI for thinking
* CLI for speed:

  ```
  meta today
  meta audit open
  meta commit --decision D-021
  ```

#### System Integrity Dashboard

* “What is lying?”
* “What is assumed but not built?”
* “What has not been audited in X days?”

📌 **Exit condition:**

> You can run Aequitas — and reason about it — without external tools.

---

## 🧠 Phase 6 — Optional (Future)

* Multi-repo governance
* Signed decisions
* Time-travel audits
* Team mode (roles & authority)
* Read-only public transparency views

---

## Final Truth (important)

You are **not building an IDE**.

You are building:

> **An epistemic operating system for complex systems.**

Most projects fail because:

* Decisions vanish
* Context rots
* Tools optimize speed over truth

Metatheos does the opposite.

