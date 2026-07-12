#!/usr/bin/env python3
"""Egalitarianism block explorer — network stats, per-algo difficulty/hashrate, rewards."""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("EGA_EXPLORER_HOST", "127.0.0.1")
PORT = int(os.environ.get("EGA_EXPLORER_PORT", "8088"))
RPC_URL = os.environ.get("EGA_RPC_URL", "http://127.0.0.1:20202")
RPC_USER = os.environ.get("EGA_RPC_USER", "")
RPC_PASS = os.environ.get("EGA_RPC_PASS", "")

# EGA consensus (frozen params)
BLOCK_TIME = 60  # overall target seconds
NUM_ALGOS = 3
ALGO_TARGET_SPACING = BLOCK_TIME * NUM_ALGOS  # MultiShield ~180s per algo
HALVING_INTERVAL = 210_000
INITIAL_SUBSIDY = 50_000  # EGA
MAX_SUPPLY = 21_000_000_000
ALGOS = ("randomx", "verthash", "yespower-ega")


def load_rpc_from_conf() -> None:
    global RPC_USER, RPC_PASS, RPC_URL
    if RPC_USER and RPC_PASS:
        return
    conf = Path.home() / ".ega" / "ega.conf"
    if not conf.is_file():
        return
    for line in conf.read_text(errors="replace").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "rpcuser":
            RPC_USER = v
        elif k == "rpcpassword":
            RPC_PASS = v
        elif k == "rpcport":
            RPC_URL = f"http://127.0.0.1:{v}"


def rpc(method: str, params=None):
    if params is None:
        params = []
    payload = json.dumps(
        {"jsonrpc": "1.0", "id": "ega-explorer", "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(RPC_URL, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if RPC_USER or RPC_PASS:
        token = base64.b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"RPC HTTP {e.code}: {body[:400]}") from e
    except Exception as e:
        raise RuntimeError(f"RPC error: {e}") from e
    if data.get("error"):
        err = data["error"]
        if isinstance(err, dict):
            raise RuntimeError(err.get("message") or str(err))
        raise RuntimeError(str(err))
    return data["result"]


def esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_time(ts) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(int(ts)))
    except Exception:
        return str(ts or "—")


def short(h: str, n: int = 10) -> str:
    h = str(h or "")
    if len(h) <= n * 2:
        return h
    return f"{h[:n]}…{h[-n:]}"


def subsidy_at(height: int) -> float:
    """Block subsidy in EGA at height (genesis reward 0)."""
    if height is None or height <= 0:
        return 0.0
    halvings = height // HALVING_INTERVAL
    if halvings >= 64:
        return 0.0
    return float(INITIAL_SUBSIDY) / (2**halvings)


def fmt_hashrate(hps: float) -> str:
    if hps is None or hps <= 0:
        return "0 H/s"
    units = ["H/s", "kH/s", "MH/s", "GH/s", "TH/s", "PH/s"]
    i = 0
    x = float(hps)
    while x >= 1000 and i < len(units) - 1:
        x /= 1000.0
        i += 1
    if x >= 100:
        return f"{x:.1f} {units[i]}"
    if x >= 10:
        return f"{x:.2f} {units[i]}"
    return f"{x:.3f} {units[i]}"


def fmt_diff(d) -> str:
    try:
        d = float(d)
    except Exception:
        return str(d)
    if d <= 0:
        return "0"
    if d < 0.001:
        return f"{d:.6g}"
    if d < 1:
        return f"{d:.5g}"
    if d < 1000:
        return f"{d:.4g}"
    return f"{d:,.2f}"


def fmt_ega(n: float) -> str:
    if n >= 1_000_000:
        return f"{n:,.0f}"
    if abs(n - int(n)) < 1e-9:
        return f"{int(n):,}"
    return f"{n:,.8f}".rstrip("0").rstrip(".")


def hashrate_from_diff(difficulty: float, target_seconds: float = ALGO_TARGET_SPACING) -> float:
    """Bitcoin-family estimate: H/s ≈ difficulty * 2^32 / target_block_time."""
    if difficulty is None or difficulty <= 0 or target_seconds <= 0:
        return 0.0
    return float(difficulty) * (2**32) / float(target_seconds)


def collect_algo_stats(height: int, window: int = 120):
    """Count recent blocks per algo and estimate spacing-based hashrate."""
    counts = {a: 0 for a in ALGOS}
    times = {a: [] for a in ALGOS}
    start = max(1, height - window + 1)  # skip genesis
    for h in range(height, start - 1, -1):
        try:
            bh = rpc("getblockhash", [h])
            b = rpc("getblock", [bh])
        except Exception:
            continue
        algo = (b.get("pow_algo") or b.get("algo") or "").lower()
        if algo in counts:
            counts[algo] += 1
            if b.get("time"):
                times[algo].append(int(b["time"]))
    return counts, times


def network_snapshot():
    info = rpc("getblockchaininfo")
    height = int(info.get("blocks", 0))
    diffs = info.get("difficulties") or {}
    # normalize keys
    diff_map = {}
    for k, v in diffs.items():
        diff_map[k.lower()] = float(v)
    try:
        mining = rpc("getmininginfo")
    except Exception:
        mining = {}
    for a in ALGOS:
        key = f"difficulty_{a}"
        if a not in diff_map and key in mining:
            diff_map[a] = float(mining[key])
    try:
        net_hps = float(rpc("getnetworkhashps", [min(120, max(1, height)), -1]))
    except Exception:
        net_hps = 0.0

    counts, _ = collect_algo_stats(height, window=min(120, max(1, height)))
    total_counted = sum(counts.values()) or 1

    algos = []
    for a in ALGOS:
        d = diff_map.get(a, 0.0)
        hps = hashrate_from_diff(d, ALGO_TARGET_SPACING)
        share = 100.0 * counts.get(a, 0) / total_counted
        algos.append(
            {
                "algo": a,
                "difficulty": d,
                "hashrate": hps,
                "blocks_window": counts.get(a, 0),
                "share_pct": share,
            }
        )

    reward = subsidy_at(height)
    next_halving = ((height // HALVING_INTERVAL) + 1) * HALVING_INTERVAL
    blocks_to_halving = max(0, next_halving - height)

    return {
        "info": info,
        "height": height,
        "chain": info.get("chain"),
        "best": info.get("bestblockhash"),
        "algos": algos,
        "network_hashps_rpc": net_hps,
        "network_hashps_sum": sum(x["hashrate"] for x in algos),
        "reward": reward,
        "next_halving_height": next_halving,
        "blocks_to_halving": blocks_to_halving,
        "max_supply": MAX_SUPPLY,
        "block_time": BLOCK_TIME,
    }


CSS = """
:root{
  --bg:#070b14;--panel:#0f1626;--panel2:#141e32;--line:#1e2a42;
  --text:#e8eef9;--muted:#8b9bb8;--accent:#2dd4bf;--accent2:#14b8a6;
  --gold:#e2b84a;--row:#0c1322;--rowh:#12203a;--rx:#60a5fa;--vh:#a78bfa;--yp:#34d399;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
a{color:var(--accent);text-decoration:none}
a:hover{color:#5eead4}
.shell{max-width:1120px;margin:0 auto;padding:0 1.1rem 2.5rem}
.top{display:flex;align-items:center;justify-content:space-between;gap:1rem;
  padding:1rem 0;border-bottom:1px solid var(--line);position:sticky;top:0;
  background:rgba(7,11,20,.94);backdrop-filter:blur(10px);z-index:5}
.brand{display:flex;align-items:center;gap:.65rem;color:var(--text);font-weight:750;letter-spacing:-.02em}
.logo{width:34px;height:34px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#5eead4,#0f766e 55%,#042f2e);
  box-shadow:0 0 0 2px #1e2a42}
.nav{display:flex;gap:1rem;font-size:.9rem}
.nav a{color:var(--muted)}.nav a:hover{color:var(--text)}
h1{font-size:1.45rem;letter-spacing:-.03em;margin:.25rem 0 .5rem;font-weight:800}
h2{font-size:1.02rem;margin:0;font-weight:700}
.muted{color:var(--muted)}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.84rem;word-break:break-all}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin:1rem 0}
@media(max-width:900px){.stats{grid-template-columns:1fr 1fr}}
.stat{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:14px;padding:.9rem 1rem}
.stat .l{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700}
.stat .v{font-size:1.25rem;font-weight:800;margin-top:.2rem;letter-spacing:-.02em}
.stat .s{color:var(--muted);font-size:.78rem;margin-top:.2rem}
.search{display:flex;gap:.5rem;margin:0 0 1.1rem}
.search input{flex:1;background:var(--panel);border:1px solid var(--line);color:var(--text);
  border-radius:10px;padding:.7rem .9rem;font-size:.95rem}
.search input:focus{outline:1px solid var(--accent);border-color:var(--accent)}
.search button{background:var(--accent);color:#042f2e;border:0;border-radius:10px;
  padding:.7rem 1.1rem;font-weight:750;cursor:pointer}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-bottom:1rem}
.card-h{padding:.85rem 1rem;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:.5rem}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:.7rem .9rem;border-bottom:1px solid var(--line);vertical-align:middle}
th{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;background:rgba(0,0,0,.2);font-weight:700}
tr:hover td{background:var(--rowh)}
tr:last-child td,tr:last-child th{border-bottom:0}
.kv th{width:30%;background:transparent;text-transform:none;letter-spacing:0;font-size:.88rem;color:var(--muted);font-weight:600}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:999px;font-size:.72rem;font-weight:750;
  background:rgba(45,212,191,.12);color:var(--accent)}
.badge-rx{background:rgba(96,165,250,.15);color:var(--rx)}
.badge-vh{background:rgba(167,139,250,.15);color:var(--vh)}
.badge-yp{background:rgba(52,211,153,.15);color:var(--yp)}
.badge-gold{background:rgba(226,184,74,.14);color:var(--gold)}
.err{background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.35);color:#fecaca;
  padding:1rem;border-radius:12px;margin:1rem 0}
.note{background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.22);color:#b7f5eb;
  padding:1rem;border-radius:12px;margin:1rem 0;font-size:.92rem}
.crumbs{color:var(--muted);font-size:.88rem;margin-bottom:.55rem}
.crumbs a{color:var(--muted)}.crumbs a:hover{color:var(--accent)}
.pager{display:flex;gap:.75rem;padding:.85rem 1rem;border-top:1px solid var(--line);font-size:.9rem}
footer{margin-top:1.5rem;color:var(--muted);font-size:.82rem;display:flex;justify-content:space-between;gap:.5rem;flex-wrap:wrap}
ul.tx{list-style:none}
ul.tx li{padding:.55rem .95rem;border-bottom:1px solid var(--line)}
ul.tx li:last-child{border-bottom:0}
.bar{height:8px;background:#0a1220;border-radius:99px;overflow:hidden;min-width:80px}
.bar > i{display:block;height:100%;border-radius:99px}
.right{text-align:right}
"""


def algo_badge(algo: str) -> str:
    a = (algo or "").lower()
    cls = "badge"
    if a == "randomx":
        cls += " badge-rx"
    elif a == "verthash":
        cls += " badge-vh"
    elif "yespower" in a:
        cls += " badge-yp"
    return f'<span class="{cls}">{esc(algo or "—")}</span>'


def layout(title: str, body: str) -> bytes:
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="refresh" content="60"/>
<title>{esc(title)} · EGA Explorer</title>
<style>{CSS}</style>
</head><body>
<div class="shell">
  <header class="top">
    <a class="brand" href="/"><span class="logo"></span> EGA Explorer</a>
    <nav class="nav">
      <a href="/">Overview</a>
      <a href="/#algos">Algorithms</a>
      <a href="/#blocks">Blocks</a>
      <a href="/api/stats">API</a>
    </nav>
  </header>
  {body}
  <footer>
    <span>Egalitarianism explorer · auto-refresh 60s</span>
    <span class="mono">target {BLOCK_TIME}s · MultiShield · 3 algos</span>
  </footer>
</div>
</body></html>"""
    return html.encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_html(self, code: int, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, code: int, obj):
        raw = json.dumps(obj, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        try:
            self._route()
        except Exception as e:
            if self.path.startswith("/api/"):
                self.send_json(500, {"error": str(e)})
            else:
                self.send_html(500, layout("Error", f'<div class="err">{esc(e)}</div>'))

    def _route(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        q = parse_qs(u.query)
        if path == "/api/stats":
            snap = network_snapshot()
            # JSON-serializable
            self.send_json(
                200,
                {
                    "height": snap["height"],
                    "chain": snap["chain"],
                    "bestblockhash": snap["best"],
                    "block_reward_ega": snap["reward"],
                    "next_halving_height": snap["next_halving_height"],
                    "blocks_to_halving": snap["blocks_to_halving"],
                    "max_supply_ega": snap["max_supply"],
                    "target_block_time_sec": snap["block_time"],
                    "network_hashps_rpc": snap["network_hashps_rpc"],
                    "network_hashps_sum_est": snap["network_hashps_sum"],
                    "algorithms": snap["algos"],
                },
            )
            return
        if path == "/":
            self.send_html(200, layout("Network", self._home()))
        elif path.startswith("/block/"):
            self.send_html(200, layout("Block", self._block(path[len("/block/") :])))
        elif path.startswith("/tx/"):
            self.send_html(200, layout("Transaction", self._tx(path[len("/tx/") :])))
        elif path == "/search":
            self.send_html(200, layout("Search", self._search((q.get("q") or [""])[0].strip())))
        else:
            self.send_html(404, layout("Not found", '<div class="err">Page not found.</div>'))

    def _search_form(self, value: str = "") -> str:
        return f"""
<form class="search" action="/search" method="get">
  <input type="text" name="q" value="{esc(value)}" placeholder="Height, block hash, or transaction id" />
  <button type="submit">Search</button>
</form>"""

    def _home(self) -> str:
        snap = network_snapshot()
        height = snap["height"]
        reward = snap["reward"]

        # algo table rows
        colors = {"randomx": "var(--rx)", "verthash": "var(--vh)", "yespower-ega": "var(--yp)"}
        algo_rows = []
        for a in snap["algos"]:
            name = a["algo"]
            col = colors.get(name, "var(--accent)")
            pct = a["share_pct"]
            algo_rows.append(
                f"""<tr>
                <td>{algo_badge(name)}</td>
                <td class="right mono">{esc(fmt_diff(a['difficulty']))}</td>
                <td class="right mono"><strong>{esc(fmt_hashrate(a['hashrate']))}</strong></td>
                <td class="right">{a['blocks_window']}</td>
                <td>
                  <div style="display:flex;align-items:center;gap:.6rem">
                    <div class="bar" style="flex:1"><i style="width:{pct:.1f}%;background:{col}"></i></div>
                    <span class="muted" style="min-width:3.2rem">{pct:.0f}%</span>
                  </div>
                </td>
                </tr>"""
            )

        # recent blocks
        rows = []
        for h in range(height, max(-1, height - 29), -1):
            try:
                bh = rpc("getblockhash", [h])
                b = rpc("getblock", [bh])
            except Exception:
                continue
            algo = b.get("pow_algo") or b.get("algo") or "—"
            rew = subsidy_at(h if h is not None else 0)
            ntx = len(b.get("tx", []))
            rows.append(
                f"""<tr>
                <td><a href="/block/{h}"><strong>{h}</strong></a></td>
                <td class="mono"><a href="/block/{esc(bh)}">{esc(short(bh, 7))}</a></td>
                <td>{algo_badge(algo)}</td>
                <td class="right">{esc(fmt_ega(rew))}</td>
                <td class="right mono">{esc(fmt_diff(b.get('difficulty')))}</td>
                <td class="right">{ntx}</td>
                <td class="muted">{esc(fmt_time(b.get('time')))}</td>
                </tr>"""
            )

        return f"""
<h1>Network overview</h1>
<p class="muted">Live chain data from your node · MultiShield triple PoW</p>

<div class="stats">
  <div class="stat">
    <div class="l">Height</div>
    <div class="v">{esc(height)}</div>
    <div class="s">{esc(snap['chain'])} · headers {esc(snap['info'].get('headers',''))}</div>
  </div>
  <div class="stat">
    <div class="l">Block reward</div>
    <div class="v">{esc(fmt_ega(reward))} <span style="font-size:.7em">EGA</span></div>
    <div class="s">halves every {HALVING_INTERVAL:,} blocks</div>
  </div>
  <div class="stat">
    <div class="l">Next halving</div>
    <div class="v" style="font-size:1.05rem">#{esc(snap['next_halving_height']):,}</div>
    <div class="s">{esc(snap['blocks_to_halving']):,} blocks left</div>
  </div>
  <div class="stat">
    <div class="l">Est. total hashrate</div>
    <div class="v" style="font-size:1.05rem">{esc(fmt_hashrate(snap['network_hashps_sum']))}</div>
    <div class="s">RPC blend {esc(fmt_hashrate(snap['network_hashps_rpc']))}</div>
  </div>
</div>

{self._search_form()}

<div class="card" id="algos">
  <div class="card-h">
    <h2>Algorithms</h2>
    <span class="muted">difficulty · estimated hashrate · last ~120 blocks</span>
  </div>
  <table>
    <tr>
      <th>Algo</th>
      <th class="right">Difficulty</th>
      <th class="right">Network hashrate</th>
      <th class="right">Blocks</th>
      <th>Share</th>
    </tr>
    {''.join(algo_rows)}
  </table>
  <div style="padding:.75rem 1rem;border-top:1px solid var(--line)" class="muted">
    Hashrate estimate: <span class="mono">difficulty × 2³² / {ALGO_TARGET_SPACING}s</span>
    (MultiShield target spacing per algo). Block time target ~{BLOCK_TIME}s overall.
    Max supply {MAX_SUPPLY:,} EGA · subsidy starts at {INITIAL_SUBSIDY:,} EGA.
  </div>
</div>

<div class="card" id="blocks">
  <div class="card-h"><h2>Recent blocks</h2><span class="muted">latest 30</span></div>
  <table>
    <tr>
      <th>Height</th><th>Hash</th><th>Algo</th>
      <th class="right">Reward</th><th class="right">Difficulty</th>
      <th class="right">Txs</th><th>Time</th>
    </tr>
    {''.join(rows) or '<tr><td colspan="7" class="muted">No blocks yet</td></tr>'}
  </table>
</div>
"""

    def _block(self, key: str) -> str:
        if re.fullmatch(r"\d+", key):
            height_key = int(key)
            bh = rpc("getblockhash", [height_key])
        else:
            bh = key
        b = rpc("getblock", [bh])
        height = b.get("height")
        txs = b.get("tx", [])
        algo = b.get("pow_algo") or b.get("algo") or "—"
        rew = subsidy_at(int(height) if height is not None else 0)
        # coinbase total if available
        coinbase_val = None
        if height and height > 0 and txs:
            try:
                tx = rpc("getrawtransaction", [txs[0], True])
                coinbase_val = sum(float(o.get("value") or 0) for o in tx.get("vout", []))
            except Exception:
                pass

        tx_items = []
        for i, t in enumerate(txs):
            if height == 0 and i == 0:
                tx_items.append(
                    f'<li class="mono">{esc(t)} <span class="badge badge-gold">genesis coinbase</span></li>'
                )
            elif i == 0:
                tx_items.append(
                    f'<li class="mono"><a href="/tx/{esc(t)}">{esc(t)}</a> <span class="badge">coinbase</span></li>'
                )
            else:
                tx_items.append(f'<li class="mono"><a href="/tx/{esc(t)}">{esc(t)}</a></li>')

        reward_line = f"{fmt_ega(rew)} EGA"
        if coinbase_val is not None:
            reward_line += f" (coinbase outputs {fmt_ega(coinbase_val)} EGA)"

        fields = [
            ("Hash", b.get("hash")),
            ("Previous", b.get("previousblockhash")),
            ("Next", b.get("nextblockhash")),
            ("Merkle root", b.get("merkleroot")),
            ("PoW hash", b.get("pow_hash")),
            ("Time", fmt_time(b.get("time"))),
            ("Algorithm", algo),
            ("Block reward", reward_line),
            ("Difficulty", fmt_diff(b.get("difficulty"))),
            ("Est. algo hashrate", fmt_hashrate(hashrate_from_diff(float(b.get("difficulty") or 0)))),
            ("Nonce", b.get("nonce")),
            ("Bits", b.get("bits")),
            ("Size", f"{b.get('size', '—')} bytes"),
            ("Weight", b.get("weight")),
            ("Version", b.get("versionHex") or b.get("version")),
            ("Confirmations", b.get("confirmations")),
        ]
        rows = "".join(
            f"<tr><th>{esc(k)}</th><td class='mono'>{esc('' if v is None else v)}</td></tr>"
            for k, v in fields
        )
        prev = b.get("previousblockhash")
        nxt = b.get("nextblockhash")
        pager = []
        if prev is not None:
            pager.append(f'<a href="/block/{esc(prev)}">← Previous</a>')
        if nxt:
            pager.append(f'<a href="/block/{esc(nxt)}">Next →</a>')
        return f"""
<div class="crumbs"><a href="/">Overview</a> / Block {esc(height)}</div>
<h1>Block {esc(height)}</h1>
<p>{algo_badge(algo)} <span class="muted">{esc(fmt_time(b.get('time')))} · reward {esc(fmt_ega(rew))} EGA · {len(txs)} tx</span></p>
{self._search_form()}
<div class="card">
  <div class="card-h"><h2>Details</h2></div>
  <table class="kv">{rows}</table>
  <div class="pager">{' · '.join(pager) if pager else '<span class="muted">—</span>'}</div>
</div>
<div class="card">
  <div class="card-h"><h2>Transactions</h2><span class="muted">{len(txs)}</span></div>
  <ul class="tx">{''.join(tx_items) or '<li class="muted">None</li>'}</ul>
</div>
"""

    def _tx(self, txid: str) -> str:
        try:
            genesis = rpc("getblockhash", [0])
            gblock = rpc("getblock", [genesis])
            if gblock.get("tx") and gblock["tx"][0] == txid:
                return f"""
<div class="crumbs"><a href="/">Overview</a> / <a href="/block/0">Genesis</a> / Tx</div>
<h1>Genesis coinbase</h1>
<div class="note">
  Genesis coinbase is not a normal spendable transaction (Bitcoin-family rule). Reward at height 0 is <strong>0 EGA</strong>.
</div>
<div class="card"><table class="kv">
<tr><th>Txid</th><td class="mono">{esc(txid)}</td></tr>
<tr><th>Block</th><td><a href="/block/0">Genesis · height 0</a></td></tr>
<tr><th>Block hash</th><td class="mono">{esc(genesis)}</td></tr>
<tr><th>Reward</th><td>0 EGA</td></tr>
</table></div>
"""
        except Exception:
            pass

        try:
            tx = rpc("getrawtransaction", [txid, True])
        except Exception as e:
            msg = str(e)
            hint = ""
            if "genesis" in msg.lower() or "coinbase is not considered" in msg.lower():
                hint = "<div class='note'>Genesis coinbase cannot be loaded as a normal transaction.</div>"
            elif "No such" in msg or "-5" in msg:
                hint = "<div class='note'>Enable <code>txindex=1</code> in <code>~/.ega/ega.conf</code> and restart (reindex if needed).</div>"
            return f'<div class="err">Could not load transaction: {esc(msg)}</div>{hint}'

        vins = tx.get("vin", [])
        vouts = tx.get("vout", [])
        total_out = sum(float(o.get("value") or 0) for o in vouts)
        vin_html = []
        for v in vins:
            if "coinbase" in v:
                vin_html.append(
                    f"<li class='mono'>coinbase <span class='badge'>block reward / fees</span></li>"
                )
            else:
                vin_html.append(
                    f"<li class='mono'><a href='/tx/{esc(v.get('txid',''))}'>{esc(short(v.get('txid','')))}</a>:{v.get('vout','')}</li>"
                )
        vout_html = []
        for o in vouts:
            spk = o.get("scriptPubKey") or {}
            addrs = spk.get("addresses") or ([spk["address"]] if spk.get("address") else [])
            dest = ", ".join(addrs) if addrs else spk.get("type", "—")
            vout_html.append(
                f"<li><strong>{esc(o.get('value',''))}</strong> EGA → <span class='mono'>{esc(dest)}</span></li>"
            )
        return f"""
<div class="crumbs"><a href="/">Overview</a> / Transaction</div>
<h1>Transaction</h1>
{self._search_form(txid)}
<div class="card"><table class="kv">
<tr><th>Txid</th><td class="mono">{esc(tx.get("txid", txid))}</td></tr>
<tr><th>Block</th><td class="mono"><a href="/block/{esc(tx.get('blockhash',''))}">{esc(tx.get('blockhash',''))}</a></td></tr>
<tr><th>Confirmations</th><td>{esc(tx.get('confirmations',''))}</td></tr>
<tr><th>Time</th><td>{esc(fmt_time(tx.get('time') or tx.get('blocktime')))}</td></tr>
<tr><th>Size</th><td>{esc(tx.get('size',''))} bytes</td></tr>
<tr><th>Total output</th><td><strong>{esc(fmt_ega(total_out))}</strong> EGA</td></tr>
</table></div>
<div class="card">
  <div class="card-h"><h2>Inputs</h2></div>
  <ul class="tx">{''.join(vin_html) or '<li class="muted">—</li>'}</ul>
</div>
<div class="card">
  <div class="card-h"><h2>Outputs</h2></div>
  <ul class="tx">{''.join(vout_html) or '<li class="muted">—</li>'}</ul>
</div>
"""

    def _search(self, term: str) -> str:
        if not term:
            return f"<h1>Search</h1>{self._search_form()}<p class='muted'>Enter a height, block hash, or txid.</p>"
        if re.fullmatch(r"\d+", term):
            return self._block(term)
        if re.fullmatch(r"[0-9a-fA-F]{64}", term):
            try:
                rpc("getblock", [term])
                return self._block(term)
            except Exception:
                return self._tx(term)
        return f"{self._search_form(term)}<div class='err'>Unrecognized query. Use height, 64-char block hash, or txid.</div>"


def main():
    load_rpc_from_conf()
    if not RPC_USER or not RPC_PASS:
        print("Set RPC in ~/.ega/ega.conf or EGA_RPC_USER / EGA_RPC_PASS", file=sys.stderr)
        sys.exit(1)
    try:
        info = rpc("getblockchaininfo")
    except Exception as e:
        print(f"Cannot reach egad at {RPC_URL}: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Connected chain={info.get('chain')} height={info.get('blocks')}")
    print(f"Explorer http://{HOST}:{PORT}/")
    print(f"Stats API http://{HOST}:{PORT}/api/stats")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
