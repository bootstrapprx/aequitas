# AUTH RECOVERY – REMOVE AFTER FIXING GOOGLE OAUTH

## Purpose
Emergency path to regain admin access when Google OAuth or standard login flows are broken. This path must only be used temporarily during recovery and then removed.

## Environment Variables
Set these in your active `.env` file (or container env) and restart the backend:

```
AUTH_RECOVERY_MODE=true
ENABLE_GOOGLE_AUTH=false
RECOVERY_ADMIN_EMAIL=admin@example.com
RECOVERY_ADMIN_PASSWORD=SuperSecret123!
```

- `AUTH_RECOVERY_MODE` gates the fallback login endpoint.
- `ENABLE_GOOGLE_AUTH=false` hides OAuth buttons, disables `/auth/oauth/*` routes, and prevents accidental redirects while recovering.
- `RECOVERY_ADMIN_*` credentials are used for the one-off admin session. Choose unique, temporary values.

## Recovery Login Steps
1. Configure the variables above and restart the backend service (`make backend`, `docker compose up`, etc.).
2. Run the emergency login request (replace creds to match your env):
   ```bash
   curl -X POST \
     http://localhost:8000/api/v1/auth/recovery-login \
     -H 'Content-Type: application/json' \
     -d '{"email":"admin@example.com","password":"SuperSecret123!","recovery":true}'
   ```
3. The response includes a normal JWT bearer token. Use it immediately:
   ```bash
   export AUTH_TOKEN="<token from step 2>"
   curl -H "Authorization: Bearer $AUTH_TOKEN" http://localhost:8000/api/v1/auth/me
   ```
4. Optional: open `http://localhost:5173/login`, enter the same credentials, and click **Use Recovery Login**. The UI now calls `/auth/recovery-login` and redirects to `/auth/setup` or `/dashboard`.

## After Regaining Access
1. Reset passwords and confirm you can log in via normal `/auth/login-json`.
2. Re-enable Google OAuth and exit recovery mode:
   ```
   AUTH_RECOVERY_MODE=false
   ENABLE_GOOGLE_AUTH=true
   RECOVERY_ADMIN_EMAIL=
   RECOVERY_ADMIN_PASSWORD=
   ```
3. Restart the backend to apply changes.
4. Remove or rotate any temporary credentials that may have been committed locally.

## Removal Checklist
Once Google OAuth is stable:
- Delete the recovery env variables from `.env` files.
- Remove the `/auth/recovery-login` endpoint, related config flags, and UI messaging marked with `AUTH RECOVERY – REMOVE AFTER FIXING GOOGLE OAUTH`.
- Confirm the OAuth login flow works end-to-end and that the recovery button disappears from the login screen.
