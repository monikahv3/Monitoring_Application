# Security notes — local demo only

**This application is not production software.** It is a local demo for internal walkthroughs. Do not expose it to the internet or use real production credentials.

## What is protected (demo-grade)

- Admin password is stored as a **Werkzeug hash** in SQLite (never plaintext).
- Flask sessions are signed with `SECRET_KEY`.
- Forms use **CSRF** tokens (Flask-WTF).
- Monitoring pages are **read-only**; only inventory add/remove mutates app state.
- SSH metric commands are **fixed strings** (no user-controlled shell concatenation).
- Templates do not render SSH passwords or key paths.
- The app binds to **`127.0.0.1`** by default.
- `.env`, `*.db`, and SSH key patterns are **gitignored**.

## Demo risks you must accept

| Risk | Detail |
|------|--------|
| SSH password in SQLite | For password auth, the demo stores the SSH password in the local DB so collection can run. Prefer **private key path** auth. Use disposable demo accounts only. |
| Host keys | Paramiko uses `AutoAddPolicy` (auto-trust unknown hosts). Convenient for demos; unsafe for production (MITM). |
| Local-only | Binding to localhost reduces exposure; do not rebind to `0.0.0.0` without additional controls. |
| Default secrets | Code includes local demo defaults for `SECRET_KEY` / admin password. Change them via `.env` before sharing a machine. |

## Credential handling

- **Key auth (preferred):** store only a filesystem path to a private key on the demo host.
- **Password auth:** stored in SQLite for demo convenience — treat the DB file as secret; never commit it.
- Never log passwords, key contents, or `.env` values.

## CI

GitHub Actions runs `pytest` with non-sensitive test env vars only. It does **not** upload `.env` or database artifacts, and does **not** talk to real SSH hosts (collectors are mocked).
