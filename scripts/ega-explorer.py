#!/usr/bin/env python3
"""Egalitarianism block explorer — polished UI over local egad RPC."""
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


CSS = """
:root{
  --bg:#070b14;--panel:#0f1626;--panel2:#141e32;--line:#1e2a42;
  --text:#e8eef9;--muted:#8b9bb8;--accent:#2dd4bf;--accent2:#14b8a6;
  --gold:#e2b84a;--row:#0c1322;--rowh:#12203a;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
a{color:var(--accent);text-decoration:none}
a:hover{color:#5eead4}
.shell{max-width:1100px;margin:0 auto;padding:0 1.1rem 2.5rem}
.top{display:flex;align-items:center;justify-content:space-between;gap:1rem;
  padding:1rem 0;border-bottom:1px solid var(--line);position:sticky;top:0;
  background:rgba(7,11,20,.92);backdrop-filter:blur(10px);z-index:5}
.brand{display:flex;align-items:center;gap:.65rem;color:var(--text);font-weight:750;letter-spacing:-.02em}
.logo{width:34px;height:34px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#5eead4,#0f766e 55%,#042f2e);
  box-shadow:0 0 0 2px #1e2a42}
.nav{display:flex;gap:1rem;font-size:.9rem;color:var(--muted)}
.nav a{color:var(--muted)}.nav a:hover{color:var(--text)}
h1{font-size:1.45rem;letter-spacing:-.03em;margin:.2rem 0 .75rem;font-weight:800}
h2{font-size:1.05rem;margin:1.4rem 0 .7rem;font-weight:700}
.muted{color:var(--muted)}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.84rem;word-break:break-all}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin:1rem 0 1.25rem}
@media(max-width:800px){.stats{grid-template-columns:1fr 1fr}}
.stat{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:14px;padding:.95rem 1rem}
.stat .l{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700}
.stat .v{font-size:1.35rem;font-weight:800;margin-top:.25rem;letter-spacing:-.02em}
.stat .s{color:var(--muted);font-size:.8rem;margin-top:.2rem}
.search{display:flex;gap:.5rem;margin:1rem 0 1.25rem}
.search input{flex:1;background:var(--panel);border:1px solid var(--line);color:var(--text);
  border-radius:10px;padding:.7rem .9rem;font-size:.95rem}
.search input:focus{outline:1px solid var(--accent);border-color:var(--accent)}
.search button{background:var(--accent);color:#042f2e;border:0;border-radius:10px;
  padding:.7rem 1.1rem;font-weight:750;cursor:pointer}
.search button:hover{background:#5eead4}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-bottom:1rem}
.card-h{padding:.85rem 1rem;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:.5rem}
.card-h h2{margin:0;font-size:.95rem}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:.72rem .95rem;border-bottom:1px solid var(--line);vertical-align:middle}
th{color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;background:rgba(0,0,0,.2);font-weight:700}
tr:hover td{background:var(--rowh)}
tr:last-child td,tr:last-child th{border-bottom:0}
.kv th{width:28%;background:transparent;text-transform:none;letter-spacing:0;font-size:.88rem;color:var(--muted);font-weight:600}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:999px;font-size:.72rem;font-weight:750;
  background:rgba(45,212,191,.12);color:var(--accent)}
.badge-gold{background:rgba(226,184,74,.14);color:var(--gold)}
.err{background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.35);color:#fecaca;
  padding:1rem;border-radius:12px;margin:1rem 0}
.note{background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.22);color:#b7f5eb;
  padding:1rem;border-radius:12px;margin:1rem 0;font-size:.92rem}
.crumbs{color:var(--muted);font-size:.88rem;margin-bottom:.6rem}
.crumbs a{color:var(--muted)}.crumbs a:hover{color:var(--accent)}
.pager{display:flex;gap:.75rem;padding:.85rem 1rem;border-top:1px solid var(--line);font-size:.9rem}
footer{margin-top:1.5rem;color:var(--muted);font-size:.82rem;display:flex;justify-content:space-between;gap:.5rem;flex-wrap:wrap}
ul.tx{list-style:none;padding:.3rem 0}
ul.tx li{padding:.55rem .95rem;border-bottom:1px solid var(--line)}
ul.tx li:last-child{border-bottom:0}
"""


def layout(title: str, body: str) -> bytes:
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)} · EGA Explorer</title>
<style>{CSS}</style>
</head><body>
<div class="shell">
  <header class="top">
    <a class="brand" href="/"><span class="logo"></span> EGA Explorer</a>
    <nav class="nav">
      <a href="/">Blocks</a>
      <a href="https://egalitarianism-ega.github.io/ega-website/" target="_blank" rel="noopener">Website</a>
    </nav>
  </header>
  {body}
  <footer>
    <span>Egalitarianism block explorer</span>
    <span class="mono">RPC · local node</span>
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

    def do_GET(self):
        try:
            self._route()
        except Exception as e:
            self.send_html(500, layout("Error", f'<div class="err">{esc(e)}</div>'))

    def _route(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        q = parse_qs(u.query)
        if path == "/":
            self.send_html(200, layout("Blocks", self._home()))
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
  <input type="text" name="q" value="{esc(value)}" placeholder="Search by height, block hash, or transaction id" />
  <button type="submit">Search</button>
</form>"""

    def _home(self) -> str:
        info = rpc("getblockchaininfo")
        height = int(info.get("blocks", 0))
        diffs = info.get("difficulties") or {}
        diff_bits = " · ".join(f"{k.split('-')[0]} {float(v):.3g}" for k, v in list(diffs.items())[:3]) if diffs else "—"
        rows = []
        for h in range(height, max(-1, height - 24), -1):
            try:
                bh = rpc("getblockhash", [h])
                b = rpc("getblock", [bh])
            except Exception:
                continue
            algo = b.get("pow_algo") or b.get("algo") or "—"
            ntx = len(b.get("tx", []))
            rows.append(
                f"""<tr>
                <td><a href="/block/{h}"><strong>{h}</strong></a></td>
                <td class="mono"><a href="/block/{esc(bh)}">{esc(short(bh, 8))}</a></td>
                <td><span class="badge">{esc(algo)}</span></td>
                <td>{ntx}</td>
                <td class="muted">{esc(fmt_time(b.get('time')))}</td>
                </tr>"""
            )
        return f"""
<h1>Blocks</h1>
<p class="muted">Live view of the Egalitarianism chain from your node.</p>
<div class="stats">
  <div class="stat"><div class="l">Height</div><div class="v">{esc(height)}</div></div>
  <div class="stat"><div class="l">Network</div><div class="v" style="font-size:1.05rem">{esc(info.get('chain','—'))}</div>
    <div class="s">headers {esc(info.get('headers',''))}</div></div>
  <div class="stat"><div class="l">Difficulty</div><div class="v" style="font-size:.82rem;line-height:1.35">{esc(diff_bits)}</div></div>
  <div class="stat"><div class="l">Best block</div><div class="v mono" style="font-size:.78rem">{esc(short(info.get('bestblockhash',''), 6))}</div>
    <div class="s mono">{esc(info.get('bestblockhash',''))}</div></div>
</div>
{self._search_form()}
<div class="card">
  <div class="card-h"><h2>Recent blocks</h2><span class="muted">latest 25</span></div>
  <table>
    <tr><th>Height</th><th>Hash</th><th>Algo</th><th>Txs</th><th>Time</th></tr>
    {''.join(rows) or '<tr><td colspan="5" class="muted">No blocks yet</td></tr>'}
  </table>
</div>
"""

    def _block(self, key: str) -> str:
        if re.fullmatch(r"\d+", key):
            bh = rpc("getblockhash", [int(key)])
        else:
            bh = key
        b = rpc("getblock", [bh])
        height = b.get("height")
        txs = b.get("tx", [])
        algo = b.get("pow_algo") or b.get("algo") or "—"
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

        fields = [
            ("Hash", b.get("hash")),
            ("Previous", b.get("previousblockhash")),
            ("Next", b.get("nextblockhash")),
            ("Merkle root", b.get("merkleroot")),
            ("Time", fmt_time(b.get("time"))),
            ("Algo", algo),
            ("Difficulty", b.get("difficulty")),
            ("Nonce", b.get("nonce")),
            ("Bits", b.get("bits")),
            ("Size", f"{b.get('size', '—')} bytes"),
            ("Version", b.get("version")),
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
<div class="crumbs"><a href="/">Blocks</a> / Block {esc(height)}</div>
<h1>Block {esc(height)}</h1>
<p><span class="badge">{esc(algo)}</span> <span class="muted">{esc(fmt_time(b.get('time')))} · {len(txs)} transaction(s)</span></p>
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
<div class="crumbs"><a href="/">Blocks</a> / <a href="/block/0">Genesis</a> / Tx</div>
<h1>Genesis coinbase</h1>
<div class="note">
  The genesis coinbase is not a normal spendable transaction. Nodes reject
  <code>getrawtransaction</code> for it (same as Bitcoin).
</div>
<div class="card"><table class="kv">
<tr><th>Txid</th><td class="mono">{esc(txid)}</td></tr>
<tr><th>Block</th><td><a href="/block/0">Genesis · height 0</a></td></tr>
<tr><th>Block hash</th><td class="mono">{esc(genesis)}</td></tr>
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
        vin_html = []
        for v in vins:
            if "coinbase" in v:
                vin_html.append(f"<li class='mono'>coinbase <span class='muted'>{esc(str(v.get('coinbase',''))[:40])}…</span></li>")
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
<div class="crumbs"><a href="/">Blocks</a> / Transaction</div>
<h1>Transaction</h1>
{self._search_form(txid)}
<div class="card"><table class="kv">
<tr><th>Txid</th><td class="mono">{esc(tx.get("txid", txid))}</td></tr>
<tr><th>Block</th><td class="mono"><a href="/block/{esc(tx.get('blockhash',''))}">{esc(tx.get('blockhash',''))}</a></td></tr>
<tr><th>Confirmations</th><td>{esc(tx.get('confirmations',''))}</td></tr>
<tr><th>Time</th><td>{esc(fmt_time(tx.get('time') or tx.get('blocktime')))}</td></tr>
<tr><th>Size</th><td>{esc(tx.get('size',''))} bytes</td></tr>
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
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
