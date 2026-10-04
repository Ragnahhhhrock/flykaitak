#!/usr/bin/env python3
"""Render the Facebook page images in the Fly Kai Tak design system.

Usage:  python3 tools/facebook_page.py
Outputs (assets/social/facebook):
  profile.png            1080x1080 (Facebook shows a circle: the mark sits inside the safe circle)
  post-welcome.jpg       1200x630  launch post
  post-checkerboard.jpg  1200x630  the 47 degree turn
  post-terminal.jpg      1200x630  the 1998 apron
  post-report-card.jpg   1200x630  copy of the share-card image
  cover.jpg / cover@2x.jpg  copies of assets/social/facebook-cover*.jpg (820x312 / 1640x624)
Photos come from the sim's own screenshots (cockpit off). No real airline names or logos.
Needs: pip install playwright pillow.
"""
import base64
import io
import pathlib
import shutil

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "social" / "facebook"
FONTS = ("https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700"
         "&family=Noto+Serif+TC:wght@900&display=swap")
CHECK = "repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%)"


def data_uri(path, width=1800):
    im = Image.open(path).convert("RGB")
    im.thumbnail((width, width))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


MARK = (ROOT / "assets" / "brand" / "mark.svg").read_text()

PAGE = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{fonts}">
<style>body{{margin:0;background:#0a1115}}
.c{{position:relative;width:{w}px;height:{h}px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',ui-sans-serif,system-ui,sans-serif}}
.photo{{position:absolute;inset:0;background:url('{photo}') {pos}/cover}}
.fade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,17,21,.96) 0,rgba(10,17,21,.82) 38%,rgba(10,17,21,.15) 78%,rgba(10,17,21,0) 100%)}}
.vig{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,17,21,.35),rgba(10,17,21,0) 28%,rgba(10,17,21,0) 70%,rgba(10,17,21,.55))}}
.k{{position:absolute;left:64px;top:72px;font-family:'B612 Mono',ui-monospace,monospace;letter-spacing:.22em;font-size:20px;color:#ff6b5e;white-space:nowrap}}
h1{{position:absolute;left:62px;top:116px;margin:0;font-weight:700;font-size:84px;line-height:1.02;letter-spacing:-.01em;color:#f5efe3;width:620px}}
.s{{position:absolute;left:64px;font-weight:700;font-size:30px;line-height:1.3;color:#e9eee8;width:560px}}
.han{{position:absolute;left:66px;font-family:'Noto Serif TC','Noto Serif CJK TC',serif;font-weight:900;font-size:30px;letter-spacing:.16em;color:#f5efe3}}
.url{{position:absolute;right:48px;bottom:84px;font-family:'B612 Mono',ui-monospace,monospace;font-weight:700;font-size:26px;color:#8ff5a8;letter-spacing:.06em;background:rgba(9,16,20,.88);border:1px solid #3a5058;border-radius:3px;padding:8px 16px}}
.green{{position:absolute;left:0;right:0;bottom:34px;height:12px;background:#1f8a5b}}
.chk{{position:absolute;left:0;right:0;bottom:0;height:34px;background:{chk} 0 0/34px 34px}}
</style></head><body>{body}</body></html>"""


def post(photo, pos, kicker, headline, sub, han=True, extra=""):
    body = f"""<div class="c"><div class="photo"></div><div class="fade"></div><div class="vig"></div>{extra}
<div class="k">{kicker}</div>
<h1>{headline}</h1>
<div class="s" style="top:{{subtop}}px">{sub}</div>
{'<div class="han" style="top:{hantop}px">啟德機場</div>' if han else ''}
<div class="url">flykaitak.com</div><div class="green"></div><div class="chk"></div></div>"""
    return dict(w=1200, h=630, body=body, photo=photo, pos=pos)


def finish(spec, lines):
    # headline height drives where the subtitle goes (84px * 1.02 per line)
    subtop = 116 + int(lines * 86) + 22
    spec["body"] = spec["body"].replace("{subtop}", str(subtop)).replace("{hantop}", str(subtop + 120))
    return spec


def profile():
    body = f"""<div class="c" style="background:#17262d">
<div style="position:absolute;left:170px;top:170px;width:740px;height:740px;filter:drop-shadow(0 12px 30px rgba(0,0,0,.35))">{MARK.replace('<svg ', '<svg width="740" height="740" ', 1)}</div>
</div>"""
    return dict(w=1080, h=1080, body=body, photo="", pos="center")


def render(browser, name, spec, ext="jpg"):
    html = PAGE.format(fonts=FONTS, chk=CHECK, **spec)
    page = browser.new_page(viewport={"width": spec["w"], "height": spec["h"]}, device_scale_factor=1)
    page.set_content(html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(600)
    tmp = OUT / f"{name}.tmp.png"
    page.screenshot(path=str(tmp), clip={"x": 0, "y": 0, "width": spec["w"], "height": spec["h"]})
    page.close()
    im = Image.open(tmp).convert("RGB")
    if ext == "png":
        im.save(OUT / f"{name}.png", optimize=True)
    else:
        im.save(OUT / f"{name}.jpg", quality=92, optimize=True)
    tmp.unlink()
    print("wrote", OUT / f"{name}.{ext}", im.size)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shots = ROOT / "assets" / "blog" / "shots"
    dusk = data_uri(shots / "tod-dusk-igs.jpg")
    pier = data_uri(shots / "kai-tak-terminal-pier.jpg")
    aerial = data_uri(ROOT / "assets" / "home" / "aerial-kai-tak.jpg")

    igs = ('<svg style="position:absolute;left:0;top:0" width="1200" height="630" viewBox="0 0 1200 630" aria-hidden="true">'
           '<path d="M690 190 C800 168 910 214 980 300 L1050 400" fill="none" stroke="#0a1115" stroke-width="15" stroke-linecap="round"/>'
           '<path d="M690 190 C800 168 910 214 980 300 L1050 400" fill="none" stroke="#ff5ad9" stroke-width="10" stroke-linecap="round"/>'
           + "".join(f'<g transform="translate({x} {y}) rotate({r})"><rect x="-{s/2}" y="-{s/2}" width="{s}" height="{s}" fill="none" stroke="#0a1115" stroke-width="14"/>'
                     f'<rect x="-{s/2}" y="-{s/2}" width="{s}" height="{s}" fill="none" stroke="#ff5ad9" stroke-width="7"/></g>'
                     for x, y, r, s in [(745, 184, 4, 34), (835, 190, 14, 42), (920, 226, 27, 52)])
           + '</svg>')

    specs = {
        "post-welcome": finish(post(dusk, "50% 60%", "VHHH · IGS 13 · 1998", "Fly into<br>Kai Tak", "The 1998 Runway 13 approach, free in your browser."), 2),
        "post-checkerboard": finish(post(aerial, "60% 50%", "47° RIGHT TURN", "Hit the checkerboard.<br>Turn right.", "Then land before the harbour.", extra=igs), 3),
        "post-terminal": finish(post(pier, "50% 70%", "THE 1998 APRON", "Eight stands.<br>Jet bridges.", "Built from the Kai Tak chart, with pushback tugs and apron buses."), 2),
    }
    with sync_playwright() as p:
        b = p.chromium.launch()
        render(b, "profile", profile(), "png")
        for name, spec in specs.items():
            render(b, name, spec)
        b.close()

    shutil.copy(shots / "report-card-image.jpg", OUT / "post-report-card.jpg")
    shutil.copy(ROOT / "assets" / "social" / "facebook-cover.jpg", OUT / "cover.jpg")
    shutil.copy(ROOT / "assets" / "social" / "facebook-cover@2x.jpg", OUT / "cover@2x.jpg")
    print("copied report card and cover")


if __name__ == "__main__":
    main()
