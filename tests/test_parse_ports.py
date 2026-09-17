"""端口表达式解析测试（parse_ports 是唯一被 UI 与生成器共用的输入解析逻辑）。"""

import pytest

from traffic_test_gui import parse_ports


def test_single_port():
    assert parse_ports("8080") == ([8080], "single port 8080")


def test_single_port_with_spaces():
    assert parse_ports("  443  ") == ([443], "single port 443")


def test_csv_dedup_and_sort():
    ports, desc = parse_ports("443, 80,443,22")
    assert ports == [22, 80, 443]
    assert "3" in desc


def test_csv_ignores_empty_items():
    ports, _ = parse_ports("80,,443,")
    assert ports == [80, 443]


def test_range():
    ports, desc = parse_ports("100-103")
    assert ports == [100, 101, 102, 103]
    assert "4" in desc


def test_range_single_element():
    assert parse_ports("1024-1024")[0] == [1024]


def test_range_with_count_is_sampled():
    ports, desc = parse_ports("100-1000:50")
    assert len(ports) == 50
    assert len(set(ports)) == 50                      # 采样不重复
    assert all(100 <= p <= 1000 for p in ports)       # 不越界
    assert ports == sorted(ports)
    assert "50 ports from 100-1000" == desc


def test_range_with_count_clamped_to_range_size():
    ports, _ = parse_ports("1-10:999")
    assert len(ports) == 10                            # 不能超过区间元素个数


def test_empty_input():
    assert parse_ports("") == ([], "empty")
    assert parse_ports("   ") == ([], "empty")


@pytest.mark.parametrize("bad", [
    "0",              # 端口下界
    "65536",          # 端口上界
    "abc",
    "-1",
    "1-0",            # 区间反了
    "0-10",           # 区间下界非法
    "1024-65536",     # 区间上界非法
    "80,abc",         # 逗号列表里混入非数字
    "100-200:abc",    # 采样数量非数字
    "1-999999999",    # 天文数字区间必须被拒（不能尝试分配内存）
])
def test_invalid_inputs_return_empty(bad):
    ports, desc = parse_ports(bad)
    assert ports == []
    assert "invalid" in desc


def test_extreme_but_legal_range_does_not_hang():
    ports, _ = parse_ports("1-65535")
    assert len(ports) == 65535
