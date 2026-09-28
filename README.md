<div align="center">

<img src="app_icon.ico" width="96" alt="Traffic Load Tester" />

# 网关超大并发流量测试工具 · Traffic Load Tester - Gateway Stress Tool

**基于 Python GUI 的网关大并发流量压力测试工具，支持 TCP / UDP，实时显示 PPS 和带宽**<br/>
<sub>**A Python GUI tool for high-concurrency network traffic testing against a gateway or server.**</sub>

<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/ci.yml?branch=main&style=for-the-badge&label=CI&color=5E81AC" alt="CI" /></a>
<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/build.yml?branch=main&style=for-the-badge&label=Build%20EXE&color=81A1C1" alt="Build EXE" /></a>
<a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.9%2B-8FBCBB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+" /></a>
<img src="https://img.shields.io/badge/platform-Windows-88C0D0?style=for-the-badge&logo=windows11&logoColor=white" alt="Platform: Windows" />
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-8FBCBB?style=for-the-badge" alt="License: MIT" /></a>
<img src="https://img.shields.io/badge/version-v1.1.0-5E81AC?style=for-the-badge" alt="v1.1.0" />

**v1.1.0** · [CHANGELOG](CHANGELOG.md) · [开发与测试](#开发与测试--development--tests)

</div>

> 基于 Python GUI 的网关大并发流量压力测试工具，支持 **TCP / UDP**，实时显示 **PPS** 和**带宽**；面向需要对网关或服务器做高并发流量压测的网络工程师。
> A Python GUI tool for high-concurrency network traffic testing against a gateway or server. Supports both TCP and UDP, with real-time PPS and bandwidth monitoring.

---

## ✨ 特点速览 · At a glance

| | 中文 | English |
| :-- | :-- | :-- |
| 🧩 | **零第三方依赖** — 仅使用内置 `tkinter`、`socket`、`threading` | **No third-party dependencies** — built-in modules only |
| 🖥️ | **GUI 直启** — 双击 `traffic_test_gui.pyw` 即可启动，无命令行窗口 | **GUI first** — double-click `traffic_test_gui.pyw` to launch, no console window |
| 🌐 | **三种协议模式** — UDP / TCP / TCP SYN | **Three protocol modes** — UDP, TCP and TCP SYN |
| 🚦 | **令牌桶限速** — 平滑限速，`0` 表示不限速全速发送 | **Token-bucket rate limiting** — `0` means unlimited full-speed burst |
| 📊 | **实时指标** — PPS、带宽 (Mbps)、总包数、总字节数、运行时长、日志 | **Live metrics** — PPS, bandwidth, totals, elapsed time, log |
| 🧪 | **自带测试与 CI** — pytest、ruff，GitHub Actions 自动跑 | **Tested in CI** — pytest + ruff on GitHub Actions |

---

## 📘 中文说明 · Chinese Guide

### 🔧 环境要求 · Requirements

- Python 3.8+（在 3.11 上测试通过）
- 无需安装第三方库（仅使用内置 `tkinter`、`socket`、`threading`）

### 🚀 快速启动 · Quick Start

双击 [`traffic_test_gui.pyw`](traffic_test_gui.pyw) 即可启动（无命令行窗口），或在终端运行：

```bash
python traffic_test_gui.py
```

### 🎛️ 功能参数 · Features

| 参数 · Parameter | 范围 · Range | 说明 · Description |
| :-- | :-- | :-- |
| Target IP / 目标IP | 任意 | 目标网关/服务器 IP 地址 |
| Port / 端口 | 1-65535 | 目标端口号 |
| Protocol / 协议 | TCP / UDP | 传输层协议 |
| Concurrency / 并发数 | 1-500 | 并发发送线程数量 |
| Packet Size / 包大小 | 64-65535 字节 | 每包载荷大小（预设：64/256/512/1024/1460） |
| Rate / 发包速率 | 0-50000 pkt/s | 每个线程每秒发包数（0 = 不限速全速发送） |

### 📊 实时显示 · Real-time Display

| 指标 · Metric | 说明 · Description |
| :-- | :-- |
| **PPS** | 当前每秒发包数 |
| **Bandwidth (Mbps)** | 当前吞吐带宽 |
| **Total Packets / 总包数** | 累计已发送包数 |
| **Total Bytes / 总字节数** | 累计已发送字节数 |
| **Elapsed / 运行时长** | 测试已运行时间 |
| **Log / 日志** | 启停事件及汇总统计 |

### 🏗️ 架构说明 · Architecture

```
TrafficGUI (tkinter界面)
  |
  +-- TrafficGenerator (流量生成器)
        |
        +-- N 个工作线程 (UDP 或 TCP)
        |     每个线程：令牌桶速率控制 + socket 发送
        |
        +-- Stats (线程安全的计数器)
             总包数、总字节数、当前PPS、当前带宽
```

**UDP 模式**：每个线程创建一个 UDP socket，向目标持续发送数据报。

**TCP 模式**：每个线程建立 TCP 长连接后持续发送数据，断连后自动重连（间隔 0.5 秒），已关闭 Nagle 算法（`TCP_NODELAY`）以降低延迟。

**速率控制**：基于令牌桶算法的平滑速率限制，每轮将累积时间换算为应发送包数，单轮最大突发限制为 1000 包以防 CPU 尖峰。

### ⚠️ 注意事项 · Notes

- **请确保在授权范围内使用**，不要对未授权的系统发起测试
- 超高并发可能触发操作系统端口耗尽或防火墙限制
- 目标服务器需要有足够的处理能力，否则可能导致服务不可用

---

## 🗂️ 仓库内容 · Repository layout

| 路径 · Path | 说明 · Description | English |
| :-- | :-- | :-- |
| [`traffic_test_gui.pyw`](traffic_test_gui.pyw) | GUI 入口：双击启动，无命令行窗口 | GUI entry — double-click to launch, no console window |
| [`traffic_test_gui.py`](traffic_test_gui.py) | 同一 GUI 的终端入口（`python traffic_test_gui.py`） | Same GUI, launched from a terminal |
| [`TrafficTest.spec`](TrafficTest.spec) | PyInstaller 单文件 exe 打包配置 | PyInstaller single-file exe spec |
| [`pyproject.toml`](pyproject.toml) | 项目元数据、开发依赖与版本号；命令入口 `traffic-load-tester` | Project metadata, dev extras, version |
| [`CHANGELOG.md`](CHANGELOG.md) | 版本变更记录 | Release notes |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | CI：Windows 跑 pytest、Linux 跑 ruff | CI: pytest on Windows, ruff on Linux |
| [`.github/workflows/build.yml`](.github/workflows/build.yml) | 打 tag 或手动触发 → 产出 exe artifact | Tag or manual run → exe artifact |
| [`LICENSE`](LICENSE) | MIT 许可 | MIT license |

---

## 🌐 English

## 📦 Requirements

- Python 3.8+ (tested on 3.11)
- No third-party dependencies (uses only built-in `tkinter`, `socket`, `threading`)

---

## 🚀 Quick Start

Double-click [`traffic_test_gui.pyw`](traffic_test_gui.pyw) to launch (no console window).

Or run from terminal:

```bash
python traffic_test_gui.py
```

---

## 🎛️ Features

| Parameter | Range | Description |
| :-- | :-- | :-- |
| Target IP | any | Destination IP address |
| Port | see below | Destination port with multi-port syntax |
| Protocol | UDP / TCP / TCP SYN | Transport layer protocol |
| Concurrency | 1-500 | Number of parallel sending threads |
| Packet Size | 64-65535 bytes | Payload size per packet (presets: 64, 256, 512, 1024, 1460) |
| Rate | 0-50000 pkt/s | Packets per second per thread (0 = unlimited burst) |

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

- **PPS** - current packets per second
- **Bandwidth (Mbps)** - current throughput
- **Total Packets / Bytes** - cumulative sent
- **Elapsed Time** - running duration
- **Log** - start/stop events with summary statistics

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

Each thread creates a UDP socket, connects to the target (datagram mode), and fires packets at the configured rate.

### 🗄️ TCP Mode

Each thread establishes a TCP connection, then sends data continuously. On disconnection, the thread automatically reconnects after 0.5s delay. Nagle's algorithm is disabled (`TCP_NODELAY`) for lower latency.

### 🚦 Rate Limiting

Uses a token-bucket-like accumulator to smooth packet bursts. Each tick, the elapsed time accumulated is converted to the number of packets to send. Burst is capped at 1000 packets per tick to avoid CPU spikes.

---

## ⚠️ Note

This tool sends raw payloads. Ensure the target server can handle the traffic load. Do not use against systems without authorization.

---

<a name="开发与测试--development--tests"></a>

## 🧪 开发与测试 · Development & Tests

```bash
# 安装（含开发依赖）
python -m pip install -e ".[dev]"

# 跑测试
python -m pytest -q

# 静态检查
ruff check .

# 打包单文件 exe（Windows）
python -m PyInstaller --clean --noconfirm TrafficTest.spec
```

- 装好后也可用命令入口启动：`traffic-load-tester`
- 测试覆盖：端口表达式解析 / 统计计数与速率换算 / 负载生成 / 两个入口文件一致性 / 版本号与 `pyproject.toml` 一致
- CI：[`.github/workflows/ci.yml`](.github/workflows/ci.yml)（Windows 跑 pytest、Linux 跑 ruff）；[`.github/workflows/build.yml`](.github/workflows/build.yml)（打 tag 或手动触发 → 产出 exe artifact）
- 版本号在 [`pyproject.toml`](pyproject.toml) 与 `traffic_test_gui.__version__` **两处**，必须保持一致（有测试守着）

---

## 📜 许可 · License

本项目以 **MIT** 许可发布，详见 [LICENSE](LICENSE)。
Released under the **MIT** license — see [LICENSE](LICENSE).

---

## ⚠️ 免责声明 · Disclaimer

**请确保在授权范围内使用**，不要对未授权的系统发起测试；超高并发可能触发操作系统端口耗尽或防火墙限制，目标服务器也需要有足够的处理能力。
Only test systems you are authorized to test. Do not use against systems without authorization.

---

<div align="center">
<sub>MIT License · Traffic Load Tester - Gateway Stress Tool</sub>
</div>
