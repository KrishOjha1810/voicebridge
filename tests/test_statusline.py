"""The status-line text: rotating tips, per-state hints, update alert.

Run: python3 tests/test_statusline.py   (no pytest needed)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vb import core  # noqa: E402


def test_every_phase_renders_non_empty():
    for ph in ("listening", "hearing", "thinking", "speaking", "wake",
               "speakonly", "away", "off", "bogus"):
        out = core.render_statusline({"phase": ph}, n=0)
        assert out.startswith("vb "), out
        assert "·" in out, out


def test_tips_rotate_across_refreshes():
    # Different n values should surface different tips for a rotating state.
    seen = {core.render_statusline({"phase": "listening"}, n=i)
            for i in range(len(core._SL_TIPS))}
    assert len(seen) == len(core._SL_TIPS), "tips are not rotating"


def test_speaking_shows_the_cut_in_hint_not_a_random_tip():
    out = core.render_statusline({"phase": "speaking"}, n=3)
    assert "cut in" in out


def test_update_alert_carries_the_command():
    out = core.render_statusline({"phase": "off"},
                                 update_cmd="update: run  vb update")
    assert "⬆" in out and "vb update" in out


def test_no_alert_when_no_update():
    out = core.render_statusline({"phase": "listening"}, update_cmd="")
    assert "⬆" not in out


if __name__ == "__main__":
    test_every_phase_renders_non_empty()
    test_tips_rotate_across_refreshes()
    test_speaking_shows_the_cut_in_hint_not_a_random_tip()
    test_update_alert_carries_the_command()
    test_no_alert_when_no_update()
    print("ok  status line: rotation + per-state hints + update command")
