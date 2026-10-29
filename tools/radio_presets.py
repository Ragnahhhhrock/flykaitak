#!/usr/bin/env python3
"""Pre-record the ATC radio pieces so the sim never has to call ElevenLabs while you fly.

The sim builds every radio call from pieces (fixed phrases and single number words, see radioParts in index.html).
This tool finds every piece the sim can say, records each one once and writes assets/radio/*.mp3 plus
assets/radio/index.json, which the sim loads at start. A piece missing from the index still works through the
Worker's /tts route (if set up), then the browser voice.

Usage:
  python3 tools/radio_presets.py list                  fly the sim headless (both runways, every game mode and weather,
                                                        a few random seeds) and write assets/radio/manifest.json. Prints counts.
  python3 tools/radio_presets.py build                 record every piece in the manifest that has no MP3 yet
  python3 tools/radio_presets.py build --via-worker    same, but through the deployed Worker's /tts route (no key needed;
                                                        the Worker limits new pieces per hour per IP: on 429, wait and run again)
  python3 tools/radio_presets.py build --force         record everything again (after changing a voice)
  python3 tools/radio_presets.py build --digits-only   record only the number words again (after changing DIGIT_TEMPO)

build needs ELEVENLABS_API_KEY in the environment (unless --via-worker). Voice IDs come from server/wrangler.toml.
It is safe to run again: pieces that already have an MP3 are skipped.
"""
import argparse
import hashlib
import http.server
import json
import os
import pathlib
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "radio"
WORKER = "https://flykaitak-scores.malgordonperth.workers.dev/tts"
WX = ["clear", "rain", "typhoon", "storm", "lowcloud", "fog"]
ROLES = ["APP", "TWR", "YOU", "OTH"]
NUMW = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "niner"]


def voices():
    t = (ROOT / "server" / "wrangler.toml").read_text()
    return {r: re.search(r"ELEVENLABS_VOICE_%s\s*=\s*\"([^\"]+)\"" % r, t).group(1) for r in ROLES}


DIGIT_TEMPO = 1.3   # number words are read faster than phrases (ffmpeg atempo, pitch kept), so a call with many digits is not slow


def speed_up(path):
    tmp = str(path) + ".tmp.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-af", "atempo=%s" % DIGIT_TEMPO, "-b:a", "64k", tmp], check=True)
    os.replace(tmp, path)


def fname(role, text):
    return "%s-%s.mp3" % (role, hashlib.sha1(text.encode()).hexdigest()[:12])


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


FLY = """
([cfg, sec]) => {
  window.__radioLog = [];
  window.__kt.start(cfg);
  const K = window.__kt, S = K.ST;
  // the sim's frame loop calls the radio controller; here it is called by hand, as often as a 30 fps frame would
  if (cfg.game === 'watch') { for (let t = 0; t < sec; t += 0.5) { S.t += 0.5; K.atc(0.5); } }
  else {
    const n = (cfg.game === 'free' ? Math.min(sec, 200) : sec) * 120;
    for (let i = 0; i < n && !S.ended; i++) {
      if (cfg.game === 'free') {   // roll for take-off so the tower clears the player, then climb away
        S.throttle = 1;
        if (S.onGround) S.inPitch = S.Gs > 75 ? 0.5 : 0;
        else { S.inPitch = Math.max(-1, Math.min(1, (0.1 - S.gamma) * 6)); S.inRoll = Math.max(-1, Math.min(1, -S.phi * 3)); }
      }
      K.step();
      if (i % 4 === 0) K.atc(1 / 30);
    }
  }
  return window.__radioLog.map(l => ({who: l.who, text: l.text, parts: K.radioParts(l.text).map(p => p.t)}));
}
"""


OTHERS = ["Lantau 120", "Pearl 66", "Victoria 318", "Jade 7", "Lamma 905", "Tsing Yi 41"]   # OTHERS in index.html


def extras():
    """Lines the autopilot and the scripted traffic rarely or never trigger (a low approach, a go-around, hold reasons,
    runway-control calls to other crews), written out from the templates in atcUpdate, rcTower and chatter. Numbers
    do not matter: they become single number words whatever they are. The sim's own radioParts splits them, so the
    pieces match what it asks for in flight."""
    out = []
    call, full, q = "Harbour 482", "Harbour 482 Heavy", "1013"
    whys = ["a departure is on the runway", "the runway is occupied", "traffic is on final"]
    winds = ["wind variable at 3 knots", "wind 310 at 12 knots", "wind 310 at 12 knots gusting 20"]
    vis = ["", ", visibility 800 metres"]
    wet = ["", ", runway wet"]
    for E in (False, True):
        rid, sight = ("31", "Lei Yue Mun") if E else ("13", "checkerboard")
        if E:
            out += [("APP", "%s, Hong Kong Approach, radar contact. Cleared visual approach runway 31, QNH %s. Report Lei Yue Mun in sight." % (full, q)),
                    ("YOU", "Cleared visual approach 31, QNH %s, will report Lei Yue Mun in sight, %s." % (q, call)),
                    ("YOU", "Going around, left heading 255, %s." % call)]
        else:
            out += [("APP", "%s, Hong Kong Approach, radar contact. Cleared IGS approach runway 13, QNH %s. Report checkerboard in sight." % (full, q)),
                    ("YOU", "Cleared IGS 13, QNH %s, will report checkerboard, %s." % (q, call)),
                    ("YOU", "Going around, %s." % call)]
        out += [("APP", "%s, contact Kai Tak Tower 118.7." % call), ("YOU", "118.7, %s." % call),
                ("YOU", "%s in sight, %s." % ("Lei Yue Mun" if E else "Checkerboard", call)),
                ("YOU", "Cleared to land %s, %s." % (rid, call)), ("YOU", "Cleared for takeoff %s, %s." % (rid, call)),
                ("TWR", "%s, contact Approach 119.1." % call), ("YOU", "119.1, %s." % call),
                ("APP", "%s, Hong Kong Approach, radar contact, QNH %s. Report leaving the zone." % (call, q)),
                ("TWR", "%s, vacate when able and taxi to the apron. Contact Ground." % call), ("YOU", "Vacating, %s." % call),
                ("TWR", "%s, you are not cleared for takeoff. Stop immediately." % full)]
        for W in winds:
            out.append(("TWR", "%s, Kai Tak Tower, %s. Report %s in sight." % (call, W, sight)))
            for v in vis:
                for w in wet:
                    out.append(("TWR", "%s, %s%s%s, runway %s cleared to land." % (call, W, v, w, rid)))
            for w in wet:
                out.append(("TWR", "%s, Kai Tak Tower, %s%s, runway %s cleared for takeoff." % (full, W, w, rid)))
        for y in whys:
            out += [("TWR", "%s, continue approach, %s. Expect clearance when it is clear." % (call, y)),
                    ("TWR", "%s, go around, go around, %s.%s" % (call, y, " Turn left heading 255 toward Stonecutters." if E else "")),
                    ("TWR", "%s, Kai Tak Tower, hold position, %s." % (full, y))]
        for freq in ("APP", "TWR"):
            for d in ("below", "above"):
                out.append((freq, "%s, check your height, you are %s the glidepath." % (call, d)))
        # runway control calls to the scripted traffic (rcTower)
        for cs in OTHERS:
            out += [("TWR", "%s, go around, runway %s is not clear." % (cs, rid)), ("OTH", "Going around, %s." % cs),
                    ("OTH", "Cleared to land %s, %s." % (rid, cs)), ("TWR", "%s, continue approach, runway %s not yet clear." % (cs, rid)),
                    ("OTH", "Continue approach, %s." % cs), ("OTH", "Holding position, %s." % cs),
                    ("TWR", "%s, runway %s, line up and wait." % (cs, rid)), ("OTH", "Cleared for takeoff %s, %s." % (rid, cs))]
            for y in whys:
                out.append(("TWR", "%s, hold position, %s." % (cs, y)))
            for W in winds:
                out += [("TWR", "%s, Kai Tak Tower, %s, runway %s cleared to land." % (cs, W, rid)),
                        ("TWR", "%s, %s, runway %s cleared for takeoff." % (cs, W, rid))]
    return out


def cmd_list(a):
    from playwright.sync_api import sync_playwright
    srv = serve()
    url = "http://127.0.0.1:%d/index.html" % srv.server_address[1]
    pieces = {r: set() for r in ROLES}
    lines = set()
    configs = []
    for rwy in ("13", "31"):
        for game in ("approach", "free", "watch"):
            for wx in WX:
                for seed in range(a.seeds):
                    configs.append({"ac": "b744", "ap": True, "game": game, "wx": wx, "rwy": rwy, "deck": False})
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                                    "--ignore-gpu-blocklist", "--no-sandbox"])
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        pg.add_init_script("window.__capture=true")
        pg.goto(url, wait_until="load")
        pg.wait_for_function("window.__kt!==undefined", timeout=90000)
        pg.wait_for_timeout(6000)
        for i, cfg in enumerate(configs):
            try:
                res = pg.evaluate(FLY, [cfg, a.sec])
            except Exception as e:  # keep going: one failed run should not lose the rest
                print("run failed", cfg, str(e)[:120])
                continue
            for l in res:
                lines.add((l["who"], l["text"]))
                for t in l["parts"]:
                    pieces[l["who"]].add(t)
            print("%3d/%d %s %s %s %s -> %d lines, %d pieces so far" % (i + 1, len(configs), cfg["rwy"], cfg["game"], cfg["wx"], "", len(res), sum(len(v) for v in pieces.values())))
        ex = extras()
        parts = pg.evaluate("(L) => L.map(l => window.__kt.radioParts(l[1]).map(p => p.t))", ex)
        for (who, text), ps in zip(ex, parts):
            lines.add((who, text))
            pieces[who].update(ps)
        b.close()
    # every role can say every number word, whichever call it is reading
    for r in ROLES:
        pieces[r].update(NUMW + ["decimal"])
    man = {r: sorted(pieces[r]) for r in ROLES}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
    n = sum(len(v) for v in man.values())
    chars = sum(len(t) for v in man.values() for t in v)
    print("\n%d distinct lines seen, %d pieces to record, %d characters (about %d credits at 1 credit per character, half that on Flash and Turbo models)" % (len(lines), n, chars, chars))
    for r in ROLES:
        print("  %s: %d pieces" % (r, len(man[r])))


def post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def cmd_build(a):
    man = json.loads((OUT / "manifest.json").read_text())
    idx_path = OUT / "index.json"
    idx = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    v = voices()
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key and not a.via_worker:
        sys.exit("Set ELEVENLABS_API_KEY, or use --via-worker.")
    nums = set(NUMW + ["decimal"])
    todo = [(r, t) for r in ROLES for t in man[r]
            if (a.force or not (OUT / fname(r, t)).exists() or (a.digits_only and t in nums)) and (not a.digits_only or t in nums)]
    print("%d pieces to record" % len(todo))
    done = 0
    for r, t in todo:
        f = fname(r, t)
        try:
            if a.via_worker:
                audio = post(WORKER, {"content-type": "application/json", "Origin": "https://flykaitak.com", "User-Agent": "flykaitak-radio-presets"}, {"role": r, "text": t})
            else:
                audio = post("https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=mp3_44100_64" % v[r],
                             {"xi-api-key": key, "content-type": "application/json", "accept": "audio/mpeg"},
                             {"text": t, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_turbo_v2_5"),
                              "voice_settings": {"stability": 0.55, "similarity_boost": 0.75, "speed": 1.1 if r == "OTH" else 1.05}})
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            print("stopped at %s '%s': HTTP %d %s" % (r, t, e.code, body))
            break
        (OUT / f).write_bytes(audio)
        if t in nums:
            speed_up(OUT / f)
        idx[r + "|" + t] = f
        done += 1
        if done % 20 == 0:
            idx_path.write_text(json.dumps(idx, indent=0, ensure_ascii=False, sort_keys=True) + "\n")
            print("  %d/%d" % (done, len(todo)))
        time.sleep(0.15)
    # index every piece whose MP3 exists (also ones recorded by an earlier run)
    for r in ROLES:
        for t in man[r]:
            if (OUT / fname(r, t)).exists():
                idx[r + "|" + t] = fname(r, t)
    idx_path.write_text(json.dumps(idx, indent=0, ensure_ascii=False, sort_keys=True) + "\n")
    missing = sum(1 for r in ROLES for t in man[r] if (r + "|" + t) not in idx)
    print("recorded %d, %d still missing, index has %d pieces" % (done, missing, len(idx)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list")
    l.add_argument("--sec", type=int, default=420)
    l.add_argument("--seeds", type=int, default=2)
    b = sub.add_parser("build")
    b.add_argument("--via-worker", action="store_true")
    b.add_argument("--force", action="store_true")
    b.add_argument("--digits-only", action="store_true", help="record the number words again (after changing DIGIT_TEMPO)")
    a = ap.parse_args()
    {"list": cmd_list, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    main()
