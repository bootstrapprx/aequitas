import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_settings_require_a_strong_secret():
    with pytest.raises(ValidationError):
        Settings(APP_ENV="production", SECRET_KEY="dev_key", _env_file=None)


def test_non_test_settings_require_a_secret():
    with pytest.raises(ValidationError):
        Settings(APP_ENV="development", SECRET_KEY="", _env_file=None)


def test_production_rejects_mock_payments():
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV="production",
            SECRET_KEY="s" * 32,
            ALLOW_MOCK_PAYMENTS=True,
            _env_file=None,
        )


def test_production_accepts_explicit_secure_settings():
    settings = Settings(
        APP_ENV="production",
        SECRET_KEY="s" * 32,
        OAUTH_STATE_SECRET="o" * 32,
        _env_file=None,
    )

    assert settings.SECRET_KEY == "s" * 32
    assert settings.ALLOW_MOCK_PAYMENTS is False
