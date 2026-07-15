#!/usr/bin/env python3
"""Serve web-wallet + JSON-RPC proxy to local egad (browser-friendly)."""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.environ.get("EGA_WEB_WALLET_HOST", "0.0.0.0")
PORT = int(os.environ.get("EGA_WEB_WALLET_PORT", "8090"))
RPC_URL = os.environ.get("EGA_RPC_URL", "http://127.0.0.1:20202")
RPC_USER = os.environ.get("EGA_RPC_USER", "")
RPC_PASS = os.environ.get("EGA_RPC_PASS", "")
ROOT = Path(__file__).resolve().parents[1]
WALLET_DIR = ROOT / "web-wallet"


def load_conf():
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
        if k == "rpcuser" and not os.environ.get("EGA_RPC_USER"):
            RPC_USER = v
        elif k == "rpcpassword" and not os.environ.get("EGA_RPC_PASS"):
            RPC_PASS = v
        elif k == "rpcport":
            RPC_URL = f"http://127.0.0.1:{v}"


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            f = WALLET_DIR / "index.html"
            self._send(200, f.read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/rpc":
            self._send(404, b"not found", "text/plain")
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        req = urllib.request.Request(RPC_URL, data=raw, method="POST")
        req.add_header("Content-Type", "application/json")
        if RPC_USER or RPC_PASS:
            token = base64.b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode()
            req.add_header("Authorization", f"Basic {token}")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
            self._send(200, body, "application/json")
        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else str(e).encode()
            self._send(e.code, body, "application/json")
        except Exception as e:
            self._send(502, json.dumps({"error": str(e)}).encode(), "application/json")


def main():
    load_conf()
    if not WALLET_DIR.is_dir():
        raise SystemExit(f"missing {WALLET_DIR}")
    print(f"Web wallet http://{HOST}:{PORT}/  (RPC proxy → {RPC_URL})")
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()


if __name__ == "__main__":
    main()
