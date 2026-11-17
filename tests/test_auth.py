"""Auth unit tests: login, logout, protection, hashed passwords."""

LOGIN_PASSWORD = "test-password"


def test_protected_route_redirects_when_anonymous(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_successful_login(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": LOGIN_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    body = dashboard.data.decode()
    assert "Dashboard" in body
    assert LOGIN_PASSWORD not in body


def test_failed_login_generic_error(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.data.decode()
    assert "Invalid username or password." in body
    # Must not echo the attempted password in the response body.
    assert "wrong-password" not in body

    # Still unauthenticated
    protected = client.get("/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_logout_clears_session(client):
    client.post("/login", data={"username": "admin", "password": LOGIN_PASSWORD})
    assert client.get("/").status_code == 200

    logout = client.post("/logout", follow_redirects=False)
    assert logout.status_code == 302
    assert "/login" in logout.headers["Location"]

    protected = client.get("/")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_password_stored_hashed_not_plaintext(app):
    with app.app_context():
        row = app.get_db().execute(
            "SELECT username, password_hash FROM users WHERE username = ?",
            ("admin",),
        ).fetchone()

    assert row is not None
    assert row["username"] == "admin"
    assert row["password_hash"] != LOGIN_PASSWORD
    assert LOGIN_PASSWORD not in row["password_hash"]
    # Werkzeug scrypt/pbkdf2 hashes include a method prefix
    assert row["password_hash"].startswith(("scrypt:", "pbkdf2:"))
