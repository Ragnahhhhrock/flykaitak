# Analytics

Google Analytics 4 through the Google tag (gtag.js). It loads only on flykaitak.com.

## Setup
1. In GA4, create a web data stream for https://flykaitak.com and copy the measurement ID (G-…).
2. In `index.html`, set `window.FKT_ANALYTICS.id` to that ID.
3. Optional, Google tag gateway: in Cloudflare, go to the zone, then Speed (or "Google tag gateway"), and enable it with your measurement ID and a path such as `/metrics/`. Then set `window.FKT_ANALYTICS.src` to `/metrics/` so the tag loads first-party from flykaitak.com. Leave `src` at the googletagmanager.com URL until the gateway is live.

## Events
Every event carries `aircraft`, `weather` and `time_of_day`.

| Event | When | Extra parameters |
|---|---|---|
| game_start | Begin descent / Fly it again | autopilot, guide, walled_city, flight605_wreck, lightning |
| landing | Aircraft stops on the runway | grade, score, touchdown_fpm, touchdown_m, flight_seconds, autopilot_used |
| crash | Any accident | cause, flight_seconds, distance_nm |
| missed_approach | Go-around or overflight | cause, flight_seconds, distance_nm |
| view_change | Camera view changed | view |
| autopilot | Autopilot toggled in flight | on |
| weather_change | Weather changed in flight | |
| day_night_toggle | Night button | |
| zoom | Zoom level changed | level |
| time_speed | Time speed changed | speed |
| rewind / fast_forward | 10-second jumps | seconds |

In GA4, register `grade`, `cause`, `view` and `aircraft` as custom dimensions, and `score` and `touchdown_fpm` as custom metrics, to report on them. Mark `landing` as a key event.
