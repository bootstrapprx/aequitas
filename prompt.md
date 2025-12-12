You are operating inside the Aequitas repository. Perform a full-scale code cleanup focusing on correctness, consistency, and elimination of technical debt. Use the following directives:

1. **Remove duplication and consolidate services:**
   - Merge master_chart_service.py and masterchart_service.py into a single consistent service.
   - Merge/replace Mapping model vs AccountMapping model.
   - Remove unused or obsolete modules.

2. **Normalize naming conventions and fix structural issues:**
   - Enforce consistent naming for account fields:
     - company_account.code
     - company_account.description
     - company_account.type
   - Fix incorrect references in Dexter (learning_engine.py).

3. **Run static corrections across backend:**
   - Ensure all new accounting models are imported correctly in app/main.py.
   - Verify that all relationships use correct back_populates.
   - Confirm that database models declare indexes and constraints properly.
   - Remove commented code blocks, dead imports, unused functions, and TODO placeholders that no longer apply.

4. **Ensure Pydantic schema alignment:**
   - Confirm every schema matches its corresponding DB model.
   - Add missing validators.
   - Ensure journal entry validation is strict (debits = credits, at least 2 lines).

5. **Check for architectural consistency:**
   - Ensure services follow the same pattern (CRUD, helpers, exceptions).
   - Ensure API routes are grouped correctly and import services consistently.
   - Make accounting services follow the same return structure as existing modules.

6. **Fix any formatting, typing, or style inconsistencies:**
   - Apply uniform TypeHints across all services.
   - Ensure datetime/date usage is consistent.
   - Normalize all Enum classes.
   - Enforce alphabetical imports and remove unused imports.

7. **Stabilize integrations:**
   - Ensure QBO token model is used instead of in-memory store.
   - Remove any leftover mock data across frontend and backend.
   - Normalize OrganizerMemory integration points.

8. **Frontend cleanup:**
   - Remove unused placeholder components.
   - Ensure all accounting pages import correct API endpoints.
   - Normalize naming in React components (PascalCase for components, camelCase for functions).
   - Remove any leftover mock dashboard lists.

9. **Report your changes clearly:**
   - For each file modified:
     - Output: “FILE UPDATED: <path>”
     - Summarize the fixes.
   - For each removed file:
     - Output: “FILE REMOVED: <path>”
     - Explain why.
   - For each new helper, validator, or service:
     - Output: “FILE ADDED: <path>”
     - Describe purpose.

Clean, correct, and prepare the entire codebase so development can continue immediately with Phase 4 and Phase 2 tasks.
