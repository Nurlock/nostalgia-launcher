"""qmllint gate for QML sources (skips when the binary is absent).

qmllint is a Qt binary, not a PyPI/uv package: the `pyside6` wheel does
not bundle it and no `pyside6-qmllint` package exists. Candidate
locations, first hit wins: `PATH`, then the distro Qt path
(`/usr/lib/qt6/bin/qmllint`, owned by `qt6-declarative` on Arch).
"""

import os
import re
import shutil
import subprocess

import pytest

QML_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "src",
    "nostalgia_launcher",
    "ui",
    "qml",
    "qml",
)

_CANDIDATES = ("qmllint", "/usr/lib/qt6/bin/qmllint")


def _pyside6_qml_dir() -> str | None:
    """QML modules bundled in the PySide6 wheel (portable Arch/Ubuntu)."""
    try:
        import PySide6

        cand = os.path.join(
            os.path.dirname(os.path.abspath(PySide6.__file__)),
            "Qt",
            "qml",
        )
        if os.path.isdir(os.path.join(cand, "QtQuick")):
            return cand
    except Exception:
        pass
    return None


def _import_paths() -> list[str]:
    """-I dirs for qmllint (PySide6 wheel first, distro Qt fallback)."""
    paths = []
    for cand in (
        _pyside6_qml_dir(),
        "/usr/lib/qt6/qml",  # Arch qt6-declarative + Ubuntu -dev-tools
        os.environ.get("QML_IMPORT_PATH", ""),
    ):
        if cand and os.path.isdir(cand) and cand not in paths:
            paths.append(cand)
    return paths


# Base-module import failure is environment noise (version-skewed or
# missing QtQuick on CI), not a QML bug — skip the file instead of
# failing (same spirit as the QMLLINT-is-None skip).
_BASE_IMPORT_MARKERS = (
    "Warnings occurred while importing base modules",
    "Failed to import QtQuick",
    "jsroot.qmltypes",
)


def _qmllint():
    for cand in _CANDIDATES:
        path = shutil.which(cand) if "/" not in cand else cand
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


QMLLINT = _qmllint()

# Known root-context globals set on QQmlEngine in python (ui/qml/app.py)
_CONTEXT_PROPERTIES = {
    "appTheme",
    "settingsModel",
    "wizard",
    "linuxModel",
    "updateState",
    "customModModel",
    "launcherState",
    "newsModel",
    "customAssetModel",
    "customAddonModel",
    "logModel",
    "addonsModel",
    "modsModel",
    "assetsModel",
    "browseModsModel",
    "browseAssetsModel",
    "browseAddonsModel",
}


def _qml_files():
    return sorted(f for f in os.listdir(QML_DIR) if f.endswith(".qml"))


def _lint(path: str) -> str:
    cmd = [QMLLINT]
    for imp in _import_paths():
        cmd += ["-I", imp]
    cmd.append(path)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return (proc.stdout or "") + (proc.stderr or "")


@pytest.mark.skipif(
    QMLLINT is None,
    reason="qmllint not found (PATH or /usr/lib/qt6/bin/qmllint "
    "from qt6-declarative) — install distro Qt to run the QML lint",
)
def test_qmllint_available():
    assert QMLLINT is not None


@pytest.mark.skipif(QMLLINT is None, reason="no qmllint binary")
@pytest.mark.parametrize("name", _qml_files())
def test_qml_file_lints_clean(name):
    file_path = os.path.join(QML_DIR, name)
    out = _lint(file_path)
    if any(mark in out for mark in _BASE_IMPORT_MARKERS):
        pytest.skip(
            f"qmllint cannot resolve QtQuick base modules here "
            f"({_qmllint()}); environment issue, not a QML bug"
        )
    with open(file_path, encoding="utf-8") as fp:
        source_lines = fp.readlines()

    problems = []
    for line in out.splitlines():
        trimmed = line.strip()
        if not trimmed.startswith("Warning:") and not trimmed.startswith(
            "Error:"
        ):
            continue
        if "[unqualified]" in line:
            # Only allow unqualified access if the target token is a registered
            # engine root-context property. Delegate/local identifiers must be
            # qualified.
            match = re.search(r":(\d+):(\d+):", line)
            if match:
                l_num = int(match.group(1)) - 1
                c_num = int(match.group(2)) - 1
                if l_num < len(source_lines):
                    ident_m = re.match(
                        r"[a-zA-Z_0-9]+", source_lines[l_num][c_num:]
                    )
                    ident = ident_m.group(0) if ident_m else ""
                    if ident in _CONTEXT_PROPERTIES:
                        continue
        problems.append(line)
    assert not problems, "\n".join(problems)
