# High scores

Every hand-flown IGS 13 landing is scored out of 100 (see `gradeLanding` in `index.html`) and added to the table.

| Score | Rank |
|---|---|
| 90+ | Captain |
| 76+ | First Officer |
| 60+ | Second Officer |
| 45+ | Flight Engineer |
| below 45 | Cadet |

Not ranked: autopilot landings (the autopilot was on at any point), landings after a rewind, free flight, Plane Spotter and crashes.
The table is sorted by score, earlier landing first on a tie. The player's callsign (up to 12 letters, digits, space, `. _ -`) is set on the result screen and remembered.

## Where it is stored
- **This browser** (always): `localStorage` keys `fkt-scores` (top 100) and `fkt-callsign`. Works offline and with no backend.
- **Shared table** (optional): a Cloudflare Worker with a D1 database in `server/`. Set `HS_API` near the top of the high score block in `index.html` to the Worker URL and every browser sees one table. Local scores are merged with the shared ones.

## Deploy the shared table
```
cd server
npx wrangler d1 create flykaitak-scores        # paste the database_id into wrangler.toml
npx wrangler d1 execute flykaitak-scores --remote --file=schema.sql
npx wrangler deploy                            # prints https://flykaitak-scores.<account>.workers.dev
```
Then set `const HS_API='https://flykaitak-scores.<account>.workers.dev'` in `index.html`, commit and push.
Scores are submitted by the browser, so a determined player can post a fake score. The Worker only checks the shape (score 0 to 100, clean name).
