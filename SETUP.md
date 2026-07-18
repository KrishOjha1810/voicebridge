# voicebridge setup

## Dependencies (already installed if you ran the build)

```
brew install whisper-cpp sox
```

Model (~142MB, downloaded to `~/.voicebridge/models/ggml-base.en.bin`):

```
curl -fSL -o ~/.voicebridge/models/ggml-base.en.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
```

Check readiness: `vb stt` should print `ready : True`.

## macOS permissions (first run of `vb listen`)

macOS will prompt for these the first time. If it doesn't, grant them
manually in **System Settings -> Privacy & Security**:

1. **Microphone** -> enable your terminal app (Terminal / iTerm / the app
   running `vb listen`). Needed for `rec` to record.
2. **Accessibility** -> enable the same app. Needed for the Cmd+V paste
   keystroke that drops your transcribed text into the Claude window.

If a paste does nothing, it's almost always the Accessibility toggle.

## Seamless hands-free use (recommended)

The point is to talk without leaving the Claude Code window. Bind
`vb listen --send` to a global hotkey so triggering it never steals focus:

### Option A - macOS Shortcuts (no install)

1. Shortcuts app -> new shortcut -> "Run Shell Script".
2. Command: `/Users/krishojha/voicebridge/bin/vb listen --send`
3. Assign a keyboard shortcut in the shortcut's settings.

### Option B - Raycast / Alfred

Add a Script Command that runs the same line, bind a hotkey.

### Option C - skhd (power users)

```
brew install koekeishiya/formulae/skhd
# ~/.skhdrc
cmd + shift - space : /Users/krishojha/voicebridge/bin/vb listen --send
skhd --start-service
```

## The loop, day to day

1. `vb on` once (starts the watcher; Claude speaks its replies).
2. Wear headphones.
3. Hit your hotkey, speak, pause. Your words paste into Claude and send.
4. Claude replies out loud. Hit the hotkey again to cut in and respond.

Turn it all off with `vb off`.

## Tuning

- Voice/speed of output: `VOICEBRIDGE_VOICE`, `VOICEBRIDGE_RATE` env vars.
  List voices: `say -v '?'`.
- Silence sensitivity / max length of a recording: `record()` args in
  `vb/stt.py` (`silence_stop`, `max_secs`).
- Bigger/more accurate model: swap `ggml-base.en.bin` for
  `ggml-small.en.bin` (slower, more accurate) and update `MODEL` in
  `vb/stt.py`.
