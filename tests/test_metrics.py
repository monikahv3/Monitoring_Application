"""Metrics parsers and collector tests with mocked SSH (no real hosts)."""

from metrics import (
    collect_server_metrics,
    parse_cpu,
    parse_disk,
    parse_load,
    parse_memory,
    parse_network,
    parse_ports,
)
from ssh_client import SSHError, SSHResult


SAMPLE_CPU = "cpu  100 0 50 850 0 0 0 0\n"
SAMPLE_MEM = (
    "              total        used        free      shared  buff/cache   available\n"
    "Mem:     8000000000  2000000000  1000000000           0  5000000000  6000000000\n"
)
SAMPLE_LOAD = "0.10 0.20 0.30 1/100 1234\n"
SAMPLE_DISK = (
    "Filesystem     1B-blocks        Used  Available Use% Mounted on\n"
    "/dev/sda1    100000000000 40000000000 60000000000  40% /\n"
    "tmpfs          1000000000          0  1000000000   0% /dev/shm\n"
)
SAMPLE_NET = (
    "Inter-|   Receive                                                |  Transmit\n"
    " face |bytes    packets errs drop fifo frame compressed multicast|bytes\n"
    "  eth0: 1000 1 0 0 0 0 0 0 2000 2 0 0 0 0 0 0\n"
    "    lo: 10 1 0 0 0 0 0 0 10 1 0 0 0 0 0 0\n"
)
SAMPLE_PORTS = (
    "Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process\n"
    'tcp   LISTEN 0      128          0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=1,fd=3))\n'
)


def test_parsers():
    assert parse_cpu(SAMPLE_CPU) == 15.0
    mem = parse_memory(SAMPLE_MEM)
    assert mem["total"] == 8_000_000_000
    assert mem["used"] == 2_000_000_000
    assert mem["percent"] == 25.0
    assert parse_load(SAMPLE_LOAD) == {"1": 0.1, "5": 0.2, "15": 0.3}
    disks = parse_disk(SAMPLE_DISK)
    assert len(disks) == 1
    assert disks[0]["mount"] == "/"
    nets = parse_network(SAMPLE_NET)
    assert nets == [{"iface": "eth0", "rx_bytes": 1000, "tx_bytes": 2000}]
    ports = parse_ports(SAMPLE_PORTS)
    assert ports[0]["port"] == 22
    assert ports[0]["process"] == "sshd"


def test_collect_with_mock_runner_ok():
    outputs = {
        "grep '^cpu ' /proc/stat": SAMPLE_CPU,
        "free -b": SAMPLE_MEM,
        "cat /proc/loadavg": SAMPLE_LOAD,
        "df -PB1": SAMPLE_DISK,
        "cat /proc/net/dev": SAMPLE_NET,
        "ss -lntup 2>/dev/null || ss -lntu 2>/dev/null": SAMPLE_PORTS,
    }

    def runner(**kwargs):
        # Fixture must not use real credentials
        assert kwargs["password"] == "fake-demo-password"
        assert kwargs.get("key_filename") is None
        cmd = kwargs["command"]
        return SSHResult(stdout=outputs[cmd], stderr="", exit_code=0)

    result = collect_server_metrics(
        {
            "host": "192.0.2.10",
            "port": 22,
            "ssh_username": "demo",
            "auth_type": "password",
            "credential_ref": "fake-demo-password",
        },
        runner=runner,
    )
    assert result["status"] == "ok"
    assert result["cpu_percent"] == 15.0
    assert result["memory"]["percent"] == 25.0
    assert result["ports"][0]["process"] == "sshd"


def test_collect_unreachable():
    def runner(**_kwargs):
        raise SSHError("SSH failed: TimeoutError")

    result = collect_server_metrics(
        {
            "host": "192.0.2.11",
            "port": 22,
            "ssh_username": "demo",
            "auth_type": "key",
            "credential_ref": "/tmp/fake-key",
        },
        runner=runner,
    )
    assert result["status"] == "unreachable"
    assert "TimeoutError" in result["error"]
