import os

from nostalgia_launcher.services import warp


def test_find_wireproxy_prefers_bundled(tmp_path, monkeypatch):
    fake = tmp_path / "wireproxy"
    fake.write_bytes(b"x")
    fake.chmod(0o755)
    monkeypatch.setattr(warp, "_bundled_wireproxy", lambda: str(fake))
    assert warp.find_wireproxy() == str(fake)


def test_find_wireproxy_empty_when_missing(monkeypatch):
    monkeypatch.setattr(warp, "_bundled_wireproxy", lambda: "")
    monkeypatch.setattr("shutil.which", lambda _: None)
    assert warp.find_wireproxy() == ""


def test_get_free_port_binds():
    import socket

    port = warp.get_free_port()
    assert 1024 <= port <= 65535
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))  # must not raise EADDRINUSE


def test_render_config_contains_keys():
    cfg = warp.render_config(
        private_key="PRIV=",
        address_v4="172.16.0.2/32",
        socks_port=18080,
        http_port=18081,
    )
    assert "PrivateKey = PRIV=" in cfg
    assert "BindAddress = 127.0.0.1:18080" in cfg
    assert "engage.cloudflareclient.com:2408" in cfg


def test_tunnel_sets_env_and_cleans_up(monkeypatch, tmp_path):
    fake_bin = tmp_path / "wireproxy"
    fake_bin.write_bytes(b"x")
    fake_bin.chmod(0o755)
    monkeypatch.setattr(warp, "find_wireproxy", lambda: str(fake_bin))
    started = {}

    class FakeProc:
        stderr = None

        def terminate(self):
            started["term"] = True

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(warp.subprocess, "Popen", lambda *a, **k: FakeProc())
    monkeypatch.setattr(warp, "wait_for_port", lambda port, timeout=12.0: True)
    with warp.embedded_tunnel("PRIV=") as proxies:
        assert proxies["ALL_PROXY"].startswith("socks5h://127.0.0.1:")
        assert proxies["HTTP_PROXY"].startswith("http://127.0.0.1:")
        assert "127.0.0.1" in proxies["ALL_PROXY"]
    assert started.get("term") is True


def test_tunnel_raises_when_port_never_opens(monkeypatch, tmp_path):
    import pytest

    fake_bin = tmp_path / "wireproxy"
    fake_bin.write_bytes(b"x")
    fake_bin.chmod(0o755)
    monkeypatch.setattr(warp, "find_wireproxy", lambda: str(fake_bin))

    class FakeProc:
        stderr = None

        def terminate(self):
            pass

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(warp.subprocess, "Popen", lambda *a, **k: FakeProc())
    monkeypatch.setattr(
        warp, "wait_for_port", lambda port, timeout=12.0: False
    )
    with pytest.raises(RuntimeError, match="failed to start"):
        with warp.embedded_tunnel("PRIV="):
            pass


def test_start_stop_tunnel_lifecycle(monkeypatch, tmp_path):
    fake_bin = tmp_path / "wireproxy"
    fake_bin.write_bytes(b"x")
    fake_bin.chmod(0o755)
    monkeypatch.setattr(warp, "find_wireproxy", lambda: str(fake_bin))
    seen = {}

    class FakeProc:
        def terminate(self):
            seen["term"] = True

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(warp.subprocess, "Popen", lambda *a, **k: FakeProc())
    monkeypatch.setattr(warp, "wait_for_port", lambda p, timeout=12.0: True)
    handle = warp.start_tunnel("PRIV=")
    assert handle["proxies"]["ALL_PROXY"].startswith("socks5h://127.0.0.1:")
    assert os.path.exists(handle["cfg_path"])
    warp.stop_tunnel(handle)
    assert seen.get("term") is True
    assert not os.path.exists(handle["cfg_path"])
    warp.stop_tunnel(None)


def test_warp_key_from_env(monkeypatch):
    monkeypatch.setenv("NOSTALGIA_WARP_KEY", "PRIV=")
    assert warp.warp_key_from_env() == "PRIV="


def test_generate_keypair_matches_openssl_vector():
    # Ground truth from `openssl genpkey -algorithm X25519` (independent impl).
    import base64

    priv = base64.b64decode("CCnNE0Nv8LDawOp68AN87uSeuCY81HyY7cKfLDr6gWM=")
    assert warp._x25519(priv) == base64.b64decode(
        "oQ3D8T24SK52HAqA4Fwe59TpIYIvO7Iv6oIZ5xgOGwM="
    )
    p1, q1 = warp.generate_keypair()
    assert len(base64.b64decode(p1)) == 32
    assert warp._x25519(base64.b64decode(p1)) == base64.b64decode(q1)


def _reg_payload(**overrides):
    import json

    body = {
        "id": "device-id",
        "config": {
            "interface": {"addresses": {"v4": "172.16.0.2", "v6": "::/0"}},
            "peers": [
                {
                    "endpoint": {"v4": "162.159.192.1", "ports": [2408]},
                    "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
                }
            ],
        },
    }
    body.update(overrides)
    return json.dumps(body).encode()


def test_register_device_parses_peers_shape():
    seen = {}

    class _Resp:
        def __init__(self):
            self._done = False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, size=-1):
            if self._done:
                return b""
            self._done = True
            return _reg_payload()

    def fake_open(req, timeout=15):
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        return _Resp()

    reg = warp.register_device(urlopen=fake_open)
    assert seen["url"].endswith("/reg")
    assert len(reg["private_key"]) == 44
    assert reg["address_v4"] == "172.16.0.2/32"
    assert reg["peer_endpoint"] == "162.159.192.1:2408"
    assert reg["device_id"] == "device-id"


def test_register_device_falls_back_to_legacy_peer_shape():
    import json

    class _Resp:
        def __init__(self):
            self._done = False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, size=-1):
            if self._done:
                return b""
            self._done = True
            return json.dumps(
                {
                    "id": "d",
                    "config": {
                        "interface": {"addresses": {"v4": "172.16.0.2/32"}},
                        "peer": {
                            "endpoint": {
                                "host": "engage.cloudflareclient.com:2408"
                            },
                            "public_key": "k=",
                        },
                    },
                }
            ).encode()

    reg = warp.register_device(urlopen=lambda req, timeout=15: _Resp())
    assert reg["peer_endpoint"] == "engage.cloudflareclient.com:2408"
    assert reg["address_v6"] == ""


def test_register_device_rejects_broken_payload():
    import pytest

    class _Resp:
        def __init__(self):
            self._done = False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, size=-1):
            if self._done:
                return b""
            self._done = True
            return b"[1, 2"

    with pytest.raises(ValueError):
        warp.register_device(urlopen=lambda req, timeout=15: _Resp())


def test_register_device_propagates_network_errors():
    import pytest

    def boom(req, timeout=15):
        raise RuntimeError("offline")

    with pytest.raises(RuntimeError, match="offline"):
        warp.register_device(urlopen=boom)
