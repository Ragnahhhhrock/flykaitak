// Fly Kai Tak API: a Cloudflare Worker with a D1 database.
//   GET  /scores  -> top 100 [{id,n,s,g,ac,wx,tod,d}]
//   POST /scores  -> add or rename {id,n,s,g,ac,wx,tod,d}
//   POST /events  -> one anonymous gameplay event {k,mode,ac,wx,tod,cause,grade,score,fpm,secs,ap}
//   GET  /stats   -> public aggregate counts for flykaitak.com/stats/
//   GET  /replays -> {ok:true,max} when replay share links are switched on (an R2 bucket is bound as REPLAYS)
//   POST /replays -> multipart {video: mp4, poster: jpg, card: png, meta: json} -> {id, url}
//   POST /store/checkout {product} -> {ok,url}  Stripe Checkout page for a paid aircraft (Concorde, $7 USD)
//   POST /store/claim {session}    -> {ok,key}  after paying: Stripe returns the buyer to the sim with ?concorde_session=cs_...; the Worker checks it with Stripe and issues a licence key
//   POST /store/redeem {code}      -> {ok,key}  a free giveaway code (FKT-XXXX-XXXX), or a licence key typed in on a new device
//   POST /store/check {key,product}-> {ok}      is this licence key valid (not revoked)
//   /admin/*  (Authorization: Bearer ADMIN_TOKEN)  make and list giveaway codes, revoke a licence, sales counts. See docs/concorde.md
//   GET  /r/<id>  -> the share page for one replay (video, report card, Open Graph tags so a posted link shows the video)
//   GET  /v/<id>.mp4, /p/<id>.jpg, /c/<id>.png -> the video (with HTTP ranges), its poster frame, the report card image
const ORIGINS = ['https://flykaitak.com', 'https://www.flykaitak.com'];
const clean = (n) => String(n || '').replace(/[^A-Za-z0-9 _.\-]/g, '').trim().slice(0, 12).toUpperCase() || 'PILOT';
const EVENTS = new Set(['game_start', 'landing_attempt', 'landing', 'crash', 'missed_approach', 'aircraft_select', 'lesson_start', 'lesson_complete']);
const tok = (v, n = 24) => String(v == null ? '' : v).replace(/[^A-Za-z0-9 _.,:'\/\-]/g, '').trim().slice(0, n) || null;
const num = (v, lo, hi) => { v = Math.round(Number(v)); return Number.isFinite(v) && v >= lo && v <= hi ? v : null; };

// Scoring v2 started on 12 Oct 2026. Older scores stay in the database but are not served. Keep in step with HS_SINCE in index.html.
const SINCE = 1791784800000;

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ORIGINS.includes(origin) ? origin : ORIGINS[0],
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'content-type,authorization',
      Vary: 'Origin',
    };
    const json = (body, status = 200, extra = {}) =>
      new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', ...cors, ...extra } });
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    if (url.pathname === '/stats' && req.method === 'GET') return stats(env, json);
    if (url.pathname.startsWith('/store/') || url.pathname.startsWith('/admin/')) return store(req, env, url, json);
    if (url.pathname === '/replays') {
      if (req.method === 'GET') return json(env.REPLAYS ? { ok: true, max: MAX_VIDEO } : { ok: false });
      if (req.method === 'POST') return replayUpload(req, env, json);
    }
    if (req.method === 'GET' || req.method === 'HEAD') {
      let m;
      if ((m = url.pathname.match(/^\/r\/([a-z0-9]{10})\/?$/))) return replayPage(m[1], env, url);
      if ((m = url.pathname.match(/^\/v\/([a-z0-9]{10})\.mp4$/))) return replayFile(req, env, `replays/${m[1]}.mp4`, 'video/mp4');
      if ((m = url.pathname.match(/^\/p\/([a-z0-9]{10})\.jpg$/))) return replayFile(req, env, `replays/${m[1]}.jpg`, 'image/jpeg');
      if ((m = url.pathname.match(/^\/c\/([a-z0-9]{10})\.png$/))) return replayFile(req, env, `replays/${m[1]}.png`, 'image/png');
    }
    if (url.pathname === '/events' && req.method === 'POST') {
      let b;
      try { b = await req.json(); } catch { return json({ error: 'bad json' }, 400); }
      if (!EVENTS.has(b.k)) return json({ error: 'invalid' }, 400);
      await env.DB.prepare(
        'INSERT INTO events (ts, k, mode, ac, wx, tod, cause, grade, score, fpm, secs, ap) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12)'
      ).bind(Date.now(), b.k, tok(b.mode, 16), tok(b.ac, 12), tok(b.wx, 12), b.tod === 'night' ? 'night' : 'day',
             tok(b.cause, 48), tok(b.grade, 1), num(b.score, 0, 100), num(b.fpm, 0, 5000), num(b.secs, 0, 86400), b.ap ? 1 : 0).run();
      return json({ ok: true });
    }
    if (url.pathname !== '/scores') return json({ error: 'not found' }, 404);

    if (req.method === 'GET') {
      const { results } = await env.DB.prepare(
        'SELECT id, name AS n, score AS s, grade AS g, ac, wx, tod, ts AS d FROM scores WHERE ts >= ?1 ORDER BY score DESC, ts ASC LIMIT 100'
      ).bind(SINCE).all();
      return json(results);
    }
    if (req.method === 'POST') {
      let b;
      try { b = await req.json(); } catch { return json({ error: 'bad json' }, 400); }
      const id = String(b.id || '');
      const s = Number(b.s);
      if (!/^[a-z0-9]{6,24}$/.test(id) || !Number.isInteger(s) || s < 0 || s > 100) return json({ error: 'invalid' }, 400);
      // A score is written once. A repeat of the same id only renames it.
      await env.DB.prepare(
        `INSERT INTO scores (id, name, score, grade, ac, wx, tod, ts) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
         ON CONFLICT(id) DO UPDATE SET name = excluded.name`
      ).bind(id, clean(b.n), s, String(b.g || '').slice(0, 1), String(b.ac || '').slice(0, 20),
             String(b.wx || '').slice(0, 12), b.tod === 'night' ? 'night' : 'day', Math.min(Number(b.d) || Date.now(), Date.now())).run();
      return json({ ok: true });
    }
    return json({ error: 'method not allowed' }, 405);
  },
};

async function stats(env, json) {
  const q = (sql, ...a) => env.DB.prepare(sql).bind(...a);
  const since = Date.now() - 30 * 86400e3;
  const [kinds, modes, acs, causes, grades, wx, tod, daily, land, first] = await env.DB.batch([
    q('SELECT k, COUNT(*) n FROM events GROUP BY k'),
    q("SELECT mode, COUNT(*) n FROM events WHERE k='game_start' GROUP BY mode"),
    q('SELECT ac, k, COUNT(*) n FROM events WHERE ac IS NOT NULL GROUP BY ac, k'),
    q("SELECT cause, COUNT(*) n FROM events WHERE k='crash' AND cause IS NOT NULL GROUP BY cause ORDER BY n DESC LIMIT 8"),
    q("SELECT grade, COUNT(*) n FROM events WHERE k='landing' AND grade IS NOT NULL GROUP BY grade"),
    q("SELECT wx, k, COUNT(*) n FROM events WHERE wx IS NOT NULL AND k IN ('game_start','landing','crash','landing_attempt') GROUP BY wx, k"),
    q("SELECT tod, k, COUNT(*) n FROM events WHERE k IN ('game_start','landing','crash','landing_attempt') GROUP BY tod, k"),
    q("SELECT date(ts/1000,'unixepoch') d, k, COUNT(*) n FROM events WHERE ts >= ?1 AND k IN ('game_start','landing','crash','missed_approach') GROUP BY d, k", since),
    q("SELECT COUNT(*) n, AVG(score) avg_score, MAX(score) best_score, AVG(fpm) avg_fpm, AVG(secs) avg_secs, SUM(ap) ap FROM events WHERE k='landing'"),
    q('SELECT MIN(ts) ts FROM events'),
  ]);
  const body = {
    updated: Date.now(),
    since: first.results[0]?.ts || null,
    kinds: kinds.results, modes: modes.results, aircraft: acs.results, causes: causes.results,
    grades: grades.results, weather: wx.results, tod: tod.results, daily: daily.results,
    landings: land.results[0],
  };
  return json(body, 200, { 'Cache-Control': 'public, max-age=60' });
}

/* ---------------- paid aircraft: Stripe Checkout, licence keys and free codes ----------------
   Nothing about the buyer is kept. A licence is just a random key with the Stripe session (or giveaway code) it came from.
   The sim stores the key in the browser and asks /store/check when an aircraft is chosen. Secrets (wrangler secret put):
     STRIPE_SECRET_KEY  a Stripe secret or restricted key that can create and read Checkout Sessions (sales stay off without it)
     ADMIN_TOKEN        a long random string; it protects /admin/*
   Optional vars: SITE_BASE (default https://flykaitak.com, where Stripe sends the buyer back), STRIPE_API (tests). */
const PRODUCTS = {
  concorde: { name: 'Concorde for Fly Kai Tak', desc: 'Fly the delta-wing Concorde into Kai Tak: droop nose, reheat take-off and the Runway 13 approach. One payment, yours to keep.', cents: 700, cur: 'usd', pre: 'CONC' },
};
const KEY_ABC = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const rnd = (n) => Array.from(crypto.getRandomValues(new Uint8Array(n)), (x) => KEY_ABC[x % 32]).join('');
const eq = (a, b) => { a = String(a); b = String(b); let d = a.length ^ b.length; for (let i = 0; i < Math.max(a.length, b.length); i++) d |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0); return d === 0; };
const KEY_RE = /^[A-Z]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/, CODE_RE = /^FKT-[A-Z0-9]{4}-[A-Z0-9]{4}$/;
const normKey = (v) => String(v == null ? '' : v).toUpperCase().replace(/[^A-Z0-9-]/g, '').slice(0, 40);

async function mintLicence(env, product, src, ref) {
  const P = PRODUCTS[product];
  for (let i = 0; i < 5; i++) {
    const key = `${P.pre}-${rnd(4)}-${rnd(4)}-${rnd(4)}`;
    try {
      await env.DB.prepare('INSERT INTO licences (key, product, src, ref, ts) VALUES (?1,?2,?3,?4,?5)').bind(key, product, src, ref, Date.now()).run();
      return key;
    } catch (e) {
      if (src === 'purchase') { const r = await env.DB.prepare("SELECT key FROM licences WHERE src='purchase' AND ref=?1").bind(ref).first(); if (r) return r.key; }
      if (!/UNIQUE|constraint/i.test(String(e))) throw e;
    }
  }
  throw new Error('could not issue a key');
}

async function stripe(env, method, path, form) {
  const r = await fetch((env.STRIPE_API || 'https://api.stripe.com') + path, {
    method, headers: { authorization: 'Bearer ' + env.STRIPE_SECRET_KEY, ...(form ? { 'content-type': 'application/x-www-form-urlencoded' } : {}) },
    body: form ? new URLSearchParams(form).toString() : undefined });
  let j = null; try { j = await r.json(); } catch {}
  return { ok: r.ok, status: r.status, j };
}

async function store(req, env, url, json) {
  const path = url.pathname;
  if (path.startsWith('/admin/')) return admin(req, env, url, json);
  if (req.method !== 'POST') return json({ error: 'method not allowed' }, 405);
  let b; try { b = await req.json(); } catch { return json({ ok: false, error: 'bad json' }, 400); }
  const product = PRODUCTS[b.product] ? b.product : 'concorde', P = PRODUCTS[product];
  const who = await sha((req.headers.get('cf-connecting-ip') || '') + (env.SALT || 'fkt-replays'));
  // wrong codes, keys and sessions are limited to 15 an hour from one address (kept only as a salted hash)
  const limited = async () => { const r = await env.DB.prepare('SELECT COUNT(*) n FROM lic_fail WHERE who = ?1 AND ts > ?2').bind(who, Date.now() - 3600e3).first(); return r && r.n >= 15; };
  const fail = async (error, status) => { await env.DB.prepare('INSERT INTO lic_fail (who, ts) VALUES (?1,?2)').bind(who, Date.now()).run(); return json({ ok: false, error }, status); };

  if (path === '/store/check') {
    const key = normKey(b.key);
    if (!KEY_RE.test(key)) return json({ ok: false });
    const r = await env.DB.prepare('SELECT product, revoked FROM licences WHERE key = ?1').bind(key).first();
    return json({ ok: !!r && !r.revoked && r.product === product });
  }
  if (path === '/store/checkout') {
    if (!env.STRIPE_SECRET_KEY) return json({ ok: false, error: 'sales are not switched on yet' }, 503);
    const base = (env.SITE_BASE || 'https://flykaitak.com').replace(/\/$/, '');
    const r = await stripe(env, 'POST', '/v1/checkout/sessions', {
      mode: 'payment', 'line_items[0][quantity]': '1', 'line_items[0][price_data][currency]': P.cur,
      'line_items[0][price_data][unit_amount]': String(P.cents), 'line_items[0][price_data][product_data][name]': P.name,
      'line_items[0][price_data][product_data][description]': P.desc,
      success_url: `${base}/?${product}_session={CHECKOUT_SESSION_ID}`, cancel_url: `${base}/?${product}=cancelled`,
      'metadata[product]': product });
    if (!r.ok || !r.j || !r.j.url) return json({ ok: false, error: 'could not start checkout' }, 502);
    return json({ ok: true, url: r.j.url });
  }
  if (path === '/store/claim') {
    if (!env.STRIPE_SECRET_KEY) return json({ ok: false, error: 'sales are not switched on yet' }, 503);
    const sid = String(b.session || '');
    if (!/^cs_(live|test)_[A-Za-z0-9]{10,200}$/.test(sid)) return fail('invalid', 400);
    if (await limited()) return json({ ok: false, error: 'too many tries, try again later' }, 429);
    const have = await env.DB.prepare("SELECT key, revoked FROM licences WHERE src='purchase' AND ref=?1").bind(sid).first();
    if (have) return have.revoked ? json({ ok: false, error: 'revoked' }, 403) : json({ ok: true, key: have.key, product });
    const r = await stripe(env, 'GET', '/v1/checkout/sessions/' + sid);
    const s = r.j;
    // only a paid session that this Worker made for this product counts (so a coffee payment cannot unlock an aircraft)
    if (!r.ok || !s || s.payment_status !== 'paid' || !s.metadata || s.metadata.product !== product || s.currency !== P.cur || !(s.amount_total >= P.cents)) return fail('not paid', 402);
    return json({ ok: true, key: await mintLicence(env, product, 'purchase', sid), product });
  }
  if (path === '/store/redeem') {
    if (await limited()) return json({ ok: false, error: 'too many tries, try again later' }, 429);
    const raw = normKey(b.code);
    if (KEY_RE.test(raw)) {   // a licence key typed in on another device: hand it back if it is good
      const r = await env.DB.prepare('SELECT product, revoked FROM licences WHERE key = ?1').bind(raw).first();
      return r && !r.revoked && r.product === product ? json({ ok: true, key: raw, product, restored: true }) : fail('invalid', 404);
    }
    if (!CODE_RE.test(raw)) return fail('invalid', 404);
    const c = await env.DB.prepare('SELECT * FROM codes WHERE code = ?1').bind(raw).first();
    if (!c || c.disabled || c.product !== product) return fail('invalid', 404);
    if (c.expires && c.expires < Date.now()) return fail('expired', 410);
    // take one use atomically, so two people cannot share the last use
    const u = await env.DB.prepare('UPDATE codes SET uses = uses + 1 WHERE code = ?1 AND uses < max_uses AND disabled = 0').bind(raw).run();
    if (!u.meta || u.meta.changes !== 1) return fail('used', 410);
    return json({ ok: true, key: await mintLicence(env, product, 'code', raw), product });
  }
  return json({ error: 'not found' }, 404);
}

async function admin(req, env, url, json) {
  const tok = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '');
  if (!env.ADMIN_TOKEN || !tok || !eq(tok, env.ADMIN_TOKEN)) return json({ error: 'unauthorised' }, 401);
  const path = url.pathname;
  if (path === '/admin/codes' && req.method === 'GET') {
    const { results } = await env.DB.prepare('SELECT code, product, max_uses, uses, note, ts, expires, disabled FROM codes ORDER BY ts DESC LIMIT 500').all();
    return json({ codes: results });
  }
  if (path === '/admin/sales' && req.method === 'GET') {
    const { results } = await env.DB.prepare('SELECT product, src, revoked, COUNT(*) n FROM licences GROUP BY product, src, revoked').all();
    const c = await env.DB.prepare('SELECT COUNT(*) codes, COALESCE(SUM(max_uses),0) allowed, COALESCE(SUM(uses),0) used FROM codes').first();
    return json({ licences: results, codes: c });
  }
  if (req.method !== 'POST') return json({ error: 'method not allowed' }, 405);
  let b; try { b = await req.json(); } catch { return json({ error: 'bad json' }, 400); }
  if (path === '/admin/codes') {
    const product = PRODUCTS[b.product] ? b.product : 'concorde';
    const count = Math.min(500, Math.max(1, Math.floor(Number(b.count) || 1))), uses = Math.min(100000, Math.max(1, Math.floor(Number(b.uses) || 1)));
    const days = Number(b.days) > 0 ? Number(b.days) : 0, expires = days ? Date.now() + days * 86400e3 : null, note = txt(b.note, 80);
    const codes = [];
    for (let i = 0; i < count; i++) {
      for (let t = 0; t < 5; t++) {
        const code = `FKT-${rnd(4)}-${rnd(4)}`;
        try { await env.DB.prepare('INSERT INTO codes (code, product, max_uses, uses, note, ts, expires, disabled) VALUES (?1,?2,?3,0,?4,?5,?6,0)').bind(code, product, uses, note, Date.now(), expires).run(); codes.push(code); break; }
        catch (e) { if (!/UNIQUE|constraint/i.test(String(e))) throw e; }
      }
    }
    return json({ ok: true, product, uses, expires, note, codes });
  }
  if (path === '/admin/codes/disable') {
    const r = await env.DB.prepare('UPDATE codes SET disabled = ?2 WHERE code = ?1').bind(normKey(b.code), b.enable ? 0 : 1).run();
    return json({ ok: !!(r.meta && r.meta.changes) });
  }
  if (path === '/admin/licences/revoke') {
    const r = await env.DB.prepare('UPDATE licences SET revoked = ?2 WHERE key = ?1').bind(normKey(b.key), b.restore ? 0 : 1).run();
    return json({ ok: !!(r.meta && r.meta.changes) });
  }
  return json({ error: 'not found' }, 404);
}

/* ---------------- replay share links ----------------
   The video is made in the player's browser; this only stores it (R2) with a row in D1, and serves a page per replay.
   Limits: one video up to MAX_VIDEO bytes, 12 uploads an hour from one address (kept only as a salted hash). */
const MAX_VIDEO = 48e6, MAX_IMG = 2e6;
const ID_ABC = 'abcdefghijkmnpqrstuvwxyz23456789';
const rid = () => { const b = crypto.getRandomValues(new Uint8Array(10)); return Array.from(b, (x) => ID_ABC[x & 31]).join(''); };
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const txt = (v, n) => String(v == null ? '' : v).replace(/[\u0000-\u001f<>]/g, '').trim().slice(0, n) || null;
const isMp4 = (b) => b.length > 12 && String.fromCharCode(b[4], b[5], b[6], b[7]) === 'ftyp';
const isJpg = (b) => b.length > 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff;
const isPng = (b) => b.length > 8 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47;
async function sha(s) { const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)); return Array.from(new Uint8Array(d).slice(0, 12), (x) => x.toString(16).padStart(2, '0')).join(''); }
const fileBytes = async (f, max) => (f && typeof f === 'object' && typeof f.arrayBuffer === 'function' && f.size <= max ? new Uint8Array(await f.arrayBuffer()) : null);

async function replayUpload(req, env, json) {
  if (!env.REPLAYS) return json({ error: 'replays not enabled' }, 503);
  if (Number(req.headers.get('content-length') || 0) > MAX_VIDEO + 2 * MAX_IMG + 1e5) return json({ error: 'too large' }, 413);
  const who = await sha((req.headers.get('cf-connecting-ip') || '') + (env.SALT || 'fkt-replays'));
  const recent = await env.DB.prepare('SELECT COUNT(*) n FROM replays WHERE who = ?1 AND ts > ?2').bind(who, Date.now() - 3600e3).first();
  if (recent && recent.n >= 12) return json({ error: 'too many uploads, try again later' }, 429);
  let fd;
  try { fd = await req.formData(); } catch { return json({ error: 'bad form' }, 400); }
  const v = await fileBytes(fd.get('video'), MAX_VIDEO);
  if (!v || v.length < 2000 || !isMp4(v)) return json({ error: 'invalid video' }, 400);
  let p = await fileBytes(fd.get('poster'), MAX_IMG); if (p && !isJpg(p)) p = null;
  let c = await fileBytes(fd.get('card'), MAX_IMG); if (c && !isPng(c)) c = null;
  let m = {};
  try { m = JSON.parse(String(fd.get('meta') || '{}')) || {}; } catch {}
  const id = rid(), meta = { contentType: 'video/mp4', cacheControl: 'public, max-age=31536000, immutable' };
  await env.REPLAYS.put(`replays/${id}.mp4`, v, { httpMetadata: meta });
  if (p) await env.REPLAYS.put(`replays/${id}.jpg`, p, { httpMetadata: { ...meta, contentType: 'image/jpeg' } });
  if (c) await env.REPLAYS.put(`replays/${id}.png`, c, { httpMetadata: { ...meta, contentType: 'image/png' } });
  const kind = ['landed', 'crash', 'missed'].includes(m.kind) ? m.kind : null;
  await env.DB.prepare(
    `INSERT INTO replays (id, ts, who, kind, grade, score, title, eyebrow, ac, route, w, h, secs, lang, size, poster, card)
     VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,?16,?17)`
  ).bind(id, Date.now(), who, kind, txt(m.grade, 1), num(m.score, 0, 100), txt(m.title, 80), txt(m.eyebrow, 60), txt(m.ac, 20), txt(m.route, 60),
         num(m.w, 100, 4000), num(m.h, 100, 4000), num(m.secs, 1, 600), m.lang === 'zh' ? 'zh' : 'en', v.length, p ? 1 : 0, c ? 1 : 0).run();
  const base = (env.PUBLIC_BASE || new URL(req.url).origin).replace(/\/$/, '');
  return json({ id, url: `${base}/r/${id}` });
}

async function replayFile(req, env, key, type) {
  if (!env.REPLAYS) return new Response('Not found', { status: 404 });
  const opts = {}, rg = req.headers.get('range');
  const m = rg && rg.match(/^bytes=(\d*)-(\d*)$/);
  if (m && (m[1] || m[2])) opts.range = m[1] ? (m[2] ? { offset: +m[1], length: +m[2] - +m[1] + 1 } : { offset: +m[1] }) : { suffix: +m[2] };
  const obj = await env.REPLAYS.get(key, opts);
  if (!obj) return new Response('Not found', { status: 404 });
  const h = new Headers({ 'content-type': type, 'accept-ranges': 'bytes', etag: obj.httpEtag,
    'cache-control': 'public, max-age=31536000, immutable', 'access-control-allow-origin': '*' });
  const body = req.method === 'HEAD' ? null : obj.body;
  if (opts.range && obj.range) {
    const off = obj.range.offset ?? obj.size - obj.range.suffix, len = obj.range.length ?? obj.size - off;
    h.set('content-range', `bytes ${off}-${off + len - 1}/${obj.size}`); h.set('content-length', String(len));
    return new Response(body, { status: 206, headers: h });
  }
  h.set('content-length', String(obj.size));
  return new Response(body, { headers: h });
}

const PAGE_TXT = {
  en: { fly: 'Fly it yourself', free: 'Free in your browser. No download.', share: 'Share', copy: 'Copy link', copied: 'Copied',
        grade: 'Grade', crash: 'Accident', missed: 'Approach abandoned', gone: 'This replay is no longer available.',
        desc: (r) => `${r.ac ? r.ac + ' · ' : ''}${r.route || 'Hong Kong Kai Tak, 1998'}. Watch the replay, then try the famous checkerboard approach yourself, free in your browser.` },
  zh: { fly: '親自飛一次', free: '喺瀏覽器免費玩，唔使下載。', share: '分享', copy: '複製連結', copied: '已複製',
        grade: '評級', crash: '意外', missed: '放棄進場', gone: '呢段重播已經冇咗。',
        desc: (r) => `${r.ac ? r.ac + ' · ' : ''}${r.route || '香港啟德機場，1998'}。睇完重播，喺瀏覽器免費親自飛一次著名嘅格仔山進場。` },
};

async function replayPage(id, env, url) {
  const row = env.REPLAYS ? await env.DB.prepare('SELECT * FROM replays WHERE id = ?1').bind(id).first() : null;
  const base = (env.PUBLIC_BASE || url.origin).replace(/\/$/, '');
  const home = 'https://flykaitak.com/?utm_source=replay&utm_medium=social&utm_campaign=replay_page';
  const T = PAGE_TXT[row && row.lang === 'zh' ? 'zh' : 'en'];
  const page = (status, head, body) => new Response(`<!doctype html><html lang="${row && row.lang === 'zh' ? 'zh-HK' : 'en'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">${head}
<link rel="icon" href="https://flykaitak.com/assets/brand/favicon-32.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=B612:wght@400;700&family=B612+Mono:wght@400;700&display=swap">
<style>${PAGE_CSS}</style></head><body>${body}</body></html>`, { status, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' } });
  if (!row) return page(404, '<title>Fly Kai Tak</title>', `<main class="wrap"><div class="checkband"></div><div class="card"><p class="eyebrow">FLY KAI TAK · HONG KONG · 1998</p><h1>${esc(PAGE_TXT.en.gone)}</h1><a class="go" href="${home}">${esc(PAGE_TXT.en.fly)} →</a></div></main>`);
  const sub = row.kind === 'landed' ? `${T.grade} ${esc(row.grade || '')}${row.score != null ? ' · ' + row.score + '/100' : ''}` : row.kind === 'crash' ? T.crash : row.kind === 'missed' ? T.missed : '';
  const title = `${row.title || 'Fly Kai Tak'}${sub ? ' · ' + sub : ''}`, desc = T.desc(row);
  const vid = `${base}/v/${id}.mp4`, pageUrl = `${base}/r/${id}`, img = row.card ? `${base}/c/${id}.png` : row.poster ? `${base}/p/${id}.jpg` : 'https://flykaitak.com/assets/social/og-image.jpg';
  const w = row.w || 1280, h = row.h || 720, port = h > w, q = encodeURIComponent;
  const head = `<title>${esc(title)} · Fly Kai Tak</title><meta name="description" content="${esc(desc)}">
<link rel="canonical" href="${esc(pageUrl)}">
<meta property="og:type" content="video.other"><meta property="og:site_name" content="Fly Kai Tak">
<meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${esc(pageUrl)}">
<meta property="og:image" content="${esc(img)}">${row.card ? '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' : ''}
<meta property="og:video" content="${esc(vid)}"><meta property="og:video:secure_url" content="${esc(vid)}"><meta property="og:video:type" content="video/mp4">
<meta property="og:video:width" content="${w}"><meta property="og:video:height" content="${h}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${esc(title)}"><meta name="twitter:description" content="${esc(desc)}"><meta name="twitter:image" content="${esc(img)}">`;
  const text = `${title} · Fly Kai Tak`;
  const links = [['X', `https://twitter.com/intent/tweet?text=${q(text)}&url=${q(pageUrl)}`], ['Facebook', `https://www.facebook.com/sharer/sharer.php?u=${q(pageUrl)}`],
    ['WhatsApp', `https://wa.me/?text=${q(text + ' ' + pageUrl)}`], ['Reddit', `https://www.reddit.com/submit?url=${q(pageUrl)}&title=${q(text)}`],
    ['Threads', `https://www.threads.net/intent/post?text=${q(text + ' ' + pageUrl)}`]];
  const body = `<main class="wrap${port ? ' port' : ''}"><div class="checkband"></div><div class="card">
<p class="eyebrow">${esc(row.eyebrow || 'FLY KAI TAK · HONG KONG · 1998')}</p>
<h1>${esc(row.title || 'Fly Kai Tak')}</h1>${sub ? `<p class="sub${row.kind !== 'landed' ? ' bad' : ''}">${sub}</p>` : ''}
<video src="${esc(vid)}" poster="${row.poster ? esc(`${base}/p/${id}.jpg`) : ''}" controls playsinline preload="metadata" width="${w}" height="${h}"></video>
<p class="meta">${esc([row.ac, row.route].filter(Boolean).join(' · '))}</p>
<a class="go" href="${home}">${esc(T.fly)} →</a><p class="free">${esc(T.free)}</p>
<div class="share"><span>${esc(T.share)}</span>${links.map(([n, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${n}</a>`).join('')}<button type="button" id="cp" data-u="${esc(pageUrl)}">${esc(T.copy)}</button></div>
</div><p class="foot"><a href="${home}">flykaitak.com</a> · Hong Kong Kai Tak, 1998</p></main>
<script>document.getElementById('cp').onclick=async e=>{const b=e.currentTarget;try{await navigator.clipboard.writeText(b.dataset.u);b.textContent=${JSON.stringify(T.copied)}}catch(_){prompt('',b.dataset.u)}}</script>`;
  return page(200, head, body);
}

const PAGE_CSS = `:root{--ink:#0a1115;--panel:#121e24;--line:#27373e;--line-2:#3a5058;--text:#e9eee8;--muted:#93a6a2;--checker:#e8571f;--paper:#f5efe3;--jade:#1b7d52;--phosphor:#8ff5a8;--alarm:#ff5b4f;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--ink);color:var(--text);font-family:"B612",ui-sans-serif,system-ui,sans-serif;min-height:100vh}
.wrap{width:min(860px,100%);margin:0 auto;padding:24px 16px 40px}.wrap.port{width:min(520px,100%)}
.checkband{height:12px;background:repeating-conic-gradient(var(--checker) 0 25%,var(--paper) 0 50%) 0 0/12px 12px;border-radius:3px 3px 0 0}
.card{background:var(--panel);border:1px solid var(--line-2);border-top:0;border-radius:0 0 4px 4px;padding:20px 22px 24px;display:grid;gap:12px}
.eyebrow{margin:0;font-family:"B612 Mono",monospace;font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--phosphor)}
h1{margin:0;font-size:clamp(24px,5vw,34px);line-height:1.1}
.sub{margin:0;font-family:"B612 Mono",monospace;font-size:15px;color:var(--phosphor)}.sub.bad{color:var(--alarm)}
video{display:block;width:100%;height:auto;background:#000;border:1px solid var(--line);border-radius:3px}
.meta{margin:0;font-family:"B612 Mono",monospace;font-size:12px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
.go{display:block;text-align:center;background:var(--jade);color:#f6f5f0;text-decoration:none;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:15px 18px;border-radius:3px;font-size:15px}
.go:hover{filter:brightness(1.1)}.free{margin:-4px 0 0;text-align:center;color:var(--muted);font-size:13px}
.share{display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-top:1px solid var(--line);padding-top:14px}
.share span{font-family:"B612 Mono",monospace;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-right:4px}
.share a,.share button{font:inherit;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--text);background:var(--ink);border:1px solid var(--line-2);border-radius:3px;padding:9px 12px;text-decoration:none;cursor:pointer}
.share a:hover,.share button:hover{border-color:var(--paper)}a:focus-visible,button:focus-visible{outline:2px solid var(--checker);outline-offset:2px}
.foot{text-align:center;color:var(--muted);font-size:12px;margin-top:16px}.foot a{color:var(--checker);text-decoration:none}`;
