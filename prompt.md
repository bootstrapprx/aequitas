/agent backend-architect

Implement secure login and password feedback flow for Council Members ("Super Users") during account creation.

--------------------------------------------------
CONTEXT
--------------------------------------------------
The system currently allows account creation without proper guidance or credential feedback.
Council Members are privileged "super users" and must have a controlled, auditable onboarding flow.

--------------------------------------------------
SCOPE (STRICT)
--------------------------------------------------
This task is LIMITED to backend logic, API endpoints, and security enforcement.

DO NOT:
- Redesign frontend UI
- Implement accounting logic
- Introduce insecure password handling
- Bypass authentication best practices

--------------------------------------------------
OBJECTIVES
--------------------------------------------------
1. Allow creation of Super User (Council Member) accounts
2. Provide clear credential feedback at creation time
3. Allow controlled database population from within the application
4. Enforce strict role-based access control
5. Ensure security, auditability, and revocation capability

--------------------------------------------------
REQUIREMENTS
--------------------------------------------------

1. Super User Role
   - Define or confirm a role such as:
     • SUPER_USER
     • COUNCIL_MEMBER
   - This role must:
     • Have elevated permissions
     • Be explicitly assigned
     • Never be granted implicitly

2. Account Creation Flow
   - Implement a secure endpoint for creating Super Users
   - Access restricted to:
     • Existing Super Users
     • Or bootstrap-only initial setup
   - On creation:
     • Generate a temporary password OR
     • Accept a password that meets strict policy

3. Password Feedback
   - On successful account creation, return:
     • Username / email
     • Temporary password OR password status
     • Forced password reset flag
   - Password must:
     • Never be logged
     • Never be retrievable later
     • Be hashed immediately

4. Forced Password Reset
   - Newly created Super Users must:
     • Be required to change password on first login
     • Be blocked from sensitive actions until reset

5. Database Population
   - Allow Super Users to:
     • Create other Super Users
     • Populate necessary reference data
   - All such actions must:
     • Be permission-checked
     • Be auditable (created_by, timestamp)

6. Security & Validation
   - Enforce password policy:
     • Minimum length
     • Complexity
   - Prevent duplicate privileged accounts
   - Rate-limit account creation
   - Ensure proper error handling

--------------------------------------------------
TECHNICAL TASKS
--------------------------------------------------
- Update or create user and role models if needed
- Add secure API endpoint(s) for Super User creation
- Implement forced password reset mechanism
- Add audit fields where appropriate
- Ensure integration with existing auth system

--------------------------------------------------
SUCCESS CRITERIA
--------------------------------------------------
Before stopping, verify:
[ ] Only authorized users can create Super Users
[ ] Credentials are shown ONLY at creation time
[ ] Passwords are never stored or returned in plain text
[ ] Forced password reset is enforced
[ ] Database population actions are permission-checked
[ ] No security regressions introduced

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------
For each file modified or created:
- FILE UPDATED / CREATED: <path>
- Description of changes
- Security considerations

Stop once the Super User onboarding flow is complete and secure.
