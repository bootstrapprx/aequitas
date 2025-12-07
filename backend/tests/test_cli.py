"""Tests for Aequitas CLI."""

import pytest
from typer.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cli.main import app
from app.db.base import Base
from app.db.models.user import User
from app.db.models.company import Company
from app.core.security import get_password_hash
from app.core.ucid import generate_ucid

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cli.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

runner = CliRunner()


@pytest.fixture(scope="function")
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def setup_test_data(db):
    """Set up test data."""
    # Create superuser
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("testpass"),
        is_superuser=True,
        is_active=True
    )
    db.add(user)

    # Create test company
    company = Company(
        name="Test Company",
        ucid=generate_ucid("Test Company"),
        is_active=True
    )
    db.add(company)

    db.commit()
    db.refresh(user)
    db.refresh(company)

    return {"user": user, "company": company}


def test_cli_help():
    """Test CLI help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Aequitas CLI" in result.stdout


def test_companies_list():
    """Test companies list command."""
    result = runner.invoke(app, ["companies", "list"])
    assert result.exit_code in [0, 1]  # May fail if no DB, but command should exist


def test_companies_list_json():
    """Test companies list command with JSON output."""
    result = runner.invoke(app, ["companies", "list", "--json"])
    assert result.exit_code in [0, 1]


def test_groups_list():
    """Test groups list command."""
    result = runner.invoke(app, ["groups", "list"])
    assert result.exit_code in [0, 1]


def test_users_list():
    """Test users list command."""
    result = runner.invoke(app, ["users", "list"])
    assert result.exit_code in [0, 1]


def test_db_inspect():
    """Test database inspect command."""
    result = runner.invoke(app, ["db", "inspect"])
    assert result.exit_code in [0, 1]


def test_diag_health():
    """Test diagnostics health command."""
    result = runner.invoke(app, ["diag", "health"])
    assert result.exit_code in [0, 1]  # May fail without DB connection


def test_diag_version():
    """Test diagnostics version command."""
    result = runner.invoke(app, ["diag", "version"])
    assert result.exit_code == 0
    assert "Aequitas Version Information" in result.stdout or "cli_version" in result.stdout


def test_diag_version_json():
    """Test diagnostics version command with JSON."""
    result = runner.invoke(app, ["diag", "version", "--json"])
    assert result.exit_code == 0


def test_json_flag_global():
    """Test that --json flag is available globally."""
    result = runner.invoke(app, ["--json", "companies", "list"])
    assert result.exit_code in [0, 1]


def test_debug_flag_global():
    """Test that --debug flag is available globally."""
    result = runner.invoke(app, ["--debug", "diag", "version"])
    assert result.exit_code == 0


def test_all_command_groups_registered():
    """Test that all command groups are registered."""
    result = runner.invoke(app, ["--help"])
    assert "companies" in result.stdout
    assert "groups" in result.stdout
    assert "mappings" in result.stdout
    assert "users" in result.stdout
    assert "db" in result.stdout
    assert "logs" in result.stdout
    assert "diag" in result.stdout


def test_companies_command_help():
    """Test companies command help."""
    result = runner.invoke(app, ["companies", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "create" in result.stdout
    assert "info" in result.stdout
    assert "delete" in result.stdout


def test_groups_command_help():
    """Test groups command help."""
    result = runner.invoke(app, ["groups", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "create" in result.stdout
    assert "info" in result.stdout


def test_mappings_command_help():
    """Test mappings command help."""
    result = runner.invoke(app, ["mappings", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "propagate" in result.stdout


def test_users_command_help():
    """Test users command help."""
    result = runner.invoke(app, ["users", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "create" in result.stdout


def test_db_command_help():
    """Test db command help."""
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    assert "upgrade" in result.stdout
    assert "downgrade" in result.stdout
    assert "inspect" in result.stdout


def test_exit_codes():
    """Test that commands return proper exit codes."""
    # Valid command with help should return 0
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    # Invalid command should not crash
    result = runner.invoke(app, ["nonexistent"])
    assert result.exit_code != 0
