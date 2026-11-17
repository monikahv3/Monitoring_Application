"""Pytest fixtures for the monitoring demo app."""

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.db"
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "test-password",
            "DATABASE": str(db_path),
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
