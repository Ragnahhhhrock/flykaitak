#!/usr/bin/env python3
"""Runway control test for Fly Kai Tak.

Usage:  python3 tools/test_runway.py [--rwy 13|31|both] [--sec 1200]

Opens the repo in headless Chromium and uses the sim's test hooks (window.__kt) to check, on each runway:
  1. Plane Spotter traffic: no two aircraft are on the runway strip together unless one is standing, no arrival is over the threshold with
     the runway occupied, and the planned timetable needs no go-around;
  2. a player standing on the runway makes every arrival that would land on it go around, and nothing touches down on the player;
  3. the tower only clears a take-off when the runway is clear: with an arrival inbound, rcTakeoffWhy() says so.
Exit code 0 means every check passed.
"""
import argparse, http.server, json, pathlib, socketserver, sys, threading
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

        def handle_error(self, *a):
            pass

    srv = Srv(("127.0.0.1", 0), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


WATCH = """
([cfg, T]) => {
  const K = window.__kt; K.start(cfg); const S = K.ST; S.t = 0; K.updateAI();
  const lS = p => K.LND.dir > 0 ? K.rwS(p.x, p.z) : 3390 - K.rwS(p.x, p.z), E = 4, bad = [];
  for (let t = 0.5; t <= T; t += 0.5) {
    S.t = t; K.updateAI(); const occ = [];
    for (const a of K.AI) { if (!a.p || a.role === 'holding' || !a.m.visible) continue;
      const p = a.p; if (p.y < E + 3 && K.rcStrip(p.x, p.z, p.y, K.AC[a.type].span / 2)) occ.push({a, s: lS(p), v: a.v || 0}); }
    for (let i = 0; i < occ.length; i++) for (let j = i + 1; j < occ.length; j++)
      { const r = occ[i].s <= occ[j].s ? occ[i] : occ[j], f = r === occ[i] ? occ[j] : occ[i];   // the one behind must not be fast while closing on the one ahead
        if (r.v > 8 && f.s - r.s < 500 && r.v > f.v - 1) bad.push([t, 'two on the strip', r.a.type, f.a.type]); }
    for (const a of K.AI) { if (a.role !== 'arrival' || !a.p || a.ga != null) continue;
      const p = a.p, s = lS(p);
      if (p.y > E + 3 && p.y < E + 75 && s > -700 && s < 250 && occ.some(o => o.a !== a)) bad.push([t, 'arrival over an occupied runway', a.type]); }
  }
  const lg = K.RC.log.reduce((o, e) => { o[e.ev] = (o[e.ev] || 0) + 1; return o; }, {});
  return {bad: bad.length, first: bad[0] || null, hits: (K.hits || []).length, goArounds: lg['go-around'] || 0, holds: lg.hold || 0};
}
"""

BLOCKED = """
(cfg) => {
  const K = window.__kt; K.start(cfg); const S = K.ST; let ga = 0, onPlayer = 0, t = 0;
  S.throttle = 0; S.brake = 1;
  for (let i = 0; i < 400 * 120 && !S.ended; i++) {
    K.step(); t = S.t; if (i % 15 === 0) K.aiTick();
    if (i % 60 === 0) for (const a of K.AI) { if (a.role !== 'arrival' || !a.p) continue;
      const p = a.p; if (p.y < 8 && Math.hypot(p.x - S.x, p.z - S.z) < 400 && (a.v || 0) > 30) onPlayer++; }
  }
  ga = K.RC.log.filter(e => e.ev === 'go-around').length;
  return {t: Math.round(t), ended: S.ended ? S.ended.title : null, goArounds: ga, touchedDownOnPlayer: onPlayer};
}
"""

CLEAR = """
(cfg) => {
  const K = window.__kt; K.start(cfg); const S = K.ST; let why = null, seen = false, t = 0;
  S.throttle = 0; S.brake = 1;
  for (let i = 0; i < 300 * 120 && !S.ended && !seen; i++) {
    K.step(); if (i % 15 === 0) K.aiTick();
    if (i % 60 === 0 && K.RC.V && K.RC.V.some(v => v && v.eta !== null && v.eta > 0 && v.eta < 60)) { seen = true; why = K.rcTakeoffWhy ? K.rcTakeoffWhy() : 'no hook'; }
  }
  return {seen, why};
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rwy", default="both")
    ap.add_argument("--sec", type=int, default=1200)
    a = ap.parse_args()
    rwys = ["13", "31"] if a.rwy == "both" else [a.rwy]
    srv = serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    fails = 0
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--no-sandbox"])
        errs = []
        for rwy in rwys:
            pg = b.new_page(viewport={"width": 960, "height": 540})
            pg.add_init_script("window.__capture=true")
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url, wait_until="load")
            pg.wait_for_function("window.__kt!==undefined", timeout=90000)
            pg.wait_for_timeout(4000)
            r = pg.evaluate(WATCH, [{"game": "watch", "rwy": rwy, "wx": "clear", "night": False, "deck": False}, a.sec])
            ok = r["bad"] == 0 and r["goArounds"] == 0 and r["hits"] == 0
            print(f"RWY {rwy} plane spotter {a.sec}s -> {r['bad']} runway conflicts, {r['goArounds']} go-arounds, {r['holds']} holds, {r['hits']} collisions {r['first'] or ''}", flush=True)
            fails += 0 if ok else 1
            r = pg.evaluate(BLOCKED, {"game": "free", "rwy": rwy, "ac": "b744", "wx": "clear", "night": False, "deck": False, "ap": False})
            ok = r["goArounds"] >= 1 and r["touchedDownOnPlayer"] == 0 and r["ended"] is None
            print(f"RWY {rwy} player on the runway -> {r['goArounds']} go-arounds, {r['touchedDownOnPlayer']} landed on the player, ended={r['ended']}", flush=True)
            fails += 0 if ok else 1
            r = pg.evaluate(CLEAR, {"game": "free", "rwy": rwy, "ac": "b744", "wx": "clear", "night": False, "deck": False, "ap": False})
            ok = r["seen"] and r["why"] == "traffic is on final"
            print(f"RWY {rwy} take-off with traffic on final -> {r['why']}", flush=True)
            fails += 0 if ok else 1
            pg.close()
        b.close()
    srv.shutdown()
    if errs:
        print("PAGE ERRORS:", json.dumps(errs[:5], indent=1))
        fails += 1
    print("PASS" if not fails else f"FAIL ({fails})")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
