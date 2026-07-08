import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import time
import random
import subprocess
from dataclasses import dataclass, field
from typing import List, Tuple

def detect_gateways() -> List[Tuple[str, str]]:
    cmd = (
        "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | "
        "ForEach-Object { '{0}|{1}' -f $_.NextHop, $_.InterfaceAlias }"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except FileNotFoundError:
        return []
    except subprocess.TimeoutExpired:
        return []

    results: List[Tuple[str, str]] = []
    seen = set()
    for line in proc.stdout.strip().splitlines():
        line = line.strip()
        if not line or '|' not in line:
            continue
        parts = line.split('|', 1)
        if len(parts) != 2:
            continue
        gw_ip, iface = parts[0].strip(), parts[1].strip()
        key = gw_ip
        if key in seen:
            continue
        seen.add(key)
        display = f"{gw_ip}  ({iface})"
        results.append((display, gw_ip))
    return results


def parse_ports(port_str: str) -> Tuple[List[int], str]:
    """Parse port string into list of ports.
    Formats:
      '8080'             -> [8080], desc='single port 8080'
      '80,443,8080'      -> [80, 443, 8080], desc='3 ports'
      '100-1000'         -> [100..1000], desc='range 100-1000 (901 ports)'
      '100-1000:50'      -> 50 random ports from 100-1000, desc='50 ports from 100-1000'
    Returns (list_of_ports, description_string).
    """
    raw = port_str.strip()
    if not raw:
        return [], "empty"

    if ':' in raw and '-' in raw:
        range_part, count_part = raw.rsplit(':', 1)
        parts = range_part.split('-', 1)
        try:
            lo, hi = int(parts[0]), int(parts[1])
            cnt = int(count_part)
        except ValueError:
            return [], f"invalid: {raw}"
        if lo < 1 or hi > 65535 or lo > hi:
            return [], f"invalid range: {raw}"
        cnt = min(cnt, hi - lo + 1)
        ports = sorted(random.sample(range(lo, hi + 1), cnt))
        return ports, f"{cnt} ports from {lo}-{hi}"

    if '-' in raw:
        parts = raw.split('-', 1)
        try:
            lo, hi = int(parts[0]), int(parts[1])
        except ValueError:
            return [], f"invalid: {raw}"
        if lo < 1 or hi > 65535 or lo > hi:
            return [], f"invalid range: {raw}"
        ports = list(range(lo, hi + 1))
        return ports, f"range {lo}-{hi} ({len(ports)} ports)"

    if ',' in raw:
        ports = []
        for part in raw.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                p = int(part)
            except ValueError:
                return [], f"invalid port: {part}"
            if p < 1 or p > 65535:
                return [], f"invalid port: {p}"
            ports.append(p)
        return sorted(set(ports)), f"{len(ports)} port(s)"

    try:
        p = int(raw)
        if p < 1 or p > 65535:
            return [], f"invalid port: {p}"
        return [p], f"single port {p}"
    except ValueError:
        return [], f"invalid: {raw}"


@dataclass
class Stats:
    total_packets: int = 0
    total_bytes: int = 0
    prev_packets: int = 0
    prev_bytes: int = 0
    current_pps: float = 0.0
    current_bps: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add(self, packet_size: int, count: int = 1):
        with self.lock:
            self.total_packets += count
            self.total_bytes += count * packet_size

    def snapshot(self) -> tuple:
        with self.lock:
            now_packets = self.total_packets
            now_bytes = self.total_bytes
            pps = self.current_pps
            bps = self.current_bps
        return pps, bps, now_packets, now_bytes

    def tick(self, interval: float):
        with self.lock:
            dp = self.total_packets - self.prev_packets
            db = self.total_bytes - self.prev_bytes
            self.current_pps = dp / interval if interval > 0 else 0.0
            self.current_bps = db / interval if interval > 0 else 0.0
            self.prev_packets = self.total_packets
            self.prev_bytes = self.total_bytes


class TCPServer:
    def __init__(self, port: int, log_callback=None):
        self.port = port
        self.log = log_callback or (lambda msg: None)
        self.stats = Stats()
        self.running = False
        self.server_sock: socket.socket | None = None
        self.server_thread: threading.Thread | None = None
        self.client_threads: List[threading.Thread] = []

    def start(self):
        if self.running:
            return
        self.running = True
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.settimeout(0.5)
        try:
            self.server_sock.bind(("0.0.0.0", self.port))
            self.server_sock.listen(100)
        except OSError as e:
            self.log(f"TCP server bind failed: {e}")
            self.running = False
            return

        self.server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.server_thread.start()
        self.log(f"TCP server listening on 0.0.0.0:{self.port}")

    def stop(self):
        self.running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None
        for t in list(self.client_threads):
            t.join(timeout=1)
        self.client_threads.clear()
        self.log(f"TCP server stopped. Rx: {self.stats.total_packets:,} pkts, "
                 f"{self._fmt(self.stats.total_bytes)}")

    def _accept_loop(self):
        while self.running:
            try:
                client, addr = self.server_sock.accept()
            except (socket.timeout, OSError):
                if not self.running:
                    break
                continue
            t = threading.Thread(target=self._recv_worker, args=(client, addr), daemon=True)
            t.start()
            self.client_threads.append(t)
            self.client_threads = [t for t in self.client_threads if t.is_alive()]

    def _recv_worker(self, sock: socket.socket, addr):
        sock.settimeout(1)
        try:
            while self.running:
                try:
                    data = sock.recv(65536)
                except socket.timeout:
                    continue
                except OSError:
                    break
                if not data:
                    break
                self.stats.add(len(data))
        finally:
            try:
                sock.close()
            except Exception:
                pass

    @staticmethod
    def _fmt(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        elif b < 1024 ** 2:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 ** 3:
            return f"{b / 1024 ** 2:.1f} MB"
        else:
            return f"{b / 1024 ** 3:.2f} GB"


class TrafficGenerator:
    def __init__(self, target_ip: str, target_port_str: str, protocol: str,
                 concurrency: int, packet_size: int, rate: int,
                 log_callback=None):
        self.target_ip = target_ip
        self.target_port_str = target_port_str
        self.target_ports, self.port_desc = parse_ports(target_port_str)
        self.protocol = protocol.upper()
        self.concurrency = concurrency
        self.packet_size = packet_size
        self.rate = rate
        self.log = log_callback or (lambda msg: None)
        self.stats = Stats()
        self.running = False
        self.threads: List[threading.Thread] = []
        self.payload = self._generate_payload()
        self._tcp_connect_error_logged = 0

    def _pick_port(self) -> int:
        return random.choice(self.target_ports)

    def _generate_payload(self) -> bytes:
        return bytes(random.getrandbits(8) for _ in range(self.packet_size))

    def _udp_worker(self, thread_id: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536 * 8)

        interval = 1.0 / self.rate if self.rate > 0 else 0.0
        last_time = time.perf_counter()
        accumulated = 0.0

        while self.running:
            target = (self.target_ip, self._pick_port())
            now = time.perf_counter()
            elapsed = now - last_time
            last_time = now
            accumulated += elapsed

            if self.rate > 0:
                to_send = int(accumulated * self.rate)
                if to_send > 1000:
                    to_send = 1000
                if to_send > 0:
                    accumulated -= to_send / self.rate
            else:
                to_send = 1000
                accumulated = 0.0

            for _ in range(to_send):
                try:
                    sock.sendto(self.payload, target)
                    self.stats.add(self.packet_size)
                except Exception:
                    pass

            if self.rate > 0:
                sleep_time = interval - (time.perf_counter() - last_time)
                if sleep_time > 0:
                    time.sleep(min(sleep_time, 0.1))
            else:
                time.sleep(0.001)

        sock.close()

    def _tcp_worker(self, thread_id: int):
        while self.running:
            sock = None
            port = self._pick_port()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536 * 8)
                sock.settimeout(5)
                sock.connect((self.target_ip, port))

                interval = 1.0 / self.rate if self.rate > 0 else 0.0
                last_time = time.perf_counter()
                accumulated = 0.0

                while self.running:
                    now = time.perf_counter()
                    elapsed = now - last_time
                    last_time = now
                    accumulated += elapsed

                    if self.rate > 0:
                        to_send = int(accumulated * self.rate)
                        if to_send > 1000:
                            to_send = 1000
                        if to_send > 0:
                            accumulated -= to_send / self.rate
                    else:
                        to_send = 1000
                        accumulated = 0.0

                    for _ in range(to_send):
                        try:
                            sock.sendall(self.payload)
                            self.stats.add(self.packet_size)
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            raise

                    if self.rate > 0:
                        sleep_time = interval - (time.perf_counter() - last_time)
                        if sleep_time > 0:
                            time.sleep(min(sleep_time, 0.1))
                    else:
                        time.sleep(0.001)

            except (ConnectionRefusedError, ConnectionAbortedError):
                if self._tcp_connect_error_logged < 3:
                    self.log(f"TCP connect to {self.target_ip}:{port} refused "
                             f"(thread #{thread_id}) - is a TCP server listening?")
                    self._tcp_connect_error_logged += 1
            except socket.timeout:
                if self._tcp_connect_error_logged < 3:
                    self.log(f"TCP connect to {self.target_ip}:{port} timed out "
                             f"(thread #{thread_id})")
                    self._tcp_connect_error_logged += 1
            except (BrokenPipeError, ConnectionResetError):
                pass
            except OSError as e:
                if self._tcp_connect_error_logged < 1:
                    self.log(f"TCP connect error: {e} (thread #{thread_id})")
                    self._tcp_connect_error_logged += 1
            except Exception:
                pass
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass
                if self.running:
                    time.sleep(0.5)

    def _tcp_syn_worker(self, thread_id: int):
        interval = 1.0 / self.rate if self.rate > 0 else 0.0
        last_time = time.perf_counter()
        accumulated = 0.0

        while self.running:
            port = self._pick_port()
            now = time.perf_counter()
            elapsed = now - last_time
            last_time = now
            accumulated += elapsed

            if self.rate > 0:
                to_send = int(accumulated * self.rate)
                if to_send > 500:
                    to_send = 500
                if to_send > 0:
                    accumulated -= to_send / self.rate
            else:
                to_send = 500
                accumulated = 0.0

            if to_send <= 0:
                time.sleep(0.001)
                continue

            socks = []
            for _ in range(to_send):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setblocking(False)
                    s.connect((self.target_ip, port))
                except BlockingIOError:
                    pass
                except Exception:
                    try:
                        s.close()
                    except Exception:
                        pass
                    continue
                socks.append(s)

            sent = len(socks)
            if sent > 0:
                self.stats.add(1, count=sent)

            for s in socks:
                try:
                    s.close()
                except Exception:
                    pass

            if self.rate > 0:
                sleep_time = interval - (time.perf_counter() - last_time)
                if sleep_time > 0:
                    time.sleep(min(sleep_time, 0.1))
            else:
                time.sleep(0.001)

    def start(self):
        if self.running:
            return
        self.running = True
        self.threads.clear()
        if self.protocol == 'UDP':
            worker = self._udp_worker
        elif self.protocol == 'TCP SYN':
            worker = self._tcp_syn_worker
        else:
            worker = self._tcp_worker
        for i in range(self.concurrency):
            t = threading.Thread(target=worker, args=(i,), daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        self.running = False
        for t in self.threads:
            t.join(timeout=2)


class TrafficGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Traffic Load Tester - Gateway Stress Tool")
        self.root.geometry("700x750")
        self.root.resizable(True, True)

        self.generator: TrafficGenerator | None = None
        self.tcp_server: TCPServer | None = None
        self.monitor_id: str | None = None
        self.start_time: float = 0.0

        self._build_ui()
        self._start_monitor()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Target Config ---
        target_frame = ttk.LabelFrame(main_frame, text="Target Configuration", padding=10)
        target_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(target_frame, text="Target IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ip_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(target_frame, textvariable=self.ip_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(target_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(15, 5))
        self.port_var = tk.StringVar(value="8080")
        ttk.Entry(target_frame, textvariable=self.port_var, width=14).grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Label(target_frame, text="e.g. 8080, 80,443, 100-1000, 100-1000:50",
                  foreground="gray", font=("", 7)).grid(
            row=1, column=2, columnspan=2, sticky=tk.W, padx=(20, 0), pady=(0, 2))

        ttk.Label(target_frame, text="Protocol:").grid(row=0, column=4, sticky=tk.W, padx=(15, 5))
        self.protocol_var = tk.StringVar(value="UDP")
        proto_combo = ttk.Combobox(target_frame, textvariable=self.protocol_var,
                                   values=["UDP", "TCP", "TCP SYN"], state="readonly", width=8)
        proto_combo.grid(row=0, column=5, sticky=tk.W, padx=5)

        ttk.Label(target_frame, text="Detected Gateways:").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(8, 0))
        self.gateway_var = tk.StringVar(value="")
        self.gateway_combo = ttk.Combobox(
            target_frame, textvariable=self.gateway_var,
            values=[], state="readonly", width=32)
        self.gateway_combo.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=(8, 0))
        self.gateway_combo.bind("<<ComboboxSelected>>", self._on_gateway_selected)

        detect_btn = ttk.Button(target_frame, text="Detect", command=self._on_detect_gateways)
        detect_btn.grid(row=2, column=3, sticky=tk.W, padx=5, pady=(8, 0))

        # --- TCP Server ---
        tcp_srv_frame = ttk.LabelFrame(main_frame, text="Built-in TCP Receiver (for TCP testing)", padding=10)
        tcp_srv_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(tcp_srv_frame, text="Listen Port:").pack(side=tk.LEFT)
        self.tcp_srv_port_var = tk.IntVar(value=8080)
        ttk.Entry(tcp_srv_frame, textvariable=self.tcp_srv_port_var, width=8).pack(side=tk.LEFT, padx=5)

        self.tcp_srv_start_btn = ttk.Button(tcp_srv_frame, text="Start Server",
                                            command=self._on_start_tcp_server)
        self.tcp_srv_start_btn.pack(side=tk.LEFT, padx=5)

        self.tcp_srv_stop_btn = ttk.Button(tcp_srv_frame, text="Stop Server",
                                           command=self._on_stop_tcp_server, state=tk.DISABLED)
        self.tcp_srv_stop_btn.pack(side=tk.LEFT, padx=5)

        self.tcp_srv_status_var = tk.StringVar(value="Stopped")
        ttk.Label(tcp_srv_frame, textvariable=self.tcp_srv_status_var,
                  foreground="gray").pack(side=tk.LEFT, padx=10)

        self.tcp_srv_rx_var = tk.StringVar(value="")
        ttk.Label(tcp_srv_frame, textvariable=self.tcp_srv_rx_var,
                  foreground="darkgreen").pack(side=tk.RIGHT, padx=5)

        # --- Traffic Params ---
        param_frame = ttk.LabelFrame(main_frame, text="Traffic Parameters", padding=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(param_frame, text="Concurrency (threads):").grid(row=0, column=0, sticky=tk.W)
        self.concurrency_var = tk.IntVar(value=10)
        conc_scale = ttk.Scale(param_frame, from_=1, to=500, variable=self.concurrency_var,
                               orient=tk.HORIZONTAL, length=200, command=self._on_concurrency_scale)
        conc_scale.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.conc_label = ttk.Label(param_frame, text="10", width=4)
        self.conc_label.grid(row=0, column=2, sticky=tk.W)
        self.concurrency_var.trace_add("write", lambda *_: self._update_conc_label())

        ttk.Label(param_frame, text="Packet Size (bytes):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.pkt_size_var = tk.IntVar(value=1024)
        size_frame = ttk.Frame(param_frame)
        size_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(10, 0), padx=5)
        ttk.Radiobutton(size_frame, text="64", variable=self.pkt_size_var, value=64).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(size_frame, text="256", variable=self.pkt_size_var, value=256).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(size_frame, text="512", variable=self.pkt_size_var, value=512).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(size_frame, text="1024", variable=self.pkt_size_var, value=1024).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(size_frame, text="1460", variable=self.pkt_size_var, value=1460).pack(side=tk.LEFT, padx=2)
        custom_entry = ttk.Entry(param_frame, textvariable=self.pkt_size_var, width=8)
        custom_entry.grid(row=1, column=3, sticky=tk.W, pady=(10, 0), padx=5)

        ttk.Label(param_frame, text="Rate (pkt/s/thread):").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.rate_var = tk.IntVar(value=1000)
        rate_scale = ttk.Scale(param_frame, from_=0, to=50000, variable=self.rate_var,
                               orient=tk.HORIZONTAL, length=200, command=self._on_rate_scale)
        rate_scale.grid(row=2, column=1, sticky=tk.W, pady=(10, 0), padx=5)
        self.rate_label = ttk.Label(param_frame, text="1000", width=8)
        self.rate_label.grid(row=2, column=2, sticky=tk.W, pady=(10, 0))
        self.rate_var.trace_add("write", lambda *_: self._update_rate_label())
        ttk.Label(param_frame, text="(0 = unlimited burst)").grid(row=2, column=3, sticky=tk.W, pady=(10, 0), padx=5)

        # --- Control Buttons ---
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(ctrl_frame, text="Start", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(ctrl_frame, text="Stop", command=self._on_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(ctrl_frame, textvariable=self.status_var, foreground="gray").pack(side=tk.LEFT, padx=20)

        # --- Stats Display ---
        stats_frame = ttk.LabelFrame(main_frame, text="Real-time Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        row0 = ttk.Frame(stats_frame)
        row0.pack(fill=tk.X)
        ttk.Label(row0, text="PPS (packets/sec):", font=("Consolas", 11, "bold")).pack(side=tk.LEFT)
        self.pps_var = tk.StringVar(value="0")
        ttk.Label(row0, textvariable=self.pps_var, font=("Consolas", 14, "bold"),
                  foreground="blue", width=20, anchor=tk.E).pack(side=tk.RIGHT)

        row0b = ttk.Frame(stats_frame)
        row0b.pack(fill=tk.X, pady=(2, 5))
        ttk.Label(row0b, text="Bandwidth (Mbps):", font=("Consolas", 11, "bold")).pack(side=tk.LEFT)
        self.bps_var = tk.StringVar(value="0")
        ttk.Label(row0b, textvariable=self.bps_var, font=("Consolas", 14, "bold"),
                  foreground="green", width=20, anchor=tk.E).pack(side=tk.RIGHT)

        row1 = ttk.Frame(stats_frame)
        row1.pack(fill=tk.X)
        ttk.Label(row1, text="Total Packets:").pack(side=tk.LEFT)
        self.total_pkt_var = tk.StringVar(value="0")
        ttk.Label(row1, textvariable=self.total_pkt_var, width=20, anchor=tk.E).pack(side=tk.RIGHT)

        row2 = ttk.Frame(stats_frame)
        row2.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(row2, text="Total Bytes:").pack(side=tk.LEFT)
        self.total_bytes_var = tk.StringVar(value="0")
        ttk.Label(row2, textvariable=self.total_bytes_var, width=20, anchor=tk.E).pack(side=tk.RIGHT)

        row3 = ttk.Frame(stats_frame)
        row3.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(row3, text="Elapsed:").pack(side=tk.LEFT)
        self.elapsed_var = tk.StringVar(value="00:00:00")
        ttk.Label(row3, textvariable=self.elapsed_var, width=20, anchor=tk.E).pack(side=tk.RIGHT)

        # --- Log ---
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, width=80,
                                                   font=("Consolas", 9), state=tk.DISABLED)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def _update_conc_label(self):
        self.conc_label.config(text=str(self.concurrency_var.get()))

    def _on_concurrency_scale(self, val):
        self.concurrency_var.set(int(float(val)))
        self._update_conc_label()

    def _update_rate_label(self):
        self.rate_label.config(text=str(self.rate_var.get()))

    def _on_rate_scale(self, val):
        self.rate_var.set(int(float(val)))
        self._update_rate_label()

    def _on_detect_gateways(self):
        gateways = detect_gateways()
        if not gateways:
            messagebox.showwarning("Detect Gateways",
                                   "No default gateways found.\n\n"
                                   "Possible causes:\n"
                                   "- No active network interfaces\n"
                                   "- PowerShell unavailable")
            self._log("Gateway detection: none found")
            return
        display_names = [g[0] for g in gateways]
        self._gateway_map = {g[0]: g[1] for g in gateways}
        self.gateway_combo["values"] = display_names
        if display_names:
            self.gateway_combo.current(0)
            self._on_gateway_selected()
        self._log(f"Gateway detection: found {len(gateways)} gateway(s)")
        for display, ip in gateways:
            self._log(f"  {display}")

    def _on_gateway_selected(self, event=None):
        selected = self.gateway_var.get()
        if hasattr(self, '_gateway_map') and selected in self._gateway_map:
            self.ip_var.set(self._gateway_map[selected])

    def _on_start(self):
        ip = self.ip_var.get().strip()
        port_str = self.port_var.get().strip()
        if not ip:
            messagebox.showerror("Error", "Target IP cannot be empty")
            return

        ports, port_desc = parse_ports(port_str)
        if not ports:
            messagebox.showerror("Error", f"Invalid port spec: {port_desc}")
            return

        self.generator = TrafficGenerator(
            target_ip=ip,
            target_port_str=port_str,
            protocol=self.protocol_var.get(),
            concurrency=self.concurrency_var.get(),
            packet_size=self.pkt_size_var.get(),
            rate=self.rate_var.get(),
            log_callback=self._log
        )

        self.generator.start()
        self.start_time = time.perf_counter()
        self.status_var.set("Running...")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._log(f"Started: {self.generator.concurrency} threads, "
                  f"{self.generator.protocol} -> {ip}, "
                  f"ports={port_desc}, "
                  f"pkt_size={self.generator.packet_size}B, "
                  f"rate={self.generator.rate} pkt/s/thread")

    def _on_stop(self):
        if self.generator:
            self._log("Stopping...")
            self.generator.stop()
            elapsed = time.perf_counter() - self.start_time
            stats = self.generator.stats
            with stats.lock:
                total_pkts = stats.total_packets
                total_bytes = stats.total_bytes
            avg_pps = total_pkts / elapsed if elapsed > 0 else 0
            avg_mbps = (total_bytes * 8) / elapsed / 1e6 if elapsed > 0 else 0
            self._log(f"Stopped. Total: {total_pkts:,} packets, {self._fmt_bytes(total_bytes)}. "
                      f"Avg PPS: {avg_pps:,.0f}, Avg Mbps: {avg_mbps:.2f}")
            self.generator = None
        self.status_var.set("Idle")
        self.pps_var.set("0")
        self.bps_var.set("0")
        self.total_pkt_var.set("0")
        self.total_bytes_var.set("0")
        self.elapsed_var.set("00:00:00")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def _on_start_tcp_server(self):
        port = self.tcp_srv_port_var.get()
        self.tcp_server = TCPServer(port, log_callback=self._log)
        self.tcp_server.start()
        if self.tcp_server.running:
            self.tcp_srv_start_btn.config(state=tk.DISABLED)
            self.tcp_srv_stop_btn.config(state=tk.NORMAL)
            self.tcp_srv_status_var.set("Listening")

    def _on_stop_tcp_server(self):
        if self.tcp_server:
            self.tcp_server.stop()
            self.tcp_server = None
        self.tcp_srv_start_btn.config(state=tk.NORMAL)
        self.tcp_srv_stop_btn.config(state=tk.DISABLED)
        self.tcp_srv_status_var.set("Stopped")
        self.tcp_srv_rx_var.set("")

    def _start_monitor(self):
        self._monitor_tick()
        self.monitor_id = self.root.after(500, self._start_monitor)

    def _monitor_tick(self):
        if self.generator and self.generator.running:
            elapsed = time.perf_counter() - self.start_time
            self.generator.stats.tick(0.5)
            pps, bps, total_pkts, total_bytes = self.generator.stats.snapshot()

            self.pps_var.set(f"{pps:,.0f}")
            self.bps_var.set(f"{(bps * 8) / 1e6:,.2f}")
            self.total_pkt_var.set(f"{total_pkts:,}")
            self.total_bytes_var.set(self._fmt_bytes(total_bytes))

            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            self.elapsed_var.set(f"{h:02d}:{m:02d}:{s:02d}")

        if self.tcp_server and self.tcp_server.running:
            s = self.tcp_server.stats
            with s.lock:
                rx_pkts = s.total_packets
                rx_bytes = s.total_bytes
            self.tcp_srv_rx_var.set(f"Rx: {rx_pkts:,} pkts, {TCPServer._fmt(rx_bytes)}")

    def _log(self, msg: str):
        self.log_area.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    @staticmethod
    def _fmt_bytes(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        elif b < 1024 ** 2:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 ** 3:
            return f"{b / 1024 ** 2:.1f} MB"
        else:
            return f"{b / 1024 ** 3:.2f} GB"

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TrafficGUI()
    app.run()
