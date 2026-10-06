#!/usr/bin/env python3
"""Render the Fly Kai Tak social reel (YouTube / Instagram / Facebook) from the sim itself.

Usage:
  python3 tools/reel.py render yt  [--out DIR] [--shots a,b]     1920x1080 (YouTube, also used for Facebook)
  python3 tools/reel.py render ig  [--out DIR] [--shots a,b]     1080x1920 (Instagram Reels)
  python3 tools/reel.py scout yt   [--out DIR] [--shots a,b]     3 stills per shot, to check framing

Every shot is a continuous take of the sim (cockpit deck off, all overlays hidden). Only exterior and
cockpit-windscreen cameras are used: no view from inside the passenger cabin.

The sim runs in software WebGL here, where one frame costs about 4 s whatever the size. So the sim is stepped
at 24 Hz but only every second step is drawn (a 12 fps render); tools/reel_assemble.sh turns each shot into
24 fps with ffmpeg's motion interpolation. Frames land in OUT/<format>/<shot>/f00001.jpg. A shot with a
DONE marker is skipped, so an interrupted render resumes at the next shot.
Needs: pip install playwright pillow (Chromium is already present in the Claude workspace).
"""
import argparse
import base64
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import screenshot as sc  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = sc.ROOT
FORMATS = {"yt": (1920, 1080), "ig": (1080, 1920)}
STEP_MS = 1000 / 24          # one sim step (the sim caps a frame at 50 ms, so 24 Hz is safe)
DRAW_EVERY = 2               # draw every 2nd step: 12 fps frames, interpolated to 24 later
SETTLE_STEPS = 12            # undrawn steps after the camera is set, so the chase camera settles

# One entry per take. dur is in seconds of finished (24 fps) video. run = seconds of sim to skip first.
# start = options for window.__kt.start. look = chase-camera orbit (yaw, pitch, dist). ig = overrides for the vertical cut.
SHOTS = [
    {"name": "01-night-final", "dur": 5, "run": 96, "view": "chase", "start": {"ac": "b744", "wx": "clear", "night": True},
     "look": {"orbitYaw": 0.3, "orbitPitch": 0.1, "dist": 0.7}, "sweep": {"orbitYaw": [0.3, 1.0]}},
    {"name": "02-low-cloud", "dur": 5, "run": 166, "view": "chase", "start": {"ac": "a333", "wx": "lowcloud"},
     "look": {"orbitYaw": -0.5, "orbitPitch": 0.0, "dist": 0.8}, "sweep": {"orbitYaw": [-0.5, -0.1]}},
    {"name": "03-gear-down", "dur": 4, "run": 104, "view": "chase", "start": {"ac": "b744", "wx": "clear"},
     "look": {"orbitYaw": 0.9, "orbitPitch": -0.15, "dist": 0.55}, "sweep": {"orbitYaw": [0.9, 1.5]}},
    {"name": "04-turn-over-kowloon", "dur": 6, "run": 188, "view": "chase", "start": {"ac": "a343", "wx": "clear"},
     "look": {"orbitYaw": 1.1, "orbitPitch": 0.15, "dist": 0.7}, "sweep": {"orbitYaw": [1.1, 0.5]}},
    {"name": "05-kowloon-street", "dur": 4, "run": 202.5, "view": "street", "start": {"ac": "b744", "wx": "clear"}},
    {"name": "06-overhead-pass", "dur": 5, "run": 204, "view": "ped", "start": {"ac": "b744", "wx": "clear"}},
    {"name": "07-touchdown", "dur": 5, "run": 237, "view": "chase", "start": {"ac": "b744", "wx": "clear"},
     "look": {"orbitYaw": 0.9, "orbitPitch": 0.02, "dist": 0.5}, "sweep": {"orbitYaw": [0.9, 1.4]},
     "ig": {"look": {"orbitYaw": 0.9, "orbitPitch": 0.05, "dist": 0.75}}},
    {"name": "08-typhoon-crab", "dur": 5, "run": 258, "view": "chase", "start": {"ac": "b772", "wx": "typhoon"},
     "look": {"orbitYaw": 0.0, "orbitPitch": 0.12, "dist": 0.7}},
    {"name": "09-lightning-storm", "dur": 5, "run": 215, "view": "chase",
     "start": {"ac": "a343", "wx": "storm", "lightning": True},
     "look": {"orbitYaw": -0.6, "orbitPitch": 0.1, "dist": 0.8}},
    {"name": "10-night-rain-touchdown", "dur": 5, "run": 232, "view": "chase",
     "start": {"ac": "b744", "wx": "rain", "night": True},
     "look": {"orbitYaw": 1.2, "orbitPitch": 0.05, "dist": 0.5}, "sweep": {"orbitYaw": [1.2, 1.7]}},
    {"name": "11-night-runway-lights", "dur": 4, "run": 226, "view": "cockpit",
     "start": {"ac": "b744", "wx": "rain", "night": True}},
]
IG_CHASE_DIST = 1.7   # the vertical frame is narrow, so chase cameras pull back to keep the wings in

INIT_JS = """
window.__capture=true;
(()=>{const names=['drawElements','drawArrays','drawElementsInstanced','drawArraysInstanced','drawRangeElements'];
 for(const C of [window.WebGLRenderingContext,window.WebGL2RenderingContext]){if(!C)continue;
  for(const n of names){const o=C.prototype[n];if(!o)continue;C.prototype[n]=function(...a){if(window.__skipDraw)return;return o.apply(this,a)}}}})();
"""
HIDE_JS = "()=>{document.querySelectorAll('body>*:not(#gl)').forEach(e=>{if(e.tagName!=='SCRIPT')e.style.display='none'})}"
STEP_JS = """([t,draw,q])=>{
  window.__skipDraw=!draw;window.__kt.frame(t);window.__skipDraw=false;
  return draw?document.getElementById('gl').toDataURL('image/jpeg',q):null}"""


def shot_cfg(shot, fmt):
    cfg = dict(shot)
    cfg.update(shot.get(fmt, {}))
    if fmt == "ig" and cfg["view"] == "chase":
        cfg["look"] = {**cfg["look"], "dist": cfg["look"]["dist"] * IG_CHASE_DIST}
    return cfg


def open_page(p, size):
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                                "--ignore-gpu-blocklist", "--no-sandbox"])
    pg = b.new_page(viewport={"width": size[0], "height": size[1]})
    pg.add_init_script(INIT_JS)
    return b, pg


def setup_shot(pg, cfg):
    # CFG persists between starts, so reset everything a shot might set; no cockpit deck, no guide hoops
    start = {"deck": False, "guide": False, "night": False, "lightning": False, "ap": True, "game": "approach",
             **cfg["start"]}
    # readSetup() reads these two from the setup checkboxes, so set them there
    pg.evaluate("o=>{document.getElementById('optGuide').checked=false;document.getElementById('optLightning').checked=!!o.lightning}", start)
    pg.evaluate("s=>window.__kt.start(s)", start)
    if cfg.get("run"):
        pg.evaluate("s=>window.__kt.run(s)", cfg["run"])
    pg.evaluate("v=>window.__kt.setView(v)", cfg["view"])
    if cfg.get("look"):
        pg.evaluate("l=>Object.assign(window.__kt.look,l)", cfg["look"])
    pg.evaluate("()=>{window.__camFn=null;window.__kt.freeCam=null}")
    if cfg.get("js"):
        pg.evaluate(cfg["js"])
    pg.evaluate(HIDE_JS)


def run_shot(pg, cfg, now, out_dir, scout=False):
    """Step one take. Returns the new clock. Writes f00001.jpg... (or s0/s1/s2.jpg when scouting)."""
    setup_shot(pg, cfg)
    n_steps = int(round(cfg["dur"] * 24))
    for _ in range(SETTLE_STEPS):
        now += STEP_MS
        pg.evaluate(STEP_JS, [now, False, 0])
    picks = {0, n_steps // 2, n_steps - 1} if scout else None
    k = 0
    for i in range(n_steps):
        now += STEP_MS
        if cfg.get("sweep"):  # a slow camera move: orbitYaw / orbitPitch / dist go linearly from a to b over the take
            f = i / max(1, n_steps - 1)
            pg.evaluate("l=>Object.assign(window.__kt.look,l)", {k: v[0] + (v[1] - v[0]) * f for k, v in cfg["sweep"].items()})
        draw = (i in picks) if scout else (i % DRAW_EVERY == DRAW_EVERY - 1)
        data = pg.evaluate(STEP_JS, [now, draw, 0.96])
        if draw:
            k += 1
            name = f"s{k - 1}.jpg" if scout else f"f{k:05d}.jpg"
            (out_dir / name).write_bytes(base64.b64decode(data.split(",", 1)[1]))
            if not scout and k % 10 == 0:
                print(f"  {cfg['name']}: {k}/{n_steps // DRAW_EVERY}", flush=True)
    return now


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["render", "scout"])
    ap.add_argument("fmt", choices=list(FORMATS))
    ap.add_argument("--out", default=str(ROOT / "assets" / "video" / "reel-frames"))
    ap.add_argument("--shots", default="")
    a = ap.parse_args()
    want = [s for s in a.shots.split(",") if s]
    shots = [s for s in SHOTS if not want or s["name"] in want or s["name"][:2] in want]
    size = FORMATS[a.fmt]
    srv = sc.serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    now = 100000.0
    with sync_playwright() as p:
        b, pg = open_page(p, size)
        pg.goto(url, wait_until="load")
        pg.wait_for_function("window.__kt!==undefined", timeout=60000)
        pg.wait_for_timeout(8000)  # map data and fonts
        for s in shots:
            cfg = shot_cfg(s, a.fmt)
            d = pathlib.Path(a.out) / a.fmt / s["name"]
            d.mkdir(parents=True, exist_ok=True)
            if a.mode == "render" and (d / "DONE").exists():
                print("skip", s["name"], flush=True)
                continue
            t0 = time.time()
            now = run_shot(pg, cfg, now, d, scout=a.mode == "scout")
            if a.mode == "render":
                (d / "DONE").write_text(json.dumps({"seconds": round(time.time() - t0)}))
            print("done", s["name"], round(time.time() - t0), "s", flush=True)
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
