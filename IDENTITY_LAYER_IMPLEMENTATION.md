# Identity Layer Implementation

## Overview
This document describes the implementation of a foundational identity layer for the Aequitas accounting system. The implementation ensures proper user-company relationships, authentication with company context, and a complete sign-up flow.

## Implementation Summary

### Backend Changes

#### 1. User Model Updates (`backend/app/db/models/user.py`)
- **Added `user_uid`**: A unique, user-facing identifier (UUIDv4) distinct from internal `id`
- **Added `preferred_company_id`**: Stores the user's preferred/default company context
- Both fields are indexed for performance

#### 2. Company UCID Generation
- ✅ Already implemented in `backend/app/core/ucid.py`
- UCID generation is deterministic based on normalized company name
- Synced to frontend via CompanyResponse schema

#### 3. User ↔ Company Relationship Enforcement
**File**: `backend/app/services/user_service.py`
- Modified `create_user()` to require company assignment
- Users cannot be created without at least one company (except for initial sign-up flow)
- Automatically creates `UserCompany` associations during user creation
- Sets `preferred_company_id` to first assigned company

#### 4. Authentication Updates
**Files**:
- `backend/app/api/v1/auth.py`
- `backend/app/schemas/user.py`

**Changes**:
- JWT now includes: `company_ids`, `preferred_company_id`, `is_superuser`
- Login endpoints (`/login`, `/login-json`) return company information
- Token schema updated to include company fields
- Registration endpoint supports two modes:
  - **Initial Sign-Up**: Creates company + user + admin permissions
  - **Join Existing**: Assigns user to existing company(ies)

#### 5. New API Endpoint
**Endpoint**: `GET /api/v1/companies/{company_id}/users`
**File**: `backend/app/api/v1/companies.py`

Returns all users assigned to a specific company with their permissions.

#### 6. Database Migration
**File**: `backend/migration_identity_layer.sql`

Adds new fields and populates existing data:
```sql
-- Adds user_uid (with auto-generated UUIDs)
-- Adds preferred_company_id (set to first company for existing users)
-- Creates indexes for performance
```

### Frontend Changes

#### 1. Type Definitions (`frontend/src/types/user.ts`)
- Updated `User` interface to include:
  - `user_uid: string`
  - `preferred_company_id?: string`
- Updated `UserCreate` to support:
  - `company_ids?: string[]`
  - `is_initial_signup?: boolean`
  - `company_name?: string`
- Added `LoginResponse` interface with company fields

#### 2. AuthContext Updates (`frontend/src/contexts/AuthContext.tsx`)
**New State**:
- `companyIds: string[]` - List of companies user has access to
- `currentCompanyId: string | null` - Active company context

**New Methods**:
- `switchCompany(companyId: string)` - Switch active company context
- Enhanced `register()` to support both sign-up modes
- Enhanced `login()` to fetch and store company context

**Storage**:
- Persists company context to localStorage
- Keys: `chartforge_company_ids`, `chartforge_current_company`

#### 3. Registration Flow (`frontend/src/pages/auth/RegisterPage.tsx`)
**Two-Mode Sign-Up**:
1. **Create Company Tab**:
   - User provides email, password, and company name
   - System creates company with auto-generated CUID
   - User becomes admin of new company

2. **Join Company Tab**:
   - User provides email, password, and existing CUID
   - Note: Full implementation requires CUID lookup (marked as coming soon)

#### 4. Companies Page - User Display
**New Component**: `frontend/src/components/manual/companies/CompanyUsers.tsx`

Features:
- Collapsible user list for each company
- Shows all users with access to the company
- Displays user email, UID, and superuser status
- Lazy-loads users only when expanded
- Integrated into `CompaniesList.tsx`

## Migration Instructions

### 1. Apply Database Migration
```bash
cd backend
psql $DATABASE_URL -f migration_identity_layer.sql
```

Or connect to PostgreSQL and run the migration manually:
```bash
make dev  # Ensure services are running
docker exec -i aequitas-postgres-1 psql -U user -d chartforge_dev < backend/migration_identity_layer.sql
```

### 2. Restart Services
```bash
make stop
make dev
```

The FastAPI backend will automatically recognize the model changes.

### 3. Test the Implementation
1. **Test Initial Sign-Up**:
   - Navigate to `/register`
   - Select "Create Company" tab
   - Enter email, password, and company name
   - Verify company is created with CUID
   - Verify user is logged in with company context

2. **Test Login**:
   - Login with existing user
   - Check browser localStorage for company context
   - Verify JWT includes company information

3. **Test Company Users Display**:
   - Navigate to `/companies`
   - Click arrow to expand user list for a company
   - Verify users are displayed correctly

4. **Test Company Switching** (via browser console):
   ```javascript
   // Access AuthContext via React DevTools or:
   const { switchCompany } = useAuth();
   switchCompany('company-id-here');
   ```

## API Changes Summary

### Modified Endpoints

#### POST `/api/v1/auth/register`
**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123",

  // For initial sign-up:
  "is_initial_signup": true,
  "company_name": "Acme Corp"

  // OR for joining existing:
  "company_ids": ["uuid-1", "uuid-2"]
}
```

#### POST `/api/v1/auth/login-json`
**Response**:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "company_ids": ["uuid-1", "uuid-2"],
  "preferred_company_id": "uuid-1"
}
```

#### GET `/api/v1/auth/me`
**Response**:
```json
{
  "id": "uuid",
  "user_uid": "uuid-v4-string",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "preferred_company_id": "company-uuid",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

### New Endpoints

#### GET `/api/v1/companies/{company_id}/users`
**Response**:
```json
[
  {
    "id": "uuid",
    "user_uid": "uuid-v4-string",
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "preferred_company_id": "company-uuid",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
]
```

## Security Considerations

### Company Access Control
- Regular users can only access companies they're assigned to via `UserCompany` table
- Superusers (`is_superuser=True`) bypass company access restrictions
- JWT includes `company_ids` for frontend filtering
- Backend enforces access via `check_company_access()` dependency (existing)

### User Enforcement
- New users MUST be assigned to at least one company (unless initial sign-up)
- UserService validates company assignment during creation
- Prevents orphaned users without company access

### Preferred Company
- Stored in user record for convenience
- User can override via `switchCompany()`
- Not security-critical (user can only switch to accessible companies)

## Data Model

```
User
├── id (UUID, PK)
├── user_uid (VARCHAR, UNIQUE) ← NEW
├── email (VARCHAR, UNIQUE)
├── hashed_password (VARCHAR)
├── is_active (BOOLEAN)
├── is_superuser (BOOLEAN)
├── preferred_company_id (UUID, FK → companies.id) ← NEW
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

UserCompany (Junction Table)
├── id (UUID, PK)
├── user_id (UUID, FK → users.id)
├── company_id (UUID, FK → companies.id)
├── is_admin (BOOLEAN)
├── can_edit (BOOLEAN)
├── can_view (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

Company
├── id (UUID, PK)
├── name (VARCHAR)
├── ucid (VARCHAR, UNIQUE)
├── is_active (BOOLEAN)
└── ... (other fields)
```

## Backward Compatibility

### Existing Users
- Migration automatically generates `user_uid` for existing users
- Migration sets `preferred_company_id` to first accessible company
- No manual intervention required

### Existing Companies
- UCID generation was already implemented
- No changes needed

### Existing API Clients
- Login endpoints remain backward compatible
- New fields are additive (optional in responses)
- Old tokens still work (company fields optional in JWT)

## Future Enhancements

1. **Join Existing Company Flow**:
   - Implement CUID → Company ID lookup
   - Add company discovery/search endpoint
   - Require admin approval for joining

2. **Company Switching UI**:
   - Add company selector dropdown in navbar
   - Show current active company
   - Persist selection across sessions

3. **Multi-Company Dashboard**:
   - Aggregate view across all accessible companies
   - Company-specific data filtering

4. **User Management UI**:
   - Invite users to company
   - Manage user-company permissions
   - Remove users from company

5. **Audit Trail**:
   - Log company switches
   - Track user-company assignment changes
   - Monitor cross-company access patterns

## Files Modified

### Backend
- `backend/app/db/models/user.py`
- `backend/app/schemas/user.py`
- `backend/app/services/user_service.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/companies.py`
- `backend/migration_identity_layer.sql` (new)

### Frontend
- `frontend/src/types/user.ts`
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/pages/auth/RegisterPage.tsx`
- `frontend/src/components/manual/companies/CompaniesList.tsx`
- `frontend/src/components/manual/companies/CompanyUsers.tsx` (new)

## Testing Checklist

- [ ] Database migration runs successfully
- [ ] Existing users get `user_uid` populated
- [ ] Existing users get `preferred_company_id` set
- [ ] New user registration (create company) works
- [ ] Login returns company information
- [ ] JWT includes company_ids
- [ ] `/companies/{id}/users` endpoint returns users
- [ ] Companies page displays user list
- [ ] Company users can be expanded/collapsed
- [ ] Superuser can access all companies
- [ ] Regular user sees only assigned companies
- [ ] Registration requires company information
- [ ] Cannot create user without company assignment

## Rollback Plan

If issues arise, rollback via:

```sql
BEGIN;
ALTER TABLE users DROP COLUMN IF EXISTS user_uid;
ALTER TABLE users DROP COLUMN IF EXISTS preferred_company_id;
DROP INDEX IF EXISTS idx_users_user_uid;
COMMIT;
```

Then revert code changes via git:
```bash
git stash  # or git reset --hard <previous-commit>
```

## Support

For issues or questions:
1. Check backend logs: `make logs`
2. Check database state: `psql $DATABASE_URL`
3. Verify migration applied: `SELECT user_uid FROM users LIMIT 1;`
4. Test API via Swagger: `http://localhost:8000/docs`

---

**Implementation Date**: 2025-12-03
**Version**: 1.0
**Status**: ✅ Complete
