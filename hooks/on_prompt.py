#!/usr/bin/env python3
"""UserPromptSubmit hook: steer response language + spoken conversation tone.

If a voicebridge language is set (`vb lang ...`), this prints a short
directive that Claude Code adds to the context, so replies come back in the
language you chose and in a natural, spoken, back-and-forth tone (since
they'll be read aloud). Prints nothing when no language is set, so it never
interferes with normal work.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vb import core  # noqa: E402


def directive(lang: str) -> str:
    low = lang.lower()
    if low == "auto":
        how = ("Respond in the same language the user's message is in "
               "(English, Hindi in Devanagari, or Hinglish in Latin script, "
               "mirror them).")
    elif "hinglish" in low:
        how = "Respond in Hinglish (a natural, casual mix of Hindi and " \
              "English written in Latin script)."
    elif low in ("hindi", "हिंदी"):
        how = "Respond in Hindi, using Devanagari script."
    else:
        how = f"Respond in {lang}."
    tone = ("Use a warm, natural, spoken conversational tone, as if talking "
            "out loud: first person, concise, and end with a short follow-up "
            "question when it fits naturally. This is a style note for prose "
            "only; do not let it change code, commands, or file contents.")
    return f"[voicebridge] {how} {tone}"


def main() -> int:
    # A new prompt means the user has moved on: stop any speech mid-sentence
    # so the voice never talks over the next exchange.
    core.hush()

    # Record which session this prompt belongs to; talkd uses it so
    # /voice-on binds to THIS session, never a guess.
    data = core.read_hook_input()
    sid = data.get("session_id", "")
    tp = data.get("transcript_path", "")
    if sid and tp:
        from vb import talkd
        talkd.record_prompt(sid, tp)

    lang = core.get_lang()
    if lang:
        print(directive(lang))
    return 0


if __name__ == "__main__":
    sys.exit(main())
