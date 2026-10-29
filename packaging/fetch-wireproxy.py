"""Stage pinned wireproxy binaries under packaging/vendor/wireproxy/."""

import os
import sys

VERSION = "0.0.0"  # spike placeholder — pin real release tag during spike
BASE = "https://github.com/pufferffish/wireproxy/releases/download/" + VERSION
ARTIFACTS = (
    # (staged name, url, sha256) — fill during spike with real tag + hashes
    ("wireproxy-linux-amd64", BASE + "/wireproxy_linux_amd64.tar.gz", "TODO"),
    (
        "wireproxy-macos-universal",
        BASE + "/wireproxy_darwin_universal.tar.gz",
        "TODO",
    ),
    ("wireproxy.exe", BASE + "/wireproxy_windows_amd64.exe.tar.gz", "TODO"),
)
HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(HERE, "vendor", "wireproxy")


def main():
    os.makedirs(VENDOR_DIR, exist_ok=True)
    print("wireproxy fetch is a spike stub — pin VERSION + SHA256 before use")
    return 0


if __name__ == "__main__":
    sys.exit(main())
