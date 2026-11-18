# Demo Linux Server Monitoring

Local demo Flask app for **read-only** Linux server metrics over SSH. **Local demo only — not for production.** Use disposable demo credentials only.

Docs: [requirements.md](docs/requirements.md) · [TODO.md](docs/TODO.md) · [security.md](docs/security.md)

## Quick start

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # optional; demo defaults work without it
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) → sign in as **`admin` / `admin`** (or your `.env` values) → **Add server**.

The app binds to `127.0.0.1` only.

## Environment variables

| Variable | Purpose | Local demo default |
|----------|---------|--------------------|
| `SECRET_KEY` | Flask session signing | `dev-only-secret-key` |
| `ADMIN_USERNAME` | Seeded admin username | `admin` |
| `ADMIN_PASSWORD` | Seed password (hashed on first DB init) | `admin` |
| `DATABASE` | SQLite path | `monitoring.db` |

Never commit `.env` or real passwords. `ADMIN_PASSWORD` applies only when the admin row is missing (delete the DB to re-seed).

## Servers & credentials

Add a host with hostname/IP, SSH port (default 22), username, and either:

- **Private key path** (preferred), or
- **SSH password** (stored in local SQLite for this demo — see [security.md](docs/security.md))

Dashboard lists servers and live summary stats; detail pages show CPU, memory, load, disk, network counters, and listening ports. Remove uses `POST` with confirm. Credential fields are never shown in the UI after save.

## Metrics & SSH

- Live collection on page load / refresh via **Paramiko** (read-only remote commands).
- Auto-refresh every **10 seconds** on dashboard and detail pages (plus manual Refresh).
- Demo host-key policy: **AutoAdd** (not for production). Details in [security.md](docs/security.md).

Remote commands (fixed): `/proc/stat`, `free -b`, `/proc/loadavg`, `df -PB1`, `/proc/net/dev`, `ss`.

## UI stack

Flask + Jinja + Bootstrap 5 (CDN). Status badges: OK / Unreachable / Error.

## Tests

```bash
pytest
```

Covers auth, server CRUD (including “credentials not rendered”), and metrics parsers with **mocked SSH** (no real hosts). Suitable for CI.

## CI

GitHub Actions (`.github/workflows/ci.yml`) on push/PR: install deps, run `pytest`. Validates auth/UI/metrics unit tests only — **not** live SSH. No secrets or DB artifacts are uploaded.
