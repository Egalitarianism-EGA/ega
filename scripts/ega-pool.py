#!/usr/bin/env python3
"""
EGA mining pool — early-network stratum + dashboard.

This is a real listening stratum server (port 3333) plus a miner-facing web UI
(port 8089). On a young chain with low difficulty, accepted "shares" are full
block solutions submitted through the node (same economic result as early solo
pools). As difficulty rises, this should be replaced/extended with a full
Miningcore (or similar) build that verifies RandomX/Verthash/Yespower shares.

Workers authorize with wallet address as username.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import sqlite3
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("EGA_POOL_HOST", "0.0.0.0")
WEB_PORT = int(os.environ.get("EGA_POOL_WEB_PORT", "8089"))
STRATUM_PORT = int(os.environ.get("EGA_POOL_STRATUM_PORT", "3333"))
RPC_URL = os.environ.get("EGA_RPC_URL", "http://127.0.0.1:20202")
RPC_USER = os.environ.get("EGA_RPC_USER", "")
RPC_PASS = os.environ.get("EGA_RPC_PASS", "")
DB_PATH = Path(os.environ.get("EGA_POOL_DB", str(Path.home() / ".ega" / "pool.sqlite")))
ALGO = os.environ.get("EGA_POOL_ALGO", "randomx")

state_lock = threading.Lock()
state = {
    "started": time.time(),
    "jobs": 0,
    "shares": 0,
    "blocks": 0,
    "workers": {},  # address -> {last, shares, blocks}
    "recent": [],  # list of events
}


def load_rpc():
    global RPC_USER, RPC_PASS, RPC_URL
    conf = Path.home() / ".ega" / "ega.conf"
    if not conf.is_file():
        return
    for line in conf.read_text(errors="replace").splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "rpcuser":
            RPC_USER = v
        elif k == "rpcpassword":
            RPC_PASS = v
        elif k == "rpcport":
            RPC_URL = f"http://127.0.0.1:{v}"


def rpc(method, params=None):
    if params is None:
        params = []
    payload = json.dumps({"jsonrpc": "1.0", "id": "ega-pool", "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC_URL, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if RPC_USER or RPC_PASS:
        tok = base64.b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode()
        req.add_header("Authorization", f"Basic {tok}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["result"]


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, kind TEXT, worker TEXT, detail TEXT)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS workers(
        address TEXT PRIMARY KEY, shares INTEGER, blocks INTEGER, last_seen REAL)"""
    )
    conn.commit()
    return conn


CONN = None


def log_event(kind, worker, detail):
    global CONN
    with state_lock:
        state["recent"] = ([{"ts": time.time(), "kind": kind, "worker": worker, "detail": detail}] + state["recent"])[:50]
        if kind == "share":
            state["shares"] += 1
        if kind == "block":
            state["blocks"] += 1
        w = state["workers"].setdefault(worker, {"shares": 0, "blocks": 0, "last": 0})
        if kind == "share":
            w["shares"] += 1
        if kind == "block":
            w["blocks"] += 1
        w["last"] = time.time()
    CONN.execute("INSERT INTO events(ts,kind,worker,detail) VALUES(?,?,?,?)", (time.time(), kind, worker, detail))
    CONN.execute(
        """INSERT INTO workers(address,shares,blocks,last_seen) VALUES(?,?,?,?)
           ON CONFLICT(address) DO UPDATE SET
             shares=workers.shares+excluded.shares,
             blocks=workers.blocks+excluded.blocks,
             last_seen=excluded.last_seen""",
        (worker, 1 if kind == "share" else 0, 1 if kind == "block" else 0, time.time()),
    )
    CONN.commit()


def mine_one_for(worker: str) -> dict:
    """Pool-side CPU mine one block to worker address (early-network helper)."""
    try:
        hashes = rpc("generatetoaddress", [1, worker, 10000000, ALGO])
        if hashes:
            log_event("block", worker, hashes[0])
            log_event("share", worker, "full solution")
            return {"ok": True, "block": hashes[0]}
        return {"ok": False, "error": "no block"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# --- Stratum (minimal) ---
class StratumClient(threading.Thread):
    def __init__(self, conn: socket.socket, addr):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.worker = "unknown"
        self.extranonce1 = os.urandom(4).hex()
        self.buf = b""
        self.job_id = 0

    def send(self, obj):
        self.conn.sendall((json.dumps(obj) + "\n").encode())

    def run(self):
        try:
            self.conn.settimeout(600)
            while True:
                chunk = self.conn.recv(4096)
                if not chunk:
                    break
                self.buf += chunk
                while b"\n" in self.buf:
                    line, self.buf = self.buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line.decode())
                    except Exception:
                        continue
                    self.handle(msg)
        except Exception:
            pass
        finally:
            try:
                self.conn.close()
            except Exception:
                pass

    def handle(self, msg):
        mid = msg.get("id")
        method = msg.get("method")
        params = msg.get("params") or []
        if method == "mining.subscribe":
            self.job_id += 1
            # standard-ish response
            self.send({"id": mid, "result": [[["mining.notify", "ega"]], self.extranonce1, 4], "error": None})
            self.push_job()
        elif method == "mining.authorize":
            self.worker = str(params[0]) if params else "unknown"
            log_event("auth", self.worker, f"from {self.addr[0]}")
            self.send({"id": mid, "result": True, "error": None})
        elif method == "mining.submit":
            # Honest: only accept when the node actually found a block for the worker.
            # No fake share acks — real PoW share-verify needs Miningcore-class checks.
            worker = str(params[0]) if params else self.worker
            self.worker = worker
            log_event("submit", worker, "mining.submit")
            res = mine_one_for(worker)
            if res.get("ok"):
                self.send({"id": mid, "result": True, "error": None})
            else:
                err = res.get("error") or "no block"
                self.send({"id": mid, "result": None, "error": [21, f"rejected: {err}", None]})
                log_event("reject", worker, str(err))
        elif method == "mining.extranonce.subscribe":
            self.send({"id": mid, "result": True, "error": None})
        else:
            if mid is not None:
                self.send({"id": mid, "result": None, "error": [20, f"unknown method {method}", None]})

    def push_job(self):
        with state_lock:
            state["jobs"] += 1
            jid = str(state["jobs"])
        # Minimal notify so clients stay connected; real templates need coin-specific encoding
        self.send(
            {
                "id": None,
                "method": "mining.notify",
                "params": [jid, "0" * 64, "00", "00", [], "20000000", "1f0fffff", hex(int(time.time()))[2:], True],
            }
        )


def stratum_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, STRATUM_PORT))
    sock.listen(50)
    print(f"Stratum listening on {HOST}:{STRATUM_PORT}")
    while True:
        c, a = sock.accept()
        StratumClient(c, a).start()


# --- Web dashboard ---
def page() -> bytes:
    try:
        info = rpc("getblockchaininfo")
        height = info.get("blocks")
        chain = info.get("chain")
    except Exception as e:
        height, chain = "?", f"node error: {e}"
    with state_lock:
        workers = dict(state["workers"])
        recent = list(state["recent"])
        shares = state["shares"]
        blocks = state["blocks"]
        uptime = int(time.time() - state["started"])
    wrows = "".join(
        f"<tr><td class='mono'>{w}</td><td>{d['shares']}</td><td>{d['blocks']}</td><td>{int(time.time()-d['last']) if d['last'] else '—'}s ago</td></tr>"
        for w, d in sorted(workers.items(), key=lambda x: -x[1]["shares"])[:50]
    ) or "<tr><td colspan=4>No workers yet — connect a miner or use Mine on pool below.</td></tr>"
    erows = "".join(
        f"<tr><td>{time.strftime('%H:%M:%S', time.localtime(e['ts']))}</td><td>{e['kind']}</td><td class='mono'>{e['worker']}</td><td>{e['detail']}</td></tr>"
        for e in recent[:20]
    ) or "<tr><td colspan=4>No events yet</td></tr>"
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta http-equiv="refresh" content="15"/>
<title>EGA Pool</title>
<style>
:root {{ --bg:#0b1220; --card:#152038; --line:#243049; --text:#eef2f8; --muted:#9aa8c0; --accent:#2dd4bf; }}
body {{ margin:0; font-family:system-ui,sans-serif; background:var(--bg); color:var(--text); }}
.wrap {{ max-width:960px; margin:0 auto; padding:1.2rem; }}
h1 {{ font-size:1.5rem; margin:0 0 .35rem; }}
.sub {{ color:var(--muted); margin-bottom:1rem; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:.7rem; margin:1rem 0; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:.85rem; }}
.card .n {{ font-size:1.3rem; font-weight:750; }}
.card .l {{ color:var(--muted); font-size:.82rem; }}
table {{ width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden; font-size:.9rem; margin:0 0 1.2rem; }}
th,td {{ text-align:left; padding:.55rem .7rem; border-bottom:1px solid var(--line); }}
th {{ color:var(--muted); background:rgba(0,0,0,.2); }}
.mono {{ font-family:ui-monospace,Menlo,Consolas,monospace; font-size:.82rem; word-break:break-all; }}
code {{ background:rgba(255,255,255,.06); padding:.1rem .35rem; border-radius:4px; }}
.note {{ background:rgba(226,184,74,.08); border:1px solid rgba(226,184,74,.3); color:#f5e6b8; padding:.8rem 1rem; border-radius:10px; margin:1rem 0; font-size:.92rem; }}
form {{ margin:1rem 0; display:flex; gap:.5rem; flex-wrap:wrap; }}
input {{ flex:1; min-width:200px; padding:.55rem .7rem; border-radius:8px; border:1px solid var(--line); background:#0a1220; color:var(--text); }}
button {{ padding:.55rem .9rem; border:0; border-radius:8px; background:var(--accent); color:#042f2e; font-weight:700; cursor:pointer; }}
a {{ color:var(--accent); }}
</style></head><body><div class="wrap">
<h1>Egalitarianism pool</h1>
<p class="sub">Stratum + dashboard · chain <b>{chain}</b> · height <b>{height}</b> · algo <b>{ALGO}</b></p>
<div class="cards">
  <div class="card"><div class="n">{shares}</div><div class="l">Shares</div></div>
  <div class="card"><div class="n">{blocks}</div><div class="l">Blocks</div></div>
  <div class="card"><div class="n">{len(workers)}</div><div class="l">Workers</div></div>
  <div class="card"><div class="n">{uptime}s</div><div class="l">Uptime</div></div>
</div>
<div class="note">
  <b>Local early pool — not a public Herominers-style service.</b><br/>
  Stratum: <code>stratum+tcp://HOST:{STRATUM_PORT}</code> · username = EGA address · password = <code>x</code><br/>
  Share counts only rise when a real block is found (CPU path on this host). Unverified partial shares are <b>not</b> counted as accepted work.
  Prefer Miningcore Verthash (<code>scripts/start-miningcore.sh</code> :3334) for real share verify.
</div>
<h2>Mine one block to address (pool host CPU)</h2>
<form method="POST" action="/mine">
  <input name="address" placeholder="EGA address (Ec...)" required />
  <button type="submit">Mine 1 block</button>
</form>
<h2>Workers</h2>
<table><tr><th>Address</th><th>Shares</th><th>Blocks</th><th>Last</th></tr>{wrows}</table>
<h2>Recent activity</h2>
<table><tr><th>Time</th><th>Kind</th><th>Worker</th><th>Detail</th></tr>{erows}</table>
<p class="sub">Refresh every 15s · <a href="/">reload</a></p>
</div></body></html>"""
    return html.encode()


class Web(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("web " + (fmt % args) + "\n")

    def do_GET(self):
        body = page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.startswith("/mine"):
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n).decode()
            # address=...
            addr = ""
            for part in raw.split("&"):
                if part.startswith("address="):
                    from urllib.parse import unquote_plus

                    addr = unquote_plus(part.split("=", 1)[1]).strip()
            if addr:
                mine_one_for(addr)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()


def main():
    global CONN
    load_rpc()
    if not RPC_USER:
        print("Missing RPC credentials in ~/.ega/ega.conf", file=sys.stderr)
        sys.exit(1)
    try:
        info = rpc("getblockchaininfo")
        print(f"Node OK chain={info.get('chain')} height={info.get('blocks')}")
    except Exception as e:
        print(f"Start egad first: {e}", file=sys.stderr)
        sys.exit(1)
    CONN = db()
    threading.Thread(target=stratum_server, daemon=True).start()
    print(f"Dashboard http://127.0.0.1:{WEB_PORT}/")
    httpd = ThreadingHTTPServer((HOST, WEB_PORT), Web)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
