# DECISION: 002 Auth Strategy

## Context
- How should we handle user identity and access control?
- We need robust security but also control over the user data for multi-tenancy.

## Options Considered
1. **SaaS Auth**: Clerk, Auth0.
2. **Library Auth**: NextAuth (if we used Next.js).
3. **Custom + OAuth**: Homegrown JWT implementation with Google OAuth via library.

## Decision
- We chose: **Custom Implementation + Google OAuth**.
- We use `authlib` for OAuth flows and issue our own JWTs.
- Identity is owned by our database (`User` table).

## Consequences
- **Positive**: Total control over the `User` > `Company` > `Role` graph. No vendor lock-in. Free.
- **Negative**: We own the security risk. Must maintain token refresh logic, CORS, etc.

## Reversal Plan
- Can migrate to Clerk later by swapping the token issuer, but keeping our `User` table is harder if we offload everything.

## Canon Check
- Does this violate any Canon? **No**. Canon II (Authority) implies we should own the keys to the castle.
