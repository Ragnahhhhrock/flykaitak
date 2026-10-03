# Blog

Static pages at https://flykaitak.com/blog/, built by `tools/blog.py` from `blog/posts.json` and `blog/src/<slug>.html`. Styling is `assets/blog/blog.css` (the sim's design system).

## Rule
Every new feature or bug fix gets a blog post, written in the same change and pushed to `main` with the code.

## Screenshot rule
When flying routes to create screenshots, toggle the cockpit off. `tools/screenshot.py` sets `deck: false` by default; only a shot that is meant to show the cockpit sets `"deck": true`.

## Add a post
1. Take screenshots: write a `shots.json` (see the docstring in `tools/screenshot.py`) and run `python3 tools/screenshot.py shots.json`. JPGs land in `assets/blog/shots/`.
2. Write the body as an HTML fragment in `blog/src/<slug>.html` (h2, p, ul, `<figure class="wide">`, `.readouts`, `.callout`; copy an existing post).
3. Write the Cantonese body in `blog/src/<slug>.zh.html` (same structure and images as the English fragment, written Cantonese, translated `alt` and `figcaption` text; keep product names, key letters and code as they are). Then add an entry at the top of `blog/posts.json`: `slug` (the URL stub), `title`, `dek`, `description` (the meta description, under about 160 characters), `date`, `tag` (Feature, Fix, Update, New, History, Behind the scenes), `category` (a slug from `blog/categories.json`: aircraft, flying, scenery, controls, scores or site), `keywords`, `hero` (a shot name), `hero_alt`, `hero_caption`, the card fields `card_kicker`, `card_title`, `card_sub`, `card_image`, `card_focus`, and a `zh` object with `title`, `dek`, `description`, `hero_alt`, `hero_caption` in Cantonese. `tools/blog.py` fails if the Cantonese body or `zh` fields are missing.
4. Run `python3 tools/blog_images.py <slug>` to render the 1200x630 social card, then `python3 tools/blog.py` to build the pages, feed and sitemap.
5. Commit and push everything, including the generated `blog/` pages.

Every blog page has an EN / 粵 button in the header (`assets/blog/lang.js`). It shares its saved choice with the home screen (`fkt-lang` in localStorage). The English and Cantonese bodies are both in the page and the button swaps them.
The generator adds the title, description, canonical, Open Graph and Twitter tags, BlogPosting and breadcrumb JSON-LD, share buttons (X, Facebook, Reddit, LinkedIn, WhatsApp, Threads, email, copy link, native share), the RSS feed entry and the sitemap entry.
Only state facts that are in the README or the code. Do not use real airline names or logos.

## Categories, sort, pages and search
- Categories live in `blog/categories.json` (slug, name, zh, desc; the order is the display order). Every post needs a `category`; `tools/blog.py` fails without a valid one. Add a new category there first, with its Cantonese name.
- `tools/blog.py` builds `/blog/` (20 posts per page, `/blog/page/N/`), `/blog/category/<slug>/` (+ pages), `/blog/sort/category/` (sorted by category, `noindex`) and `blog/search.json`. Listing pages are regenerated from scratch each build.
- `assets/blog/search.js` searches `blog/search.json` in the browser (title, description, keywords, category, body text, English and Cantonese), 20 results per page, and supports `/blog/?q=term`. It sends a GA4 `search` event.
- Category pages and extra pages are in `sitemap.xml`; each post's breadcrumb and JSON-LD include its category, and "More from the blog" lists same-category posts first.
