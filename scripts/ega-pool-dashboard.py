#!/usr/bin/env python3
"""
EGA mining pool website (single-coin, 4 algos) — miner-facing UI.
Inspired by typical pool sites: Network | Shared pool | Solo, Start, Wallet lookup.
"""
from __future__ import annotations

import json
import os
import socket
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("EGA_POOL_UI_HOST", "0.0.0.0")
PORT = int(os.environ.get("EGA_POOL_UI_PORT", "8089"))
API_BASE = os.environ.get("EGA_POOL_API_BASE", "http://127.0.0.1:4000").rstrip("/")
STRATUM_STATS = os.environ.get("EGA_STRATUM_STATS", "http://127.0.0.1:3337").rstrip("/")
RPC_URL = os.environ.get("EGA_RPC_URL", "http://127.0.0.1:20202")
PUBLIC = os.environ.get("EGA_PUBLIC_HOST", "105.225.100.58")
EXPLORER = os.environ.get("EGA_EXPLORER_URL", f"http://{PUBLIC}:8088")
WALLET_WEB = os.environ.get("EGA_WALLET_URL", f"http://{PUBLIC}:8090")

ALGOS = [
    {"name": "RandomX", "hw": "CPU / laptop", "port": 3333, "mc": None, "tag": "rx"},
    {"name": "Verthash", "hw": "GPU", "port": 3334, "mc": "ega-verthash", "tag": "vh"},
    {"name": "YespowerEGA", "hw": "Phone / weak CPU", "port": 3335, "mc": None, "tag": "yp"},
    {"name": "Scrypt", "hw": "CPU / ASIC path", "port": 3336, "mc": "ega-scrypt", "tag": "sc"},
]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def api(path):
    try:
        with urllib.request.urlopen(f"{API_BASE}{path}", timeout=8) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)


def rpc_load():
    import base64
    from pathlib import Path
    user = passwd = ""
    conf = Path.home() / ".ega" / "ega.conf"
    if conf.is_file():
        for line in conf.read_text(errors="replace").splitlines():
            line = line.split("#", 1)[0].strip()
            if line.startswith("rpcuser="):
                user = line.split("=", 1)[1]
            elif line.startswith("rpcpassword="):
                passwd = line.split("=", 1)[1]
    def rpc(method, params=None):
        payload = json.dumps({"jsonrpc": "1.0", "id": "ui", "method": method, "params": params or []}).encode()
        req = urllib.request.Request(RPC_URL, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        if user or passwd:
            tok = base64.b64encode(f"{user}:{passwd}".encode()).decode()
            req.add_header("Authorization", f"Basic {tok}")
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode())
        if d.get("error"):
            raise RuntimeError(d["error"])
        return d["result"]
    return rpc


def fmt_hps(n):
    try:
        n = float(n or 0)
    except Exception:
        return "0 H/s"
    for u in ["H/s", "kH/s", "MH/s", "GH/s", "TH/s"]:
        if n < 1000:
            return f"{n:.2f} {u}" if n < 100 else f"{n:.1f} {u}"
        n /= 1000
    return f"{n:.2f} PH/s"


def port_open(port: int) -> bool:
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=0.4)
        s.close()
        return True
    except Exception:
        return False


def chain_stats():
    try:
        rpc = rpc_load()
        info = rpc("getblockchaininfo")
        mining = rpc("getmininginfo")
        peers = rpc("getconnectioncount")
        try:
            hr = float(rpc("getnetworkhashps", [120, -1]))
        except Exception:
            hr = 0.0
        diffs = info.get("difficulties") or {}
        return {
            "height": info.get("blocks"),
            "peers": peers,
            "hr": hr,
            "diffs": diffs,
            "algo": mining.get("pow_algo"),
            "ok": True,
        }
    except Exception as e:
        return {"ok": False, "err": str(e)}


CSS = """
:root{--bg:#12151c;--panel:#1a1f2b;--panel2:#222836;--line:#2d3548;--text:#eef1f6;--muted:#8b95a8;
--teal:#2dd4bf;--blue:#60a5fa;--green:#34d399;--yellow:#fbbf24;--pink:#f472b6}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;font-size:15px}
a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1120px;margin:0 auto;padding:0 1rem 3rem}
.top{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:.75rem;
padding:.85rem 0;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(18,21,28,.95);z-index:10;backdrop-filter:blur(8px)}
.logo{font-weight:800;font-size:1.05rem;color:#fff;letter-spacing:-.02em}
.logo span{color:var(--teal)}
.nav{display:flex;flex-wrap:wrap;gap:.2rem}
.nav a{color:var(--muted);padding:.45rem .7rem;border-radius:8px;font-weight:600;font-size:.88rem}
.nav a:hover,.nav a.on{background:var(--panel);color:#fff;text-decoration:none}
.bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.55rem;margin:1.1rem 0}
.bar .b{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:.7rem .8rem}
.bar .l{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700}
.bar .v{font-size:1.1rem;font-weight:800;margin-top:.15rem}
.bar .s{font-size:.75rem;color:var(--muted);margin-top:.15rem}
h1{font-size:1.55rem;margin:1rem 0 .35rem;letter-spacing:-.03em}
h2{font-size:1.05rem;margin:0 0 .65rem}
.sub{color:var(--muted);margin-bottom:1rem}
.cols{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.75rem;margin:1rem 0}
@media(max-width:900px){.cols{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:1rem 1.05rem;margin:0 0 1rem}
.card h3{font-size:.95rem;margin-bottom:.5rem;display:flex;align-items:center;gap:.4rem}
.card ul{margin:.4rem 0 0 1.1rem;color:var(--muted);font-size:.9rem}
.card li{margin:.25rem 0}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{text-align:left;padding:.6rem .45rem;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:.04em}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem;word-break:break-all}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:999px;font-size:.7rem;font-weight:700}
.ok{background:rgba(52,211,153,.15);color:var(--green)}
.warn{background:rgba(251,191,36,.12);color:var(--yellow)}
.bad{background:rgba(244,114,182,.12);color:var(--pink)}
pre{background:#0d1118;border:1px solid var(--line);border-radius:10px;padding:.75rem;overflow:auto;font-size:.8rem;margin:.5rem 0}
.copy{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap}
.copy code{background:#0d1118;padding:.35rem .55rem;border-radius:8px;border:1px solid var(--line);font-size:.8rem}
.btn{display:inline-block;background:var(--teal);color:#042f2e;padding:.55rem .9rem;border-radius:9px;font-weight:750;border:0;cursor:pointer;font-size:.9rem}
.btn:hover{filter:brightness(1.08);text-decoration:none;color:#042f2e}
.btn2{background:transparent;border:1px solid var(--line);color:var(--text)}
.note{background:rgba(45,212,191,.07);border:1px solid rgba(45,212,191,.2);border-radius:12px;padding:.85rem 1rem;margin:1rem 0;font-size:.9rem}
.search{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}
.search input{flex:1;min-width:200px;background:#0d1118;border:1px solid var(--line);color:var(--text);border-radius:10px;padding:.7rem}
.search button{background:var(--teal);color:#042f2e;border:0;border-radius:10px;padding:.7rem 1rem;font-weight:750;cursor:pointer}
.err{color:#fecaca;background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.3);padding:.8rem;border-radius:12px}
footer{margin-top:2rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.8rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem}
.algo-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.75rem}
"""


def layout(title, active, body):
    def n(lab, href):
        return f'<a class="{"on" if lab==active else ""}" href="{href}">{lab}</a>'
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="refresh" content="30"/>
<title>{esc(title)} · EGA Pool</title>
<style>{CSS}</style></head><body>
<div class="wrap">
<header class="top">
  <div class="logo">EGA <span>Pool</span></div>
  <nav class="nav">
    {n("Home","/")}{n("Start","/start")}{n("Solo","/solo")}{n("Shared","/shared")}
    {n("Blocks","/blocks")}{n("Workers","/workers")}{n("Payments","/payments")}{n("Wallet","/wallet")}
    <a href="{esc(EXPLORER)}" target="_blank">Explorer</a>
  </nav>
</header>
{body}
<footer>
  <span>Egalitarianism · MultiShield-4 · seed <span class="mono">{esc(PUBLIC)}:20201</span></span>
  <span><a href="{esc(WALLET_WEB)}">Web wallet</a> · <a href="https://egalitarianism-ega.github.io/ega-website/">Website</a></span>
</footer>
</div></body></html>""".encode()


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def top_bar(cs, mc_pools):
    miners = sum(int((p.get("poolStats") or {}).get("connectedMiners") or 0) for p in mc_pools.values())
    blocks = sum(int(p.get("totalBlocks") or 0) for p in mc_pools.values())
    open_ports = sum(1 for a in ALGOS if port_open(a["port"]))
    return f"""
<div class="bar">
  <div class="b"><div class="l">Network height</div><div class="v">{esc(cs.get('height','—'))}</div><div class="s">{esc(cs.get('peers',0))} peers</div></div>
  <div class="b"><div class="l">Network hashrate</div><div class="v" style="font-size:1rem">{esc(fmt_hps(cs.get('hr',0)))}</div><div class="s">from recent blocks</div></div>
  <div class="b"><div class="l">Shared miners</div><div class="v">{esc(miners)}</div><div class="s">Miningcore workers</div></div>
  <div class="b"><div class="l">Pool blocks</div><div class="v">{esc(blocks)}</div><div class="s">shared only</div></div>
  <div class="b"><div class="l">Stratum ports</div><div class="v">{esc(open_ports)}/4</div><div class="s">listening</div></div>
</div>"""


def load_mc():
    data, err = api("/api/pools")
    if err or not data:
        return {}, err
    return {p["id"]: p for p in (data.get("pools") or [])}, None


def page_home():
    cs = chain_stats()
    mc, err = load_mc()
    bar = top_bar(cs if cs.get("ok") else {}, mc)
    cards = []
    for a in ALGOS:
        up = port_open(a["port"])
        badge = f'<span class="badge ok">ONLINE</span>' if up else f'<span class="badge bad">OFFLINE</span>'
        st = ""
        if a["mc"] and a["mc"] in mc:
            ps = mc[a["mc"]].get("poolStats") or {}
            st = f"<div class='s' style='margin-top:.5rem;color:var(--muted)'>Miners {ps.get('connectedMiners',0)} · {fmt_hps(ps.get('poolHashrate'))}</div>"
        cards.append(f"""
        <div class="card">
          <h3>{esc(a['name'])} {badge}</h3>
          <div style="color:var(--muted);font-size:.85rem;margin-bottom:.45rem">{esc(a['hw'])}</div>
          <div class="copy"><code>stratum+tcp://{esc(PUBLIC)}:{a['port']}</code></div>
          <div style="margin-top:.45rem;font-size:.85rem;color:var(--muted)">user = <strong>your E… address</strong> · pass = <code>x</code></div>
          {st}
          <div style="margin-top:.65rem;font-size:.85rem">
            <a href="/shared">Shared setup</a> · <a href="/solo">Solo setup</a>
          </div>
        </div>""")
    body = f"""
<h1>Egalitarianism mining pool</h1>
<p class="sub">One coin · four algorithms · <strong>solo</strong> and <strong>shared</strong></p>
{bar}
{"<div class='err'>Chain RPC issue: "+esc(cs.get('err',''))+"</div>" if not cs.get("ok") else ""}
<div class="cols">
  <div class="card">
    <h3>🌐 Network</h3>
    <ul>
      <li>Height: <strong>{esc(cs.get('height','—'))}</strong></li>
      <li>Peers: <strong>{esc(cs.get('peers',0))}</strong></li>
      <li>Seed: <span class="mono">{esc(PUBLIC)}:20201</span></li>
      <li><a href="{esc(EXPLORER)}" target="_blank">Block explorer</a></li>
    </ul>
  </div>
  <div class="card">
    <h3>🤝 Shared pool</h3>
    <ul>
      <li>Connect miner → get paid by shares</li>
      <li>Steadier than solo</li>
      <li>All 4 algos have stratum ports</li>
      <li><a href="/shared">How to connect →</a></li>
    </ul>
  </div>
  <div class="card">
    <h3>⛏️ Solo mining</h3>
    <ul>
      <li>You find the block → full 50,000 EGA</li>
      <li>Run a node (PC or Android)</li>
      <li>Higher variance</li>
      <li><a href="/solo">Solo guide →</a></li>
    </ul>
  </div>
</div>
<div class="note">
  <strong>Quick start:</strong> get an address from the <a href="{esc(WALLET_WEB)}">web wallet</a> or <code>ega-cli getnewaddress</code>,
  then point your miner at the stratum below. Join the network with <code>addnode={esc(PUBLIC)}:20201</code>.
</div>
<h2 style="margin:1.25rem 0 .75rem">Algorithms</h2>
<div class="algo-grid">{''.join(cards)}</div>
"""
    return layout("Home", "Home", body)


def page_start():
    rows = []
    for a in ALGOS:
        up = "● online" if port_open(a["port"]) else "○ offline"
        rows.append(f"""
        <tr>
          <td><strong>{esc(a['name'])}</strong><br/><span style="color:var(--muted);font-size:.8rem">{esc(a['hw'])}</span></td>
          <td class="mono">stratum+tcp://{esc(PUBLIC)}:{a['port']}</td>
          <td>Your E… address</td>
          <td class="mono">x</td>
          <td>{up}</td>
        </tr>""")
    body = f"""
<h1>Start mining</h1>
<p class="sub">Copy these settings into your miner software.</p>
<div class="card">
<table>
<tr><th>Algorithm</th><th>Stratum (shared)</th><th>Username</th><th>Password</th><th>Status</th></tr>
{''.join(rows)}
</table>
</div>
<div class="card">
  <h2>GPU Verthash example</h2>
  <pre>VerthashMiner -a verthash \\
  -o stratum+tcp://{esc(PUBLIC)}:3334 \\
  -u YOUR_EGA_ADDRESS -p x \\
  --all-cl-devices -f ega-verthash.dat \\
  --no-verthash-data_verification</pre>
  <p style="color:var(--muted);font-size:.88rem">Need the EGA 256 MiB dataset (not Vertcoin’s file). See ega-verthash-miner on GitHub.</p>
</div>
<div class="card">
  <h2>CPU / phone (shared or solo)</h2>
  <p style="color:var(--muted);font-size:.9rem;margin-bottom:.5rem">Shared: use stratum for RandomX (:3333) or YespowerEGA (:3335) if your miner supports Bitcoin-style stratum.</p>
  <p style="color:var(--muted);font-size:.9rem;margin-bottom:.5rem">Solo (always works with a node):</p>
  <pre>ega-cli generatetoaddress 1 $(ega-cli getnewaddress) 10000000 yespower-ega
# or: randomx | verthash | scrypt</pre>
</div>
<div class="card">
  <h2>Join the chain first</h2>
  <pre># in ~/.ega/ega.conf
addnode={esc(PUBLIC)}:20201</pre>
</div>
"""
    return layout("Start", "Start", body)


def page_solo():
    body = f"""
<h1>Solo mining</h1>
<p class="sub">You run a node. When you find a block, you keep the <strong>full 50,000 EGA</strong> (after maturity).</p>
<div class="cols">
  <div class="card">
    <h3>1. Run a node</h3>
    <pre>egad -daemon
# Android Termux: pruned light node
# docs/ega/ANDROID-LIGHT-NODE.md</pre>
  </div>
  <div class="card">
    <h3>2. Connect to seed</h3>
    <pre>addnode={esc(PUBLIC)}:20201</pre>
  </div>
  <div class="card">
    <h3>3. Get an address</h3>
    <pre>ega-cli getnewaddress
# or web wallet {esc(WALLET_WEB)}</pre>
  </div>
</div>
<div class="card">
  <h2>Mine one block (any algo)</h2>
  <pre>ega-cli generatetoaddress 1 YOUR_ADDRESS 10000000 randomx
ega-cli generatetoaddress 1 YOUR_ADDRESS 10000000 yespower-ega
ega-cli generatetoaddress 1 YOUR_ADDRESS 10000000 verthash
ega-cli generatetoaddress 1 YOUR_ADDRESS 10000000 scrypt</pre>
  <p style="color:var(--muted);font-size:.88rem">Rewards stay immature for a few confirmations, then appear as spendable balance.</p>
</div>
<div class="note">Solo = high variance. Shared pool = steadier. You can use both.</div>
"""
    return layout("Solo", "Solo", body)


def page_shared():
    mc, err = load_mc()
    cards = []
    for a in ALGOS:
        up = port_open(a["port"])
        badge = '<span class="badge ok">STRATUM UP</span>' if up else '<span class="badge bad">STRATUM DOWN</span>'
        extra = ""
        if a["mc"] and a["mc"] in mc:
            st = mc[a["mc"]].get("poolStats") or {}
            ns = mc[a["mc"]].get("networkStats") or {}
            extra = f"""<tr><th>Miners</th><td>{esc(st.get('connectedMiners',0))}</td></tr>
            <tr><th>Pool HR</th><td>{esc(fmt_hps(st.get('poolHashrate')))}</td></tr>
            <tr><th>Height</th><td>{esc(ns.get('blockHeight','—'))}</td></tr>"""
        cards.append(f"""
        <div class="card">
          <h3>{esc(a['name'])} {badge}</h3>
          <p style="color:var(--muted);font-size:.88rem;margin-bottom:.5rem">{esc(a['hw'])}</p>
          <table>
            <tr><th>URL</th><td class="mono">stratum+tcp://{esc(PUBLIC)}:{a['port']}</td></tr>
            <tr><th>User</th><td>EGA address starting with E</td></tr>
            <tr><th>Pass</th><td class="mono">x</td></tr>
            {extra}
          </table>
        </div>""")
    body = f"""
<h1>Shared mining</h1>
<p class="sub">Many miners · shares · steadier payouts when the pool finds blocks.</p>
<div class="note">
  <strong>How it works:</strong> your miner sends <em>shares</em> (partial proofs of work) to the pool.
  When the pool finds a full block, rewards are distributed by share contribution.
  Username must be the address that should get paid.
</div>
{"<div class='err'>Miningcore API unreachable for Verthash/Scrypt stats (stratum may still accept miners).</div>" if err else ""}
<div class="algo-grid">{''.join(cards)}</div>
"""
    return layout("Shared", "Shared", body)


def page_blocks():
    mc, err = load_mc()
    parts = []
    if err:
        parts.append(f'<div class="err">{esc(err)}</div>')
    for a in ALGOS:
        if not a["mc"]:
            parts.append(f"""<div class="card"><h2>{esc(a['name'])}</h2>
            <p style="color:var(--muted)">Solo + EGA stratum blocks appear on the
            <a href="{esc(EXPLORER)}">explorer</a>.</p></div>""")
            continue
        data, e2 = api(f"/api/pools/{a['mc']}/blocks")
        rows = []
        if isinstance(data, list):
            for b in data[:40]:
                rows.append(
                    f"<tr><td>{esc(b.get('blockHeight',''))}</td>"
                    f"<td class='mono'>{esc(str(b.get('status',''))[:48])}</td>"
                    f"<td class='mono'>{esc(str(b.get('created',''))[:28])}</td></tr>"
                )
        parts.append(f"""<div class="card"><h2>{esc(a['name'])} · pool blocks</h2>
        <table><tr><th>Height</th><th>Status</th><th>Time</th></tr>
        {''.join(rows) or '<tr><td colspan="3" style="color:var(--muted)">No pool blocks yet — connect hashrate.</td></tr>'}
        </table></div>""")
    body = f"<h1>Blocks</h1><p class='sub'>Found by shared pools. Solo blocks → explorer.</p>{''.join(parts)}"
    return layout("Blocks", "Blocks", body)


def load_stratum_stats():
    try:
        with urllib.request.urlopen(f"{STRATUM_STATS}/api/", timeout=5) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)


def page_workers():
    parts = []
    st, err = load_stratum_stats()
    if err:
        parts.append(f'<div class="note">RX/YP stratum: offline ({esc(err)})</div>')
    else:
        pools = (st or {}).get("pools") or []
        workers = (st or {}).get("workers") or []
        prow = "".join(
            f"<tr><td>{esc(p.get('algo'))}</td><td>{esc(p.get('port'))}</td>"
            f"<td>{esc(p.get('active_connections'))}</td><td>{esc(p.get('accepts'))}</td>"
            f"<td>{esc(p.get('rejects'))}</td><td>{esc(p.get('blocks'))}</td></tr>"
            for p in pools
        )
        wrows = "".join(
            f"<tr><td class='mono'>{esc(w.get('name'))}</td><td>{esc(w.get('algo'))}</td>"
            f"<td>{esc(w.get('accepts'))}</td><td>{esc(w.get('rejects'))}</td>"
            f"<td>{esc(w.get('blocks'))}</td>"
            f"<td>{esc(int(time.time()-w['last_share']) if w.get('last_share') else '—')}s</td></tr>"
            for w in workers
        )
        pay = esc((st or {}).get("payout_address") or "—")
        parts.append(
            f"""<div class="card"><h2>CPU stratum (RandomX · YespowerEGA)</h2>
            <table><tr><th>Algo</th><th>Port</th><th>Active</th><th>Accepts</th><th>Rejects</th><th>Blocks</th></tr>
            {prow or '<tr><td colspan="6" style="color:var(--muted)">—</td></tr>'}</table>
            <p style="color:var(--muted);font-size:.85rem;margin-top:.5rem">Pool coinbase address: <span class="mono">{pay}</span></p>
            <h2 style="margin-top:1rem">Workers</h2>
            <table><tr><th>Worker / address</th><th>Algo</th><th>Accepts</th><th>Rejects</th><th>Blocks</th><th>Last share</th></tr>
            {wrows or '<tr><td colspan="6" style="color:var(--muted)">No workers yet — connect a miner.</td></tr>'}
            </table></div>"""
        )

    for a in ALGOS:
        if not a.get("mc"):
            continue
        data, e2 = api(f"/api/pools/{a['mc']}/miners")
        rows = ""
        if isinstance(data, list) and data:
            for m in data[:50]:
                name = m.get("miner") or m.get("address") or m.get("name") or json.dumps(m)[:40]
                rows += f"<tr><td class='mono'>{esc(name)}</td><td class='mono'>{esc(str(m)[:80])}</td></tr>"
        else:
            rows = f'<tr><td colspan="2" style="color:var(--muted)">No Miningcore workers yet ({esc(e2 or "empty")}).</td></tr>'
        parts.append(
            f"""<div class="card"><h2>{esc(a['name'])} · Miningcore workers</h2>
            <table><tr><th>Miner</th><th>Info</th></tr>{rows}</table></div>"""
        )

    body = f"""
<h1>Workers</h1>
<p class="sub">Who is connected and submitting shares.</p>
{''.join(parts)}
"""
    return layout("Workers", "Workers", body)


def page_payments():
    parts = []
    for a in ALGOS:
        if not a.get("mc"):
            parts.append(
                f"""<div class="card"><h2>{esc(a['name'])}</h2>
                <p style="color:var(--muted)">EGA stratum pays pool coinbase to the node wallet when blocks are found.
                Per-share accounting is tracked under Workers; mature funds sit in the pool address until operator pays out
                (or use solo to get full block to your address).</p></div>"""
            )
            continue
        data, err = api(f"/api/pools/{a['mc']}/payments")
        rows = ""
        if isinstance(data, list) and data:
            for p in data[:40]:
                rows += (
                    f"<tr><td class='mono'>{esc(p.get('address', p.get('created','')))}</td>"
                    f"<td>{esc(p.get('amount', p.get('amountFormatted','')))}</td>"
                    f"<td class='mono'>{esc(str(p.get('transactionConfirmationData', p.get('id','')))[:48])}</td></tr>"
                )
        else:
            rows = f'<tr><td colspan="3" style="color:var(--muted)">{esc(err or "No payments recorded yet.")}</td></tr>'
        parts.append(
            f"""<div class="card"><h2>{esc(a['name'])} · payments</h2>
            <table><tr><th>Address / time</th><th>Amount</th><th>Tx / id</th></tr>{rows}</table></div>"""
        )
    body = f"""
<h1>Payments</h1>
<p class="sub">Shared-pool payouts. Solo rewards go straight to your wallet on the explorer.</p>
<div class="note">Miningcore records payments when payment processing runs. Empty tables mean no automated payouts yet —
connect miners and find blocks, or solo-mine to your own address.</div>
{''.join(parts)}
"""
    return layout("Payments", "Payments", body)


def page_wallet(addr=""):
    addr = (addr or "").strip()
    form = f"""<form class="search" method="get" action="/wallet">
      <input name="address" value="{esc(addr)}" placeholder="Paste EGA address (E…)"/>
      <button type="submit">Lookup</button>
    </form>"""
    extra = ""
    if addr:
        bits = [
            f'<div class="note">Also open in explorer: '
            f'<a href="{esc(EXPLORER)}/address/{esc(urllib.parse.quote(addr))}" target="_blank">{esc(addr)}</a></div>'
        ]
        mc, _ = load_mc()
        for a in ALGOS:
            if not a["mc"]:
                bits.append(
                    f"<div class='card'><h3>{esc(a['name'])}</h3>"
                    f"<p style='color:var(--muted)'>Use explorer for solo rewards. Stratum :{a['port']} for shared.</p></div>"
                )
                continue
            data, err = api(f"/api/pools/{a['mc']}/miners/{urllib.parse.quote(addr)}")
            if err or not data:
                bits.append(
                    f"<div class='card'><h3>{esc(a['name'])}</h3>"
                    f"<p style='color:var(--muted)'>No shared-pool shares for this address yet.</p></div>"
                )
            else:
                bits.append(
                    f"<div class='card'><h3>{esc(a['name'])} · pool stats</h3>"
                    f"<pre>{esc(json.dumps(data, indent=2)[:1500])}</pre></div>"
                )
        extra = "".join(bits)
    body = f"""
<h1>Wallet lookup</h1>
<p class="sub">Check shared-pool activity for your address (like other pools’ “account” page).</p>
{form}
{extra or '<div class="note">Enter the same address you use as stratum username.</div>'}
<div class="card">
  <h2>Need a wallet?</h2>
  <p><a class="btn" href="{esc(WALLET_WEB)}">Open web wallet</a>
  <a class="btn btn2" style="margin-left:.4rem" href="https://github.com/Egalitarianism-EGA/ega/releases">Download node / Qt</a></p>
</div>
"""
    return layout("Wallet", "Wallet", body)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
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
            elif path == "/solo":
                body = page_solo()
            elif path == "/shared":
                body = page_shared()
            elif path == "/blocks":
                body = page_blocks()
            elif path == "/workers":
                body = page_workers()
            elif path == "/payments":
                body = page_payments()
            elif path == "/wallet":
                body = page_wallet((q.get("address") or [""])[0])
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
    print(f"EGA Pool site http://{HOST}:{PORT}/")
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()


if __name__ == "__main__":
    main()
