#!/usr/bin/env python3
"""EGA pool dashboard — human UI over Miningcore JSON API (not raw API dump)."""
from __future__ import annotations

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("EGA_POOL_UI_HOST", "0.0.0.0")
PORT = int(os.environ.get("EGA_POOL_UI_PORT", "8089"))
API = os.environ.get("EGA_POOL_API", "http://127.0.0.1:4000/api/pools")
PUBLIC_HOST = os.environ.get("EGA_PUBLIC_HOST", "105.225.100.58")


def fetch_pools():
    try:
        with urllib.request.urlopen(API, timeout=8) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)


def fmt_hps(n):
    try:
        n = float(n or 0)
    except Exception:
        return "0 H/s"
    u = ["H/s", "kH/s", "MH/s", "GH/s", "TH/s"]
    i = 0
    while n >= 1000 and i < len(u) - 1:
        n /= 1000
        i += 1
    if n >= 100:
        return f"{n:.1f} {u[i]}"
    if n >= 10:
        return f"{n:.2f} {u[i]}"
    return f"{n:.3f} {u[i]}"


def page() -> bytes:
    data, err = fetch_pools()
    cards = []
    if err:
        cards.append(f'<div class="err">Pool API offline: {err}<br/>Start: <code>bash scripts/start-miningcore.sh</code></div>')
    else:
        pools = (data or {}).get("pools") or []
        if not pools:
            cards.append('<div class="err">No pools configured.</div>')
        for p in pools:
            ports = p.get("ports") or {}
            port = next(iter(ports.keys()), "?")
            algo = (p.get("coin") or {}).get("algorithm") or p.get("id")
            st = p.get("poolStats") or {}
            ns = p.get("networkStats") or {}
            cards.append(
                f"""
<div class="card">
  <h2>{algo}</h2>
  <div class="grid">
    <div><div class="l">Stratum</div><div class="v mono">stratum+tcp://{PUBLIC_HOST}:{port}</div></div>
    <div><div class="l">Miners online</div><div class="v">{st.get('connectedMiners', 0)}</div></div>
    <div><div class="l">Pool hashrate</div><div class="v">{fmt_hps(st.get('poolHashrate'))}</div></div>
    <div><div class="l">Network height</div><div class="v">{ns.get('blockHeight', '—')}</div></div>
    <div><div class="l">Network hashrate</div><div class="v">{fmt_hps(ns.get('networkHashrate'))}</div></div>
    <div><div class="l">Blocks found</div><div class="v">{p.get('totalBlocks', 0)}</div></div>
  </div>
  <p class="hint">Username = your EGA address (E…) · Password = <code>x</code></p>
</div>"""
            )

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="refresh" content="30"/>
<title>EGA Mining Pool</title>
<style>
:root {{ --bg:#070b14; --card:#121a2b; --line:#243049; --text:#eef2f8; --muted:#9aa8c0; --accent:#2dd4bf; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,sans-serif; background:var(--bg); color:var(--text); }}
.wrap {{ max-width:960px; margin:0 auto; padding:1.25rem; }}
h1 {{ margin:0 0 .35rem; font-size:1.6rem; }}
.sub {{ color:var(--muted); margin-bottom:1.25rem; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; margin:0 0 1rem; }}
.card h2 {{ margin:0 0 .75rem; font-size:1.15rem; color:var(--accent); }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:.75rem; }}
.l {{ color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; }}
.v {{ font-weight:700; margin-top:.15rem; word-break:break-all; }}
.mono {{ font-family:ui-monospace,Menlo,Consolas,monospace; font-size:.88rem; }}
.hint {{ color:var(--muted); font-size:.9rem; margin:.85rem 0 0; }}
.err {{ background:rgba(248,113,113,.12); border:1px solid rgba(248,113,113,.35); color:#fecaca; padding:1rem; border-radius:12px; }}
a {{ color:var(--accent); }}
code {{ background:rgba(255,255,255,.06); padding:.1rem .35rem; border-radius:4px; }}
.note {{ background:rgba(45,212,191,.08); border:1px solid rgba(45,212,191,.22); padding:.85rem 1rem; border-radius:12px; margin-bottom:1rem; font-size:.92rem; }}
table {{ width:100%; border-collapse:collapse; font-size:.92rem; }}
th,td {{ text-align:left; padding:.5rem .4rem; border-bottom:1px solid var(--line); }}
th {{ color:var(--muted); font-size:.75rem; text-transform:uppercase; }}
</style></head><body><div class="wrap">
<h1>Egalitarianism pool</h1>
<p class="sub">Live stats · refreshes every 30s · not the raw API dump</p>
<div class="note">
  <strong>How to mine:</strong> point your miner at the stratum below.
  GPU Verthash and Scrypt have full share verification (Miningcore).
  RandomX / YespowerEGA: use <strong>solo</strong> on your node until custom pool support lands.
</div>
{''.join(cards)}
<div class="card">
  <h2>Connection cheat-sheet</h2>
  <table>
    <tr><th>Algo</th><th>Stratum</th><th>Status</th></tr>
    <tr><td>Verthash (GPU)</td><td class="mono">stratum+tcp://{PUBLIC_HOST}:3334</td><td>Pool live</td></tr>
    <tr><td>Scrypt</td><td class="mono">stratum+tcp://{PUBLIC_HOST}:3336</td><td>Pool live</td></tr>
    <tr><td>RandomX</td><td class="mono">solo: easy-mine.sh randomx</td><td>Solo only</td></tr>
    <tr><td>YespowerEGA</td><td class="mono">solo: easy-mine.sh yespower-ega</td><td>Solo only</td></tr>
  </table>
  <p class="hint">Dashboard API (machines): <a href="{API}">{API}</a> · Explorer: <a href="http://127.0.0.1:8088/">local explorer</a></p>
</div>
</div></body></html>"""
    return html.encode()


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        body = page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    print(f"Pool UI http://{HOST}:{PORT}/  (API {API})")
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()


if __name__ == "__main__":
    main()
