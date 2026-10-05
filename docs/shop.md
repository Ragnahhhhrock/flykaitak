# Shop

Static merch page at https://flykaitak.com/shop/, built by `tools/shop.py` from `assets/shop/products.json`.

- Each product: `slug`, `name`, `zh`, `price` (AUD), `kind`/`kind_zh` (filter chip), `desc`/`desc_zh`, `specs`/`specs_zh`, `checkout`.
- Artwork is `assets/shop/<slug>.svg` (original designs; no real airline names or logos), inlined into the page.
- `checkout` is a Stripe Payment Link (`https://buy.stripe.com/...`). Empty = "Coming soon" + a **Notify me** mailto to contact@flykaitak.com (no payment taken). Paste a link and rebuild to switch that product to **Buy**. Collect size and shipping address in the Stripe Payment Link settings.
- Build: `python3 tools/shop.py` (add `--images` after changing artwork to re-render `assets/shop/<slug>.jpg` and the `og.jpg` social card).
- Home screen links: the **Shop** button in the top bar and the **Kai Tak merch** card under the coffee button. The blog header links to it too, and `tools/blog.py` adds `/shop/` to the sitemap.
- Analytics: `shop_click` (see docs/analytics-events.md).
