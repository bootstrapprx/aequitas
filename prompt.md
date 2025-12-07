
# **Claude Code – Autonomous Implementation Prompt**

### **Feature: GroupCompany (Umbrella View) + SU Manual Company Creation + CORS Fix**

### **Instructions to the agent**

Work directly in the existing `aequitas` repository.
Make **small, atomic commits**, each with clear messages (e.g., `feat(groups): ...`, `fix(cors): ...`).
Open PRs or provide patches in logical units.
Do not remove or break existing features.
Maintain compatibility with current permission system.

---

# **OBJECTIVE**

Implement the following end-to-end:

1. **CORS fix** (backend must accept frontend running at `localhost:5173`).
2. **GroupCompany / Umbrella View**:

   * DB models
   * Migrations
   * CRUD endpoints
   * Association table for companies
   * Permission rules
   * Frontend pages + components
3. **SU manual company creation endpoint** (`/api/v1/companies/su-create`) that bypasses payment.
4. **Mapping propagation** within a group.
5. **Tests** for all core flows.
6. **Documentation** update.

This feature is foundational to allow **Bob’s multi-company environment** to operate under a single “umbrella”, and to give the SU the power to create companies manually without payment.

---

# **SCOPE – What must be delivered**

### **Backend**

* CORS middleware properly configured
* SQLAlchemy models:

  * `GroupCompany`
  * `GroupCompanyMember`
* Alembic migration (with downgrade)
* Service layer:

  * create/list groups
  * add/remove company in group
  * propagate mappings
* API endpoints:

  * `GET /api/v1/groups`
  * `POST /api/v1/groups`
  * `GET /api/v1/groups/{id}`
  * `POST /api/v1/groups/{id}/companies`
  * `DELETE /api/v1/groups/{id}/companies/{company_id}`
  * `POST /api/v1/groups/{id}/propagate-mappings`
  * `POST /api/v1/companies/su-create` (restricted to superusers)
* Integration of group–company relationships across existing modules
* Tests (pytest) for:

  * CORS
  * group creation
  * manual SU company creation
  * group membership
  * mapping propagation

---

### **Frontend (React + TS + Tailwind/shadcn)**

* New pages:

  * `/groups` list
  * `/groups/:id` detail with company list, “Add Company”, “Create Company (SU)”, “Propagate Mappings”
* New components:

  * `GroupForm`
  * `AddCompanyToGroupDialog`
  * `SUCreateCompanyDialog`
* New API hooks under `src/lib/api/groups.ts`
* Updated router entries
* Clean, minimal shadcn layout; no breaking changes to existing pages

---

### **Documentation**

* New file: `docs/groups.md`

  * ER diagram
  * workflow of SU-create
  * API examples (cURL)
* Update main `README.md` with deployment instructions for the new modules

---

# **TASKS – Execute in this order**

---

## **Task A — Fix CORS**

File: `backend/app/main.py`

Add:

```py
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit:
`fix(cors): enable CORS for localhost:5173`

---

## **Task B — Database Models**

Create `backend/app/db/models/group_company.py`:

```py
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class GroupCompany(Base):
    __tablename__ = "group_companies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="owned_groups")
    members = relationship("GroupCompanyMember", back_populates="group", cascade="all, delete-orphan")
```

Create `backend/app/db/models/group_company_member.py`:

```py
import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class GroupCompanyMember(Base):
    __tablename__ = "group_company_members"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_company_id = Column(UUID(as_uuid=True), ForeignKey("group_companies.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    group = relationship("GroupCompany", back_populates="members")
    company = relationship("Company")
```

Register in `models/__init__.py`.

Commit:
`feat(groups): add GroupCompany and GroupCompanyMember models`

---

## **Task C — Migration**

Create alembic migration creating both tables and unique constraints.
Include downgrade removing both tables.

Commit:
`chore(migrations): create group companies tables`

---

## **Task D — Service Layer**

Create `backend/app/services/group_service.py` with:

* `create_group(...)`
* `get_groups_for_user(...)`
* `add_company_to_group(...)`
* `remove_company_from_group(...)`
* `propagate_mappings(...)`:

  * copy rows from `AccountMapping`
  * do not overwrite unless `force=True`
  * mark propagated rows with `propagated_from = source_company_id`
  * decrease confidence if copied

Commit:
`feat(groups): implement group service and mapping propagation`

---

## **Task E — API Endpoints**

Create router: `backend/app/api/v1/groups.py`

Endpoints:

* `GET /api/v1/groups`
* `POST /api/v1/groups`
* `GET /api/v1/groups/{group_id}`
* `POST /api/v1/groups/{group_id}/companies`
* `DELETE /api/v1/groups/{group_id}/companies/{company_id}`
* `POST /api/v1/groups/{group_id}/propagate-mappings`

Create **SU manual company creation**:

File: `backend/app/api/v1/companies_su.py`

Endpoint:
`POST /api/v1/companies/su-create`

Rules:

* Only `current_user.is_superuser == True`
* Creates a company with payment skipped
* If `group_company_id` provided → associate immediately

Commit:
`feat(api): add groups router and su-create company route`

---

## **Task F — Permissions**

Ensure only SU can use su-create route.
Ensure only SU or group owner can create groups.
Ensure group membership operations follow permission rules.

Commit:
`feat(auth): implement permission checks for groups and su-create`

---

## **Task G — Frontend**

Create:

`src/pages/groups/GroupsList.tsx`
`src/pages/groups/GroupDetail.tsx`
`src/components/groups/GroupForm.tsx`
`src/components/groups/AddCompanyToGroupDialog.tsx`
`src/components/groups/SUCreateCompanyDialog.tsx`

Add API client:

`src/lib/api/groups.ts`

Integrate router entries and nav links.

UI requirements:

* Use shadcn/ui components
* Keep consistent card-based layout
* Add “Consolidated Dashboard” placeholder button

Commit:
`feat(frontend): implement groups pages, dialogs, api hooks`

---

## **Task H — Tests**

Add:

`tests/test_groups.py`
`tests/test_su_create_company.py`
`tests/test_cors.py`

Commit:
`test(groups): add backend tests for groups, su-create, mappings and cors`

---

## **Task I — Documentation**

Add:

`docs/groups.md` with:

* ER diagram (mermaid or ascii)
* API examples (cURL)
* SU-create workflow
* Mapping propagation flow

Update `README.md`.

Commit:
`docs(groups): add groups.md and update README`

---

# **ACCEPTANCE CRITERIA**

1. Frontend at `localhost:5173` communicates with backend without CORS errors.
2. SU-create company works and bypasses payment.
3. GroupCompany CRUD and membership fully functional.
4. Mapping propagation works and is tested.
5. All migrations apply and rollback cleanly.
6. All new endpoints appear in OpenAPI.
7. Frontend pages render group list and group details with no errors.
8. All new tests pass.

---

# **FINAL OUTPUT REQUIRED FROM CLAUDE**

Return:

> “Branch `feature/group-company` created. All tasks completed. Commits summary, migrations, endpoints, tests, and documentation are ready. Provide PR for review.”


