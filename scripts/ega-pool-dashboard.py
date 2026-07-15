#!/usr/bin/env python3
"""
EGA mining pool UI — HeroMiners-style single-coin dashboard (4 algos).
Backed by Miningcore REST API. Verthash+Scrypt live; RX/YP marked solo until shared stratum ships.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("EGA_POOL_UI_HOST", "0.0.0.0")
PORT = int(os.environ.get("EGA_POOL_UI_PORT", "8089"))
API_BASE = os.environ.get("EGA_POOL_API_BASE", "http://127.0.0.1:4000").rstrip("/")
PUBLIC_HOST = os.environ.get("EGA_PUBLIC_HOST", "105.225.100.58")

# Product definition: four “networks” (algos) under one coin
ALGOS = [
    {
        "id": "randomx",
        "name": "RandomX",
        "who": "Modern CPU / laptop",
        "pool_id": None,  # not in Miningcore yet
        "port": 3333,
        "mode": "solo",
        "solo": "ega-cli generatetoaddress 1 $(ega-cli getnewaddress) 10000000 randomx",
        "stratum": None,
    },
    {
        "id": "verthash",
        "name": "Verthash",
        "who": "Consumer GPU",
        "pool_id": "ega-verthash",
        "port": 3334,
        "mode": "pool",
        "solo": "easy-mine.sh verthash  # node CPU path; prefer GPU miner",
        "stratum": f"stratum+tcp://{PUBLIC_HOST}:3334",
    },
    {
        "id": "yespower-ega",
        "name": "YespowerEGA",
        "who": "Phone / Pi / weak CPU",
        "pool_id": None,
        "port": 3335,
        "mode": "solo",
        "solo": "ega-cli generatetoaddress 1 $(ega-cli getnewaddress) 10000000 yespower-ega",
        "stratum": None,
    },
    {
        "id": "scrypt",
        "name": "Scrypt",
        "who": "Hard door / capital market",
        "pool_id": "ega-scrypt",
        "port": 3336,
        "mode": "pool",
        "solo": "easy-mine.sh scrypt",
        "stratum": f"stratum+tcp://{PUBLIC_HOST}:3336",
    },
]


def api_get(path: str):
    url = f"{API_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)


def fmt_hps(n):
    try:
        n = float(n or 0)
    except Exception:
        return "0 H/s"
    units = ["H/s", "kH/s", "MH/s", "GH/s", "TH/s", "PH/s"]
    i = 0
    while n >= 1000 and i < len(units) - 1:
        n /= 1000.0
        i += 1
    if n >= 100:
        return f"{n:.1f} {units[i]}"
    if n >= 10:
        return f"{n:.2f} {units[i]}"
    return f"{n:.3f} {units[i]}"


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


CSS = """
:root{--bg:#0b0f14;--panel:#151b24;--line:#2a3444;--text:#e8eef7;--muted:#8b9bb0;
--accent:#3dd6c6;--accent2:#5b8def;--good:#3dd68c;--warn:#e2b84a;--bad:#f07178}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1100px;margin:0 auto;padding:0 1rem 2.5rem}
.top{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:.75rem;
padding:1rem 0;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(11,15,20,.94);z-index:5}
.brand{font-weight:800;letter-spacing:-.02em;color:var(--text);font-size:1.05rem}
.nav{display:flex;flex-wrap:wrap;gap:.35rem}
.nav a{color:var(--muted);padding:.4rem .7rem;border-radius:8px;font-size:.9rem;font-weight:600}
.nav a:hover,.nav a.on{background:var(--panel);color:var(--text);text-decoration:none}
h1{font-size:1.55rem;margin:.9rem 0 .35rem;letter-spacing:-.03em}
h2{font-size:1.05rem;margin:0 0 .65rem}
.sub{color:var(--muted);margin-bottom:1rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.65rem;margin:1rem 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:.75rem .85rem}
.stat .l{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700}
.stat .v{font-size:1.15rem;font-weight:800;margin-top:.2rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1rem 1.1rem;margin:0 0 1rem}
.note{background:rgba(61,214,198,.08);border:1px solid rgba(61,214,198,.25);border-radius:12px;padding:.85rem 1rem;margin:1rem 0;font-size:.92rem}
.warn{background:rgba(226,184,74,.08);border-color:rgba(226,184,74,.35)}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{text-align:left;padding:.55rem .45rem;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.84rem;word-break:break-all}
.badge{display:inline-block;padding:.12rem .45rem;border-radius:999px;font-size:.72rem;font-weight:700}
.badge-pool{background:rgba(61,214,140,.15);color:var(--good)}
.badge-solo{background:rgba(226,184,74,.15);color:var(--warn)}
.badge-soon{background:rgba(91,141,239,.15);color:var(--accent2)}
pre{background:#0a1018;border:1px solid var(--line);border-radius:10px;padding:.75rem;overflow:auto;font-size:.82rem}
.search{display:flex;gap:.5rem;margin:1rem 0;flex-wrap:wrap}
.search input{flex:1;min-width:200px;background:#0a1018;border:1px solid var(--line);color:var(--text);
border-radius:10px;padding:.65rem .8rem}
.search button{background:var(--accent);color:#042f2e;border:0;border-radius:10px;padding:.65rem 1rem;font-weight:750;cursor:pointer}
.err{color:#fecaca;background:rgba(240,113,120,.1);border:1px solid rgba(240,113,120,.35);padding:.85rem;border-radius:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
@media(max-width:720px){.grid2{grid-template-columns:1fr}}
footer{margin-top:1.5rem;color:var(--muted);font-size:.82rem}
"""


def layout(title: str, active: str, body: str) -> bytes:
    def nav(name, href):
        cls = "on" if name == active else ""
        return f'<a class="{cls}" href="{href}">{name}</a>'

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="refresh" content="45"/>
<title>{esc(title)} · EGA Pool</title>
<style>{CSS}</style>
</head><body><div class="wrap">
<header class="top">
  <a class="brand" href="/">Egalitarianism Pool</a>
  <nav class="nav">
    {nav("Home","/")}
    {nav("Start","/start")}
    {nav("Blocks","/blocks")}
    {nav("Wallet","/wallet")}
    {nav("Mission","/mission")}
  </nav>
</header>
{body}
<footer>EGA MultiShield-4 · Solo + shared for everyone · API <span class="mono">{esc(API_BASE)}/api/pools</span></footer>
</div></body></html>"""
    return html.encode()


def pool_map():
    data, err = api_get("/api/pools")
    if err or not data:
        return {}, err
    out = {}
    for p in data.get("pools") or []:
        out[p.get("id")] = p
    return out, None


def page_home() -> bytes:
    pools, err = pool_map()
    total_miners = 0
    total_blocks = 0
    height = "—"
    net_hr = 0
    cards = []
    if err:
        api_note = f'<div class="err">Miningcore API: {esc(err)}. Start: <code>bash scripts/start-miningcore.sh</code></div>'
    else:
        api_note = ""
        for p in pools.values():
            st = p.get("poolStats") or {}
            ns = p.get("networkStats") or {}
            total_miners += int(st.get("connectedMiners") or 0)
            total_blocks += int(p.get("totalBlocks") or 0)
            height = ns.get("blockHeight", height)
            net_hr = max(net_hr, float(ns.get("networkHashrate") or 0))

    for a in ALGOS:
        p = pools.get(a["pool_id"]) if a["pool_id"] else None
        if a["mode"] == "pool" and p:
            st = p.get("poolStats") or {}
            ns = p.get("networkStats") or {}
            badge = '<span class="badge badge-pool">SHARED POOL LIVE</span>'
            extra = f"""
            <div class="grid2" style="margin-top:.6rem">
              <div><div class="l" style="color:var(--muted);font-size:.7rem">POOL HR</div><div class="mono">{esc(fmt_hps(st.get('poolHashrate')))}</div></div>
              <div><div class="l" style="color:var(--muted);font-size:.7rem">MINERS</div><div class="mono">{esc(st.get('connectedMiners',0))}</div></div>
              <div><div class="l" style="color:var(--muted);font-size:.7rem">STRATUM</div><div class="mono">{esc(a['stratum'])}</div></div>
              <div><div class="l" style="color:var(--muted);font-size:.7rem">HEIGHT</div><div class="mono">{esc(ns.get('blockHeight','—'))}</div></div>
            </div>
            <p style="margin-top:.6rem;color:var(--muted);font-size:.88rem">User = EGA address · Pass = <code>x</code> · Solo also OK</p>
            """
        elif a["mode"] == "pool":
            badge = '<span class="badge badge-soon">POOL OFFLINE</span>'
            extra = f'<p class="mono" style="margin-top:.5rem">{esc(a["stratum"] or "")}</p>'
        else:
            badge = '<span class="badge badge-solo">SOLO NOW</span> <span class="badge badge-soon">SHARED SOON</span>'
            extra = f"""
            <p style="margin-top:.5rem;color:var(--muted);font-size:.9rem">
              Shared stratum for this algo is <strong>mission-required</strong> and being engineered
              (Miningcore must verify EGA RandomX / YespowerEGA headers). Until then:
            </p>
            <pre>{esc(a["solo"])}</pre>
            <p style="color:var(--muted);font-size:.85rem">Port reserved for shared: <span class="mono">:{a['port']}</span></p>
            """
        cards.append(
            f"""<div class="card">
            <h2>{esc(a['name'])} {badge}</h2>
            <p style="color:var(--muted);font-size:.9rem">{esc(a['who'])}</p>
            {extra}
            </div>"""
        )

    body = f"""
<h1>EGA mining pool</h1>
<p class="sub">One coin · four algorithms · solo <em>and</em> shared for accessibility</p>
{api_note}
<div class="stats">
  <div class="stat"><div class="l">Connected miners</div><div class="v">{esc(total_miners)}</div></div>
  <div class="stat"><div class="l">Pool blocks</div><div class="v">{esc(total_blocks)}</div></div>
  <div class="stat"><div class="l">Chain height</div><div class="v">{esc(height)}</div></div>
  <div class="stat"><div class="l">Network HR (API)</div><div class="v" style="font-size:1rem">{esc(fmt_hps(net_hr))}</div></div>
</div>
<div class="note">
  <strong>Mission:</strong> weak phones and rich GPUs share the same chain (MultiShield-4).
  Verthash + Scrypt shared pools are live. RandomX + YespowerEGA shared pools are next engineering —
  solo already works for everyone with a node.
</div>
{''.join(cards)}
"""
    return layout("Home", "Home", body)


def page_start() -> bytes:
    rows = []
    for a in ALGOS:
        if a["stratum"]:
            how = f'<span class="mono">{esc(a["stratum"])}</span><br/><span style="color:var(--muted);font-size:.85rem">user = your E… address, pass = x</span>'
            mode = '<span class="badge badge-pool">shared + solo</span>'
        else:
            how = f'<pre style="margin:0">{esc(a["solo"])}</pre>'
            mode = '<span class="badge badge-solo">solo today</span>'
        rows.append(
            f"<tr><td><strong>{esc(a['name'])}</strong><br/><span style='color:var(--muted);font-size:.8rem'>{esc(a['who'])}</span></td>"
            f"<td>{mode}</td><td>{how}</td></tr>"
        )
    body = f"""
<h1>Start mining</h1>
<p class="sub">Copy the connection for your hardware. Same chain either way.</p>
<div class="card">
<table>
<tr><th>Algorithm</th><th>Mode</th><th>How to connect</th></tr>
{''.join(rows)}
</table>
</div>
<div class="card">
<h2>GPU Verthash (shared)</h2>
<pre>VerthashMiner -a verthash \\
  -o stratum+tcp://{esc(PUBLIC_HOST)}:3334 \\
  -u YOUR_EGA_ADDRESS -p x \\
  --all-cl-devices -f ega-verthash.dat \\
  --no-verthash-data_verification</pre>
<p class="sub">EGA 256 MiB dataset — see ega-verthash-miner repo (not stock Vertcoin file).</p>
</div>
<div class="card">
<h2>Join the network (any miner)</h2>
<pre># ~/.ega/ega.conf on your full node
addnode={esc(PUBLIC_HOST)}:20201</pre>
</div>
"""
    return layout("Start", "Start", body)


def page_blocks() -> bytes:
    pools, err = pool_map()
    sections = []
    if err:
        sections.append(f'<div class="err">{esc(err)}</div>')
    for a in ALGOS:
        if not a["pool_id"]:
            sections.append(
                f'<div class="card"><h2>{esc(a["name"])}</h2>'
                f'<p style="color:var(--muted)">Shared pool not online yet — solo blocks appear on the '
                f'<a href="http://127.0.0.1:8088/">explorer</a>.</p></div>'
            )
            continue
        data, e2 = api_get(f"/api/pools/{a['pool_id']}/blocks")
        if e2:
            sections.append(f'<div class="card"><h2>{esc(a["name"])}</h2><div class="err">{esc(e2)}</div></div>')
            continue
        blocks = data if isinstance(data, list) else []
        rows = []
        for b in blocks[:40]:
            rows.append(
                f"<tr><td>{esc(b.get('blockHeight', b.get('height','')))}</td>"
                f"<td class='mono'>{esc(str(b.get('status', b.get('reward','')))[:48])}</td>"
                f"<td class='mono'>{esc(str(b.get('created', b.get('confirmationProgress','')))[:32])}</td></tr>"
            )
        sections.append(
            f"""<div class="card"><h2>{esc(a['name'])} · pool blocks</h2>
            <table><tr><th>Height</th><th>Status / reward</th><th>Info</th></tr>
            {''.join(rows) or '<tr><td colspan="3" style="color:var(--muted)">No pool blocks yet — connect miners.</td></tr>'}
            </table></div>"""
        )
    body = f"""
<h1>Blocks</h1>
<p class="sub">Blocks found by the shared pools (Miningcore). Solo blocks are on the chain explorer.</p>
{''.join(sections)}
"""
    return layout("Blocks", "Blocks", body)


def page_wallet(addr: str = "") -> bytes:
    addr = (addr or "").strip()
    form = f"""
<form class="search" method="get" action="/wallet">
  <input name="address" value="{esc(addr)}" placeholder="Paste your EGA address (E…)" />
  <button type="submit">Lookup</button>
</form>
"""
    body_extra = ""
    if addr:
        chunks = []
        for a in ALGOS:
            if not a["pool_id"]:
                chunks.append(
                    f"<div class='card'><h2>{esc(a['name'])}</h2>"
                    f"<p style='color:var(--muted)'>Shared pool N/A — solo rewards show in "
                    f"<a href='http://127.0.0.1:8088/address/{esc(urllib.parse.quote(addr))}'>explorer</a>.</p></div>"
                )
                continue
            # Miningcore miner endpoint
            data, err = api_get(f"/api/pools/{a['pool_id']}/miners/{urllib.parse.quote(addr)}")
            if err:
                # try list miners
                data2, err2 = api_get(f"/api/pools/{a['pool_id']}/miners")
                chunks.append(
                    f"<div class='card'><h2>{esc(a['name'])}</h2>"
                    f"<p style='color:var(--muted)'>No miner stats yet for this address on shared pool "
                    f"(connect a worker or {esc(err)[:80]}).</p></div>"
                )
                continue
            if not data:
                chunks.append(
                    f"<div class='card'><h2>{esc(a['name'])}</h2><p style='color:var(--muted)'>No shares yet.</p></div>"
                )
                continue
            # flexible field names
            hr = data.get("performance", {}) if isinstance(data.get("performance"), dict) else {}
            ph = data.get("pendingBalance") or data.get("pendingShares") or data.get("pending")
            tb = data.get("totalPaid") or data.get("paid")
            chunks.append(
                f"""<div class="card"><h2>{esc(a['name'])} · your stats</h2>
                <table class="kv">
                <tr><th>Raw</th><td class="mono" style="font-size:.75rem">{esc(json.dumps(data)[:500])}…</td></tr>
                </table>
                <p style="color:var(--muted);font-size:.85rem">Pending/paid fields depend on Miningcore payment config.</p>
                </div>"""
            )
        body_extra = f"<h2>Results for <span class='mono'>{esc(addr)}</span></h2>" + "".join(chunks)

    body = f"""
<h1>Wallet lookup</h1>
<p class="sub">Like HeroMiners: paste your address to see pool activity. Solo balance is on the explorer.</p>
{form}
{body_extra or '<div class="note">Enter the same address you use as stratum username.</div>'}
"""
    return layout("Wallet", "Wallet", body)


def page_mission() -> bytes:
    body = f"""
<h1>Accessibility mission</h1>
<p class="sub">Why four algos and light clients matter</p>
<div class="card">
<p><strong>Egalitarianism</strong> means equality of opportunity to mine and hold value —
not only people who can buy ASICs or cloud VPS.</p>
<ul style="margin:1rem 0 0 1.2rem;color:var(--muted)">
<li>RandomX — normal laptops</li>
<li>YespowerEGA — phones, Pi, old CPUs</li>
<li>Verthash — normal GPUs</li>
<li>Scrypt — hard door so capital markets can’t ignore the chain</li>
</ul>
</div>
<div class="card">
<h2>Solo vs shared (both required)</h2>
<p><strong>Solo:</strong> you find a block → you get the full 50,000 EGA. High variance.</p>
<p style="margin-top:.5rem"><strong>Shared (pool):</strong> many miners submit shares → steadier payouts when the pool finds blocks.</p>
<p style="margin-top:.75rem;color:var(--muted)">Users must have <em>both</em> options on all four algos. VH+Scrypt shared are live; RX+YP shared are in progress.</p>
</div>
<div class="card">
<h2>Phones & tablets</h2>
<p>Full archival nodes belong on always-on PCs. Phones get <strong>light wallets</strong> and <strong>CPU mining</strong> (Yespower/RandomX) so poor devices still participate. See <span class="mono">docs/ega/ACCESSIBILITY-ROADMAP.md</span>.</p>
</div>
"""
    return layout("Mission", "Mission", body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        q = parse_qs(u.query)
        try:
            if path == "/":
                body = page_home()
            elif path == "/start":
                body = page_start()
            elif path == "/blocks":
                body = page_blocks()
            elif path == "/wallet":
                body = page_wallet((q.get("address") or [""])[0])
            elif path == "/mission":
                body = page_mission()
            else:
                body = layout("Not found", "", '<div class="err">Page not found.</div>')
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            err = f'<div class="err">{esc(e)}</div>'.encode()
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)


def main():
    print(f"EGA Pool UI http://{HOST}:{PORT}/  (Miningcore {API_BASE})")
    print("Pages: / /start /blocks /wallet /mission")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
