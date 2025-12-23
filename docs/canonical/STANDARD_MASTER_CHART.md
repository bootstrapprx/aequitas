STANDARD MASTER CHART OF ACCOUNTS

Aequitas – Canonical Foundation Document

Purpose of This Document

This document defines the non-negotiable principles that govern the Standard Master Chart of Accounts in Aequitas.

These rules exist to ensure that the system:

remains consistent across companies,

supports real consolidation,

avoids structural pollution,

and stays understandable to accountants, business owners, and auditors.

All features, interfaces, imports, and automations must respect this document.

1. Standard Master Chart Canon

The system must be built around a single, standard master chart of accounts.

This chart represents accounting concepts, not operational details.

It exists to support:

financial statements,

cross-company comparison,

consolidation,

and long-term stability.

The master chart is not a mirror of any client’s bookkeeping system.

2. Concept Over Fact Canon

The master chart must never contain factual or client-specific information.

The following are explicitly forbidden in the master chart:

bank names or account numbers,

people’s names,

property addresses,

vehicle models,

credit card identifiers,

tax form references.

These items are facts, not accounting concepts.

Facts belong to operational layers, metadata, or analytics — not to the master chart.

3. Clean Kernel Canon

The master chart must be:

small,

stable,

and sufficient.

It must contain only the minimum number of accounts required to produce correct financial statements and meaningful analysis.

Adding accounts for convenience, habit, or familiarity is not allowed.

If detail is needed, it must be expressed outside the master chart.

4. Root / Branch / Leaf / Fruit Canon

Accounting structure in Aequitas is expressed through four strictly separated layers.

Root

Represents immutable accounting truth.
Roots are abstract and universal.

Roots do not change to accommodate individual companies.

Branch

Represents structural organization and reporting groupings.
Branches organize accounts but do not receive postings.

Leaf

Represents posting endpoints.
All journal entries post to leaves.

Leaves classify transactions but do not identify specific instances.

Fruit

Represents analytical context and factual detail.
Fruits answer questions like who, where, which, and under what condition.

No layer may take on the role of another.

5. Extension Discipline Canon

Detail must grow around the master chart, never inside it.

Company-specific needs must be handled through:

branches,

leaves,

or fruits.

The master chart itself must not be modified to accommodate individual businesses.

If a requirement forces modification of the master chart, the requirement is invalid.

6. Value Destination Axis Canon

Accounting exists to explain where economic value must go.

The system must explicitly recognize legitimate value destinations, including:

government,

suppliers,

employees,

capital providers,

and the entity itself.

This axis:

does not create accounts,

does not change balances,

and does not alter accounting records.

It interprets accounting data for obligation awareness, planning, and decision support.

7. Operational Obligations Canon

Only obligations arising from normal business operations guide planning and projections.

Examples include:

taxes incurred from operations,

payroll,

supplier payments.

Extraordinary or exceptional events must not shape the system’s core behavior.

The system is designed around recurring economic reality, not edge cases.

8. Principal vs. Accessory Obligation Canon

Declarative duties (such as filing or reporting) are separate from monetary duties.

Only obligations that require actual payment participate in:

cash flow analysis,

projections,

and value destination logic.

Reporting obligations never generate cash movement by themselves.

9. Sandbox Mode Canon

The system must provide a sandbox mode where users can:

simulate scenarios,

project revenues and expenses,

test decisions,

and explore consequences.

Sandbox mode:

never writes to real accounting data,

never creates legal obligations,

and never alters historical records.

Its purpose is understanding, not execution.

10. Conscious Decision Canon

The goal of simulation is informed choice, not automation.

The system must help users:

see consequences,

understand trade-offs,

and take responsibility for decisions.

The system must not decide on behalf of the user.

11. Dexter as Insight, Not Authority Canon

The intelligent assistant may:

observe patterns,

suggest relationships,

highlight risks.

It must never:

impose structure,

enforce decisions,

or act without explicit user intent.

Dexter supports judgment; it does not replace it.

12. Completeness Out-of-the-Box Canon

The system must be conceptually complete from the start.

There must be:

no placeholder layers,

no undefined future concepts,

no “slots” reserved for later thinking.

The foundation must stand on its own and evolve only through explicit, controlled extensions.

Final Statement

The Standard Master Chart of Accounts is the foundation of Aequitas.

No interface, integration, client request, or automation may override the principles in this document.

If a feature conflicts with this canon, the feature is wrong.