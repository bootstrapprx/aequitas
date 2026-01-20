"""
Tests for PermissionService permission check methods.
"""
import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.user_company import UserCompany
from app.services.permission_service import PermissionService
from app.core.security import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_permissions.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def permission_service(db):
    """Create a PermissionService instance"""
    return PermissionService(db)


@pytest.fixture
def test_company(db):
    """Create a test company"""
    company = Company(
        name="Test Company",
        email="test@company.com",
        ucid="TEST"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def superuser(db):
    """Create a superuser"""
    user = User(
        email="superuser@test.com",
        hashed_password=get_password_hash("testpass"),
        is_superuser=True,
        is_active=True,
        role="SU"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def council_member(db):
    """Create a council member user"""
    user = User(
        email="council@test.com",
        hashed_password=get_password_hash("testpass"),
        is_superuser=False,
        is_active=True,
        role="COUNCIL_MEMBER"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db):
    """Create a regular user"""
    user = User(
        email="user@test.com",
        hashed_password=get_password_hash("testpass"),
        is_superuser=False,
        is_active=True,
        role="USER"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("testpass"),
        is_superuser=False,
        is_active=True,
        role="ADMIN"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ========================================
# can_view_company tests
# ========================================

def test_can_view_company_superuser(permission_service, superuser, test_company):
    """Superuser can view any company"""
    assert permission_service.can_view_company(superuser.id, test_company.id) is True


def test_can_view_company_council_member_requires_membership(permission_service, council_member, test_company):
    """Council member without membership cannot view company"""
    assert permission_service.can_view_company(council_member.id, test_company.id) is False


def test_can_view_company_authorized_user(permission_service, regular_user, test_company, db):
    """User with can_view=True can view company"""
    # Create UserCompany relationship with can_view=True
    user_company = UserCompany(
        user_id=regular_user.id,
        company_id=test_company.id,
        can_view=True,
        can_edit=False,
        is_admin=False
    )
    db.add(user_company)
    db.commit()

    assert permission_service.can_view_company(regular_user.id, test_company.id) is True


def test_can_view_company_unauthorized_user(permission_service, regular_user, test_company):
    """User without UserCompany relationship cannot view"""
    assert permission_service.can_view_company(regular_user.id, test_company.id) is False


def test_can_view_company_no_view_permission(permission_service, regular_user, test_company, db):
    """User with can_view=False cannot view"""
    # Create UserCompany relationship with can_view=False
    user_company = UserCompany(
        user_id=regular_user.id,
        company_id=test_company.id,
        can_view=False,
        can_edit=False,
        is_admin=False
    )
    db.add(user_company)
    db.commit()

    assert permission_service.can_view_company(regular_user.id, test_company.id) is False


def test_can_view_company_nonexistent_user(permission_service, test_company):
    """Non-existent user cannot view"""
    fake_user_id = uuid.uuid4()
    assert permission_service.can_view_company(fake_user_id, test_company.id) is False


def test_can_view_company_nonexistent_company(permission_service, regular_user):
    """Permission check on non-existent company returns False"""
    fake_company_id = uuid.uuid4()
    assert permission_service.can_view_company(regular_user.id, fake_company_id) is False


# ========================================
# can_manage_company tests
# ========================================

def test_can_manage_company_superuser(permission_service, superuser, test_company):
    """Superuser can manage any company"""
    assert permission_service.can_manage_company(superuser.id, test_company.id) is True


def test_can_manage_company_council_member_requires_admin(permission_service, council_member, test_company):
    """Council member without admin membership cannot manage company"""
    assert permission_service.can_manage_company(council_member.id, test_company.id) is False


def test_can_manage_company_company_admin(permission_service, admin_user, test_company, db):
    """User with is_admin=True can manage company"""
    # Create UserCompany relationship with is_admin=True
    user_company = UserCompany(
        user_id=admin_user.id,
        company_id=test_company.id,
        can_view=True,
        can_edit=True,
        is_admin=True
    )
    db.add(user_company)
    db.commit()

    assert permission_service.can_manage_company(admin_user.id, test_company.id) is True


def test_can_manage_company_regular_user_no_admin(permission_service, regular_user, test_company, db):
    """Regular user with is_admin=False cannot manage"""
    # Create UserCompany relationship with is_admin=False
    user_company = UserCompany(
        user_id=regular_user.id,
        company_id=test_company.id,
        can_view=True,
        can_edit=True,
        is_admin=False
    )
    db.add(user_company)
    db.commit()

    assert permission_service.can_manage_company(regular_user.id, test_company.id) is False


def test_can_manage_company_unauthorized_user(permission_service, regular_user, test_company):
    """User without UserCompany relationship cannot manage"""
    assert permission_service.can_manage_company(regular_user.id, test_company.id) is False


def test_can_manage_company_nonexistent_user(permission_service, test_company):
    """Non-existent user cannot manage"""
    fake_user_id = uuid.uuid4()
    assert permission_service.can_manage_company(fake_user_id, test_company.id) is False


def test_can_manage_company_nonexistent_company(permission_service, regular_user):
    """Permission check on non-existent company returns False"""
    fake_company_id = uuid.uuid4()
    assert permission_service.can_manage_company(regular_user.id, fake_company_id) is False


# ========================================
# Edge cases and security tests
# ========================================

def test_permissions_deny_by_default(permission_service, regular_user, test_company):
    """Both permission methods deny by default"""
    assert permission_service.can_view_company(regular_user.id, test_company.id) is False
    assert permission_service.can_manage_company(regular_user.id, test_company.id) is False


def test_manage_does_not_imply_view_without_explicit_flag(permission_service, regular_user, test_company, db):
    """is_admin=True alone doesn't grant view access if can_view=False"""
    user_company = UserCompany(
        user_id=regular_user.id,
        company_id=test_company.id,
        can_view=False,  # Explicitly no view
        can_edit=False,
        is_admin=True    # But is admin
    )
    db.add(user_company)
    db.commit()

    # Can manage (because is_admin=True)
    assert permission_service.can_manage_company(regular_user.id, test_company.id) is True
    # Cannot view (because can_view=False)
    assert permission_service.can_view_company(regular_user.id, test_company.id) is False
