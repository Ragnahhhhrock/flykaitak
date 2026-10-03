#!/usr/bin/env python3
"""Render the Facebook and X/Twitter cover images in the Fly Kai Tak design system.

Usage:  python3 tools/covers.py
Outputs (assets/social):
  facebook-cover.jpg   820x312  (rendered at 2x = 1640x624)
  twitter-cover.jpg    1500x500 (rendered at 2x = 3000x1000, saved at 1500x500 + 2x copy)
Safe zones: X puts the avatar bottom-left and crops the top/bottom edge on some clients; Facebook crops
~90px off each side on mobile. Key text sits in the upper-left/centre, the URL bottom-right.
Needs: pip install playwright pillow.
"""
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "social"
FONTS = ("https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700"
         "&family=Noto+Serif+TC:wght@900&display=swap")
def _aerial():
    import base64, io
    from PIL import Image
    im = Image.open(ROOT / "assets" / "home" / "aerial-kai-tak.jpg").convert("RGB")
    im.thumbnail((1400, 1400))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


AERIAL = _aerial()
CHECK = "repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%)"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{fonts}">
<style>body{{margin:0;background:#0a1115}}
.c{{position:relative;width:{w}px;height:{h}px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',ui-sans-serif,system-ui,sans-serif}}
.photo{{position:absolute;top:0;right:0;width:{pw}px;height:{h}px;background:url('{aerial}') {pos}/cover;opacity:.9}}
.fade{{position:absolute;inset:0;background:linear-gradient(90deg,#0a1115 0,#0a1115 {f0}%,rgba(10,17,21,.78) {f1}%,rgba(10,17,21,.15) 100%)}}
.vig{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,17,21,.35),rgba(10,17,21,0) 30%,rgba(10,17,21,0) 70%,rgba(10,17,21,.55))}}
.k{{position:absolute;font-family:'B612 Mono',ui-monospace,monospace;letter-spacing:.22em;color:#ff6b5e;white-space:nowrap}}
h1{{position:absolute;margin:0;font-weight:700;letter-spacing:-.01em;color:#f5efe3;line-height:.95;white-space:nowrap}}
.t{{position:absolute;font-weight:700;color:#e9eee8;line-height:1.2}}
.han{{position:absolute;font-family:'Noto Serif TC','Songti TC','Noto Serif CJK TC',serif;font-weight:900;color:#f5efe3;letter-spacing:.16em;white-space:nowrap}}
.url{{position:absolute;font-family:'B612 Mono',ui-monospace,monospace;font-weight:700;color:#8ff5a8;letter-spacing:.06em;background:rgba(9,16,20,.86);border:1px solid #3a5058;border-radius:3px;white-space:nowrap}}
.turn{{position:absolute;display:flex;align-items:center;background:#101a1f;border:1px solid #3a5058;border-radius:3px;white-space:nowrap}}
.turn b{{font-family:'B612 Mono',ui-monospace,monospace;color:#8ff5a8;line-height:1}}
.turn i{{font-style:normal;display:flex;flex-direction:column}}
.turn i u{{text-decoration:none;color:#e9eee8;letter-spacing:.18em}}
.turn i s{{text-decoration:none;font-family:'B612 Mono',ui-monospace,monospace;color:#3bf0ff;letter-spacing:.14em}}
.green{{position:absolute;left:0;right:0;background:#1f8a5b}}
.chk{{position:absolute;left:0;right:0;background:{chk} 0 0/{cs}px {cs}px}}
</style></head><body>{body}</body></html>"""

# IGS path: 47 degree right turn, magenta with ink casing, drawn over the photo.
def igs(w, h, d, gates, sw):
    g = "".join(
        f'<g transform="translate({x} {y}) rotate({r})"><rect x="-{s/2}" y="-{s/2}" width="{s}" height="{s}" fill="none" stroke="#0a1115" stroke-width="{sw+4}"/>'
        f'<rect x="-{s/2}" y="-{s/2}" width="{s}" height="{s}" fill="none" stroke="#ff5ad9" stroke-width="{sw-2}"/></g>'
        for x, y, r, s in gates)
    return (f'<svg style="position:absolute;left:0;top:0" width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true">'
            f'<path d="{d}" fill="none" stroke="#0a1115" stroke-width="{sw+5}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#ff5ad9" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>{g}</svg>')


def twitter():
    w, h = 1500, 500
    body = f"""<div class="c">
<div class="photo" style="width:1000px"></div><div class="fade"></div><div class="vig"></div>
{igs(w, h, "M930 150 C1040 128 1150 170 1220 250 L1290 340", [(985,140,4,30),(1075,146,14,36),(1160,182,27,44)], 9)}
<div style="position:absolute;left:1330px;top:56px;width:112px;height:112px;border-radius:3px;background:{CHECK} 0 0/56px 56px;border:1px solid #3a5058"></div>
<div class="k" style="left:240px;top:70px;font-size:20px;line-height:24px">VHHH · IGS 13 · 1998</div>
<h1 style="left:236px;top:104px;font-size:128px">Fly Kai Tak</h1>
<div class="t" style="left:240px;top:252px;font-size:34px">Hit the checkerboard. Turn right.</div>
<div class="han" style="left:242px;top:318px;font-size:34px;line-height:40px">啟德機場</div>
<div class="url" style="right:48px;top:386px;font-size:26px;line-height:32px;padding:8px 16px">flykaitak.com</div>
<div class="green" style="top:452px;height:14px"></div>
<div class="chk" style="top:466px;height:34px" ></div>
</div>"""
    return w, h, body, dict(pw=1000, pos="62% 50%", f0=34, f1=58, chk=CHECK, cs=34)


def facebook():
    w, h = 820, 312
    body = f"""<div class="c">
<div class="photo" style="width:560px"></div><div class="fade"></div><div class="vig"></div>
{igs(w, h, "M566 100 C630 88 690 110 724 156 L744 200", [(594,96,4,18),(644,98,14,22),(694,118,27,28)], 6)}
<div class="k" style="left:120px;top:44px;font-size:13px;line-height:16px">VHHH · IGS 13 · 1998</div>
<h1 style="left:117px;top:66px;font-size:80px">Fly Kai Tak</h1>
<div class="t" style="left:120px;top:158px;font-size:22px">Hit the checkerboard. Turn right.</div>
<div class="han" style="left:121px;top:200px;font-size:22px;line-height:26px">啟德機場</div>
<div class="url" style="right:34px;top:232px;font-size:17px;line-height:22px;padding:5px 11px">flykaitak.com</div>
<div class="green" style="top:274px;height:10px"></div>
<div class="chk" style="top:284px;height:28px"></div>
</div>"""
    return w, h, body, dict(pw=560, pos="60% 50%", f0=30, f1=60, chk=CHECK, cs=28)


def render(p, name, spec, scale=2):
    w, h, body, kw = spec
    html = PAGE.format(fonts=FONTS, w=w, h=h, aerial=AERIAL, body=body, **kw)
    page = p.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
    page.set_content(html, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(600)
    tmp = OUT / f"{name}@2x.png"
    page.screenshot(path=str(tmp), clip={"x": 0, "y": 0, "width": w, "height": h})
    page.close()
    from PIL import Image
    im = Image.open(tmp).convert("RGB")
    im.resize((w, h), Image.LANCZOS).save(OUT / f"{name}.jpg", quality=92, optimize=True)
    im.save(OUT / f"{name}@2x.jpg", quality=90, optimize=True)
    tmp.unlink()
    print("wrote", OUT / f"{name}.jpg", (w, h))


if __name__ == "__main__":
    with sync_playwright() as p:
        b = p.chromium.launch()
        render(b, "facebook-cover", facebook())
        render(b, "twitter-cover", twitter())
        b.close()
