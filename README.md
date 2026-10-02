# Fly Kai Tak

A browser flight simulator for the Runway 13 IGS approach into Hong Kong Kai Tak, set in 1998.

You start descending over Tsing Yi at about 3,100 ft on the instrument guidance system, heading 088. Fly toward the checkerboard on the hill at Kowloon Tsai, make the 47° right turn low over Kowloon City, and land on a runway that ends in Kowloon Bay. Each run ends in a landing (graded) or a crash (with the cause).

Play: open `index.html` in a browser. It needs no build step, and Three.js r128 loads from cdnjs.

## MVP features
- Aircraft: 747-400, 777-200, A330-300, A340-300, each with its own flight model (mass, wing area, thrust, Vref, roll rate, flap labels and limits)
- Day / night: lit windows, street lights, neon signs, runway, approach and lead-in strobe lights, PAPI
- Weather: clear, rain, typhoon, storm, low cloud, fog, plus a lightning toggle. Wind, gusts and turbulence affect the flight
- Landmarks: the checkerboard, Kowloon Walled City (pre-1994, or the 1998 park), Bank of China Tower, Central Plaza, The Center, HSBC, Jardine House, Exchange Square, One IFC, Lippo Centre, Hopewell Centre, the Convention Centre extension, the TST Clock Tower, the Cultural Centre, Ocean Terminal, the Hung Hom Coliseum, and the Kai Tak terminal and tower
- Traffic: cars, red taxis and buses on the main roads; container ships, Star Ferries, junks and tugs in the harbour
- Views: cockpit (HUD, flight path vector, IGS deviation), exterior, control tower, and a passenger cabin window (pick a row and side; the computer flies)
- Autopilot and autothrottle that fly the full approach and autoland
- GPWS callouts and warnings, engine, wind, rain and thunder sound

## Controls
| Key | Action |
|---|---|
| ↑ ↓ / W S | Pitch (↑ pushes the nose down) |
| ← → / A D | Roll / nosewheel steering |
| E Q / = − | Thrust |
| G | Gear |
| F V | Flaps extend / retract |
| C | Cycle view |
| Z | Autopilot |
| N, P | Day/night, pause |

On touch screens, use the on-screen yoke, thrust lever and gear/flap buttons.

## Roadmap
- ATC radio: Kai Tak approach and tower instructions, other crews on frequency
- More aircraft: 747-200/300, 767-300, MD-11, A300-600, A320, 737-300, L-1011, DC-10
- Higher-fidelity terrain and coastline, more hand-built landmarks
