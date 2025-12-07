# GroupCompany (Umbrella View) Documentation

## Overview

The GroupCompany feature allows users to manage multiple companies under a single "umbrella" group. This enables efficient management of related companies and facilitates account mapping propagation across all companies in the group.

## Key Features

1. **Group Management**: Create and manage groups of related companies
2. **Company Association**: Add/remove companies from groups
3. **Mapping Propagation**: Copy account mappings from one company to others in the group
4. **SU Manual Company Creation**: Superusers can create companies bypassing payment workflow

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ GROUP_COMPANY : owns
    GROUP_COMPANY ||--o{ GROUP_COMPANY_MEMBER : contains
    COMPANY ||--o{ GROUP_COMPANY_MEMBER : "member of"
    COMPANY ||--o{ ACCOUNT_MAPPING : has
    ACCOUNT_MAPPING }o--|| COMPANY : "propagated from"

    USER {
        uuid id PK
        string email
        boolean is_superuser
    }

    GROUP_COMPANY {
        uuid id PK
        string name UK
        text description
        uuid owner_user_id FK
        timestamp created_at
        timestamp updated_at
    }

    GROUP_COMPANY_MEMBER {
        uuid id PK
        uuid group_company_id FK
        uuid company_id FK
    }

    COMPANY {
        uuid id PK
        string name
        string ucid UK
        boolean is_active
        enum subscription_type
    }

    ACCOUNT_MAPPING {
        uuid id PK
        uuid company_account_id FK
        string master_code
        float confidence
        string status
        uuid propagated_from FK
        text notes
    }
```

---

## Database Schema

### `group_companies`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `name` | VARCHAR(255) | Unique group name |
| `description` | TEXT | Optional group description |
| `owner_user_id` | UUID | Foreign key to `users.id` |
| `created_at` | TIMESTAMP | Auto-generated creation timestamp |
| `updated_at` | TIMESTAMP | Auto-updated timestamp |

**Constraints:**
- UNIQUE: `name`
- FOREIGN KEY: `owner_user_id` → `users.id`

### `group_company_members`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `group_company_id` | UUID | Foreign key to `group_companies.id` |
| `company_id` | UUID | Foreign key to `companies.id` |

**Constraints:**
- UNIQUE: (`group_company_id`, `company_id`)
- FOREIGN KEY: `group_company_id` → `group_companies.id`
- FOREIGN KEY: `company_id` → `companies.id`

### Updates to `account_mappings`

Added column:
- `propagated_from` (UUID, nullable): Tracks the source company ID when a mapping is propagated

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

---

### 1. List Groups

**GET** `/groups`

List all groups owned by the current user (or all groups if superuser).

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Bob's Restaurant Group",
    "description": "All Bob's restaurant locations",
    "owner_user_id": "uuid",
    "created_at": "2025-12-07T10:00:00Z",
    "updated_at": "2025-12-07T10:00:00Z"
  }
]
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/groups \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 2. Create Group

**POST** `/groups`

Create a new group.

**Request Body:**
```json
{
  "name": "Bob's Restaurant Group",
  "description": "All Bob's restaurant locations"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Bob's Restaurant Group",
  "description": "All Bob's restaurant locations",
  "owner_user_id": "uuid",
  "created_at": "2025-12-07T10:00:00Z",
  "updated_at": null
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/groups \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob'\''s Restaurant Group",
    "description": "All Bob'\''s restaurant locations"
  }'
```

---

### 3. Get Group Details

**GET** `/groups/{group_id}`

Get group details with member companies.

**Response:**
```json
{
  "id": "uuid",
  "name": "Bob's Restaurant Group",
  "description": "All Bob's restaurant locations",
  "owner_user_id": "uuid",
  "created_at": "2025-12-07T10:00:00Z",
  "updated_at": "2025-12-07T10:00:00Z",
  "companies": [
    {
      "id": "uuid",
      "name": "Bob's Downtown",
      "ucid": "BD01",
      "email": "downtown@bobs.com",
      "is_active": true
    },
    {
      "id": "uuid",
      "name": "Bob's Uptown",
      "ucid": "BU01",
      "email": "uptown@bobs.com",
      "is_active": true
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/groups/GROUP_UUID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 4. Add Company to Group

**POST** `/groups/{group_id}/companies`

Add an existing company to a group.

**Request Body:**
```json
{
  "company_id": "uuid"
}
```

**Response:**
```json
{
  "message": "Company added to group successfully",
  "member_id": "uuid"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/groups/GROUP_UUID/companies \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "COMPANY_UUID"
  }'
```

---

### 5. Remove Company from Group

**DELETE** `/groups/{group_id}/companies/{company_id}`

Remove a company from a group.

**Response:**
```json
{
  "message": "Company removed from group successfully"
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/groups/GROUP_UUID/companies/COMPANY_UUID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 6. Propagate Mappings

**POST** `/groups/{group_id}/propagate-mappings`

Copy account mappings from a source company to other companies in the group.

**Request Body:**
```json
{
  "source_company_id": "uuid",
  "target_company_id": "uuid (optional, null = all companies)",
  "force": false
}
```

**Parameters:**
- `source_company_id` (required): Company to copy mappings from
- `target_company_id` (optional): Specific company to copy to (if null, copies to all)
- `force` (default: false): If true, overwrites existing mappings

**Behavior:**
- Copied mappings have confidence reduced by 10% (multiplied by 0.9)
- Minimum confidence after propagation is 0.5
- Mappings are marked with `status = "suggested"` and `propagated_from = source_company_id`
- Existing mappings are skipped unless `force = true`

**Response:**
```json
{
  "source_company_id": "uuid",
  "target_companies": 2,
  "source_mappings": 150,
  "created": 120,
  "updated": 10,
  "skipped": 20
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/groups/GROUP_UUID/propagate-mappings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_company_id": "SOURCE_COMPANY_UUID",
    "target_company_id": null,
    "force": false
  }'
```

---

### 7. SU Create Company (Superuser Only)

**POST** `/companies/su-create`

Manually create a company with NATIVE subscription (bypasses payment).

**Permissions:** Superuser only

**Request Body:**
```json
{
  "name": "Bob's New Location",
  "email": "new@bobs.com",
  "phone": "+1-555-1234",
  "address_line1": "123 Main St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "USA",
  "tax_id": "12-3456789",
  "industry": "Restaurant",
  "description": "New restaurant location",
  "group_company_id": "uuid (optional)"
}
```

**Note:** All fields except `name` are optional. If `group_company_id` is provided, the company is automatically added to that group.

**Response:**
```json
{
  "id": "uuid",
  "name": "Bob's New Location",
  "ucid": "BNL1",
  "email": "new@bobs.com",
  "subscription_type": "native",
  "is_active": true
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/companies/su-create \
  -H "Authorization: Bearer YOUR_SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob'\''s New Location",
    "email": "new@bobs.com",
    "group_company_id": "GROUP_UUID"
  }'
```

---

## Workflows

### Workflow 1: Create a Group with Companies

1. **Create Group:**
   ```bash
   POST /api/v1/groups
   {
     "name": "Bob's Restaurants",
     "description": "All Bob's locations"
   }
   ```

2. **Add Existing Companies:**
   ```bash
   POST /api/v1/groups/{group_id}/companies
   {
     "company_id": "COMPANY_1_UUID"
   }

   POST /api/v1/groups/{group_id}/companies
   {
     "company_id": "COMPANY_2_UUID"
   }
   ```

3. **Create New Company (SU):**
   ```bash
   POST /api/v1/companies/su-create
   {
     "name": "Bob's New Location",
     "group_company_id": "GROUP_UUID"
   }
   ```

---

### Workflow 2: Propagate Mappings

1. **Verify Company Mappings:**
   - Ensure the source company has confirmed or suggested account mappings

2. **Propagate to All Companies:**
   ```bash
   POST /api/v1/groups/{group_id}/propagate-mappings
   {
     "source_company_id": "SOURCE_COMPANY_UUID",
     "force": false
   }
   ```

3. **Propagate to Specific Company:**
   ```bash
   POST /api/v1/groups/{group_id}/propagate-mappings
   {
     "source_company_id": "SOURCE_COMPANY_UUID",
     "target_company_id": "TARGET_COMPANY_UUID",
     "force": false
   }
   ```

4. **Force Overwrite:**
   ```bash
   POST /api/v1/groups/{group_id}/propagate-mappings
   {
     "source_company_id": "SOURCE_COMPANY_UUID",
     "force": true
   }
   ```

---

## Permission Rules

### Group Operations

- **Create Group:** Any authenticated user can create a group (they become the owner)
- **View Group:** Only group owner or superuser
- **Modify Group:** Only group owner or superuser
- **Delete Group:** Only group owner or superuser

### SU Create Company

- **Permission:** Superuser only
- **Subscription Type:** Always `NATIVE` (bypasses payment workflow)
- **Group Association:** Optional; if provided, company is auto-added to group

---

## Frontend Integration

### Pages

1. **`/groups`** - GroupsList page
   - Lists all groups owned by user
   - Button to create new group
   - Cards showing group info

2. **`/groups/:groupId`** - GroupDetail page
   - Group details and description
   - List of member companies
   - Buttons to:
     - Add existing company
     - Create company (SU only)
     - Propagate mappings

### Components

1. **GroupForm** - Form to create/edit groups
2. **AddCompanyToGroupDialog** - Modal to add existing company
3. **SUCreateCompanyDialog** - Modal for SU to create company
4. **PropagateMappingsDialog** - Modal to configure mapping propagation

---

## Testing

Run the test suite:

```bash
cd backend
python -m pytest tests/test_groups.py -v
python -m pytest tests/test_su_create_company.py -v
python -m pytest tests/test_cors.py -v
```

---

## Migration

To apply the database migration:

```bash
cd backend
alembic upgrade head
```

To rollback:

```bash
alembic downgrade -1
```

---

## Use Case: Bob's Multi-Company Environment

Bob owns 5 restaurant locations, each set up as a separate company:

1. **Bob's Downtown** (UCID: BD01)
2. **Bob's Uptown** (UCID: BU01)
3. **Bob's Midtown** (UCID: BM01)
4. **Bob's Eastside** (UCID: BE01)
5. **Bob's Westside** (UCID: BW01)

### Solution with GroupCompany

1. Create "Bob's Restaurant Group"
2. Add all 5 companies to the group
3. Set up chart of accounts mappings for Bob's Downtown
4. Propagate mappings to all other locations
5. When adding a new location (Bob's Northside), use SU-create with `group_company_id` to auto-add it to the group

### Benefits

- Consistent chart of accounts across all locations
- Centralized management
- Easy onboarding of new locations
- Reduced manual mapping work

---

## Notes

- Group names must be unique
- A company can belong to multiple groups
- Propagated mappings retain source company ID for audit trail
- Confidence is reduced during propagation to indicate uncertainty
- SU-created companies have `subscription_type = NATIVE` (no Stripe payment required)

---

## Related Documentation

- [Company Registration](../README.md#company-registration)
- [Account Mapping](./mapping.md)
- [Superuser Panel](../README.md#administration)
