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
            "WTF_CSRF_ENABLED": False,
            # Avoid live SSH in unit/integration tests by default
            "METRICS_COLLECTOR": lambda _server: {
                "status": "ok",
                "error": None,
                "cpu_percent": 12.5,
                "memory": {
                    "total": 8_000_000_000,
                    "used": 2_000_000_000,
                    "available": 6_000_000_000,
                    "percent": 25.0,
                },
                "load": {"1": 0.1, "5": 0.2, "15": 0.3},
                "disk": [
                    {
                        "mount": "/",
                        "filesystem": "/dev/sda1",
                        "total": 100_000_000_000,
                        "used": 40_000_000_000,
                        "percent": 40.0,
                    }
                ],
                "network": [{"iface": "eth0", "rx_bytes": 1000, "tx_bytes": 2000}],
                "ports": [{"proto": "tcp", "port": 22, "process": "sshd"}],
            },
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post(
        "/login",
        data={"username": "admin", "password": "test-password"},
    )
    return client
