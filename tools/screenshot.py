#!/usr/bin/env python3
"""Take screenshots of the sim for blog posts.

Usage:  python3 tools/screenshot.py shots.json [out_dir]

Serves the repo on localhost, opens it in headless Chromium (software WebGL), starts a flight with the
sim's own test hooks (window.__kt) and saves a 1600x900 JPG per shot. Default out_dir: assets/blog/shots.

shots.json is a list of shots:
  {"name": "night", "start": {"ac": "b744", "ap": true, "game": "approach", "wx": "clear", "night": true, "deck": true},
   "run": 175, "view": "cockpit", "frames": 14, "js": "window.__kt.drawDisplays()"}

  start   settings passed to __kt.start. The cockpit (deck) is OFF by default for screenshots; set "deck": true
          only for a shot that is meant to show the cockpit. (ac: b744|b772|a333|a343, game: approach|free|watch,
          wx: clear|rain|typhoon|storm|lowcloud|fog, night, deck, lightning, ap ...)
  run     seconds of simulation to advance first (the approach turn is at about 190 s,
          the Kowloon City street camera sees the jet overhead at about 204 s)
  view    cockpit, chase, tower, street, ped, carpark, boat, checker, cabin
  cam     optional free camera [x, y, z, targetX, targetY, targetZ] in sim metres (x east, z south)
  clean   true hides all UI overlays so the shot is only the 3D scene
  frames  frames to render before the shot (about 14 settles the scene; 30 also draws the cockpit displays)
  js      optional JavaScript to run before the shot

Needs: pip install playwright pillow (Chromium is already present in the Claude workspace).
"""
import http.server
import io
import json
import pathlib
import socketserver
import sys
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(ROOT), **k)

        def log_message(self, *a):
            pass

    class Srv(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

        def handle_error(self, *a):  # the browser drops connections it no longer needs; ignore
            pass

    srv = Srv(("127.0.0.1", 0), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    shots = json.load(open(sys.argv[1]))
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "assets/blog/shots"
    out.mkdir(parents=True, exist_ok=True)
    srv = serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                                    "--ignore-gpu-blocklist", "--no-sandbox"])
        pg = b.new_page(viewport={"width": 1600, "height": 900})
        pg.add_init_script("window.__capture=true")  # the sim stops its own loop; we step frames below
        pg.goto(url, wait_until="load")
        pg.wait_for_function("window.__kt!==undefined", timeout=60000)
        pg.wait_for_timeout(8000)  # map data and fonts
        for s in shots:
            start = {"deck": False, **s["start"]}  # rule: cockpit off for screenshots unless a shot sets deck true
            pg.evaluate("s=>window.__kt.start(s)", start)
            if s.get("run"):
                pg.evaluate("s=>window.__kt.run(s)", s["run"])
            if s.get("view"):
                pg.evaluate("v=>window.__kt.setView(v)", s["view"])
            if s.get("cam"):  # free camera [x, y, z, targetX, targetY, targetZ] in sim metres (x east, z south)
                pg.evaluate("c=>{window.__kt.freeCam=c}", s["cam"])
            if s.get("clean"):  # hide every overlay: just the 3D scene
                pg.evaluate("()=>{document.querySelectorAll('body>*:not(#gl)').forEach(e=>{if(e.tagName!=='SCRIPT')e.style.display='none'})}")
            if s.get("js"):
                pg.evaluate(s["js"])
            for i in range(s.get("frames", 14)):
                pg.evaluate("t=>window.__kt.frame(t)", 1000 + i * 33)
            pg.wait_for_timeout(300)
            im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            dest = out / f"{s['name']}.jpg"
            im.save(dest, quality=82, optimize=True, progressive=True)
            print("saved", dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest, flush=True)
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
