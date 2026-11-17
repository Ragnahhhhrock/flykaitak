# ATC radio voices

The radio lines (Approach 119.1, Tower 118.7, your readbacks, other crews) are played from pre-recorded MP3 pieces in `assets/radio/` (listed in `assets/radio/index.json`). The pieces were recorded once, in 2026, with ElevenLabs voices. The sim makes no voice-service or Worker request while you fly, and there is no ElevenLabs account, key or Worker route behind it any more.

## How a call is played
A radio call is built from pieces (`radioParts` in `index.html`): fixed phrases, and each number as one piece read as digits ("one one eight decimal seven", "niner"), like real ATC read-outs. Callsign numbers come from a fixed pool of 40 (`CALLS` in `index.html`), so every callsign is pre-recorded too. The sim loads the index at start and plays a call by stitching the MP3s together (edge silence trimmed, a short pause at commas and full stops), through a highpass/lowpass radio band with faint static (`sfx.voice`).

A piece missing from the index (a new line nobody has recorded) is read by the browser's speech voice instead. The sim waits up to 2.5 s for a line before falling back to the browser voice for that call.

## Adding new lines
- `python3 tools/radio_presets.py list` flies the sim headless and writes `assets/radio/manifest.json`, listing every piece the sim can say. Run it after changing any radio wording or the callsign pool in `index.html`.
- `tools/radio_presets.py build` recorded the missing pieces with ElevenLabs (needs an `ELEVENLABS_API_KEY`, voice IDs in `voices()` in the script, and ffmpeg). That subscription has been cancelled, so new pieces need a new recording source (or a re-subscription) before `build` works again. Until then new lines use the browser voice.

## Notes
- Replay videos use captions and squelch only; the voices are not rendered into them.
