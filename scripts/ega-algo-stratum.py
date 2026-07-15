#!/usr/bin/env python3
"""
EGA shared stratum — RandomX :3333 + YespowerEGA :3335
Real PoW via ega-pow-hash; worker stats + HTTP API on :3337
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import struct
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POW_HASH = os.environ.get("EGA_POW_HASH", str(ROOT / "src" / "ega-pow-hash"))
RPC_URL = os.environ.get("EGA_RPC_URL", "http://127.0.0.1:20202")
RPC_USER = os.environ.get("EGA_RPC_USER", "")
RPC_PASS = os.environ.get("EGA_RPC_PASS", "")
RX_PORT = int(os.environ.get("EGA_STRATUM_RX_PORT", "3333"))
YP_PORT = int(os.environ.get("EGA_STRATUM_YP_PORT", "3335"))
STATS_PORT = int(os.environ.get("EGA_STRATUM_STATS_PORT", "3337"))
HOST = os.environ.get("EGA_STRATUM_HOST", "0.0.0.0")
SHARE_DIFF_MULT = float(os.environ.get("EGA_SHARE_DIFF_MULT", "0.001"))

# worker_key -> stats
WORKERS: dict[str, dict] = {}
WORKERS_LOCK = threading.Lock()
SERVERS: list = []


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


def rpc(method, params=None):
    payload = json.dumps({"jsonrpc": "1.0", "id": "s", "method": method, "params": params or []}).encode()
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


def double_sha256(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def pow_hash(algo: str, header80: bytes) -> bytes:
    out = subprocess.check_output([POW_HASH, algo, header80.hex()], timeout=30).decode().strip()
    return bytes.fromhex(out)


def target_from_bits(bits_hex: str) -> int:
    bits = int(bits_hex, 16)
    exp = bits >> 24
    mant = bits & 0xFFFFFF
    if exp <= 3:
        return mant >> (8 * (3 - exp))
    return mant << (8 * (exp - 3))


def hash_to_int(h: bytes) -> int:
    return int.from_bytes(h, "big")


def touch_worker(algo: str, name: str, **kw):
    key = f"{algo}:{name}"
    with WORKERS_LOCK:
        w = WORKERS.setdefault(
            key,
            {
                "algo": algo,
                "name": name,
                "accepts": 0,
                "rejects": 0,
                "blocks": 0,
                "connected": 0,
                "last_share": 0,
                "first_seen": time.time(),
            },
        )
        for k, v in kw.items():
            if k in ("accepts", "rejects", "blocks", "connected") and isinstance(v, int):
                w[k] = w.get(k, 0) + v
            else:
                w[k] = v
        return dict(w)


class Job:
    _payout_script = None
    _payout_addr = None

    def __init__(self, algo: str, tmpl: dict, job_id: str):
        self.algo = algo
        self.tmpl = tmpl
        self.job_id = job_id
        self.version = tmpl["version"]
        self.prevhash = tmpl["previousblockhash"]
        self.curtime = tmpl["curtime"]
        self.bits = tmpl["bits"]
        self.height = tmpl["height"]
        self.target = target_from_bits(tmpl["bits"])
        self.share_target = max(1, int(self.target / SHARE_DIFF_MULT)) if SHARE_DIFF_MULT > 0 else self.target
        self.coinbase_tx = self._make_coinbase(tmpl, tmpl["coinbasevalue"])
        self.merkle_root = self._merkle_root(self.coinbase_tx, tmpl.get("transactions") or [])

    def _make_coinbase(self, tmpl, value_sats: int) -> bytes:
        height = tmpl["height"]
        hb = []
        h = height
        while h > 0:
            hb.append(h & 0xFF)
            h >>= 8
        if not hb:
            hb = [0]
        height_bytes = bytes(hb)
        script_sig = bytes([len(height_bytes)]) + height_bytes + b"/EGA/"
        if not Job._payout_script:
            addr = os.environ.get("EGA_POOL_PAYOUT") or rpc("getnewaddress")
            info = rpc("getaddressinfo", [addr])
            Job._payout_script = bytes.fromhex(info["scriptPubKey"])
            Job._payout_addr = addr
            print(f"[pool] payout {addr}")
        spk = Job._payout_script
        return b"".join(
            [
                struct.pack("<I", 1),
                b"\x01",
                b"\x00" * 32,
                struct.pack("<I", 0xFFFFFFFF),
                bytes([len(script_sig)]) + script_sig,
                struct.pack("<I", 0xFFFFFFFF),
                b"\x01",
                struct.pack("<Q", int(value_sats)),
                bytes([len(spk)]) + spk,
                struct.pack("<I", 0),
            ]
        )

    def _merkle_root(self, coinbase: bytes, txs: list) -> bytes:
        hashes = [double_sha256(coinbase)]
        for tx in txs:
            hashes.append(double_sha256(bytes.fromhex(tx["data"])))
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            nxt = []
            for i in range(0, len(hashes), 2):
                nxt.append(double_sha256(hashes[i] + hashes[i + 1]))
            hashes = nxt
        return hashes[0]

    def header(self, nonce: int, ntime: int | None = None) -> bytes:
        ver = struct.pack("<I", self.version)
        prev = bytes.fromhex(self.prevhash)[::-1]
        merkle = self.merkle_root
        ntime_b = struct.pack("<I", ntime if ntime is not None else self.curtime)
        bits_b = struct.pack("<I", int(self.bits, 16))
        nonce_b = struct.pack("<I", nonce & 0xFFFFFFFF)
        return ver + prev + merkle + ntime_b + bits_b + nonce_b

    def block_hex(self, header: bytes) -> str:
        tx_count = 1 + len(self.tmpl.get("transactions") or [])
        vtx = bytes([tx_count]) if tx_count < 0xFD else b"\xfd" + struct.pack("<H", tx_count)
        body = header + vtx + self.coinbase_tx
        for tx in self.tmpl.get("transactions") or []:
            body += bytes.fromhex(tx["data"])
        return body.hex()


class AlgoStratum(threading.Thread):
    def __init__(self, algo: str, port: int):
        super().__init__(daemon=True)
        self.algo = algo
        self.port = port
        self.job: Job | None = None
        self.job_lock = threading.Lock()
        self.job_counter = 0
        self.stats = {"accepts": 0, "rejects": 0, "blocks": 0, "active": 0}

    def refresh_job(self):
        try:
            tmpl = rpc("getblocktemplate", [{"rules": ["segwit"]}, self.algo])
        except Exception:
            tmpl = rpc("getblocktemplate", [{"rules": ["segwit"]}])
        if not isinstance(tmpl, dict):
            raise RuntimeError("bad template")
        self.job_counter += 1
        jid = f"{self.job_counter:08x}"
        with self.job_lock:
            self.job = Job(self.algo, tmpl, jid)
        return self.job

    def run(self):
        print(f"[stratum] {self.algo} :{self.port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, self.port))
        sock.listen(100)
        while True:
            c, addr = sock.accept()
            threading.Thread(target=self.handle_client, args=(c, addr), daemon=True).start()

    def handle_client(self, conn: socket.socket, addr):
        extranonce1 = os.urandom(4).hex()
        worker = f"anon-{addr[0]}"
        self.stats["active"] += 1
        touch_worker(self.algo, worker, connected=1)
        buf = b""
        try:
            conn.settimeout(300)
            try:
                job = self.refresh_job()
            except Exception as e:
                print(f"[{self.algo}] GBT: {e}")
                return
            while True:
                data = conn.recv(8192)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line.decode())
                    except Exception:
                        continue
                    mid = msg.get("id")
                    method = msg.get("method")
                    params = msg.get("params") or []
                    if method == "mining.subscribe":
                        self.send(
                            conn,
                            {"id": mid, "result": [[["mining.notify", "ega"]], extranonce1, 4], "error": None},
                        )
                        self.push_job(conn, job)
                    elif method == "mining.authorize":
                        worker = str(params[0]) if params else worker
                        touch_worker(self.algo, worker, connected=0)  # name change; track new
                        touch_worker(self.algo, worker)
                        self.send(conn, {"id": mid, "result": True, "error": None})
                        self.push_job(conn, job)
                    elif method == "mining.submit":
                        ok, detail = self.process_submit(params, worker)
                        if ok:
                            self.stats["accepts"] += 1
                            touch_worker(self.algo, worker, accepts=1, last_share=time.time())
                            self.send(conn, {"id": mid, "result": True, "error": None})
                            if detail == "block":
                                self.stats["blocks"] += 1
                                touch_worker(self.algo, worker, blocks=1)
                                print(f"[{self.algo}] BLOCK {worker}")
                                try:
                                    job = self.refresh_job()
                                    self.push_job(conn, job)
                                except Exception as e:
                                    print(f"[{self.algo}] refresh: {e}")
                        else:
                            self.stats["rejects"] += 1
                            touch_worker(self.algo, worker, rejects=1, last_share=time.time())
                            self.send(conn, {"id": mid, "result": None, "error": [21, detail, None]})
                    elif method == "mining.extranonce.subscribe":
                        self.send(conn, {"id": mid, "result": True, "error": None})
                    elif mid is not None:
                        self.send(conn, {"id": mid, "result": None, "error": [20, f"unknown {method}", None]})
        except Exception as e:
            print(f"[{self.algo}] {addr}: {e}")
        finally:
            self.stats["active"] = max(0, self.stats["active"] - 1)
            try:
                conn.close()
            except Exception:
                pass

    def send(self, conn, obj):
        conn.sendall((json.dumps(obj) + "\n").encode())

    def push_job(self, conn, job: Job):
        prev = bytes.fromhex(job.prevhash)[::-1].hex()
        cb = job.coinbase_tx.hex()
        mid = len(cb) // 2
        self.send(
            conn,
            {
                "id": None,
                "method": "mining.notify",
                "params": [
                    job.job_id,
                    prev,
                    cb[:mid],
                    cb[mid:],
                    [],
                    f"{job.version:08x}",
                    job.bits,
                    f"{job.curtime:08x}",
                    True,
                ],
            },
        )
        self.send(conn, {"id": None, "method": "mining.set_difficulty", "params": [0.01]})

    def process_submit(self, params, worker: str):
        if len(params) < 5:
            return False, "bad params"
        job_id, _en2, ntime_hex, nonce_hex = params[1], params[2], params[3], params[4]
        with self.job_lock:
            job = self.job
        if not job:
            return False, "no job"
        try:
            nonce = int(nonce_hex, 16)
            ntime = int(ntime_hex, 16)
        except Exception:
            return False, "bad nonce"
        header = job.header(nonce, ntime)
        try:
            h = pow_hash(self.algo, header)
        except Exception as e:
            return False, f"pow:{e}"
        hv = hash_to_int(h)
        if hv >= job.share_target and hv >= job.target:
            return False, "above target"
        if hv < job.target:
            try:
                res = rpc("submitblock", [job.block_hex(header)])
                if res in (None, ""):
                    return True, "block"
                return True, f"share:{res}"
            except Exception as e:
                return True, f"share:{e}"
        return True, "share"


def stats_snapshot():
    with WORKERS_LOCK:
        workers = sorted(WORKERS.values(), key=lambda w: -w.get("accepts", 0))
    pools = []
    for s in SERVERS:
        pools.append(
            {
                "algo": s.algo,
                "port": s.port,
                "accepts": s.stats["accepts"],
                "rejects": s.stats["rejects"],
                "blocks": s.stats["blocks"],
                "active_connections": s.stats["active"],
            }
        )
    return {
        "pools": pools,
        "workers": workers[:100],
        "payout_address": Job._payout_addr,
        "ts": time.time(),
    }


class StatsHTTP(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/api/"):
            body = json.dumps(stats_snapshot()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def job_refresher():
    while True:
        time.sleep(20)
        for s in SERVERS:
            try:
                s.refresh_job()
            except Exception as e:
                print(f"[{s.algo}] refresh: {e}")


def main():
    global SERVERS
    load_conf()
    if not Path(POW_HASH).is_file():
        raise SystemExit(f"missing {POW_HASH}")
    rpc("getblockchaininfo")
    SERVERS = [AlgoStratum("randomx", RX_PORT), AlgoStratum("yespower-ega", YP_PORT)]
    for s in SERVERS:
        try:
            s.refresh_job()
        except Exception as e:
            print(f"[{s.algo}] GBT: {e}")
        s.start()
    threading.Thread(target=job_refresher, daemon=True).start()
    print(f"RandomX :{RX_PORT}  YespowerEGA :{YP_PORT}  stats :{STATS_PORT}/api/")
    ThreadingHTTPServer((HOST, STATS_PORT), StatsHTTP).serve_forever()


if __name__ == "__main__":
    main()
