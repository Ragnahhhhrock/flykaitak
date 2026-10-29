# ATC radio voices (ElevenLabs)

The radio lines (Approach 119.1, Tower 118.7, your readbacks, other crews) can be voiced by ElevenLabs. The browser asks the Cloudflare Worker (`POST /tts {role, text}` in `server/worker.js`), which holds the API key, generates each line once, and caches the MP3 in the `flykaitak-radio` R2 bucket. `index.html` plays it through a highpass/lowpass radio band with faint static (`sfx.voice`). If `/tts` returns 503 (not set up) or any error, the sim uses the browser's speech voice as before. The key never reaches the browser.

## Switch it on
1. Create the bucket: `npx wrangler r2 bucket create flykaitak-radio`
2. Apply the new table: `npx wrangler d1 execute flykaitak-scores --remote --command "CREATE TABLE IF NOT EXISTS tts_gen (who TEXT NOT NULL, ts INTEGER NOT NULL); CREATE INDEX IF NOT EXISTS tts_gen_who_ts ON tts_gen (who, ts);"`
3. Voices are set in `server/wrangler.toml` under `[vars]` (`ELEVENLABS_VOICE_APP`, `_TWR`, `_YOU`, `_OTH`): Daniel, Bill, Chris and Charlie from the ElevenLabs default voices. Change the IDs to use other voices.
4. Store the API key as a secret: `npx wrangler secret put ELEVENLABS_API_KEY`
5. `npx wrangler deploy` from `server/`.

## Credit use
A line is voiced in pieces, not whole (`radioParts` in `index.html`): fixed phrases and number groups (callsign digits, runway, wind, QNH) each go to `/tts` on their own, are cached in R2 by the Worker and kept decoded in the tab, then are trimmed of edge silence and stitched into one clip. Callsigns are random, so whole lines were almost never cache hits. Short words ("at") join the number after them; a line that splits into more than 8 pieces is sent whole. If the voice service fails 3 times in a row with a 502 (for example, out of credits), the sim stops asking for the rest of the session and uses the browser voice.

## Notes
- Model defaults to `eleven_turbo_v2_5` (set `ELEVENLABS_MODEL` to change it). Output is `mp3_44100_64`.
- Text sent is the spoken form (digits as words, "niner"), at most 400 characters. Only `APP`, `TWR`, `YOU`, `OTH` are accepted, from flykaitak.com or localhost.
- A visitor can cause at most 120 new (uncached) pieces an hour; cached pieces are free. Each new piece is a billed ElevenLabs request, so repeated pieces cost nothing. Redeploy the Worker (`npx wrangler deploy` from `server/`) for the higher limit; the piece caching itself is client-side and works with the old Worker.
- The sim waits up to 2.5 s for a line before falling back to the browser voice for that call.
- Replay videos still use captions and squelch only; the voices are not rendered into them.
