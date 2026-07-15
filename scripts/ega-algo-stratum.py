#!/usr/bin/env python3
"""
EGA shared stratum for RandomX + YespowerEGA (Bitcoin-family multi-algo).
Uses node GBT + ega-pow-hash for real share/block verify + submitblock.

Ports (default):
  RandomX     3333
  YespowerEGA 3335

Env:
  EGA_RPC_URL, EGA_RPC_USER, EGA_RPC_PASS (or ~/.ega/ega.conf)
  EGA_POW_HASH  path to ega-pow-hash binary
  EGA_STRATUM_RX_PORT  EGA_STRATUM_YP_PORT
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POW_HASH = os.environ.get("EGA_POW_HASH", str(ROOT / "src" / "ega-pow-hash"))
RPC_URL = os.environ.get("EGA_RPC_URL", "http://127.0.0.1:20202")
RPC_USER = os.environ.get("EGA_RPC_USER", "")
RPC_PASS = os.environ.get("EGA_RPC_PASS", "")
RX_PORT = int(os.environ.get("EGA_STRATUM_RX_PORT", "3333"))
YP_PORT = int(os.environ.get("EGA_STRATUM_YP_PORT", "3335"))
HOST = os.environ.get("EGA_STRATUM_HOST", "0.0.0.0")

# share difficulty: shares must be under network target * this factor (easier shares)
SHARE_DIFF_MULT = float(os.environ.get("EGA_SHARE_DIFF_MULT", "0.001"))


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
    if params is None:
        params = []
    payload = json.dumps({"jsonrpc": "1.0", "id": "stratum", "method": method, "params": params}).encode()
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


def hex_swap(h: str) -> str:
    b = bytes.fromhex(h)
    return b[::-1].hex()


def pow_hash(algo: str, header80: bytes) -> bytes:
    hx = header80.hex()
    out = subprocess.check_output([POW_HASH, algo, hx], timeout=30).decode().strip()
    # GetHex is display order (reversed from internal LE on some chains) — uint256 GetHex is big-endian hex
    return bytes.fromhex(out)


def target_from_bits(bits_hex: str) -> int:
    bits = int(bits_hex, 16)
    exp = bits >> 24
    mant = bits & 0xFFFFFF
    if exp <= 3:
        return mant >> (8 * (3 - exp))
    return mant << (8 * (exp - 3))


def hash_to_int(h: bytes) -> int:
    # ega-pow-hash prints uint256.GetHex() (big-endian numeric form)
    return int.from_bytes(h, "big")


class Job:
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
        # coinbase
        cb_val = tmpl["coinbasevalue"]
        self.coinbase_tx = self._make_coinbase(tmpl, cb_val)
        self.merkle_root = self._merkle_root(self.coinbase_tx, tmpl.get("transactions") or [])
        self.n1 = os.urandom(4).hex()  # extranonce1 per job template refresh actually per client

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
        script_pubkey = getattr(Job, "_payout_script", None)
        if not script_pubkey:
            addr = os.environ.get("EGA_POOL_PAYOUT") or rpc("getnewaddress")
            info = rpc("getaddressinfo", [addr])
            script_pubkey = bytes.fromhex(info["scriptPubKey"])
            Job._payout_script = script_pubkey
            Job._payout_addr = addr
            print(f"[pool] payout address {addr}")
        parts = [
            struct.pack("<I", 1),
            b"\x01",
            b"\x00" * 32,
            struct.pack("<I", 0xFFFFFFFF),
            bytes([len(script_sig)]) + script_sig,
            struct.pack("<I", 0xFFFFFFFF),
            b"\x01",
            struct.pack("<Q", int(value_sats)),
            bytes([len(script_pubkey)]) + script_pubkey,
            struct.pack("<I", 0),
        ]
        return b"".join(parts)

    def _merkle_root(self, coinbase: bytes, txs: list) -> bytes:
        hashes = [double_sha256(coinbase)]
        for tx in txs:
            raw = bytes.fromhex(tx["data"])
            hashes.append(double_sha256(raw))
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            nxt = []
            for i in range(0, len(hashes), 2):
                nxt.append(double_sha256(hashes[i] + hashes[i + 1]))
            hashes = nxt
        return hashes[0]

    def header(self, nonce: int, ntime: int | None = None, extranonce2: bytes = b"\x00" * 4) -> bytes:
        # rebuild coinbase with extranonce2 appended in script for uniqueness
        # For simplicity use fixed coinbase; nonce varies
        ver = struct.pack("<I", self.version)
        prev = bytes.fromhex(self.prevhash)[::-1]
        merkle = self.merkle_root  # already LE internal
        ntime_b = struct.pack("<I", ntime if ntime is not None else self.curtime)
        bits_b = bytes.fromhex(self.bits)[::-1] if len(self.bits) == 8 else struct.pack("<I", int(self.bits, 16))
        # bits in header is 4 bytes LE of the compact bits value
        bits_b = struct.pack("<I", int(self.bits, 16))
        nonce_b = struct.pack("<I", nonce & 0xFFFFFFFF)
        return ver + prev + merkle + ntime_b + bits_b + nonce_b

    def block_hex(self, header: bytes) -> str:
        tx_count = 1 + len(self.tmpl.get("transactions") or [])
        # varint
        if tx_count < 0xFD:
            vtx = bytes([tx_count])
        else:
            vtx = b"\xfd" + struct.pack("<H", tx_count)
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
        self.stats = {"accepts": 0, "rejects": 0, "blocks": 0, "connections": 0}

    def refresh_job(self):
        # EGA/DigiByte-style: template request + algo name
        try:
            tmpl = rpc("getblocktemplate", [{"rules": ["segwit"]}, self.algo])
        except Exception:
            tmpl = rpc("getblocktemplate", [{"rules": ["segwit"]}])
            # force version bits for algo if node ignored second arg
        if not isinstance(tmpl, dict):
            raise RuntimeError("bad template")
        self.job_counter += 1
        jid = f"{self.job_counter:08x}"
        with self.job_lock:
            self.job = Job(self.algo, tmpl, jid)
        return self.job

    def run(self):
        print(f"[stratum] {self.algo} listening on {HOST}:{self.port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, self.port))
        sock.listen(50)
        while True:
            c, addr = sock.accept()
            self.stats["connections"] += 1
            threading.Thread(target=self.handle_client, args=(c, addr), daemon=True).start()

    def handle_client(self, conn: socket.socket, addr):
        extranonce1 = os.urandom(4).hex()
        worker = "unknown"
        buf = b""
        try:
            conn.settimeout(600)
            # initial job
            try:
                job = self.refresh_job()
            except Exception as e:
                print(f"[{self.algo}] GBT fail: {e}")
                conn.close()
                return
            while True:
                data = conn.recv(4096)
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
                        # [[notifications], extranonce1, extranonce2_size]
                        self.send(conn, {"id": mid, "result": [[["mining.notify", "ega"]], extranonce1, 4], "error": None})
                        self.push_job(conn, job, force=True)
                    elif method == "mining.authorize":
                        worker = str(params[0]) if params else worker
                        self.send(conn, {"id": mid, "result": True, "error": None})
                        self.push_job(conn, job, force=True)
                    elif method == "mining.submit":
                        # worker, job_id, extranonce2, ntime, nonce
                        ok, detail = self.process_submit(params, extranonce1)
                        if ok:
                            self.stats["accepts"] += 1
                            self.send(conn, {"id": mid, "result": True, "error": None})
                            if detail == "block":
                                self.stats["blocks"] += 1
                                print(f"[{self.algo}] BLOCK from {worker}")
                                try:
                                    job = self.refresh_job()
                                    self.push_job(conn, job, force=True)
                                except Exception as e:
                                    print(f"[{self.algo}] refresh after block: {e}")
                        else:
                            self.stats["rejects"] += 1
                            self.send(conn, {"id": mid, "result": None, "error": [21, detail, None]})
                    elif method == "mining.extranonce.subscribe":
                        self.send(conn, {"id": mid, "result": True, "error": None})
                    else:
                        if mid is not None:
                            self.send(conn, {"id": mid, "result": None, "error": [20, f"unknown {method}", None]})
        except Exception as e:
            print(f"[{self.algo}] client {addr}: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def send(self, conn, obj):
        conn.sendall((json.dumps(obj) + "\n").encode())

    def push_job(self, conn, job: Job, force=False):
        # mining.notify params for bitcoin-style:
        # job_id, prevhash, coinb1, coinb2, merkle_branch[], version, nbits, ntime, clean
        prev = hex_swap(job.prevhash)
        # dummy coinbase split (we use fixed coinbase; miner nonce only)
        cb = job.coinbase_tx.hex()
        mid = len(cb) // 2
        coinb1, coinb2 = cb[:mid], cb[mid:]
        version = f"{job.version:08x}"
        nbits = job.bits
        ntime = f"{job.curtime:08x}"
        self.send(
            conn,
            {
                "id": None,
                "method": "mining.notify",
                "params": [job.job_id, prev, coinb1, coinb2, [], version, nbits, ntime, True],
            },
        )
        # set difficulty — share target relative
        # mining.set_difficulty: network is easy so use small number
        self.send(conn, {"id": None, "method": "mining.set_difficulty", "params": [0.01]})

    def process_submit(self, params, extranonce1: str):
        if len(params) < 5:
            return False, "bad params"
        job_id, en2, ntime_hex, nonce_hex = params[1], params[2], params[3], params[4]
        with self.job_lock:
            job = self.job
        if not job or job.job_id != job_id:
            # still try with current job
            if not job:
                return False, "no job"
        try:
            nonce = int(nonce_hex, 16)
            ntime = int(ntime_hex, 16)
        except Exception:
            return False, "bad nonce/ntime"
        header = job.header(nonce, ntime)
        try:
            h = pow_hash(self.algo, header)
        except Exception as e:
            return False, f"pow fail: {e}"
        hv = hash_to_int(h)
        if hv >= job.share_target and hv >= job.target:
            return False, "above target"
        # block?
        if hv < job.target:
            blk = job.block_hex(header)
            try:
                res = rpc("submitblock", [blk])
                if res is None or res == "":
                    return True, "block"
                # some nodes return null on success
                if res is None:
                    return True, "block"
                return True, f"block-submit:{res}"
            except Exception as e:
                # share still valid even if submit fails
                return True, f"share-block-err:{e}"
        return True, "share"


def job_refresher(servers: list[AlgoStratum]):
    while True:
        time.sleep(15)
        for s in servers:
            try:
                s.refresh_job()
            except Exception as e:
                print(f"[{s.algo}] refresh: {e}")


def main():
    load_conf()
    if not Path(POW_HASH).is_file():
        raise SystemExit(f"missing {POW_HASH} — build: make -C src ega-pow-hash")
    # init payout script
    try:
        rpc("getblockchaininfo")
    except Exception as e:
        raise SystemExit(f"node RPC failed: {e}")

    servers = [
        AlgoStratum("randomx", RX_PORT),
        AlgoStratum("yespower-ega", YP_PORT),
    ]
    for s in servers:
        try:
            s.refresh_job()
        except Exception as e:
            print(f"[{s.algo}] initial GBT: {e}")
        s.start()
    threading.Thread(target=job_refresher, args=(servers,), daemon=True).start()
    print(f"EGA shared stratum RandomX :{RX_PORT}  YespowerEGA :{YP_PORT}")
    print(f"pow-hash: {POW_HASH}")
    while True:
        time.sleep(60)
        for s in servers:
            print(f"[{s.algo}] stats {s.stats}")


if __name__ == "__main__":
    main()
