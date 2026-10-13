#!/usr/bin/env python3
"""Render the Fly Kai Tak "Concorde is flyable" launch promo from the sim itself, in landscape and portrait.

Usage:
  python3 tools/concorde_promo.py scout  yt|ig [--out DIR] [--shots 01,02]   3 stills per shot, to check framing
  python3 tools/concorde_promo.py render yt|ig [--out DIR] [--shots 01,02]   12 fps frames (resumable, like tools/reel.py)
  python3 tools/concorde_promo.py build  [yt|ig|all] [--out DIR] [--dest DIR]  overlays, end card, music, final MP4s
  python3 tools/concorde_promo.py image  [--out DIR] [--dest DIR]            the still promo images (needs rendered frames)

yt = 1920x1080 (YouTube, Facebook, X, LinkedIn), ig = 1080x1920 (YouTube Shorts, Instagram Reels, Facebook Reels, TikTok).
Every take is the sim's own Concorde (cockpit off, overlays hidden): autopilot approaches to Runway 13 and one
reheat take-off flown by a small controller in the take-off take. Music is the project's synthesised track
(tools/reel_music.py): nothing to license. Needs: playwright, pillow, numpy, scipy, ffmpeg.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reel  # noqa: E402
import screenshot as sc  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = sc.ROOT
FORMATS = {"yt": (1920, 1080), "ig": (1080, 1920)}
CONC = {"ac": "conc", "wx": "clear", "hour": 15}

# the take-off take: a controller (the same one tools/test_landings.py uses) flies the reheat take-off, before and during the take
TAKEOFF_JS = """(()=>{const k=window.__kt,S=k.ST;let air=null;
 const ctl=()=>{S.throttle=1;if(!S.onGround&&air===null)air=S.t;
  if(S.onGround)S.inPitch=S.Gs>75?0.5:0;
  else{S.inPitch=Math.max(-1,Math.min(1,(0.1-S.gamma)*6));if(S.ra>40)S.gearDown=false;S.inRoll=Math.max(-1,Math.min(1,-S.phi*3))}};
 for(let i=0;i<%PRE%*120&&!S.ended;i++){ctl();k.step()}
 if(!window.__fr0)window.__fr0=k.frame;k.frame=(t)=>{ctl();return window.__fr0(t)}})()"""


def S(name, run, dur, view, look, sweep=None, start=None, kicker="", line="", js=None, ig=None):
    return {"name": name, "dur": dur, "run": run, "view": view, "start": {**CONC, **(start or {})}, "look": look,
            "sweep": sweep, "kicker": kicker, "line": line, "js": js, "ig": ig or {}}


SHOTS = [
    S("01-final", 156, 4, "chase", {"orbitYaw": .55, "orbitPitch": .06, "dist": .55}, {"orbitYaw": [.55, 1.05]},
      kicker="NOW FLYABLE", line="Concorde is at Kai Tak."),
    S("02-turn", 132, 4, "chase", {"orbitYaw": 1.1, "orbitPitch": .15, "dist": .7}, {"orbitYaw": [1.1, .55]},
      kicker="THE CHECKERBOARD TURN", line="Droop nose. Delta wing."),
    S("03-droop", 174, 3.5, "chase", {"orbitYaw": -.45, "orbitPitch": .02, "dist": .42}, {"orbitYaw": [-.45, -.9]},
      kicker="OVER KOWLOON CITY", line="Low over the rooftops."),
    S("04-touchdown", 184, 4, "chase", {"orbitYaw": .9, "orbitPitch": .02, "dist": .5}, {"orbitYaw": [.9, 1.4]},
      kicker="RUNWAY 13", line="Nose high. Wheels down."),
    S("05-takeoff", 0, 3.5, "chase", {"orbitYaw": 2.5, "orbitPitch": .08, "dist": .6}, {"orbitYaw": [2.5, 3.0]},
      start={"game": "free", "ap": False}, js=TAKEOFF_JS.replace("%PRE%", "20"),
      kicker="FULL REHEAT", line="Four engines. Climb out."),
    S("06-night", 184, 3.5, "chase", {"orbitYaw": 1.2, "orbitPitch": .05, "dist": .5}, {"orbitYaw": [1.2, 1.7]},
      start={"night": True, "hour": 22}, kicker="DAY OR NIGHT", line="Any weather you like."),
]
TAKEOFF_RUN_NOTE = "05-takeoff pre-rolls 24 s of take-off roll, then the take starts just before rotation"


def cfg_for(s, fmt):
    cfg = {"name": s["name"], "dur": s["dur"], "run": s["run"], "view": s["view"], "start": s["start"], "look": s["look"],
           **({"sweep": s["sweep"]} if s["sweep"] else {}), **({"js": s["js"]} if s["js"] else {}), "ig": s["ig"]}
    return reel.shot_cfg(cfg, fmt)


def render(fmt, out, want, scout):
    srv = sc.serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    now = 100000.0
    with sync_playwright() as p:
        b, pg = reel.open_page(p, FORMATS[fmt])
        pg.goto(url, wait_until="load")
        pg.wait_for_function("window.__kt!==undefined", timeout=60000)
        pg.wait_for_timeout(8000)
        for s in SHOTS:
            if want and s["name"][:2] not in want:
                continue
            d = out / ("scout" if scout else "frames") / fmt / s["name"]
            d.mkdir(parents=True, exist_ok=True)
            if not scout and (d / "DONE").exists():
                print("skip", s["name"], flush=True)
                continue
            t0 = time.time()
            now = reel.run_shot(pg, cfg_for(s, fmt), now, d, scout=scout)
            if not scout:
                (d / "DONE").write_text(json.dumps({"seconds": round(time.time() - t0)}))
            print("done", s["name"], round(time.time() - t0), "s", flush=True)
        b.close()
    srv.shutdown()


FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700'
         '&family=Noto+Serif+TC:wght@900&display=swap">')
CHECK = "repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%)"

# on-screen lines: bottom-left on landscape; vertical keeps clear of the top 140 px and bottom 330 px (the apps' own buttons)
OVL = {
    "yt": """<!doctype html><html><head><meta charset="utf-8">""" + FONTS + """<style>html,body{margin:0;background:transparent}
.c{position:relative;width:1920px;height:1080px;font-family:'B612',sans-serif}
.g{position:absolute;left:0;right:0;bottom:0;height:480px;background:linear-gradient(to top,rgba(6,12,15,.82),rgba(6,12,15,0))}
.k{position:absolute;left:110px;bottom:200px;font-family:'B612 Mono',monospace;font-weight:700;font-size:30px;letter-spacing:.2em;color:#8ff5a8}
.l{position:absolute;left:106px;bottom:100px;font-weight:700;font-size:84px;line-height:1.05;color:#f5efe3;text-shadow:0 3px 18px rgba(0,0,0,.5)}
.t{position:absolute;left:110px;top:70px;font-family:'B612 Mono',monospace;font-weight:700;font-size:26px;letter-spacing:.18em;color:#f5efe3;
   background:rgba(9,16,20,.7);border:1px solid #3a5058;border-radius:3px;padding:12px 20px}.t b{color:#e8571f}</style></head><body><div class="c">
<div class="t"><b>■</b> FLY KAI TAK · CONCORDE</div><div class="g"></div><div class="k">{k}</div><div class="l">{l}</div></div></body></html>""",
    "ig": """<!doctype html><html><head><meta charset="utf-8">""" + FONTS + """<style>html,body{margin:0;background:transparent}
.c{position:relative;width:1080px;height:1920px;font-family:'B612',sans-serif}
.g{position:absolute;left:0;right:0;bottom:0;height:760px;background:linear-gradient(to top,rgba(6,12,15,.82),rgba(6,12,15,0))}
.k{position:absolute;left:84px;bottom:470px;font-family:'B612 Mono',monospace;font-weight:700;font-size:34px;letter-spacing:.2em;color:#8ff5a8}
.l{position:absolute;left:80px;right:80px;bottom:330px;font-weight:700;font-size:76px;line-height:1.05;color:#f5efe3;text-shadow:0 3px 18px rgba(0,0,0,.5)}
.t{position:absolute;left:84px;top:150px;font-family:'B612 Mono',monospace;font-weight:700;font-size:28px;letter-spacing:.18em;color:#f5efe3;
   background:rgba(9,16,20,.7);border:1px solid #3a5058;border-radius:3px;padding:12px 20px}.t b{color:#e8571f}</style></head><body><div class="c">
<div class="t"><b>■</b> FLY KAI TAK · CONCORDE</div><div class="g"></div><div class="k">{k}</div><div class="l">{l}</div></div></body></html>""",
}

CARD = {
    "yt": """<!doctype html><html><head><meta charset="utf-8">""" + FONTS + """<style>body{margin:0;background:#0a1115}
.c{position:relative;width:1920px;height:1080px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',sans-serif}
.chk{position:absolute;left:1180px;top:150px;width:600px;height:600px;background:""" + CHECK + """;background-size:240px 240px;border-radius:3px}
.k{position:absolute;left:120px;top:190px;font-family:'B612 Mono',monospace;letter-spacing:.22em;font-size:30px;color:#ff8a7e}
h1{position:absolute;left:114px;top:240px;margin:0;font-size:230px;line-height:.95;color:#f5efe3;font-weight:700}
.s{position:absolute;left:120px;top:700px;font-size:56px;font-weight:700;line-height:1.2}
.url{position:absolute;left:120px;top:900px;font-family:'B612 Mono',monospace;font-weight:700;font-size:44px;color:#8ff5a8;letter-spacing:.06em;background:rgba(9,16,20,.88);border:1px solid #3a5058;border-radius:3px;padding:16px 30px}
.han{position:absolute;left:1818px;top:150px;font-family:'Noto Serif TC',serif;font-weight:900;font-size:60px;writing-mode:vertical-rl;letter-spacing:.2em;color:#f5efe3}
.green{position:absolute;left:0;right:0;bottom:0;height:18px;background:#1f8a5b}</style></head><body><div class="c">
<div class="chk"></div><div class="han">協和式客機</div>
<div class="k">FLY KAI TAK · HONG KONG 1998</div><h1>Fly<br>Concorde.</h1>
<div class="s">US$7 once, or free with a code.<br>In your browser.</div><div class="url">flykaitak.com</div><div class="green"></div></div></body></html>""",
    "ig": """<!doctype html><html><head><meta charset="utf-8">""" + FONTS + """<style>body{margin:0;background:#0a1115}
.c{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',sans-serif}
.chk{position:absolute;left:190px;top:250px;width:700px;height:700px;background:""" + CHECK + """;background-size:280px 280px;border-radius:3px}
.han{position:absolute;right:70px;top:250px;font-family:'Noto Serif TC',serif;font-weight:900;font-size:56px;writing-mode:vertical-rl;letter-spacing:.2em;color:#f5efe3}
.k{position:absolute;left:96px;top:1040px;font-family:'B612 Mono',monospace;letter-spacing:.22em;font-size:30px;color:#ff8a7e}
h1{position:absolute;left:90px;top:1090px;margin:0;font-size:160px;line-height:.95;color:#f5efe3;font-weight:700}
.s{position:absolute;left:96px;top:1420px;font-size:48px;font-weight:700;line-height:1.2}
.url{position:absolute;left:96px;top:1580px;font-family:'B612 Mono',monospace;font-weight:700;font-size:48px;color:#8ff5a8;letter-spacing:.06em;background:rgba(9,16,20,.88);border:1px solid #3a5058;border-radius:3px;padding:16px 30px}
.green{position:absolute;left:0;right:0;bottom:0;height:18px;background:#1f8a5b}</style></head><body><div class="c">
<div class="chk"></div><div class="han">協和式客機</div>
<div class="k">FLY KAI TAK · HONG KONG 1998</div><h1>Fly<br>Concorde.</h1>
<div class="s">US$7 once, or free<br>with a code.</div><div class="url">flykaitak.com</div><div class="green"></div></div></body></html>""",
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("failed:\n" + " ".join(map(str, cmd)) + "\n" + r.stderr[-1500:])
    return r.stdout


def graphics(fmt, tmp):
    w, h = FORMATS[fmt]
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": w, "height": h})
        for s in SHOTS:
            pg.set_content(OVL[fmt].replace("{k}", s["kicker"]).replace("{l}", s["line"]), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(tmp / f"ovl-{fmt}-{s['name']}.png"), omit_background=True)
        pg.set_content(CARD[fmt], wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(tmp / f"card-{fmt}.png"))
        b.close()


def build(fmt, out, dest):
    tmp = out / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    graphics(fmt, tmp)
    clips = []
    for s in SHOTS:
        fr = out / "frames" / fmt / s["name"]
        if not (fr / "DONE").exists():
            sys.exit(f"not rendered: {fmt} {s['name']}")
        c = tmp / f"{fmt}-{s['name']}.mp4"
        lift = ",eq=gamma=1.15:saturation=1.05" if s["start"].get("night") else ""
        run(["ffmpeg", "-v", "error", "-y", "-framerate", "12", "-i", str(fr / "f%05d.jpg"), "-loop", "1", "-i", str(tmp / f"ovl-{fmt}-{s['name']}.png"),
             "-filter_complex", "[0:v]minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" + lift +
             f"[a];[1:v]format=rgba,fade=t=in:st=0.25:d=0.4:alpha=1,fade=t=out:st={s['dur'] - 0.55}:d=0.4:alpha=1[o];[a][o]overlay=shortest=1,format=yuv420p",
             "-t", str(s["dur"]), "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-r", "24", str(c)])
        clips.append(c)
    CARD_S, FADE = 4.5, 0.6
    # minterpolate trims a little off each take, so measure the real lengths: the end card must fade in at the real end
    durs = [float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(c)]).strip()) for c in clips]
    body = sum(durs)
    total = body + CARD_S - FADE
    cuts, acc = [], 0.0
    for d in durs[:-1]:
        acc += d
        cuts.append(round(acc, 3))
    cuts.append(round(body - FADE, 3))
    music = tmp / f"music-{fmt}.wav"
    run([sys.executable, str(HERE / "reel_music.py"), str(music), f"{total:.3f}", ",".join(map(str, cuts))])
    ins = []
    for c in clips:
        ins += ["-i", str(c)]
    n = len(clips)
    ins += ["-loop", "1", "-framerate", "24", "-t", str(CARD_S), "-i", str(tmp / f"card-{fmt}.png"), "-i", str(music)]
    chain = ["".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0,fps=24,settb=AVTB[body]",
             f"[{n}:v]format=yuv420p,setsar=1,fps=24,settb=AVTB[card]",
             f"[body][card]xfade=transition=fade:duration={FADE}:offset={body - FADE:.3f}[x]",
             f"[x]fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.5:.3f}:d=0.5[v]",
             f"[{n + 1}:a]volume=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[au]"]
    dest.mkdir(parents=True, exist_ok=True)
    name = {"yt": "flykaitak-concorde-launch-1920x1080.mp4", "ig": "flykaitak-concorde-launch-1080x1920.mp4"}[fmt]
    final = dest / name
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(chain), "-map", "[v]", "-map", "[au]",
         "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "24", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", str(final)])
    print("built", final, f"{total:.1f} s", final.stat().st_size // 1024 // 1024, "MB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["scout", "render", "build", "image"])
    ap.add_argument("fmt", nargs="?", default="all", choices=["yt", "ig", "all"])
    ap.add_argument("--out", default=str(ROOT / "assets" / "video" / "concorde-frames"))
    ap.add_argument("--dest", default=str(ROOT / "assets" / "video" / "social" / "concorde-launch"))
    ap.add_argument("--shots", default="")
    a = ap.parse_args()
    out, dest = pathlib.Path(a.out), pathlib.Path(a.dest)
    want = {s for s in a.shots.split(",") if s}
    fmts = ["yt", "ig"] if a.fmt == "all" else [a.fmt]
    if a.mode == "build":
        for f in fmts:
            build(f, out, dest)
    elif a.mode == "image":
        import concorde_image
        concorde_image.main(out, dest)
    else:
        for f in fmts:
            render(f, out, want, a.mode == "scout")


if __name__ == "__main__":
    main()
