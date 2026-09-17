# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 与
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。

## [1.0.0] - 2026-09-17

首个带版本号的发布：把仓库从「能跑的脚本」整理成规范开源项目。

### Added

- `LICENSE`（MIT）、`pyproject.toml`（可 `pip install`，含 `traffic-load-tester` 命令入口）
- `tests/` pytest 测试（端口解析 / 统计计数 / 负载生成 / 双文件一致性）
- GitHub Actions：`ci.yml`（Windows 跑 pytest + Linux 跑 ruff）、`build.yml`（打 exe 并上传 artifact）
- 绿色主题（零依赖，clam 基底）：统一按钮 / 表格 / 进度条 / 滚动条配色
- `rate = 0`（不限速）时界面红字警告 —— 避免误用于本机环回压测
- 包大小与监听端口的输入校验：非数字或越界给明确提示
- 本 CHANGELOG

### Fixed

- 端口描述里的数量与实际生效端口数不一致（`443,80,443,22` 会显示 `4 port(s)`，实际只发 3 个端口）—— 由新增的测试发现并修正

- 包大小 / 监听端口输入非数字时 `tk.TclError` 静默失败（`.pyw` 无窗口模式下完全看不到报错）

[1.0.0]: https://github.com/Yata-Datacom/Traffic-Load-Tester---Gateway-Stress-Tool/releases/tag/v1.0.0
