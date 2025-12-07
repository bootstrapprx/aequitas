import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.group_company import GroupCompany
from app.core.security import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_su_company.db"
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


@pytest.fixture(scope="function")
def client(db):
    """Create test client with db override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def superuser(db):
    """Create a test superuser"""
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("testpass"),
        is_superuser=True,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def regular_user(db):
    """Create a test regular user"""
    user = User(
        email="user@test.com",
        hashed_password=get_password_hash("testpass"),
        is_superuser=False,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers_su(client, superuser):
    """Get auth headers for superuser"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "testpass"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_regular(client, regular_user):
    """Get auth headers for regular user"""
    response = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "testpass"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_su_create_company_basic(client, auth_headers_su, db):
    """Test SU creating a company"""
    response = client.post(
        "/api/v1/companies/su-create",
        json={
            "name": "SU Test Company",
            "email": "test@company.com",
            "phone": "+1-555-1234"
        },
        headers=auth_headers_su
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SU Test Company"
    assert data["email"] == "test@company.com"
    assert data["subscription_type"] == "native"


def test_su_create_company_with_group(client, auth_headers_su, superuser, db):
    """Test SU creating a company and adding to group"""
    # Create a group first
    group = GroupCompany(
        name="Test Group",
        owner_user_id=superuser.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    response = client.post(
        "/api/v1/companies/su-create",
        json={
            "name": "SU Company with Group",
            "email": "test@company.com",
            "group_company_id": str(group.id)
        },
        headers=auth_headers_su
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SU Company with Group"

    # Verify company was added to group
    from app.db.models.group_company_member import GroupCompanyMember
    member = db.query(GroupCompanyMember).filter(
        GroupCompanyMember.group_company_id == group.id
    ).first()
    assert member is not None


def test_su_create_company_regular_user_denied(client, auth_headers_regular):
    """Test that regular users cannot use SU create endpoint"""
    response = client.post(
        "/api/v1/companies/su-create",
        json={
            "name": "Should Fail",
            "email": "fail@company.com"
        },
        headers=auth_headers_regular
    )

    assert response.status_code == 403
    assert "superuser" in response.json()["detail"].lower()


def test_su_create_company_unauthorized(client):
    """Test that unauthenticated requests are rejected"""
    response = client.post(
        "/api/v1/companies/su-create",
        json={
            "name": "Should Fail",
            "email": "fail@company.com"
        }
    )

    assert response.status_code == 401
