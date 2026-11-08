"""Fetch the wireproxy sidecar binaries for the frozen builds.

Downloads pinned upstream artifacts, verifies their SHA-256, extracts the
single binary from each tarball, and stages them under
``packaging/vendor/wireproxy/`` for the PyInstaller specs to bundle:

* ``wireproxy-linux`` -- linux/amd64 build (AppImage onedir)
* ``wireproxy-macos`` -- darwin universal (fat arm64+x86_64) build (.app)
* ``wireproxy.exe`` -- windows/amd64 build (onefile)
* ``LICENSE`` -- upstream ISC license text (attribution)

Idempotent: a VERSION sidecar tracks what is staged; matching versions are
left untouched. Stdlib only, so it runs on stock GitHub runners.

Usage (from the repo root)::

    python packaging/fetch-wireproxy.py
"""

import hashlib
import os
import sys
import tarfile
import urllib.request

VERSION = "v1.1.3"
BASE_URL = "https://github.com/windtf/wireproxy/releases/download/" + VERSION
LICENSE_URL = (
    "https://raw.githubusercontent.com/windtf/wireproxy/master/LICENSE"
)
# (staged name, download URL, pinned SHA-256, tarball member).
ARCHIVES = (
    (
        "wireproxy-linux",
        BASE_URL + "/wireproxy_linux_amd64.tar.gz",
        "e88c1d090740373fc606c1bafd81d9a5eadc642cce5667616e20e9d7a444f51c",
        "wireproxy",
    ),
    (
        "wireproxy-macos",
        BASE_URL + "/wireproxy_darwin_all.tar.gz",
        "7d55581d0310afe6b882717e6e6d5abf86cad05b9f5de63d0bb5133ba9da0cee",
        "wireproxy",
    ),
    (
        "wireproxy.exe",
        BASE_URL + "/wireproxy_windows_amd64.tar.gz",
        "bce041ea9fe0f8a3351301dcbe29cdf6a523bb25cf9c62f17ebb5699a8051d0f",
        "wireproxy.exe",
    ),
)
# (staged name, download URL, pinned SHA-256).
TEXTS = (
    (
        "LICENSE",
        LICENSE_URL,
        "12e05cf70e2876d0cfd1c649e1c0032f82a370b365dcccd7d5a03feee17f2625",
    ),
)
HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(HERE, "vendor", "wireproxy")
VERSION_FILE = os.path.join(VENDOR_DIR, "VERSION")
UPSTREAM_URL = "https://github.com/windtf/wireproxy"


def _sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url, sha256):
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()
    except Exception as e:
        raise SystemExit(f"error: download failed: {url} ({e})") from e
    actual = hashlib.sha256(data).hexdigest()
    if actual != sha256:
        raise SystemExit(
            f"error: SHA-256 mismatch for {url}:\n"
            f"  expected {sha256}\n"
            f"  got      {actual}"
        )
    return data


def _stage_archive(name, url, sha256, member, dest):
    print("downloading " + url + " ...")
    data = _download(url, sha256)
    tmp = dest + ".tgz"
    with open(tmp, "wb") as f:
        f.write(data)
    with tarfile.open(tmp, "r:gz") as tar:
        info = tar.getmember(member)
        info.name = name
        tar.extract(info, path=VENDOR_DIR, filter="data")
    os.remove(tmp)
    if not name.endswith(".exe"):
        os.chmod(dest, 0o755)
    print(f"staged {dest} ({len(data)} bytes, sha256 ok)")


def _stage_text(name, url, sha256, dest):
    print("downloading " + url + " ...")
    with open(dest, "wb") as f:
        f.write(_download(url, sha256))
    print("staged " + dest + " (sha256 ok)")


def _write_readme():
    lines = [
        "# Bundled wireproxy sidecar",
        "",
        "Staged by `packaging/fetch-wireproxy.py` (not committed;",
        " see `.gitignore`).",
        "",
        f"Upstream: windtf/wireproxy {VERSION} ({UPSTREAM_URL}).",
        "Binaries: single-file userspace WireGuard-to-SOCKS5 builds,",
        " bundled for the opt-in WARP tunnel (no warp-cli daemon).",
        "",
    ]
    dest = os.path.join(VENDOR_DIR, "README.md")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote " + dest)


def main():
    os.makedirs(VENDOR_DIR, exist_ok=True)
    try:
        with open(VERSION_FILE, encoding="utf-8") as f:
            staged = f.read().strip()
    except OSError:
        staged = ""
    if staged == VERSION and all(
        os.path.isfile(os.path.join(VENDOR_DIR, n))
        for n, _u, _s, _m in ARCHIVES
    ):
        print("up to date: " + VENDOR_DIR)
        return 0
    for name, url, sha256, member in ARCHIVES:
        _stage_archive(
            name, url, sha256, member, os.path.join(VENDOR_DIR, name)
        )
    for name, url, sha256 in TEXTS:
        _stage_text(name, url, sha256, os.path.join(VENDOR_DIR, name))
    _write_readme()
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(VERSION + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
