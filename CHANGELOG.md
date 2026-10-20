# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 与
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。

## [2.0.0] - 2026-10-20

UI/工作区重构 + 更多测试能力。发包引擎继续复用 V1。

### Added

- **Traffic Studio 工作区**：总览 / 流量测试 / 目标诊断 / 结果历史
- **目标诊断**：ICMP Ping（丢包、RTT、抖动）、DNS 解析、TCP 端口探测、默认网关
- **测试场景**：Web / DNS / 视频 UDP / TCP SYN 内置场景，支持保存自定义场景
- **持续时间**：0 = 手动停止，或按秒自动停止
- **结果历史**：`runs.json` 自动记录，历史页查看、导出 CSV、清空
- **安全默认值**：默认目标改为文档地址 `192.0.2.10`，启动前必须勾选授权
- **中文界面**：工作区、参数、诊断、历史
- `traffic_studio.py` / `traffic_studio.pyw` / `traffic_diag.py`
- `TrafficStudio.spec` 打包配置
- `docs/USER_GUIDE.md` / `docs/USER_GUIDE.zh-CN.md`
- 合成演示截图

### Changed

- `pyproject.toml` 版本 2.0.0，新增 `traffic-studio` 命令
- V1 入口 `traffic_test_gui.py` / `.pyw` 版本号同步为 2.0.0，默认目标同步为文档地址
- `.gitignore` 增加 `runs.json`、`scenarios.json`、`reports/`

### Tests

- **55 项 pytest**：新增诊断解析、目标风险、记录/CSV、场景完整性、V2 工作区冒烟测试

## [1.1.0] - 2026-09-17

工程化改造：把仓库从「能跑的脚本」整理成规范开源项目。

### Added

- `LICENSE`（MIT）
- `pyproject.toml`：PEP 621 元数据 + `[project.scripts]` 命令入口 + ruff/pytest 配置，
  现在可以 `pip install -e .`（装好后运行 `traffic-load-tester` 即可启动）
- `tests/`：43 项 pytest —— 端口表达式解析、Stats 并发计数与速率换算、负载生成、
  两个入口文件（`.py`/`.pyw`）逐字节一致、版本号与 `pyproject.toml` 一致
- GitHub Actions：`.github/workflows/ci.yml`（Windows 跑 pytest、Linux 跑 ruff）、
  `.github/workflows/build.yml`（打 tag 或手动触发 → PyInstaller 打包并上传 exe artifact）
- 绿色主题（零依赖，clam 基底）：统一按钮 / 表格 / 进度条 / 滚动条配色
- `rate = 0`（不限速）时界面红字警告，避免误用于本机环回压测
- 包大小与监听端口的输入校验：非数字或越界给明确提示
- 本 CHANGELOG 与 README 徽章

### Fixed

- `parse_ports` 的端口描述与实际生效端口数不一致：输入 `443,80,443,22` 会显示 `4 port(s)`，
  实际只发 3 个端口（**由新增测试发现**）
- 包大小 / 监听端口输入非数字时 `tk.TclError` 静默失败（`.pyw` 无窗口模式下完全看不到报错）

## [1.0.0] - 2026-07-08

### Added

- 首个发布：多端口表达式（`80,443` / `100-1000` / `100-1000:50`）、TCP SYN 模式、
  网关自动探测、实时 PPS 与带宽显示

[1.1.0]: https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/releases/tag/v1.1.0
[1.0.0]: https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/releases/tag/v1.0.0
