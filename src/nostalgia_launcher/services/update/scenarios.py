"""Server download scenarios and JSON hook for client acquisition & updates.

The server configuration JSON (`server.download` in `LauncherConfig`) is the
sole source of truth. Scenarios define the exact execution path for initial
client acquisition and incremental updates without backward-compatibility shims.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.launcher import LauncherConfig


class TorrentKind(StrEnum):
    """The locator kind for BitTorrent acquisition."""

    MAGNET = "magnet"
    TORRENT_FILE = "torrent_file"


# ── 1. Initial Download Scenarios ──────────────────────────────────────────


@dataclass(frozen=True)
class DirectDownloadScenario:
    """Direct HTTP download of the full base client (archive or folder)."""

    url: str
    content_type: str = "folder"  # "folder" | "zip" | "rar"


@dataclass(frozen=True)
class TorrentInitialScenario:
    """BitTorrent download of the full base client via Magnet or .torrent file."""

    kind: TorrentKind
    locator: str  # magnet URI or https .torrent URL
    content_type: str = "folder"
    fallback_url: str | None = None  # optional direct download fallback


InitialDownloadScenario = (
    DirectDownloadScenario | TorrentInitialScenario | None
)


# ── 2. Update Process Scenarios ───────────────────────────────────────────


@dataclass(frozen=True)
class ManifestUpdateScenario:
    """Manifest-based incremental update (per-file HTTPS hash sync)."""

    manifest_config: dict


@dataclass(frozen=True)
class TorrentFileUpdateScenario:
    """Torrent-file-based incremental update (.torrent URL via BitTorrent)."""

    torrent_url: str


@dataclass(frozen=True)
class NoUpdateScenario:
    """No incremental update possible (e.g. magnet-only or updates disabled)."""

    reason: str


UpdateProcessScenario = (
    ManifestUpdateScenario | TorrentFileUpdateScenario | NoUpdateScenario
)


# ── Server JSON Hook ────────────────────────────────────────────────────


@dataclass(frozen=True)
class ServerDownloadScenarios:
    """The resolved acquisition and update scenarios for the active server."""

    initial: InitialDownloadScenario
    update: UpdateProcessScenario

    @property
    def torrent_locator(self) -> str | None:
        if isinstance(self.initial, TorrentInitialScenario):
            return self.initial.locator
        return (
            self.update.torrent_url
            if isinstance(self.update, TorrentFileUpdateScenario)
            else None
        )

    @property
    def torrent_url(self) -> str | None:
        if isinstance(self.update, TorrentFileUpdateScenario):
            return self.update.torrent_url
        if isinstance(self.initial, TorrentInitialScenario):
            return (
                self.initial.locator
                if self.initial.kind == TorrentKind.TORRENT_FILE
                else None
            )
        return None

    @property
    def torrent_magnet(self) -> str | None:
        if isinstance(self.initial, TorrentInitialScenario):
            return (
                self.initial.locator
                if self.initial.kind == TorrentKind.MAGNET
                else None
            )
        return None

    @property
    def fallback_url(self) -> str:
        if isinstance(self.initial, DirectDownloadScenario):
            return self.initial.url
        if isinstance(self.initial, TorrentInitialScenario):
            return self.initial.fallback_url or ""
        return ""


def resolve_server_scenarios(
    cfg: LauncherConfig | None,
) -> ServerDownloadScenarios:
    """Hook server JSON into updater scenarios.

    Inspects ``server.download`` on the launcher configuration and resolves:
    1. Initial download scenario:
       - Direct Download (HTTP fallback archive/folder)
       - Torrent (Magnet or Torrent file)
    2. Update process scenario:
       - Manifest based
       - Torrent file based
       - (or NoUpdateScenario when not supported / magnet-only / disabled)
    """
    if cfg is None:
        return ServerDownloadScenarios(
            initial=None,
            update=NoUpdateScenario("No launcher configuration"),
        )

    # ── 1. Initial Download Scenario ──
    initial: InitialDownloadScenario = None
    torrent_url = cfg.download_torrent_url
    magnet = cfg.download_torrent_magnet
    fallback = cfg.download_fallback_url or None
    content_type = cfg.download_content_type or "folder"

    if torrent_url:
        initial = TorrentInitialScenario(
            kind=TorrentKind.TORRENT_FILE,
            locator=torrent_url,
            content_type=content_type,
            fallback_url=fallback,
        )
    elif magnet:
        initial = TorrentInitialScenario(
            kind=TorrentKind.MAGNET,
            locator=magnet,
            content_type=content_type,
            fallback_url=fallback,
        )
    elif fallback:
        initial = DirectDownloadScenario(
            url=fallback,
            content_type=content_type,
        )

    # ── 2. Update Process Scenario ──
    # Manifest takes precedence when configured;
    # otherwise Torrent File is used if a .torrent URL is provided and update is allowed.
    from ..manifest import _manifest_block

    manifest_doc = (
        cfg.download_manifest if cfg is not None else None
    ) or _manifest_block()

    update: UpdateProcessScenario
    if manifest_doc:
        update = ManifestUpdateScenario(manifest_config=manifest_doc)
    elif torrent_url and cfg.torrent_update_allowed():
        update = TorrentFileUpdateScenario(torrent_url=torrent_url)
    elif magnet:
        update = NoUpdateScenario(
            "Magnet sources do not support incremental updates"
        )
    else:
        update = NoUpdateScenario("No incremental update source configured")

    return ServerDownloadScenarios(initial=initial, update=update)


def DownloadSource(
    torrent_url: str | None = None,
    fallback_url: str = "",
    torrent_magnet: str | None = None,
    *args,
    **kwargs,
) -> ServerDownloadScenarios:
    """Compatibility factory constructing scenarios directly."""
    initial: InitialDownloadScenario = None
    if torrent_url:
        initial = TorrentInitialScenario(
            kind=TorrentKind.TORRENT_FILE,
            locator=torrent_url,
            fallback_url=fallback_url or None,
        )
    elif torrent_magnet:
        initial = TorrentInitialScenario(
            kind=TorrentKind.MAGNET,
            locator=torrent_magnet,
            fallback_url=fallback_url or None,
        )
    elif fallback_url:
        initial = DirectDownloadScenario(url=fallback_url)

    from ..manifest import _manifest_block

    manifest_doc = _manifest_block()
    update: UpdateProcessScenario
    if manifest_doc:
        update = ManifestUpdateScenario(manifest_config=manifest_doc)
    elif torrent_url:
        update = TorrentFileUpdateScenario(torrent_url=torrent_url)
    elif torrent_magnet:
        update = NoUpdateScenario(
            "Magnet sources do not support incremental updates"
        )
    else:
        update = NoUpdateScenario("No incremental update source configured")

    return ServerDownloadScenarios(initial=initial, update=update)
