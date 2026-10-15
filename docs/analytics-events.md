# Analytics events (GA4 `G-7MNP3SBEF8`)

Every event also carries `aircraft`, `weather` and `time_of_day`. Events only send on flykaitak.com.

| Event | When | Key parameters |
|---|---|---|
| `aircraft_select` | Aircraft card chosen on the setup screen | `aircraft` |
| `setup_option` | Any other setup choice (mode, time, weather, tick boxes) | `option`, `value` |
| `language_toggle` | Home screen language button (English / Cantonese) | `language` (`english`, `cantonese`) |
| `game_start` | Flight begins | `flight_number`, `game_mode` (`approach`, `approach31`, `free`, `free31`, `watch`, `watch31`, `lesson`), `runway`, `autopilot`, `guide`, `walled_city`, `flight605_wreck`, `lightning` |
| `lesson_start`, `lesson_step`, `lesson_complete`, `lesson_skip`, `lesson_action` | Take-off and Landing lessons (all carry `lesson`: `takeoff` or `landing`): begun; a step reached (`step`, `index`); finished (`flight_seconds`; for the Landing lesson, on landing); skipped (`step`, `index`); end-card choice (`action`: `keep_flying`, `try_landing`) | per event |
| `landing_attempt` | Wheels touch, or a crash / missed approach with gear down | `attempt_number`, `how` (`touchdown`, `crash`, `missed`), `flight_seconds` |
| `landing` | Successful landing (approach: rolled out; free flight: stopped) | `runway`, `grade`, `score`, `touchdown_fpm`, `touchdown_m`, `flight_number`, `flight_seconds`, `sim_seconds` |
| `crash` / `missed_approach` | Flight ended badly | `cause`, `distance_nm`, `flight_seconds`, `sim_seconds` |
| `control_toggle` | Gear, flaps, autopilot, HUD, deck, guide, sound, clouds, map, night, pause, seat side, flight board (`flight_board`, Plane Spotter), flight board flap sound (`flight_board_sound`, Plane Spotter) | `control`, `state`, `via` (`button`, `key`, `auto`), `flight_seconds` |
| `view_change`, `zoom`, `time_speed`, `weather_change`, `rewind`, `fast_forward` | In-flight controls | per event |
| `replay_start` / `replay_end` | Replay opened (automatically at the end of a flight, or Watch replay / Video on the report card) / closed (Report card, Esc, or automatically after the highlights) | `auto` (true when it opened by itself), `game_mode`, `runway`, `result` (`landed`, `crash`, `missed`), `replay_seconds` (start: length of the highlights; end: seconds watched) |
| `video_export` / `video_export_fail` | Replay video made / failed | `format` (`landscape`, `portrait`), `video_seconds`, `render_seconds`, `sound` / `reason` (`nosup`, `fail`) |
| `replay_link` / `replay_link_fail` | Share link made (video uploaded to the worker) / failed | `format`, `video_seconds` / `status` (HTTP status, 0 for a network error) |
| `flight_end` | Result screen, back to menu, restart, or page close | `outcome`, `flight_seconds`, `sim_seconds`, `landing_attempts`, `successful_landings`, `controls_toggled`, `flight_number` |
| `session_summary` | Tab hidden or page closed | `flights`, `landing_attempts`, `successful_landings`, `crashes`, `missed_approaches`, `landing_success_pct`, `total_flight_seconds`, `session_seconds` |
| `share` (replay video) | Replay video sheet | `method` (`video_download`, `video_native`, `video_copy`, `video_upload_youtube`, `_tiktok`, `_instagram`, `_facebook`, `_x`, `link_copy`, `link_native`, `link_x`, `link_facebook`, `link_whatsapp`, `link_reddit`, `link_threads`), `content_type` (`replay_video`), `result`, `grade` |
| `share` | Blog share button clicked (blog pages only) | `method` (`x`, `facebook`, `reddit`, `linkedin`, `whatsapp`, `threads`, `email`, `copy_link`, `native`), `content_type` (`article`), `item_id` (post slug) |
| `follow` | Facebook or Instagram link clicked on the home screen | `method` (`facebook`, `instagram`), `content_type` (`home`) |
| `shop_click` | Shop link on the home screen, or a product button on /shop/ | `method` (`nav`, `teaser`, `notify`, `checkout`), `content_type` (`home`, `shop`), `item_id` (product slug, shop page only) |
| `search` | Blog search box used, after typing pauses (blog pages only) | `search_term`, `results`, `page_type` (`blog`) |

`flight_seconds` is real play time (excludes pauses and rewinds). `sim_seconds` is simulation time (affected by time speed and rewinds).

To report on parameters in GA4, register them as custom dimensions (Admin > Custom definitions): event-scoped text for `control`, `state`, `via`, `outcome`, `game_mode`, `grade`, `how`, `option`, `value`; event-scoped numbers for `flight_seconds`, `landing_attempts`, `successful_landings`, `touchdown_fpm`, `score`.
| `concorde_offer_view` | Concorde purchase / code window opened | `owned` (true if already unlocked) |
| `concorde_checkout` | Buy button clicked (before going to Stripe) | none |
| `concorde_unlock` | Concorde unlocked | `method` (`purchase`, `code`, `restore`) |

`an225_offer_view`, `an225_checkout`, `an225_unlock`: the same three events as Concorde's, for the An-225 (see `docs/an225.md`).
