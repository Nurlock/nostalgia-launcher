"""Download scenarios resolution for the client update backends.

The server configuration JSON (`server.download`) is the source of truth.
"""

from __future__ import annotations

from ...core import launcher
from ...core.log_sink import debug_emit
from ..update.scenarios import (
    DownloadSource,
    ServerDownloadScenarios,
    resolve_server_scenarios,
)


def _download_source() -> ServerDownloadScenarios | None:
    """Resolve the active scenarios from launcher config (server.json)."""
    cfg = launcher.config()
    if cfg is None:
        return None
    debug_emit(
        f"[torrent] selected server {cfg.server_name} "
        f"(torrent={'yes' if cfg.download_torrent_url else 'no'}, "
        f"magnet={'yes' if cfg.download_torrent_magnet else 'no'})"
    )
    return resolve_server_scenarios(cfg)


__all__ = ["DownloadSource", "ServerDownloadScenarios", "_download_source"]
