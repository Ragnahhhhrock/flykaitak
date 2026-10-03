// Fly Kai Tak high score API: a Cloudflare Worker with a D1 database.
//   GET  /scores  -> top 100 [{id,n,s,g,ac,wx,tod,d}]
//   POST /scores  -> add or rename {id,n,s,g,ac,wx,tod,d}
const ORIGINS = ['https://flykaitak.com', 'https://www.flykaitak.com'];
const clean = (n) => String(n || '').replace(/[^A-Za-z0-9 _.\-]/g, '').trim().slice(0, 12).toUpperCase() || 'PILOT';

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ORIGINS.includes(origin) ? origin : ORIGINS[0],
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'content-type',
      Vary: 'Origin',
    };
    const json = (body, status = 200) =>
      new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', ...cors } });
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
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
