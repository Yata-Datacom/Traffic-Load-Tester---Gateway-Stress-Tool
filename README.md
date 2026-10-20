<div align="center">

<img src="app_icon.ico" width="96" alt="Traffic Studio" />

# Traffic Studio — Gateway Stress & Diagnostics

**A gateway stress-test and diagnostics studio for network engineers — load test, diagnose, and keep every run**<br/>
<sub>TCP / UDP / TCP SYN · live PPS & Mbps · ICMP/DNS/TCP diagnostics · scenarios · run history</sub>

<sub>[**English**](README.md) · [**简体中文**](README.zh-CN.md) · [**User guide**](docs/USER_GUIDE.md)</sub>

<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/ci.yml?branch=main&style=for-the-badge&label=CI&color=5E81AC" alt="CI" /></a>
<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/build.yml?branch=main&style=for-the-badge&label=Build%20EXE&color=81A1C1" alt="Build EXE" /></a>
<a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-8FBCBB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" /></a>
<img src="https://img.shields.io/badge/platform-Windows-88C0D0?style=for-the-badge&logo=windows11&logoColor=white" alt="Platform: Windows" />
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-8FBCBB?style=for-the-badge" alt="License: MIT" /></a>
<img src="https://img.shields.io/badge/version-v2.0.0-5E81AC?style=for-the-badge" alt="v2.0.0" />

**v2.0.0** · [CHANGELOG](CHANGELOG.md) · [User guide](docs/USER_GUIDE.md)

</div>

> ⚠ **Authorized targets only.** Do not stress public, customer or third-party systems without explicit permission.

![Traffic Studio dashboard](assets/traffic_v2_dashboard.png)

---

## ✨ At a glance

| | |
| :-- | :-- |
| 🧪 | **Diagnose first** — ICMP loss/RTT/jitter, DNS, TCP ports and default gateway |
| 🚦 | **Three load modes** — UDP / TCP / TCP SYN, live PPS and Mbps |
| 🎬 | **Scenarios** — Web, DNS, video UDP and SYN presets; save your own |
| ⏱️ | **Duration** — run for N seconds or stop manually |
| 📜 | **Run history** — every completed test is recorded and exportable as CSV |
| 🛡️ | **Safety defaults** — documentation-address target, explicit authorization gate |
| 🧩 | **No third-party runtime dependencies** — Tkinter + sockets only |

---

## 🆕 What's new in 2.0

- Four workspaces: **Overview / Load test / Diagnostics / History**
- **Target diagnostics**: Ping loss + RTT + jitter, DNS resolution, TCP port probes, gateway detection
- **Scenarios**: built-in Web / DNS / Video UDP / TCP SYN; save custom scenarios locally
- **Duration + auto-stop**
- **Automatic run history** with CSV export
- **Chinese UI** while keeping technical fields in English
- **V1 engine reused** — traffic generator, TCP receiver, port parser and gateway detector are unchanged

---

## 🚀 Quick start

```bash
python traffic_studio.py
```

Or double-click [`traffic_studio.pyw`](traffic_studio.pyw) for a windowless launch.
A single-file exe is available on the [Releases](https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/releases) page.

The legacy V1 UI remains available:

```bash
python traffic_test_gui.py
```

---

## 🎛️ Load test

| Parameter | Range | Notes |
| :-- | :-- | :-- |
| Target | any | Only authorized targets |
| Ports | `8080` / `80,443` / `100-1000` / `100-1000:50` | Multi-port syntax |
| Protocol | UDP / TCP / TCP SYN | TCP requires a listener |
| Concurrency | 1–500 | Threads |
| Packet size | 1–65535 B | Presets 64/256/512/1024/1460 |
| Rate | 0–50000 pkt/s/thread | 0 = unlimited, confirmation required |
| Duration | 0–86400 s | 0 = manual stop |

### Protocol modes

| Mode | Listener required | Description |
| :-- | :-- | :-- |
| UDP | No | Direct datagrams |
| TCP | Yes | Full connection, then payload |
| TCP SYN | No | Non-blocking half-open connects |

### Built-in receiver

For a local TCP loopback check, start the receiver, then target `127.0.0.1` on the same port.

---

## 🩺 Diagnostics

| Check | Output |
| :-- | :-- |
| ICMP Ping | Loss, min/avg/max RTT, jitter |
| DNS | Resolved A/AAAA addresses |
| TCP ports | Open/closed + connect latency (up to 50 ports) |
| Gateway | Next hop + interface alias |

![Diagnostics](assets/traffic_v2_diag.png)

---

## 🎬 Scenarios

| Scenario | Protocol | Ports | Packet | Rate | Concurrency |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Web gateway | TCP | 80,443 | 512 | 1000 | 20 |
| DNS 53 | UDP | 53 | 256 | 2000 | 10 |
| Video UDP | UDP | 5000 | 1200 | 2000 | 30 |
| TCP SYN | TCP SYN | 80,443 | 64 | 2000 | 50 |

Save the current parameters as a custom scenario; it is stored in local `scenarios.json` (git-ignored).

---

## 📜 Run history

Every completed run is appended to local `runs.json`:

- Target, ports, protocol, concurrency, packet size, rate, duration
- Total packets/bytes, average PPS/Mbps
- History page: refresh, export CSV to `reports/`, open folder, clear

![History](assets/traffic_v2_history.png)

---

## 🏗️ Architecture

```text
TrafficStudio (Tkinter workspace shell)
  ├── Overview / Load test / Diagnostics / History
  ├── traffic_diag.py      ICMP / DNS / TCP / storage / CSV
  └── traffic_test_gui.py  V1 engine: TrafficGenerator / TCPServer / Stats
```

---

## 🧪 Development & tests

```bash
python -m pytest -q
python -m ruff check .
```

**55 pytest tests**: port parsing, thread-safe Stats, payload generation, ping parsing,
record/CSV storage, legacy entry consistency and V2 workspace smoke tests.

---

## 🔐 Privacy

- `runs.json`, `scenarios.json`, `reports/`, `build/`, `dist/` and `*.exe` are ignored
- Screenshots and docs use RFC 5737 addresses (`192.0.2.0/24`, `198.51.100.0/24`) and synthetic data
- Never commit real targets, results, captures or customer topologies

---

MIT License · © 2026 Yata-Datacom · Traffic Studio
