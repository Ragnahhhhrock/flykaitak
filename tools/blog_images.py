#!/usr/bin/env python3
"""Render the blog's header image and the social card for every post, in the Fly Kai Tak design system.

Usage:  python3 tools/blog_images.py            # header + all post cards
        python3 tools/blog_images.py <slug>     # one post card only

Outputs:
  assets/blog/header.jpg          1600x400 blog masthead (checkerboard, IGS path, approach gates, 747 plan view)
  assets/blog/og/<slug>.jpg       1200x630 card used for og:image, twitter:image and the post list
Cards read blog/posts.json (card_kicker, card_title, card_sub, card_image) and a screenshot in assets/blog/shots.
Needs: pip install playwright pillow.
"""
import html
import io
import json
import pathlib
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ("https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700"
         "&family=Noto+Serif+TC:wght@900&display=swap")

# The checkerboard + IGS path + gates + aircraft plan view, copied from assets/social/youtube-thumbnail.html
ART = """
<div style="position:absolute;left:724px;top:76px;width:{blockw}px;height:520px;border-radius:3px;background:repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%) 0 0/208px 208px"></div>
<svg style="position:absolute;left:0;top:0" width="1280" height="720" viewBox="0 0 1280 720" aria-hidden="true">
<path d="M640 90 C860 80, 1010 150, 1050 290 L1090 430" fill="none" stroke="#0a1115" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M640 90 C860 80, 1010 150, 1050 290 L1090 430" fill="none" stroke="#ff5ad9" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
<g transform="translate(734 91) rotate(4)"><rect x="-17" y="-17" width="34" height="34" fill="none" stroke="#0a1115" stroke-width="11"/><rect x="-17" y="-17" width="34" height="34" fill="none" stroke="#ff5ad9" stroke-width="5"/></g>
<g transform="translate(833 106) rotate(14)"><rect x="-21" y="-21" width="42" height="42" fill="none" stroke="#0a1115" stroke-width="11"/><rect x="-21" y="-21" width="42" height="42" fill="none" stroke="#ff5ad9" stroke-width="5"/></g>
<g transform="translate(921 138) rotate(27)"><rect x="-26" y="-26" width="52" height="52" fill="none" stroke="#0a1115" stroke-width="11"/><rect x="-26" y="-26" width="52" height="52" fill="none" stroke="#ff5ad9" stroke-width="5"/></g>
<g transform="translate(1041 256) rotate(149) scale(1.05)" fill="#000" opacity="0.3">
<path d="M0 -100 C9 -100 11 -78 11 -56 L11 66 C11 84 6 98 0 102 C-6 98 -11 84 -11 66 L-11 -56 C-11 -78 -9 -100 0 -100 Z"/><path d="M10 -22 L102 46 L102 58 L10 24 Z"/><path d="M-10 -22 L-102 46 L-102 58 L-10 24 Z"/><path d="M10 72 L44 94 L44 102 L10 92 Z"/><path d="M-10 72 L-44 94 L-44 102 L-10 92 Z"/></g>
<g transform="translate(1025 232) rotate(149) scale(1.05)" stroke="#0a1115" stroke-width="3.5" stroke-linejoin="round">
<path d="M10 -22 L102 46 L102 58 L10 24 Z" fill="#a9aeb1"/><path d="M-10 -22 L-102 46 L-102 58 L-10 24 Z" fill="#a9aeb1"/><path d="M10 72 L44 94 L44 102 L10 92 Z" fill="#a9aeb1"/><path d="M-10 72 L-44 94 L-44 102 L-10 92 Z" fill="#a9aeb1"/>
<rect x="40" y="-12" width="13" height="32" rx="6.5" fill="#3a5058"/><rect x="-53" y="-12" width="13" height="32" rx="6.5" fill="#3a5058"/>
<path d="M0 -100 C9 -100 11 -78 11 -56 L11 66 C11 84 6 98 0 102 C-6 98 -11 84 -11 66 L-11 -56 C-11 -78 -9 -100 0 -100 Z" fill="#f6f5f0"/>
<rect x="-4.5" y="-40" width="9" height="104" fill="#005f4b" stroke="none"/><path d="M-6 -80 L6 -80 L5 -69 L-5 -69 Z" fill="#10201b" stroke="none"/></g>
</svg>
<div style="position:absolute;left:1160px;top:40px;width:84px;box-sizing:border-box;padding:16px 14px;display:flex;flex-direction:column;align-items:center;background:rgba(9,16,20,.86);border:1px solid #3a5058;border-radius:3px;font-family:'Noto Serif TC','Songti TC','PMingLiU','SimSun',serif;font-weight:900;font-size:56px;line-height:1.08;color:#f5efe3"><span>啟</span><span>德</span><span>機</span><span>場</span></div>
"""


def header_html():
    # Art box is 1280x720 (thumbnail space); scale and park it at the right of a 1600x400 banner.
    s, tx, ty = 0.82, 330, -42
    art = ART.replace("{blockw}", "1060")
    return f"""<!doctype html><meta charset=utf-8><link rel=stylesheet href="{FONTS}">
<body style="margin:0;background:#0a1115"><div style="position:relative;width:1600px;height:400px;overflow:hidden;background:#0a1115">
<div style="position:absolute;left:0;top:0;width:1600px;height:720px;transform-origin:0 0;transform:translate({tx}px,{ty}px) scale({s})">{art}</div>
<div style="position:absolute;left:0;top:0;width:700px;height:400px;background:linear-gradient(90deg,#0a1115 0,#0a1115 55%,rgba(10,17,21,0) 100%)"></div>
<div style="position:absolute;left:0;right:0;bottom:0;height:3px;background:#1b7d52"></div>
</div></body>"""


def card_html(p, shot_b64):
    t = html.escape
    return f"""<!doctype html><meta charset=utf-8><link rel=stylesheet href="{FONTS}">
<body style="margin:0;background:#0a1115"><div style="position:relative;width:1200px;height:630px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',sans-serif">
<img src="data:image/jpeg;base64,{shot_b64}" style="position:absolute;left:300px;top:0;width:900px;height:600px;object-fit:cover;object-position:{p.get('card_focus', 50)}% 50%">
<div style="position:absolute;left:0;top:0;width:900px;height:600px;background:linear-gradient(90deg,#0a1115 0,#0a1115 34%,rgba(10,17,21,.82) 52%,rgba(10,17,21,0) 78%)"></div>
<div style="position:absolute;left:64px;top:56px;display:flex;align-items:center;gap:14px">
  <svg width="56" height="56" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0a1115"/><g transform="translate(8 8)"><rect width="48" height="48" fill="#f5efe3"/><path fill="#e8571f" d="M0 0h12v12H0zM24 0h12v12H24zM12 12h12v12H12zM36 12h12v12H36zM0 24h12v12H0zM24 24h12v12H24zM12 36h12v12H12zM36 36h12v12H36z"/></g><path d="M4 21 C 24 20, 36 26, 44 38 L 58 58" fill="none" stroke="#0a1115" stroke-width="9" stroke-linecap="round"/><path d="M4 21 C 24 20, 36 26, 44 38 L 58 58" fill="none" stroke="#1f8a5b" stroke-width="5" stroke-linecap="round"/></svg>
  <div style="font-family:'B612 Mono',monospace;font-size:18px;letter-spacing:.22em;color:#ff6b5e;text-transform:uppercase">Fly Kai Tak · Blog</div>
</div>
<div style="position:absolute;left:64px;top:150px;width:640px;display:flex;flex-direction:column;gap:26px">
  <div style="font-size:76px;line-height:1.02;font-weight:700;letter-spacing:-.01em">{t(p['card_title'])}</div>
  <div style="font-size:30px;line-height:1.3;width:560px">{t(p['card_sub'])}</div>
</div>
<div style="position:absolute;left:64px;top:512px;font-family:'B612 Mono',monospace;font-size:20px;letter-spacing:.18em;color:#8ff5a8">{t(p['card_kicker'])}</div>
<div style="position:absolute;right:30px;bottom:44px;font-family:'B612 Mono',monospace;font-size:22px;letter-spacing:.06em;background:rgba(9,16,20,.88);padding:8px 16px;border-radius:3px;color:#e9eee8">flykaitak.com/blog</div>
<div style="position:absolute;left:0;right:0;top:600px;height:6px;background:#1b7d52"></div>
<div style="position:absolute;left:0;right:0;top:606px;height:24px;background:repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%) 0 0/24px 24px"></div>
</div></body>"""


def snap(page, markup, w, h, out):
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(markup, wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(600)
    im = Image.open(io.BytesIO(page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}))).convert("RGB")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=88, optimize=True, progressive=True)
    print("saved", out.relative_to(ROOT), flush=True)


def main():
    import base64
    only = sys.argv[1] if len(sys.argv) > 1 else None
    posts = json.load(open(ROOT / "blog/posts.json", encoding="utf-8"))
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page()
        if not only:
            snap(pg, header_html(), 1600, 400, ROOT / "assets/blog/header.jpg")
        for post in posts:
            if only and post["slug"] != only:
                continue
            im = Image.open(ROOT / "assets/blog/shots" / f"{post['card_image']}.jpg").convert("RGB")
            im = im.crop((0, 90, im.width, im.height - 120))  # drop the sim's button bar and bottom readouts
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=90)
            snap(pg, card_html(post, base64.b64encode(buf.getvalue()).decode()), 1200, 630,
                 ROOT / "assets/blog/og" / f"{post['slug']}.jpg")
        b.close()


if __name__ == "__main__":
    main()
