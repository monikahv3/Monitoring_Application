"""Demo Linux Server Monitoring — local Flask entry point."""

from __future__ import annotations

import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash

from metrics import collect_server_metrics

# Local-demo defaults only — never use these in production.
DEFAULT_SECRET_KEY = "dev-only-secret-key"
DEFAULT_ADMIN_PASSWORD = "admin"
DEFAULT_DB_PATH = "monitoring.db"
AUTO_REFRESH_SECONDS = 10


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory (supports pytest with an isolated DB)."""
    app = Flask(__name__)

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY),
        ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "admin"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
        DATABASE=os.environ.get("DATABASE", DEFAULT_DB_PATH),
        WTF_CSRF_ENABLED=True,
        AUTO_REFRESH_SECONDS=AUTO_REFRESH_SECONDS,
    )
    if test_config:
        app.config.update(test_config)

    csrf = CSRFProtect(app)

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc: BaseException | None = None) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db() -> None:
        """Create tables and seed hashed admin if missing."""
        db_path = Path(app.config["DATABASE"])
        if db_path.parent != Path("."):
            db_path.parent.mkdir(parents=True, exist_ok=True)

        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT,
                host TEXT NOT NULL,
                port INTEGER NOT NULL DEFAULT 22,
                ssh_username TEXT NOT NULL,
                auth_type TEXT NOT NULL CHECK(auth_type IN ('password', 'key')),
                credential_ref TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        username = app.config["ADMIN_USERNAME"]
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing is None:
            password_hash = generate_password_hash(app.config["ADMIN_PASSWORD"])
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
        db.commit()

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("user_id") is None:
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped

    def list_servers_safe() -> list[sqlite3.Row]:
        """Server rows for UI — never select credential_ref for templates."""
        return (
            get_db()
            .execute(
                """
                SELECT id, display_name, host, port, ssh_username, auth_type, created_at
                FROM servers
                ORDER BY id
                """
            )
            .fetchall()
        )

    def get_server_full(server_id: int) -> sqlite3.Row | None:
        return (
            get_db()
            .execute("SELECT * FROM servers WHERE id = ?", (server_id,))
            .fetchone()
        )

    def server_label(row: sqlite3.Row) -> str:
        name = (row["display_name"] or "").strip()
        return name or row["host"]

    def metrics_for_server(row: sqlite3.Row) -> dict:
        collector = app.config.get("METRICS_COLLECTOR") or collect_server_metrics
        server = {
            "host": row["host"],
            "port": row["port"],
            "ssh_username": row["ssh_username"],
            "auth_type": row["auth_type"],
            "credential_ref": row["credential_ref"],
        }
        return collector(server)

    @app.before_request
    def load_logged_in_user() -> None:
        user_id = session.get("user_id")
        g.user = None
        if user_id is not None:
            g.user = (
                get_db()
                .execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
                .fetchone()
            )

    @app.context_processor
    def inject_globals():
        return {
            "auto_refresh_seconds": app.config.get(
                "AUTO_REFRESH_SECONDS", AUTO_REFRESH_SECONDS
            ),
            "csrf_token": generate_csrf,
        }

    @app.route("/")
    @login_required
    def index():
        servers = list_servers_safe()
        summaries = []
        for row in servers:
            full = get_server_full(row["id"])
            metrics = metrics_for_server(full) if full else {
                "status": "error",
                "error": "Missing server",
            }
            summaries.append(
                {
                    "server": row,
                    "label": server_label(row),
                    "metrics": metrics,
                }
            )
        return render_template("index.html", summaries=summaries)

    @app.route("/servers/add", methods=["GET", "POST"])
    @login_required
    def add_server():
        errors: list[str] = []
        form = {
            "display_name": "",
            "host": "",
            "port": "22",
            "ssh_username": "",
            "auth_type": "password",
        }
        if request.method == "POST":
            form["display_name"] = (request.form.get("display_name") or "").strip()
            form["host"] = (request.form.get("host") or "").strip()
            form["port"] = (request.form.get("port") or "22").strip()
            form["ssh_username"] = (request.form.get("ssh_username") or "").strip()
            form["auth_type"] = (request.form.get("auth_type") or "password").strip()
            password = request.form.get("password") or ""
            key_path = (request.form.get("key_path") or "").strip()

            if not form["host"]:
                errors.append("Host / IP is required.")
            if not form["ssh_username"]:
                errors.append("SSH username is required.")
            try:
                port = int(form["port"])
                if port < 1 or port > 65535:
                    raise ValueError
            except ValueError:
                errors.append("SSH port must be an integer from 1 to 65535.")
                port = 22

            if form["auth_type"] not in ("password", "key"):
                errors.append("Auth type must be password or key.")
            elif form["auth_type"] == "password":
                if not password:
                    errors.append("SSH password is required for password auth.")
                credential_ref = password
            else:
                if not key_path:
                    errors.append("Private key path is required for key auth.")
                credential_ref = key_path

            if not errors:
                get_db().execute(
                    """
                    INSERT INTO servers
                      (display_name, host, port, ssh_username, auth_type, credential_ref)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        form["display_name"] or None,
                        form["host"],
                        port,
                        form["ssh_username"],
                        form["auth_type"],
                        credential_ref,
                    ),
                )
                get_db().commit()
                flash("Server added.", "success")
                return redirect(url_for("index"))

        return render_template("server_form.html", form=form, errors=errors)

    @app.route("/servers/<int:server_id>/remove", methods=["POST"])
    @login_required
    def remove_server(server_id: int):
        row = get_server_full(server_id)
        if row is None:
            flash("Server not found.", "warning")
            return redirect(url_for("index"))
        get_db().execute("DELETE FROM servers WHERE id = ?", (server_id,))
        get_db().commit()
        flash(f"Removed {server_label(row)}.", "info")
        return redirect(url_for("index"))

    @app.route("/servers/<int:server_id>")
    @login_required
    def server_detail(server_id: int):
        row = get_server_full(server_id)
        if row is None:
            flash("Server not found.", "warning")
            return redirect(url_for("index"))
        # Safe view model — omit credential_ref
        safe = {
            "id": row["id"],
            "display_name": row["display_name"],
            "host": row["host"],
            "port": row["port"],
            "ssh_username": row["ssh_username"],
            "auth_type": row["auth_type"],
        }
        metrics = metrics_for_server(row)
        return render_template(
            "server_detail.html",
            server=safe,
            label=server_label(row),
            metrics=metrics,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id") is not None:
            return redirect(url_for("index"))

        error = None
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = (
                get_db()
                .execute(
                    "SELECT id, username, password_hash FROM users WHERE username = ?",
                    (username,),
                )
                .fetchone()
            )
            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Invalid username or password."
            else:
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("index"))

        return render_template("login.html", error=error)

    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        session.clear()
        flash("Signed out.", "info")
        return redirect(url_for("login"))

    app.get_db = get_db  # type: ignore[attr-defined]
    app.init_db = init_db  # type: ignore[attr-defined]
    app.csrf = csrf  # type: ignore[attr-defined]

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    # Local demo only: bind to loopback, not 0.0.0.0
    app.run(host="127.0.0.1", port=5000, debug=True)
