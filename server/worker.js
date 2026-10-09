// Fly Kai Tak API: a Cloudflare Worker with a D1 database.
//   GET  /scores  -> top 100 [{id,n,s,g,ac,wx,tod,d}]
//   POST /scores  -> add or rename {id,n,s,g,ac,wx,tod,d}
//   POST /events  -> one anonymous gameplay event {k,mode,ac,wx,tod,cause,grade,score,fpm,secs,ap}
//   GET  /stats   -> public aggregate counts for flykaitak.com/stats/
const ORIGINS = ['https://flykaitak.com', 'https://www.flykaitak.com'];
const clean = (n) => String(n || '').replace(/[^A-Za-z0-9 _.\-]/g, '').trim().slice(0, 12).toUpperCase() || 'PILOT';
const EVENTS = new Set(['game_start', 'landing_attempt', 'landing', 'crash', 'missed_approach', 'aircraft_select', 'lesson_start', 'lesson_complete']);
const tok = (v, n = 24) => String(v == null ? '' : v).replace(/[^A-Za-z0-9 _.,:'\/\-]/g, '').trim().slice(0, n) || null;
const num = (v, lo, hi) => { v = Math.round(Number(v)); return Number.isFinite(v) && v >= lo && v <= hi ? v : null; };

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ORIGINS.includes(origin) ? origin : ORIGINS[0],
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'content-type',
      Vary: 'Origin',
    };
    const json = (body, status = 200, extra = {}) =>
      new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', ...cors, ...extra } });
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    if (url.pathname === '/stats' && req.method === 'GET') return stats(env, json);
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
        'SELECT id, name AS n, score AS s, grade AS g, ac, wx, tod, ts AS d FROM scores ORDER BY score DESC, ts ASC LIMIT 100'
      ).all();
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
