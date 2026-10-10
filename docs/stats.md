# Public stats dashboard

`/stats/` (https://flykaitak.com/stats/) shows anonymous counts: flights started, landing attempts, successful landings, crashes, missed approaches, mode selections, aircraft selections and results, weather, day/night, crash causes, grades and a 30-day trend.

## How it works
- The game posts one small event per `game_start`, `landing_attempt`, `landing`, `crash`, `missed_approach`, `aircraft_select`, `lesson_start` and `lesson_complete` to `{FKT_API}/events` (`statPost` in `index.html`). Only on flykaitak.com, so local test runs are never counted. No IP, name or id is stored.
- The Worker in `server/` stores them in the D1 `events` table and serves aggregates at `GET /stats` (cached 60 s).
- `/stats/` (`assets/stats/stats.js`) draws the page from that feed. `/stats/?demo` previews the layout with labelled sample data.

## Turn it on
Counting only starts once the Worker is deployed and its URL is set:
```
cd server
npx wrangler d1 create flykaitak-scores        # paste the database_id into wrangler.toml (skip if done)
npx wrangler d1 execute flykaitak-scores --remote --file=schema.sql   # adds the events table
npx wrangler deploy
```
Then set `window.FKT_API='https://flykaitak-scores.<account>.workers.dev'` in `assets/api.js` (it also drives the shared high score table), commit and push.
Counts start from deploy; earlier flights are only in Google Analytics. Events are posted by browsers, so a determined person could inflate them.

## Live setup
- D1 database `flykaitak-scores` (id `c89ea623-d09e-4285-8a4f-884c7ded2cd2`) and Worker `flykaitak-scores`, created in the Cloudflare dashboard.
- Worker URL: https://flykaitak-scores.malgordonperth.workers.dev (set in `assets/api.js`).
- The deployed Worker was pasted into the dashboard editor as a single line (same logic as `server/worker.js`). Redeploy from `server/` with `npx wrangler deploy` if you change the Worker; set the `database_id` in `server/wrangler.toml` first.
