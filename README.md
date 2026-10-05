# Fly Kai Tak

A browser flight simulator for the Runway 13 IGS approach into Hong Kong Kai Tak, set in 1998.

You start descending over Tsing Yi at about 3,100 ft on the instrument guidance system, heading 088. Fly toward the checkerboard on the hill at Kowloon Tsai, make the 47° right turn low over Kowloon City (in at about 650 ft, 2 NM from touchdown; out at about 140 ft), and land on a runway that ends in Kowloon Bay. Each run ends in a landing (graded) or a crash (with the cause).

Play at https://flykaitak.com, or serve the folder with any static web server (`python3 -m http.server`) and open `index.html`. Opening the file directly won't work because the map data is fetched.

## Real Hong Kong
- The aerial imagery, coastline, main roads and about 24,000 building footprints come from the Hong Kong Lands Department's open data. Terrain is SRTM elevation with building bumps filtered out
- The runway is fitted to the old Kai Tak strip (threshold 13 at 22.3256°N 114.1926°E, true heading 134.08°)
- 1998 corrections: no buildings on the Kai Tak site or the West Kowloon reclamation, and the Central Reclamation Phase III waterfront is harbour again
- Rebuild the assets with `python3 tools/fetch.py && python3 tools/build.py`

Data: © Lands Department, HKSAR Government (CSDI). Public housing estates: Housing Authority via DATA.GOV.HK, hosted by Esri China (Hong Kong) Ltd. Elevation: SRTM via AWS Terrain Tiles.

## MVP features
- Aircraft: 747-400, 777-200, A330-300, A340-300 (plus a delta-wing supersonic jet that only visits Plane Spotter), each with its own flight model (mass, wing area, thrust, Vref, roll rate, flap labels and limits)
- Sun, moon and time of day: a 24-hour clock (Dawn, Day, Dusk, Night presets) with the sun and moon placed for Hong Kong in early July 1998, a moon with phase, turning stars, twilight colours and lights that come on at sunset
- Day / night: lit windows, street lights, neon signs, runway, approach and lead-in strobe lights, PAPI
- Weather: clear, rain, typhoon, storm, low cloud, fog, plus a lightning toggle. Wind, gusts and turbulence affect the flight
- Landmarks: the checkerboard (aviation orange and white on two concrete retaining walls, with the striped mast and IGS lamp housings, from period photos), Kowloon Walled City (pre-1994, or the 1998 park), Bank of China Tower, Central Plaza, The Center, HSBC, Jardine House, Exchange Square, One IFC, Lippo Centre, Hopewell Centre, the Convention Centre extension, the TST Clock Tower, the Cultural Centre, Ocean Terminal, the Hung Hom Coliseum, the Kai Tak terminal and tower, Happy Valley Racecourse (floodlights, stand canopy, infield screen) Ocean Park (Waterfront Ferris wheel, Summit tower, Dragon-style coaster, Space Wheel and the cable car between the Waterfront and the Summit) and the Peak (the Peak Tower, the Peak Tram from Garden Road with two cars on one cable and four request stops, and the Peak Lookout)
- Traffic: about 6,900 vehicles on the real main roads and the Kowloon City streets: red Crown Comfort-style taxis with silver roofs (and green New Territories taxis), cream minibuses, double-decker buses, lorries and cars. In the harbour: container ships, Star Ferries, junks, tugs, and two liners at Ocean Terminal
- Kowloon City street scene: shop signs from period photos (新澧傢俬, 鳳香園, 金輝粥麵專家, 珍珍珠寶金行, 君皇酒樓, 黃珍珍 and more), signs hung across the streets, rooftop billboard frames, air-conditioners, laundry poles, bamboo scaffolding, and Nathan Road neon. Corporate logos are left out
- Public housing estates: the 145 Housing Authority estates in service by 1998 (101 of them inside the map), placed from the Housing Authority's estate list (location, block count, year of intake, block types). The nearest matching footprints are rebuilt as that estate's standard blocks: Harmony / Cruciform (cross plan), Trident (Y plan), Twin Tower (one tower taller), H blocks, and Old Slab, Slab and Small Household blocks, with floors by type (about 13-21 for Old Slab and Small Household, 24-28 for Twin Tower and H, 33-35 for Trident, 32-40 for Harmony, always under the approach clearance). Each estate has its own pastel scheme, stair and lift cores every eight bays, air-conditioners, and a lift motor room and water tank on every roof. Rebuild the list with `python3 tools/estates.py`
- Billboards and neon: about 170 giant hoardings on Kowloon rooftops and on poles beside the airport roads, floodlit at night and kept under the approach clearance, for eight invented brands (electronics, soft drink, whisky, western jeans and boots, colour film, a car, a watch, a night club). Three are glass-tube neon signs (watch, electronics, restaurant and night club) that glow at night, and the projecting neon on Nathan Road and the main roads has a glow halo. No real logos
- Spectator views: the Peak (on the Peak Tower rim, over the harbour), the top of Checkerboard Hill beside the IGS lamps, a Kowloon City street (the aircraft passes just overhead), Prince Edward Road beside the threshold, the roof of the Kai Tak car park with the plane-spotters, and a junk moored in the harbour off the runway
- The Garden Hill obstacle beacon in Sham Shui Po, and the sequenced lead-in strobes to touchdown
- Flight decks per type: the 747-400 (CRT glass, yokes, four thrust levers), the 777-200 (LCD glass, yokes) and the A330/A340 (sidesticks, ECAM, Airbus blue-grey). Live PFD, ND, EICAS/ECAM and checklist displays; the controls, levers, flap and gear handles move. The HUD overlay is optional
- Passenger cabin: a 3D interior with seats in each type's layout (3-4-3, 3-3-3, 2-4-2), bins, windows and passengers. Pick a row and side, then drag to look around
- Views: cockpit, exterior, control tower, four spectator spots, cabin seat
- Sound: engines, wind, rain, a touchdown thud with tyre chirp, brake squeal, reverser roar, gear hydraulics with a lock clunk, flap motor, gear-down rumble, thunder, GPWS
- Runway control: one movement at a time on the runway. The tower clears a landing, or a take-off, only when the runway is clear and will stay clear. Departures hold short and wait at the line-up point, arrivals that find the runway occupied 12 s before the threshold go around, and the AI timetable is planned with the same numbers (a departure is airborne at least 15 s before the next arrival crosses the threshold). In Free Flight the tower holds you until the runway is clear and nothing on final can reach the threshold before you are airborne, and arrivals go around for a player on the runway. The top bar shows the runway state (CLEAR, LANDING, TAKE-OFF, OCCUPIED). `python3 tools/test_runway.py` checks it.
- ATC radio: Hong Kong Approach (119.1) clears you for the IGS 13 approach and hands you to Kai Tak Tower (118.7), who clears you to land after you report the checkerboard. Calls follow your position and the live weather (wind, QNH, visibility), your readbacks are automatic, and other crews chatter on frequency. Free flight gets a takeoff clearance and the hand-off to Approach; Spectator plays the tower and approach traffic. Captions show on screen, voices use the browser's speech synthesis, and R turns the radio off
- Autopilot and autothrottle that fly the full approach and autoland
- High score table: every hand-flown IGS 13 landing is scored out of 100 and ranked by score: Captain (90+), First Officer (76+), Second Officer (60+), Flight Engineer (45+), Cadet. Saved in the browser with a callsign; an optional Cloudflare Worker + D1 database in `server/` shares one table (see `docs/highscores.md`)
- Map toggle: the corner map (a home screen option, the Map button or M; off until you turn it on) shows your aircraft and the live position of the other traffic, in the sim's own time: airborne aircraft in amber with their altitude in hundreds of feet, aircraft on the ground in grey. It is shown at double size on the home screen over the live demo (moving clear of the High scores panel when that is open) and in Plane Spotter (centred on the runway, with a dot where you are watching from), where M toggles it. It follows rewind and fast-forward, and is off in the cabin view
- Moving control surfaces: ailerons and elevators follow the controls, flaps follow the flap setting, spoilers deploy on touchdown (on the AI traffic too)
- Terminal and apron layout (from the Kai Tak chart): a pier at the north-west end of the apron, at right angles to the runway, with a main terminal block beyond its west end and a long multi-storey car park on its landside (north), joined by footbridges, with the clock and airport sign on its end wall and the spotters on its roof, and the maintenance area on the north-west edge beyond the terminal: three hangars with lit bays, a workshop tower, a fenced aircraft compound, a blast fence, floodlights, an interline building and a fuel tank farm. Eight nose-in stands run along the pier face, each with a jet bridge that swings out to the forward left door once an aircraft has docked and back before it leaves. Stands 1 to 6 are used by the turnarounds, and 7 and 8 always hold a parked aircraft
- Historical note: Kai Tak was always at or near capacity in 1998. The apron was often full or nearly full, with few empty parking bays, so the sim's stands and remote stands should be kept busy rather than empty
- Jet bridges and pushback: arrivals leave the runway by a link taxiway, join taxiway A, follow apron lane D3 to the stand's yellow lead-in line and stop at the bridge. A departure waits at the stand, the bridge retracts, a pushback tug drives out from its bay to the nose gear, pushes the aircraft straight back and turns it a quarter circle toward taxiway A, then drives back to its bay. In Plane Spotter and Free flight each stand has an arriving aircraft that docks and an identical aircraft that later departs, so it reads as a turnaround
- Apron markings: yellow taxi guidance lines along taxiway A and the three apron lanes (D3 at the stands, D2 and D1 behind it; corners drawn with the same curve the taxiing aircraft follow), numbered stands (1 to 8 nose-in at the pier, 11 to 19 remote stands on the far side of lane D2, 21 to 26 on its near side, 41 to 46 at the cargo terminal, 51 to 57 on the east apron and 71 to 81 on the south apron) with lead-in lines, nose-wheel stop bars and red stand boxes, and curved lead-on lines and runway holding positions at both ends of taxiway A. The stand numbers beyond 8 are the sim's own. Arrivals taxi in along the lines, and the markings dim at night
- Tarmac only: aircraft on the ground stay on the grey tarmac (the runway, taxiway A, the six link taxiways and the apron) and never cross the green grass. Runway 13 arrivals leave by the link that leans toward the 31 end and Runway 31 arrivals by the one that leans toward the 13 end, and round pads widen the tightest corners so the nose wheel stays on the tarmac. Your own aircraft needs all three wheels on the tarmac: leaving it at more than about 12 kt is a runway excursion, and slower than that it stops at the edge. A touchdown with a wheel off the tarmac counts as landing off the runway. `tools/test_landings.py` checks every ground position of the other traffic
- Airfield signs and markings (FAA AIM chapter 2, section 3): touchdown-zone bars to 3,000 ft, 120 ft/80 ft centre-line stripes, link taxiways B1 to B6 (the names are the sim's own) with a yellow centre line, enhanced dashes and a four-line runway holding position, a double yellow edge line along taxiway A, and mandatory (white on red), location (yellow on black), direction and destination (black on yellow) and runway distance remaining (white on black, per 1,000 ft) signs. The signs are lit from inside, so they stay readable at night
- Airport ground vehicles: catering trucks whose boxes lift to the door of a docked aircraft, baggage tractors towing loaded carts under the wing, cargo main-deck loaders, container dolly trains, forklifts and container trucks at the cargo terminal (stands 41 to 46, with scheduled 747-400F and A300-600F freighters), a lorry on the service road at the far end of the apron, and a fire station with crash tenders and a rescue vehicle. They run on the sim clock, so rewind and fast-forward work. At night they show headlights, tail lamps and beacons
- Extra parking bays (from Technocratic Aviation's unofficial Kai Tak plan): a second row of stands, 21 to 26, between lanes D3 and D2, nose toward the terminal; an east apron past the maintenance hangars, out to the airport's east boundary road, with stands 51 to 57 nose-in toward the boundary; and the south apron stands 71 to 81 are nose-in toward the far edge, tail to taxiway B4. Each holds a parked aircraft or stands empty, and the interline building sits at the north-east end of the cargo terminal
- Remote stands and apron buses: five aircraft park nose-in on remote stands 11 to 19 (no jet bridge) with the tail toward lane D2, and five apron buses each run from the bus gate at the root of the pier, in front of the noses and down beside their aircraft to the forward left door, wait there and drive back. They only run when no jet bridge is free (all eight contact stands are taken)
- Flight information board: an old split-flap board of every arrival and departure (made-up airlines and flight numbers, 1998 destinations, Hong Kong clock, status read from the aircraft). It is on the home screen and in Plane Spotter (B or the Flights button toggles it in both), clatters like the real thing when letters change (a button on the board switches the sound on or off), and follows the English / Cantonese button
- Other airliners: a 747 landing two minutes ahead of you, an A340 following you in on the IGS, departures pushed back from the bridges, taxiing out and climbing over Kowloon Bay, two aircraft in the hold west of the harbour, and apron movements
- Zoom 1×, 2×, 4×, 8×, 16× (I / O); time 1×, 2×, 4×, 8× (T); jump back or forward 10 seconds ([ / ]), including back from a crash
- GPWS callouts and warnings (gear and flap calls only while descending, so take-offs stay quiet), engine, wind, rain and thunder sound

## Demo reel
The home screen shows the live sim of the airport in the background, with a 58-second muted demo reel (`assets/video/reel.mp4`, with a WebM fallback) looping in a framed inset beside the title. It's rendered from the sim itself: a 747 at night, an A330 breaking out of low cloud, gear and flaps deploying, the turn at the checkerboard, ailerons over Kowloon City, a 747 low over a Kowloon City street, a 777 crabbing in a typhoon, an A340 in a lightning storm, and touchdowns in rain and at night. It pauses during play; reduced-motion users see the poster frame.

## Site
- Start screen has a Blog menu button (top left) linking to /blog/
- Blog at https://flykaitak.com/blog/ (every feature and fix gets a post; see docs/blog.md)
- Merch shop at https://flykaitak.com/shop/ (Shop button and Kai Tak merch card on the start screen; see docs/shop.md)
- Contact: contact@flykaitak.com
- "Another Mal Gordon project" links to https://malgordon.com
- The "Buy me a coffee" button ($5 AUD) opens a Stripe Payment Link, set in `STRIPE_LINK` in `index.html`

## Modes
- **Take-off lesson**: a guided take-off for people who have never flown. A coach panel gives one step at a time (full thrust, stay on the centre line, rotate at 150 kt, gear up, flaps up, climb to 2,000 ft, autopilot), with a live meter for each step, plain-language warnings (drifting off the centre line, nose too high or low, stall) and a highlight on the control to use. It moves on by itself when you do the step; Skip lesson hands you free flight at any time. It ends with a choice to keep flying or start the Landing lesson
- **Landing lesson**: the same coach on the IGS 13 approach, hand-flown with the guide hoops on. Nine steps: gear down, landing flaps, hold the approach speed (Vref + 10 kt), follow the hoops, the 47° right turn at the checkerboard, final, flare, brake to a stop. Live meters (speed, distance left or right of the line, turn to go, height, descent rate, ground speed), warnings (too slow or fast, below or above the glidepath, off the line, bank, stall, drifting after touchdown) and a lesson tip on the result card after a crash. Lesson landings are not ranked on the high score table
- **IGS 13 approach**: the original game. Start on the IGS at 3,100 ft and land.
- **Runway 31 approach**: the easterly approach. Start about 8 NM out over the sea at 2,700 ft, heading 314, fly through the Lei Yue Mun gap and land on Runway 31 (own approach lights, PAPI, radio calls and traffic; a Lei Yue Mun spotter view).
- **Free flight**: start lined up on Runway 13. Take off over Kowloon Bay and fly anywhere; landings are graded but the flight carries on (touch-and-go with full thrust). The autopilot holds heading, altitude and speed once airborne.
- **Runway 31 take-off**: free flight lined up on Runway 31 at the Kowloon Bay end, pointing at Kowloon City. Climb and turn left; radio calls and traffic follow Runway 31.
- **Spotter · Runway 31**: Plane Spotter with Runway 31 in use; the Lei Yue Mun spectator view (C cycles to it) follows the jet nearest to it.
- **Spotter · Concorde special**: Plane Spotter with a rare supersonic delta-wing visitor (nose droops for landing) that lands on the hour, parks at stand 6 and departs about 10 minutes later. The flight board lists it in gold as a special (made-up charter, no real airline). Plane Spotter on its own shows the visit once an hour too.
- **Plane Spotter**: no flying. A continuous schedule of arrivals every 100 s with departures in between, plus aircraft in the hold. Watch from the car park roof, Prince Edward Road, a Kowloon City street, a harbour junk or the tower, or follow the active jet.

## Controls
| Key | Action |
|---|---|
| ↑ ↓ / W S | Pitch (↑ pushes the nose down) |
| ← → / A D | Roll / nosewheel steering |
| E Q / = − | Thrust |
| G | Gear |
| F V | Flaps extend / retract |
| C | Cycle view |
| Drag | Look around (cockpit, cabin) / orbit (exterior) |
| Z | Autopilot |
| R | ATC radio on/off |
| N, P | Time of day (Dawn, Day, Dusk, Night), pause |
| I / O, mouse wheel | Zoom in / out (scroll up zooms in, scroll down zooms out) |
| B | Flight information board on/off (home screen and Plane Spotter) |
| T | Time speed |
| [ / ] | Back / forward 10 s |
| K | Cockpit panel on/off |

The on-screen yoke works with touch or a mouse and is inverted like a real control column: drag down to pull the nose up, drag up to push it down. On touch screens, use the on-screen yoke, thrust lever and gear/flap buttons. Landscape is recommended: on phones Begin descent goes full screen and asks for landscape where the browser allows it. The toolbar is one row with a More drawer for the rest.

## Shipping and water
- About 140 vessels: Star Ferries on four routes, freighters, container ships, ocean liners, junks, yachts, marine police launches, tugs, walla-walla launches, and ships at anchor. Moving ships follow one-way, keep-right lanes along the charted fairways and traffic separation schemes (Victoria Harbour and Lei Yue Mun, Ma Wan and Western Fairway, Castle Peak, Rambler Channel, East Lamma Channel) and never turn round; about half the fleet is moored or at anchor with anchor lights only. All carry navigation lights (masthead, stern, red port, green starboard), and police launches flash blue. Boats pass right alongside the runway seawall but never enter the inlet under the taxiways to the south apron
- Water shader: wind-driven waves and whitecaps (calm on clear days, white-streaked in a typhoon), deep and shallow colour from distance to shore, surf on the sea walls, sky reflection with sun glitter, and city glow at night. V-shaped wakes
- Red obstruction lights on the rooftops of tall buildings, some flashing under the approach

## Analytics
Google Analytics 4 with game events. See docs/analytics.md.

## Roadmap
- Learn to fly, next: ground and taxi lessons, and a Runway 31 landing lesson
- ATC radio, next: ground and taxi calls, more voices, crews that match the AI traffic
- More aircraft: 747-200/300, 767-300, MD-11, A300-600, A320, 737-300, L-1011, DC-10
- Higher-fidelity terrain and coastline, more hand-built landmarks
