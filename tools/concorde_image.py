"""Still promo images for the Concorde launch (called by tools/concorde_promo.py image).

Landscape 1600x900 (X, Facebook, LinkedIn, link cards) and portrait 1080x1350 (Instagram, Facebook, Threads) from
frames the promo render left in OUT/frames. Fonts and colours follow docs/claude-project.md.
"""
import base64
import io
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700'
         '&family=Noto+Serif+TC:wght@900&display=swap">')
CHECK = "repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%)"
PAGE = """<!doctype html><html><head><meta charset="utf-8">""" + FONTS + """<style>body{margin:0;background:#0a1115}
.c{position:relative;width:%(w)dpx;height:%(h)dpx;overflow:hidden;background:#0a1115 url('%(img)s') %(pos)s/cover;color:#e9eee8;font-family:'B612',sans-serif}
.sh{position:absolute;inset:0;background:%(shade)s}
.k{position:absolute;left:%(m)dpx;top:%(kt)dpx;font-family:'B612 Mono',monospace;font-weight:700;letter-spacing:.2em;font-size:%(ks)dpx;color:#8ff5a8;background:rgba(9,16,20,.72);border:1px solid #3a5058;border-radius:3px;padding:10px 18px}
h1{position:absolute;left:%(m)dpx;top:%(ht)dpx;margin:0;font-size:%(hs)dpx;line-height:.95;color:#f5efe3;font-weight:700;text-shadow:0 4px 24px rgba(0,0,0,.45)}
.s{position:absolute;left:%(m)dpx;top:%(st)dpx;font-size:%(ss)dpx;font-weight:700;line-height:1.2;text-shadow:0 2px 14px rgba(0,0,0,.5)}
.url{position:absolute;left:%(m)dpx;top:%(ut)dpx;font-family:'B612 Mono',monospace;font-weight:700;font-size:%(us)dpx;color:#8ff5a8;letter-spacing:.06em;background:rgba(9,16,20,.88);border:1px solid #3a5058;border-radius:3px;padding:12px 24px}
.chk{position:absolute;right:%(m)dpx;top:%(m)dpx;width:%(cs)dpx;height:%(cs)dpx;background:""" + CHECK.replace("%", "%%") + """;background-size:%(cs2)dpx %(cs2)dpx;border-radius:3px;opacity:.95}
.han{position:absolute;right:%(hm)dpx;top:%(hy)dpx;font-family:'Noto Serif TC',serif;font-weight:900;font-size:%(hn)dpx;writing-mode:vertical-rl;letter-spacing:.2em;color:#f5efe3;text-shadow:0 2px 14px rgba(0,0,0,.6)}
.green{position:absolute;left:0;right:0;bottom:0;height:14px;background:#1f8a5b}</style></head><body><div class="c">
<div class="sh"></div><div class="chk"></div><div class="han">協和式客機</div>
<div class="k">NOW FLYABLE</div><h1>%(h1)s</h1><div class="s">%(sub)s</div><div class="url">flykaitak.com</div><div class="green"></div></div></body></html>"""

LAND = dict(w=1600, h=900, m=80, kt=80, ks=26, ht=150, hs=150, st=470, ss=44, ut=720, us=40, cs=220, cs2=88, hm=80, hy=330, hn=48,
            pos="50% 60%", shade="linear-gradient(90deg,rgba(6,12,15,.82) 0,rgba(6,12,15,.55) 45%,rgba(6,12,15,0) 80%)",
            h1="Fly<br>Concorde.", sub="At Kai Tak, Hong Kong 1998.<br>US$7 once, or free with a code.")
PORT = dict(w=1080, h=1350, m=70, kt=70, ks=28, ht=170, hs=190, st=560, ss=46, ut=1160, us=44, cs=200, cs2=80, hm=70, hy=330, hn=50,
            pos="50% 0%", shade="linear-gradient(180deg,rgba(6,12,15,.82) 0,rgba(6,12,15,.5) 45%,rgba(6,12,15,0) 75%)",
            h1="Fly<br>Concorde.", sub="At Kai Tak, Hong Kong 1998.<br>US$7 once, or free with a code.")


def uri(path, size):
    im = Image.open(path).convert("RGB")
    im.thumbnail(size)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main(out, dest, land_frame="yt/04-touchdown/f00030.jpg", port_frame="ig/04-touchdown/f00030.jpg"):
    dest.mkdir(parents=True, exist_ok=True)
    jobs = [("flykaitak-concorde-launch-1600x900.jpg", LAND, out / "frames" / land_frame, (1920, 1080)),
            ("flykaitak-concorde-launch-1080x1350.jpg", PORT, out / "frames" / port_frame, (1920, 1920))]
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        for name, cfg, frame, size in jobs:
            pg = b.new_page(viewport={"width": cfg["w"], "height": cfg["h"]})
            pg.set_content(PAGE % {**cfg, "img": uri(frame, size)}, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(dest / name), type="jpeg", quality=92)
            print("saved", dest / name)
        b.close()
