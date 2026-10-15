# Concorde (premium aircraft)

The An-225 is sold the same way: see `docs/an225.md`. The store, codes and admin API below take a `product` (`concorde` or `an225`).

A flyable delta-wing supersonic jet, US$7, one-off. Code is in `index.html` (`AC.conc`, `concPodGeo`, `noseFrame`, the `#concModal` window, the `ENT` licence code) and `server/worker.js` (`/store/*`, `/admin/*`). Generic navy/red livery: no real airline names or logos.

## Flying it
Droop nose follows the gear (down with gear down, up when retracted). No flaps; vortex-lift delta model (`am` in `AC.conc`), approach alpha about 13.5°, reheat on take-off, flight engineer panel in the cockpit. The autopilot lands it on both runways in all weather presets (`python3 tools/test_landings.py` includes `conc`).

## Setup (once)
1. Re-run `server/schema.sql` on the D1 database (adds `licences`, `codes`, `lic_fail`): `npx wrangler d1 execute flykaitak-scores --remote --file=schema.sql`
2. Secrets: `npx wrangler secret put STRIPE_SECRET_KEY` (a secret or restricted key that can create and read Checkout Sessions) and `npx wrangler secret put ADMIN_TOKEN` (long random string).
3. `npx wrangler deploy`. Sales stay off (the window says so) until `STRIPE_SECRET_KEY` is set.
4. Optional var `SITE_BASE` (default `https://flykaitak.com`): where Stripe sends the buyer back.

## Purchase flow
Picking Concorde without a licence opens the window. **Buy** calls `POST /store/checkout`, which makes a Stripe Checkout Session (US$7, `metadata.product=concorde`) and redirects. Stripe returns to `/?concorde_session=cs_...`; the page calls `POST /store/claim`, the Worker reads the session from Stripe, checks it is paid, for this product, in USD and at least US$7, then mints a key `CONC-XXXX-XXXX-XXXX` (once per session; no webhook needed). The key is stored in `localStorage` (`fkt-lic`) and shown so the buyer can keep it. Typing the key into the code box on another device restores it.

## Free codes (giveaways)
Make codes with the admin API (`Authorization: Bearer $ADMIN_TOKEN`):

    curl -X POST https://<worker>/admin/codes -H "authorization: Bearer $ADMIN_TOKEN" \
      -d '{"count":5,"uses":1,"days":30,"note":"streamer giveaway"}'

`count` (1-500 codes), `uses` per code (default 1; `"unlimited"` or `0` for no cap), `days` until expiry (leave out or `0` for never), `note`. Each use mints its own licence key.

Make an existing code reusable with no expiry:

    curl -X POST https://<worker>/admin/codes/update -H "authorization: Bearer $ADMIN_TOKEN" \
      -d '{"code":"FKT-XXXX-XXXX","uses":"unlimited","days":0}'

`uses` and `days` are each optional; only the ones sent are changed. Codes look like `FKT-XXXX-XXXX`; the player pastes one in the Concorde window and gets a licence key.
- `GET /admin/codes` lists codes and use counts; `GET /admin/sales` counts licences by source.
- `POST /admin/codes/disable {"code":"FKT-...","enable":false}` stops a code (`enable:true` turns it back on).
- `POST /admin/licences/revoke {"key":"CONC-...","restore":false}` revokes a licence (a revoked purchase cannot be re-claimed).
- Wrong codes, keys or sessions are limited to 15 an hour per address (kept only as a salted hash).

## Limits
The site is static, so the licence check is client side (the key is re-checked with `/store/check` in the background). A determined player can edit the page to bypass it. That is accepted for a US$7 item. Tests set `window.__capture` to skip the gate.

## Analytics
`concorde_offer_view`, `concorde_checkout`, `concorde_unlock` (see `docs/analytics-events.md`).
