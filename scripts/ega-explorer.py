#!/usr/bin/env python3
"""
Lightweight Egalitarianism block explorer — talks to local egad RPC.
No external deps. Default: http://127.0.0.1:8088
"""
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
    user = passwd = None
    port = None
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
        raise RuntimeError(f"RPC HTTP {e.code}: {body[:400]}") from e
    except Exception as e:
        raise RuntimeError(f"RPC error: {e}") from e
    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    return data["result"]


def esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def layout(title: str, body: str) -> bytes:
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(title)} — EGA Explorer</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; background: #fafafa; color: #1a1a1a; }}
  .wrap {{ max-width: 900px; margin: 0 auto; padding: 1rem 1.2rem 2.5rem; }}
  header {{ display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:.5rem;
    border-bottom:1px solid #ddd; padding-bottom:.75rem; margin-bottom:1rem; }}
  a {{ color: #0b6e4f; }}
  h1 {{ font-size: 1.35rem; margin: 0 0 .75rem; }}
  table {{ width:100%; border-collapse: collapse; background:#fff; border:1px solid #ddd; border-radius:8px; overflow:hidden; }}
  th, td {{ text-align:left; padding:.55rem .75rem; border-bottom:1px solid #eee; font-size:.92rem; vertical-align:top; word-break:break-all; }}
  th {{ width: 28%; color:#555; background:#f5f5f5; font-weight:600; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:.6rem; margin:1rem 0; }}
  .card {{ background:#fff; border:1px solid #ddd; border-radius:8px; padding:.75rem; }}
  .card .n {{ font-size:1.2rem; font-weight:700; }}
  .card .l {{ color:#666; font-size:.85rem; }}
  form {{ display:flex; gap:.4rem; flex-wrap:wrap; margin:1rem 0; }}
  input[type=text] {{ flex:1; min-width:180px; padding:.45rem .6rem; border:1px solid #ccc; border-radius:6px; }}
  button {{ padding:.45rem .8rem; border:0; border-radius:6px; background:#1a1a1a; color:#fff; font-weight:600; cursor:pointer; }}
  .err {{ background:#fee; border:1px solid #fbb; padding:.75rem; border-radius:8px; color:#800; }}
  .mono {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size:.85rem; }}
  footer {{ margin-top:2rem; color:#777; font-size:.85rem; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <strong><a href="/" style="color:inherit;text-decoration:none">EGA Explorer</a></strong>
  <span class="mono"><a href="/">Home</a></span>
</header>
{body}
<footer>Egalitarianism lightweight explorer · local RPC only</footer>
</div>
</body>
</html>"""
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
            return
        if path.startswith("/block/"):
            key = path[len("/block/") :]
            self.send_html(200, layout("Block", self._block(key)))
            return
        if path.startswith("/tx/"):
            txid = path[len("/tx/") :]
            self.send_html(200, layout("Transaction", self._tx(txid)))
            return
        if path == "/search":
            term = (q.get("q") or [""])[0].strip()
            self.send_html(200, layout("Search", self._search(term)))
            return
        self.send_html(404, layout("Not found", "<p>Not found.</p>"))

    def _home(self) -> str:
        info = rpc("getblockchaininfo")
        height = int(info.get("blocks", 0))
        rows = []
        start = max(0, height - 14)
        for h in range(height, start - 1, -1):
            try:
                bh = rpc("getblockhash", [h])
                b = rpc("getblock", [bh])
            except Exception:
                continue
            ntx = len(b.get("tx", []))
            rows.append(
                f'<tr><td><a href="/block/{h}">{h}</a></td>'
                f'<td class="mono"><a href="/block/{esc(bh)}">{esc(bh[:16])}…</a></td>'
                f'<td>{ntx}</td><td>{b.get("time","")}</td></tr>'
            )
        table = (
            "<table><tr><th>Height</th><th>Hash</th><th>Txs</th><th>Time</th></tr>"
            + "".join(rows)
            + "</table>"
        )
        return f"""
<h1>Chain overview</h1>
<div class="cards">
  <div class="card"><div class="n">{esc(height)}</div><div class="l">Height</div></div>
  <div class="card"><div class="n">{esc(info.get("headers",""))}</div><div class="l">Headers</div></div>
  <div class="card"><div class="n">{esc(info.get("difficulty",""))}</div><div class="l">Difficulty</div></div>
  <div class="card"><div class="n">{esc(info.get("chain",""))}</div><div class="l">Chain</div></div>
</div>
<form action="/search" method="get">
  <input type="text" name="q" placeholder="Height, block hash, or txid" />
  <button type="submit">Search</button>
</form>
<p class="mono">Best: {esc(info.get("bestblockhash",""))}</p>
<h2>Recent blocks</h2>
{table}
"""

    def _block(self, key: str) -> str:
        if re.fullmatch(r"\d+", key):
            bh = rpc("getblockhash", [int(key)])
        else:
            bh = key
        b = rpc("getblock", [bh])
        txs = b.get("tx", [])
        tx_links = "".join(
            f'<li class="mono"><a href="/tx/{esc(t)}">{esc(t)}</a></li>' for t in txs
        )
        fields = [
            ("Height", b.get("height")),
            ("Hash", b.get("hash")),
            ("Prev", b.get("previousblockhash")),
            ("Next", b.get("nextblockhash")),
            ("Time", b.get("time")),
            ("Nonce", b.get("nonce")),
            ("Bits", b.get("bits")),
            ("Difficulty", b.get("difficulty")),
            ("Merkle", b.get("merkleroot")),
            ("Size", b.get("size")),
            ("Version", b.get("version")),
            ("Algo", b.get("pow_algo") or b.get("algo") or "—"),
        ]
        rows = "".join(
            f"<tr><th>{esc(k)}</th><td class='mono'>{esc(v if v is not None else '')}</td></tr>"
            for k, v in fields
        )
        prev = b.get("previousblockhash")
        nxt = b.get("nextblockhash")
        nav = []
        if prev:
            nav.append(f'<a href="/block/{esc(prev)}">← prev</a>')
        if b.get("height") is not None:
            nav.append(f'height {b["height"]}')
        if nxt:
            nav.append(f'<a href="/block/{esc(nxt)}">next →</a>')
        return f"""
<h1>Block</h1>
<p>{' · '.join(nav)}</p>
<table>{rows}</table>
<h2>Transactions ({len(txs)})</h2>
<ul>{tx_links or '<li>none</li>'}</ul>
"""

    def _tx(self, txid: str) -> str:
        try:
            tx = rpc("getrawtransaction", [txid, True])
        except Exception as e:
            return f'<div class="err">Could not load tx (need txindex=1?): {esc(e)}</div>'
        vins = tx.get("vin", [])
        vouts = tx.get("vout", [])
        vin_html = "".join(
            f"<li class='mono'>{esc(v.get('txid','coinbase'))}"
            f"{'' if 'txid' not in v else ':'+str(v.get('vout',''))}</li>"
            for v in vins
        )
        vout_html = "".join(
            f"<li>{esc(o.get('value',''))} EGA → "
            f"<span class='mono'>{esc(','.join(o.get('scriptPubKey',{}).get('addresses') or [o.get('scriptPubKey',{}).get('address','')]))}</span></li>"
            for o in vouts
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
<h2>Inputs</h2><ul>{vin_html}</ul>
<h2>Outputs</h2><ul>{vout_html}</ul>
"""

    def _search(self, term: str) -> str:
        if not term:
            return "<p>Empty search.</p>"
        if re.fullmatch(r"\d+", term):
            return self._block(term)
        if re.fullmatch(r"[0-9a-fA-F]{64}", term):
            # try block first, then tx
            try:
                rpc("getblock", [term])
                return self._block(term)
            except Exception:
                return self._tx(term)
        return f'<div class="err">Unrecognized query: {esc(term)}</div>'


def main():
    load_rpc_from_conf()
    if not RPC_USER or not RPC_PASS:
        print("Set RPC credentials in ~/.ega/ega.conf or EGA_RPC_USER / EGA_RPC_PASS", file=sys.stderr)
        sys.exit(1)
    try:
        info = rpc("getblockchaininfo")
    except Exception as e:
        print(f"Cannot reach egad at {RPC_URL}: {e}", file=sys.stderr)
        print("Start the node: bash scripts/easy-start.sh", file=sys.stderr)
        sys.exit(1)
    print(f"Connected to chain={info.get('chain')} height={info.get('blocks')}")
    print(f"Explorer: http://{HOST}:{PORT}/")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
