"""Traffic Studio 2.0 — NADT-style shell over the proven traffic engine.

The stress engine, TCP receiver, port parser and gateway detector remain in
``traffic_test_gui.py`` (legacy UI kept for compatibility). This module owns the
new workspace shell, diagnostics, scenarios and run history.
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import traffic_diag as diag
import traffic_test_gui as core

__version__ = "2.0.0"

BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
HISTORY_FILE = os.path.join(BASE_DIR, "runs.json")
SCENARIO_FILE = os.path.join(BASE_DIR, "scenarios.json")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

# palette
BG = "#eef4fa"
PANEL = "#ffffff"
NAVY = "#0b1f3a"
NAVY2 = "#102b4e"
ACCENT = "#0284c7"
ACCENT2 = "#38bdf8"
GREEN = "#059669"
RED = "#dc2626"
AMBER = "#b45309"
MUTED = "#64748b"
LINE = "#d6e2ee"
HEADER_BG = "#e5eff9"

FONT = ("Microsoft YaHei UI", 9)
FONT_B = ("Microsoft YaHei UI", 9, "bold")
FONT_H = ("Microsoft YaHei UI", 12, "bold")
FONT_NUM = ("Consolas", 20, "bold")
FONT_MONO = ("Consolas", 9)

NAV_ITEMS = [
    ("dashboard", "总览", "Overview", "测试"),
    ("traffic", "流量测试", "Load test", "测试"),
    ("diagnostics", "目标诊断", "Diagnostics", "测试"),
    ("history", "结果历史", "History", "记录"),
]


def setup_studio_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    root.configure(bg=BG)
    style.configure(".", background=BG, foreground=NAVY, bordercolor=LINE,
                    lightcolor=BG, darkcolor=BG, focuscolor=ACCENT)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=NAVY, font=FONT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Microsoft YaHei UI", 8))
    style.configure("Card.TFrame", background=PANEL)
    style.configure("Card.TLabel", background=PANEL, foreground=NAVY, font=FONT)
    style.configure("CardMuted.TLabel", background=PANEL, foreground=MUTED,
                    font=("Microsoft YaHei UI", 8))
    style.configure("Card.TLabelframe", background=PANEL, bordercolor=LINE,
                    relief="solid", borderwidth=1, padding=10)
    style.configure("Card.TLabelframe.Label", background=PANEL, foreground=NAVY, font=FONT_H)
    style.configure("TButton", background="#e2ebf5", foreground=NAVY, borderwidth=0,
                    focusthickness=0, padding=(10, 6), font=FONT)
    style.map("TButton", background=[("pressed", "#c7d8ea"), ("active", "#d3e2f2")])
    style.configure("Accent.TButton", background=ACCENT, foreground="white",
                    padding=(12, 7), font=FONT_B)
    style.map("Accent.TButton", background=[("pressed", "#075985"), ("active", ACCENT2)],
              foreground=[("disabled", "#bae6fd")])
    style.configure("Green.TButton", background=GREEN, foreground="white",
                    padding=(12, 7), font=FONT_B)
    style.map("Green.TButton", background=[("pressed", "#065f46"), ("active", "#10b981")])
    style.configure("Danger.TButton", background=RED, foreground="white",
                    padding=(10, 6), font=FONT_B)
    style.map("Danger.TButton", background=[("pressed", "#991b1b"), ("active", "#ef4444")])
    style.configure("TEntry", fieldbackground="white", foreground=NAVY, bordercolor=LINE,
                    padding=4, insertcolor=ACCENT)
    style.configure("TCombobox", fieldbackground="white", foreground=NAVY,
                    bordercolor=LINE, padding=4, arrowcolor=ACCENT)
    style.configure("TCheckbutton", background=BG, foreground=NAVY, font=FONT, focuscolor=ACCENT)
    style.configure("Card.TCheckbutton", background=PANEL, foreground=NAVY, font=FONT)
    style.configure("TRadiobutton", background=PANEL, foreground=NAVY, font=FONT)
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background="#dbe8f4", foreground=MUTED,
                    padding=(14, 6), borderwidth=0, font=FONT)
    style.map("TNotebook.Tab", background=[("selected", PANEL)],
              foreground=[("selected", ACCENT)])
    style.configure("Treeview", background="white", fieldbackground="white",
                    foreground=NAVY, rowheight=26, borderwidth=0, font=FONT)
    style.configure("Treeview.Heading", background=HEADER_BG, foreground="#28415f",
                    padding=(8, 5), relief="flat", font=FONT_B)
    style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", NAVY)])
    style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor="#dbe8f4",
                    borderwidth=0, thickness=8)
    style.configure("Vertical.TScrollbar", background="#c7d8ea", troughcolor=BG,
                    borderwidth=0, arrowsize=12)
    style.configure("Horizontal.TScrollbar", background="#c7d8ea", troughcolor=BG,
                    borderwidth=0, arrowsize=12)


class NavItem(tk.Frame):
    def __init__(self, parent, key: str, zh: str, en: str, command):
        super().__init__(parent, bg=NAVY, cursor="hand2")
        self.key = key
        self.command = command
        self.active = False
        self.bar = tk.Frame(self, bg=NAVY, width=4)
        self.bar.pack(side=tk.LEFT, fill=tk.Y)
        self.zh = tk.Label(self, text=zh, bg=NAVY, fg="#dbeafe",
                           font=("Microsoft YaHei UI", 9, "bold"), anchor="w")
        self.zh.pack(fill=tk.X, padx=(10, 6), pady=(6, 0))
        self.en = tk.Label(self, text=en, bg=NAVY, fg="#7f9cbb",
                           font=("Microsoft YaHei UI", 7), anchor="w")
        self.en.pack(fill=tk.X, padx=(10, 6), pady=(0, 5))
        for widget in (self, self.bar, self.zh, self.en):
            widget.bind("<Button-1>", lambda _e: self.command(self.key))
            widget.bind("<Enter>", lambda _e: self._hover(True))
            widget.bind("<Leave>", lambda _e: self._hover(False))

    def _hover(self, on: bool) -> None:
        if self.active:
            return
        color = "#15345a" if on else NAVY
        for widget in (self, self.bar):
            widget.configure(bg=color)
        for widget in (self.zh, self.en):
            widget.configure(bg=color)

    def set_active(self, active: bool) -> None:
        self.active = active
        bg = "#123b66" if active else NAVY
        for widget in (self, self.bar):
            widget.configure(bg=bg)
        self.zh.configure(bg=bg, fg="#ffffff" if active else "#dbeafe")
        self.en.configure(bg=bg, fg="#bae6fd" if active else "#7f9cbb")
        self.bar.configure(bg=ACCENT2 if active else NAVY)


class TrafficStudio:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Traffic Studio {__version__} — 网关流量测试工作台")
        self.root.geometry("1440x900")
        self.root.minsize(1180, 740)
        setup_studio_style(self.root)

        self.generator: core.TrafficGenerator | None = None
        self.tcp_server: core.TCPServer | None = None
        self.monitor_id = None
        self.auto_stop_id = None
        self.start_time = 0.0
        self.current_duration = 0
        self.records = diag.load_records(HISTORY_FILE)
        self.custom_scenarios = self._load_scenarios()
        self.gateway_map: dict[str, str] = {}
        self._diag_queue: queue.Queue = queue.Queue()
        self._diag_busy = False
        self.pages: dict[str, tuple[ttk.Frame, ttk.Frame]] = {}
        self.nav: dict[str, NavItem] = {}

        self._build_ui()
        self._start_monitor()
        self._show_page("dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── shell ─────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self._build_header()
        self._build_statusbar()
        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True)
        self._build_rail(body)
        self.content = ttk.Frame(body)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self._build_dashboard()
        self._build_traffic()
        self._build_diagnostics()
        self._build_history()
        for idx, key in enumerate(("dashboard", "traffic", "diagnostics", "history"), 1):
            self.root.bind_all(f"<Control-Key-{idx}>", lambda _e, k=key: self._show_page(k))
        self.root.bind_all("<Control-Return>", lambda _e: self._start_test())
        self.root.bind_all("<Escape>", lambda _e: self._stop_test())

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=NAVY, height=64)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        logo = tk.Frame(header, bg=NAVY2, width=38, height=38)
        logo.pack(side=tk.LEFT, padx=(16, 10), pady=13)
        logo.pack_propagate(False)
        tk.Label(logo, text="TS", bg=NAVY2, fg=ACCENT2,
                 font=("Consolas", 13, "bold")).pack(expand=True)
        titles = tk.Frame(header, bg=NAVY)
        titles.pack(side=tk.LEFT)
        tk.Label(titles, text="TRAFFIC STUDIO", bg=NAVY, fg="white",
                 font=("Microsoft YaHei UI", 13, "bold"), anchor="w").pack(anchor="w")
        tk.Label(titles, text="网关流量测试 · 目标诊断 · 结果历史",
                 bg=NAVY, fg="#8bb3d6", font=("Microsoft YaHei UI", 8), anchor="w").pack(anchor="w")
        chips = tk.Frame(header, bg=NAVY)
        chips.pack(side=tk.RIGHT, padx=16)
        tk.Label(chips, text=f"v{__version__}", bg="#17395f", fg="#93c5fd",
                 font=("Consolas", 8), padx=8, pady=3).pack(side=tk.LEFT, padx=4)
        self.header_records = tk.Label(chips, text="记录 0", bg="#17395f", fg="#93c5fd",
                                       font=("Consolas", 8), padx=8, pady=3)
        self.header_records.pack(side=tk.LEFT, padx=4)

    def _build_statusbar(self) -> None:
        bar = tk.Frame(self.root, bg=PANEL, height=26)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        tk.Frame(bar, bg=ACCENT, width=3).pack(side=tk.LEFT, fill=tk.Y)
        self.status_var = tk.StringVar(value="就绪 · 仅对已授权目标测试")
        tk.Label(bar, textvariable=self.status_var, bg=PANEL, fg=MUTED,
                 font=("Microsoft YaHei UI", 8), padx=10).pack(side=tk.LEFT)
        tk.Label(bar, text="Ctrl+1…4 切换  ·  Ctrl+Enter 开始  ·  Esc 停止",
                 bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 8),
                 padx=12).pack(side=tk.RIGHT)

    def _build_rail(self, body) -> None:
        rail = tk.Frame(body, bg=NAVY, width=188)
        rail.pack(side=tk.LEFT, fill=tk.Y)
        rail.pack_propagate(False)
        tk.Label(rail, text="工作区 / WORKSPACES", bg=NAVY, fg="#5f7f9e",
                 font=("Microsoft YaHei UI", 7), anchor="w", padx=14).pack(
            fill=tk.X, pady=(10, 4))
        last_section = None
        for key, zh, en, section in NAV_ITEMS:
            if section != last_section:
                tk.Label(rail, text=section, bg=NAVY, fg="#5f7f9e",
                         font=("Microsoft YaHei UI", 7), anchor="w", padx=14).pack(
                    fill=tk.X, pady=(8, 2))
                last_section = section
            item = NavItem(rail, key, zh, en, self._show_page)
            item.pack(fill=tk.X, padx=8, pady=2)
            self.nav[key] = item
        tk.Label(rail, text="V2 shell · V1 engine", bg=NAVY, fg="#4d6b88",
                 font=("Consolas", 7)).pack(side=tk.BOTTOM, pady=10)

    def _page(self, key: str, title: str, subtitle: str, hint: str) -> ttk.Frame:
        page = ttk.Frame(self.content)
        page.grid(row=0, column=0, sticky="nsew")
        header = tk.Frame(page, bg=BG)
        header.pack(fill=tk.X, padx=16, pady=(12, 4))
        tk.Frame(header, bg=ACCENT, width=5, height=36).pack(side=tk.LEFT, padx=(0, 10))
        titles = tk.Frame(header, bg=BG)
        titles.pack(side=tk.LEFT)
        tk.Label(titles, text=title, bg=BG, fg=NAVY, font=FONT_H, anchor="w").pack(anchor="w")
        tk.Label(titles, text=subtitle, bg=BG, fg=MUTED,
                 font=("Microsoft YaHei UI", 8), anchor="w").pack(anchor="w")
        tk.Label(header, text=hint, bg=BG, fg=MUTED,
                 font=("Microsoft YaHei UI", 8)).pack(side=tk.RIGHT)
        tk.Frame(page, bg=LINE, height=1).pack(fill=tk.X, padx=16)
        body = ttk.Frame(page)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)
        self.pages[key] = (page, body)
        return body

    def _show_page(self, key: str) -> None:
        if not hasattr(self, "pages") or key not in self.pages:
            return
        page, _body = self.pages[key]
        page.tkraise()
        self.current_page = key
        for name, item in self.nav.items():
            item.set_active(name == key)
        if key == "dashboard":
            self._refresh_dashboard()
        elif key == "history":
            self._refresh_history()

    # ── dashboard ─────────────────────────────────────────────────────
    def _build_dashboard(self) -> None:
        body = self._page("dashboard", "总览", "测试入口 · 安全提示 · 最近结果", "Ctrl+1…4 切换")
        hero = tk.Frame(body, bg=NAVY, highlightthickness=0)
        hero.pack(fill=tk.X, pady=(0, 10))
        left = tk.Frame(hero, bg=NAVY)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=18, pady=16)
        tk.Label(left, text="今天要测什么？", bg=NAVY, fg="white",
                 font=("Microsoft YaHei UI", 16, "bold"), anchor="w").pack(anchor="w")
        tk.Label(left, text="先做目标诊断，再按授权范围做流量测试；结果自动进入历史。",
                 bg=NAVY, fg="#9dc0de", font=("Microsoft YaHei UI", 8), anchor="w").pack(
            anchor="w", pady=(4, 10))
        actions = tk.Frame(left, bg=NAVY)
        actions.pack(anchor="w")
        for text, key, style in (("开始流量测试", "traffic", "Accent.TButton"),
                                 ("目标诊断", "diagnostics", "TButton"),
                                 ("结果历史", "history", "TButton")):
            ttk.Button(actions, text=text, style=style,
                       command=lambda k=key: self._show_page(k)).pack(side=tk.LEFT, padx=(0, 8))
        warning = tk.Frame(hero, bg="#152e4b")
        warning.pack(side=tk.RIGHT, padx=14, pady=14)
        tk.Label(warning, text="⚠ 仅限授权目标", bg="#152e4b", fg="#fbbf24",
                 font=("Microsoft YaHei UI", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 0))
        tk.Label(warning, text="不要对公网/他人设备做压力测试\n高并发前先确认业务窗口",
                 bg="#152e4b", fg="#cbd5e1", font=("Microsoft YaHei UI", 8),
                 justify=tk.LEFT).pack(anchor="w", padx=12, pady=(2, 8))

        cards = tk.Frame(body, bg=BG)
        cards.pack(fill=tk.X, pady=(0, 10))
        self.dash_last_pps = tk.StringVar(value="0")
        self.dash_last_mbps = tk.StringVar(value="0")
        self.dash_records = tk.StringVar(value=str(len(self.records)))
        self.dash_scenarios = tk.StringVar(value=str(len(diag.BUILTIN_SCENARIOS) + len(self.custom_scenarios)))
        for idx, (title, var, color) in enumerate((
                ("最近 PPS", self.dash_last_pps, ACCENT),
                ("最近 Mbps", self.dash_last_mbps, GREEN),
                ("历史记录", self.dash_records, NAVY),
                ("可用场景", self.dash_scenarios, AMBER))):
            card = tk.Frame(cards, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0, 8) if idx < 3 else 0)
            cards.grid_columnconfigure(idx, weight=1)
            tk.Label(card, text=title, bg=PANEL, fg=MUTED,
                     font=("Microsoft YaHei UI", 8), anchor="w").pack(
                fill=tk.X, padx=12, pady=(8, 0))
            tk.Label(card, textvariable=var, bg=PANEL, fg=color,
                     font=("Consolas", 20, "bold"), anchor="w").pack(
                fill=tk.X, padx=12, pady=(0, 8))

        lower = tk.Frame(body, bg=BG)
        lower.pack(fill=tk.BOTH, expand=True)
        recent = ttk.LabelFrame(lower, text="最近结果 / Recent runs", style="Card.TLabelframe")
        recent.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        cols = ("time", "target", "protocol", "pps", "mbps")
        self.dash_tree = ttk.Treeview(recent, columns=cols, show="headings", height=8)
        for col, text, width in (("time", "时间", 140), ("target", "目标", 160),
                                 ("protocol", "协议", 80), ("pps", "平均 PPS", 100),
                                 ("mbps", "平均 Mbps", 100)):
            self.dash_tree.heading(col, text=text)
            self.dash_tree.column(col, width=width, anchor="w", stretch=(col == "target"))
        self.dash_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        tips = ttk.LabelFrame(lower, text="安全流程 / Workflow", style="Card.TLabelframe")
        tips.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        for line in ("1. 目标诊断：Ping / DNS / TCP 端口",
                     "2. 选择场景，确认授权",
                     "3. 流量测试：观察 PPS / Mbps",
                     "4. 结果自动写入历史，可导出 CSV"):
            ttk.Label(tips, text=line, style="Card.TLabel").pack(anchor="w", padx=8, pady=5)

    def _refresh_dashboard(self) -> None:
        self.dash_records.set(str(len(self.records)))
        self.dash_scenarios.set(str(len(diag.BUILTIN_SCENARIOS) + len(self.custom_scenarios)))
        self.header_records.configure(text=f"记录 {len(self.records)}")
        if self.records:
            last = self.records[0]
            self.dash_last_pps.set(f"{float(last.get('avg_pps', 0)):,.0f}")
            self.dash_last_mbps.set(f"{float(last.get('avg_mbps', 0)):,.2f}")
        else:
            self.dash_last_pps.set("0")
            self.dash_last_mbps.set("0")
        if hasattr(self, "dash_tree"):
            self.dash_tree.delete(*self.dash_tree.get_children())
            for record in self.records[:8]:
                self.dash_tree.insert("", tk.END, values=(
                    record.get("time", ""), record.get("target", ""),
                    record.get("protocol", ""), f"{float(record.get('avg_pps', 0)):,.0f}",
                    f"{float(record.get('avg_mbps', 0)):,.2f}"))

    # ── traffic page ──────────────────────────────────────────────────
    def _build_traffic(self) -> None:
        body = self._page("traffic", "流量测试", "TCP / UDP / TCP SYN · 网关压力测试",
                          "Ctrl+Enter 开始 · Esc 停止")
        top = ttk.Frame(body)
        top.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(top, text="场景：", style="TLabel").pack(side=tk.LEFT)
        self.scenario_var = tk.StringVar(value="自定义")
        self.scenario_combo = ttk.Combobox(top, textvariable=self.scenario_var,
                                           state="readonly", width=28)
        self.scenario_combo.pack(side=tk.LEFT, padx=4)
        self.scenario_combo.bind("<<ComboboxSelected>>", self._on_scenario_selected)
        ttk.Button(top, text="加载场景", command=self._load_selected_scenario).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="保存当前", command=self._save_scenario).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="删除自定义", command=self._delete_scenario).pack(side=tk.LEFT, padx=4)
        self._refresh_scenarios()

        split = tk.Frame(body, bg=BG)
        split.pack(fill=tk.BOTH, expand=True)
        left = ttk.LabelFrame(split, text="测试配置 / Configuration", style="Card.TLabelframe")
        left.pack(side=tk.LEFT, anchor="n", padx=(0, 8))
        left.configure(width=500)

        # target + gateway
        ttk.Label(left, text="目标 IP / 主机", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", pady=3)
        self.ip_var = tk.StringVar(value="192.0.2.10")
        ttk.Entry(left, textvariable=self.ip_var, width=24).grid(
            row=0, column=1, sticky="w", padx=6, pady=3)
        self.risk_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.risk_var, style="CardMuted.TLabel").grid(
            row=0, column=2, columnspan=2, sticky="w", padx=6)
        self.ip_var.trace_add("write", lambda *_: self._update_risk())

        ttk.Label(left, text="端口表达式", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=3)
        self.port_var = tk.StringVar(value="8080")
        ttk.Entry(left, textvariable=self.port_var, width=24).grid(
            row=1, column=1, sticky="w", padx=6, pady=3)
        ttk.Label(left, text="8080 / 80,443 / 100-1000 / 100-1000:50",
                  style="CardMuted.TLabel").grid(row=1, column=2, columnspan=2, sticky="w")

        ttk.Label(left, text="协议", style="Card.TLabel").grid(
            row=2, column=0, sticky="w", pady=3)
        self.protocol_var = tk.StringVar(value="UDP")
        ttk.Combobox(left, textvariable=self.protocol_var, values=["UDP", "TCP", "TCP SYN"],
                     state="readonly", width=10).grid(row=2, column=1, sticky="w", padx=6, pady=3)

        ttk.Label(left, text="默认网关", style="Card.TLabel").grid(
            row=3, column=0, sticky="w", pady=3)
        self.gateway_var = tk.StringVar(value="")
        self.gateway_combo = ttk.Combobox(left, textvariable=self.gateway_var,
                                          values=[], state="readonly", width=24)
        self.gateway_combo.grid(row=3, column=1, sticky="w", padx=6, pady=3)
        self.gateway_combo.bind("<<ComboboxSelected>>", self._on_gateway_selected)
        ttk.Button(left, text="探测网关", command=self._detect_gateways).grid(
            row=3, column=2, sticky="w", padx=6)

        ttk.Label(left, text="并发线程", style="Card.TLabel").grid(
            row=4, column=0, sticky="w", pady=(8, 3))
        self.concurrency_var = tk.IntVar(value=10)
        ttk.Scale(left, from_=1, to=500, variable=self.concurrency_var,
                  orient=tk.HORIZONTAL, length=220,
                  command=lambda v: self._set_int_var(self.concurrency_var, v)).grid(
            row=4, column=1, columnspan=2, sticky="w", padx=6, pady=(8, 3))
        self.conc_label = ttk.Label(left, text="10", style="Card.TLabel", width=5)
        self.conc_label.grid(row=4, column=3, sticky="w")
        self.concurrency_var.trace_add("write", lambda *_: self.conc_label.config(
            text=str(self.concurrency_var.get())))

        ttk.Label(left, text="包大小 (B)", style="Card.TLabel").grid(
            row=5, column=0, sticky="w", pady=(8, 3))
        self.pkt_size_var = tk.IntVar(value=1024)
        sizes = ttk.Frame(left)
        sizes.grid(row=5, column=1, columnspan=3, sticky="w", padx=6, pady=(8, 3))
        for size in (64, 256, 512, 1024, 1460):
            ttk.Radiobutton(sizes, text=str(size), variable=self.pkt_size_var,
                            value=size).pack(side=tk.LEFT, padx=1)
        ttk.Entry(sizes, textvariable=self.pkt_size_var, width=7).pack(side=tk.LEFT, padx=6)

        ttk.Label(left, text="速率 (pkt/s/线程)", style="Card.TLabel").grid(
            row=6, column=0, sticky="w", pady=(8, 3))
        self.rate_var = tk.IntVar(value=1000)
        ttk.Scale(left, from_=0, to=50000, variable=self.rate_var,
                  orient=tk.HORIZONTAL, length=220,
                  command=lambda v: self._set_int_var(self.rate_var, v)).grid(
            row=6, column=1, columnspan=2, sticky="w", padx=6, pady=(8, 3))
        self.rate_label = ttk.Label(left, text="1000", style="Card.TLabel", width=8)
        self.rate_label.grid(row=6, column=3, sticky="w")
        self.rate_var.trace_add("write", lambda *_: self._update_rate())
        self.rate_warn_var = tk.StringVar(value="")
        tk.Label(left, textvariable=self.rate_warn_var, bg=PANEL, fg=RED,
                 font=("Microsoft YaHei UI", 8, "bold"), anchor="w", justify=tk.LEFT).grid(
            row=7, column=0, columnspan=4, sticky="w", pady=(2, 0))

        ttk.Label(left, text="持续时间 (秒)", style="Card.TLabel").grid(
            row=8, column=0, sticky="w", pady=(6, 3))
        self.duration_var = tk.IntVar(value=0)
        ttk.Spinbox(left, from_=0, to=86400, textvariable=self.duration_var,
                    width=10).grid(row=8, column=1, sticky="w", padx=6, pady=(6, 3))
        ttk.Label(left, text="0 = 手动停止", style="CardMuted.TLabel").grid(
            row=8, column=2, columnspan=2, sticky="w")

        self.authorized_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="我确认已获得对该目标的测试授权",
                        variable=self.authorized_var,
                        style="Card.TCheckbutton").grid(
            row=9, column=0, columnspan=4, sticky="w", pady=(8, 0))

        actions = tk.Frame(left, bg=PANEL)
        actions.grid(row=10, column=0, columnspan=4, sticky="w", pady=(8, 2))
        self.start_btn = ttk.Button(actions, text="开始测试", style="Green.TButton",
                                    command=self._start_test)
        self.start_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(actions, text="停止", style="Danger.TButton",
                                   command=self._stop_test, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=6)
        self.test_status_var = tk.StringVar(value="Idle")
        ttk.Label(actions, textvariable=self.test_status_var, style="CardMuted.TLabel").pack(
            side=tk.LEFT, padx=10)

        # right: stats + receiver + log
        right = tk.Frame(split, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats = tk.Frame(right, bg=BG)
        stats.pack(fill=tk.X, pady=(0, 6))
        self.pps_var = tk.StringVar(value="0")
        self.mbps_var = tk.StringVar(value="0")
        self.total_pkt_var = tk.StringVar(value="0")
        self.elapsed_var = tk.StringVar(value="00:00:00")
        for idx, (label, var, color) in enumerate((
                ("PPS", self.pps_var, ACCENT), ("Mbps", self.mbps_var, GREEN),
                ("总包数", self.total_pkt_var, NAVY), ("时长", self.elapsed_var, AMBER))):
            card = tk.Frame(stats, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0, 6) if idx < 3 else 0)
            stats.grid_columnconfigure(idx, weight=1)
            tk.Label(card, text=label, bg=PANEL, fg=MUTED,
                     font=("Microsoft YaHei UI", 8), anchor="w").pack(
                fill=tk.X, padx=10, pady=(6, 0))
            tk.Label(card, textvariable=var, bg=PANEL, fg=color,
                     font=("Consolas", 16, "bold"), anchor="w").pack(
                fill=tk.X, padx=10, pady=(0, 6))

        self.progress = ttk.Progressbar(right, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X, pady=(0, 6))

        receiver = ttk.LabelFrame(right, text="本机 TCP 接收端 / Built-in receiver",
                                  style="Card.TLabelframe")
        receiver.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(receiver, text="监听端口", style="Card.TLabel").pack(side=tk.LEFT)
        self.tcp_srv_port_var = tk.IntVar(value=8080)
        ttk.Entry(receiver, textvariable=self.tcp_srv_port_var, width=8).pack(side=tk.LEFT, padx=4)
        self.tcp_srv_start_btn = ttk.Button(receiver, text="启动", style="Accent.TButton",
                                            command=self._start_receiver)
        self.tcp_srv_start_btn.pack(side=tk.LEFT, padx=4)
        self.tcp_srv_stop_btn = ttk.Button(receiver, text="停止", style="Danger.TButton",
                                          command=self._stop_receiver, state=tk.DISABLED)
        self.tcp_srv_stop_btn.pack(side=tk.LEFT, padx=4)
        self.tcp_srv_status_var = tk.StringVar(value="Stopped")
        ttk.Label(receiver, textvariable=self.tcp_srv_status_var,
                  style="CardMuted.TLabel").pack(side=tk.LEFT, padx=8)
        self.tcp_srv_rx_var = tk.StringVar(value="")
        ttk.Label(receiver, textvariable=self.tcp_srv_rx_var,
                  style="Card.TLabel").pack(side=tk.RIGHT, padx=6)

        log_frame = ttk.LabelFrame(right, text="日志 / Log", style="Card.TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = tk.Text(log_frame, height=10, font=FONT_MONO, state=tk.DISABLED,
                                bg="#fbfdff", fg=NAVY, relief="flat", wrap="word")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self._update_risk()
        self._update_rate()

    @staticmethod
    def _set_int_var(var: tk.IntVar, value: str) -> None:
        var.set(int(float(value)))

    def _update_risk(self) -> None:
        self.risk_var.set(diag.target_risk(self.ip_var.get()))

    def _update_rate(self) -> None:
        self.rate_label.config(text=str(self.rate_var.get()))
        if self.rate_var.get() == 0:
            self.rate_warn_var.set("⚠ rate=0 为不限速全速发包，CPU/网卡占用很高")
        else:
            self.rate_warn_var.set("")

    # ── scenarios ─────────────────────────────────────────────────────
    def _load_scenarios(self) -> list[dict]:
        import json
        path = Path(SCENARIO_FILE)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def _save_scenarios(self) -> None:
        import json
        path = Path(SCENARIO_FILE)
        path.write_text(json.dumps(self.custom_scenarios, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    def _refresh_scenarios(self) -> None:
        names = [s["name"] for s in diag.BUILTIN_SCENARIOS] + [s["name"] for s in self.custom_scenarios]
        self.scenario_combo["values"] = names + ["自定义"]
        if self.scenario_var.get() not in names + ["自定义"]:
            self.scenario_var.set("自定义")

    def _get_scenario(self, name: str) -> dict | None:
        for scenario in diag.BUILTIN_SCENARIOS + self.custom_scenarios:
            if scenario["name"] == name:
                return scenario
        return None

    def _on_scenario_selected(self, _event=None) -> None:
        self._load_selected_scenario()

    def _load_selected_scenario(self) -> None:
        scenario = self._get_scenario(self.scenario_var.get())
        if not scenario:
            return
        self.protocol_var.set(scenario.get("protocol", "UDP"))
        self.port_var.set(str(scenario.get("ports", "8080")))
        self.pkt_size_var.set(int(scenario.get("packet_size", 1024)))
        self.rate_var.set(int(scenario.get("rate", 1000)))
        self.concurrency_var.set(int(scenario.get("concurrency", 10)))
        self._log(f"场景已加载：{scenario['name']}")
        self.status_var.set(f"场景：{scenario['name']}")

    def _save_scenario(self) -> None:
        name = simpledialog.askstring("保存场景", "场景名称：", parent=self.root)
        if not name:
            return
        name = name.strip()
        if any(s["name"] == name for s in diag.BUILTIN_SCENARIOS + self.custom_scenarios):
            messagebox.showwarning("保存场景", "名称已存在，请换一个。")
            return
        try:
            scenario = {
                "name": name,
                "description": "自定义场景",
                "protocol": self.protocol_var.get(),
                "ports": self.port_var.get().strip(),
                "packet_size": int(self.pkt_size_var.get()),
                "rate": int(self.rate_var.get()),
                "concurrency": int(self.concurrency_var.get()),
            }
        except (tk.TclError, ValueError):
            messagebox.showerror("保存场景", "当前参数不是有效数字。")
            return
        self.custom_scenarios.append(scenario)
        self._save_scenarios()
        self._refresh_scenarios()
        self.scenario_var.set(name)
        self._log(f"场景已保存：{name}")

    def _delete_scenario(self) -> None:
        name = self.scenario_var.get()
        custom = [s for s in self.custom_scenarios if s["name"] == name]
        if not custom:
            messagebox.showinfo("删除场景", "内置场景不可删除。")
            return
        if not messagebox.askyesno("删除场景", f"删除自定义场景「{name}」？"):
            return
        self.custom_scenarios = [s for s in self.custom_scenarios if s["name"] != name]
        self._save_scenarios()
        self.scenario_var.set("自定义")
        self._refresh_scenarios()

    # ── gateways ─────────────────────────────────────────────────────
    def _detect_gateways(self) -> None:
        gateways = core.detect_gateways()
        if not gateways:
            messagebox.showwarning("探测网关", "未发现默认网关（PowerShell 不可用或无活动网卡）。")
            self._log("网关探测：未发现")
            return
        self.gateway_map = {display: ip for display, ip in gateways}
        self.gateway_combo["values"] = [g[0] for g in gateways]
        self.gateway_combo.current(0)
        self._on_gateway_selected()
        self._log(f"网关探测：找到 {len(gateways)} 个默认网关")
        for display, ip in gateways:
            self._log(f"  {display}")

    def _on_gateway_selected(self, _event=None) -> None:
        ip = self.gateway_map.get(self.gateway_var.get())
        if ip:
            self.ip_var.set(ip)

    # ── traffic start/stop ────────────────────────────────────────────
    def _start_test(self) -> None:
        if self.generator and self.generator.running:
            return
        ip = self.ip_var.get().strip()
        if not ip:
            messagebox.showerror("参数错误", "目标 IP / 主机不能为空。")
            return
        if not self.authorized_var.get():
            messagebox.showwarning("授权确认", "请先勾选「我确认已获得对该目标的测试授权」。")
            return
        try:
            pkt_size = int(self.pkt_size_var.get())
            concurrency = int(self.concurrency_var.get())
            rate = int(self.rate_var.get())
            duration = int(self.duration_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("参数错误", "包大小 / 并发 / 速率 / 时长必须是数字。")
            return
        if not 1 <= pkt_size <= 65535:
            messagebox.showerror("参数错误", "包大小必须在 1–65535 字节。")
            return
        if not 1 <= concurrency <= 500:
            messagebox.showerror("参数错误", "并发线程必须在 1–500。")
            return
        if rate < 0 or rate > 50000:
            messagebox.showerror("参数错误", "速率必须在 0–50000 pkt/s/线程。")
            return
        if duration < 0 or duration > 86400:
            messagebox.showerror("参数错误", "持续时间必须在 0–86400 秒。")
            return
        ports, port_desc = core.parse_ports(self.port_var.get().strip())
        if not ports:
            messagebox.showerror("参数错误", f"端口表达式无效：{port_desc}")
            return
        if diag.is_loopback(ip) and rate == 0:
            if not messagebox.askyesno(
                    "环回地址全速测试",
                    "目标是环回地址且 rate=0（不限速），可能瞬间占满 CPU。\n仍要继续？"):
                return
        elif rate == 0:
            if not messagebox.askyesno("全速发包", "rate=0 会不限速发送，CPU/网卡占用很高。继续？"):
                return

        self.generator = core.TrafficGenerator(
            target_ip=ip, target_port_str=self.port_var.get().strip(),
            protocol=self.protocol_var.get(), concurrency=concurrency,
            packet_size=pkt_size, rate=rate, log_callback=self._log)
        self.generator.start()
        self.start_time = time.perf_counter()
        self.current_duration = duration
        self.progress["value"] = 0
        self.test_status_var.set("Running")
        self.status_var.set(f"运行中 · {self.protocol_var.get()} → {ip}")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._log(f"开始：{concurrency} 线程，{self.protocol_var.get()} → {ip}，"
                  f"端口 {port_desc}，包 {pkt_size}B，速率 {rate}/s/线程，"
                  f"时长 {duration or '手动'}")
        if duration > 0:
            self.auto_stop_id = self.root.after(duration * 1000, self._stop_test)

    def _stop_test(self) -> None:
        if self.auto_stop_id:
            try:
                self.root.after_cancel(self.auto_stop_id)
            except tk.TclError:
                pass
            self.auto_stop_id = None
        if self.generator:
            elapsed = time.perf_counter() - self.start_time
            self._log("正在停止…")
            self.generator.stop()
            stats = self.generator.stats
            with stats.lock:
                total_pkts = stats.total_packets
                total_bytes = stats.total_bytes
            avg_pps = total_pkts / elapsed if elapsed > 0 else 0
            avg_mbps = total_bytes * 8 / elapsed / 1e6 if elapsed > 0 else 0
            self._log(f"已停止：{total_pkts:,} 包，{diag.format_bytes(total_bytes)}，"
                      f"平均 {avg_pps:,.0f} PPS / {avg_mbps:.2f} Mbps")
            if elapsed > 0 and total_pkts > 0:
                record = {
                    "time": diag.now_text(), "target": self.generator.target_ip,
                    "ports": self.generator.port_desc, "protocol": self.generator.protocol,
                    "concurrency": self.generator.concurrency,
                    "packet_size": self.generator.packet_size,
                    "rate": self.generator.rate, "duration": f"{elapsed:.1f}s",
                    "packets": total_pkts, "bytes": total_bytes,
                    "avg_pps": round(avg_pps, 1), "avg_mbps": round(avg_mbps, 2),
                    "note": "manual" if self.current_duration == 0 else f"auto {self.current_duration}s",
                }
                self.records = diag.append_record(HISTORY_FILE, record)
                self._refresh_dashboard()
                self._refresh_history()
            self.generator = None
        self.test_status_var.set("Idle")
        self.status_var.set("就绪 · 仅对已授权目标测试")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.pps_var.set("0")
        self.mbps_var.set("0")
        self.elapsed_var.set("00:00:00")

    def _start_receiver(self) -> None:
        try:
            port = int(self.tcp_srv_port_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("参数错误", "监听端口必须是数字。")
            return
        if not 1 <= port <= 65535:
            messagebox.showerror("参数错误", "监听端口必须在 1–65535。")
            return
        self.tcp_server = core.TCPServer(port, log_callback=self._log)
        self.tcp_server.start()
        if self.tcp_server.running:
            self.tcp_srv_start_btn.config(state=tk.DISABLED)
            self.tcp_srv_stop_btn.config(state=tk.NORMAL)
            self.tcp_srv_status_var.set("Listening")

    def _stop_receiver(self) -> None:
        if self.tcp_server:
            self.tcp_server.stop()
            self.tcp_server = None
        self.tcp_srv_start_btn.config(state=tk.NORMAL)
        self.tcp_srv_stop_btn.config(state=tk.DISABLED)
        self.tcp_srv_status_var.set("Stopped")
        self.tcp_srv_rx_var.set("")

    # ── diagnostics ───────────────────────────────────────────────────
    def _build_diagnostics(self) -> None:
        body = self._page("diagnostics", "目标诊断", "Ping · DNS · TCP 端口 · 网关",
                          "不发送压测流量")
        top = ttk.LabelFrame(body, text="诊断目标 / Target", style="Card.TLabelframe")
        top.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(top, text="目标", style="Card.TLabel").pack(side=tk.LEFT)
        self.diag_target = tk.StringVar(value="192.0.2.10")
        ttk.Entry(top, textvariable=self.diag_target, width=26).pack(side=tk.LEFT, padx=6)
        ttk.Label(top, text="端口", style="Card.TLabel").pack(side=tk.LEFT, padx=(10, 0))
        self.diag_ports = tk.StringVar(value="80,443")
        ttk.Entry(top, textvariable=self.diag_ports, width=18).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Ping", style="Accent.TButton",
                   command=lambda: self._run_diag("ping")).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="DNS 解析", command=lambda: self._run_diag("dns")).pack(
            side=tk.LEFT, padx=3)
        ttk.Button(top, text="TCP 端口", command=lambda: self._run_diag("ports")).pack(
            side=tk.LEFT, padx=3)
        ttk.Button(top, text="探测网关", command=self._diag_gateways).pack(side=tk.LEFT, padx=3)
        ttk.Button(top, text="清空", command=self._clear_diag).pack(side=tk.LEFT, padx=3)

        self.diag_summary = tk.StringVar(value="就绪：先输入目标，再选择诊断项。")
        ttk.Label(body, textvariable=self.diag_summary, style="Muted.TLabel").pack(
            anchor="w", pady=(0, 6))
        table = ttk.Frame(body)
        table.pack(fill=tk.BOTH, expand=True)
        cols = ("check", "target", "result", "detail")
        self.diag_tree = ttk.Treeview(table, columns=cols, show="headings")
        for col, text, width in (("check", "检查", 120), ("target", "目标", 190),
                                 ("result", "结果", 100), ("detail", "详情", 500)):
            self.diag_tree.heading(col, text=text)
            self.diag_tree.column(col, width=width, anchor="w", stretch=(col == "detail"))
        vsb = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.diag_tree.yview)
        self.diag_tree.configure(yscrollcommand=vsb.set)
        self.diag_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.diag_tree.tag_configure("ok", foreground=GREEN)
        self.diag_tree.tag_configure("bad", foreground=RED)
        self.diag_tree.tag_configure("warn", foreground=AMBER)

    def _clear_diag(self) -> None:
        self.diag_tree.delete(*self.diag_tree.get_children())
        self.diag_summary.set("已清空。")

    def _run_diag(self, kind: str) -> None:
        if self._diag_busy:
            messagebox.showinfo("诊断", "上一项诊断还在执行。")
            return
        target = self.diag_target.get().strip()
        if not target:
            messagebox.showerror("诊断", "请输入目标。")
            return
        ports, desc = core.parse_ports(self.diag_ports.get().strip() or "80")
        if kind == "ports" and not ports:
            messagebox.showerror("诊断", f"端口表达式无效：{desc}")
            return
        self._diag_busy = True
        self.diag_summary.set(f"执行中：{kind} → {target}")
        threading.Thread(target=self._diag_worker, args=(kind, target, ports), daemon=True).start()
        self.after(100, self._poll_diag)

    def _diag_worker(self, kind: str, target: str, ports: list[int]) -> None:
        if kind == "ping":
            result = diag.ping_host(target, count=4, timeout=1.2)
            self._diag_queue.put(("ping", target, result.ok, result.summary()))
            self._diag_queue.put(("done", target, True, "Ping 完成"))
        elif kind == "dns":
            addresses = diag.resolve_host(target)
            self._diag_queue.put(("dns", target, bool(addresses),
                                  ", ".join(addresses[:5]) if addresses else "解析失败"))
            self._diag_queue.put(("done", target, True, "DNS 完成"))
        elif kind == "ports":
            results = diag.check_ports(target, ports, timeout=1.0)
            for item in results:
                self._diag_queue.put(("port", f"{target}:{item.port}", item.ok,
                                      f"{item.latency_ms:.1f} ms" if item.ok else item.error))
            self._diag_queue.put(("done", target, True, f"检查 {len(results)} 个端口"))
        else:
            self._diag_queue.put(("done", target, True, "完成"))

    def _poll_diag(self) -> None:
        while True:
            try:
                kind, target, ok, detail = self._diag_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "done":
                self._diag_busy = False
                self.diag_summary.set(f"完成：{detail}")
                return
            label = {"ping": "ICMP Ping", "dns": "DNS 解析", "port": "TCP 端口"}.get(kind, kind)
            self.diag_tree.insert("", 0, values=(label, target, "通过" if ok else "失败", detail),
                                  tags=("ok" if ok else "bad",))
            self.diag_summary.set(f"{label} {target}: {'通过' if ok else '失败'} · {detail}")
        if self._diag_busy:
            self.after(100, self._poll_diag)

    def _diag_gateways(self) -> None:
        gateways = core.detect_gateways()
        self.diag_tree.delete(*self.diag_tree.get_children())
        if not gateways:
            self.diag_tree.insert("", 0, values=("默认网关", "-", "失败", "未发现默认网关"),
                                  tags=("bad",))
            self.diag_summary.set("未发现默认网关")
            return
        for display, ip in gateways:
            self.diag_tree.insert("", 0, values=("默认网关", display, "通过", ip),
                                  tags=("ok",))
        self.diag_summary.set(f"发现 {len(gateways)} 个默认网关")

    # ── history ───────────────────────────────────────────────────────
    def _build_history(self) -> None:
        body = self._page("history", "结果历史", "每次流量测试自动记录 · 可导出 CSV",
                          "记录只保存在本机")
        bar = ttk.Frame(body)
        bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(bar, text="刷新", command=self._refresh_history).pack(side=tk.LEFT)
        ttk.Button(bar, text="导出 CSV", style="Accent.TButton",
                   command=self._export_history).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="打开报告目录",
                   command=lambda: self._open_dir(REPORT_DIR)).pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="清空历史", style="Danger.TButton",
                   command=self._clear_history).pack(side=tk.LEFT, padx=6)
        self.history_summary = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.history_summary, style="Muted.TLabel").pack(
            side=tk.LEFT, padx=10)

        cols = ("time", "target", "protocol", "conc", "rate", "duration", "packets", "pps", "mbps")
        self.history_tree = ttk.Treeview(body, columns=cols, show="headings")
        for col, text, width in (
                ("time", "时间", 140), ("target", "目标", 160), ("protocol", "协议", 80),
                ("conc", "并发", 60), ("rate", "速率", 80), ("duration", "时长", 80),
                ("packets", "包数", 100), ("pps", "平均 PPS", 100), ("mbps", "平均 Mbps", 100)):
            self.history_tree.heading(col, text=text)
            self.history_tree.column(col, width=width, anchor="w", stretch=(col == "target"))
        vsb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_tree"):
            return
        self.records = diag.load_records(HISTORY_FILE)
        self.history_tree.delete(*self.history_tree.get_children())
        for idx, record in enumerate(self.records):
            self.history_tree.insert("", tk.END, iid=str(idx), values=(
                record.get("time", ""), record.get("target", ""), record.get("protocol", ""),
                record.get("concurrency", ""), record.get("rate", ""),
                record.get("duration", ""), f"{int(record.get('packets', 0)):,}",
                f"{float(record.get('avg_pps', 0)):,.0f}",
                f"{float(record.get('avg_mbps', 0)):,.2f}"))
        self.history_summary.set(f"{len(self.records)} 条记录")
        if hasattr(self, "header_records"):
            self.header_records.configure(text=f"记录 {len(self.records)}")

    def _export_history(self) -> None:
        if not self.records:
            messagebox.showinfo("导出", "没有可导出的记录。")
            return
        default = os.path.join(REPORT_DIR, f"traffic_runs_{datetime.now():%Y%m%d_%H%M%S}.csv")
        path = filedialog.asksaveasfilename(
            title="导出结果 CSV", defaultextension=".csv", initialdir=REPORT_DIR,
            initialfile=os.path.basename(default),
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            os.makedirs(REPORT_DIR, exist_ok=True)
            diag.export_records_csv(path, self.records)
        except OSError as exc:
            messagebox.showerror("导出失败", str(exc))
            return
        self.status_var.set(f"已导出 {os.path.basename(path)}")
        messagebox.showinfo("导出完成", path)

    def _clear_history(self) -> None:
        if not self.records:
            return
        if not messagebox.askyesno("清空历史", "删除本机全部流量测试记录？"):
            return
        Path(HISTORY_FILE).write_text("[]\n", encoding="utf-8")
        self.records = []
        self._refresh_history()
        self._refresh_dashboard()

    @staticmethod
    def _open_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)
        try:
            os.startfile(path)
        except OSError as exc:
            messagebox.showerror("打开失败", str(exc))

    # ── monitor / log ────────────────────────────────────────────────
    def _start_monitor(self) -> None:
        self._monitor_tick()
        self.monitor_id = self.root.after(500, self._start_monitor)

    def _monitor_tick(self) -> None:
        if self.generator and self.generator.running:
            elapsed = time.perf_counter() - self.start_time
            self.generator.stats.tick(0.5)
            pps, bps, total_pkts, total_bytes = self.generator.stats.snapshot()
            self.pps_var.set(f"{pps:,.0f}")
            self.mbps_var.set(f"{bps * 8 / 1e6:,.2f}")
            self.total_pkt_var.set(f"{total_pkts:,}")
            self.elapsed_var.set(diag.format_duration(elapsed))
            if self.current_duration > 0:
                self.progress["value"] = min(100, elapsed / self.current_duration * 100)
        if self.tcp_server and self.tcp_server.running:
            with self.tcp_server.stats.lock:
                rx_pkts = self.tcp_server.stats.total_packets
                rx_bytes = self.tcp_server.stats.total_bytes
            self.tcp_srv_rx_var.set(f"Rx {rx_pkts:,} 包 / {diag.format_bytes(rx_bytes)}")

    def _log(self, message: str) -> None:
        if not hasattr(self, "log_area"):
            return
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def _on_close(self) -> None:
        if self.generator:
            self.generator.stop()
        if self.tcp_server:
            self.tcp_server.stop()
        if self.monitor_id:
            try:
                self.root.after_cancel(self.monitor_id)
            except tk.TclError:
                pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    TrafficStudio().run()


if __name__ == "__main__":
    main()
