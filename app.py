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
from werkzeug.security import check_password_hash, generate_password_hash

# Local-demo defaults only — never use these in production.
DEFAULT_SECRET_KEY = "dev-only-secret-key"
DEFAULT_ADMIN_PASSWORD = "admin"
DEFAULT_DB_PATH = "monitoring.db"


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory (supports pytest with an isolated DB)."""
    app = Flask(__name__)

    # Optional .env for local demo; missing file is fine.
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
    )
    if test_config:
        app.config.update(test_config)

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
        """Create users table and seed hashed admin if missing."""
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
        username = app.config["ADMIN_USERNAME"]
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing is None:
            # Hash only — never store plaintext password.
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

    @app.route("/")
    @login_required
    def index():
        return render_template("index.html")

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
            # Generic message — do not reveal which field failed.
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

    # Expose helpers for tests
    app.get_db = get_db  # type: ignore[attr-defined]
    app.init_db = init_db  # type: ignore[attr-defined]

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    # Local demo only: bind to loopback, not 0.0.0.0
    app.run(host="127.0.0.1", port=5000, debug=True)
