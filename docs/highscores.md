# High scores

Every hand-flown IGS 13 landing is scored out of 100 (see `gradeLanding` in `index.html`) and added to the table.

| Score | Rank |
|---|---|
| 90+ | Captain |
| 78+ | First Officer |
| 62+ | Second Officer |
| 45+ | Flight Engineer |
| below 45 | Cadet |

## How a landing is scored (v2, 12 Oct 2026)
`gradeLanding` in `index.html`. Every part is a smooth curve: full marks only inside a tight window, a straight-line fall to nothing outside it. A 100 needs every part inside its window on the same flight, which is harder than the autopilot manages (it scores about 80 to 89 in most weather).

| Part | Points | Full marks | Zero at |
|---|---|---|---|
| Sink rate at touchdown | 16 | 120 fpm or less | 480 fpm |
| Touchdown point | 14 | 280 to 450 m past the threshold | 100 m or 900 m |
| Centreline at touchdown | 8 | within 1.5 m | 12 m |
| Touchdown speed | 8 | within 2 kt of Vref + 5 | 14 kt |
| Alignment (decrab) | 5 | within 1.5° of runway heading | 8° |
| Wings level | 4 | under 1° of bank | 5° |
| Glidepath | 14 | 6 m RMS or less, 3.5 nm out to the flare | 40 m |
| Approach track | 8 | 14 m RMS or less, same stretch | 70 m |
| Speed control | 8 | 2.5 kt RMS or less, same stretch | 12 kt |
| Rollout centreline | 8 | never more than 3 m off | 14 m |
| Stopping distance | 7 | 800 m of runway left | 150 m |

Tail strike takes 15 off. The score is rounded down, so 100 means every part was full. Approach parts are only scored on the IGS approach (`trkSample`); in free flight and the landing lesson the score is the other parts scaled to 100. The result screen shows the two parts that lost the most points.

Letter grade: A 90+, B 78+, C 62+, D 45+, E below. Ranks are in the table above.

## Table reset
Scoring v2 is much harder than v1, so the table started again on 12 Oct 2026 (`HS_SINCE` in `index.html`, `SINCE` in `server/worker.js`). Older landings stay in the database and in browsers but are not shown or served.

Not ranked: autopilot landings (the autopilot was on at any point), landings after a rewind, free flight, Plane Spotter and crashes.
The table is sorted by score, earlier landing first on a tie. The player's callsign (up to 12 letters, digits, space, `. _ -`) is set on the result screen and remembered.

## Starter scores
The table always includes ten fictional starter scores (`HS_SEED` in `index.html`, ids `seed1` to `seed10`, 52 down to 12). They are easy to beat and drop off once real landings fill the table.

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
