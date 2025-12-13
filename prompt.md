/agent backend-architect

Implement the missing permission check methods in PermissionService to resolve
BLOCKER B2.1 identified by dexter-orchestrator.

--------------------------------------------------
CONTEXT
--------------------------------------------------
API endpoints across the accounting module call:

- permission_service.can_view_company(user_id, company_id)
- permission_service.can_manage_company(user_id, company_id)

These methods DO NOT currently exist, causing runtime AttributeError and breaking
all accounting APIs.

--------------------------------------------------
TASKS
--------------------------------------------------

1. Implement the following methods in:
   backend/app/services/permission_service.py

   def can_view_company(self, user_id: UUID, company_id: UUID) -> bool
   def can_manage_company(self, user_id: UUID, company_id: UUID) -> bool

2. Logic Requirements:
   - Respect Council Member / Super User roles
   - Enforce company-level access control
   - Use existing role, membership, or permission tables
   - No hardcoded role names unless already established
   - Deny by default

3. Security Requirements:
   - No silent fallbacks
   - No implicit access
   - Explicit True / False return
   - Raise no exceptions during normal execution

4. Testing:
   - Add minimal unit or integration tests validating:
     • authorized user → True
     • unauthorized user → False
     • non-member → False

--------------------------------------------------
OUT OF SCOPE
--------------------------------------------------
- No frontend changes
- No refactors
- No new roles
- No Phase 5 features

--------------------------------------------------
SUCCESS CRITERIA
--------------------------------------------------
- All accounting endpoints execute without AttributeError
- Permission checks correctly gate access
- dexter-orchestrator P0 issue B2.1 resolved
