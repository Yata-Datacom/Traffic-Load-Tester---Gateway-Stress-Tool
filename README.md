<div align="center">

<img src="app_icon.ico" width="96" alt="Traffic Load Tester" />

# Traffic Load Tester - Gateway Stress Tool

**A Python GUI tool for high-concurrency gateway traffic stress testing — TCP / UDP, with live PPS and bandwidth display**<br/>
<sub>**A Python GUI tool for high-concurrency network traffic testing against a gateway or server.**</sub>

<sub>[**English**](README.md) · [**简体中文**](README.zh-CN.md)</sub>

<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/ci.yml?branch=main&style=for-the-badge&label=CI&color=5E81AC" alt="CI" /></a>
<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/build.yml?branch=main&style=for-the-badge&label=Build%20EXE&color=81A1C1" alt="Build EXE" /></a>
<a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.9%2B-8FBCBB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+" /></a>
<img src="https://img.shields.io/badge/platform-Windows-88C0D0?style=for-the-badge&logo=windows11&logoColor=white" alt="Platform: Windows" />
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-8FBCBB?style=for-the-badge" alt="License: MIT" /></a>
<img src="https://img.shields.io/badge/version-v1.1.0-5E81AC?style=for-the-badge" alt="v1.1.0" />

**v1.1.0** · [CHANGELOG](CHANGELOG.md) · [Development & Tests](#development--tests)

</div>

> A Python GUI tool for high-concurrency network traffic testing against a gateway or server. Supports both **TCP / UDP**, with real-time **PPS** and **bandwidth** monitoring — built for network engineers who need to stress-test a gateway or server.

---

## ✨ At a glance

| | |
| :-- | :-- |
| 🧩 | **No third-party dependencies** — built-in `tkinter`, `socket`, `threading` only |
| 🖥️ | **GUI first** — double-click `traffic_test_gui.pyw` to launch, no console window |
| 🌐 | **Three protocol modes** — UDP / TCP / TCP SYN |
| 🚦 | **Token-bucket rate limiting** — smooth pacing, `0` means unlimited full-speed sending |
| 📊 | **Live metrics** — PPS, bandwidth (Mbps), total packets, total bytes, elapsed time, log |
| 🧪 | **Tested and in CI** — pytest, ruff, run automatically on GitHub Actions |

---

## 🔧 Requirements

- Python 3.8+ (tested on 3.11)
- No third-party dependencies (uses only built-in `tkinter`, `socket`, `threading`)

---

## 🚀 Quick Start

Double-click [`traffic_test_gui.pyw`](traffic_test_gui.pyw) to launch (no console window), or run from a terminal:

```bash
python traffic_test_gui.py
```

---

## 🎛️ Features

| Parameter | Range | Description |
| :-- | :-- | :-- |
| Target IP | any | Destination gateway/server IP address |
| Port | 1-65535 | Destination port (multi-port syntax supported, see below) |
| Protocol | UDP / TCP / TCP SYN | Transport layer protocol |
| Concurrency | 1-500 | Number of parallel sending threads |
| Packet Size | 64-65535 bytes | Payload size per packet (presets: 64/256/512/1024/1460) |
| Rate | 0-50000 pkt/s | Packets per second per thread (0 = unlimited full-speed sending) |

### 🔌 Port Syntax

| Format | Example | Description |
| :-- | :-- | :-- |
| Single port | `8080` | Fixed destination port |
| Comma list | `80,443,8080` | Round-robin/random across listed ports |
| Port range | `100-1000` | Random port from range each tick/connection |
| Range with limit | `100-1000:50` | 50 random unique ports sampled from range |

### 🌐 Protocol Modes

| Mode | No Server Required | Description |
| :-- | :-- | :-- |
| UDP | Yes | Send datagrams, no handshake needed |
| TCP | **No** | Full TCP connection, needs server listening |
| TCP SYN | Yes | Half-open SYN flood using non-blocking connect, tests gateway TCP stack |

### 📊 Real-time Display

| Metric | Description |
| :-- | :-- |
| **PPS** | Current packets per second |
| **Bandwidth (Mbps)** | Current throughput bandwidth |
| **Total Packets** | Cumulative packets sent |
| **Total Bytes** | Cumulative bytes sent |
| **Elapsed** | Test running duration |
| **Log** | Start/stop events with summary statistics |

---

## 🏗️ Architecture

```
TrafficGUI (tkinter)
  |
  +-- TrafficGenerator
        |
        +-- N x worker threads (UDP or TCP)
        |     each thread: token-bucket rate limiter + socket send
        |
        +-- Stats (thread-safe counters with Lock)
              total_packets, total_bytes, current_pps, current_bps
```

### 📡 UDP Mode

Each thread creates a UDP socket, connects to the target (datagram mode), and fires datagrams continuously at the configured rate.

### 🗄️ TCP Mode

Each thread establishes a long-lived TCP connection, then sends data continuously. On disconnection, the thread automatically reconnects after a 0.5s delay. Nagle's algorithm is disabled (`TCP_NODELAY`) for lower latency.

### 🚦 Rate Limiting

Smooth rate limiting based on a token-bucket algorithm: each tick, the accumulated time is converted to the number of packets to send. Burst is capped at 1000 packets per tick to avoid CPU spikes.

---

## ⚠️ Notes

- **Make sure you use this tool only within authorized scope** — do not start tests against systems you are not authorized to test
- Very high concurrency may hit operating system port exhaustion or firewall limits
- The target server needs enough processing capacity, otherwise its service may become unavailable
- This tool sends raw payloads — ensure the target server can handle the traffic load

---

## 🗂️ Repository layout

| Path | Description |
| :-- | :-- |
| [`traffic_test_gui.pyw`](traffic_test_gui.pyw) | GUI entry — double-click to launch, no console window |
| [`traffic_test_gui.py`](traffic_test_gui.py) | Same GUI, launched from a terminal (`python traffic_test_gui.py`) |
| [`TrafficTest.spec`](TrafficTest.spec) | PyInstaller single-file exe spec |
| [`pyproject.toml`](pyproject.toml) | Project metadata, dev extras and version; command entry point `traffic-load-tester` |
| [`CHANGELOG.md`](CHANGELOG.md) | Release notes |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | CI: pytest on Windows, ruff on Linux |
| [`.github/workflows/build.yml`](.github/workflows/build.yml) | Tag or manual run → exe artifact |
| [`LICENSE`](LICENSE) | MIT license |

---

<a name="development--tests"></a>

## 🧪 Development & Tests

```bash
# install (with dev dependencies)
python -m pip install -e ".[dev]"

# run the tests
python -m pytest -q

# static checks
ruff check .

# build the single-file exe (Windows)
python -m PyInstaller --clean --noconfirm TrafficTest.spec
```

- Once installed, you can also start it through the command entry point: `traffic-load-tester`
- Test coverage: port expression parsing / stats counters and rate conversion / load generation / consistency of the two entry files / version number matching `pyproject.toml`
- CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (pytest on Windows, ruff on Linux); [`.github/workflows/build.yml`](.github/workflows/build.yml) (tag or manual run → exe artifact)
- The version number lives in **two** places — [`pyproject.toml`](pyproject.toml) and `traffic_test_gui.__version__` — and the two must stay in sync (a test guards this)

---

## 📜 License

Released under the **MIT** license — see [LICENSE](LICENSE).

---

## ⚠️ Disclaimer

**Make sure you use this tool only within authorized scope** — do not start tests against systems you are not authorized to test. Very high concurrency may hit operating system port exhaustion or firewall limits, and the target server also needs enough processing capacity.

---

<div align="center">
<sub>MIT License · Traffic Load Tester - Gateway Stress Tool</sub>
</div>
