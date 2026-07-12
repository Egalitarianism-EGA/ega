#!/usr/bin/env python3
"""Egalitarianism block explorer — local UI over egad RPC (stdlib only)."""
from __future__ import annotations

import base64
import json
import os
import re
import sys
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
    user = passwd = port = None
    for line in conf.read_text(errors="replace").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "rpcuser":
            user = v
        elif k == "rpcpassword":
            passwd = v
        elif k == "rpcport":
            port = v
    if user:
        RPC_USER = user
    if passwd:
        RPC_PASS = passwd
    if port:
        RPC_URL = f"http://127.0.0.1:{port}"


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
        raise RuntimeError(f"RPC HTTP {e.code}: {body[:500]}") from e
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


CSS = """
:root { --bg:#0b1220; --card:#152038; --line:#243049; --text:#eef2f8; --muted:#9aa8c0; --accent:#2dd4bf; }
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family: system-ui, sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }
.wrap { max-width:960px; margin:0 auto; padding:1rem 1.2rem 2.5rem; }
header { display:flex; justify-content:space-between; align-items:center; gap:.75rem; flex-wrap:wrap;
  border-bottom:1px solid var(--line); padding:.85rem 0 1rem; margin-bottom:1.1rem; }
.brand { display:flex; align-items:center; gap:.55rem; color:var(--text); text-decoration:none; font-weight:700; }
.brand .dot { width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg,#2dd4bf,#0f766e); }
a { color:var(--accent); text-decoration:none; }
a:hover { color:#5eead4; }
h1 { font-size:1.35rem; margin:0 0 .85rem; letter-spacing:-.02em; }
h2 { font-size:1.05rem; margin:1.25rem 0 .55rem; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:.65rem; margin:1rem 0; }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:.8rem; }
.card .n { font-size:1.25rem; font-weight:750; }
.card .l { color:var(--muted); font-size:.82rem; margin-top:.15rem; }
table { width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line);
  border-radius:12px; overflow:hidden; font-size:.92rem; }
th,td { text-align:left; padding:.55rem .75rem; border-bottom:1px solid var(--line); vertical-align:top; word-break:break-all; }
th { width:26%; color:var(--muted); background:rgba(0,0,0,.18); font-weight:600; }
tr:last-child th, tr:last-child td { border-bottom:none; }
form { display:flex; gap:.45rem; flex-wrap:wrap; margin:1rem 0; }
input[type=text] { flex:1; min-width:180px; padding:.55rem .7rem; border-radius:8px; border:1px solid var(--line);
  background:#0a1220; color:var(--text); }
button { padding:.55rem .9rem; border:0; border-radius:8px; background:var(--accent); color:#042f2e; font-weight:700; cursor:pointer; }
.err { background:rgba(248,113,113,.1); border:1px solid rgba(248,113,113,.35); color:#fecaca;
  padding:.85rem 1rem; border-radius:10px; margin:.75rem 0; }
.note { background:rgba(45,212,191,.08); border:1px solid rgba(45,212,191,.25); color:#b7f5eb;
  padding:.85rem 1rem; border-radius:10px; margin:.75rem 0; font-size:.92rem; }
.mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size:.84rem; }
.muted { color:var(--muted); }
footer { margin-top:2rem; color:var(--muted); font-size:.85rem; }
ul { margin:.4rem 0 .8rem 1.1rem; color:var(--muted); }
li { margin:.25rem 0; }
"""


def layout(title: str, body: str) -> bytes:
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(title)} · EGA Explorer</title>
<style>{CSS}</style>
</head><body><div class="wrap">
<header>
  <a class="brand" href="/"><span class="dot"></span> EGA Explorer</a>
  <span class="muted mono"><a href="/">Home</a></span>
</header>
{body}
<footer>Egalitarianism block explorer · connected to local node</footer>
</div></body></html>"""
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
            self.send_html(200, layout("Home", self._home()))
        elif path.startswith("/block/"):
            self.send_html(200, layout("Block", self._block(path[len("/block/") :])))
        elif path.startswith("/tx/"):
            self.send_html(200, layout("Transaction", self._tx(path[len("/tx/") :])))
        elif path == "/search":
            self.send_html(200, layout("Search", self._search((q.get("q") or [""])[0].strip())))
        else:
            self.send_html(404, layout("Not found", "<p>Not found.</p>"))

    def _home(self) -> str:
        info = rpc("getblockchaininfo")
        height = int(info.get("blocks", 0))
        diffs = info.get("difficulties") or {}
        diff_s = ", ".join(f"{k}={v}" for k, v in list(diffs.items())[:3]) if diffs else info.get("difficulty", "")
        rows = []
        for h in range(height, max(-1, height - 19), -1):
            try:
                bh = rpc("getblockhash", [h])
                b = rpc("getblock", [bh])
            except Exception:
                continue
            ntx = len(b.get("tx", []))
            algo = b.get("pow_algo") or b.get("algo") or "—"
            rows.append(
                f'<tr><td><a href="/block/{h}">{h}</a></td>'
                f'<td class="mono"><a href="/block/{esc(bh)}">{esc(bh[:18])}…</a></td>'
                f"<td>{esc(algo)}</td><td>{ntx}</td><td>{b.get('time','')}</td></tr>"
            )
        table = (
            "<table><tr><th>Height</th><th>Hash</th><th>Algo</th><th>Txs</th><th>Time</th></tr>"
            + "".join(rows)
            + "</table>"
        )
        return f"""
<h1>Chain overview</h1>
<div class="cards">
  <div class="card"><div class="n">{esc(height)}</div><div class="l">Height</div></div>
  <div class="card"><div class="n">{esc(info.get("headers",""))}</div><div class="l">Headers</div></div>
  <div class="card"><div class="n" style="font-size:.95rem">{esc(info.get("chain",""))}</div><div class="l">Network</div></div>
  <div class="card"><div class="n" style="font-size:.72rem;word-break:break-all">{esc(diff_s or "—")}</div><div class="l">Difficulty</div></div>
</div>
<form action="/search" method="get">
  <input type="text" name="q" placeholder="Search height, block hash, or txid" />
  <button type="submit">Search</button>
</form>
<p class="mono muted">Best block: {esc(info.get("bestblockhash",""))}</p>
<h2>Recent blocks</h2>
{table}
"""

    def _block(self, key: str) -> str:
        if re.fullmatch(r"\d+", key):
            bh = rpc("getblockhash", [int(key)])
        else:
            bh = key
        b = rpc("getblock", [bh])
        height = b.get("height")
        txs = b.get("tx", [])
        tx_items = []
        for i, t in enumerate(txs):
            label = "coinbase (genesis)" if height == 0 and i == 0 else ("coinbase" if i == 0 else "tx")
            # genesis coinbase cannot be fetched via getrawtransaction
            if height == 0 and i == 0:
                tx_items.append(
                    f'<li class="mono">{esc(t)} <span class="muted">— {label}; not a normal spendable tx</span></li>'
                )
            else:
                tx_items.append(
                    f'<li class="mono"><a href="/tx/{esc(t)}">{esc(t)}</a> <span class="muted">({label})</span></li>'
                )
        fields = [
            ("Height", height),
            ("Hash", b.get("hash")),
            ("Previous", b.get("previousblockhash")),
            ("Next", b.get("nextblockhash")),
            ("Time", b.get("time")),
            ("Algo", b.get("pow_algo") or b.get("algo") or "—"),
            ("Difficulty", b.get("difficulty")),
            ("Nonce", b.get("nonce")),
            ("Bits", b.get("bits")),
            ("Merkle root", b.get("merkleroot")),
            ("Size", b.get("size")),
            ("Version", b.get("version")),
        ]
        rows = "".join(
            f"<tr><th>{esc(k)}</th><td class='mono'>{esc('' if v is None else v)}</td></tr>"
            for k, v in fields
        )
        nav = []
        if b.get("previousblockhash"):
            nav.append(f'<a href="/block/{esc(b["previousblockhash"])}">← previous</a>')
        if height is not None:
            nav.append(f"height {height}")
        if b.get("nextblockhash"):
            nav.append(f'<a href="/block/{esc(b["nextblockhash"])}">next →</a>')
        return f"""
<h1>Block {esc(height if height is not None else '')}</h1>
<p class="muted">{' · '.join(nav)}</p>
<table>{rows}</table>
<h2>Transactions ({len(txs)})</h2>
<ul>{''.join(tx_items) or '<li>none</li>'}</ul>
"""

    def _tx(self, txid: str) -> str:
        # Genesis coinbase special-case
        try:
            genesis = rpc("getblockhash", [0])
            gblock = rpc("getblock", [genesis])
            if gblock.get("tx") and gblock["tx"][0] == txid:
                return f"""
<h1>Genesis coinbase</h1>
<div class="note">
  The genesis block coinbase is not a normal transaction. Bitcoin-family nodes refuse
  <code>getrawtransaction</code> for it (RPC -5). It is not spendable and has no standard vin/vout view.
</div>
<table>
<tr><th>Txid</th><td class="mono">{esc(txid)}</td></tr>
<tr><th>Block</th><td class="mono"><a href="/block/0">Genesis (height 0)</a></td></tr>
<tr><th>Hash</th><td class="mono">{esc(genesis)}</td></tr>
</table>
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
            elif "No such mempool" in msg or "No such" in msg or "-5" in msg:
                hint = "<div class='note'>Enable <code>txindex=1</code> in <code>~/.ega/ega.conf</code> and restart the node (reindex if the chain already existed without it).</div>"
            return f'<div class="err">Could not load transaction: {esc(msg)}</div>{hint}'

        vins = tx.get("vin", [])
        vouts = tx.get("vout", [])
        vin_html = []
        for v in vins:
            if "coinbase" in v:
                vin_html.append(f"<li class='mono'>coinbase {esc(str(v.get('coinbase',''))[:32])}…</li>")
            else:
                vin_html.append(
                    f"<li class='mono'><a href='/tx/{esc(v.get('txid',''))}'>{esc(v.get('txid',''))}</a>:{v.get('vout','')}</li>"
                )
        vout_html = []
        for o in vouts:
            spk = o.get("scriptPubKey") or {}
            addrs = spk.get("addresses") or ([spk["address"]] if spk.get("address") else [])
            vout_html.append(
                f"<li>{esc(o.get('value',''))} EGA → <span class='mono'>{esc(', '.join(addrs) if addrs else spk.get('type',''))}</span></li>"
            )
        return f"""
<h1>Transaction</h1>
<table>
<tr><th>Txid</th><td class="mono">{esc(tx.get("txid", txid))}</td></tr>
<tr><th>Block</th><td class="mono"><a href="/block/{esc(tx.get('blockhash',''))}">{esc(tx.get('blockhash',''))}</a></td></tr>
<tr><th>Confirmations</th><td>{esc(tx.get('confirmations',''))}</td></tr>
<tr><th>Time</th><td>{esc(tx.get('time') or tx.get('blocktime') or '')}</td></tr>
<tr><th>Size</th><td>{esc(tx.get('size',''))}</td></tr>
</table>
<h2>Inputs</h2><ul>{''.join(vin_html)}</ul>
<h2>Outputs</h2><ul>{''.join(vout_html)}</ul>
"""

    def _search(self, term: str) -> str:
        if not term:
            return "<p class='muted'>Empty search.</p>"
        if re.fullmatch(r"\d+", term):
            return self._block(term)
        if re.fullmatch(r"[0-9a-fA-F]{64}", term):
            try:
                rpc("getblock", [term])
                return self._block(term)
            except Exception:
                return self._tx(term)
        return f'<div class="err">Unrecognized query: {esc(term)}</div>'


def main():
    load_rpc_from_conf()
    if not RPC_USER or not RPC_PASS:
        print("Set RPC in ~/.ega/ega.conf or EGA_RPC_USER / EGA_RPC_PASS", file=sys.stderr)
        sys.exit(1)
    try:
        info = rpc("getblockchaininfo")
    except Exception as e:
        print(f"Cannot reach egad at {RPC_URL}: {e}", file=sys.stderr)
        print("Start the node: bash scripts/easy-start.sh", file=sys.stderr)
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
