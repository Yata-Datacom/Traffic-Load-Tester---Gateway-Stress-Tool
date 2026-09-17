# Traffic Load Tester - Gateway Stress Tool / 网关超大并发流量测试工具

[![CI](https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/ci.yml/badge.svg)](https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/ci.yml)
[![Build EXE](https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/build.yml/badge.svg)](https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](#)

**v1.1.0** · [CHANGELOG](CHANGELOG.md) · [开发与测试](#开发与测试--development--tests)

A Python GUI tool for high-concurrency network traffic testing against a gateway or server. Supports both TCP and UDP, with real-time PPS and bandwidth monitoring.

> 基于 Python GUI 的网关大并发流量压力测试工具，支持 TCP/UDP，实时显示 PPS 和带宽。

---

## 中文说明

### 环境要求

- Python 3.8+（在 3.11 上测试通过）
- 无需安装第三方库（仅使用内置 `tkinter`、`socket`、`threading`）

### 快速启动

双击 `traffic_test_gui.pyw` 即可启动（无命令行窗口），或在终端运行：

```bash
python traffic_test_gui.py
```

### 功能参数

| 参数 | 范围 | 说明 |
|------|------|------|
| Target IP / 目标IP | 任意 | 目标网关/服务器 IP 地址 |
| Port / 端口 | 1-65535 | 目标端口号 |
| Protocol / 协议 | TCP / UDP | 传输层协议 |
| Concurrency / 并发数 | 1-500 | 并发发送线程数量 |
| Packet Size / 包大小 | 64-65535 字节 | 每包载荷大小（预设：64/256/512/1024/1460） |
| Rate / 发包速率 | 0-50000 pkt/s | 每个线程每秒发包数（0 = 不限速全速发送） |

### 实时显示

- **PPS** - 当前每秒发包数
- **Bandwidth (Mbps)** - 当前吞吐带宽
- **Total Packets / 总包数** - 累计已发送包数
- **Total Bytes / 总字节数** - 累计已发送字节数
- **Elapsed / 运行时长** - 测试已运行时间
- **Log / 日志** - 启停事件及汇总统计

### 架构说明

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

### 注意事项

- **请确保在授权范围内使用**，不要对未授权的系统发起测试
- 超高并发可能触发操作系统端口耗尽或防火墙限制
- 目标服务器需要有足够的处理能力，否则可能导致服务不可用

---

## English

## Requirements

- Python 3.8+ (tested on 3.11)
- No third-party dependencies (uses only built-in `tkinter`, `socket`, `threading`)

## Quick Start

Double-click `traffic_test_gui.pyw` to launch (no console window).

Or run from terminal:

```bash
python traffic_test_gui.py
```

## Features

| Parameter | Range | Description |
|-----------|-------|-------------|
| Target IP | any | Destination IP address |
| Port | see below | Destination port with multi-port syntax |
| Protocol | UDP / TCP / TCP SYN | Transport layer protocol |
| Concurrency | 1-500 | Number of parallel sending threads |
| Packet Size | 64-65535 bytes | Payload size per packet (presets: 64, 256, 512, 1024, 1460) |
| Rate | 0-50000 pkt/s | Packets per second per thread (0 = unlimited burst) |

### Port Syntax

| Format | Example | Description |
|--------|---------|-------------|
| Single port | `8080` | Fixed destination port |
| Comma list | `80,443,8080` | Round-robin/random across listed ports |
| Port range | `100-1000` | Random port from range each tick/connection |
| Range with limit | `100-1000:50` | 50 random unique ports sampled from range |

### Protocol Modes

| Mode | No Server Required | Description |
|------|-------------------|-------------|
| UDP | Yes | Send datagrams, no handshake needed |
| TCP | **No** | Full TCP connection, needs server listening |
| TCP SYN | Yes | Half-open SYN flood using non-blocking connect, tests gateway TCP stack |

### Real-time Display

- **PPS** - current packets per second
- **Bandwidth (Mbps)** - current throughput
- **Total Packets / Bytes** - cumulative sent
- **Elapsed Time** - running duration
- **Log** - start/stop events with summary statistics

## Architecture

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

### UDP Mode

Each thread creates a UDP socket, connects to the target (datagram mode), and fires packets at the configured rate.

### TCP Mode

Each thread establishes a TCP connection, then sends data continuously. On disconnection, the thread automatically reconnects after 0.5s delay. Nagle's algorithm is disabled (`TCP_NODELAY`) for lower latency.

### Rate Limiting

Uses a token-bucket-like accumulator to smooth packet bursts. Each tick, the elapsed time accumulated is converted to the number of packets to send. Burst is capped at 1000 packets per tick to avoid CPU spikes.

## Note

This tool sends raw payloads. Ensure the target server can handle the traffic load. Do not use against systems without authorization.

---

## 开发与测试 / Development & Tests

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
- CI：`.github/workflows/ci.yml`（Windows 跑 pytest、Linux 跑 ruff）；`.github/workflows/build.yml`（打 tag 或手动触发 → 产出 exe artifact）
- 版本号在 `pyproject.toml` 与 `traffic_test_gui.__version__` **两处**，必须保持一致（有测试守着）
