---
description: Voice ON (speak-only) - replies read aloud; you type or use space-to-talk for prompts (voicebridge)
allowed-tools: Bash(vb talkd:*), Bash(vb mode:*), Bash(/opt/homebrew/bin/vb:*)
---

Run these two commands with the Bash tool now:
1. `/opt/homebrew/bin/vb talkd on`
2. `/opt/homebrew/bin/vb mode speak`

If both succeeded, reply with exactly this (two lines):
"Voice on. I'll read replies aloud. Give me a prompt by typing, or press space to dictate (Claude's built-in voice)."
"Want fully hands-free? /voice-agent listens to you; /voice-off stops."
If either printed an ERROR, relay that error instead.
