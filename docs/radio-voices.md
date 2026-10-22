# ATC radio voices (ElevenLabs)

The radio lines (Approach 119.1, Tower 118.7, your readbacks, other crews) can be voiced by ElevenLabs. The browser asks the Cloudflare Worker (`POST /tts {role, text}` in `server/worker.js`), which holds the API key, generates each line once, and caches the MP3 in the `flykaitak-radio` R2 bucket. `index.html` plays it through a highpass/lowpass radio band with faint static (`sfx.voice`). If `/tts` returns 503 (not set up) or any error, the sim uses the browser's speech voice as before. The key never reaches the browser.

## Switch it on
1. Create the bucket: `npx wrangler r2 bucket create flykaitak-radio`
2. Apply the new table: `npx wrangler d1 execute flykaitak-scores --remote --command "CREATE TABLE IF NOT EXISTS tts_gen (who TEXT NOT NULL, ts INTEGER NOT NULL); CREATE INDEX IF NOT EXISTS tts_gen_who_ts ON tts_gen (who, ts);"`
3. Voices are set in `server/wrangler.toml` under `[vars]` (`ELEVENLABS_VOICE_APP`, `_TWR`, `_YOU`, `_OTH`): Daniel, Bill, Chris and Charlie from the ElevenLabs default voices. Change the IDs to use other voices.
4. Store the API key as a secret: `npx wrangler secret put ELEVENLABS_API_KEY`
5. `npx wrangler deploy` from `server/`.

## Notes
- Model defaults to `eleven_turbo_v2_5` (set `ELEVENLABS_MODEL` to change it). Output is `mp3_44100_64`.
- Text sent is the spoken form (digits as words, "niner"), at most 400 characters. Only `APP`, `TWR`, `YOU`, `OTH` are accepted, from flykaitak.com or localhost.
- A visitor can cause at most 60 new (uncached) lines an hour; cached lines are free. Each new line is a billed ElevenLabs request, so repeated lines cost nothing.
- The sim waits up to 2.5 s for a line before falling back to the browser voice for that call.
- Replay videos still use captions and squelch only; the voices are not rendered into them.
