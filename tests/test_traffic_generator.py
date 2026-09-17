"""负载生成器与格式化工具的测试。

说明：这里只测**不启动线程、不打开 GUI** 的纯函数部分（用 __new__ 造不带 __init__ 的实例），
所以跑起来是毫秒级、无副作用的。
"""

import hashlib
import tomllib
from pathlib import Path

import pytest

import traffic_test_gui as mod
from traffic_test_gui import TCPServer, TrafficGUI, TrafficGenerator

ROOT = Path(__file__).resolve().parents[1]


def _generator(**attrs) -> TrafficGenerator:
    """造一个不启动任何线程的 TrafficGenerator（跳过 __init__）。"""
    gen = TrafficGenerator.__new__(TrafficGenerator)
    for key, value in attrs.items():
        setattr(gen, key, value)
    return gen


def test_pick_port_only_returns_target_ports():
    gen = _generator(target_ports=[80, 443, 8080])
    for _ in range(50):
        assert gen._pick_port() in (80, 443, 8080)


def test_pick_port_single_port_alway_same():
    gen = _generator(target_ports=[9])
    assert gen._pick_port() == 9


def test_generate_payload_length_matches_packet_size():
    for size in (1, 64, 512, 1460):
        gen = _generator(packet_size=size)
        payload = gen._generate_payload()
        assert isinstance(payload, bytes)
        assert len(payload) == size


def test_generate_payload_is_random():
    gen = _generator(packet_size=64)
    samples = {gen._generate_payload() for _ in range(5)}
    assert len(samples) > 1                    # 64 字节随机，几乎不可能全同


@pytest.mark.parametrize("value,expected", [
    (0, "0 B"),
    (1023, "1023 B"),
    (1024, "1.0 KB"),
    (2048, "2.0 KB"),
    (1024 ** 2, "1.0 MB"),
    (5 * 1024 ** 2, "5.0 MB"),
    (1024 ** 3, "1.00 GB"),
])
def test_tcp_server_fmt(value, expected):
    assert TCPServer._fmt(value) == expected


@pytest.mark.parametrize("value,expected", [
    (0, "0 B"),
    (1024, "1.0 KB"),
    (1024 ** 2, "1.0 MB"),
    (1024 ** 3, "1.00 GB"),
])
def test_gui_fmt_bytes(value, expected):
    assert TrafficGUI._fmt_bytes(value) == expected


def test_version_matches_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert mod.__version__ == pyproject["project"]["version"]


def test_main_is_callable_for_console_script():
    # pyproject 的 [project.scripts] 指向 traffic_test_gui:main
    assert callable(getattr(mod, "main"))


def test_py_and_pyw_are_identical():
    """两个入口文件必须保持同步（历史上曾出现只改 .py 忘了 .pyw）。"""
    a = (ROOT / "traffic_test_gui.py").read_bytes()
    b = (ROOT / "traffic_test_gui.pyw").read_bytes()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()
