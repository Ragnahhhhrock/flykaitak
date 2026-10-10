#!/usr/bin/env python3
"""Render the Fly Kai Tak helicopter tour promo (vertical 1080x1920, under 60 s) from the sim itself.

Usage:
  python3 tools/tour_promo.py scout  [--out DIR] [--shots 01,02]   3 stills per shot, to check framing
  python3 tools/tour_promo.py render [--out DIR] [--shots 01,02]   12 fps frames (resumable, like tools/reel.py)
  python3 tools/tour_promo.py build  [--out DIR] [--dest DIR]      overlays, end card, music + rotor, final MP4

Every take is a continuous run of the Harbour helicopter tour (game 'tour'): the Peninsula S-76 from its rooftop pad
over Victoria Harbour, Central, Shun Tak, Wan Chai and back. Views: 'helix' (outside, orbit camera) and 'heli'
(the left window seat). Tour times: the sim clock starts at 230 s, rotors turn up from 234 s, lift-off at 260 s,
touch-down back on the pad at about 498 s (see penTour() in index.html). run = tau - 230 - 0.5 (the settle steps).
One vertical cut serves YouTube Shorts, Instagram Reels, Facebook Reels, TikTok, Threads and X.
Needs: playwright, pillow, numpy, scipy, ffmpeg.
"""
import argparse
import pathlib
import subprocess
import sys
import time
import json

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reel  # noqa: E402
import screenshot as sc  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = sc.ROOT
SIZE = (1080, 1920)
T0 = 230.5   # sim clock at the start of the tour, plus the settle steps
DAY = {"tour": True, "game": "watch", "wx": "clear", "hour": 17}


def S(name, tau, dur, view, look, sweep=None, start=None, kicker="", line="", js=None):
    return {"name": name, "dur": dur, "run": tau - T0, "view": view, "start": {**DAY, **(start or {})},
            "look": look, "sweep": sweep, "kicker": kicker, "line": line, "js": js}


# a chase camera behind the helicopter that looks past it toward Kai Tak, so the runway and the traffic are in frame
KAI_TAK_CAM = """window.__camFn=(cam)=>{const k=window.__kt,H=k.HELI.find(h=>h.id==='pen'),P=H&&H.p;if(!P)return;
 const r=k.rwP(1400,0),dx=r[0]-P.x,dz=r[1]-P.z,L=Math.hypot(dx,dz),ux=dx/L,uz=dz/L;
 cam.position.set(P.x-ux*38+uz*7,P.y+7,P.z-uz*38-ux*7);cam.lookAt(P.x+ux*90,P.y-9,P.z+uz*90);cam.fov=55;cam.updateProjectionMatrix()}"""


SHOTS = [
    S("01-rooftop", 254, 6, "helix", {"orbitYaw": 2.4, "orbitPitch": .25, "dist": 1.0}, {"orbitYaw": [2.4, 1.6], "dist": [1.0, .8]},
      kicker="THE PENINSULA · HONG KONG · 1998", line="Your helicopter is waiting."),
    S("02-window-seat", 273, 5, "heli", {"yaw": .1, "pitch": -.15, "dist": 1}, {"yaw": [.1, .45]},
      kicker="WINDOW SEAT", line="Lift off over Tsim Sha Tsui."),
    S("03-harbour", 286, 6, "helix", {"orbitYaw": -1.0, "orbitPitch": .1, "dist": 1.1}, {"orbitYaw": [-1.0, -.4]},
      kicker="VICTORIA HARBOUR", line="Cross the harbour."),
    S("04-central", 300, 5, "heli", {"yaw": -.1, "pitch": -.08, "dist": 1}, {"yaw": [-.1, .3]},
      kicker="CENTRAL", line="Bank of China. HSBC. Jardine House."),
    S("05-peak", 324, 5, "helix", {"orbitYaw": 2.6, "orbitPitch": .05, "dist": 1.2}, {"orbitYaw": [2.6, 3.1]},
      kicker="VICTORIA PEAK", line="Turn under the Peak."),
    S("06-wan-chai", 372, 5, "helix", {"orbitYaw": -1.3, "orbitPitch": .15, "dist": 1.3}, {"orbitYaw": [-1.3, -.8]},
      kicker="WAN CHAI", line="Central Plaza and the Convention Centre."),
    S("07-kai-tak", 409, 5, "helix", {"orbitYaw": 0, "orbitPitch": .1, "dist": 1}, js=KAI_TAK_CAM,
      kicker="KAI TAK", line="Jets landing across the bay."),
    S("08-night", 290, 5, "helix", {"orbitYaw": -.9, "orbitPitch": .12, "dist": 1.1}, {"orbitYaw": [-.9, -.5]},
      start={"hour": 19.4, "night": True}, kicker="AFTER DARK", line="Or fly it at night."),
    S("09-landing", 492, 6, "helix", {"orbitYaw": 1.2, "orbitPitch": .35, "dist": 1.1}, {"orbitYaw": [1.2, .7]},
      start={"hour": 18}, kicker="BACK ON THE ROOF", line="Free. In your browser."),
]


def cfg_for(s):
    return {"name": s["name"], "dur": s["dur"], "run": s["run"], "view": s["view"], "start": s["start"],
            "look": s["look"], **({"sweep": s["sweep"]} if s["sweep"] else {}), **({"js": s["js"]} if s["js"] else {})}


def render(out, want, scout):
    srv = sc.serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    now = 100000.0
    with sync_playwright() as p:
        b, pg = reel.open_page(p, SIZE)
        pg.goto(url, wait_until="load")
        pg.wait_for_function("window.__kt!==undefined", timeout=60000)
        pg.wait_for_timeout(8000)
        for s in SHOTS:
            if want and s["name"][:2] not in want:
                continue
            d = out / ("scout" if scout else "frames") / s["name"]
            d.mkdir(parents=True, exist_ok=True)
            if not scout and (d / "DONE").exists():
                print("skip", s["name"], flush=True)
                continue
            t0 = time.time()
            now = reel.run_shot(pg, cfg_for(s), now, d, scout=scout)
            if not scout:
                (d / "DONE").write_text(json.dumps({"seconds": round(time.time() - t0)}))
            print("done", s["name"], round(time.time() - t0), "s", flush=True)
        b.close()
    srv.shutdown()


OVL = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@700&family=Noto+Serif+TC:wght@900&display=swap">
<style>html,body{margin:0;background:transparent}
.c{position:relative;width:1080px;height:1920px;font-family:'B612',sans-serif}
.g{position:absolute;left:0;right:0;bottom:0;height:760px;background:linear-gradient(to top,rgba(6,12,15,.82),rgba(6,12,15,0))}
.k{position:absolute;left:84px;bottom:470px;font-family:'B612 Mono',monospace;font-weight:700;font-size:34px;letter-spacing:.2em;color:#8ff5a8}
.l{position:absolute;left:80px;right:80px;bottom:330px;font-weight:700;font-size:76px;line-height:1.05;color:#f5efe3;text-shadow:0 3px 18px rgba(0,0,0,.5)}
.t{position:absolute;left:84px;top:150px;font-family:'B612 Mono',monospace;font-weight:700;font-size:28px;letter-spacing:.18em;color:#f5efe3;
   background:rgba(9,16,20,.7);border:1px solid #3a5058;border-radius:3px;padding:12px 20px}
.t b{color:#e8571f}</style></head><body><div class="c">
<div class="t"><b>■</b> FLY KAI TAK · HELICOPTER TOUR</div><div class="g"></div><div class="k">{k}</div><div class="l">{l}</div></div></body></html>"""

CARD = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700&family=Noto+Serif+TC:wght@900&display=swap">
<style>body{margin:0;background:#0a1115}
.c{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',sans-serif}
.pad{position:absolute;left:240px;top:250px;width:600px;height:600px;border-radius:50%;background:#2c8a55;
  box-shadow:0 0 0 26px #e6eee6,0 0 0 52px #2d8a58}
.ring{position:absolute;left:105px;top:105px;width:390px;height:390px;border-radius:50%;border:30px solid #e9a73a;box-sizing:border-box}
.h{position:absolute;left:0;right:0;top:150px;text-align:center;font-weight:700;font-size:300px;line-height:300px;color:#f2f0e8}
.k{position:absolute;left:96px;top:1040px;font-family:'B612 Mono',monospace;letter-spacing:.22em;font-size:30px;color:#ff8a7e}
h1{position:absolute;left:90px;top:1090px;margin:0;font-size:150px;line-height:.95;color:#f5efe3;font-weight:700}
.s{position:absolute;left:96px;top:1400px;font-size:50px;font-weight:700;line-height:1.2}
.url{position:absolute;left:96px;top:1560px;font-family:'B612 Mono',monospace;font-weight:700;font-size:48px;color:#8ff5a8;letter-spacing:.06em;
  background:rgba(9,16,20,.88);border:1px solid #3a5058;border-radius:3px;padding:16px 30px}
.han{position:absolute;right:70px;top:250px;font-family:'Noto Serif TC',serif;font-weight:900;font-size:56px;writing-mode:vertical-rl;letter-spacing:.2em;color:#f5efe3}
.green{position:absolute;left:0;right:0;bottom:0;height:18px;background:#1f8a5b}</style></head><body><div class="c">
<div class="pad"><div class="ring"></div><div class="h">H</div></div><div class="han">維港直升機觀光</div>
<div class="k">FLY KAI TAK · HONG KONG 1998</div><h1>Take the<br>tour.</h1>
<div class="s">Free in your browser.<br>No download. No sign-up.</div><div class="url">flykaitak.com</div><div class="green"></div></div></body></html>"""


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("failed:\n" + " ".join(map(str, cmd)) + "\n" + r.stderr[-1500:])
    return r.stdout


def graphics(tmp):
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for s in SHOTS:
            pg.set_content(OVL.replace("{k}", s["kicker"]).replace("{l}", s["line"]), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(tmp / f"ovl-{s['name']}.png"), omit_background=True)
        pg.set_content(CARD, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(tmp / "card.png"))
        b.close()


def rotor_wav(path, total, sr=44100):
    """A soft S-76 rotor: blade-pass thump (4 blades at about 5 Hz) on filtered noise, plus a turbine whine."""
    import numpy as np
    from scipy import signal
    from scipy.io import wavfile
    rng = np.random.default_rng(76)
    n = int(total * sr)
    t = np.arange(n) / sr
    noise = rng.standard_normal(n)
    b, a = signal.butter(2, [60 / (sr / 2), 420 / (sr / 2)], "band")
    body = signal.lfilter(b, a, noise)
    thump = (0.5 + 0.5 * np.cos(2 * np.pi * 5.2 * t)) ** 6
    whine = 0.04 * np.sin(2 * np.pi * 1840 * t) + 0.02 * np.sin(2 * np.pi * 3680 * t)
    x = body * (0.25 + thump) + whine
    x /= np.max(np.abs(x)) + 1e-9
    fade = np.minimum(1, np.minimum(t / 1.5, (total - t) / 2.0)).clip(0, 1)
    wavfile.write(str(path), sr, (x * fade * 0.6 * 32767).astype(np.int16))


def build(out, dest):
    tmp = out / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    graphics(tmp)
    clips = []
    for s in SHOTS:
        fr = out / "frames" / s["name"]
        if not (fr / "DONE").exists():
            sys.exit(f"not rendered: {s['name']}")
        c = tmp / f"{s['name']}.mp4"
        lift = ",eq=gamma=1.15:saturation=1.05" if s["start"].get("night") else ""
        run(["ffmpeg", "-v", "error", "-y", "-framerate", "12", "-i", str(fr / "f%05d.jpg"), "-loop", "1", "-i", str(tmp / f"ovl-{s['name']}.png"),
             "-filter_complex", "[0:v]minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" + lift +
             f"[a];[1:v]format=rgba,fade=t=in:st=0.25:d=0.4:alpha=1,fade=t=out:st={s['dur'] - 0.55}:d=0.4:alpha=1[o];[a][o]overlay=shortest=1,format=yuv420p",
             "-t", str(s["dur"]), "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-r", "24", str(c)])
        clips.append(c)
    CARD_S, FADE = 5.0, 0.6
    body = sum(s["dur"] for s in SHOTS)
    total = body + CARD_S - FADE
    cuts, acc = [], 0.0
    for s in SHOTS[:-1]:
        acc += s["dur"]
        cuts.append(round(acc, 3))
    cuts.append(round(body - FADE, 3))
    music, rotor = tmp / "music.wav", tmp / "rotor.wav"
    run([sys.executable, str(HERE / "reel_music.py"), str(music), f"{total:.3f}", ",".join(map(str, cuts))])
    rotor_wav(rotor, body)
    ins = []
    for c in clips:
        ins += ["-i", str(c)]
    n = len(clips)
    ins += ["-loop", "1", "-framerate", "24", "-t", str(CARD_S), "-i", str(tmp / "card.png"), "-i", str(music), "-i", str(rotor)]
    chain = ["".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0,fps=24,settb=AVTB[body]",
             f"[{n}:v]format=yuv420p,setsar=1,fps=24,settb=AVTB[card]",
             f"[body][card]xfade=transition=fade:duration={FADE}:offset={body - FADE:.3f}[x]",
             f"[x]fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.5:.3f}:d=0.5[v]",
             f"[{n + 1}:a]volume=0.85[m];[{n + 2}:a]volume=0.35[r];[m][r]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[au]"]
    dest.mkdir(parents=True, exist_ok=True)
    final = dest / "flykaitak-helicopter-tour-1080x1920.mp4"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(chain), "-map", "[v]", "-map", "[au]",
         "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "24", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", str(final)])
    cover = out / "frames" / "03-harbour" / "f00030.jpg"
    if cover.exists():
        (dest / "helicopter-tour-cover.jpg").write_bytes(cover.read_bytes())
    print("built", final, f"{total:.1f} s", final.stat().st_size // 1024 // 1024, "MB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["scout", "render", "build"])
    ap.add_argument("--out", default=str(ROOT / "assets" / "video" / "tour-frames"))
    ap.add_argument("--dest", default=str(ROOT / "assets" / "video" / "social" / "helicopter-tour"))
    ap.add_argument("--shots", default="")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    want = {s for s in a.shots.split(",") if s}
    if a.mode == "build":
        build(out, pathlib.Path(a.dest))
    else:
        render(out, want, a.mode == "scout")


if __name__ == "__main__":
    main()
