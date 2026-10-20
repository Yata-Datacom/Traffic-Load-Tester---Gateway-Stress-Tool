# Traffic Studio 2.0 — User Guide

> Applies to **v2.0.0**. Examples use documentation addresses (`192.0.2.10`,
> `198.51.100.20`). Never replace them with unauthorized production targets.

## 1. Safety

Traffic Studio is a **stress-testing tool**, not a general scanner.

- Test only systems you own or are explicitly authorized to test.
- Confirm the maintenance window and link capacity before high concurrency.
- Do not stress public, customer or third-party networks without authorization.
- The default target is a documentation address and will not reach a real device.
- You must tick the authorization checkbox before starting a test.

## 2. Launch

```bash
python traffic_studio.py
```

Or double-click `traffic_studio.pyw`. A single-file exe is available in Releases.
The legacy V1 UI remains available with `python traffic_test_gui.py`.

## 3. Overview

The dashboard shows the last PPS/Mbps, number of history records and scenarios,
recent runs, and the recommended workflow.

## 4. Load test

### Target and ports

- **Target**: IP address or resolvable hostname.
- **Port expression**:
  - `8080` — single port
  - `80,443` — comma list, deduplicated and sorted
  - `100-1000` — contiguous range
  - `100-1000:50` — 50 unique random ports from the range
- **Gateway detection** fills the target from the local default route.

### Protocol

| Protocol | Target listener required | Notes |
|---|---|---|
| UDP | No | Sends datagrams directly |
| TCP | Yes | Full connection, then payload |
| TCP SYN | No | Non-blocking half-open connects |

Use the built-in TCP receiver for a local loopback check: start it, then target
`127.0.0.1` on the same port.

### Load parameters

- Concurrency: 1–500 threads
- Packet size: 1–65535 bytes (presets 64/256/512/1024/1460)
- Rate: 0–50000 packets/s/thread; 0 means unlimited
- Duration: 0 = manual stop; otherwise auto-stop after N seconds

Unlimited rate and loopback full-speed tests require confirmation.

### Metrics

Live PPS, Mbps, total packets, elapsed time, progress (when duration is set),
and a log with start parameters, stop summary, TCP errors and receiver status.

## 5. Diagnostics

Diagnostics send no load traffic.

### Ping

Four ICMP probes; reports loss, min/avg/max RTT and jitter. Parses Chinese and
English Windows output.

### DNS

Resolves the target and lists A/AAAA addresses.

### TCP ports

Connects to up to 50 ports from the port expression and reports latency or error.

### Default gateway

Lists next-hop IP and interface alias from the local default route.

## 6. Scenarios

| Scenario | Protocol | Ports | Packet | Rate | Concurrency |
|---|---|---|---|---|---|
| Web gateway | TCP | 80,443 | 512 | 1000 | 20 |
| DNS 53 | UDP | 53 | 256 | 2000 | 10 |
| Video UDP | UDP | 5000 | 1200 | 2000 | 30 |
| TCP SYN | TCP SYN | 80,443 | 64 | 2000 | 50 |

Load a scenario, adjust parameters, and **Save current** to add a custom one.
Custom scenarios are stored locally in `scenarios.json` (git-ignored).

## 7. History

Every completed run is appended to `runs.json` with target, ports, protocol,
concurrency, packet size, rate, duration, total packets/bytes and average
PPS/Mbps. The History page can refresh, export CSV to `reports/`, open the report
folder, or clear local history.

## 8. Data and privacy

These stay local and are git-ignored:

- `runs.json`
- `scenarios.json`
- `reports/`
- `build/`, `dist/`, `*.exe`

Never commit real targets, results, captures or customer topologies.

## 9. Troubleshooting

**TCP connect refused** — no listener on that port. Confirm with TCP diagnostics,
or start the built-in receiver for a local test.

**Ping fails but TCP works** — ICMP may be filtered; trust the TCP result.

**PPS lower than expected** — check concurrency, rate, NIC/CPU and target capacity.

**No history record** — only runs that actually send packets and stop normally are
recorded.

**History/scenarios missing on another machine** — they are local files; copy
`runs.json` and `scenarios.json`.
