<div align="center">

<img src="app_icon.ico" width="96" alt="Traffic Load Tester" />

# 网关超大并发流量测试工具

**基于 Python GUI 的网关大并发流量压力测试工具，支持 TCP / UDP，实时显示 PPS 和带宽**<br/>
<sub>**面向网关或服务器做高并发网络流量压测的 Python GUI 工具。**</sub>

<sub>[**English**](README.md) · [**简体中文**](README.zh-CN.md)</sub>

<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/ci.yml?branch=main&style=for-the-badge&label=CI&color=5E81AC" alt="CI" /></a>
<a href="https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/build.yml?branch=main&style=for-the-badge&label=Build%20EXE&color=81A1C1" alt="Build EXE" /></a>
<a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.9%2B-8FBCBB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+" /></a>
<img src="https://img.shields.io/badge/platform-Windows-88C0D0?style=for-the-badge&logo=windows11&logoColor=white" alt="Platform: Windows" />
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-8FBCBB?style=for-the-badge" alt="License: MIT" /></a>
<img src="https://img.shields.io/badge/version-v1.1.0-5E81AC?style=for-the-badge" alt="v1.1.0" />

**v1.1.0** · [CHANGELOG](CHANGELOG.md) · [开发与测试](#开发与测试)

</div>

> 基于 Python GUI 的网关大并发流量压力测试工具，支持 **TCP / UDP**，实时显示 **PPS** 和**带宽**；面向需要对网关或服务器做高并发流量压测的网络工程师。

---

## ✨ 特点速览

| | |
| :-- | :-- |
| 🧩 | **零第三方依赖** — 仅使用内置 `tkinter`、`socket`、`threading` |
| 🖥️ | **GUI 直启** — 双击 `traffic_test_gui.pyw` 即可启动，无命令行窗口 |
| 🌐 | **三种协议模式** — UDP / TCP / TCP SYN |
| 🚦 | **令牌桶限速** — 平滑限速，`0` 表示不限速全速发送 |
| 📊 | **实时指标** — PPS、带宽 (Mbps)、总包数、总字节数、运行时长、日志 |
| 🧪 | **自带测试与 CI** — pytest、ruff，GitHub Actions 自动跑 |

---

## 🔧 环境要求

- Python 3.8+（在 3.11 上测试通过）
- 无需安装第三方库（仅使用内置 `tkinter`、`socket`、`threading`）

---

## 🚀 快速启动

双击 [`traffic_test_gui.pyw`](traffic_test_gui.pyw) 即可启动（无命令行窗口），或在终端运行：

```bash
python traffic_test_gui.py
```

---

## 🎛️ 功能参数

| 参数 | 范围 | 说明 |
| :-- | :-- | :-- |
| 目标 IP | 任意 | 目标网关/服务器 IP 地址 |
| 端口 | 1-65535 | 目标端口号（支持多端口语法，见下） |
| 协议 | UDP / TCP / TCP SYN | 传输层协议 |
| 并发数 | 1-500 | 并发发送线程数量 |
| 包大小 | 64-65535 字节 | 每包载荷大小（预设：64/256/512/1024/1460） |
| 发包速率 | 0-50000 pkt/s | 每个线程每秒发包数（0 = 不限速全速发送） |

### 🔌 端口语法

| 格式 | 示例 | 说明 |
| :-- | :-- | :-- |
| 单个端口 | `8080` | 固定的目标端口 |
| 逗号列表 | `80,443,8080` | 在列出的端口之间轮询/随机选择 |
| 端口范围 | `100-1000` | 每次发包/建连时从范围内随机取一个端口 |
| 范围加数量 | `100-1000:50` | 从范围中随机抽取 50 个不重复的端口 |

### 🌐 协议模式

| 模式 | 无需服务端 | 说明 |
| :-- | :-- | :-- |
| UDP | 是 | 直接发送数据报，无需握手 |
| TCP | **否** | 完整 TCP 连接，需要服务端处于监听状态 |
| TCP SYN | 是 | 非阻塞 connect 的半开 SYN 洪水，用于测试网关的 TCP 协议栈 |

### 📊 实时显示

| 指标 | 说明 |
| :-- | :-- |
| **PPS** | 当前每秒发包数 |
| **带宽 (Mbps)** | 当前吞吐带宽 |
| **总包数** | 累计已发送包数 |
| **总字节数** | 累计已发送字节数 |
| **运行时长** | 测试已运行时间 |
| **日志** | 启停事件及汇总统计 |

---

## 🏗️ 架构说明

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

### 📡 UDP 模式

每个线程创建一个 UDP socket，连接到目标（数据报模式），按配置速率持续发送数据报。

### 🗄️ TCP 模式

每个线程建立 TCP 长连接后持续发送数据，断连后自动重连（间隔 0.5 秒），已关闭 Nagle 算法（`TCP_NODELAY`）以降低延迟。

### 🚦 速率控制

基于令牌桶算法做平滑限速：每轮将累积时间换算为应发送包数，单轮最大突发限制为 1000 包以防 CPU 尖峰。

---

## ⚠️ 注意事项

- **请确保在授权范围内使用**，不要对未授权的系统发起测试
- 超高并发可能触发操作系统端口耗尽或防火墙限制
- 目标服务器需要有足够的处理能力，否则可能导致服务不可用
- 本工具发送的是原始载荷，请确保目标服务器能承受相应的流量压力

---

## 🗂️ 仓库内容

| 路径 | 说明 |
| :-- | :-- |
| [`traffic_test_gui.pyw`](traffic_test_gui.pyw) | GUI 入口：双击启动，无命令行窗口 |
| [`traffic_test_gui.py`](traffic_test_gui.py) | 同一 GUI 的终端入口（`python traffic_test_gui.py`） |
| [`TrafficTest.spec`](TrafficTest.spec) | PyInstaller 单文件 exe 打包配置 |
| [`pyproject.toml`](pyproject.toml) | 项目元数据、开发依赖与版本号；命令入口 `traffic-load-tester` |
| [`CHANGELOG.md`](CHANGELOG.md) | 版本变更记录 |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | CI：Windows 跑 pytest、Linux 跑 ruff |
| [`.github/workflows/build.yml`](.github/workflows/build.yml) | 打 tag 或手动触发 → 产出 exe artifact |
| [`LICENSE`](LICENSE) | MIT 许可 |

---

<a name="开发与测试"></a>

## 🧪 开发与测试

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

## 📜 许可

本项目以 **MIT** 许可发布，详见 [LICENSE](LICENSE)。

---

## ⚠️ 免责声明

**请确保在授权范围内使用**，不要对未授权的系统发起测试；超高并发可能触发操作系统端口耗尽或防火墙限制，目标服务器也需要有足够的处理能力。

---

<div align="center">
<sub>MIT License · Traffic Load Tester - Gateway Stress Tool</sub>
</div>
