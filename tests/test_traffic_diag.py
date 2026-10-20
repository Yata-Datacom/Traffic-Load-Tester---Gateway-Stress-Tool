"""Traffic diagnostics and local result-storage tests (no live traffic)."""
from __future__ import annotations

import csv
import pytest

import traffic_diag as diag


class _FakePing:
    stdout = ("正在 Ping 192.0.2.10 具有 32 字节的数据:\n"
              "来自 192.0.2.10 的回复: 字节=32 时间=10ms TTL=64\n"
              "来自 192.0.2.10 的回复: 字节=32 时间=20ms TTL=64\n"
              "数据包: 已发送 = 4，已接收 = 2，丢失 = 2 (50% 丢失)")
    stderr = ""


def test_ping_parses_chinese_rtt_and_loss(monkeypatch):
    monkeypatch.setattr(diag.subprocess, "run", lambda *a, **k: _FakePing())
    result = diag.ping_host("192.0.2.10", count=4)
    assert result.ok
    assert result.received == 2
    assert result.loss_pct == 50
    assert (result.rtt_min, result.rtt_avg, result.rtt_max) == (10, 15, 20)
    assert result.jitter == 10


def test_format_helpers():
    assert diag.format_bytes(0) == "0 B"
    assert diag.format_bytes(1024) == "1.0 KB"
    assert diag.format_bytes(1024 ** 2) == "1.0 MB"
    assert diag.format_duration(0) == "00:00:00"
    assert diag.format_duration(3661) == "01:01:01"


def test_target_risk_marks_loopback_and_docs():
    assert "环回" in diag.target_risk("127.0.0.1")
    assert "文档" in diag.target_risk("192.0.2.10")
    assert diag.target_risk("198.51.100.20").startswith("文档")
    assert diag.target_risk("203.0.113.5") == ""


def test_resolve_localhost():
    addresses = diag.resolve_host("localhost", 80)
    assert addresses


def test_append_load_and_export_records(tmp_path):
    path = tmp_path / "runs.json"
    record = {"time": "2026-10-20 10:00:00", "target": "192.0.2.10",
              "ports": "80", "protocol": "TCP", "concurrency": 2,
              "packet_size": 64, "rate": 10, "duration": "1.0s",
              "packets": 10, "bytes": 640, "avg_pps": 10.0,
              "avg_mbps": 0.05, "note": "test"}
    records = diag.append_record(path, record)
    assert len(records) == 1
    assert diag.load_records(path)[0]["target"] == "192.0.2.10"
    out = diag.export_records_csv(tmp_path / "runs.csv", records)
    with out.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["protocol"] == "TCP"
    assert rows[0]["avg_pps"] == "10.0"


def test_check_ports_caps_count(monkeypatch):
    calls = []

    def fake_probe(host, port, timeout=1.5):
        calls.append(port)
        return diag.PortResult(host, port, True, 1.0)

    monkeypatch.setattr(diag, "tcp_probe", fake_probe)
    results = diag.check_ports("192.0.2.10", range(1, 100), max_ports=5)
    assert len(results) == 5
    assert calls == list(range(1, 6))


def test_builtin_scenarios_are_complete():
    expected = {"name", "description", "protocol", "ports", "packet_size", "rate", "concurrency"}
    for scenario in diag.BUILTIN_SCENARIOS:
        assert expected <= set(scenario)
        assert scenario["protocol"] in {"UDP", "TCP", "TCP SYN"}
        assert scenario["concurrency"] >= 1


@pytest.mark.parametrize("host", ["", "localhost", "192.0.2.10"])
def test_risk_never_crashes(host):
    assert isinstance(diag.target_risk(host), str)
