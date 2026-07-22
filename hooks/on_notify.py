#!/usr/bin/env python3
"""Notification hook: speak the moment Claude needs you.

This is the "decision moment" channel. Claude Code sends a Notification
when it wants a permission/answer or hits an idle prompt. We speak the
message in plain words instead of leaving it silent on screen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vb import core  # noqa: E402


def main() -> int:
    data = core.read_hook_input()
    sid = data.get("session_id", "")
    # Strictly per-session: only speak notifications for a voiced session.
    if not core.is_voiced(sid) or core.mic_active():
        return 0
    msg = data.get("message", "") or data.get("body", "")
    if msg:
        core.speak(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
