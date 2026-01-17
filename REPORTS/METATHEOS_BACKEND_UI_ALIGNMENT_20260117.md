# Metatheos Backend ↔ UI Alignment Report (2026-01-17)

## Root Causes
- The Metatheos React pages were static placeholders with no API calls.
- The frontend had no Metatheos API base or proxy; Vite only proxied `/api` to the Aequitas backend.
- `metatheos-server` binds to port 3000 but had no host-level mapping in `docker-compose.dev.yml`, so the browser origin had no direct route to it.

## Investigation Checklist
1. Backend Server Reachability
   - Server binds `0.0.0.0:3000` in `governance/metatheos/metatheos-server/src/main.rs`.
   - `docker-compose.dev.yml` has no host port mapping for `metatheos-server`, so it is only reachable inside the Docker network.
   - Frontend origin (`http://localhost:5173`) had no proxy route to port 3000 before this patch.
2. Frontend API Base URL
   - Metatheos UI had no API adapter; login used `/auth/*` paths and the Aequitas `VITE_API_URL` default.
   - Added `VITE_METATHEOS_API_URL` default (`/metatheos-api`) and a Vite proxy target for Metatheos.
3. REST Endpoints
   - Verified routes exist in `governance/metatheos/metatheos-server/src/main.rs`:
     - `GET /api/context/overview`
     - `GET /api/phases`
     - `GET /api/phases/:id`
     - `GET /api/day/today`
     - `GET /api/timeline`
   - Runtime responses were not queried in this session (services not started).
4. DTO Shape Mismatch
   - `/api/context/overview` returns a DTO directly; list endpoints return `{ data: [...] }`.
   - Frontend adapter now normalizes both shapes when loading data.
5. CORS / Origin Issues
   - Axum server already applies permissive CORS (`allow_origin(Any)`), so no change required.
   - Dev proxy avoids browser CORS for local development.

## Fixes Applied
- Added Metatheos API adapter and wiring for Home, Phases, and Timeline data.
- Added Vite proxy `/metatheos-api` → Metatheos backend and Docker env to target the service.
- Aligned Metatheos auth calls to `/api/auth/*` endpoints.

## Legacy / Not Changed
- `/api/invoke/:command` remains intact and continues logging deprecation warnings.
- Schema and SurrealDB layout are unchanged.

## Verification Steps
- Start the stack (cached build): `make dev-cached`.
- Open `/metatheos` and confirm Active Phase + Current Day populate from real data.
- Open `/metatheos/phases` and `/metatheos/timeline` to confirm lists render.
- Check browser network calls to `/metatheos-api/api/...` for 200 responses.
- Ensure `metatheos-server` logs show no panics or errors.
