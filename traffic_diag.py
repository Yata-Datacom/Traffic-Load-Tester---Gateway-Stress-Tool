"""Diagnostics, storage and formatting helpers for Traffic Studio.

No third-party dependencies: ICMP uses the system ``ping`` command, TCP probes use
plain sockets, and results are stored as JSON next to the launcher.
"""

from __future__ import annotations

import csv
import ipaddress
import json
import os
import re
import socket
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

IS_WINDOWS = os.name == "nt"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

BUILTIN_SCENARIOS = [
    {
        "name": "网关 Web 压测",
        "description": "TCP 80/443，中等包长，适合网关 HTTP 转发压力",
        "protocol": "TCP",
        "ports": "80,443",
        "packet_size": 512,
        "rate": 1000,
        "concurrency": 20,
    },
    {
        "name": "DNS 53 压测",
        "description": "UDP 53，小包高频，观察会话表与 DNS 转发",
        "protocol": "UDP",
        "ports": "53",
        "packet_size": 256,
        "rate": 2000,
        "concurrency": 10,
    },
    {
        "name": "视频 UDP 大包",
        "description": "UDP 5000，1200B 载荷，接近视频流带宽模型",
        "protocol": "UDP",
        "ports": "5000",
        "packet_size": 1200,
        "rate": 2000,
        "concurrency": 30,
    },
    {
        "name": "TCP SYN 握手",
        "description": "TCP SYN 半开连接，重点压网关新建会话能力",
        "protocol": "TCP SYN",
        "ports": "80,443",
        "packet_size": 64,
        "rate": 2000,
        "concurrency": 50,
    },
]


@dataclass
class PingResult:
    host: str
    ok: bool
    sent: int
    received: int
    loss_pct: float
    rtt_min: float
    rtt_avg: float
    rtt_max: float
    jitter: float
    error: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        if not self.ok:
            return self.error or "不可达"
        return (f"收 {self.received}/{self.sent}，丢包 {self.loss_pct:.0f}%，"
                f"RTT {self.rtt_min:.1f}/{self.rtt_avg:.1f}/{self.rtt_max:.1f} ms，"
                f"抖动 {self.jitter:.1f} ms")


def ping_host(host: str, count: int = 4, timeout: float = 1.5) -> PingResult:
    """Ping a host with the OS command and parse RTT/loss for both zh/en output."""
    count = max(1, min(int(count), 20))
    timeout = max(0.2, min(float(timeout), 10.0))
    if IS_WINDOWS:
        cmd = ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(max(1, int(timeout))), host]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="gbk" if IS_WINDOWS else "utf-8", errors="replace",
            timeout=count * (timeout + 1) + 5,
            creationflags=NO_WINDOW,
        )
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return PingResult(host, False, count, 0, 100.0, 0, 0, 0, 0, str(exc)[:120])

    rtts = [float(m) for m in re.findall(
        r"(?:time|时间)[=<]\s*(\d+(?:\.\d+)?)\s*ms", output, re.I)]
    received = min(len(rtts), count)
    loss_match = re.search(r"\((\d+)%\s*(?:loss|丢失)", output, re.I)
    if loss_match:
        loss = float(loss_match.group(1))
    elif received:
        loss = (count - received) / count * 100
    else:
        loss = 100.0
    if not rtts:
        return PingResult(host, False, count, 0, loss, 0, 0, 0, 0, "无 ICMP 回包")
    jitter = 0.0
    if len(rtts) > 1:
        jitter = sum(abs(b - a) for a, b in zip(rtts, rtts[1:])) / (len(rtts) - 1)
    return PingResult(host, True, count, received, loss,
                      min(rtts), sum(rtts) / len(rtts), max(rtts), jitter)


@dataclass
class PortResult:
    host: str
    port: int
    ok: bool
    latency_ms: float
    error: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def tcp_probe(host: str, port: int, timeout: float = 1.5) -> PortResult:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return PortResult(host, int(port), True, (time.perf_counter() - started) * 1000)
    except OSError as exc:
        return PortResult(host, int(port), False, 0.0, str(exc)[:80])


def resolve_host(host: str, port: int = 0) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        return []
    addresses = []
    for info in infos:
        addr = info[4][0]
        if addr not in addresses:
            addresses.append(addr)
    return addresses


def check_ports(host: str, ports: Iterable[int], timeout: float = 1.0,
                max_ports: int = 50) -> list[PortResult]:
    return [tcp_probe(host, p, timeout) for p in list(ports)[:max_ports]]


def is_loopback(host: str) -> bool:
    value = (host or "").strip().lower()
    if value in {"localhost", "localhost.localdomain"}:
        return True
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def target_risk(host: str) -> str:
    value = (host or "").strip().lower()
    if is_loopback(value):
        return "环回地址：只适合本机内置接收端，不建议全速压测"
    if value in {"192.0.2.10", "198.51.100.20"}:
        return "文档示例地址：不会命中真实设备，请改成你的授权目标"
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return "主机名：启动前请先做目标诊断"
    if ip.is_multicast or ip.is_unspecified:
        return "组播/未指定地址：不适合作为压测目标"
    return ""


def format_bytes(value: float) -> str:
    if value < 1024:
        return f"{value:.0f} B"
    if value < 1024 ** 2:
        return f"{value / 1024:.1f} KB"
    if value < 1024 ** 3:
        return f"{value / 1024 ** 2:.1f} MB"
    return f"{value / 1024 ** 3:.2f} GB"


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def load_records(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def append_record(path: str | Path, record: dict, limit: int = 300) -> list[dict]:
    records = load_records(path)
    records.insert(0, record)
    records = records[:limit]
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, p)
    return records


def export_records_csv(path: str | Path, records: list[dict]) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = ["time", "target", "ports", "protocol", "concurrency", "packet_size",
              "rate", "duration", "packets", "bytes", "avg_pps", "avg_mbps", "note"]
    with p.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    return p


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
