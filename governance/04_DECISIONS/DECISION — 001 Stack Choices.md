# DECISION: 001 Stack Choices

## Context
- We needed to select a technology stack for the Aequitas platform that supports:
    - Type safety (critical for accounting/money).
    - Rapid iteration.
    - Robustness and ecosystem maturity.
    - Separation of concerns between Logic and UI.

## Options Considered
1. **Full JS/TS**: Next.js fullstack.
2. **Standard Enterprise**: Java/Spring Boot + Angular.
3. **Modern Python**: Python/FastAPI + React.

## Decision
- We chose: **Modern Python (FastAPI) + React (Vite)**.
- **Backend**: Python 3.11+. Why? Excellent for numeric precision (decimal), data processing, and AI integration (Dexter). FastAPI provides strong typing via Pydantic.
- **Frontend**: React + Vite + Tailwind. Why? Industry standard, fast dev server, huge component ecosystem.
- **Database**: PostgreSQL. Why? JSONB support + ACID compliance is non-negotiable for ledgers.

## Consequences
- **Positive**: High velocity, types on both ends (Pydantic/TypeScript), strict money handling in Python.
- **Negative**: Context switching between languages. Need to sync types (can use code generation).

## Canon Check
- Does this violate any Canon? **No**. Canon I requires Truth; Python's Decimal type is the gold standard for financial truth compared to JS floats.
