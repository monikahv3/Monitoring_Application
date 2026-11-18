# Implementation TODO — Demo Linux Server Monitoring

Incremental checklist for AI-assisted development. Complete items **in order**. Each step should stay small, include a **security** note and a **docs** update, and leave the app runnable locally.

**PRD:** [requirements.md](./requirements.md)

---

## Phase 0 — Project initialization & basic UI

### 0.1 Scaffold the project
- [x] Create app layout: `app.py` (or `app/` package), `templates/`, `static/`, `tests/`, `docs/`
- [x] Add `requirements.txt` with Flask (pin versions lightly for demo)
- [x] Add `.gitignore` (venv, `__pycache__`, `.env`, `*.db`, secrets)
- [x] **Security:** Ensure `.env`, SQLite DB, and SSH key paths are gitignored
- [x] **Docs:** Add root `README.md` with one-line purpose and “local demo only”

### 0.2 Minimal Flask app that starts
- [x] Create Flask app entry that serves `GET /` with a simple “Monitoring Demo” page
- [x] Confirm local run: `python app.py` → `http://127.0.0.1:5000`
- [x] **Security:** Bind to `127.0.0.1` by default (not `0.0.0.0`) for local demo
- [x] **Docs:** Document start command and URL in `README.md`

### 0.3 Basic Bootstrap UI shell
- [x] Add Bootstrap (CDN is fine for demo) base layout template
- [x] Add nav bar with app name; empty dashboard placeholder
- [x] Style a clean, readable landing/dashboard shell (no metrics yet)
- [x] **Security:** Use HTTPS CDN integrity attributes if practical; no inline secrets in templates
- [x] **Docs:** Note UI stack (Flask + Bootstrap) in `README.md`

---

## Phase 1 — Sign-in & unit tests

### 1.1 Config & secrets baseline
- [x] Load `SECRET_KEY` and admin seed password from environment (with safe local defaults documented)
- [x] Add example `.env.example` (no real secrets)
- [x] **Security:** Never commit real passwords; document that demo defaults are for local use only
- [x] **Docs:** Document required env vars in `README.md`

### 1.2 SQLite + hashed admin user
- [x] Add SQLite init (user table: username, password_hash)
- [x] Seed default user `admin` with **hashed** password (e.g. Werkzeug `generate_password_hash`)
- [x] **Security:** Store only password hashes; never store or log plaintext passwords
- [x] **Docs:** Document default username and how to set the seed password locally

### 1.3 Login / logout routes
- [x] Add login page (`GET/POST /login`) and logout (`POST` or `GET /logout`)
- [x] Verify username/password against hash; create session on success
- [x] Protect dashboard: redirect unauthenticated users to login
- [x] **Security:** Use Flask sessions with `SECRET_KEY`; constant-time hash check via library helpers; generic login error message (don’t reveal which field failed)
- [x] **Docs:** Document login flow and default `admin` user in `README.md`

### 1.4 Unit tests for auth
- [x] Add `pytest` (+ Flask test client) to `requirements.txt` / test deps
- [x] Tests: successful login, failed login, logout clears session, protected route redirects
- [x] Test that password is stored hashed (not plaintext) in DB
- [x] **Security:** Assert plaintext password never appears in DB or response bodies
- [x] **Docs:** Document how to run tests: `pytest`

---

## Phase 2 — CI/CD (GitHub Actions)

### 2.1 Basic CI workflow
- [x] Add `.github/workflows/ci.yml`
- [x] On push/PR: checkout, set up Python, install deps, run `pytest`
- [x] **Security:** No secrets in workflow logs; use env only for non-sensitive test config
- [x] **Docs:** Short “CI” section in `README.md` describing what Actions runs

### 2.2 Keep CI green for demo
- [x] Ensure tests pass without real SSH hosts (mock later collectors)
- [x] Pin/cache Python deps in Actions for speed (optional, keep minimal)
- [x] **Security:** Do not upload DB files or `.env` as artifacts
- [x] **Docs:** Note that CI validates auth/UI smoke tests only (not live SSH)

---

## Phase 3 — Server inventory (add / remove)

### 3.1 Server model & migrations-lite
- [x] SQLite table for servers: display name, host, SSH port, SSH username, auth type, credential reference
- [x] **Security:** Do not store SSH passwords/keys in plaintext if avoidable; prefer env/path reference; document demo risk if storing locally
- [x] **Docs:** Document server fields and credential handling in `docs/` or `README.md`

### 3.2 Add-server form (admin session required)
- [x] UI form to add Linux server (host/IP, port default 22, user, password or key path, optional label)
- [x] Validate inputs (required fields, port range)
- [x] **Security:** CSRF protection (Flask-WTF or equivalent); authorize only logged-in session; never echo secrets back into HTML
- [x] **Docs:** Document how to add a server locally

### 3.3 List & remove servers
- [x] Dashboard list of registered servers (no live metrics yet)
- [x] Remove-server action with confirm
- [x] **Security:** Mutations require session; use POST for delete; confirm intent
- [x] **Docs:** Update screenshots/notes for list/remove

### 3.4 Unit tests for server CRUD
- [x] Tests: add server (authenticated), reject unauthenticated add/remove, list servers, remove server
- [x] **Security:** Tests ensure credential fields are not rendered in list view
- [x] **Docs:** Mention CRUD tests under test instructions

---

## Phase 4 — SSH metrics collection (live only)

### 4.1 SSH client wrapper
- [x] Add Paramiko (or chosen SSH lib) dependency
- [x] Small helper: connect with timeout, run command, return stdout/stderr/exit
- [x] **Security:** Timeouts; do not log passwords/keys; prefer key file paths; host key policy documented (demo may use AutoAdd with clear warning)
- [x] **Docs:** Document SSH approach and demo host-key warning

### 4.2 Collect CPU & memory
- [x] Remote commands/parsing for CPU % and memory used/available
- [x] Return structured dict; map SSH failures to clear error status
- [x] **Security:** Use fixed command strings (no user-controlled shell concatenation)
- [x] **Docs:** Note which remote commands are used

### 4.3 Collect load average & disk
- [x] Load average (1/5/15) and disk usage per mount
- [x] **Security:** Same fixed-command rule; sanitize/limit mounts shown if huge
- [x] **Docs:** Update metrics list

### 4.4 Collect network & listening ports
- [x] Network RX/TX and listening ports (+ process if available)
- [x] **Security:** Read-only remote commands only; no remote writes
- [x] **Docs:** Update metrics list

### 4.5 Unit tests with mocked SSH
- [x] Mock SSH helper; test parsers and error handling without real hosts
- [x] **Security:** Fixtures must not contain real credentials
- [x] **Docs:** Note that metrics tests are mocked in CI

---

## Phase 5 — Read-only monitoring UI

### 5.1 Dashboard live summary
- [x] For each server, show key live stats (or unreachable/error badge)
- [x] Auto-refresh every 5–10s (pick one, e.g. 10s) + manual refresh
- [x] **Security:** Session required; no credential leakage in HTML/JSON
- [x] **Docs:** Document refresh behavior

### 5.2 Server detail page (read-only)
- [x] Full metrics view: CPU, memory, network, ports, disk, load
- [x] Clear empty/error states
- [x] **Security:** Read-only page; no forms that change remote state
- [x] **Docs:** Document detail page contents

### 5.3 UI polish (demo-minimal)
- [x] Status indicators (OK / unreachable / error), readable tables/cards
- [x] **Security:** Escape all server-provided strings in templates (Jinja autoescape on)
- [x] **Docs:** Brief UI overview in `README.md`

### 5.4 Integration-style tests (local)
- [x] Test detail/dashboard routes with mocked collectors
- [x] **Security:** Assert responses never include SSH passwords/keys
- [x] **Docs:** How to run full test suite

---

## Phase 6 — Hardening, docs wrap-up, demo checklist

### 6.1 Demo security pass
- [x] Review: hashed passwords, gitignore, bind localhost, no secrets in logs/templates, CSRF on forms
- [x] Add short `docs/security.md` (demo caveats: credential storage, host keys, local-only)
- [x] **Security:** Explicit “not production” warning
- [x] **Docs:** Link `docs/security.md` from `README.md`

### 6.2 Final local run docs
- [x] Trim `README.md` to minimal steps: venv → install → env → run → login → add server
- [x] Confirm PRD success criteria covered
- [x] **Security:** Remind users to use disposable demo credentials only
- [x] **Docs:** Cross-link `requirements.md`, `TODO.md`, `security.md`

### 6.3 CI final check
- [x] Confirm GitHub Actions workflow still runs lint/tests (tests at minimum)
- [x] **Security:** No secret values in workflow files
- [x] **Docs:** CI badge optional; keep README CI note accurate


---

## Suggested implementation order (summary)

1. Phase 0 — init + basic UI  
2. Phase 1 — sign-in + unit tests  
3. Phase 2 — GitHub Actions CI  
4. Phase 3 — add/remove servers  
5. Phase 4 — SSH metrics  
6. Phase 5 — monitoring UI + refresh  
7. Phase 6 — security/docs wrap-up  

---

## Out of scope (do not add TODO work)

- Alerts / notifications  
- Multi-user roles  
- Windows hosts  
- Long-term history / reports  
- External public API  
- Docker Compose  
- Remote agents  
- Password-change UI  
