#!/usr/bin/env python3
"""Build the Fly Kai Tak merch shop at https://flykaitak.com/shop/.

  assets/shop/products.json   the products (newest layout order), prices in AUD
  assets/shop/<slug>.svg      product artwork, inlined into the page (so the site fonts apply)
  assets/shop/shop.css        shop styles (on top of assets/blog/blog.css)
  assets/shop/og.jpg          1200x630 social card for the shop (render with --images)
  assets/shop/<slug>.jpg      800x800 product images for structured data and sharing (render with --images)

Each product's "checkout" is a Stripe Payment Link (https://buy.stripe.com/...). While it is empty the button is
"Notify me" and emails contact@flykaitak.com instead; no payment is taken. Paste a link in and rebuild to sell it.
Usage: python3 tools/shop.py [--images]
"""
import json
import pathlib
import re
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blog import E, NAME, SITE, head, site_footer, site_header  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOP = ROOT / "assets/shop"
OUT = ROOT / "shop/index.html"
URL = f"{SITE}/shop/"
EMAIL = "contact@flykaitak.com"
STRIPE = re.compile(r"^https://(buy|donate)\.stripe\.com/")

TITLE = "Fly Kai Tak shop: Kai Tak tees, caps, patches and prints"
DESC = ("Fly Kai Tak merch: checkerboard tees, a Runway 13 cap, a 1998 patch, an enamel pin, a poster, a mug and stickers. "
        "Prices in AUD.")


def load():
    items = json.load(open(SHOP / "products.json", encoding="utf-8"))
    for p in items:
        for k in ("slug", "name", "zh", "price", "kind", "kind_zh", "desc", "desc_zh", "specs", "specs_zh"):
            assert p.get(k) not in (None, ""), f"products.json: {p.get('slug')} missing {k}"
        assert (SHOP / f"{p['slug']}.svg").exists(), f"missing assets/shop/{p['slug']}.svg"
        c = p.get("checkout", "")
        assert not c or STRIPE.match(c), f"{p['slug']}: checkout must be a Stripe Payment Link"
    return items


def art(slug):
    svg = (SHOP / f"{slug}.svg").read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*>\s*", "", svg).strip()
    return svg.replace("<svg ", '<svg class="art" ', 1)


def button(p):
    if p.get("checkout"):
        return (f'<a class="btn go buy" href="{E(p["checkout"])}" target="_blank" rel="noopener" data-item="{p["slug"]}" '
                f'data-method="checkout" data-zh="購買 · A${p["price"]}">Buy · A${p["price"]}</a>')
    q = urllib.parse.urlencode({"subject": f"Fly Kai Tak merch: {p['name']}",
                                "body": f"Hi, please let me know when the {p['name']} (A${p['price']}) is available.\n\nSize (if any):\nCountry:\n"},
                               quote_via=urllib.parse.quote)
    return (f'<a class="btn notify" href="mailto:{EMAIL}?{q}" data-item="{p["slug"]}" data-method="notify" '
            f'data-zh="有貨通知我">Notify me</a>')


def product(p):
    specs = "".join(f'<li data-zh="{E(z)}">{E(s)}</li>' for s, z in zip(p["specs"], p["specs_zh"]))
    status = ('<span class="stock in" data-zh="有貨">In stock</span>' if p.get("checkout")
              else '<span class="stock soon" data-zh="即將推出">Coming soon</span>')
    return f"""<article class="prod" id="{p['slug']}" data-kind="{E(p['kind'])}">
  <div class="tile">{art(p['slug'])}{status}</div>
  <div class="pbody">
    <p class="kind" data-zh="{E(p['kind_zh'])}">{E(p['kind'])}</p>
    <h3><span data-zh="{E(p['zh'])}">{E(p['name'])}</span></h3>
    <p class="price"><b>A${p['price']}</b> <span>AUD</span></p>
    <p class="desc" data-zh="{E(p['desc_zh'])}">{E(p['desc'])}</p>
    <ul class="specs">{specs}</ul>
    {button(p)}
  </div>
</article>"""


def page(items):
    live = any(p.get("checkout") for p in items)
    kinds = []
    for p in items:
        if (p["kind"], p["kind_zh"]) not in kinds:
            kinds.append((p["kind"], p["kind_zh"]))
    chips = '<button type="button" class="on" data-k="" aria-pressed="true" data-zh="全部">All</button>' + "".join(
        f'<button type="button" data-k="{E(k)}" aria-pressed="false" data-zh="{E(z)}">{E(k)}</button>' for k, z in kinds)
    if live:
        how = ("Checkout is a secure Stripe page. Prices are in Australian dollars; shipping is added at checkout.",
               "結帳用安全嘅 Stripe 頁面。價錢以澳元計，運費喺結帳時加。")
    else:
        how = ("The first run is being made. Tap Notify me to email us and we will reply when it is ready to order. "
               "No payment is taken yet.",
               "第一批貨製作緊。撳「有貨通知我」電郵俾我哋，有得訂嘅時候會回覆你。暫時唔會收錢。")
    avail = "https://schema.org/InStock"
    ld = [{
        "@context": "https://schema.org", "@type": "ItemList", "name": f"{NAME} shop", "url": URL,
        "itemListElement": [{
            "@type": "ListItem", "position": i + 1,
            "item": {"@type": "Product", "name": p["name"], "description": p["desc"], "sku": p["slug"],
                     "image": f"{SITE}/assets/shop/{p['slug']}.jpg", "brand": {"@type": "Brand", "name": NAME},
                     "url": f"{URL}#{p['slug']}",
                     "offers": {"@type": "Offer", "price": f"{p['price']:.2f}", "priceCurrency": "AUD",
                                "availability": avail if p.get("checkout") else "https://schema.org/PreOrder",
                                "url": f"{URL}#{p['slug']}"}}} for i, p in enumerate(items)]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": NAME, "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Shop", "item": URL}]}]
    h = head(TITLE, DESC, URL, f"{SITE}/assets/shop/og.jpg",
             "Fly Kai Tak merch: a checkerboard tee, a jade cap, a round patch and an enamel pin on a dark background.",
             keywords=["Kai Tak merch", "Kai Tak t-shirt", "aviation gifts", "Hong Kong 1998", "checkerboard", "flight simulator"],
             jsonld=ld, zh_title=f"商店 | {NAME}")
    h = h.replace('<link rel="stylesheet" href="/assets/blog/blog.css">',
                  '<link rel="stylesheet" href="/assets/blog/blog.css">\n<link rel="stylesheet" href="/assets/shop/shop.css">')
    body = "\n".join(product(p) for p in items)
    js = """<script>
(function(){
  function track(n,o){try{window.gtag&&gtag('event',n,o)}catch(e){}}
  document.querySelectorAll('[data-method]').forEach(function(a){a.addEventListener('click',function(){
    track('shop_click',{method:a.getAttribute('data-method'),item_id:a.getAttribute('data-item'),content_type:'shop'})})});
  var chips=document.querySelectorAll('.kinds button'),prods=document.querySelectorAll('.prod');
  chips.forEach(function(b){b.addEventListener('click',function(){var k=b.getAttribute('data-k');
    chips.forEach(function(c){var on=c===b;c.classList.toggle('on',on);c.setAttribute('aria-pressed',on)});
    prods.forEach(function(p){p.hidden=!!k&&p.getAttribute('data-kind')!==k})})});
})();
</script>
"""
    return f"""{h}</head>
{site_header("shop")}<main id="main">
<section class="shophead"><div class="wrap">
  <div class="copy">
    <p class="eyebrow" data-zh="Fly Kai Tak · 精品">Fly Kai Tak · Merch</p>
    <h1 data-zh="啟德商店">The Kai Tak shop</h1>
    <p class="lede" data-zh="棋盤、IGS 13 進場同 1998 年嘅啟德，印喺你可以著、用同貼嘅嘢上面。每張訂單都幫手令模擬器繼續免費。">The checkerboard, the IGS 13 approach and 1998 Kai Tak, on things you can wear, use and stick on. Every order helps keep the sim free to fly.</p>
  </div>
  <div class="han" lang="zh-Hant" aria-hidden="true"><span>啟</span><span>德</span></div>
</div></section>
<div class="checkband" aria-hidden="true"></div>
<section class="wrap shopbody">
  <div class="callout status"><p class="eyebrow" data-zh="點樣訂">How ordering works</p><p data-zh="{E(how[1])}">{E(how[0])}</p></div>
  <div class="kinds" role="group" aria-label="Filter by type">{chips}</div>
  <div class="prods">
{body}
  </div>
  <p class="small" data-zh="所有設計都係 Fly Kai Tak 原創，冇用任何真實航空公司嘅名或標誌。有問題？電郵 contact@flykaitak.com。">All designs are original to Fly Kai Tak and use no real airline names or logos. Questions? Email contact@flykaitak.com.</p>
  <aside class="cta"><span class="han" lang="zh-Hant" aria-hidden="true">啟德</span><strong data-zh="親自飛一次進場">Fly the approach yourself</strong><p data-zh="喺瀏覽器就玩得，免費。">It runs in your browser, free.</p><a class="btn go" href="/" data-zh="開始下降">Begin descent</a></aside>
</section>
</main>
{site_footer(js)}"""


def images(items):
    """Render the product JPGs and the shop social card with headless Chromium."""
    import io
    from PIL import Image
    from playwright.sync_api import sync_playwright
    from blog import FONTS
    base = f'<link rel="stylesheet" href="{FONTS}"><style>html,body{{margin:0;background:#0a1115}}</style>'
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 800, "height": 800})
        for p in items:
            pg.set_content(f'{base}<div style="width:800px;height:800px;background:radial-gradient(circle at 50% 40%,#1c2a30,#0a1115 75%)">'
                           f'{art(p["slug"]).replace("<svg ", "<svg width=800 height=800 ", 1)}</div>')
            pg.wait_for_timeout(600)
            pg.evaluate("document.fonts.ready")
            Image.open(io.BytesIO(pg.screenshot())).convert("RGB").save(SHOP / f"{p['slug']}.jpg", quality=86)
        pg.set_viewport_size({"width": 1200, "height": 630})
        pick = ["tee-checkerboard", "cap-runway13", "patch-1998", "pin-checkerboard"]
        tiles = "".join(f'<div style="width:270px;height:270px">{art(s).replace("<svg ", "<svg width=270 height=270 ", 1)}</div>' for s in pick)
        pg.set_content(f"""{base}<div style="position:relative;width:1200px;height:630px;background:#0a1115;font-family:B612,sans-serif;color:#f5efe3;overflow:hidden">
  <div style="height:16px;background:repeating-conic-gradient(#e8571f 0 25%,#f5efe3 0 50%) 0 0/16px 16px"></div>
  <div style="position:absolute;left:60px;top:60px;font-family:'B612 Mono',monospace;font-size:20px;letter-spacing:.22em;color:#ff6b5e">FLY KAI TAK · MERCH</div>
  <div style="position:absolute;left:58px;top:96px;font-size:68px;font-weight:700;line-height:1.05">The Kai Tak shop</div>
  <div style="position:absolute;right:60px;top:52px;font-family:'Noto Serif TC',serif;font-weight:900;font-size:96px;letter-spacing:.06em">啟德</div>
  <div style="position:absolute;left:30px;right:30px;bottom:40px;display:flex;justify-content:space-between;background:radial-gradient(ellipse at 50% 60%,#1c2a30,#0a1115 70%)">{tiles}</div>
  <div style="position:absolute;left:60px;top:186px;font-family:'B612 Mono',monospace;font-size:20px;letter-spacing:.1em;color:#93a6a2">TEES · CAPS · PATCHES · PINS · PRINTS</div>
</div>""")
        pg.wait_for_timeout(800)
        pg.evaluate("document.fonts.ready")
        Image.open(io.BytesIO(pg.screenshot())).convert("RGB").save(SHOP / "og.jpg", quality=88)
        b.close()


def main():
    items = load()
    if "--images" in sys.argv:
        images(items)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page(items), encoding="utf-8")
    n = sum(1 for p in items if p.get("checkout"))
    print(f"built shop/index.html: {len(items)} products, {n} with checkout links")


if __name__ == "__main__":
    main()
