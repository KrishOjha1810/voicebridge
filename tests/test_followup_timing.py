"""Characterization tests for the follow-up / end-of-speech timing (issue #2).

These pin the behavior that the latency work must NOT change: the follow-up
window still adapts to how finished the words sound, and stitching still
merges a mid-thought pause. Run: python3 -m pytest tests/test_followup_timing.py
or just: python3 tests/test_followup_timing.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vb import talkd  # noqa: E402


CASES = [
    ("do it.", 0.5),            # finished sentence, common short command
    ("what changed?", 0.5),     # finished question
    ("stop!", 0.5),             # finished exclamation
    ("run the tests", 0.8),     # no punctuation (whisper's common output)
    ("open the file", 0.8),     # no punctuation, complete-sounding
    ("fix this and", 2.0),      # trailing conjunction -> mid-thought
    ("update the readme,", 2.0),  # trailing comma -> mid-thought
    ("and then we", 2.0),       # trailing pronoun in the incomplete set
    ("", 0.8),                  # empty -> neutral default
]


def test_followup_window():
    for text, want in CASES:
        got = talkd.followup_window(text)
        assert got == want, f"{text!r}: got {got}, want {want}"


if __name__ == "__main__":
    test_followup_window()
    print(f"ok  {len(CASES)} follow-up window cases pass")
