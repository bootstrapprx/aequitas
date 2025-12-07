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
from app.db.models.group_company_member import GroupCompanyMember
from app.core.security import get_password_hash
from app.core.ucid import generate_ucid
import uuid

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_groups.db"
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


@pytest.fixture(scope="function")
def test_company(db):
    """Create a test company"""
    company = Company(
        name="Test Company",
        ucid=generate_ucid("Test Company"),
        is_active=True
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def test_create_group(client, auth_headers_su, superuser):
    """Test creating a group"""
    response = client.post(
        "/api/v1/groups",
        json={
            "name": "Test Group",
            "description": "A test group"
        },
        headers=auth_headers_su
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Group"
    assert data["description"] == "A test group"
    assert data["owner_user_id"] == str(superuser.id)


def test_list_groups(client, auth_headers_su, superuser, db):
    """Test listing groups"""
    # Create a group
    group = GroupCompany(
        name="Test Group 1",
        owner_user_id=superuser.id
    )
    db.add(group)
    db.commit()

    response = client.get("/api/v1/groups", headers=auth_headers_su)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(g["name"] == "Test Group 1" for g in data)


def test_get_group_detail(client, auth_headers_su, superuser, db, test_company):
    """Test getting group details with members"""
    # Create a group
    group = GroupCompany(
        name="Test Group",
        owner_user_id=superuser.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    # Add company to group
    member = GroupCompanyMember(
        group_company_id=group.id,
        company_id=test_company.id
    )
    db.add(member)
    db.commit()

    response = client.get(f"/api/v1/groups/{group.id}", headers=auth_headers_su)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Group"
    assert len(data["companies"]) == 1
    assert data["companies"][0]["name"] == "Test Company"


def test_add_company_to_group(client, auth_headers_su, superuser, db, test_company):
    """Test adding a company to a group"""
    # Create a group
    group = GroupCompany(
        name="Test Group",
        owner_user_id=superuser.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    response = client.post(
        f"/api/v1/groups/{group.id}/companies",
        json={"company_id": str(test_company.id)},
        headers=auth_headers_su
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Company added to group successfully"


def test_remove_company_from_group(client, auth_headers_su, superuser, db, test_company):
    """Test removing a company from a group"""
    # Create a group with a company
    group = GroupCompany(
        name="Test Group",
        owner_user_id=superuser.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    member = GroupCompanyMember(
        group_company_id=group.id,
        company_id=test_company.id
    )
    db.add(member)
    db.commit()

    response = client.delete(
        f"/api/v1/groups/{group.id}/companies/{test_company.id}",
        headers=auth_headers_su
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Company removed from group successfully"


def test_permissions_regular_user(client, auth_headers_regular, regular_user, db):
    """Test that regular users can create their own groups"""
    response = client.post(
        "/api/v1/groups",
        json={
            "name": "User Group",
            "description": "Created by regular user"
        },
        headers=auth_headers_regular
    )

    assert response.status_code == 200
    data = response.json()
    assert data["owner_user_id"] == str(regular_user.id)


def test_unauthorized_access(client):
    """Test that unauthenticated requests are rejected"""
    response = client.get("/api/v1/groups")
    assert response.status_code == 401
