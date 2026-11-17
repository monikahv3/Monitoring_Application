# Demo Linux Server Monitoring

Local demo Flask app for read-only Linux server metrics over SSH. **Local demo only** — not for production.

## UI stack

Flask + Bootstrap 5 (CDN).

## Environment variables

Copy `.env.example` to `.env` for local overrides (optional). Demo defaults exist in code for convenience — **local use only**, never for real deployments.

| Variable | Purpose | Local demo default |
|----------|---------|--------------------|
| `SECRET_KEY` | Flask session signing | `dev-only-secret-key` |
| `ADMIN_USERNAME` | Seeded admin username | `admin` |
| `ADMIN_PASSWORD` | Seed password (hashed into SQLite on first init) | `admin` |
| `DATABASE` | SQLite file path | `monitoring.db` |

`ADMIN_PASSWORD` is applied only when the admin user row does not exist yet. Change it before first run, or delete the DB to re-seed. Never commit `.env` or real passwords.

## Run locally

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

The app binds to `127.0.0.1` by default (loopback only). Unauthenticated requests redirect to `/login`.

## Sign-in

1. Open the app → you are redirected to `/login`.
2. Sign in as **`admin`** with the seed password (`admin` unless you set `ADMIN_PASSWORD` before first DB init).
3. Dashboard is session-protected; use **Sign out** to clear the session (`POST /logout`).

Passwords are stored as Werkzeug hashes in SQLite only — never plaintext.

## Tests

```bash
source venv/bin/activate
pytest
```
