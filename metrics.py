"""Live Linux metrics via fixed SSH commands (read-only).

All remote command strings are fixed constants — never built from user input.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from ssh_client import SSHError, run_command

# Fixed read-only remote commands only.
CMD_CPU = "grep '^cpu ' /proc/stat"
CMD_MEM = "free -b"
CMD_LOAD = "cat /proc/loadavg"
CMD_DISK = "df -PB1"
CMD_NET = "cat /proc/net/dev"
CMD_PORTS = "ss -lntup 2>/dev/null || ss -lntu 2>/dev/null"

MAX_DISK_MOUNTS = 20
MAX_PORTS = 50


def parse_cpu(stdout: str) -> Optional[float]:
    """Approximate CPU busy % from cumulative /proc/stat since boot."""
    for line in stdout.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            values = [int(x) for x in parts[1:8]]
            total = sum(values)
            idle = values[3]
            if total <= 0:
                return None
            return round((1.0 - idle / total) * 100.0, 1)
    return None


def parse_memory(stdout: str) -> Optional[dict[str, Any]]:
    total = used = available = None
    for line in stdout.splitlines():
        if line.startswith("Mem:"):
            cols = line.split()
            # free -b: total used free shared buff/cache available
            if len(cols) >= 7:
                total = int(cols[1])
                used = int(cols[2])
                available = int(cols[6])
            elif len(cols) >= 4:
                total = int(cols[1])
                used = int(cols[2])
                available = int(cols[3])
            break
    if total is None or used is None:
        return None
    percent = round(used / total * 100.0, 1) if total else 0.0
    return {
        "total": total,
        "used": used,
        "available": available if available is not None else max(total - used, 0),
        "percent": percent,
    }


def parse_load(stdout: str) -> Optional[dict[str, float]]:
    parts = stdout.strip().split()
    if len(parts) < 3:
        return None
    return {"1": float(parts[0]), "5": float(parts[1]), "15": float(parts[2])}


def parse_disk(stdout: str) -> list[dict[str, Any]]:
    mounts: list[dict[str, Any]] = []
    lines = stdout.splitlines()
    for line in lines[1:]:  # skip header
        cols = line.split()
        if len(cols) < 6:
            continue
        filesystem, blocks, used, _avail, pct, mount = cols[0], cols[1], cols[2], cols[3], cols[4], cols[5]
        if filesystem.startswith("tmpfs") or filesystem.startswith("devtmpfs"):
            continue
        if not mount.startswith("/"):
            continue
        try:
            total_b = int(blocks)
            used_b = int(used)
            percent = float(pct.rstrip("%"))
        except ValueError:
            continue
        mounts.append(
            {
                "mount": mount,
                "filesystem": filesystem,
                "total": total_b,
                "used": used_b,
                "percent": percent,
            }
        )
        if len(mounts) >= MAX_DISK_MOUNTS:
            break
    return mounts


def parse_network(stdout: str) -> list[dict[str, Any]]:
    ifaces: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if ":" not in line or line.strip().startswith("Inter") or line.strip().startswith("face"):
            continue
        name, rest = line.split(":", 1)
        name = name.strip()
        if name == "lo":
            continue
        cols = rest.split()
        if len(cols) < 9:
            continue
        try:
            rx_bytes = int(cols[0])
            tx_bytes = int(cols[8])
        except ValueError:
            continue
        ifaces.append({"iface": name, "rx_bytes": rx_bytes, "tx_bytes": tx_bytes})
    return ifaces


def parse_ports(stdout: str) -> list[dict[str, Any]]:
    ports: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line or line.startswith("Netid") or line.startswith("State"):
            continue
        cols = line.split()
        if len(cols) < 5:
            continue
        proto = cols[0]
        local = cols[4]
        if ":" not in local:
            continue
        port_s = local.rsplit(":", 1)[-1]
        try:
            port = int(port_s)
        except ValueError:
            continue
        process = None
        if len(cols) >= 6 and "users:(" in line:
            # e.g. users:(("sshd",pid=123,fd=3))
            try:
                process = line.split('("', 1)[1].split('"', 1)[0]
            except IndexError:
                process = None
        ports.append({"proto": proto, "port": port, "process": process})
        if len(ports) >= MAX_PORTS:
            break
    return ports


Runner = Callable[..., Any]


def collect_server_metrics(
    server: dict[str, Any],
    *,
    runner: Runner = run_command,
) -> dict[str, Any]:
    """Collect live metrics for one server dict. Never logs credentials."""
    password = None
    key_filename = None
    if server.get("auth_type") == "key":
        key_filename = server.get("credential_ref") or None
    else:
        password = server.get("credential_ref") or None

    def _run(command: str):
        return runner(
            host=server["host"],
            port=int(server["port"]),
            username=server["ssh_username"],
            command=command,
            password=password,
            key_filename=key_filename,
        )

    try:
        cpu_r = _run(CMD_CPU)
        mem_r = _run(CMD_MEM)
        load_r = _run(CMD_LOAD)
        disk_r = _run(CMD_DISK)
        net_r = _run(CMD_NET)
        ports_r = _run(CMD_PORTS)
    except SSHError as exc:
        return {
            "status": "unreachable",
            "error": str(exc),
            "cpu_percent": None,
            "memory": None,
            "load": None,
            "disk": [],
            "network": [],
            "ports": [],
        }

    try:
        return {
            "status": "ok",
            "error": None,
            "cpu_percent": parse_cpu(cpu_r.stdout),
            "memory": parse_memory(mem_r.stdout),
            "load": parse_load(load_r.stdout),
            "disk": parse_disk(disk_r.stdout),
            "network": parse_network(net_r.stdout),
            "ports": parse_ports(ports_r.stdout),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "error": f"Parse error: {exc.__class__.__name__}",
            "cpu_percent": None,
            "memory": None,
            "load": None,
            "disk": [],
            "network": [],
            "ports": [],
        }
