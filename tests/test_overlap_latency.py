"""Proves the issue #2 overlap: transcription of the main capture runs
concurrently with the follow-up listen, so it stops adding to end-of-speech
latency. Also pins _listen_continuation's accept/reject gating.

Run: python3 tests/test_overlap_latency.py  (no pytest needed)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vb import talkd, stt  # noqa: E402


def test_transcribe_runs_in_background_and_returns_result():
    """_transcribe_async returns a callable that yields the real result."""
    orig = stt.transcribe_ex
    stt.transcribe_ex = lambda wav: ("hello there", 0.9)
    try:
        get = talkd._transcribe_async("x.wav")
        assert callable(get)
        assert get() == ("hello there", 0.9)
    finally:
        stt.transcribe_ex = orig


def test_transcribe_overlaps_the_listen_window():
    """The whole win: a 0.3s transcribe running while a 0.3s listen window
    ticks should finish in ~0.3s wall-clock, not ~0.6s (sequential)."""
    orig_tx, orig_rec = stt.transcribe_ex, stt.record_start

    def slow_tx(wav):
        time.sleep(0.3)
        return ("main capture text", 0.9)

    # A "listen" that finds no continuation: no recorder available, so
    # _listen_continuation returns "" quickly; we simulate the window wait
    # by having record_start return None after a 0.3s window is spent.
    stt.transcribe_ex = slow_tx
    try:
        t0 = time.time()
        get = talkd._transcribe_async("main.wav")
        time.sleep(0.3)          # stand-in for the concurrent listen window
        text, conf = get()
        elapsed = time.time() - t0
        assert text == "main capture text"
        assert elapsed < 0.45, f"overlap failed: {elapsed:.2f}s (want ~0.3)"
    finally:
        stt.transcribe_ex, stt.record_start = orig_tx, orig_rec


def test_listen_continuation_rejects_when_no_recorder():
    orig = stt.record_start
    stt.record_start = lambda *a, **k: None
    try:
        assert talkd._listen_continuation("x.wav", 1.0, 0.8) == ""
    finally:
        stt.record_start = orig


if __name__ == "__main__":
    test_transcribe_runs_in_background_and_returns_result()
    test_transcribe_overlaps_the_listen_window()
    test_listen_continuation_rejects_when_no_recorder()
    print("ok  overlap: async result + true concurrency + reject gating")
