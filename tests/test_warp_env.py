def test_warp_opt_in_off_by_default(monkeypatch):
    monkeypatch.delenv("NOSTALGIA_WARP", raising=False)
    monkeypatch.delenv("NOSTALGIA_WARP_KEY", raising=False)
    from nostalgia_launcher.services import warp

    assert warp.warp_enabled_from_env() is False


def test_warp_opt_in_requires_key(monkeypatch):
    from nostalgia_launcher.services import warp

    monkeypatch.setenv("NOSTALGIA_WARP", "1")
    monkeypatch.delenv("NOSTALGIA_WARP_KEY", raising=False)
    assert warp.warp_enabled_from_env() is False
    monkeypatch.setenv("NOSTALGIA_WARP_KEY", "PRIV=")
    assert warp.warp_enabled_from_env() is True
