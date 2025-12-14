You are executing Phase 3A: Backend Model Alignment.

Authoritative references:
- docs/canonical/DATA_DICTIONARY.md
- docs/canonical/CHART_OF_ACCOUNTS_MODEL.md
- Current PostgreSQL schema (migrations up to 023)

Rules:
- Database schema is final.
- No migrations allowed.
- No business logic or API behavior changes.
- Remove deprecated fields completely.
- Backend must reflect DB constraints exactly.

Objectives:
1. Align SQLAlchemy models to canonical schema.
2. Remove legacy columns (parent_code, master_account_code).
3. Align enums exactly to PostgreSQL enums.
4. Fix relationships using UUID foreign keys.
5. Update Pydantic schemas accordingly.
6. Ensure backend respects immutability and locking rules.

Produce:
- Updated models
- Updated schemas
- Summary of changes
- Verification notes

Do not proceed beyond Phase 3A scope.
