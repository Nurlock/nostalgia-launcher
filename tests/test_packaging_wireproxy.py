def test_fetch_script_has_pinned_artifacts():
    src = open("packaging/fetch-wireproxy.py").read()
    assert "ARTIFACTS" in src and "sha256" in src.lower()
    assert "wireproxy" in src.lower()


def test_specs_reference_wireproxy_bundle():
    for spec in (
        "NostalgiaLauncher.spec",
        "NostalgiaLauncher-linux.spec",
        "NostalgiaLauncher-macos.spec",
    ):
        assert "wireproxy" in open(spec).read().lower(), spec
