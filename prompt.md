PROMPT — FASTAPI CORS & APP LIFECYCLE PATCH (PROD-SAFE)

Role:
You are a senior FastAPI engineer fixing a CORS and application lifecycle bug in the Aequitas backend.

This is a backend-only patch.
Do NOT touch frontend code.

CONTEXT (FACTS, NOT THEORY)

Browser requests from http://localhost:5173 are blocked by CORS.

Errors show:
No 'Access-Control-Allow-Origin' header present

CORSMiddleware is present but not reliably applied.

The backend performs DB initialization and startup logic before FastAPI() is instantiated.

There are two routers mounted on /api/v1/companies, one of which is superuser-only.

OBJECTIVE

Ensure that every HTTP response, including:

401

403

404

dependency failures

always includes CORS headers, and that no route bypasses middleware.

REQUIRED CHANGES (MANDATORY)
1️⃣ Fix Application Initialization Order

Refactor app/main.py so that:

app = FastAPI(...) is created at the very top

CORSMiddleware is attached immediately after

All DB initialization, startup checks, and side effects are moved into:

a @app.on_event("startup") handler
OR

a clearly isolated function executed after app creation

Under no circumstances may DB logic execute before middleware attachment.

2️⃣ Harden CORS Configuration (Dev-Safe)

Update the CORS middleware to include:

explicit localhost origins

a regex fallback for localhost ports

Example (adapt as needed):

allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
],
allow_origin_regex=r"http://localhost:\d+",
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],


Do NOT use "*" with credentials.

3️⃣ Eliminate Router Shadowing on /api/v1/companies

Currently:

companies.router is mounted on /api/v1/companies

companies_su.router is ALSO mounted on /api/v1/companies

This can cause:

unexpected dependency execution

early 401 responses

Fix this by ONE of the following (choose the cleanest):

Move companies_su to /api/v1/admin/companies

OR namespace it clearly as /api/v1/companies-su

Do NOT leave two routers competing on the same prefix.

4️⃣ Guarantee Middleware Coverage

Verify that:

No router returns a raw Response that bypasses middleware

All errors use HTTPException or framework-managed responses

OUTPUT REQUIREMENTS

Provide:

Updated app/main.py (full file)

Explanation of what was moved into startup

List of routes whose prefixes changed (if any)

Do NOT include frontend changes.
Do NOT include speculative commentary.

ACCEPTANCE CRITERIA

After the patch:

All API responses include:

Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true


No browser request fails due to CORS

GET /api/v1/companies/{id} works from Vite dev server

Unauthorized requests return JSON with CORS headers

OnboardingGuard no longer loops due to Failed to fetch

Implement now.