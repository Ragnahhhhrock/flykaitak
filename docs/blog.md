# Blog

Static pages at https://flykaitak.com/blog/, built by `tools/blog.py` from `blog/posts.json` and `blog/src/<slug>.html`. Styling is `assets/blog/blog.css` (the sim's design system).

## Rule
Every new feature or bug fix gets a blog post, written in the same change and pushed to `main` with the code.

## Add a post
1. Take screenshots: write a `shots.json` (see the docstring in `tools/screenshot.py`) and run `python3 tools/screenshot.py shots.json`. JPGs land in `assets/blog/shots/`.
2. Write the body as an HTML fragment in `blog/src/<slug>.html` (h2, p, ul, `<figure class="wide">`, `.readouts`, `.callout`; copy an existing post).
3. Add an entry at the top of `blog/posts.json`: `slug` (the URL stub), `title`, `dek`, `description` (the meta description, under about 160 characters), `date`, `tag`, `keywords`, `hero` (a shot name), `hero_alt`, `hero_caption`, and the card fields `card_kicker`, `card_title`, `card_sub`, `card_image`, `card_focus`.
4. Run `python3 tools/blog_images.py <slug>` to render the 1200x630 social card, then `python3 tools/blog.py` to build the pages, feed and sitemap.
5. Commit and push everything, including the generated `blog/` pages.

The generator adds the title, description, canonical, Open Graph and Twitter tags, BlogPosting and breadcrumb JSON-LD, share buttons (X, Facebook, Reddit, LinkedIn, WhatsApp, email, copy link, native share), the RSS feed entry and the sitemap entry.
Only state facts that are in the README or the code. Do not use real airline names or logos.
