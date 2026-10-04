#!/usr/bin/env python3
"""Landing regression test for Fly Kai Tak.

Usage:  python3 tools/test_landings.py [--rwy 13|31|both] [--night] [--ac b744,b772,a333,a343] [--wx clear,rain,...]

Serves the repo, opens it in headless Chromium and uses the sim's test hooks (window.__kt) to check, for each
runway and weather preset:
  1. the autopilot lands the aircraft (no crash, no missed approach), touching down on the runway;
  2. with no input at all (autopilot off) the aircraft crashes;
  3. aircraft on the ground (AI traffic taxiing, docking, pushing back) keep all three wheels on the tarmac, never on the grass;
  4. the player's aircraft steered off the runway at walking pace stops at the tarmac edge, and at speed crashes (runway excursion).
Exit code 0 means every check passed.
"""
import argparse
import http.server
import json
import pathlib
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
WX = ["clear", "rain", "typhoon", "storm", "lowcloud", "fog"]


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


RUN = """
([cfg, sec]) => {
  window.__kt.start(cfg);
  const r = window.__kt.run(sec);
  const e = r.ended;
  return {kind: e ? (e.landed ? 'landed' : e.crash ? 'crash' : 'missed') : 'flying', title: e && e.title,
          why: e && e.why, t: Math.round(r.t), td: r.td ? {s: Math.round(r.td.s), l: +r.td.l.toFixed(1), fpm: Math.round(-r.td.vs * 196.85)} : null,
          d: Math.round(r.d)};
}
"""


TAKEOFF = """
([cfg, sec]) => {
  window.__kt.start(cfg);
  const S = window.__kt.ST, h = 1 / 120; let air = null, maxAlt = 0;
  for (let i = 0; i < sec * 120 && !S.ended; i++) {
    S.throttle = 1;
    if (!S.onGround && air === null) air = S.t;
    if (S.onGround) S.inPitch = S.Gs > 75 ? 0.5 : 0;
    else {
      S.inPitch = Math.max(-1, Math.min(1, (0.1 - S.gamma) * 6));
      if (S.ra > 40) S.gearDown = false;
      S.inRoll = (S.t - air > 40 && S.t - air < 110) ? Math.max(-1, Math.min(1, (-0.3 - S.phi) * 3)) : Math.max(-1, Math.min(1, -S.phi * 3));
    }
    window.__kt.step(); maxAlt = Math.max(maxAlt, S.y);
  }
  const e = S.ended;
  return {kind: e ? (e.crash ? 'crash' : 'ended') : (air === null ? 'grounded' : 'airborne'), title: e && e.title, why: e && e.why,
          t: Math.round(S.t), air: air && Math.round(air), alt: Math.round(S.y), maxAlt: Math.round(maxAlt), V: Math.round(S.V * 1.944)};
}
"""


SPOTTER = """
(cfg) => {
  window.__kt.start(cfg);
  const K = window.__kt; let bad = 0, n = 0;
  for (let t = 0; t < 900; t += 5) for (const a of K.AI) { const p = a.fn(t); if (!p) continue; n++;
    if (![p.x, p.y, p.z, p.psi].every(Number.isFinite) || p.y < 3) bad++; }
  return {bad, n};
}
"""


GROUND = """
(cfg) => {
  window.__kt.start(cfg);
  const K = window.__kt; let n = 0, bad = 0, first = null; const seen = new Set();
  for (let t = 0; t < 1500; t += 0.5) for (const a of K.AI) { const p = a.fn(t); if (!p || p.y > 4.6) continue;
    n++; const len = K.AC[a.type].len;
    if (!K.gearPaved(p.x, p.z, p.psi, len, 0)) { bad++; if (!first) first = {role: a.role, type: a.type, t, s: Math.round(K.rwS(p.x, p.z)), l: Math.round(K.rwL(p.x, p.z))}; } }
  return {n, bad, first};
}
"""


EDGE = """
([cfg, speed, side]) => {
  window.__kt.start(cfg);
  const S = window.__kt.ST, K = window.__kt, h0 = S.psiG, turn = side * Math.PI / 2;
  S.Gs = speed; let blocked = false, stopped = 0;
  for (let i = 0; i < 20 * 120 && !S.ended; i++) {
    S.psiG = S.psi = h0 + turn; S.throttle = 0.2; S.Gs = speed;
    window.__kt.step();
    if (!S.ended && !K.gearPaved(S.x, S.z, S.psiG, S.ac.len, 0)) { blocked = 'off'; break; }
  }
  const e = S.ended;
  return {kind: e ? (e.crash ? 'crash' : 'ended') : 'held', title: e && e.title, off: blocked, l: +K.rwL(S.x, S.z).toFixed(1), Gs: +S.Gs.toFixed(1)};
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rwy", default="both")
    ap.add_argument("--night", action="store_true")
    ap.add_argument("--ac", default="b744")
    ap.add_argument("--wx", default=",".join(WX))
    ap.add_argument("--sec", type=int, default=420)
    a = ap.parse_args()
    rwys = ["13", "31"] if a.rwy == "both" else [a.rwy]
    srv = serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    fails = 0
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                                    "--ignore-gpu-blocklist", "--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        pg.add_init_script("window.__capture=true")
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="load")
        pg.wait_for_function("window.__kt!==undefined", timeout=90000)
        pg.wait_for_timeout(6000)
        for rwy in rwys:
            for ac in a.ac.split(","):
                for wx in a.wx.split(","):
                    base = {"game": "approach", "rwy": rwy, "ac": ac, "wx": wx, "night": a.night, "deck": False}
                    r = pg.evaluate(RUN, [{**base, "ap": True}, a.sec])
                    ok = r["kind"] == "landed"
                    print(f"RWY {rwy} {ac} {wx:9s} autopilot   -> {r['kind']:7s} t={r['t']}s td={r['td']} {'' if ok else r['title']}", flush=True)
                    fails += 0 if ok else 1
                r = pg.evaluate(RUN, [{**base, "wx": "clear", "ap": False}, a.sec])
                ok = r["kind"] == "crash"
                print(f"RWY {rwy} {ac} no input             -> {r['kind']:7s} t={r['t']}s {r['title']}", flush=True)
                fails += 0 if ok else 1
        for rwy in rwys:
            r = pg.evaluate(TAKEOFF, [{"game": "free", "rwy": rwy, "ac": "b744", "wx": "clear", "night": a.night, "deck": False, "ap": False}, 200])
            ok = r["kind"] == "airborne" and r["alt"] > 500
            print(f"RWY {rwy} take-off (free flight)    -> {r['kind']:8s} airborne at {r['air']}s, alt {r['alt']} m, {r['V']} kt {'' if ok else r['title']} {'' if ok else r['why']}", flush=True)
            fails += 0 if ok else 1
        for rwy in rwys:
            r = pg.evaluate(SPOTTER, {"game": "watch", "rwy": rwy, "wx": "clear", "night": False, "deck": False})
            ok = r["bad"] == 0 and r["n"] > 0
            print(f"RWY {rwy} plane spotter traffic     -> {r['n']} poses, {r['bad']} bad", flush=True)
            fails += 0 if ok else 1
        for rwy in rwys:
            for game in ("watch", "approach", "free"):
                r = pg.evaluate(GROUND, {"game": game, "rwy": rwy, "wx": "clear", "night": False, "deck": False})
                ok = r["bad"] == 0 and r["n"] > 0
                print(f"RWY {rwy} {game:8s} ground traffic  -> {r['n']} ground poses, {r['bad']} off the tarmac {r['first'] or ''}", flush=True)
                fails += 0 if ok else 1
        for rwy in rwys:
            for side, nm in ((1, "toward Kowloon Bay"), (-1, "toward the apron")):
                for speed, want in ((5, "held"), (40, "crash")):
                    r = pg.evaluate(EDGE, [{"game": "free", "rwy": rwy, "ac": "b744", "wx": "clear", "night": False, "deck": False, "ap": False}, speed, side])
                    ok = r["kind"] == want and not r["off"]
                    print(f"RWY {rwy} steer {nm:19s} at {speed:2d} m/s -> {r['kind']:5s} l={r['l']} {r['title'] or ''} {'' if ok else 'WRONG'}", flush=True)
                    fails += 0 if ok else 1
        b.close()
    srv.shutdown()
    if errs:
        print("PAGE ERRORS:", json.dumps(errs[:5], indent=1))
        fails += 1
    print("PASS" if not fails else f"FAIL ({fails})")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
