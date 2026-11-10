"""Unit tests for server JSON updater scenarios and switch dispatchers."""

from unittest.mock import MagicMock

from nostalgia_launcher.core.launcher import LauncherConfig
from nostalgia_launcher.services.update.scenarios import (
    DirectDownloadScenario,
    ManifestUpdateScenario,
    NoUpdateScenario,
    TorrentFileUpdateScenario,
    TorrentInitialScenario,
    TorrentKind,
    resolve_server_scenarios,
)
from nostalgia_launcher.services.update.workflow import (
    UpdateWorker,
    dispatch_initial_download,
    dispatch_update_process,
)
from nostalgia_launcher.state.events import (
    EventDispatcher,
    TorrentUpToDate,
    UpdateCompleted,
    UpdateFailed,
)


def test_resolve_scenarios_direct_download_only():
    cfg = LauncherConfig(
        server_name="Direct Server",
        download_fallback_url="https://example.com/client.zip",
        download_content_type="zip",
    )
    scenarios = resolve_server_scenarios(cfg)

    assert isinstance(scenarios.initial, DirectDownloadScenario)
    assert scenarios.initial.url == "https://example.com/client.zip"
    assert scenarios.initial.content_type == "zip"
    assert isinstance(scenarios.update, NoUpdateScenario)


def test_resolve_scenarios_torrent_file():
    cfg = LauncherConfig(
        server_name="Torrent Server",
        download_torrent_url="https://example.com/client.torrent",
        download_fallback_url="https://example.com/client.zip",
    )
    scenarios = resolve_server_scenarios(cfg)

    assert isinstance(scenarios.initial, TorrentInitialScenario)
    assert scenarios.initial.kind == TorrentKind.TORRENT_FILE
    assert scenarios.initial.locator == "https://example.com/client.torrent"
    assert scenarios.initial.fallback_url == "https://example.com/client.zip"

    assert isinstance(scenarios.update, TorrentFileUpdateScenario)
    assert scenarios.update.torrent_url == "https://example.com/client.torrent"


def test_resolve_scenarios_magnet_only_no_incremental():
    magnet = "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567"
    cfg = LauncherConfig(
        server_name="Magnet Server",
        download_torrent_magnet=magnet,
    )
    scenarios = resolve_server_scenarios(cfg)

    assert isinstance(scenarios.initial, TorrentInitialScenario)
    assert scenarios.initial.kind == TorrentKind.MAGNET
    assert scenarios.initial.locator == magnet

    # Magnet cannot carry incremental updates
    assert isinstance(scenarios.update, NoUpdateScenario)
    assert "Magnet" in scenarios.update.reason


def test_resolve_scenarios_manifest_update():
    manifest_doc = {
        "url": "https://example.com/manifest.json",
        "schema": {
            "files": "files",
            "version": "version",
            "base_url": "base",
            "download_url": "url",
            "entry": {"path": "p", "size": "s", "sha256": "h"},
        },
        "routes": [{"match": "*", "as": "asset"}],
    }
    cfg = LauncherConfig(
        server_name="Manifest Server",
        download_fallback_url="https://example.com/client.zip",
        download_manifest=manifest_doc,
    )
    scenarios = resolve_server_scenarios(cfg)

    assert isinstance(scenarios.initial, DirectDownloadScenario)
    assert isinstance(scenarios.update, ManifestUpdateScenario)
    assert scenarios.update.manifest_config == manifest_doc


def test_resolve_scenarios_none_config():
    scenarios = resolve_server_scenarios(None)
    assert scenarios.initial is None
    assert isinstance(scenarios.update, NoUpdateScenario)


def test_launcher_config_scenarios_property():
    cfg = LauncherConfig(
        server_name="Prop Server",
        download_torrent_url="https://example.com/client.torrent",
        download_fallback_url="https://example.com/fallback.zip",
    )
    scenarios = cfg.scenarios
    assert isinstance(scenarios.initial, TorrentInitialScenario)
    assert scenarios.initial.kind == TorrentKind.TORRENT_FILE
    assert isinstance(scenarios.update, TorrentFileUpdateScenario)


# ── Switch Dispatcher Tests ───────────────────────────────────────────────


def test_dispatch_initial_download_direct(tmp_path):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)
    worker._http_fallback_download = MagicMock(return_value=True)

    scenario = DirectDownloadScenario("https://example.com/client.zip")
    result = dispatch_initial_download(worker, scenario)

    assert result is True
    worker._http_fallback_download.assert_called_once_with(
        "https://example.com/client.zip"
    )


def test_dispatch_initial_download_torrent_file_success(tmp_path, monkeypatch):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)
    worker._recovery_download = MagicMock(return_value=True)
    monkeypatch.setattr(
        "nostalgia_launcher.services.update.workflow._torrent_available",
        lambda: True,
    )

    scenario = TorrentInitialScenario(
        kind=TorrentKind.TORRENT_FILE,
        locator="https://example.com/client.torrent",
    )
    result = dispatch_initial_download(worker, scenario)

    assert result is True
    worker._recovery_download.assert_called_once_with(None)


def test_dispatch_initial_download_torrent_fallback_on_failure(
    tmp_path, monkeypatch
):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)
    worker._recovery_download = MagicMock(return_value=False)
    worker._http_fallback_download = MagicMock(return_value=True)
    monkeypatch.setattr(
        "nostalgia_launcher.services.update.workflow._torrent_available",
        lambda: True,
    )

    scenario = TorrentInitialScenario(
        kind=TorrentKind.TORRENT_FILE,
        locator="https://example.com/client.torrent",
        fallback_url="https://example.com/fallback.zip",
    )
    result = dispatch_initial_download(worker, scenario)

    assert result is True
    worker._recovery_download.assert_called_once_with(None)
    worker._http_fallback_download.assert_called_once_with(
        "https://example.com/fallback.zip"
    )


def test_dispatch_initial_download_magnet_success(tmp_path, monkeypatch):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)
    worker._recovery_download = MagicMock(return_value=True)
    monkeypatch.setattr(
        "nostalgia_launcher.services.update.workflow._torrent_available",
        lambda: True,
    )

    scenario = TorrentInitialScenario(
        kind=TorrentKind.MAGNET,
        locator="magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567",
    )
    result = dispatch_initial_download(worker, scenario)

    assert result is True
    worker._recovery_download.assert_called_once_with(None)


def test_dispatch_initial_download_no_source(tmp_path):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)

    result = dispatch_initial_download(worker, None)

    assert result is False
    events = dispatcher.drain()
    assert any(
        isinstance(e, UpdateFailed) and "No download source" in e.message
        for e in events
    )


def test_dispatch_update_process_manifest_up_to_date(tmp_path):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)

    scenario = ManifestUpdateScenario({"url": "https://example.com/m.json"})
    result = dispatch_update_process(worker, scenario, wanted=set())

    assert result is True
    events = dispatcher.drain()
    assert any(isinstance(e, TorrentUpToDate) for e in events)


def test_dispatch_update_process_manifest_downloads_wanted(tmp_path):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)
    worker._manifest_overlay_download = MagicMock(return_value=True)

    scenario = ManifestUpdateScenario({"url": "https://example.com/m.json"})
    result = dispatch_update_process(
        worker, scenario, wanted={"manifest:Data/patch.mpq"}
    )

    assert result is True
    worker._manifest_overlay_download.assert_called_once_with(
        {"Data/patch.mpq"}
    )
    events = dispatcher.drain()
    assert any(isinstance(e, UpdateCompleted) for e in events)


def test_dispatch_update_process_torrent_file(tmp_path, monkeypatch):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)
    worker._recovery_download = MagicMock(return_value=True)
    monkeypatch.setattr(
        "nostalgia_launcher.services.update.workflow._torrent_available",
        lambda: True,
    )

    scenario = TorrentFileUpdateScenario(
        torrent_url="https://example.com/client.torrent"
    )
    result = dispatch_update_process(
        worker, scenario, wanted={"Data/common.mpq"}
    )

    assert result is True
    worker._recovery_download.assert_called_once_with({"Data/common.mpq"})


def test_dispatch_update_process_no_update(tmp_path):
    dispatcher = EventDispatcher()
    worker = UpdateWorker(str(tmp_path), dispatcher)

    scenario = NoUpdateScenario("Magnet links are immutable")
    result = dispatch_update_process(
        worker, scenario, wanted={"Data/patch.mpq"}
    )

    assert result is False
    events = dispatcher.drain()
    assert any(
        isinstance(e, UpdateFailed)
        and "Magnet links are immutable" in e.message
        for e in events
    )
