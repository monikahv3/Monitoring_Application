"""Dashboard / detail route tests with mocked collectors."""

SECRET = "super-secret-ssh-password"


def test_dashboard_shows_metrics_without_secrets(auth_client):
    auth_client.post(
        "/servers/add",
        data={
            "display_name": "app-1",
            "host": "192.0.2.20",
            "port": "22",
            "ssh_username": "ops",
            "auth_type": "password",
            "password": SECRET,
        },
        follow_redirects=True,
    )
    response = auth_client.get("/")
    body = response.data.decode()
    assert response.status_code == 200
    assert "app-1" in body
    assert "OK" in body
    assert "12.5%" in body
    assert SECRET not in body


def test_detail_page_read_only_and_no_secrets(auth_client):
    auth_client.post(
        "/servers/add",
        data={
            "display_name": "app-2",
            "host": "192.0.2.21",
            "port": "22",
            "ssh_username": "ops",
            "auth_type": "password",
            "password": SECRET,
        },
        follow_redirects=True,
    )
    response = auth_client.get("/servers/1")
    body = response.data.decode()
    assert response.status_code == 200
    assert "app-2" in body
    assert "Listening ports" in body
    assert "sshd" in body
    assert SECRET not in body
    assert "credential_ref" not in body
    # Read-only: no remote-mutation forms beyond remove on dashboard
    assert 'name="password"' not in body


def test_detail_missing_server_redirects(auth_client):
    response = auth_client.get("/servers/999", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
