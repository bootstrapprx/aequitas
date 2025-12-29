# Aequitas Governance Vault

This is the **meta-module** for Aequitas: project memory, execution control, constitutional archive, and AI collaboration surface.

## Purpose

The Governance Vault is an Obsidian-based knowledge management system that:

- 🧠 **Preserves Project Memory**: Historical context, decisions, audits across sessions
- 🧭 **Controls Execution**: Phases, goals, roadmap, daily diary
- 🧱 **Archives Constitution**: Canon, Kernel, and protocols versioned alongside code
- 🗺️ **Plans Roadmap**: Strategic threads, dependencies, blockers
- 🤖 **Enables AI Collaboration**: AI agents read governance to understand architectural intent

## Structure

```
governance/
├── CONSTITUTION/         # Canon I-IV, Kernel, protocols (versioned)
├── 00_MASTER/            # Dashboards, manuals, calendars, routines
├── 01_DAILY/             # Daily execution diary (YYYY-MM-DD.md)
├── 02_PHASES/            # Lifecycle phases (P0–P8)
├── 03_GOALS_EPICS/       # Concrete goals & epics
├── 04_DECISIONS/         # Architectural / irreversible decisions
├── 05_AUDITS/            # Gap analysis, truth checks
├── 06_PROMPTS/           # Prompts given to AI agents
└── 90_ARCHIVE/           # Frozen or deprecated material
```

## Golden Rule

> **Structure explains intent.**
> **Content explains reality.**

- Do **not** flatten layers
- Do **not** mix execution with planning
- Do **not** overwrite history (archive instead)

## Entry Points

### For Humans
- **Start here**: [[Aequitas Roadmap Master]] (00_MASTER/)
- **Today's work**: Create new note in 01_DAILY/ (format: YYYY-MM-DD.md)
- **Phase status**: See 02_PHASES/
- **Active goals**: See 03_GOALS_EPICS/

### For AI Agents
- **Constitutional boundaries**: Read CONSTITUTION/ first
- **Current state**: Read [[Aequitas Roadmap Master]]
- **Recent decisions**: Check 04_DECISIONS/ (sorted by date)
- **Known gaps**: Check 05_AUDITS/

## How to Use

### Daily Work Flow

1. **Morning**: Open [[Aequitas Roadmap Master]]
2. **Create Daily Note**: 01_DAILY/YYYY-MM-DD.md (link to active goals)
3. **Work**: Execute tasks, log blockers, link decisions
4. **Evening**: Update goal statuses, mark todos complete
5. **Next Day**: Repeat

### When to Update Governance

- **Phase changes**: Update 02_PHASES/ status
- **Goal completion**: Mark goal as `done` in 03_GOALS_EPICS/
- **Irreversible decisions**: Create note in 04_DECISIONS/
- **Truth checks**: Create audit in 05_AUDITS/
- **AI prompts**: Save effective prompts in 06_PROMPTS/

## Constitution

The **CONSTITUTION/** folder contains the canonical constitutional documents:

- **Canon I-IV**: Non-negotiable accounting and architectural laws
- **Kernel**: Versioned implementation specifications (e.g., kernel_2025.2.md)
- **Protocols**: Operational protocols (future)

**Why versioned with Governance?**
- Enables full system replication from governance vault
- Preserves historical context for AI agents
- Separates constitutional truth from application code
- Security-by-separation, not obscurity

See [[CONSTITUTION/README]] for details.

## Phase System

Aequitas development follows 8 phases:

- **Phase 0**: Canon & Kernel (✅ Done)
- **Phase 1**: Foundation (✅ Done)
- **Phase 2**: Mapping (✅ Done)
- **Phase 3**: Chart Generation (✅ Done)
- **Phase 4**: Accounting Core (✅ Done)
- **Phase 5**: Financial Events Layer (🟡 Partial - Current Focus)
- **Phase 6**: Operational Modules (⚪ Planned)
- **Phase 7**: Intelligence (✅ Done - Dexter Observer, Fiscal Engine, Sandbox)
- **Phase 8**: Testing & Hardening (⚪ Planned)

See individual phase notes in 02_PHASES/ for details.

## Current Focus (2025-12-28)

**Primary Goals**:
- [[GOAL — Formal Financial Event Taxonomy (Canon)]] (Phase 5)
- [[GOAL — Sandbox UI]] (High priority - backend operational, UI missing)

**Biggest Blocker**:
- Ghost modules creating false UX expectations (see [[AUDIT — 2025-12-28 Ghost Modules and Headless Systems]])

**Next 3 Actions**:
1. Review Financial Event Taxonomy progress
2. Prioritize Sandbox UI implementation
3. Update module selector UX for honesty ("Coming Soon" labels)

## Governance Hygiene

### What Belongs Here
- Strategic decisions
- Phase definitions
- Goal tracking
- Audit findings
- Constitutional documents
- Daily work logs

### What Does NOT Belong Here
- Application code (goes in `/backend` or `/frontend`)
- Temporary notes (use scratch paper)
- User documentation (goes in `/docs` if needed)
- Secrets or credentials (never version control these)

## Tools

This vault is designed for **Obsidian** with the following plugins:
- **Dataview**: Dynamic queries for dashboards
- **Calendar**: Daily note creation
- **Graph View**: Visualize dependencies

It also works with:
- Any markdown editor (basic functionality)
- Git version control (intentional)
- AI agents (Claude Code, GPT, etc.)

## Version Control

Governance is **intentionally versioned** with the codebase.

Benefits:
- Historical context preserved
- AI agents have full project memory
- Disaster recovery: governance + code = complete system
- Cross-session continuity

## Contact

For questions about governance structure or usage:
- See [[Operating Manual]] (00_MASTER/)
- Review [[ROUTINES]] (00_MASTER/)
- Check [[Protocol Index]] (00_MASTER/)

---

*Last Updated: 2025-12-28*
*Current Phase: Phase 5 (Financial Events Layer)*
*Vault Version: Post-reconciliation*
