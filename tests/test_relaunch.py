"""Unit tests for ui/relaunch.py (detached profile relaunch)."""

import sys

from PySide6.QtCore import QProcess

from nostalgia_launcher.ui import relaunch


def test_relaunch_with_profile_args(monkeypatch):
    captured = []
    monkeypatch.setattr(
        QProcess,
        "startDetached",
        staticmethod(lambda prog, args: captured.append((prog, args)) or True),
    )
    monkeypatch.setattr(
        sys, "argv", ["launcher", "--profile", "old", "--show-log"]
    )

    ok = relaunch.relaunch_with_profile("new_profile")
    assert ok is True
    assert len(captured) == 1
    prog, args = captured[0]
    assert "--profile" in args
    assert "new_profile" in args
    assert "old" not in args
    assert "--show-log" in args


def test_relaunch_with_empty_profile_strips_profile_arg(monkeypatch):
    captured = []
    monkeypatch.setattr(
        QProcess,
        "startDetached",
        staticmethod(lambda prog, args: captured.append((prog, args)) or True),
    )
    monkeypatch.setattr(
        sys, "argv", ["launcher", "--profile=old", "--show-log"]
    )

    ok = relaunch.relaunch_with_profile("")
    assert ok is True
    assert len(captured) == 1
    prog, args = captured[0]
    assert "--profile" not in args
    assert "old" not in args
    assert "--show-log" in args


def test_switch_profile_empty_name(monkeypatch):
    relaunch_calls = []
    monkeypatch.setattr(
        relaunch,
        "relaunch_with_profile",
        lambda name: relaunch_calls.append(name) or True,
    )
    quit_calls = []
    monkeypatch.setattr(
        relaunch.QCoreApplication,
        "quit",
        lambda: quit_calls.append(True),
    )

    ok = relaunch.switch_profile("")
    assert ok is True
    assert relaunch_calls == [""]
    assert quit_calls == [True]
