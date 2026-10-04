#!/usr/bin/env python3
"""Build the Fly Kai Tak blog (static pages for GitHub Pages).

  blog/posts.json            post metadata (newest first); every post has a "category" slug
  blog/categories.json       the categories (slug, name, zh, desc), in display order
  blog/src/<slug>.html       post body (an HTML fragment)
  assets/blog/shots/*.jpg    screenshots (tools/screenshot.py)
  assets/blog/og/<slug>.jpg  social cards (tools/blog_images.py)

Each post needs a Cantonese body (blog/src/<slug>.zh.html) and a "zh" block in posts.json; the build fails without them.
Writes blog/index.html (+ blog/page/N/), blog/category/<slug>/ (+ page/N/), blog/sort/category/ (+ page/N/),
blog/<slug>/index.html, blog/search.json (read by assets/blog/search.js), blog/feed.xml and sitemap.xml. 20 posts per page.
See docs/blog.md.
Usage: python3 tools/blog.py
"""
import datetime as dt
import email.utils
import html
import json
import math
import pathlib
import re
import shutil
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
SITE = "https://flykaitak.com"
NAME = "Fly Kai Tak"
TZ = dt.timezone(dt.timedelta(hours=8))
E = html.escape
PER_PAGE = 20
CATS = {}  # slug -> {"slug","name","zh","desc"}, filled by load_categories()

FONTS = ("https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700"
         "&family=Noto+Serif+TC:wght@900&display=swap")

# Same Google Analytics 4 loader as index.html (only runs on flykaitak.com)
GA = """<script>
window.FKT_ANALYTICS={id:'G-7MNP3SBEF8',src:'/metrics/',fallback:'https://www.googletagmanager.com/gtag/js',hosts:['flykaitak.com','www.flykaitak.com']};
(function(c){window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};
  if(!/^G-[A-Z0-9]{6,}$/.test(c.id)||c.id==='G-XXXXXXXXXX'||c.hosts.indexOf(location.hostname)<0)return;
  function load(u,f){var s=document.createElement('script');s.async=true;s.src=u+(u.indexOf('?')<0?'?':'&')+'id='+c.id;if(f)s.onerror=f;document.head.appendChild(s)}
  load(c.src,function(){load(c.fallback)});
  gtag('js',new Date());gtag('config',c.id,{anonymize_ip:true});})(window.FKT_ANALYTICS);
</script>"""

ICON = {
    "link": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><path d="m22 6-10 7L2 6"/></svg>',
    "share": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/></svg>',
}

SHARE_JS = """<script>
(function(){
  document.querySelectorAll('[data-share]').forEach(function(box){
    var url=box.getAttribute('data-url'),title=box.getAttribute('data-title'),slug=box.getAttribute('data-slug');
    function track(m){try{window.gtag&&gtag('event','share',{method:m,content_type:'article',item_id:slug})}catch(e){}}
    box.querySelectorAll('a[data-method]').forEach(function(a){a.addEventListener('click',function(){track(a.getAttribute('data-method'))})});
    var copy=box.querySelector('[data-copy]');
    if(copy){copy.parentNode.hidden=false;copy.addEventListener('click',function(){
      function ok(){var zh=document.documentElement.getAttribute('data-lang')==='zh';var t=copy.querySelector('span');var o=t.textContent;t.textContent=zh?'已複製連結':'Link copied';copy.classList.add('done');track('copy_link');
        setTimeout(function(){t.textContent=o;copy.classList.remove('done')},2200)}
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(ok,function(){window.prompt(zh?'複製呢條連結':'Copy this link',url)})}
      else{window.prompt(zh?'複製呢條連結':'Copy this link',url)}})}
    var nat=box.querySelector('[data-native]');
    if(nat&&navigator.share){nat.parentNode.hidden=false;nat.addEventListener('click',function(){
      navigator.share({title:title,url:url}).then(function(){track('native')}).catch(function(){})})}
  });
})();
</script>"""


def load_categories():
    CATS.clear()
    for c in json.load(open(BLOG / "categories.json", encoding="utf-8")):
        for k in ("slug", "name", "zh", "desc"):
            assert c.get(k), f"categories.json: {c.get('slug')} missing {k}"
        CATS[c["slug"]] = c


def load_posts():
    load_categories()
    posts = json.load(open(BLOG / "posts.json", encoding="utf-8"))
    for p in posts:
        assert p.get("category") in CATS, f"{p['slug']}: category must be one of {', '.join(CATS)} (blog/categories.json)"
        p["body"] = (BLOG / "src" / f"{p['slug']}.html").read_text(encoding="utf-8").strip()
        p["body_zh"] = (BLOG / "src" / f"{p['slug']}.zh.html").read_text(encoding="utf-8").strip()
        zh = p.get("zh") or {}
        for k in ("title", "dek", "description", "hero_alt", "hero_caption"):
            assert zh.get(k), f"{p['slug']}: missing zh.{k} in posts.json"
        p["url"] = f"{SITE}/blog/{p['slug']}/"
        p["words"] = len(re.sub(r"<[^>]+>", " ", p["body"]).split())
        p["mins"] = max(1, math.ceil(p["words"] / 200))
        p["og"] = f"{SITE}/assets/blog/og/{p['slug']}.jpg"
        for f in (ROOT / "assets/blog/og" / f"{p['slug']}.jpg", ROOT / "assets/blog/shots" / f"{p['hero']}.jpg"):
            assert f.exists(), f"missing image {f}"
    posts.sort(key=lambda p: p["date"], reverse=True)  # stable: JSON order breaks ties
    return posts


def human(date):
    d = dt.date.fromisoformat(date)
    return f"{d.day} {d.strftime('%B %Y')}"


def head(title, desc, canonical, og_image, og_alt, og_type="website", extra="", keywords=None, jsonld=None, zh_title=None,
         robots="index,follow,max-image-preview:large"):
    kw = f'<meta name="keywords" content="{E(", ".join(keywords))}">\n' if keywords else ""
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False, separators=(",", ":"))}</script>\n'
                 for j in (jsonld or []))
    zt = f'<meta name="fkt-zh-title" content="{E(zh_title)}">\n' if zh_title else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#0a1115">
<meta name="color-scheme" content="dark">
<meta name="author" content="{NAME}">
{kw}<meta name="robots" content="{robots}">
<link rel="icon" href="/assets/brand/mark.svg" type="image/svg+xml">
<link rel="icon" href="/assets/brand/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{NAME} blog" href="/blog/feed.xml">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{E(og_alt)}">
<meta property="og:locale" content="en_GB">
{extra}<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(desc)}">
<meta name="twitter:image" content="{og_image}">
<meta name="twitter:image:alt" content="{E(og_alt)}">
{ld}{GA}
{zt}<script>try{{if(localStorage.getItem('fkt-lang')==='zh')document.documentElement.setAttribute('data-lang','zh')}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/assets/blog/blog.css">
</head>
"""


LANG_BTN = ('<button class="langtog" id="btnLang" type="button" aria-pressed="false" aria-label="Language: English / 廣東話" '
            'title="English / 廣東話"><span data-l="en" class="on">EN</span><span data-l="zh" lang="zh-HK">粵</span></button>')


def site_header(current):
    def a(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'
    return f"""<body>
<a class="skip" href="#main">Skip to content</a>
<div class="checkband" aria-hidden="true"></div>
<header class="site"><div class="wrap">
  <a class="brandlink" href="/" aria-label="{NAME}, play the simulator"><img src="/assets/brand/mark.svg" width="32" height="32" alt=""><span>{NAME}</span><span class="han" lang="zh-Hant" aria-hidden="true">啟德機場</span></a>
  <nav aria-label="Main">{a("/blog/", "Blog", "blog")}<a href="/">Play</a>{LANG_BTN}</nav>
</div></header>
"""


def site_footer(scripts=""):
    return f"""<footer class="foot"><div class="wrap">
  <div class="row">
    <span>&copy; {NAME}. <a href="https://malgordon.com" target="_blank" rel="noopener">Another Mal Gordon project</a></span>
    <span><a href="mailto:contact@flykaitak.com">contact@flykaitak.com</a> &middot; <a href="/blog/feed.xml">RSS</a> &middot; <a href="https://www.facebook.com/flykaitak" target="_blank" rel="noopener">Facebook</a> &middot; <a href="https://www.instagram.com/flykaitak" target="_blank" rel="noopener">Instagram</a> &middot; <a href="https://github.com/Ragnahhhhrock/flykaitak" target="_blank" rel="noopener">GitHub</a></span>
  </div>
  <div>Map data &copy; Lands Department, HKSAR Government. Elevation: SRTM via AWS Terrain Tiles. Aircraft and liveries are not real airlines.</div>
</div></footer>
<script src="/assets/blog/lang.js"></script>
{scripts}</body>
</html>
"""


def card(p):
    return f"""<a class="pcard" href="/blog/{p['slug']}/">
  <img src="/assets/blog/og/{p['slug']}.jpg" width="1200" height="630" loading="lazy" alt="{E(p['hero_alt'])}" data-zh-alt="{E(p['zh']['hero_alt'])}">
  <div class="body">
    <span class="catpill" data-zh="{E(CATS[p['category']]['zh'])}">{E(CATS[p['category']]['name'])}</span>
    <div class="meta">{E(p['tag'])} &middot; {human(p['date'])}</div>
    <h3 data-zh="{E(p['zh']['title'])}">{E(p['title'])}</h3>
    <p data-zh="{E(p['zh']['description'])}">{E(p['description'])}</p>
    <span class="more">Read the post &rarr;</span>
  </div>
</a>"""


def share_box(p, where):
    u, t = urllib.parse.quote(p["url"], safe=""), urllib.parse.quote(p["title"] + " | Fly Kai Tak", safe="")
    links = [
        ("x", "Post on X", f"https://twitter.com/intent/tweet?text={t}&url={u}"),
        ("facebook", "Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}"),
        ("reddit", "Reddit", f"https://www.reddit.com/submit?url={u}&title={urllib.parse.quote(p['title'], safe='')}"),
        ("linkedin", "LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={u}"),
        ("whatsapp", "WhatsApp", f"https://wa.me/?text={t}%20{u}"),
        ("threads", "Threads", f"https://www.threads.net/intent/post?text={t}%20{u}"),
    ]
    items = "".join(f'<li><a data-method="{m}" href="{h}" target="_blank" rel="noopener noreferrer">{l}</a></li>' for m, l, h in links)
    mail = f"mailto:?subject={urllib.parse.quote(p['title'], safe='')}&body={u}"
    items += f'<li><a data-method="email" href="{mail}">{ICON["mail"]}Email</a></li>'
    items += f'<li hidden><button type="button" data-copy>{ICON["link"]}<span>Copy link</span></button></li>'
    items += f'<li hidden><button type="button" data-native>{ICON["share"]}<span>Share&hellip;</span></button></li>'
    cls = "share share--top" if where == "top" else "share"
    return (f'<section class="{cls}" aria-label="Share this post" data-share data-url="{p["url"]}" '
            f'data-title="{E(p["title"])}" data-slug="{p["slug"]}"><h2>Share this post</h2><ul>{items}</ul></section>')


def post_page(p, others):
    desc = p["description"]
    iso = p["date"]
    mod = p.get("updated", iso)
    ld = [
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": desc,
         "image": [p["og"], f"{SITE}/assets/blog/shots/{p['hero']}.jpg"], "datePublished": iso, "dateModified": mod,
         "author": {"@type": "Organization", "name": NAME, "url": SITE + "/"},
         "publisher": {"@type": "Organization", "name": NAME, "url": SITE + "/",
                       "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/brand/icon-512.png"}},
         "mainEntityOfPage": {"@type": "WebPage", "@id": p["url"]}, "keywords": ", ".join(p["keywords"]),
         "articleSection": CATS[p["category"]]["name"], "inLanguage": "en-GB", "wordCount": p["words"],
         "isPartOf": {"@type": "Blog", "name": f"{NAME} blog", "url": f"{SITE}/blog/"}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": NAME, "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{SITE}/blog/"},
            {"@type": "ListItem", "position": 3, "name": CATS[p["category"]]["name"], "item": f"{SITE}/blog/category/{p['category']}/"},
            {"@type": "ListItem", "position": 4, "name": p["title"], "item": p["url"]}]},
    ]
    extra = (f'<meta property="article:published_time" content="{iso}">\n<meta property="article:modified_time" content="{mod}">\n'
             f'<meta property="article:section" content="{E(CATS[p["category"]]["name"])}">\n<meta property="article:author" content="{NAME}">\n'
             + "".join(f'<meta property="article:tag" content="{E(k)}">\n' for k in p["keywords"]))
    out = head(f"{p['title']} | {NAME}", desc, p["url"], p["og"], p["hero_alt"], "article", extra, p["keywords"], ld,
               zh_title=f"{p['zh']['title']} | {NAME}")
    out += site_header("blog")
    out += f"""<main id="main"><article>
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">{NAME}</a> / <a href="/blog/">Blog</a> / <a href="/blog/category/{p['category']}/" data-zh="{E(CATS[p['category']]['zh'])}">{E(CATS[p['category']]['name'])}</a> / <span aria-current="page">{E(p['tag'])}</span></nav>
  <header class="post-head">
    <p class="eyebrow"><span>{E(p['tag'])}</span> &middot; <a href="/blog/category/{p['category']}/" data-zh="{E(CATS[p['category']]['zh'])}">{E(CATS[p['category']]['name'])}</a></p>
    <h1 data-zh="{E(p['zh']['title'])}">{E(p['title'])}</h1>
    <p class="dek" data-zh="{E(p['zh']['dek'])}">{E(p['dek'])}</p>
    <div class="byline"><time datetime="{iso}">{human(iso)}</time><span>{p['mins']} min read</span><span>{NAME}</span></div>
  </header>
  {share_box(p, 'top')}
  <figure class="hero">
    <img src="/assets/blog/shots/{p['hero']}.jpg" width="1600" height="900" fetchpriority="high" alt="{E(p['hero_alt'])}" data-zh-alt="{E(p['zh']['hero_alt'])}">
    <figcaption data-zh="{E(p['zh']['hero_caption'])}">{E(p['hero_caption'])}</figcaption>
  </figure>
  <div class="prose" data-lang="en">
{p['body']}
  </div>
  <div class="prose" data-lang="zh" lang="zh-HK">
{p['body_zh']}
  </div>
  {share_box(p, 'bottom')}
  <aside class="cta" aria-label="Play Fly Kai Tak">
    <span class="han" lang="zh-Hant" aria-hidden="true">啟德</span>
    <strong>Fly the approach yourself</strong>
    <p>It runs in your browser. Pick an aircraft, a time of day and the weather, then hit the checkerboard.</p>
    <a class="btn go" href="/">Begin descent</a>
  </aside>
"""
    if others:
        out += f'  <section class="more-posts"><h2 class="label" style="font-family:var(--f-num);font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);font-weight:400;margin:0 0 20px">More from the blog</h2><div class="cards">\n'
        out += "\n".join(card(o) for o in others) + "\n  </div></section>\n"
    out += "</div>\n</article></main>\n" + site_footer().replace("</body>", SHARE_JS + "\n</body>")
    return out


def page_url(base, n):
    return base if n == 1 else f"{base}page/{n}/"


def chunks(items):
    return [items[i:i + PER_PAGE] for i in range(0, len(items), PER_PAGE)] or [[]]


def pager(base, n, pages):
    if pages < 2:
        return ""
    out = [f'<span class="pginfo">Page {n} of {pages}</span>']
    if n > 1:
        out.append(f'<a class="pg" rel="prev" href="{page_url(base, n - 1)}">&larr; Previous</a>')
    for i in range(1, pages + 1):
        cur = ' aria-current="page"' if i == n else ""
        out.append(f'<a class="pg num" href="{page_url(base, i)}"{cur} aria-label="Page {i}">{i}</a>')
    if n < pages:
        out.append(f'<a class="pg" rel="next" href="{page_url(base, n + 1)}">Next &rarr;</a>')
    return f'<nav class="pager" aria-label="Pagination">{"".join(out)}</nav>'


def cards_html(items, grouped, counts):
    if not grouped:
        return '<div class="cards">\n' + "\n".join(card(p) for p in items) + "\n</div>"
    segs = []
    for p in items:
        if segs and segs[-1][0] == p["category"]:
            segs[-1][1].append(p)
        else:
            segs.append((p["category"], [p]))
    out = ""
    for slug, ps in segs:
        c = CATS[slug]
        out += (f'<h2 class="grouphead"><a href="/blog/category/{slug}/" data-zh="{E(c["zh"])}">{E(c["name"])}</a>'
                f'<span class="n">{counts[slug]}</span></h2>\n<div class="cards">\n'
                + "\n".join(card(p) for p in ps) + "\n</div>\n")
    return out


CUR = ' aria-current="page"'


def tools_block(posts, counts, cur_cat, show_sort, sort_mode):
    chips = [f'<a href="/blog/"{CUR if cur_cat is None else ""}><span class="nm">All</span><span class="n">{len(posts)}</span></a>']
    for slug, c in CATS.items():
        if counts[slug]:
            chips.append(f'<a href="/blog/category/{slug}/"{CUR if slug == cur_cat else ""}><span class="nm" data-zh="{E(c["zh"])}">{E(c["name"])}</span>'
                         f'<span class="n">{counts[slug]}</span></a>')
    sort = ""
    if show_sort:
        sort = ('<nav class="sortbar" aria-label="Sort posts"><h2 class="k">Sort</h2><div class="seg">'
                f'<a href="/blog/"{"" if sort_mode else CUR}>Newest</a>'
                f'<a href="/blog/sort/category/"{CUR if sort_mode else ""}>By category</a></div></nav>')
    return f"""<div class="tools">
  <form class="blogsearch" id="blogsearch" role="search" action="/blog/" method="get">
    <label class="sr" for="blogq">Search posts</label>
    <input id="blogq" name="q" type="search" autocomplete="off" enterkeyhint="search">
    <button class="btn" type="submit">Search</button>
  </form>
  <nav class="chips" aria-label="Categories"><h2 class="k">Category</h2><div class="chipgrid">{"".join(chips)}</div></nav>
  {sort}
</div>"""


def listing_page(posts, items, n, pages, base, kind, cat=None):
    """kind: 'latest' (/blog/), 'category' (/blog/category/<slug>/) or 'sort' (/blog/sort/category/)."""
    counts = {s: sum(1 for p in posts if p["category"] == s) for s in CATS}
    url = SITE + page_url(base, n)
    suffix = f", page {n}" if n > 1 else ""
    zsuffix = f"，第 {n} 頁" if n > 1 else ""
    robots, canonical, ld = "index,follow,max-image-preview:large", url, None
    if kind == "category":
        title, zt = f"{cat['name']}{suffix} | Blog | {NAME}", f"{cat['zh']}{zsuffix} | 網誌 | {NAME}"
        desc = f"{cat['name']} posts from the {NAME} blog. {cat['desc']}"
        eyebrow, h1, zh_h1, lede = "Category", cat["name"], cat["zh"], cat["desc"]
        label = f"{counts[cat['slug']]} posts" if counts[cat["slug"]] != 1 else "1 post"
    else:
        title, zt = f"Blog{suffix} | {NAME}", f"網誌{zsuffix} | {NAME}"
        desc = ("News, new features and behind-the-scenes notes from Fly Kai Tak, the browser flight simulator "
                "of the 1998 Runway 13 approach into Hong Kong Kai Tak.")
        eyebrow, h1, zh_h1 = "VHHH &middot; IGS 13 &middot; 1998", "The Fly Kai Tak blog", None
        lede = "New features, bug fixes and notes from the Kai Tak approach."
        label = "Posts by category" if kind == "sort" else "Latest posts"
        if kind == "sort":
            robots, canonical = "noindex,follow", f"{SITE}/blog/"
            title, zt = f"Blog by category{suffix} | {NAME}", f"網誌（按分類）{zsuffix} | {NAME}"
        elif n == 1:
            ld = [{"@context": "https://schema.org", "@type": "Blog", "name": f"{NAME} blog", "url": f"{SITE}/blog/",
                   "description": desc, "inLanguage": "en-GB",
                   "publisher": {"@type": "Organization", "name": NAME, "url": SITE + "/"},
                   "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": p["url"], "datePublished": p["date"],
                                 "image": p["og"]} for p in posts]}]
    extra = ""
    if n > 1:
        extra += f'<link rel="prev" href="{SITE}{page_url(base, n - 1)}">\n'
    if n < pages:
        extra += f'<link rel="next" href="{SITE}{page_url(base, n + 1)}">\n'
    first = items[0] if items else posts[0]
    out = head(title, desc, canonical, first["og"], "Fly Kai Tak blog: news and features from the Kai Tak flight simulator.",
               "website", extra, ["Kai Tak", "flight simulator", "Hong Kong 1998", "IGS 13", "blog"], ld, zh_title=zt, robots=robots)
    out += site_header("blog")
    h1_attr = f' data-zh="{E(zh_h1)}"' if zh_h1 else ""
    out += f"""<main id="main">
<section class="masthead" aria-labelledby="blog-title">
  <img class="art" src="/assets/blog/header.jpg" width="1600" height="400" fetchpriority="high" alt="">
  <div class="copy"><div class="wrap">
    <p class="eyebrow">{eyebrow}</p>
    <h1 id="blog-title"{h1_attr}>{E(h1)}</h1>
    <p class="lede">{E(lede)}</p>
  </div></div>
</section>
<div class="section"><div class="wrap">
  {tools_block(posts, counts, cat["slug"] if cat else None, kind != "category", kind == "sort")}
  <div id="results" hidden>
    <p class="count" id="resultcount" role="status" aria-live="polite"></p>
    <div class="cards" id="resultcards"></div>
    <nav class="pager" id="resultpager" aria-label="Search results pages" hidden></nav>
  </div>
  <div id="postlist">
  <h2 class="label">{label}</h2>
{cards_html(items, kind == "sort", counts)}
  {pager(base, n, pages)}
  </div>
</div></div>
</main>
"""
    out += site_footer('<script src="/assets/blog/search.js"></script>\n')
    return out


def write_listing(posts, items, base, kind, cat=None):
    parts = chunks(items)
    root = ROOT / base.strip("/")
    for i, part in enumerate(parts, 1):
        d = root if i == 1 else root / "page" / str(i)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(listing_page(posts, part, i, len(parts), base, kind, cat), encoding="utf-8")
    return len(parts)


def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def search_index(posts):
    out = []
    for p in posts:
        c, d = CATS[p["category"]], dt.date.fromisoformat(p["date"])
        out.append({"s": p["slug"], "t": p["title"], "tz": p["zh"]["title"], "d": p["description"], "dz": p["zh"]["description"],
                    "tag": p["tag"], "c": p["category"], "cn": c["name"], "cz": c["zh"], "date": p["date"],
                    "dh": human(p["date"]), "dhz": f"{d.year} 年 {d.month} 月 {d.day} 日", "k": " ".join(p["keywords"]),
                    "x": plain(p["body"]), "xz": plain(p["body_zh"]), "img": f"/assets/blog/og/{p['slug']}.jpg",
                    "a": p["hero_alt"], "az": p["zh"]["hero_alt"]})
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))


def feed(posts):
    now = email.utils.format_datetime(dt.datetime.fromisoformat(posts[0]["date"]).replace(tzinfo=TZ))
    items = ""
    for p in posts:
        pub = email.utils.format_datetime(dt.datetime.fromisoformat(p["date"]).replace(tzinfo=TZ))
        items += (f"<item><title>{E(p['title'])}</title><link>{p['url']}</link><guid isPermaLink=\"true\">{p['url']}</guid>"
                  f"<pubDate>{pub}</pubDate><category>{E(p['tag'])}</category><category>{E(CATS[p['category']]['name'])}</category>"
                  f"<description>{E(p['description'])}</description>"
                  f"<enclosure url=\"{p['og']}\" type=\"image/jpeg\" length=\"{(ROOT / 'assets/blog/og' / (p['slug'] + '.jpg')).stat().st_size}\"/></item>\n")
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{NAME} blog</title>'
            f'<link>{SITE}/blog/</link><description>News and features from Fly Kai Tak, a browser flight simulator '
            f'of the 1998 Runway 13 approach into Hong Kong Kai Tak.</description><language>en-gb</language>'
            f'<lastBuildDate>{now}</lastBuildDate>\n{items}</channel></rss>\n')


def sitemap(posts, extra):
    newest = max(p.get("updated", p["date"]) for p in posts)
    urls = [(f"{SITE}/", None, "weekly"), (f"{SITE}/blog/", newest, "weekly")]
    urls += [(u, m, "weekly") for u, m in extra]
    urls += [(p["url"], p.get("updated", p["date"]), "monthly") for p in posts]
    body = "".join(f"<url><loc>{u}</loc>" + (f"<lastmod>{m}</lastmod>" if m else "") + f"<changefreq>{c}</changefreq></url>\n"
                   for u, m, c in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n'


def main():
    posts = load_posts()
    slugs = [p["slug"] for p in posts]
    assert len(set(slugs)) == len(slugs), "duplicate slugs"
    for sub in ("page", "category", "sort"):  # listing pages are regenerated from scratch
        shutil.rmtree(BLOG / sub, ignore_errors=True)
    newest = max(p.get("updated", p["date"]) for p in posts)
    extra = []
    pages = write_listing(posts, posts, "/blog/", "latest")
    extra += [(f"{SITE}/blog/page/{i}/", newest) for i in range(2, pages + 1)]
    order = {s: i for i, s in enumerate(CATS)}
    by_cat = sorted(posts, key=lambda p: order[p["category"]])  # stable: newest first inside each category
    write_listing(posts, by_cat, "/blog/sort/category/", "sort")
    for slug, c in CATS.items():
        items = [p for p in posts if p["category"] == slug]
        if not items:
            continue
        base = f"/blog/category/{slug}/"
        n = write_listing(posts, items, base, "category", c)
        last = max(p.get("updated", p["date"]) for p in items)
        extra += [(SITE + page_url(base, i), last) for i in range(1, n + 1)]
    (BLOG / "search.json").write_text(search_index(posts), encoding="utf-8")
    for p in posts:
        d = BLOG / p["slug"]
        d.mkdir(exist_ok=True)
        rel = sorted((o for o in posts if o is not p), key=lambda o: o["category"] != p["category"])  # same category first
        (d / "index.html").write_text(post_page(p, rel[:2]), encoding="utf-8")
    (BLOG / "feed.xml").write_text(feed(posts), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(posts, extra), encoding="utf-8")
    print(f"built {len(posts)} posts in {len(CATS)} categories, {pages} blog page(s): " + ", ".join(slugs))


if __name__ == "__main__":
    main()
