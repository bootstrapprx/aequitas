# Identity Layer Implementation - Final Report

## Overview
Complete implementation of a secure, admin-controlled identity layer for the Aequitas accounting system. This implementation ensures proper user-company relationships with strict access controls.

## Key Changes from Initial Implementation

### Security Enhancement: Admin-Only User Creation
Public registration has been **DISABLED**. Users can only be created by:
1. **SuperUsers** - Can create users for any company and create new companies
2. **Company Admins** - Can create users only for companies they administer

This prevents unauthorized access and ensures proper oversight of user account creation.

## Complete Implementation

### Backend Changes

#### 1. User Model (`backend/app/db/models/user.py:12,17`)
```python
user_uid = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
preferred_company_id = Column(UUID(as_uuid=True), nullable=True)
```

#### 2. Disabled Public Registration (`backend/app/api/v1/auth.py:73-87`)
```python
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, deprecated=True)
def register(...):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public registration is disabled. Please contact your administrator to create an account."
    )
```

#### 3. Admin-Only User Creation (`backend/app/api/v1/users.py:40-137`)
**Permissions**:
- SuperUsers: Create users for any company, create new companies with users
- Company Admins: Create users only for companies they admin

**Two Creation Modes**:
1. **Initial Sign-Up** (SuperUser only):
   - Creates new company with UCID
   - Creates admin user
   - Assigns user as company admin

2. **Add to Existing Company**:
   - Requires `company_ids` list
   - SuperUsers can add to any company
   - Company Admins can only add to companies they admin

#### 4. Company Access Filtering (`backend/app/api/v1/companies.py:13-46`)
```python
# Filter by user access (unless superuser)
if not current_user.is_superuser:
    permission_service = PermissionService(db)
    user_company_ids = [
        uc.company_id for uc in permission_service.get_user_companies(current_user.id)
    ]
    all_companies = [c for c in all_companies if c.id in user_company_ids]
```

Regular users now only see companies they're assigned to.

#### 5. Company Users Endpoint (`backend/app/api/v1/companies.py:146-172`)
```
GET /api/v1/companies/{company_id}/users
```
Returns all users with access to a specific company.

### Frontend Changes

#### 1. Disabled Public Registration Page (`frontend/src/pages/auth/RegisterPage.tsx`)
Now displays:
- Clear message that registration is disabled
- Instructions to contact administrators
- Link to login page

#### 2. Enhanced User Management UI (`frontend/src/components/users/UserForm.tsx`)
**SuperUser Features**:
- Two-tab interface: "Add to Existing Company" vs "Create New Company"
- Create New Company: Enter company name, auto-generates UCID
- Add to Existing: Select from available companies (checkboxes)

**Company Admin Features**:
- Can only see companies they admin
- Can assign new users to those companies
- Cannot create new companies

#### 3. Company Users Display (`frontend/src/components/manual/companies/CompanyUsers.tsx`)
- Collapsible list under each company
- Shows user email, UID, and superuser status
- Lazy-loads on expand

#### 4. Updated Types (`frontend/src/types/user.ts`)
```typescript
interface User {
  id: string;
  user_uid: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  preferred_company_id?: string;
  created_at: string;
  updated_at: string;
}

interface UserCreate {
  email: string;
  password: string;
  company_ids?: string[];
  is_initial_signup?: boolean;
  company_name?: string;
}
```

### Database Migration

**File**: `backend/migration_identity_layer.sql`

```sql
-- Add user_uid column
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_uid VARCHAR UNIQUE NOT NULL DEFAULT gen_random_uuid()::text;

-- Add preferred_company_id column
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_company_id UUID REFERENCES companies(id) ON DELETE SET NULL;

-- Populate existing users
UPDATE users SET user_uid = gen_random_uuid()::text WHERE user_uid IS NULL;
UPDATE users u SET preferred_company_id = fc.company_id
FROM first_companies fc
WHERE u.id = fc.user_id AND u.preferred_company_id IS NULL;
```

## Permission Matrix

| Action | SuperUser | Company Admin | Regular User |
|--------|-----------|---------------|--------------|
| Create users for any company | ✅ | ❌ | ❌ |
| Create new company with user | ✅ | ❌ | ❌ |
| Create users for their companies | ✅ | ✅ | ❌ |
| View all companies | ✅ | ❌ | ❌ |
| View assigned companies only | - | ✅ | ✅ |
| Manage company settings | ✅ | ✅ (their companies) | ❌ |
| Public registration | ❌ | ❌ | ❌ |

## API Changes Summary

### Modified Endpoints

#### POST `/api/v1/auth/register` ⚠️ DEPRECATED
Now returns 403 Forbidden. Use `POST /api/v1/users/` instead.

#### POST `/api/v1/users/` ✅ ADMIN ONLY
**Permissions**: SuperUser OR Company Admin

**Request (Add to Existing)**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "company_ids": ["uuid-1", "uuid-2"]
}
```

**Request (Create New Company - SuperUser Only)**:
```json
{
  "email": "admin@newcompany.com",
  "password": "password123",
  "is_initial_signup": true,
  "company_name": "New Company Inc."
}
```

#### GET `/api/v1/companies/` 🔒 FILTERED
- SuperUsers: See all companies
- Regular Users: See only assigned companies

#### POST `/api/v1/auth/login-json`
**Response** (unchanged):
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "company_ids": ["uuid-1"],
  "preferred_company_id": "uuid-1"
}
```

### New Endpoints

#### GET `/api/v1/companies/{company_id}/users`
Returns list of users assigned to the company.

## Deployment Instructions

### 1. Apply Database Migration
```bash
cd backend
psql $DATABASE_URL -f migration_identity_layer.sql
```

Or via Docker:
```bash
docker exec -i aequitas-postgres-1 psql -U user -d chartforge_dev < backend/migration_identity_layer.sql
```

### 2. Restart Services
```bash
make stop
make dev
```

### 3. First-Time Setup

#### Option A: Use Default Superuser
The system creates a default superuser on first startup:
- Email: `admin@aequitas.local`
- Password: `admin123`

**⚠️ IMPORTANT**: Change this password immediately after first login!

#### Option B: Create Superuser Manually
```python
from app.db.session import SessionLocal
from app.services.user_service import UserService
from app.schemas.user import UserCreate

db = SessionLocal()
user_service = UserService(db)
user = user_service.create_user(
    UserCreate(email="your-admin@example.com", password="your-secure-password")
)
user.is_superuser = True
db.commit()
```

### 4. Create Companies and Users

**As SuperUser**:
1. Navigate to `/users`
2. Click "Add User"
3. Select "Create New Company" tab
4. Enter company name and first admin user details
5. Submit - company and admin user will be created

**As Company Admin**:
1. Navigate to `/users`
2. Click "Add User"
3. Select companies from the list
4. Enter new user details
5. Submit - user will be added to selected companies

## Testing Checklist

### Database Migration
- [ ] Migration runs successfully
- [ ] Existing users get `user_uid` populated
- [ ] Existing users get `preferred_company_id` set
- [ ] Indexes are created

### Authentication & Authorization
- [ ] Public registration returns 403
- [ ] SuperUser can create users for any company
- [ ] SuperUser can create new companies with users
- [ ] Company Admin can create users for their companies
- [ ] Company Admin cannot create users for other companies
- [ ] Regular user cannot access user creation

### Company Filtering
- [ ] SuperUser sees all companies
- [ ] Regular user sees only assigned companies
- [ ] Companies list updates when user is assigned/unassigned

### User Management UI
- [ ] SuperUser sees two-tab form (Create Company / Add to Existing)
- [ ] Company Admin sees only company selection
- [ ] User creation succeeds with proper company assignment
- [ ] User list displays user_uid
- [ ] Company users list shows under each company
- [ ] Company users list is collapsible

### Data Integrity
- [ ] User cannot be created without company assignment
- [ ] UserCompany associations are created correctly
- [ ] Preferred company is set appropriately
- [ ] JWT includes company_ids and preferred_company_id

## Security Considerations

### Authentication
- Public registration is disabled to prevent unauthorized access
- All user creation requires authentication and authorization
- Password minimum length: 8 characters
- Passwords are hashed with bcrypt

### Authorization
- Company-level access control via `UserCompany` table
- Regular users can only access assigned companies
- Company admins can only create users for companies they admin
- SuperUsers bypass all restrictions (use sparingly)

### Data Protection
- `user_uid` provides external identifier (not internal UUID)
- Company filtering prevents data leakage across companies
- Preferred company is user preference only (not security-critical)

## Rollback Plan

If critical issues arise:

```sql
BEGIN;
ALTER TABLE users DROP COLUMN IF EXISTS user_uid;
ALTER TABLE users DROP COLUMN IF EXISTS preferred_company_id;
DROP INDEX IF EXISTS idx_users_user_uid;
COMMIT;
```

Then revert code:
```bash
git stash  # or git reset --hard <commit-before-changes>
make stop && make dev
```

## Files Modified

### Backend
- `backend/app/db/models/user.py`
- `backend/app/schemas/user.py`
- `backend/app/services/user_service.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/users.py`
- `backend/app/api/v1/companies.py`
- `backend/migration_identity_layer.sql` (new)

### Frontend
- `frontend/src/types/user.ts`
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/pages/auth/RegisterPage.tsx`
- `frontend/src/pages/users/UsersPage.tsx`
- `frontend/src/components/users/UserForm.tsx`
- `frontend/src/components/users/UsersList.tsx`
- `frontend/src/components/manual/companies/CompaniesList.tsx`
- `frontend/src/components/manual/companies/CompanyUsers.tsx` (new)

## Future Enhancements

1. **Email Invitations**: Send email invites to new users
2. **User Approval Workflow**: Require admin approval for sensitive roles
3. **Audit Trail**: Log all user creation/deletion events
4. **Company Transfer**: Allow transferring users between companies
5. **Bulk User Import**: CSV import for multiple users
6. **Password Reset**: Self-service password reset flow
7. **2FA/MFA**: Two-factor authentication for enhanced security

## Support & Troubleshooting

### Common Issues

**Issue**: "User must be assigned to at least one company"
- **Solution**: Select at least one company when creating user

**Issue**: "You are not an admin of company X"
- **Solution**: Company admins can only create users for companies they admin. Contact a SuperUser.

**Issue**: "Public registration is disabled"
- **Solution**: This is expected. Contact your administrator to create an account.

**Issue**: Companies list is empty for company admin
- **Solution**: Ensure user has `is_admin=True` for at least one company via UserCompany table.

### Logs & Debugging
```bash
# View backend logs
make logs

# Check database state
psql $DATABASE_URL
SELECT id, email, user_uid, is_superuser FROM users;
SELECT user_id, company_id, is_admin FROM user_companies;

# Test API
curl http://localhost:8000/docs
```

---

**Implementation Date**: 2025-12-03
**Version**: 2.0 (Admin-Controlled)
**Status**: ✅ Complete and Secure
