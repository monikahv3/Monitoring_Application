# Demo Monitoring Infrastructure — Product Requirements Document (PRD)

**Product:** Demo Linux Server Monitoring  
**Type:** Local demo application  
**Audience:** Internal L1 / L2 / L3 infrastructure and application teams  
**Status:** Draft for demo implementation  

---

## 1. Problem

Teams must SSH into Linux servers to check live memory, CPU, network, disk, load, and port usage. There is no shared, read-only UI for quick visibility.

## 2. Goal

Provide a **local, minimal** Flask web app that:

- Lets an admin sign in and register Linux servers
- Collects live metrics over SSH
- Shows a user-friendly, read-only monitoring UI for internal teams

This is a **demo only**, intended to run on the same machine where Cursor is running. Keep scope small and steps few.

## 3. Users & Access

| Role | Who | Capabilities |
|------|-----|--------------|
| Admin | Default single user (`admin`) | Sign in, add/remove servers, view metrics |
| Viewer (same login for demo) | L1 / L2 / L3 / app teams | View metrics only in the UI (monitoring screens are read-only) |

- Single user: username `admin`
- Password stored as a **hash** (not plain text)
- No multi-user roles or SSO for this demo

## 4. Core Features

### Feature 1 — Read-only monitoring UI

- Clean, simple Bootstrap UI
- Dashboard lists registered servers and key live stats
- Server detail view shows full metrics
- Monitoring pages are **read-only** (no edits to metrics or OS config)
- Only server inventory management (add/remove) is writable, and only after admin login

### Feature 2 — Sign-in

- Login page with username + password
- Default username: `admin`
- Password verified against a stored hash
- Session required for all app pages after login
- No “change password” UI in this demo (seed/configure at setup)

### Feature 3 — Add Linux servers to monitor

Admin can add a Linux server with:

| Field | Required | Notes |
|-------|----------|--------|
| Hostname / IP | Yes | Target host |
| SSH port | Yes | Default `22` |
| SSH username | Yes | Remote login user |
| SSH auth | Yes | Password **or** private key path/content |
| Display name / label | Optional | Friendly name in UI |

Admin can remove a registered server from monitoring.

## 5. Metrics (live only)

Collected **on demand / on refresh** via SSH. No long-term history store.

| Metric | Display |
|--------|---------|
| CPU | Usage % |
| Memory | Used / available (and %) |
| Network | RX / TX (simple rates or counters as available) |
| Listening ports | Port + process/service if available |
| Disk | Usage per mount (used / total / %) |
| Load average | 1 / 5 / 15 minute |

**Refresh:** Auto-refresh every **5–10 seconds** on monitoring views (also allow manual refresh).

## 6. Technical Approach

| Area | Choice |
|------|--------|
| Language | Python |
| Web | Flask + Jinja templates |
| UI | Bootstrap (attractive, simple) |
| DB | SQLite (servers + admin password hash) |
| Collection | SSH from the Flask host to each Linux server |
| Deploy | Local: `python app.py` (or equivalent) |
| Platform | Linux servers only |

### Minimal local run (target)

1. Install dependencies (`pip install -r requirements.txt`)
2. Ensure SQLite DB is created/seeded with hashed `admin` password
3. Start app: `python app.py`
4. Open browser to local URL (e.g. `http://127.0.0.1:5000`)
5. Sign in as `admin` and add reachable Linux servers

No Docker Compose required for this demo.

## 7. Non-Functional Requirements

- **Demo-grade reliability:** Best-effort collection; show clear error if SSH/metrics fail
- **Security (demo-appropriate):** Hashed password; do not log secrets; SSH credentials stored only as needed for the demo (document risk)
- **Usability:** Readable cards/tables; status indicators (OK / unreachable / error)
- **Performance:** Suitable for a small number of demo servers; avoid blocking the whole UI if one host is slow (timeouts)

## 8. Out of Scope

- Alerts / notifications
- Multi-user roles / RBAC
- Windows hosts
- Long-term historical reports / charts history
- Public or external API for other tools
- Docker Compose packaging
- Agent installed on remote hosts
- Password-change UI
- Production hardening (HA, audit logs, vault, etc.)

## 9. Success Criteria (Demo)

- Admin can sign in with hashed-password verification
- Admin can add and remove Linux servers with SSH details
- UI shows live CPU, memory, network, ports, disk, and load average
- Views auto-refresh every 5–10 seconds
- Monitoring UI remains read-only aside from server add/remove
- App runs locally with Python + Flask + SQLite in a few steps

## 10. Open Items (optional later)

- Exact SSH library (e.g. Paramiko) and remote commands for each metric
- Default admin password value for local seed
- Exact auto-refresh interval (pick **5s** or **10s** during implementation)
