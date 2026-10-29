"""Opt-in userspace WARP tunnel via bundled wireproxy (no warp-cli daemon)."""

import base64
import contextlib
import datetime
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request

WARP_PEER_PUBLIC_KEY = "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo="
WARP_ENDPOINT = "engage.cloudflareclient.com:2408"


def _bundled_names() -> tuple:
    """Staged sidecar name for this platform (see fetch-wireproxy.py)."""
    if os.name == "nt":
        return ("wireproxy.exe",)
    if sys.platform == "darwin":
        return ("wireproxy-macos", "wireproxy")
    return ("wireproxy-linux", "wireproxy")


def _bundled_wireproxy() -> str:
    if not getattr(sys, "frozen", False):
        return ""
    meipass = getattr(sys, "_MEIPASS", "")
    exe_dir = os.path.dirname(sys.executable or "")
    for base in (meipass, exe_dir, os.path.join(exe_dir, "_internal")):
        if not base:
            continue
        for name in _bundled_names():
            c = os.path.join(base, name)
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c
    return ""


def find_wireproxy() -> str:
    bundled = _bundled_wireproxy()
    if bundled:
        return bundled
    return shutil.which("wireproxy") or ""


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def render_config(
    private_key: str, address_v4: str, socks_port: int, http_port: int
) -> str:
    return (
        "[Interface]\n"
        f"PrivateKey = {private_key}\n"
        f"Address = {address_v4}\n"
        "DNS = 1.1.1.1\nMTU = 1280\n\n"
        "[Peer]\n"
        f"PublicKey = {WARP_PEER_PUBLIC_KEY}\n"
        "AllowedIPs = 0.0.0.0/0, ::/0\n"
        f"Endpoint = {WARP_ENDPOINT}\n"
        "PersistentKeepalive = 25\n\n"
        "[Socks5]\n"
        f"BindAddress = 127.0.0.1:{socks_port}\n\n"
        "[http]\n"
        f"BindAddress = 127.0.0.1:{http_port}\n"
    )


def wait_for_port(port: int, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.15)
    return False


_WARP_API_VERSION = (
    "v0a5641"  # wgcf-compatible; bump when Cloudflare retires it
)
_WARP_REG_URL = f"https://api.cloudflareclient.com/{_WARP_API_VERSION}/reg"
_WARP_REG_HEADERS = {
    "User-Agent": "1.1.1.1/6.38.9-5641 (Android 16.0.0)",
    "CF-Client-Version": "a-6.38.9-5641",
    "Content-Type": "application/json; charset=UTF-8",
}

_P = 2**255 - 19


def _x25519(private_bytes: bytes) -> bytes:
    """RFC 7748 public key from a 32-byte scalar (ladder verified vs OpenSSL)."""
    x1 = 9
    x2, z2, x3, z3 = 1, 0, x1, 1
    swap = 0
    kb = bytearray(private_bytes)
    kb[0] &= 248
    kb[31] &= 127
    kb[31] |= 64
    scalar = int.from_bytes(bytes(kb), "little")
    for t in range(254, -1, -1):
        bit = (scalar >> t) & 1
        swap ^= bit
        if swap:
            x2, x3 = x3, x2
            z2, z3 = z3, z2
        swap = bit
        a = (x2 + z2) % _P
        aa = a * a % _P
        b = (x2 - z2) % _P
        bb = b * b % _P
        e = (aa - bb) % _P
        c = (x3 + z3) % _P
        d = (x3 - z3) % _P
        da = d * a % _P
        cb = c * b % _P
        x3 = pow(da + cb, 2, _P)
        z3 = x1 * pow(da - cb, 2, _P) % _P
        x2 = aa * bb % _P
        z2 = e * (aa + 121665 * e) % _P
    if swap:
        x2, x3 = x3, x2
        z2, z3 = z3, z2
    return ((x2 * pow(z2, _P - 2, _P)) % _P).to_bytes(32, "little")


def generate_keypair() -> tuple:
    """Fresh WireGuard keypair as (private_b64, public_b64); no I/O."""
    priv = bytearray(os.urandom(32))
    priv[0] &= 248
    priv[31] = (priv[31] & 127) | 64
    pub = _x25519(bytes(priv))
    enc = base64.b64encode
    return enc(bytes(priv)).decode(), enc(pub).decode()


def _cidr(addr: str) -> str:
    """Ensure host bits: the API returns a bare IP, wireproxy needs CIDR."""
    return addr if "/" in addr else f"{addr}/32"


def register_device(urlopen=None, timeout: float = 15.0) -> dict:
    """Anonymous WARP registration (same call `wgcf register` makes).

    No account, email, or user input — Cloudflare mints a random device
    identity for the generated pubkey. Returns the private key and the
    assigned address. Raises on network or shape errors so callers fall
    back to a direct launch.
    """

    from ..core.security_http import read_capped, secure_urlopen

    opener = urlopen or secure_urlopen
    private_b64, public_b64 = generate_keypair()
    now = datetime.datetime.now(datetime.UTC).isoformat()
    payload = json.dumps(
        {
            "key": public_b64,
            "install_id": "",
            "fcm_token": "",
            "tos": now,
            "model": "PC",
            "serial_number": "",
            "locale": "en_US",
            "os_version": "16.0.0",
            "key_type": "curve25519",
            "tunnel_type": "wireguard",
        }
    ).encode()
    req = urllib.request.Request(
        _WARP_REG_URL,
        data=payload,
        headers=dict(_WARP_REG_HEADERS),
        method="POST",
    )
    with opener(req, timeout=timeout) as r:
        data = json.loads(read_capped(r, 64 * 1024))
    if not isinstance(data, dict):
        raise RuntimeError("WARP registration returned a broken payload")
    addrs = (data.get("config") or {}).get("interface", {})
    addrs = (addrs or {}).get("addresses") or {}
    v4 = addrs.get("v4") or "172.16.0.2/32"
    return {"private_key": private_b64, "address_v4": _cidr(v4)}


def warp_key_from_env() -> str:
    return os.environ.get("NOSTALGIA_WARP_KEY", "")


def start_tunnel(private_key: str, address_v4: str = "172.16.0.2/32") -> dict:
    """Spawn wireproxy and return a handle; pair with stop_tunnel."""
    bin_path = find_wireproxy()
    if not bin_path:
        raise RuntimeError("wireproxy binary not found (bundled or PATH)")
    if os.name != "nt":
        try:
            mode = os.stat(bin_path).st_mode
            os.chmod(
                bin_path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )
        except OSError:
            pass
    socks_port = get_free_port()
    http_port = get_free_port()
    cfg = render_config(private_key, address_v4, socks_port, http_port)
    fd, cfg_path = tempfile.mkstemp(
        prefix="warp_tun_", suffix=".conf", text=True
    )
    with os.fdopen(fd, "w") as f:
        f.write(cfg)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen(
        [bin_path, "-c", cfg_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=flags,
    )
    if not wait_for_port(socks_port, timeout=12.0):
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        if os.path.exists(cfg_path):
            os.remove(cfg_path)
        raise RuntimeError("Bundled WARP tunnel failed to start")
    return {
        "proc": proc,
        "cfg_path": cfg_path,
        "proxies": {
            "ALL_PROXY": f"socks5h://127.0.0.1:{socks_port}",
            "HTTP_PROXY": f"http://127.0.0.1:{http_port}",
            "HTTPS_PROXY": f"http://127.0.0.1:{http_port}",
        },
    }


def stop_tunnel(handle: dict | None) -> None:
    """Terminate a tunnel from start_tunnel; None-safe."""
    if not handle:
        return
    proc = handle.get("proc")
    if proc is not None:
        try:
            proc.terminate()
        except Exception:
            pass
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
        except Exception:
            pass
    cfg_path = handle.get("cfg_path", "")
    if cfg_path and os.path.exists(cfg_path):
        try:
            os.remove(cfg_path)
        except OSError:
            pass


@contextlib.contextmanager
def embedded_tunnel(private_key: str, address_v4: str = "172.16.0.2/32"):
    handle = start_tunnel(private_key, address_v4)
    try:
        yield handle["proxies"]
    finally:
        stop_tunnel(handle)


def warp_enabled_from_env() -> bool:
    return bool(os.environ.get("NOSTALGIA_WARP")) and bool(
        os.environ.get("NOSTALGIA_WARP_KEY")
    )
