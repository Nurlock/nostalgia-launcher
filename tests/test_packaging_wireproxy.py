def test_fetch_script_has_pinned_artifacts():
    src = open("packaging/fetch-wireproxy.py").read()
    assert "ARCHIVES" in src and "sha256" in src.lower()
    assert "wireproxy" in src.lower()
    assert "TODO" not in src  # no unpinned hashes or versions


def test_fetch_script_stages_per_platform_binary():
    src = open("packaging/fetch-wireproxy.py").read()
    assert "wireproxy-linux" in src
    assert "wireproxy-macos" in src
    assert "wireproxy.exe" in src
    assert "v1.1.3" in src


def test_specs_reference_wireproxy_bundle():
    expected = {
        "NostalgiaLauncher.spec": "wireproxy.exe",
        "NostalgiaLauncher-linux.spec": "wireproxy-linux",
        "NostalgiaLauncher-macos.spec": "wireproxy-macos",
    }
    for spec, binary in expected.items():
        assert binary in open(spec).read(), spec
