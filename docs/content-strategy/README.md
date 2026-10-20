# Fly Kai Tak · Blog content strategy

Plan for 90 days of daily articles, 21 Oct 2026 to 18 Jan 2027 (90 posts, one a day).

| File | What it holds |
|---|---|
| `personas.md` | Five audience personas |
| `content-pillars.md` | Five content pillars, mapped to personas and blog categories |
| `content-calendar.md` / `.csv` | The 90 articles: date, pillar, persona, working title, category, tag, keywords |
| `posting-schedule.md` / `.csv` | A different publish time every day (HKT), with the reason for each slot |

The calendar and schedule are generated from `tools/content_plan.py`. Edit the lists there and re-run `python3 tools/content_plan.py`.

## Goal
Grow flykaitak.com plays and returning players by making the blog the place people find the sim: searches for Kai Tak, the checkerboard approach, 1998 Hong Kong and flight-sim tips.

## What the blog does today
- 114 posts, almost all release notes (a feature or fix, one post each; see `docs/blog.md`). Good for existing players, thin for people who have never heard of the sim.
- Every post is English and Cantonese, with a social card, share buttons, RSS and sitemap entries.

## Strategy in one line
Keep the release notes, and add a daily layer of evergreen guides, history and behind-the-scenes stories that answer what a stranger would search for, then send them into the sim.

## Principles
1. **One job per article.** Each post teaches one thing, tells one story, or answers one question, and ends with one call to action: fly the approach, try a mode, share a score.
2. **Link in and out.** Each article links to at least two earlier posts (release notes are the proof) and to the sim at https://flykaitak.com. Older posts get a link back to the new guide where it helps.
3. **Screenshots from the sim.** Use `tools/screenshot.py` (cockpit off by default). Real screenshots beat stock art.
4. **Bilingual by default.** The English and Cantonese pair is a rule in `docs/blog.md`. Cantonese is also a way to reach Hong Kong readers directly; check search results for 啟德 terms to see how crowded they are before relying on it.
5. **Facts only from the README, the code and the docs.** For history, check the claim against `docs/` and add a source before writing. No real airline names or logos. If a fact cannot be confirmed, leave it out.
6. **Follow the design system** in `docs/claude-project.md` for any pages, cards or images.
7. **New features still get their own release post** under the existing rule. These land on top of the daily plan, so a day with a release can swap that day's guide to the next day.

## Cadence
- One article a day, Wed 21 Oct 2026 to Mon 18 Jan 2027.
- Weekday rhythm (one pillar per day, see `content-pillars.md`):
  Mon Fly the Approach · Tue Real Hong Kong 1998 · Wed Aircraft Hangar · Thu The Kai Tak Story · Fri Scores and Challenges · Sat Spectate and Explore · Sun Behind the Build.
- Posts are 500 to 900 words with two to four screenshots. A Sunday build-log post can be shorter.

## Distribution
Blog first, then the channels already set up (`docs/facebook-page.md`, `docs/instagram.md`, Threads and X share buttons).
- Facebook and Threads: 15 to 30 minutes after the blog post, card image plus a hook line.
- Instagram: the card image as a feed post twice a week (Fri and Sat), Stories on the other days when there is a clip.
- Reddit and forums: Saturday and Sunday only, and only where the post is useful on its own (flight-sim communities, Hong Kong history groups). Follow each group's self-promotion rules.
- Replay videos (`Save video`) for Friday challenge posts.

## Measurement
Use GA4 (`docs/analytics.md`) and the public stats page (`docs/stats.md`). Review every Sunday.

| Measure | Why |
|---|---|
| Blog sessions and engaged sessions per post | Which pillars attract readers |
| Click-throughs from blog to the sim (`/`) | Does the post lead to play |
| `game_start` and `landing_attempt` events from blog referrals | Blog-driven play |
| Blog search terms (the `search` event) | Topics readers want next |
| Share clicks | Which posts people pass on |
| EN vs 粵 split | Whether Cantonese posts pull their weight |
| High score entries and replay shares | Community activity |

Checkpoints: day 30 (drop or double the weakest pillar), day 60 (re-rank the calendar by what worked), day 90 (plan the next quarter).

## Risks
- **Workload.** 90 bilingual posts with screenshots is a lot. Batch screenshots by pillar and write the Cantonese from the English the same day.
- **Accuracy.** History posts are the riskiest. Every claim needs a check against `docs/` or a cited source.
- **Feature drift.** Guides describe the sim as it is. Check the README before publishing and fix posts after a feature changes.
- **Duplicates.** Existing release posts already cover many features (Concorde, An-225, Plane Spotter, the shop). Guides add a how-to or story angle, never a repeat.

## Publishing mechanics
`posts.json` stores a date, not a time, so posts are drafted ahead in `blog/queue/` with a `publish_at` time from `posting-schedule.md`. A scheduled task runs `python3 tools/publish_queue.py --push` at each time: it moves the post into `blog/src/` and `posts.json` (date = publish day), renders the social card, rebuilds the blog and pushes to `main`. See `docs/blog.md`.

## Progress
- Drafted and queued: days 1 to 7 (21 to 27 Oct 2026), each with an English and a Cantonese body, reusing existing in-game screenshots.
- Next: days 8 to 14. Facts in every draft come from the README, `docs/` or the code; history posts still need a sourced fact check before they are drafted.
