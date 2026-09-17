"""统计计数器测试（Stats 被所有发包线程并发写，锁定与速率换算必须正确）。"""

import threading

from traffic_test_gui import Stats


def test_add_accumulates_packets_and_bytes():
    s = Stats()
    s.add(packet_size=100, count=3)
    s.add(packet_size=100, count=2)
    pps, bps, packets, nbytes = s.snapshot()
    assert packets == 5
    assert nbytes == 500
    assert pps == 0.0 and bps == 0.0          # 没 tick 之前速率是 0


def test_tick_computes_rates():
    s = Stats()
    s.add(packet_size=1000, count=10)
    s.tick(interval=2.0)
    pps, bps, _, _ = s.snapshot()
    assert pps == 5.0                          # 10 包 / 2 秒
    assert bps == 5000.0                       # 10000 字节 / 2 秒


def test_tick_measures_delta_only():
    s = Stats()
    s.add(packet_size=100, count=10)
    s.tick(1.0)
    s.tick(1.0)                                # 第二轮没有新增 → 速率回到 0
    pps, bps, packets, _ = s.snapshot()
    assert (pps, bps) == (0.0, 0.0)
    assert packets == 10                       # 总量不清零


def test_tick_with_zero_interval_is_safe():
    s = Stats()
    s.add(packet_size=100, count=5)
    s.tick(0)
    pps, bps, _, _ = s.snapshot()
    assert (pps, bps) == (0.0, 0.0)            # 除零保护，不抛异常


def test_concurrent_add_is_thread_safe():
    s = Stats()
    threads = [threading.Thread(target=lambda: [s.add(1, 1) for _ in range(1000)])
               for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    _, _, packets, nbytes = s.snapshot()
    assert packets == 8000
    assert nbytes == 8000
