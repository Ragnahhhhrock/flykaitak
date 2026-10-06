#!/usr/bin/env python3
"""Render the end card of the social reel in the Fly Kai Tak design system.

Usage:  python3 tools/reel_card.py OUT_DIR
Outputs OUT_DIR/card-yt.png (1920x1080) and OUT_DIR/card-ig.png (1080x1920).
Needs: pip install playwright (Chromium is already present in the Claude workspace).
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

CHECK = "repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%)"
HTML = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700&family=Noto+Serif+TC:wght@900&display=swap">
<style>
body{{margin:0;background:#0a1115}}
.c{{position:relative;width:{w}px;height:{h}px;overflow:hidden;background:#0a1115;color:#e9eee8;font-family:'B612',ui-sans-serif,system-ui,sans-serif}}
.chk{{position:absolute;background:{chk};border-radius:3px}}
.k{{position:absolute;font-family:'B612 Mono',ui-monospace,monospace;letter-spacing:.22em;color:#ff8a7e;white-space:nowrap}}
h1{{position:absolute;margin:0;font-weight:700;letter-spacing:-.01em;line-height:.95;color:#f5efe3}}
.s{{position:absolute;font-weight:700;line-height:1.15;color:#e9eee8}}
.url{{position:absolute;font-family:'B612 Mono',ui-monospace,monospace;font-weight:700;color:#8ff5a8;letter-spacing:.06em;background:rgba(9,16,20,.88);border:1px solid #3a5058;border-radius:3px;white-space:nowrap}}
.han{{position:absolute;font-family:'Noto Serif TC','Noto Serif CJK TC',serif;font-weight:900;color:#f5efe3}}
.green{{position:absolute;left:0;right:0;background:#1f8a5b}}
</style></head><body>{body}</body></html>"""

YT = """<div class="c">
<div class="chk" style="left:1180px;top:150px;width:600px;height:600px;background-size:240px 240px"></div>
<svg style="position:absolute;left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">
<path d="M880 170 C1180 150 1420 250 1500 450 L1560 640" fill="none" stroke="#0a1115" stroke-width="30" stroke-linecap="round"/>
<path d="M880 170 C1180 150 1420 250 1500 450 L1560 640" fill="none" stroke="#1f8a5b" stroke-width="16" stroke-linecap="round"/></svg>
<div class="k" style="left:120px;top:210px;font-size:30px">VHHH · IGS 13 · 1998</div>
<h1 style="left:114px;top:262px;font-size:210px">Fly<br>Kai Tak</h1>
<div class="s" style="left:120px;top:700px;font-size:60px">Hit the checkerboard.<br>Turn right.</div>
<div class="url" style="left:120px;top:900px;font-size:44px;padding:16px 30px">flykaitak.com</div>
<div class="han" style="left:1818px;top:150px;font-size:60px;line-height:1.25;writing-mode:vertical-rl;letter-spacing:.2em">啟德機場</div>
<div class="green" style="bottom:0;height:18px"></div></div>"""

IG = """<div class="c">
<div class="chk" style="left:190px;top:270px;width:700px;height:700px;background-size:280px 280px"></div>
<svg style="position:absolute;left:0;top:0" width="1080" height="1920" viewBox="0 0 1080 1920">
<path d="M70 360 C360 330 650 430 740 650 L800 900" fill="none" stroke="#0a1115" stroke-width="34" stroke-linecap="round"/>
<path d="M70 360 C360 330 650 430 740 650 L800 900" fill="none" stroke="#1f8a5b" stroke-width="18" stroke-linecap="round"/></svg>
<div class="han" style="left:96px;top:1000px;font-size:48px;letter-spacing:.2em">啟德機場</div>
<div class="k" style="left:96px;top:1078px;font-size:28px">VHHH · IGS 13 · 1998</div>
<h1 style="left:90px;top:1130px;font-size:158px;white-space:nowrap">Fly Kai Tak</h1>
<div class="s" style="left:96px;top:1330px;font-size:54px">Hit the checkerboard. Turn right.</div>
<div class="url" style="left:96px;top:1430px;font-size:46px;padding:16px 30px">flykaitak.com</div>
<div class="green" style="bottom:0;height:18px"></div></div>"""


def main():
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        for name, (w, h, body) in {"yt": (1920, 1080, YT), "ig": (1080, 1920, IG)}.items():
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.set_content(HTML.format(w=w, h=h, chk=CHECK, body=body), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(out / f"card-{name}.png"))
            pg.close()
        b.close()


if __name__ == "__main__":
    main()
