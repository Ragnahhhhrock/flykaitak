# Fly Kai Tak · Claude Project setup

## Project name
Fly Kai Tak

## Project description
Browser flight simulator of the 1998 Runway 13 IGS approach into Hong Kong Kai Tak. Live at flykaitak.com.

## Project instructions (paste into "Instructions")
You are helping build Fly Kai Tak, a browser flight simulator of the 1998 Runway 13 IGS approach into Hong Kong's Kai Tak airport.

- Code lives in GitHub: Ragnahhhhrock/flykaitak (branch main), served by GitHub Pages at https://flykaitak.com (DNS on Cloudflare). Commit and push every update to that repo.
- Stack: one index.html with Three.js r128 from cdnjs, no build step. Map data in assets/ is built by tools/fetch.py and tools/build.py from Hong Kong Lands Department open data (aerial imagery, basemap) and SRTM elevation. Credit "© Lands Department, HKSAR Government".
- Local frame: metres from the Runway 13 threshold (22.32558N 114.19262E), x east, z south. Runway true heading 134.08°, 3,390 m. IGS course 088°, glidepath 3.1°, 47° right turn over Kowloon City.
- Period accuracy: 1998. No Two IFC (2003) or Cheung Kong Center (1999). Kowloon Walled City is a pre-1994 option. West Kowloon reclamation was empty.
- No real airline names, logos or liveries; no brand logos on in-world signs. Colours may be inspired by the era's liveries.
- Design system: the "Fly Kai Tak" Design System artifact (night cockpit UI, livery-inspired greens, Kai Tak checkerboard orange, B612 / B612 Mono / Noto Serif TC). Follow it for any UI, web or marketing work.
- Test every change: the autopilot must still land in all weather presets, and flying with no input must still crash.
- Blog: every new feature or bug fix gets a post at /blog/<slug>/ with screenshots, metadata and share buttons. See docs/blog.md. Push every update to main without asking.
- Keep explanations brief and to the point.

## Knowledge to add
- This repo's README.md and docs/claude-project.md
- Reference photos: Kowloon City street scenes under the approach, Star Ferry, 1997 Hong Kong skyline, Hong Kong taxis, 1990s airliner liveries at Kai Tak
- Links: the design system artifact, the playable artifact, https://flykaitak.com

## Roadmap
0. Learn to fly: the take-off lesson has shipped. Next: a landing lesson for first-time pilots
1. ATC radio (first version shipped: approach/tower calls, captions, R toggle). Next: ground and taxi calls, more voices, go-arounds, crews matched to the AI traffic
2. More aircraft: 747-200/300, 767-300, MD-11, A300-600, A320, 737-300, L-1011, DC-10
3. Runway 31 approach, traffic and free-flight take-off (done), Plane Spotter (done)
4. Higher-detail Kowloon City blocks and more hand-built landmarks
5. Mobile performance pass
