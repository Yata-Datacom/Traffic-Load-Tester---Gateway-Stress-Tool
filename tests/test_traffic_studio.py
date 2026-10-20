"""Traffic Studio shell smoke tests."""
from __future__ import annotations

import traffic_studio


def test_studio_pages_and_version():
    app = traffic_studio.TrafficStudio()
    app.root.withdraw()
    try:
        assert set(app.pages) == {"dashboard", "traffic", "diagnostics", "history"}
        assert app.current_page == "dashboard"
        app._show_page("diagnostics")
        assert app.current_page == "diagnostics"
        assert traffic_studio.__version__ == "2.0.0"
        assert traffic_studio.diag.is_loopback("127.0.0.1")
    finally:
        app._on_close()


def test_scenario_list_contains_builtins():
    names = [s["name"] for s in traffic_studio.diag.BUILTIN_SCENARIOS]
    assert "网关 Web 压测" in names
    assert "DNS 53 压测" in names
