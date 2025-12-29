
---

# Aequitas Operating Manual (Reference)

> [!IMPORTANT] GO TO WIZARD
> **This is the Reference Manual.**
> For daily execution, start your day at the **[[Aequitas Wizard]]**.

**Purpose:** The "Constitution" of the system. Detailed rules, philosophy, and maintenance instructions.
**Audience:** You (for deep understanding), collaborators, AI agents.

---

## 1. What This Vault Is (Mental Model)

This Obsidian vault is **not notes**.  
It is a **governance and execution system** for Aequitas.

Think of it as:

- 🧠 **Memory** (what we decided, built, audited)
    
- 🧭 **Control panel** (what matters now)
    
- 🧱 **Constitutional archive** (what cannot be violated)
    
- 🗺️ **Road map engine** (where we are going, with forks and dead ends preserved)
    

Nothing here is throwaway.  
Even wrong turns are valuable data.

---

## 2. The Core Structure (Never Change Casually)

```
CONSTITUTION/     ← Canon I-IV, Kernel, protocols (versioned)
00_MASTER/        ← Command center & dashboards
01_DAILY/         ← Work diary (what actually happened)
02_PHASES/        ← Large lifecycle blocks (P0, P1, …)
03_GOALS_EPICS/   ← Concrete goals inside phases
04_DECISIONS/     ← Irreversible or important choices
05_AUDITS/        ← Truth checks, gap analysis, reviews
06_PROMPTS/       ← Prompts given to AI agents
90_ARCHIVE/       ← Frozen or deprecated material
```

### Golden Rule

> **Structure explains intent. Content explains reality.**

Do not flatten this. Do not mix layers.

---

## 3. The Master Dashboard (How to Use It)

File:

```
00_MASTER/Aequitas Roadmap Master.md
```

> **Note:** Access this via the [[Aequitas Wizard]] for a guided flow.

### What it is

A **live dashboard**, not a narrative document.

### What you do there

- Read it daily
    
- Update **only** the “Now” panel manually
    
- Let everything else update automatically (Dataview)
    

### What you do NOT do there

- Write long explanations
    
- Track raw thoughts
    
- Log work (that’s for Daily Notes)
    

---

## 4. Daily Notes (Your Execution Diary)

Folder:

```
01_DAILY/YYYY-MM-DD.md
```

### This is the most important habit

If you only do **one thing consistently**, do this.

### Purpose

Daily notes answer:

- _What did I actually do today?_
    
- _What diverged from the plan?_
    
- _What new blockers or insights appeared?_
    

### Required Frontmatter

```yaml
---
type: daily
date: YYYY-MM-DD
phase: P?
goals: []
blockers: []
decisions: []
updated: YYYY-MM-DD
---
```

If you don’t know a field → leave it empty.  
Never guess.

### Recommended Sections

```md
## Focus
(one sentence)

## What I did
(bullets, factual)

## Divergences
(where reality differed from plan)

## Blockers
(if any)

## Notes for future me
```

This creates a **forensic timeline** of the project.

---

## 5. Goals & Phases (Planning Without Lying to Yourself)

### Phases (`02_PHASES/`)

Big containers like:

- P0 — Foundations
    
- P1 — Kernel & Canon
    
- P2 — Sandbox
    
- …
    

Phases **do not contain tasks**.  
They contain **goals**.

### Goals (`03_GOALS_EPICS/`)

This is where work is scoped.

#### Required Frontmatter

```yaml
---
type: goal
id: G-###
status: planned | active | blocked | partial | done
phase: P?
depends_on: []
canon: []
owner: you
updated: YYYY-MM-DD
---
```

### Status meanings (important)

- **planned** → not started
    
- **active** → currently worked on
    
- **blocked** → cannot proceed (external or internal reason)
    
- **partial** → delivered but not fully resolved
    
- **done** → closed, frozen, archived
    

Never mark `done` unless it is **canonically closed**.

---

## 6. Decisions (Point of No Return)

Folder:

```
04_DECISIONS/
```

A decision is something that:

- Changes architecture
    
- Narrows future options
    
- Would be expensive to reverse
    

### Rule

> If you feel uneasy about forgetting _why_ you chose something — write a Decision note.

These are surfaced automatically in the Dashboard.

---

## 7. Audits (How You Avoid Self-Deception)

Folder:

```
05_AUDITS/
```

Audits answer:

- What is missing?
    
- What is broken?
    
- What are we pretending exists?
    

Audits are **descriptive**, not prescriptive.

They do not execute change.  
They justify it.

---

## 8. Prompts (AI as First-Class Actor)

Folder:

```
06_PROMPTS/
```

Why this matters:

- Prompts _are design artifacts_
    
- They encode intent, constraints, and authority
    
- They explain why AI produced what it did
    

Always log:

- Who the prompt was for (Claude, Antigravity, Gemini)
    
- What the goal was
    
- What constraints were imposed
    

---

## 9. Canon vs Everything Else (Do Not Mix)

### Canonical documents (inside governance, versioned)

Located in:

```
governance/CONSTITUTION/
```

They include:

- Canons I–IV (Constitution)

- Kernel 2025.2 (and future kernel versions)

- Protocols (Financial Event Taxonomy, etc.)


**Why in governance?**
- Constitutional documents versioned with project by design
- Enables full system replication from governance vault
- AI agents can read Canon to understand architectural intent
- Security-by-separation, not obscurity

### Rule

> **Nothing in Obsidian can override the Canon.**

Obsidian documents:

- interpret

- plan

- execute

- audit


They **never redefine truth**.

See [[CONSTITUTION/README]] for full details.

---

## 10. Dataview: How Automation Works (High Level)

You don’t need to write Dataview daily, but you should know:

- Dashboards **query metadata**, not text
    
- Frontmatter consistency matters more than prose
    
- Missing metadata shows up as warnings (by design)
    

If something doesn’t appear in the dashboard:

1. Check its frontmatter
    
2. Check its folder
    
3. Check its `type`
    

---

## 11. Divergence Is Not Failure (Core Philosophy)

This system explicitly allows:

- Backtracking
    
- Re-framing
    
- Dead ends
    
- Partial deliveries
    

That’s why:

- Daily notes exist
    
- Blocked status exists
    
- Partial status exists
    
- Audits exist
    

The goal is **clarity**, not linear progress.

---

## 12. How to Use This Daily (Simple Loop)

**Every day (5–10 minutes):**

1. Open today’s Daily note
    
2. Write what you actually did
    
3. Add blockers if any
    
4. Link goals naturally (`[[G-###]]`)
    

**Every week (15 minutes):**

1. Open Master Dashboard
    
2. Update the “Now” panel
    
3. Check blocked goals
    
4. Decide what _not_ to work on
    

---

## 13. What Not to Do (Very Important)

❌ Don’t track tasks only in your head  
❌ Don’t mark goals done “emotionally”  
❌ Don’t let the Master become a wall of text  
❌ Don’t change Canon to match code  
❌ Don’t skip Daily notes for multiple days

---

## 14. If You Forget Everything Else

Remember this:

> **The vault is a mirror.  
> If it’s confusing, reality is confusing.  
> Fix the mirror last. Fix thinking first.**

---

