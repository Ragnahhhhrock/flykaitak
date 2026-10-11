# Replays, replay videos and share links

## In the sim (no server needed)
- Every flight is recorded at 10 Hz (`REC.f`), with its radio calls (`REC.r`). When the flight ends the highlights play by themselves, then the report card. See "Flight replay" in the README.
- **Save video** renders the highlights to an MP4 in the browser: WebCodecs for video and audio, `assets/vendor/mp4-muxer.js` (MIT) to write the file. 1280×720 or 720×1280, 30 fps, about 4.5 Mbit/s.
  - Video: H.264 (Chrome, Edge, Safari), VP9 where H.264 is missing.
  - Sound: AAC, or Opus where AAC is missing. The track is rendered offline with an `OfflineAudioContext` from what each frame shows: engine, whine, wind, rain, reverser, tyres, gear rumble (quieter when the camera is far away), the touchdown thump, the crash, radio squelch and static under each call (the words are captions; the browser's speech voice can't be recorded), and a two-tone airport chime over the report card.
- Download, Share… (the phone's share sheet with the file) and Copy caption always work.

## Share links (needs the worker)
**Get share link** uploads the video, a poster frame and the report card image to the Fly Kai Tak worker. It returns a page, `/r/<id>`, with the video, the result, a "Fly it yourself" button and Open Graph video tags. A link posted on X, Facebook, WhatsApp, Reddit or Threads then shows the report card as its preview, and Facebook can play the video inline.
The button only appears when `GET <FKT_API>/replays` answers `{"ok":true}`, so nothing changes in the sim until the worker below is deployed.

### Switch it on
From `server/` (the same place the scores worker is deployed from, with your real `database_id` in `wrangler.toml`):
```
npx wrangler r2 bucket create flykaitak-replays
npx wrangler d1 execute flykaitak-scores --remote --file=schema.sql   # adds the replays table; existing tables are untouched
npx wrangler deploy
```
Check: `https://flykaitak-scores.malgordonperth.workers.dev/replays` should show `{"ok":true,...}`.

### Optional: links on your own domain
By default links look like `https://flykaitak-scores.malgordonperth.workers.dev/r/abc123`. For `https://replay.flykaitak.com/r/abc123`, uncomment the `routes` line and the `[vars]` block in `server/wrangler.toml` and deploy again. Cloudflare creates the DNS record for the custom domain.

### Limits and housekeeping
- Up to 48 MB a video, 12 uploads an hour from one address (stored only as a salted hash; set a `SALT` secret with `npx wrangler secret put SALT` to change the salt).
- Pages are `noindex`. Files are served with long cache headers and HTTP range support (needed for Safari).
- R2's free tier is 10 GB of storage. A 45-second video is about 25–30 MB, so roughly 350 videos fit. To keep it in check, add a lifecycle rule in the Cloudflare dashboard (R2 › flykaitak-replays › Settings › Object lifecycle rules) to delete objects under `replays/` after, say, 90 days. Old share pages then say the replay is no longer available.
- To remove one replay: delete `replays/<id>.mp4`, `.jpg` and `.png` from the bucket and `DELETE FROM replays WHERE id='<id>'`.
