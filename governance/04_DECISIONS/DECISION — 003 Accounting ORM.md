# DECISION: 003 Accounting ORM

## Context
- How do we interact with the database, especially for complex accounting queries (ledgers, balance sheets)?
- We initially considered SQLModel for simplicity/modernity.

## Decision
- We chose: **SQLAlchemy (Core/ORM) 2.0+**.
- We moved away from pure SQLModel for complex relationships or use standard SQLAlchemy models where SQLModel's magic fell short.
- *Correction*: The codebase shows standard SQLAlchemy models are prevalent.

## Consequences
- **Positive**: Battle-tested, supports complex joins/CTEs needed for accounting aggregation.
- **Negative**: More verbose than active record patterns.

## Canon Check
- Does this violate any Canon? **No**.
