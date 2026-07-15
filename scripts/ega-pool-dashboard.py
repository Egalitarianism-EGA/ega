#!/usr/bin/env python3
"""EGA pool site — Solo vs Shared, clear setup for every algo. User-facing only."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("EGA_POOL_UI_HOST", "0.0.0.0")
PORT = int(os.environ.get("EGA_POOL_UI_PORT", "8089"))
API_BASE = os.environ.get("EGA_POOL_API_BASE", "http://127.0.0.1:4000").rstrip("/")
PUBLIC_HOST = os.environ.get("EGA_PUBLIC_HOST", "105.225.100.58")

# Four networks under one coin
NETWORKS = [
    {
        "key": "randomx",
        "name": "RandomX",
        "hw": "Laptop & desktop CPU",
        "shared": True,
        "port": 3333,
        "pool_id": None,  # stats from ega-algo-stratum (not Miningcore)
        "stratum_live": True,
        "solo_cmd": "ega-cli generatetoaddress 1 $(ega-cli getnewaddress) 10000000 randomx",
        "stratum": f"stratum+tcp://{PUBLIC_HOST}:3333",
    },
    {
        "key": "verthash",
        "name": "Verthash",
        "hw": "Normal GPU",
        "shared": True,
        "port": 3334,
        "pool_id": "ega-verthash",
        "stratum_live": True,
        "solo_cmd": "ega-cli generatetoaddress 1 $(ega-cli getnewaddress) 10000000 verthash",
        "stratum": f"stratum+tcp://{PUBLIC_HOST}:3334",
        "gpu_example": f"""VerthashMiner -a verthash \\
  -o stratum+tcp://{PUBLIC_HOST}:3334 \\
  -u YOUR_EGA_ADDRESS -p x \\
  --all-cl-devices -f ega-verthash.dat \\
  --no-verthash-data_verification""",
    },
    {
        "key": "yespower-ega",
        "name": "YespowerEGA",
        "hw": "Phone, Pi, weak CPU",
        "shared": True,
        "port": 3335,
        "pool_id": None,
        "stratum_live": True,
        "solo_cmd": "ega-cli generatetoaddress 1 $(ega-cli getnewaddress) 10000000 yespower-ega",
        "stratum": f"stratum+tcp://{PUBLIC_HOST}:3335",
    },
    {
        "key": "scrypt",
        "name": "Scrypt",
        "hw": "CPU / future ASIC path",
        "shared": True,
        "port": 3336,
        "pool_id": "ega-scrypt",
        "stratum_live": True,
        "solo_cmd": "ega-cli generatetoaddress 1 $(ega-cli getnewaddress) 10000000 scrypt",
        "stratum": f"stratum+tcp://{PUBLIC_HOST}:3336",
    },
]


def api_get(path: str):
    try:
        with urllib.request.urlopen(f"{API_BASE}{path}", timeout=10) as r:
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
    return f"{n:.2f} {u[i]}" if n < 100 else f"{n:.1f} {u[i]}"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


CSS = """
:root{--bg:#0b0f14;--panel:#151b24;--line:#2a3444;--text:#e8eef7;--muted:#8b9bb0;
--accent:#3dd6c6;--good:#3dd68c;--warn:#e2b84a;--blue:#5b8def}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.5}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1000px;margin:0 auto;padding:0 1rem 2.5rem}
.top{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:space-between;align-items:center;
padding:1rem 0;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(11,15,20,.95);z-index:5}
.brand{font-weight:800;color:var(--text)}
.nav{display:flex;flex-wrap:wrap;gap:.25rem}
.nav a{color:var(--muted);padding:.4rem .65rem;border-radius:8px;font-weight:600;font-size:.9rem}
.nav a.on,.nav a:hover{background:var(--panel);color:var(--text);text-decoration:none}
h1{font-size:1.5rem;margin:1rem 0 .35rem}
h2{font-size:1.05rem;margin:0 0 .6rem}
.sub{color:var(--muted);margin-bottom:1rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1rem;margin:0 0 1rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.6rem;margin:1rem 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:.7rem .8rem}
.stat .l{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700}
.stat .v{font-size:1.15rem;font-weight:800;margin-top:.15rem}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{text-align:left;padding:.55rem .4rem;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-size:.72rem;text-transform:uppercase}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.84rem;word-break:break-all}
.badge{display:inline-block;padding:.12rem .45rem;border-radius:999px;font-size:.72rem;font-weight:700}
.b-shared{background:rgba(61,214,140,.15);color:var(--good)}
.b-solo{background:rgba(226,184,74,.15);color:var(--warn)}
pre{background:#0a1018;border:1px solid var(--line);border-radius:10px;padding:.7rem;overflow:auto;font-size:.8rem;margin:.5rem 0}
.note{background:rgba(61,214,198,.07);border:1px solid rgba(61,214,198,.22);border-radius:12px;padding:.85rem 1rem;margin:1rem 0;font-size:.92rem}
.two{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
@media(max-width:720px){.two{grid-template-columns:1fr}}
.search{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}
.search input{flex:1;min-width:180px;background:#0a1018;border:1px solid var(--line);color:var(--text);border-radius:10px;padding:.65rem}
.search button{background:var(--accent);color:#042f2e;border:0;border-radius:10px;padding:.65rem 1rem;font-weight:750;cursor:pointer}
.err{color:#fecaca;background:rgba(240,113,120,.1);border:1px solid rgba(240,113,120,.35);padding:.8rem;border-radius:12px}
footer{margin-top:1.5rem;color:var(--muted);font-size:.8rem}
.col h3{font-size:.95rem;margin-bottom:.4rem}
"""


def layout(title, active, body):
    def n(label, href):
        return f'<a class="{"on" if label==active else ""}" href="{href}">{label}</a>'

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="refresh" content="40"/>
<title>{esc(title)} · EGA Pool</title><style>{CSS}</style></head><body>
<div class="wrap">
<header class="top">
  <a class="brand" href="/">Egalitarianism · Mine</a>
  <nav class="nav">
    {n("Home","/")}{n("Solo","/solo")}{n("Shared","/shared")}{n("Start","/start")}
    {n("Blocks","/blocks")}{n("Wallet","/wallet")}
  </nav>
</header>
{body}
<footer>EGA · four algorithms · solo and shared · seed {esc(PUBLIC_HOST)}:20201</footer>
</div></body></html>""".encode()


def pools_by_id():
    data, err = api_get("/api/pools")
    if err or not data:
        return {}, err
    return {p["id"]: p for p in (data.get("pools") or [])}, None


def page_home():
    pools, err = pools_by_id()
    miners = blocks = 0
    height = "—"
    for p in pools.values():
        st = p.get("poolStats") or {}
        ns = p.get("networkStats") or {}
        miners += int(st.get("connectedMiners") or 0)
        blocks += int(p.get("totalBlocks") or 0)
        height = ns.get("blockHeight", height)

    rows = []
    for n in NETWORKS:
        p = pools.get(n["pool_id"]) if n.get("pool_id") else None
        if n.get("shared") and n.get("stratum_live"):
            if p:
                st = p.get("poolStats") or {}
                stats = f"Pool miners: {st.get('connectedMiners',0)} · {fmt_hps(st.get('poolHashrate'))}"
            else:
                stats = f"Stratum :{n['port']} · solo also OK"
            mode = '<span class="badge b-shared">Shared live</span> · solo OK'
        elif n.get("shared"):
            mode = '<span class="badge b-shared">Shared</span>'
            stats = "Start pool services"
        else:
            mode = '<span class="badge b-solo">Solo</span>'
            stats = "Mine with your own node"
        rows.append(
            f"<tr><td><strong>{esc(n['name'])}</strong><br/><span style='color:var(--muted);font-size:.8rem'>{esc(n['hw'])}</span></td>"
            f"<td>{mode}</td><td style='color:var(--muted);font-size:.88rem'>{esc(stats)}</td></tr>"
        )

    body = f"""
<h1>Mine EGA</h1>
<p class="sub">One coin, four algorithms. Choose <strong>solo</strong> or <strong>shared</strong> below.</p>
{"<div class='err'>Pool engine offline — shared Verthash/Scrypt need Miningcore. Solo still works on any node.</div>" if err else ""}
<div class="stats">
  <div class="stat"><div class="l">Shared miners online</div><div class="v">{esc(miners)}</div></div>
  <div class="stat"><div class="l">Shared pool blocks</div><div class="v">{esc(blocks)}</div></div>
  <div class="stat"><div class="l">Chain height</div><div class="v">{esc(height)}</div></div>
  <div class="stat"><div class="l">Network peers</div><div class="v" style="font-size:.95rem">Use seed {esc(PUBLIC_HOST)}</div></div>
</div>
<div class="two">
  <div class="card col">
    <h3>Solo mining</h3>
    <p style="color:var(--muted);font-size:.9rem;margin-bottom:.5rem">
      You run a node. When <em>you</em> find a block, you keep the full 50,000 EGA reward.
      Best if you want full control. Works on all 4 algorithms today.
    </p>
    <a href="/solo">Open solo guide →</a>
  </div>
  <div class="card col">
    <h3>Shared mining (pool)</h3>
    <p style="color:var(--muted);font-size:.9rem;margin-bottom:.5rem">
      Many miners combine work. You get paid by shares when the pool finds blocks — steadier than solo.
      Live now: <strong>Verthash</strong> + <strong>Scrypt</strong>. RandomX + YespowerEGA shared ports next.
    </p>
    <a href="/shared">Open shared guide →</a>
  </div>
</div>
<div class="card">
  <h2>All four networks</h2>
  <table>
    <tr><th>Algorithm</th><th>What you can do</th><th>Live stats</th></tr>
    {''.join(rows)}
  </table>
</div>
"""
    return layout("Home", "Home", body)


def page_solo():
    blocks = []
    for n in NETWORKS:
        blocks.append(
            f"""<div class="card">
            <h2>{esc(n['name'])} <span class="badge b-solo">Solo</span></h2>
            <p style="color:var(--muted);font-size:.9rem">{esc(n['hw'])}</p>
            <p style="margin:.5rem 0;font-size:.9rem"><strong>1.</strong> Run a full or light node (PC or Android Termux).</p>
            <p style="margin:.5rem 0;font-size:.9rem"><strong>2.</strong> Mine to your wallet:</p>
            <pre>{esc(n['solo_cmd'])}</pre>
            <p style="color:var(--muted);font-size:.85rem">You receive the whole block reward when you find a block (after maturity confirmations).</p>
            </div>"""
        )
    body = f"""
<h1>Solo mining</h1>
<p class="sub">Your node · your work · full block reward when you win.</p>
<div class="note">
  <strong>Setup once:</strong> install EGA, start <code>egad</code>, create an address with <code>ega-cli getnewaddress</code>.
  Join seed: <code>addnode={esc(PUBLIC_HOST)}:20201</code> in <code>~/.ega/ega.conf</code>.
  Android light node: see project docs <span class="mono">ANDROID-LIGHT-NODE.md</span>.
</div>
{''.join(blocks)}
"""
    return layout("Solo", "Solo", body)


def page_shared():
    pools, err = pools_by_id()
    live = []
    for n in NETWORKS:
        if not n.get("shared"):
            continue
        p = pools.get(n["pool_id"]) if n.get("pool_id") else None
        st = (p or {}).get("poolStats") or {}
        ns = (p or {}).get("networkStats") or {}
        live.append(
            f"""<div class="card">
            <h2>{esc(n['name'])} <span class="badge b-shared">Shared</span></h2>
            <p style="color:var(--muted);font-size:.9rem">{esc(n['hw'])}</p>
            <table>
              <tr><th>Stratum</th><td class="mono">{esc(n.get('stratum', f"stratum+tcp://{PUBLIC_HOST}:{n['port']}"))}</td></tr>
              <tr><th>Username</th><td>Your EGA address (starts with E)</td></tr>
              <tr><th>Password</th><td class="mono">x</td></tr>
              <tr><th>Miners (Miningcore)</th><td>{esc(st.get('connectedMiners', '—') if p else 'EGA stratum')}</td></tr>
              <tr><th>Pool hashrate</th><td>{esc(fmt_hps(st.get('poolHashrate')) if p else 'see solo+shared')}</td></tr>
              <tr><th>Height</th><td>{esc(ns.get('blockHeight', '—') if p else '—')}</td></tr>
            </table>
            {"<pre style='margin-top:.75rem'>"+esc(n.get('gpu_example',''))+"</pre>" if n.get('gpu_example') else ""}
            <p style="margin-top:.6rem;color:var(--muted);font-size:.88rem">You can still solo-mine this algo on your own node anytime.</p>
            </div>"""
        )

    body = f"""
<h1>Shared mining (pool)</h1>
<p class="sub">Combine hashrate with others · paid by shares · lower variance than solo.</p>
{"<div class='note'>Miningcore stats for Verthash/Scrypt offline — stratum ports may still work if started.</div>" if err else ""}
<div class="note">
  <strong>How shared works:</strong> your miner submits shares to the pool. When the pool finds a block,
  rewards go to the pool wallet / share scheme. Username = your payout address.
</div>
<h2 style="margin:1rem 0 .5rem">All four algorithms — shared stratum</h2>
{''.join(live)}
"""
    return layout("Shared", "Shared", body)


def page_start():
    # compact cheat sheet both modes
    body = f"""
<h1>Start here</h1>
<p class="sub">Pick hardware → pick solo or shared → copy settings.</p>
<div class="card">
<table>
<tr><th>Algo</th><th>Solo</th><th>Shared</th></tr>
<tr>
  <td><strong>RandomX</strong><br/><span style="color:var(--muted);font-size:.8rem">CPU</span></td>
  <td class="mono" style="font-size:.78rem">generatetoaddress … randomx</td>
  <td class="mono" style="font-size:.78rem">stratum+tcp://{esc(PUBLIC_HOST)}:3333 · user=E… pass=x</td>
</tr>
<tr>
  <td><strong>Verthash</strong><br/><span style="color:var(--muted);font-size:.8rem">GPU</span></td>
  <td class="mono" style="font-size:.78rem">node or GPU solo</td>
  <td class="mono" style="font-size:.78rem">stratum+tcp://{esc(PUBLIC_HOST)}:3334 · user=E… pass=x</td>
</tr>
<tr>
  <td><strong>YespowerEGA</strong><br/><span style="color:var(--muted);font-size:.8rem">Phone / weak CPU</span></td>
  <td class="mono" style="font-size:.78rem">generatetoaddress … yespower-ega</td>
  <td class="mono" style="font-size:.78rem">stratum+tcp://{esc(PUBLIC_HOST)}:3335 · user=E… pass=x</td>
</tr>
<tr>
  <td><strong>Scrypt</strong></td>
  <td class="mono" style="font-size:.78rem">generatetoaddress … scrypt</td>
  <td class="mono" style="font-size:.78rem">stratum+tcp://{esc(PUBLIC_HOST)}:3336 · user=E… pass=x</td>
</tr>
</table>
</div>
<div class="card">
<h2>Join the network</h2>
<pre>addnode={esc(PUBLIC_HOST)}:20201</pre>
<p style="color:var(--muted);font-size:.9rem">Wallet: desktop <code>ega-qt</code>, CLI, or web wallet on port 8090.</p>
</div>
"""
    return layout("Start", "Start", body)


def page_blocks():
    pools, err = pools_by_id()
    parts = []
    if err:
        parts.append(f'<div class="err">{esc(err)}</div>')
    for n in NETWORKS:
        if not n["pool_id"]:
            parts.append(
                f'<div class="card"><h2>{esc(n["name"])}</h2>'
                f'<p style="color:var(--muted)">Solo blocks show on the '
                f'<a href="http://{esc(PUBLIC_HOST)}:8088/">block explorer</a>.</p></div>'
            )
            continue
        data, e2 = api_get(f"/api/pools/{n['pool_id']}/blocks")
        rows = []
        if isinstance(data, list):
            for b in data[:30]:
                rows.append(
                    f"<tr><td>{esc(b.get('blockHeight',''))}</td>"
                    f"<td class='mono'>{esc(str(b.get('status',''))[:40])}</td>"
                    f"<td class='mono'>{esc(str(b.get('created',''))[:24])}</td></tr>"
                )
        parts.append(
            f"""<div class="card"><h2>{esc(n['name'])} · shared pool blocks</h2>
            <table><tr><th>Height</th><th>Status</th><th>When</th></tr>
            {''.join(rows) or '<tr><td colspan="3" style="color:var(--muted)">No pool blocks yet.</td></tr>'}
            </table></div>"""
        )
    body = f"<h1>Blocks</h1><p class='sub'>Found by shared pools. Solo finds appear on the explorer.</p>{''.join(parts)}"
    return layout("Blocks", "Blocks", body)


def page_wallet(addr=""):
    addr = (addr or "").strip()
    form = f"""<form class="search" method="get" action="/wallet">
      <input name="address" value="{esc(addr)}" placeholder="Your EGA address (E…)"/>
      <button type="submit">Lookup</button>
    </form>"""
    extra = ""
    if addr:
        bits = []
        for n in NETWORKS:
            if not n["pool_id"]:
                bits.append(
                    f"<div class='card'><h2>{esc(n['name'])}</h2>"
                    f"<p style='color:var(--muted)'>Solo rewards: "
                    f"<a href='http://{esc(PUBLIC_HOST)}:8088/address/{esc(urllib.parse.quote(addr))}'>open in explorer</a></p></div>"
                )
                continue
            data, err = api_get(f"/api/pools/{n['pool_id']}/miners/{urllib.parse.quote(addr)}")
            if err or not data:
                bits.append(
                    f"<div class='card'><h2>{esc(n['name'])} · shared</h2>"
                    f"<p style='color:var(--muted)'>No shared-pool activity for this address yet. "
                    f"Point a miner at stratum with this address as username.</p></div>"
                )
            else:
                bits.append(
                    f"<div class='card'><h2>{esc(n['name'])} · shared</h2>"
                    f"<pre>{esc(json.dumps(data, indent=2)[:1200])}</pre></div>"
                )
        extra = f"<p class='sub'>Address <span class='mono'>{esc(addr)}</span></p>" + "".join(bits)
    body = f"""
<h1>Wallet lookup</h1>
<p class="sub">Check shared-pool stats for your address. Solo balance is on the explorer / web wallet.</p>
{form}
{extra or '<div class="note">Enter the address you use as stratum username.</div>'}
"""
    return layout("Wallet", "Wallet", body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        q = parse_qs(u.query)
        pages = {
            "/": page_home,
            "/solo": page_solo,
            "/shared": page_shared,
            "/start": page_start,
            "/blocks": page_blocks,
        }
        try:
            if path == "/wallet":
                body = page_wallet((q.get("address") or [""])[0])
            elif path in pages:
                body = pages[path]()
            else:
                body = layout("404", "", '<div class="err">Not found</div>')
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
            b = f'<div class="err">{esc(e)}</div>'.encode()
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)


def main():
    print(f"Pool UI http://{HOST}:{PORT}/  Solo=/solo Shared=/shared")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
