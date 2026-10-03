# Fly Kai Tak

A browser flight simulator for the Runway 13 IGS approach into Hong Kong Kai Tak, set in 1998.

You start descending over Tsing Yi at about 3,100 ft on the instrument guidance system, heading 088. Fly toward the checkerboard on the hill at Kowloon Tsai, make the 47° right turn low over Kowloon City, and land on a runway that ends in Kowloon Bay. Each run ends in a landing (graded) or a crash (with the cause).

Play at https://flykaitak.com, or serve the folder with any static web server (`python3 -m http.server`) and open `index.html`. Opening the file directly won't work because the map data is fetched.

## Real Hong Kong
- The aerial imagery, coastline, main roads and about 24,000 building footprints come from the Hong Kong Lands Department's open data. Terrain is SRTM elevation with building bumps filtered out
- The runway is fitted to the old Kai Tak strip (threshold 13 at 22.3256°N 114.1926°E, true heading 134.08°)
- 1998 corrections: no buildings on the Kai Tak site or the West Kowloon reclamation, and the Central Reclamation Phase III waterfront is harbour again
- Rebuild the assets with `python3 tools/fetch.py && python3 tools/build.py`

Data: © Lands Department, HKSAR Government (CSDI). Elevation: SRTM via AWS Terrain Tiles.

## MVP features
- Aircraft: 747-400, 777-200, A330-300, A340-300, each with its own flight model (mass, wing area, thrust, Vref, roll rate, flap labels and limits)
- Day / night: lit windows, street lights, neon signs, runway, approach and lead-in strobe lights, PAPI
- Weather: clear, rain, typhoon, storm, low cloud, fog, plus a lightning toggle. Wind, gusts and turbulence affect the flight
- Landmarks: the checkerboard (red and white on two concrete retaining walls, with the striped mast and IGS lamp housings, from period photos), Kowloon Walled City (pre-1994, or the 1998 park), Bank of China Tower, Central Plaza, The Center, HSBC, Jardine House, Exchange Square, One IFC, Lippo Centre, Hopewell Centre, the Convention Centre extension, the TST Clock Tower, the Cultural Centre, Ocean Terminal, the Hung Hom Coliseum, the Kai Tak terminal and tower, Happy Valley Racecourse (floodlights, stand canopy, infield screen) Ocean Park (Waterfront Ferris wheel, Summit tower, Dragon-style coaster, Space Wheel and the cable car between the Waterfront and the Summit) and the Peak (the Peak Tower, the Peak Tram from Garden Road with two cars on one cable and four request stops, and the Peak Lookout)
- Traffic: about 6,900 vehicles on the real main roads and the Kowloon City streets: red Crown Comfort-style taxis with silver roofs (and green New Territories taxis), cream minibuses, double-decker buses, lorries and cars. In the harbour: container ships, Star Ferries, junks, tugs, and two liners at Ocean Terminal
- Kowloon City street scene: shop signs from period photos (新澧傢俬, 鳳香園, 金輝粥麵專家, 珍珍珠寶金行, 君皇酒樓, 黃珍珍 and more), signs hung across the streets, rooftop billboard frames, air-conditioners, laundry poles, bamboo scaffolding, and Nathan Road neon. Corporate logos are left out
- Billboards and neon: about 170 giant hoardings on Kowloon rooftops and on poles beside the airport roads, floodlit at night and kept under the approach clearance, for eight invented brands (electronics, soft drink, whisky, western jeans and boots, colour film, a car, a watch, a night club). Three are glass-tube neon signs (watch, electronics, restaurant and night club) that glow at night, and the projecting neon on Nathan Road and the main roads has a glow halo. No real logos
- Spectator views: the Peak (on the Peak Tower rim, over the harbour), the top of Checkerboard Hill beside the IGS lamps, a Kowloon City street (the aircraft passes just overhead), Prince Edward Road beside the threshold, the roof of the Kai Tak car park with the plane-spotters, and a junk moored in the harbour off the runway
- The Garden Hill obstacle beacon in Sham Shui Po, and the sequenced lead-in strobes to touchdown
- Flight decks per type: the 747-400 (CRT glass, yokes, four thrust levers), the 777-200 (LCD glass, yokes) and the A330/A340 (sidesticks, ECAM, Airbus blue-grey). Live PFD, ND, EICAS/ECAM and checklist displays; the controls, levers, flap and gear handles move. The HUD overlay is optional
- Passenger cabin: a 3D interior with seats in each type's layout (3-4-3, 3-3-3, 2-4-2), bins, windows and passengers. Pick a row and side, then drag to look around
- Views: cockpit, exterior, control tower, four spectator spots, cabin seat
- Sound: engines, wind, rain, a touchdown thud with tyre chirp, brake squeal, reverser roar, gear hydraulics with a lock clunk, flap motor, gear-down rumble, thunder, GPWS
- ATC radio: Hong Kong Approach (119.1) clears you for the IGS 13 approach and hands you to Kai Tak Tower (118.7), who clears you to land after you report the checkerboard. Calls follow your position and the live weather (wind, QNH, visibility), your readbacks are automatic, and other crews chatter on frequency. Free flight gets a takeoff clearance and the hand-off to Approach; Spectator plays the tower and approach traffic. Captions show on screen, voices use the browser's speech synthesis, and R turns the radio off
- Autopilot and autothrottle that fly the full approach and autoland
- High score table: every hand-flown IGS 13 landing is scored out of 100 and ranked by score: Captain (90+), First Officer (76+), Second Officer (60+), Flight Engineer (45+), Cadet. Saved in the browser with a callsign; an optional Cloudflare Worker + D1 database in `server/` shares one table (see `docs/highscores.md`)
- Moving control surfaces: ailerons and elevators follow the controls, flaps follow the flap setting, spoilers deploy on touchdown (on the AI traffic too)
- Jet bridges and pushback: six nose-in stands along the terminal, each with a jet bridge that swings out to the forward left door once an aircraft has docked and back before it leaves. Arrivals taxi down the stand's yellow lead-in line and stop at the bridge. A departure waits at the stand, the bridge retracts, a pushback tug drives out from its bay to the nose gear, pushes the aircraft straight back and turns it to face the runway, then drives back to its bay. In Plane Spotter and Free flight each stand has an arriving aircraft that docks and an identical aircraft that later departs, so it reads as a turnaround
- Apron markings: yellow taxi guidance lines along taxiway A, the east link and the apron lane (corners drawn with the same curve the taxiing aircraft follow), numbered stands (1 to 6 nose-in at the terminal's jet bridges, 7 at the end of the east link, 11 to 15 drive-through on the runway side of the lane) with lead-in lines, nose-wheel stop bars and red stand boxes, and curved lead-on lines and runway holding positions at both ends of taxiway A. The stand numbers are the sim's own. Arrivals taxi in along the lines, and the markings dim at night
- Airport ground vehicles: catering trucks whose boxes lift to the door of a docked aircraft, baggage tractors towing loaded carts under the wing, container and box freight trucks around a cargo shed, a lorry on the service road behind the terminal, and a fire station with crash tenders and a rescue vehicle. They run on the sim clock, so rewind and fast-forward work. At night they show headlights, tail lamps and beacons
- Other airliners: a 747 landing two minutes ahead of you, an A340 following you in on the IGS, departures pushed back from the bridges, taxiing out and climbing over Kowloon Bay, two aircraft in the hold west of the harbour, and apron movements
- Zoom 1×, 2×, 4×, 8×, 16× (I / O); time 1×, 2×, 4×, 8× (T); jump back or forward 10 seconds ([ / ]), including back from a crash
- GPWS callouts and warnings (gear and flap calls only while descending, so take-offs stay quiet), engine, wind, rain and thunder sound

## Demo reel
The home screen shows the live sim of the airport in the background, with a 58-second muted demo reel (`assets/video/reel.mp4`, with a WebM fallback) looping in a framed inset beside the title. It's rendered from the sim itself: a 747 at night, an A330 breaking out of low cloud, gear and flaps deploying, the turn at the checkerboard, ailerons over Kowloon City, a 747 low over a Kowloon City street, a 777 crabbing in a typhoon, an A340 in a lightning storm, and touchdowns in rain and at night. It pauses during play; reduced-motion users see the poster frame.

## Site
- Start screen has a Blog menu button (top left) linking to /blog/
- Blog at https://flykaitak.com/blog/ (every feature and fix gets a post; see docs/blog.md)
- Contact: contact@flykaitak.com
- "Another Mal Gordon project" links to https://malgordon.com
- The "Buy me a coffee" button ($5 AUD) opens a Stripe Payment Link, set in `STRIPE_LINK` in `index.html`

## Modes
- **Take-off lesson**: a guided take-off for people who have never flown. A coach panel gives one step at a time (full thrust, stay on the centre line, rotate at 150 kt, gear up, flaps up, climb to 2,000 ft, autopilot), with a live meter for each step, plain-language warnings (drifting off the centre line, nose too high or low, stall) and a highlight on the control to use. It moves on by itself when you do the step; Skip lesson hands you free flight at any time. It ends with a choice to keep flying or try the IGS 13 approach
- **IGS 13 approach**: the original game. Start on the IGS at 3,100 ft and land.
- **Runway 31 approach**: the easterly approach. Start about 8 NM out over the sea at 2,700 ft, heading 314, fly through the Lei Yue Mun gap and land on Runway 31 (own approach lights, PAPI, radio calls and traffic; a Lei Yue Mun spotter view).
- **Free flight**: start lined up on Runway 13. Take off over Kowloon Bay and fly anywhere; landings are graded but the flight carries on (touch-and-go with full thrust). The autopilot holds heading, altitude and speed once airborne.
- **Runway 31 take-off**: free flight lined up on Runway 31 at the Kowloon Bay end, pointing at Kowloon City. Climb and turn left; radio calls and traffic follow Runway 31.
- **Spotter · Runway 31**: Plane Spotter with Runway 31 in use; the Lei Yue Mun spectator view (C cycles to it) follows the jet nearest to it.
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
| N, P | Day/night, pause |
| I / O, mouse wheel | Zoom in / out (scroll up zooms in, scroll down zooms out) |
| T | Time speed |
| [ / ] | Back / forward 10 s |
| K | Cockpit panel on/off |

The on-screen yoke works with touch or a mouse and is inverted like a real control column: drag down to pull the nose up, drag up to push it down. On touch screens, use the on-screen yoke, thrust lever and gear/flap buttons. Landscape is recommended: on phones Begin descent goes full screen and asks for landscape where the browser allows it. The toolbar is one row with a More drawer for the rest.

## Shipping and water
- About 134 vessels: Star Ferries on four routes, freighters, container ships, moving and berthed ocean liners, junks, yachts, marine police launches, tugs, walla-walla launches, and ships at anchor. All carry navigation lights (masthead, stern, red port, green starboard), and police launches flash blue
- Water shader: wind-driven waves and whitecaps (calm on clear days, white-streaked in a typhoon), deep and shallow colour from distance to shore, surf on the sea walls, sky reflection with sun glitter, and city glow at night. V-shaped wakes
- Red obstruction lights on the rooftops of tall buildings, some flashing under the approach

## Analytics
Google Analytics 4 with game events. See docs/analytics.md.

## Roadmap
- Learn to fly, next: a landing lesson that follows the take-off lesson
- ATC radio, next: ground and taxi calls, more voices, go-around instructions, crews that match the AI traffic
- More aircraft: 747-200/300, 767-300, MD-11, A300-600, A320, 737-300, L-1011, DC-10
- Higher-fidelity terrain and coastline, more hand-built landmarks
