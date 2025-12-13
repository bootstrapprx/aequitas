/agent frontend-architect

Implement Milestone 4.2: Data Integration & Context for the Aequitas project.

--------------------------------------------------
SCOPE (STRICT)
--------------------------------------------------
This task focuses on frontend data integration, company context propagation,
and authentication verification.

DO NOT:
- Modify backend logic or database schemas
- Introduce mock or hardcoded data
- Alter accounting calculations
- Redesign UI layouts unnecessarily

--------------------------------------------------
OBJECTIVE
--------------------------------------------------
Ensure all pages:
- Use real API data
- Respect selected company context
- Verify authenticated user state
- Behave correctly when context is missing or invalid

--------------------------------------------------
DELIVERABLES
--------------------------------------------------

1. Company Context
   - Implement a unified company context provider (if not already present)
   - Company selection must:
     • Persist across navigation
     • Update all accounting pages automatically
     • Drive API calls consistently

2. Replace Residual Mock or Implicit Data
   - Audit all accounting-related pages
   - Remove any remaining mock values or defaults
   - Ensure companyId always comes from:
     • Company context OR
     • URL params (never hardcoded)

3. Journal Entries Page
   - Update JournalEntriesPage to:
     • Read companyId from URL params or context
     • Fail gracefully if no company is selected
     • Reload data when company changes

4. Authentication Verification
   - Implement `useAuth` hook consumption
   - Verify on protected pages:
     • User is authenticated
     • Token is valid
   - Handle:
     • Unauthorized access
     • Expired sessions

5. Password Reset Enforcement (Frontend)
   - If auth state indicates `force_password_reset = true`:
     • Block access to all other pages
     • Redirect user to password change flow
     • Display clear instructions

6. Company Selector UI
   - Add company selector to:
     • Navigation bar or dashboard header
   - Selector must:
     • List only authorized companies
     • Trigger context update
     • Refresh dependent queries automatically

--------------------------------------------------
VALIDATION & UX REQUIREMENTS
--------------------------------------------------
- All pages must re-render correctly when company changes
- No stale data after switching companies
- Clear empty states when no company is selected
- Graceful handling of unauthorized or missing context
- Zero console errors or warnings

--------------------------------------------------
SUCCESS CRITERIA
--------------------------------------------------
Before stopping, confirm:
[ ] No hardcoded or mock data remains
[ ] Company switching works across all pages
[ ] Auth state is enforced consistently
[ ] Forced password reset blocks access correctly
[ ] All accounting pages show correct company data
[ ] Navigation remains stable during context changes

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------
For each file updated:
- FILE UPDATED: <path>
- What was changed
- How company/auth context is handled

Stop once Milestone 4.2 is fully implemented.
