"""Server inventory CRUD tests."""

SECRET_PASSWORD = "ssh-demo-secret-password"
SECRET_KEY_PATH = "/tmp/demo-only-id_ed25519"


def _add_server(client, **overrides):
    data = {
        "display_name": "web-1",
        "host": "10.0.0.5",
        "port": "22",
        "ssh_username": "monitor",
        "auth_type": "password",
        "password": SECRET_PASSWORD,
        "key_path": "",
    }
    data.update(overrides)
    return client.post("/servers/add", data=data, follow_redirects=True)


def test_add_server_authenticated(auth_client):
    response = _add_server(auth_client)
    assert response.status_code == 200
    body = response.data.decode()
    assert "web-1" in body
    assert "10.0.0.5" in body
    assert SECRET_PASSWORD not in body


def test_list_servers_hides_credentials(auth_client, app):
    _add_server(auth_client)
    response = auth_client.get("/")
    body = response.data.decode()
    assert "web-1" in body
    assert SECRET_PASSWORD not in body
    assert "credential_ref" not in body

    with app.app_context():
        row = app.get_db().execute(
            "SELECT credential_ref FROM servers WHERE host = ?", ("10.0.0.5",)
        ).fetchone()
    assert row["credential_ref"] == SECRET_PASSWORD


def test_unauthenticated_add_redirects(client):
    response = client.post(
        "/servers/add",
        data={
            "host": "10.0.0.5",
            "port": "22",
            "ssh_username": "monitor",
            "auth_type": "password",
            "password": SECRET_PASSWORD,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unauthenticated_remove_redirects(client):
    response = client.post("/servers/1/remove", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_remove_server(auth_client):
    _add_server(auth_client)
    listed = auth_client.get("/")
    assert b"web-1" in listed.data
    assert b"10.0.0.5" in listed.data

    removed = auth_client.post("/servers/1/remove", follow_redirects=True)
    assert removed.status_code == 200
    body = removed.data.decode()
    assert "Removed web-1." in body
    # Host row gone from inventory (name may still appear in flash)
    assert "10.0.0.5" not in body
    assert "No servers registered yet." in body



def test_add_server_key_auth_hides_path_in_list(auth_client):
    response = _add_server(
        auth_client,
        auth_type="key",
        password="",
        key_path=SECRET_KEY_PATH,
        display_name="db-1",
    )
    body = response.data.decode()
    assert "db-1" in body
    assert SECRET_KEY_PATH not in body
