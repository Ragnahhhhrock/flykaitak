#!/usr/bin/env python3
"""Build the 90-day blog content calendar and posting schedule.

Edits go in the ARTICLES lists below. Run `python3 tools/content_plan.py` from the
repo root to rewrite docs/content-strategy/content-calendar.{md,csv} and
posting-schedule.{md,csv}. It checks that the plan has 90 consecutive days, that
every publish time is different, and that every linked slug is a real post.
"""
import csv
import datetime as dt
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "content-strategy"
START = dt.date(2026, 10, 21)
DAYS = 90

# weekday (Mon=0) -> (pillar number, pillar name, primary persona, lead language)
DAY_PLAN = {
    0: (1, "Fly the Approach", "Sim Sam", "English"),
    1: (2, "Real Hong Kong 1998", "Wing", "Cantonese"),
    2: (3, "Aircraft Hangar", "Sim Sam", "English"),
    3: (4, "The Kai Tak Story", "History Harry", "English"),
    4: (1, "Fly the Approach", "Casual Casey", "English"),
    5: (2, "Real Hong Kong 1998", "Wing", "Cantonese"),
    6: (5, "Behind the Build", "Eddie", "English"),
}

# Per-article persona override: date -> persona
PERSONA_OVERRIDE = {
    dt.date(2026, 11, 4): "History Harry",
    dt.date(2026, 12, 16): "History Harry",
    dt.date(2026, 10, 24): "Casual Casey",
    dt.date(2026, 11, 7): "Casual Casey",
}

# (title, category, tag, keywords, existing posts to link, note)
MON = [
    ("Fly your first Kai Tak approach in 10 minutes", "flying", "Feature", "Kai Tak approach simulator, first landing, beginner", "landing-lesson-for-first-time-pilots, checkerboard-turn-igs-13-approach", "Start-to-landing walkthrough using the landing lesson"),
    ("Reading the IGS 13: heading 088 to the checkerboard", "flying", "Feature", "IGS 13 approach, heading 088, checkerboard", "checkerboard-turn-igs-13-approach, checkerboard-turn-wider-and-higher", "Where to be and when, from Tsing Yi at about 3,100 ft"),
    ("The 47-degree right turn over Kowloon City, step by step", "flying", "Feature", "47 degree turn, Kowloon City, checkerboard turn", "checkerboard-turn-tightens-at-the-end, kowloon-walled-city-rebuilt", "In at about 650 ft, out at about 140 ft"),
    ("Speed, flaps and Vref: flying the approach on speed", "flying", "Feature", "Vref, flap settings, approach speed", "landing-lesson-for-first-time-pilots, first-perfect-score-100", "Per-type numbers come from the flight models in the code"),
    ("Wind and gusts: landing in a crosswind", "flying", "Feature", "crosswind landing, gusts, turbulence", "typhoons-fog-and-night-flying, harder-scoring-fresh-high-score-table", "How wind, gusts and turbulence change the approach"),
    ("Typhoon approach: when to go around", "flying", "Feature", "typhoon landing, go around, Kai Tak weather", "typhoons-fog-and-night-flying, runway-control-clearances-only-when-clear", "Decision points on the approach"),
    ("Night approach: flying by the lights and PAPI", "flying", "Feature", "night approach, PAPI, runway lights", "sun-moon-and-time-of-day, rooftop-cross-bar-lights", "Strobes, PAPI and the lead-in lights"),
    ("Fog and low cloud: finding the checkerboard", "flying", "Feature", "fog landing, low cloud, IGS approach", "typhoons-fog-and-night-flying, checkerboard-turn-igs-13-approach", "Flying the IGS when you cannot see the hill"),
    ("Take-off from Runway 13: climbing out over Kowloon Bay", "flying", "Feature", "take-off, Runway 13, Kowloon Bay", "take-off-lesson-for-first-time-pilots, runway-control-clearances-only-when-clear", "Free Flight take-off and the tower hold"),
    ("Runway 31 from the east: the Lei Yue Mun approach", "flying", "Feature", "Runway 31, Lei Yue Mun, easterly approach", "runway-31-easterly-approach-lei-yue-mun, runway-31-takeoff-free-flight", "The other end of the runway"),
    ("Autopilot and autoland: watch the machine fly the approach", "flying", "Feature", "autopilot, autoland, autothrottle", "checkerboard-turn-igs-13-approach, landing-lesson-for-first-time-pilots", "Learn the profile by watching it, then take over"),
    ("Flying without the HUD: instruments only", "controls", "Feature", "PFD, ND, HUD off, flight deck", "redrawn-aircraft-cockpit-winglets, landing-lesson-for-first-time-pilots", "Using the PFD, ND and checklist displays"),
    ("Go-arounds: when the runway is not clear", "flying", "Feature", "go-around, runway occupied, tower clearance", "runway-control-clearances-only-when-clear, bot-aircraft-bank-direction-fixed", "How the tower and arrivals decide"),
]
TUE = [
    ("Kowloon City in 1998: the shop signs under the flight path", "scenery", "Feature", "Kowloon City 1998, shop signs, 九龍城", "kowloon-walled-city-rebuilt, real-hong-kong-1998-open-data", "Photo story; Cantonese first"),
    ("Kowloon Walled City: the pre-1994 version and the 1998 park", "scenery", "Feature", "Kowloon Walled City, 九龍城寨, 1998 park", "kowloon-walled-city-rebuilt, lion-rock-and-kai-tak", "The sim offers both"),
    ("Checkerboard Hill: the marker on the hill", "scenery", "Feature", "checkerboard, Kowloon Tsai, 啟德", "checkerboard-turn-igs-13-approach, lion-rock-and-kai-tak", "Orange and white walls, striped mast, IGS lamps"),
    ("Real Hong Kong from open data: how the map was built", "scenery", "Behind the scenes", "Lands Department data, open data, Hong Kong map", "real-hong-kong-1998-open-data, real-1998-road-network", "Imagery, footprints, SRTM terrain, 1998 corrections"),
    ("Public housing estates under the approach", "scenery", "Feature", "public housing estates, Hong Kong 1998, Housing Authority", "public-housing-estates, real-housing-estates-from-hd-data", "Harmony, Trident, Twin Tower and Old Slab blocks"),
    ("The harbour in 1998: ferries, junks and container ships", "scenery", "Feature", "Victoria Harbour, Star Ferry, junks", "star-ferry-piers-boats-and-timetable, harbour-shipping-follows-the-fairways", "Ground-level life on the water"),
    ("Neon and billboards: Nathan Road after dark", "scenery", "Feature", "Hong Kong neon, Nathan Road, billboards", "giant-billboards-and-neon-over-kowloon, sun-moon-and-time-of-day", "Invented brands, no real logos"),
    ("Central skyline in 1998: Bank of China Tower and HSBC", "scenery", "Feature", "Bank of China Tower, HSBC building, Hong Kong skyline 1998", "bank-of-china-hsbc-rebuilt, landmarks-ocean-park-happy-valley", "Landmarks of the period; no Two IFC"),
    ("Happy Valley and Ocean Park from the air", "scenery", "Feature", "Happy Valley Racecourse, Ocean Park, 1998", "landmarks-ocean-park-happy-valley, ocean-park-rebuilt", "Floodlights, the Headland, the cable car"),
    ("The Peak, the Peak Tram and the view over the harbour", "scenery", "Feature", "the Peak, Peak Tram, Hong Kong view", "the-peak-tram-lookout-and-view, plane-spotter-viewpoints-car-park-roof-and-the-peak", "Two cars on one cable"),
    ("Taxis, minibuses and double-deckers: the traffic of Kowloon", "scenery", "Feature", "Hong Kong taxis, minibuses, double-decker buses", "real-1998-road-network, real-hong-kong-1998-open-data", "About 6,900 vehicles on the real roads"),
    ("Kwai Chung container terminal: the working harbour", "scenery", "Feature", "Kwai Chung, container terminal, Hong Kong port", "kwai-chung-container-terminal-detail, harbour-shipping-follows-the-fairways", "Cranes and container ships"),
]
WED = [
    ("Six aircraft at Kai Tak: which one should you fly?", "aircraft", "Feature", "747-400, 777-200, A330, A340, Concorde, An-225", "airlines-and-aircraft-at-kai-tak, fly-concorde-at-kai-tak", "Comparison table of the six types"),
    ("The 747-400 flight deck: CRT glass, yokes and four thrust levers", "aircraft", "Feature", "747-400 cockpit, CRT, thrust levers", "redrawn-aircraft-cockpit-winglets, 747-upper-deck-hump-reshaped", "Flight deck tour"),
    ("Flight 605: the 747-400 overrun of 4 November 1993", "aircraft", "History", "Flight 605, 747-400 overrun, Kai Tak 1993", "flight-605-wreck-at-the-runway-end, 747-upper-deck-hump-reshaped", "Anniversary post; check every fact against a source"),
    ("The 777-200 at Kai Tak: LCD glass, yokes and a stable approach", "aircraft", "Feature", "777-200 cockpit, LCD glass, stable approach", "redrawn-aircraft-cockpit-winglets, airlines-and-aircraft-at-kai-tak", "Flight deck and handling"),
    ("A330 and A340: sidesticks, ECAM and the Airbus feel", "aircraft", "Feature", "A330-300, A340-300, sidestick, ECAM", "redrawn-aircraft-cockpit-winglets, airlines-and-aircraft-at-kai-tak", "Blue-grey flight deck and sidesticks"),
    ("Concorde at Kai Tak: why it is a premium aircraft", "aircraft", "Feature", "Concorde, Kai Tak, premium aircraft", "fly-concorde-at-kai-tak, concorde-at-kai-tak-history", "Link to docs/concorde.md; avoid repeating the release post"),
    ("The Antonov An-225: six engines and 88.4 m of wing", "aircraft", "Feature", "An-225, Mriya, six engines", "fly-the-an-225-at-kai-tak, cargo-terminal-and-freighters", "Runway-only on the ground; capped take-off weight"),
    ("Inside the cabin: pick a seat and look around", "aircraft", "Feature", "airliner cabin, seat view, passenger cabin", "airlines-and-aircraft-at-kai-tak, fictional-airlines-of-kai-tak", "3-4-3, 3-3-3 and 2-4-2 layouts"),
    ("Fictional airlines of Kai Tak: why no real logos", "aircraft", "Behind the scenes", "fictional airlines, liveries, Kai Tak aircraft", "fictional-airlines-of-kai-tak, airlines-and-aircraft-at-kai-tak", "Explain the rule and show the invented liveries"),
    ("Flaps, spoilers and ailerons: the control surfaces that move", "aircraft", "Feature", "control surfaces, spoilers, flaps", "redrawn-aircraft-cockpit-winglets, landing-lesson-for-first-time-pilots", "Spoilers deploy on touchdown, including AI traffic"),
    ("Freighters and the cargo terminal: stands 41 to 46", "aircraft", "Feature", "cargo terminal, freighters, Kai Tak cargo", "cargo-terminal-and-freighters, airport-ground-vehicles", "Container dollies, loaders and forklifts"),
    ("Jet bridges and pushback: a turnaround at the stand", "aircraft", "Feature", "jet bridge, pushback, turnaround", "jet-bridges-and-pushback-tugs, airport-ground-vehicles", "Dock, retract, push back, turn"),
    ("The sound of Kai Tak: engines, GPWS and the touchdown chirp", "aircraft", "Feature", "flight sim sound, GPWS, touchdown", "quiet-take-offs-no-false-too-low-calls, flight-board-flap-sound", "Listen-through post; include a short clip"),
]
THU = [
    ("Why Kai Tak was one of the hardest airports to land at", "flying", "History", "Kai Tak, hardest airport, checkerboard approach", "checkerboard-turn-igs-13-approach, lion-rock-and-kai-tak", "Opening explainer; source every claim"),
    ("The IGS approach explained: guiding a jet to the hill", "flying", "History", "IGS approach, instrument guidance system, Kai Tak", "checkerboard-turn-igs-13-approach, landing-lesson-for-first-time-pilots", "How the IGS 13 worked"),
    ("The checkerboard: how a hillside marker became an icon", "scenery", "History", "checkerboard, Kai Tak icon, 啟德", "checkerboard-turn-igs-13-approach, lion-rock-and-kai-tak", "Use period photos already researched for the build"),
    ("A runway into the harbour: Kai Tak's geography", "scenery", "History", "Kai Tak geography, Kowloon Bay, runway 13", "real-hong-kong-1998-open-data, runway-31-easterly-approach-lei-yue-mun", "Why the runway sits where it does"),
    ("Kowloon Walled City: a city inside the flight path", "scenery", "History", "Kowloon Walled City, flight path, history", "kowloon-walled-city-rebuilt, lion-rock-and-kai-tak", "Context for the sim's two versions"),
    ("Typhoons and Kai Tak: why weather decided everything", "scenery", "History", "typhoon Hong Kong, Kai Tak weather, signals", "typhoons-fog-and-night-flying, harder-scoring-fresh-high-score-table", "Weather presets and what they model"),
    ("A full apron: Kai Tak at capacity in 1998", "aircraft", "History", "Kai Tak apron, capacity, stands", "kai-tak-terminal-and-apron-layout, remote-stands-and-apron-buses", "Why the sim keeps stands busy"),
    ("Talking to Kai Tak: Approach 119.1 and Tower 118.7", "flying", "History", "ATC radio, Hong Kong Approach, Kai Tak Tower", "runway-control-clearances-only-when-clear, control-tower-moved-to-terminal-roof", "How the radio calls work in the sim"),
    ("Reclamation and 1998: how the harbour has changed since", "scenery", "History", "Hong Kong reclamation, 1998 harbour, West Kowloon", "real-hong-kong-1998-open-data, real-1998-road-network", "The 1998 corrections the map makes"),
    ("The last summer: Kai Tak in 1998", "scenery", "History", "Kai Tak 1998, last year, closure", "kai-tak-terminal-and-apron-layout, real-hong-kong-1998-open-data", "Needs a sourced fact check before writing"),
    ("How the tower and the apron worked together at Kai Tak", "aircraft", "History", "control tower, apron control, Kai Tak operations", "control-tower-moved-to-terminal-roof, apron-taxi-lines-and-numbered-stands", "Layout from the chart"),
    ("Kai Tak by night: how the runway looked after dark", "flying", "History", "Kai Tak night, runway lights, approach lights", "sun-moon-and-time-of-day, rooftop-cross-bar-lights", "Night photos and the sim side by side"),
    ("After Kai Tak: why a simulator keeps the airport alive", "scenery", "History", "Kai Tak memories, flight simulator, Hong Kong history", "real-hong-kong-1998-open-data, blog-in-cantonese", "Reflective piece for Cantonese readers"),
]
FRI = [
    ("How landings are scored: the road to 100 out of 100", "scores", "Feature", "flight sim score, landing score, 100 points", "first-perfect-score-100, harder-scoring-fresh-high-score-table", "Spell out the score bands from the code"),
    ("Halloween challenge: one landing in a storm at night", "scores", "Feature", "flight sim challenge, storm landing, night", "typhoons-fog-and-night-flying, share-your-score-and-report-card", "Weekend challenge with replay video"),
    ("What a Captain landing takes (90 and up)", "scores", "Feature", "Captain rank, high score, landing grade", "high-score-table-captains-and-first-officers, first-perfect-score-100", "Ranks: Captain 90+, First Officer 78+, Second Officer 62+"),
    ("Flying Kai Tak on your phone: touch controls", "controls", "Feature", "mobile flight sim, touch controls, phone", "flying-kai-tak-on-your-phone, inverted-yoke-touch-and-mouse", "Phone tips and setup"),
    ("Mouse and keyboard: a Kai Tak control cheat sheet", "controls", "Feature", "flight sim keyboard controls, mouse, cheat sheet", "mouse-wheel-zoom, inverted-yoke-touch-and-mouse", "One-page key list from the code"),
    ("Weekend challenge: land in the worst weather you can", "scores", "Feature", "weather challenge, typhoon landing, flight sim", "typhoons-fog-and-night-flying, share-your-score-and-report-card", "Reader challenge, replay video"),
    ("Share your report card: post a landing in three taps", "scores", "Feature", "share score, report card, flight sim", "share-your-score-and-report-card, home-screen-share-buttons", "How sharing works"),
    ("Save and share a replay video of your landing", "scores", "Feature", "replay video, flight replay, MP4", "replay-highlights-video, replay-video-sound-and-share-links", "720p and vertical formats"),
    ("Crash causes: what the live stats show", "scores", "Feature", "crash causes, flight sim stats, Kai Tak", "public-stats-dashboard, live-stats-on-the-home-screen", "Use real numbers from /stats/ on the day"),
    ("Christmas night landing challenge", "scores", "Feature", "night landing challenge, Christmas, flight sim", "sun-moon-and-time-of-day, share-your-score-and-report-card", "Short, seasonal, shareable"),
    ("New year, new rank: set a 2027 score goal", "scores", "Feature", "flight sim goals, rank, high score table", "high-score-table-captains-and-first-officers, high-scores-button-on-the-home-screen", "A practice plan toward Captain"),
    ("Which aircraft lands easiest? Scores by type", "scores", "Feature", "aircraft comparison, landing score, 747 vs A330", "public-stats-dashboard, airlines-and-aircraft-at-kai-tak", "Use real data from /stats/; say what it does and does not show"),
    ("The best landings of the quarter", "scores", "Update", "best landings, leaderboard, high scores", "harder-scoring-fresh-high-score-table, first-perfect-score-100", "Community round-up; ask permission before naming players"),
]
SAT = [
    ("Plane Spotter: watch Kai Tak from the car park roof", "scenery", "Feature", "plane spotting, Kai Tak car park, spotter view", "plane-spotter-viewpoints-car-park-roof-and-the-peak, car-park-spotter-view-moved", "The no-pressure way into the sim"),
    ("The view from the Peak: jets over the harbour", "scenery", "Feature", "the Peak, spotter view, Hong Kong harbour", "the-peak-tram-lookout-and-view, plane-spotter-viewpoints-car-park-roof-and-the-peak", "Spectator view on the Peak Tower rim"),
    ("Take the Hong Kong harbour helicopter tour", "scenery", "Feature", "helicopter tour, Hong Kong harbour, scenic flight", "helicopter-scenic-tour-hong-kong-harbour, helicopter-tour-guide-voice", "About four minutes, captions in English and Cantonese"),
    ("Reading the apron: stands, buses and pushback tugs", "aircraft", "Feature", "Kai Tak apron, stands, pushback", "jet-bridges-and-pushback-tugs, remote-stands-and-apron-buses", "What to watch for in Plane Spotter"),
    ("From the control tower: how the runway is managed", "flying", "Feature", "control tower view, runway control, Kai Tak", "runway-control-clearances-only-when-clear, control-tower-moved-to-terminal-roof", "Tower view tour"),
    ("From a junk in the harbour: a plane spotter's view", "scenery", "Feature", "harbour view, junk, plane spotting", "harbour-shipping-follows-the-fairways, plane-spotter-viewpoints-car-park-roof-and-the-peak", "A different angle on the approach"),
    ("Plane Spotter in a typhoon", "scenery", "Feature", "typhoon, plane spotter, weather", "typhoons-fog-and-night-flying, plane-spotter-viewpoints-car-park-roof-and-the-peak", "Weather and time controls in the spotter views"),
    ("Dusk at Kai Tak: when the lights come on", "scenery", "Feature", "dusk, night lights, Kai Tak", "sun-moon-and-time-of-day, red-floodlight-masts-over-the-stands", "Time of day presets and lighting"),
    ("Prince Edward Road: aircraft passing overhead", "scenery", "Feature", "Prince Edward Road, low flying, spotter", "plane-spotter-viewpoints-car-park-roof-and-the-peak, kowloon-walled-city-rebuilt", "The street view of the approach"),
    ("The split-flap flight board: reading 1998 departures", "scenery", "Feature", "split-flap board, flight information, 1998", "split-flap-flight-information-board, flight-board-key-and-button", "Made-up airlines and flight numbers"),
    ("Checkerboard Hill: the spectator view", "scenery", "Feature", "checkerboard hill, IGS lamps, spectator", "checkerboard-turn-igs-13-approach, lion-rock-and-kai-tak", "Watch the turn from the hilltop"),
    ("The corner map: live traffic dots and altitudes", "controls", "Feature", "live map, traffic, altitude in hundreds of feet", "map-toggle-live-aircraft, bigger-map-home-and-plane-spotter", "How to read the map"),
    ("Runway 31 spotting: easterly arrivals", "scenery", "Feature", "Runway 31, plane spotter, easterly", "runway-31-plane-spotter, runway-31-easterly-approach-lei-yue-mun", "The other direction of traffic"),
]
SUN = [
    ("Why build a Kai Tak simulator in the browser?", "site", "Behind the scenes", "Kai Tak simulator, browser game, Three.js", "latest-updates-on-the-home-screen, real-hong-kong-1998-open-data", "Founder story; short and personal"),
    ("From open data to Three.js: how the map is built", "site", "Behind the scenes", "Three.js, open data, map building", "real-hong-kong-1998-open-data, real-1998-road-network", "The tools in tools/ and the steps"),
    ("Rebuilding the checkerboard from period photos", "scenery", "Behind the scenes", "checkerboard, period photos, 3D model", "checkerboard-turn-igs-13-approach, lion-rock-and-kai-tak", "Photo to model, with before and after"),
    ("How we test it: the autopilot in every weather preset", "site", "Behind the scenes", "testing, autopilot, flight sim development", "typhoons-fog-and-night-flying, first-perfect-score-100", "The no-input crash test and autoland test"),
    ("How runway control works: one movement at a time", "site", "Behind the scenes", "runway control, air traffic, sim design", "runway-control-clearances-only-when-clear, runway-31-takeoff-free-flight", "tools/test_runway.py explained"),
    ("Writing Kai Tak in Cantonese: how the bilingual blog works", "site", "Behind the scenes", "Cantonese blog, bilingual website, 粵語", "blog-in-cantonese, cantonese-language-toggle", "EN / 粵 toggle and the writing rules"),
    ("What the stats page shows: 30 days of landings", "site", "Update", "flight sim stats, landing data, dashboard", "public-stats-dashboard, live-stats-on-the-home-screen", "Use real numbers from /stats/ on the day"),
    ("Round-up: what shipped since October", "site", "Update", "Fly Kai Tak updates, round-up, new features", "latest-updates-on-the-home-screen, blog-categories-search-and-pages", "List from the git log"),
    ("Help build the Kai Tak terminal interior", "site", "Update", "Kai Tak terminal, photos wanted, community", "help-build-the-kai-tak-terminal-interior, inside-the-1998-terminal-staff-and-signs", "Photo and memory call-out"),
    ("Roadmap: what is next for Fly Kai Tak", "site", "Update", "flight sim roadmap, Kai Tak, new aircraft", "landing-lesson-for-first-time-pilots, take-off-lesson-for-first-time-pilots", "From docs/claude-project.md roadmap"),
    ("The Kai Tak shop: designs, merch and how it works", "site", "Update", "Kai Tak merch, shop, original designs", "the-kai-tak-shop, follow-fly-kai-tak-on-facebook-and-instagram", "Original artwork only; no airline logos"),
    ("What players asked for: community feedback", "site", "Update", "player feedback, feature requests, community", "share-your-score-and-report-card, follow-fly-kai-tak-on-facebook-and-instagram", "Pull from emails, comments and shares"),
    ("90 days of daily posts: what worked", "site", "Behind the scenes", "blog results, content strategy, 90 days", "blog-categories-search-and-pages, public-stats-dashboard", "Reads from the GA4 review"),
]
ARTICLES = {0: MON, 1: TUE, 2: WED, 3: THU, 4: FRI, 5: SAT, 6: SUN}

# persona -> list of (start HH:MM, end HH:MM, label), all Hong Kong time (UTC+8)
WINDOWS = {
    "Sim Sam": [("19:00", "21:30", "HK evening, Perth evening, European lunch"), ("22:00", "23:30", "late evening HKT, US morning"), ("09:00", "11:00", "US evening, Australian morning")],
    "Wing": [("07:30", "08:45", "Hong Kong commute"), ("12:15", "13:15", "Hong Kong lunch"), ("20:00", "22:30", "Hong Kong after dinner")],
    "History Harry": [("18:30", "20:30", "early evening HKT, European lunch"), ("10:00", "11:30", "late morning HKT, US evening")],
    "Casual Casey": [("12:30", "13:30", "lunch break"), ("17:45", "19:00", "after school and work"), ("21:30", "23:00", "late evening scroll")],
    "Eddie": [("07:00", "08:00", "early planning time, Perth and Hong Kong"), ("15:30", "16:30", "mid-afternoon HKT")],
}


def mins(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def fmt(m):
    return "%02d:%02d" % (m // 60, m % 60)


def build():
    posts_slugs = {p["slug"] for p in json.load(open(ROOT / "blog" / "posts.json"))}
    # also accept built post pages that are not listed in posts.json
    posts_slugs |= {p.name for p in (ROOT / "blog").iterdir() if (p / "index.html").exists()}
    queues = {k: list(v) for k, v in ARTICLES.items()}
    rng = random.Random(2026)
    used, prev, persona_count = set(), None, {}
    rows = []
    for i in range(DAYS):
        d = START + dt.timedelta(days=i)
        wd = d.weekday()
        pn, pname, persona, lang = DAY_PLAN[wd]
        persona = PERSONA_OVERRIDE.get(d, persona)
        title, cat, tag, kw, links, note = queues[wd].pop(0)
        for s in [x.strip() for x in links.split(",")]:
            assert s in posts_slugs, "unknown slug %s (%s)" % (s, title)
        wins = WINDOWS[persona]
        n = persona_count.get(persona, 0)
        persona_count[persona] = n + 1
        a, b, label = wins[n % len(wins)]
        for _ in range(500):
            m = rng.randint(mins(a), mins(b))
            if m % 5 == 0:
                continue
            t = fmt(m)
            if t in used:
                continue
            if prev is not None and abs(m - prev) < 45:
                continue
            break
        else:
            raise SystemExit("no time found for %s" % d)
        used.add(t)
        prev = m
        social = fmt(m + 20)
        rows.append(dict(n=i + 1, date=d.isoformat(), day=d.strftime("%a"), pillar="%d. %s" % (pn, pname),
                         persona=persona, lang=lang, title=title, category=cat, tag=tag, keywords=kw,
                         links=links, note=note, time=t, window=label, social=social))
    assert all(not q for q in queues.values()), "unused articles"
    assert len(rows) == DAYS and len({r["time"] for r in rows}) == DAYS
    return rows


def write(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    cal_cols = ["n", "date", "day", "pillar", "persona", "lang", "title", "category", "tag", "keywords", "links", "note"]
    with open(OUT / "content-calendar.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#", "Date", "Day", "Pillar", "Persona", "Lead language", "Working title", "Blog category", "Tag", "Keywords", "Link to existing posts", "Angle and notes"])
        for r in rows:
            w.writerow([r[c] for c in cal_cols])
    sch_cols = ["n", "date", "day", "time", "social", "persona", "window", "title"]
    with open(OUT / "posting-schedule.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#", "Date", "Day", "Blog publish (HKT)", "Facebook and Threads (HKT)", "Persona", "Why this slot", "Article"])
        for r in rows:
            w.writerow([r[c] for c in sch_cols])

    md = ["# 90-day content calendar", "",
          "One article a day, %s to %s. Weekday rhythm: Mon Fly the Approach, Tue Real Hong Kong 1998, Wed Aircraft Hangar, Thu The Kai Tak Story, Fri Scores and Challenges, Sat Spectate and Explore, Sun Behind the Build." % (rows[0]["date"], rows[-1]["date"]), "",
          "Titles are working titles. Every article needs: screenshots (`tools/screenshot.py`), an English and a Cantonese body, links to the existing posts listed, and the checks in `README.md` (facts from the repo or a named source, no real airline names or logos). The Cantonese version leads on Tuesday and Saturday posts. Times are in `posting-schedule.md`. Generated by `tools/content_plan.py`; the same data is in `content-calendar.csv`.", ""]
    weeks = {}
    for r in rows:
        monday = dt.date.fromisoformat(r["date"])
        monday -= dt.timedelta(days=monday.weekday())
        weeks.setdefault(monday, []).append(r)
    for wi, (monday, rs) in enumerate(sorted(weeks.items()), 1):
        md += ["## Week %d (week of %s)" % (wi, monday.strftime("%-d %b %Y")), "",
               "| # | Date | Pillar | Persona | Working title | Category | Tag | Angle |", "|---|---|---|---|---|---|---|---|"]
        for r in rs:
            md.append("| %d | %s %s | %s | %s | %s | %s | %s | %s |" % (
                r["n"], r["day"], dt.date.fromisoformat(r["date"]).strftime("%-d %b"), r["pillar"], r["persona"],
                r["title"], r["category"], r["tag"], r["note"]))
        md.append("")
    counts = {}
    for r in rows:
        counts[r["pillar"]] = counts.get(r["pillar"], 0) + 1
    md += ["## Totals", "", "| Pillar | Posts |", "|---|---|"] + ["| %s | %d |" % (k, v) for k, v in sorted(counts.items())] + ["| Total | %d |" % len(rows), ""]
    (OUT / "content-calendar.md").write_text("\n".join(md))

    sm = ["# Posting schedule", "",
          "A different publish time every day, in Hong Kong time (HKT, UTC+8, the same as Perth). No two days share a time, and consecutive days are at least 45 minutes apart. Each slot is picked inside a window when that day's main persona is most likely to be reading (see `personas.md`). Facebook and Threads follow 20 minutes after the blog post; Instagram gets the card image on Fridays and Saturdays.", "",
          "Re-test after 30 days with GA4 (sessions by hour of day and by referrer) and move the windows toward what works. Generated by `tools/content_plan.py`; same data in `posting-schedule.csv`.", "",
          "| # | Date | Blog (HKT) | Social (HKT) | Persona | Why this slot | Article |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        sm.append("| %d | %s %s | %s | %s | %s | %s | %s |" % (
            r["n"], r["day"], dt.date.fromisoformat(r["date"]).strftime("%-d %b %Y"), r["time"], r["social"], r["persona"], r["window"], r["title"]))
    sm.append("")
    (OUT / "posting-schedule.md").write_text("\n".join(sm))


if __name__ == "__main__":
    rows = build()
    write(rows)
    print("wrote %d days, %s to %s" % (len(rows), rows[0]["date"], rows[-1]["date"]))
