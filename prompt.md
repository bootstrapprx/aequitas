/agent dexter-orchestrator

Perform a system-level acceptance review for Aequitas after completion of Milestones 4.1 and 4.2.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------
Validate that the system is coherent, secure, and ready to move into Phase 5
(Externalization / Client Readiness).

--------------------------------------------------
REVIEW AREAS
--------------------------------------------------

1. Architecture Coherence
   - Verify context hierarchy (Auth → Company → Routes)
   - Identify any remaining implicit assumptions
   - Flag coupling risks

2. Security & Access Control
   - Review auth enforcement
   - Review company isolation guarantees
   - Identify privilege escalation risks

3. Data Integrity
   - Confirm company-scoped queries everywhere
   - Identify any possible cross-company bleed
   - Review cache invalidation logic

4. UX Failure Modes
   - What happens when:
     • No company exists
     • User has one company
     • User has many companies
     • Token expires mid-session
     • Password reset is required

5. Operational Risks
   - Identify issues that would appear only with real users
   - Flag areas needing logging, metrics, or alerts

--------------------------------------------------
OUTPUT
--------------------------------------------------
Provide:
- A short ACCEPT / ACCEPT WITH NOTES / BLOCK verdict
- A prioritized list of risks (if any)
- Clear recommendation for Phase 5 scope

DO NOT implement code.
This is a review-only task.
