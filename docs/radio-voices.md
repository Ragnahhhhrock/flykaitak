# ATC radio voices (ElevenLabs)

The radio lines (Approach 119.1, Tower 118.7, your readbacks, other crews) can be voiced by ElevenLabs. The browser asks the Cloudflare Worker (`POST /tts {role, text}` in `server/worker.js`), which holds the API key, generates each line once, and caches the MP3 in the `flykaitak-radio` R2 bucket. `index.html` plays it through a highpass/lowpass radio band with faint static (`sfx.voice`). If `/tts` returns 503 (not set up) or any error, the sim uses the browser's speech voice as before. The key never reaches the browser.

## Switch it on
1. Create the bucket: `npx wrangler r2 bucket create flykaitak-radio`
2. Apply the new table: `npx wrangler d1 execute flykaitak-scores --remote --command "CREATE TABLE IF NOT EXISTS tts_gen (who TEXT NOT NULL, ts INTEGER NOT NULL); CREATE INDEX IF NOT EXISTS tts_gen_who_ts ON tts_gen (who, ts);"`
3. Voices are set in `server/wrangler.toml` under `[vars]` (`ELEVENLABS_VOICE_APP`, `_TWR`, `_YOU`, `_OTH`): Daniel, Bill, Chris and Charlie from the ElevenLabs default voices. Change the IDs to use other voices.
4. Store the API key as a secret: `npx wrangler secret put ELEVENLABS_API_KEY`
5. `npx wrangler deploy` from `server/`.

## Pre-recorded pieces (no live calls)
A radio call is built from pieces (`radioParts` in `index.html`): fixed phrases, and each digit as its own word ("one one eight decimal seven", "niner"), like real ATC read-outs. `tools/radio_presets.py` finds every piece the sim can say and records it once into `assets/radio/` (one MP3 per piece, listed in `assets/radio/index.json`). The sim loads the index at start and plays a call by stitching the MP3s together (edge silence trimmed, a short pause at commas and full stops), through the usual radio filter. Playing a call makes no ElevenLabs or Worker request.

- `python3 tools/radio_presets.py list` flies the sim headless (both runways, every game mode and weather, a few random seeds), adds the rare calls from templates (low on the glidepath, go-around, hold reasons, runway-control calls to other crews) and writes `assets/radio/manifest.json`. About 175 pieces and 3,500 characters in total.
- `ELEVENLABS_API_KEY=... python3 tools/radio_presets.py build` records every piece without an MP3 (voices from `server/wrangler.toml`). `build --via-worker` does it through the deployed Worker with no key (the Worker limits new pieces per hour per IP; on a 429 wait and run again). Safe to re-run; `--force` records everything again after a voice change.
- Run `list` again after changing any radio wording in `index.html`, then `build`, and commit `assets/radio/`.
- A piece missing from the index (a new line nobody has recorded yet) is asked of the Worker's `/tts` route if that is set up (cached in R2, a few credits), then the browser voice. If the voice service fails 3 times in a row with a 502 (for example out of credits) the sim stops asking for the rest of the session.

## Notes
- Model defaults to `eleven_turbo_v2_5` (set `ELEVENLABS_MODEL` to change it). Output is `mp3_44100_64`.
- Text sent is the spoken form (digits as words, "niner"), at most 400 characters. Only `APP`, `TWR`, `YOU`, `OTH` are accepted, from flykaitak.com or localhost.
- Through `/tts` a visitor can cause at most 120 new (uncached) pieces an hour; cached pieces are free. With the pre-recorded pieces in `assets/radio/` this route is only a fallback. Redeploy the Worker (`npx wrangler deploy` from `server/`) for the higher limit.
- The sim waits up to 2.5 s for a line before falling back to the browser voice for that call.
- Replay videos still use captions and squelch only; the voices are not rendered into them.
