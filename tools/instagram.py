#!/usr/bin/env python3
"""Render the Instagram assets in the Fly Kai Tak design system.

Usage:  python3 tools/instagram.py
Outputs (assets/social/instagram):
  profile.png                      1080x1080 (shown as a circle)
  post-1-welcome.jpg ... post-3    1080x1350 (4:5 feed posts; key text sits in the centre 3:4 for the grid crop)
  story-1-welcome.jpg, story-2-turn.jpg, story-3-report-card.jpg   1080x1920 (text kept out of the top 250 / bottom 340 px)
  highlight-play/turn/apron/scores.png   1080x1920 highlight covers (icon in the centre circle)
Photos come from the sim's own screenshots (cockpit off). No real airline names or logos.
Needs: pip install playwright pillow.
"""
import pathlib
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import facebook_page as fb  # noqa: E402

ROOT = fb.ROOT
OUT = ROOT / "assets" / "social" / "instagram"
CHECK = fb.CHECK

CSS = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{fonts}">
<style>body{{margin:0;background:#0a1115}}
.c{{position:relative;width:{w}px;height:{h}px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',ui-sans-serif,system-ui,sans-serif}}
.photo{{position:absolute;inset:0;background:url('{photo}') {pos}/cover}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,17,21,.55) 0,rgba(10,17,21,0) 25%,rgba(10,17,21,.7) 52%,rgba(10,17,21,.97) 100%)}}
.k{{position:absolute;left:72px;font-family:'B612 Mono',ui-monospace,monospace;letter-spacing:.22em;font-size:26px;color:#ff8a7e;text-shadow:0 2px 8px #0a1115;white-space:nowrap}}
h1{{position:absolute;left:70px;margin:0;font-weight:700;font-size:112px;text-shadow:0 3px 18px rgba(10,17,21,.7);line-height:1.02;letter-spacing:-.01em;color:#f5efe3;width:930px}}
.s{{position:absolute;left:72px;font-weight:700;font-size:38px;line-height:1.3;color:#e9eee8;width:940px;font-size:34px}}
.han{{position:absolute;left:74px;font-family:'Noto Serif TC','Noto Serif CJK TC',serif;font-weight:900;font-size:36px;letter-spacing:.16em;color:#f5efe3}}
.url{{position:absolute;left:72px;font-family:'B612 Mono',ui-monospace,monospace;font-weight:700;font-size:32px;color:#8ff5a8;letter-spacing:.06em;background:rgba(9,16,20,.88);border:1px solid #3a5058;border-radius:3px;padding:10px 20px;white-space:nowrap}}
.green{{position:absolute;left:0;right:0;height:14px;background:#1f8a5b}}
.chk{{position:absolute;left:0;right:0;height:42px;background:{chk} 0 0/42px 42px}}
</style></head><body>{body}</body></html>"""


def layout(w, h, photo, pos, kicker, headline, lines, sub, bottom, extra=""):
    """Vertical post: text block stacked from the bottom edge up to the checker strip."""
    hh = int(lines * 114)
    sub_h = 100 if sub else 0
    url_top = h - bottom - 70
    sub_top = url_top - 40 - sub_h if sub else url_top
    han_top = sub_top - 70
    h1_top = han_top - 24 - hh
    k_top = h1_top - 54
    body = f"""<div class="c"><div class="photo"></div><div class="shade"></div>{extra}
<div class="k" style="top:{k_top}px">{kicker}</div>
<h1 style="top:{h1_top}px">{headline}</h1>
<div class="han" style="top:{han_top}px">啟德機場</div>
{f'<div class="s" style="top:{sub_top}px">{sub}</div>' if sub else ''}
<div class="url" style="top:{url_top}px">flykaitak.com</div>
<div class="green" style="bottom:42px"></div><div class="chk" style="bottom:0"></div></div>"""
    return dict(w=w, h=h, body=body, photo=photo, pos=pos)


def igs(w, h, d, gates):
    g = "".join(
        f'<g transform="translate({x} {y}) rotate({r})"><rect x="-{s/2}" y="-{s/2}" width="{s}" height="{s}" fill="none" stroke="#0a1115" stroke-width="16"/>'
        f'<rect x="-{s/2}" y="-{s/2}" width="{s}" height="{s}" fill="none" stroke="#ff5ad9" stroke-width="8"/></g>' for x, y, r, s in gates)
    return (f'<svg style="position:absolute;left:0;top:0" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<path d="{d}" fill="none" stroke="#0a1115" stroke-width="18" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#ff5ad9" stroke-width="11" stroke-linecap="round"/>{g}</svg>')


def report_story(uri):
    body = f"""<div class="c" style="background:#0a1115">
<div class="k" style="top:430px">YOUR LANDING, GRADED</div>
<div style="position:absolute;left:0;top:490px;width:1080px;height:567px;background:url('{uri}') center/cover"></div>
<h1 style="top:1100px;font-size:96px">Can you make<br>Captain?</h1>
<div class="s" style="top:1330px">90+ out of 100 is Captain.</div>
<div class="url" style="top:1420px">flykaitak.com</div>
<div class="green" style="bottom:42px"></div><div class="chk" style="bottom:0"></div></div>"""
    return dict(w=1080, h=1920, body=body, photo="", pos="center")


def highlight(label, icon_svg):
    body = f"""<div class="c" style="background:#17262d">
<div style="position:absolute;left:290px;top:690px;width:500px;height:500px;border-radius:50%;background:#0a1115;border:6px solid #1f8a5b;display:flex;align-items:center;justify-content:center">{icon_svg}</div>
<div class="han" style="left:0;right:0;top:1250px;text-align:center;font-size:44px;letter-spacing:.1em">{label}</div></div>"""
    return dict(w=1080, h=1920, body=body, photo="", pos="center")


def render(browser, name, spec, ext="jpg"):
    html = CSS.format(fonts=fb.FONTS, chk=CHECK, **spec)
    page = browser.new_page(viewport={"width": spec["w"], "height": spec["h"]}, device_scale_factor=1)
    page.set_content(html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(600)
    tmp = OUT / f"{name}.tmp.png"
    page.screenshot(path=str(tmp), clip={"x": 0, "y": 0, "width": spec["w"], "height": spec["h"]})
    page.close()
    im = Image.open(tmp).convert("RGB")
    im.save(OUT / f"{name}.{ext}", **({"optimize": True} if ext == "png" else {"quality": 92, "optimize": True}))
    tmp.unlink()
    print("wrote", OUT / f"{name}.{ext}", im.size)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shots = ROOT / "assets" / "blog" / "shots"
    dusk = fb.data_uri(shots / "tod-dusk-igs.jpg")
    pier = fb.data_uri(shots / "kai-tak-terminal-pier.jpg")
    aerial = fb.data_uri(ROOT / "assets" / "home" / "aerial-kai-tak.jpg")
    card = fb.data_uri(shots / "report-card-image.jpg")

    turn_post = igs(1080, 1350, "M180 330 C330 300 520 360 650 480 L770 640", [(240, 322, 4, 44), (380, 330, 14, 56), (520, 380, 27, 70)])
    turn_story = igs(1080, 1920, "M170 520 C320 490 520 550 650 670 L770 840", [(230, 512, 4, 44), (370, 520, 14, 56), (510, 570, 27, 70)])
    mark = fb.MARK.replace("<svg ", '<svg width="330" height="330" ', 1)
    plane = ('<svg width="260" height="260" viewBox="-110 -110 220 220"><g transform="rotate(-35)" fill="#e9eee8">'
             '<path d="M0 -100 C9 -100 11 -78 11 -56 L11 66 C11 84 6 98 0 102 C-6 98 -11 84 -11 66 L-11 -56 C-11 -78 -9 -100 0 -100 Z"/>'
             '<path d="M10 -22 L102 46 L102 58 L10 24 Z"/><path d="M-10 -22 L-102 46 L-102 58 L-10 24 Z"/>'
             '<path d="M10 72 L44 94 L44 102 L10 92 Z"/><path d="M-10 72 L-44 94 L-44 102 L-10 92 Z"/></g></svg>')
    pier_icon = '<svg width="260" height="260" viewBox="0 0 100 100"><g fill="none" stroke="#e9eee8" stroke-width="5"><rect x="10" y="22" width="80" height="18"/><path d="M22 40v26M40 40v26M58 40v26M76 40v26"/></g><g fill="#ff6b5e"><circle cx="22" cy="72" r="6"/><circle cx="40" cy="72" r="6"/><circle cx="58" cy="72" r="6"/><circle cx="76" cy="72" r="6"/></g></svg>'
    score_icon = '<div style="font-family:B612,sans-serif;font-weight:700;font-size:250px;color:#8ff5a8;line-height:1">B</div>'

    specs = {
        "post-1-welcome": layout(1080, 1350, dusk, "55% 50%", "VHHH · IGS 13 · 1998", "Fly into<br>Kai Tak", 2, "The 1998 Runway 13 approach. Free in your browser.", 130),
        "post-2-turn": layout(1080, 1350, aerial, "58% 50%", "47° RIGHT TURN", "Hit the<br>checkerboard.<br>Turn right.", 3, "", 130, turn_post),
        "post-3-apron": layout(1080, 1350, pier, "50% 50%", "THE 1998 APRON", "Eight stands.<br>Jet bridges.", 2, "Pushback tugs and apron buses, built from the Kai Tak chart.", 130),
        "story-1-welcome": layout(1080, 1920, dusk, "52% 50%", "VHHH · IGS 13 · 1998", "Fly into<br>Kai Tak", 2, "Free in your browser.", 340),
        "story-2-turn": layout(1080, 1920, aerial, "60% 50%", "47° RIGHT TURN", "Hit the<br>checkerboard.<br>Turn right.", 3, "", 340, turn_story),
        "story-3-report-card": report_story(card),
    }
    with sync_playwright() as p:
        b = p.chromium.launch()
        fbp = fb.profile()
        fbp["body"] = fbp["body"].replace("740px", "740px")
        fb.OUT = OUT
        fb.render(b, "profile", fbp, "png")
        for name, spec in specs.items():
            render(b, name, spec)
        for name, label, icon in [("highlight-play", "PLAY", mark), ("highlight-turn", "THE TURN", plane),
                                  ("highlight-apron", "APRON", pier_icon), ("highlight-scores", "SCORES", score_icon)]:
            render(b, name, highlight(label, icon), "png")
        b.close()


if __name__ == "__main__":
    main()
