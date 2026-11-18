"""SSH helper for live metric collection (local demo only).

Host key policy: AutoAddPolicy — convenient for demos, NOT for production.
See docs/security.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import paramiko


DEFAULT_TIMEOUT_SECONDS = 8


@dataclass
class SSHResult:
    stdout: str
    stderr: str
    exit_code: int


class SSHError(Exception):
    """Raised when an SSH connection or command fails."""


def run_command(
    *,
    host: str,
    port: int,
    username: str,
    command: str,
    password: Optional[str] = None,
    key_filename: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> SSHResult:
    """Connect, run a fixed command string, return stdout/stderr/exit.

    Does not log passwords or key material.
    Prefer key_filename over password when possible.
    """
    client = paramiko.SSHClient()
    # DEMO ONLY: auto-accept unknown host keys. Do not use in production.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs: dict = {
        "hostname": host,
        "port": port,
        "username": username,
        "timeout": timeout,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if key_filename:
        connect_kwargs["key_filename"] = key_filename
    elif password is not None:
        connect_kwargs["password"] = password
    else:
        raise SSHError("No SSH credential provided (password or key path).")

    try:
        client.connect(**connect_kwargs)
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return SSHResult(
            stdout=stdout.read().decode("utf-8", errors="replace"),
            stderr=stderr.read().decode("utf-8", errors="replace"),
            exit_code=exit_code,
        )
    except SSHError:
        raise
    except Exception as exc:  # noqa: BLE001 — map all transport failures
        raise SSHError(f"SSH failed: {exc.__class__.__name__}") from exc
    finally:
        client.close()
