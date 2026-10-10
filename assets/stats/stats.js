/* Fly Kai Tak public stats dashboard. Reads GET {FKT_API}/stats (see server/worker.js).
   Add ?demo to the URL to preview the layout with clearly labelled sample data. */
(function () {
  var app = document.getElementById('app');
  var MODES = { approach: 'IGS 13 approach', approach31: 'Runway 31 approach', free: 'Free flight, runway 13', free31: 'Free flight, runway 31',
    watch: 'Plane Spotter, runway 13', watch31: 'Plane Spotter, runway 31', lesson: 'Take-off lesson', lesson_land: 'Landing lesson', tour: 'Helicopter tour' };
  var ACS = { b744: '747-400', b772: '777-200', a333: 'A330-300', conc: 'Concorde', a343: 'A340-300', b744f: '747-400F', a306f: 'A300-600F' };
  var WXN = { clear: 'Clear', rain: 'Rain', typhoon: 'Typhoon', storm: 'Storm', lowcloud: 'Low cloud', fog: 'Fog' };
  var GRADES = ['A', 'B', 'C', 'D', 'F'];
  var C = { land: '#2fa36d', miss: '#ffb94a', crash: '#ff5b4f' };

  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function fmt(n) { return Number(n || 0).toLocaleString('en-AU'); }
  function pct(a, b) { return b ? Math.round(1000 * a / b) / 10 : null; }
  function pcts(a, b) { var p = pct(a, b); return p === null ? '–' : p + '%'; }
  function dur(s) { s = Math.round(s || 0); return s >= 60 ? Math.floor(s / 60) + 'm ' + String(s % 60).padStart(2, '0') + 's' : s + 's'; }

  function demo() {
    var r = function (n) { return Math.floor(Math.random() * n); };
    var kinds = [['game_start', 1840], ['landing_attempt', 1210], ['landing', 690], ['crash', 455], ['missed_approach', 140], ['aircraft_select', 2650], ['lesson_start', 210], ['lesson_complete', 120]];
    var aircraft = []; var acn = { b744: 36, b772: 22, a333: 12, conc: 18, a343: 6, b744f: 4, a306f: 2 };
    Object.keys(acn).forEach(function (k) {
      var sel = acn[k] * 26, st = Math.round(acn[k] * 18.4), la = Math.round(st * .34), cr = Math.round(st * .27), at = Math.round(st * .66);
      aircraft.push({ ac: k, k: 'aircraft_select', n: sel }, { ac: k, k: 'game_start', n: st }, { ac: k, k: 'landing', n: la }, { ac: k, k: 'crash', n: cr }, { ac: k, k: 'landing_attempt', n: at });
    });
    var weather = []; var wxs = { clear: 800, rain: 420, typhoon: 160, storm: 210, lowcloud: 150, fog: 100 }; var wl = { clear: .5, rain: .38, typhoon: .12, storm: .2, lowcloud: .28, fog: .22 };
    Object.keys(wxs).forEach(function (k) { var n = wxs[k]; weather.push({ wx: k, k: 'game_start', n: n }, { wx: k, k: 'landing_attempt', n: Math.round(n * .65) }, { wx: k, k: 'landing', n: Math.round(n * wl[k] * .85) }, { wx: k, k: 'crash', n: Math.round(n * (.42 - wl[k] * .5)) }); });
    var daily = []; for (var i = 29; i >= 0; i--) { var d = new Date(Date.now() - i * 86400e3).toISOString().slice(0, 10), s = 20 + r(70); daily.push({ d: d, k: 'game_start', n: s }, { d: d, k: 'landing', n: Math.round(s * .34) + r(5) }, { d: d, k: 'crash', n: Math.round(s * .25) + r(4) }, { d: d, k: 'missed_approach', n: r(8) }); }
    return { demo: true, updated: Date.now(), since: Date.now() - 30 * 86400e3, kinds: kinds.map(function (x) { return { k: x[0], n: x[1] }; }),
      modes: [{ mode: 'approach', n: 920 }, { mode: 'free', n: 410 }, { mode: 'watch', n: 160 }, { mode: 'approach31', n: 140 }, { mode: 'lesson', n: 110 }, { mode: 'free31', n: 60 }, { mode: 'lesson_land', n: 40 }],
      aircraft: aircraft, weather: weather, daily: daily,
      tod: [{ tod: 'day', k: 'game_start', n: 1300 }, { tod: 'night', k: 'game_start', n: 540 }, { tod: 'day', k: 'landing', n: 520 }, { tod: 'night', k: 'landing', n: 170 }, { tod: 'day', k: 'crash', n: 300 }, { tod: 'night', k: 'crash', n: 155 }],
      causes: [{ cause: 'Crashed short of the runway', n: 140 }, { cause: 'Hit the buildings', n: 110 }, { cause: 'Landed in the harbour', n: 90 }, { cause: 'Runway overrun', n: 70 }, { cause: 'Tail strike', n: 45 }],
      grades: [{ grade: 'A', n: 80 }, { grade: 'B', n: 190 }, { grade: 'C', n: 230 }, { grade: 'D', n: 130 }, { grade: 'F', n: 60 }],
      landings: { n: 690, avg_score: 63.4, best_score: 98, avg_fpm: 312, avg_secs: 281, ap: 210 } };
  }

  function sumKind(rows, key, val, kind) { var t = 0; rows.forEach(function (r) { if (r[key] === val && r.k === kind) t += r.n; }); return t; }
  function kindN(d, k) { var t = 0; d.kinds.forEach(function (r) { if (r.k === k) t = r.n; }); return t; }

  var IC = {
    start: '<path d="M3 19h18"/><path d="M4.5 14.5l3.2.9 4.1-3.6-5.6-3 1.3-1 7.9 1.9 4.2-3.6a1.9 1.9 0 0 1 2.7 2.7l-3.8 4.4-1.2 7.7-1.3.3-1.9-5.3-4.3 2.8z"/>',
    attempt: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    land: '<circle cx="12" cy="12" r="9"/><path d="M7.5 12.5l3 3 6-7"/>',
    crash: '<path d="M12 2l2.4 4.9 5.4-.8-2.5 4.8 4.2 3.6-5.3 1.2.1 5.4L12 18.4l-4.3 2.7.1-5.4-5.3-1.2 4.2-3.6-2.5-4.8 5.4.8z"/>',
    miss: '<path d="M4 20c5 0 8-2.5 8-8V4"/><path d="M7.5 7.5L12 3l4.5 4.5"/><path d="M3 20h5"/>'
  };
  function icon(k) { return '<svg class="ic" viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + IC[k] + '</svg>'; }
  function kpi(cls, l, v, s, ic) { return '<div class="kpi ' + cls + '">' + icon(ic) + '<p class="l">' + esc(l) + '</p><p class="v">' + esc(v) + '</p>' + (s ? '<p class="s">' + esc(s) + '</p>' : '') + '</div>'; }

  function bars(items, opts) {
    opts = opts || {}; var max = 0; items.forEach(function (i) { if (i.v > max) max = i.v; });
    if (!items.length || !max) return '<p class="empty">No data yet.</p>';
    return '<ul class="rows">' + items.map(function (i) {
      return '<li class="row' + (opts.alt ? ' alt' : '') + '"><span class="n" title="' + esc(i.n) + '">' + esc(i.n) + '</span><span class="t"><span class="b" style="width:' + (100 * i.v / max).toFixed(1) + '%"></span></span><span class="c">' + fmt(i.v) + (i.s ? '<small>' + esc(i.s) + '</small>' : '') + '</span></li>';
    }).join('') + '</ul>';
  }

  function dailyChart(d) {
    var days = {}; d.daily.forEach(function (r) { var o = days[r.d] || (days[r.d] = { land: 0, miss: 0, crash: 0, start: 0 }); if (r.k === 'landing') o.land = r.n; else if (r.k === 'crash') o.crash = r.n; else if (r.k === 'missed_approach') o.miss = r.n; else if (r.k === 'game_start') o.start = r.n; });
    var keys = []; for (var i = 29; i >= 0; i--) keys.push(new Date(Date.now() - i * 86400e3).toISOString().slice(0, 10));
    var W = 720, H = 220, L = 34, B = 24, T = 8, pw = W - L - 6, ph = H - B - T, bw = pw / keys.length;
    var max = 1; keys.forEach(function (k) { var o = days[k]; if (o) max = Math.max(max, o.land + o.miss + o.crash); });
    var step = max <= 5 ? 1 : max <= 20 ? 5 : max <= 60 ? 10 : max <= 150 ? 25 : 50; var top = Math.ceil(max / step) * step;
    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Outcomes per day, last 30 days">';
    for (var g = 0; g <= top; g += step) { var y = T + ph - ph * g / top; svg += '<g class="grid"><line x1="' + L + '" x2="' + (W - 6) + '" y1="' + y + '" y2="' + y + '"/></g><text x="' + (L - 6) + '" y="' + (y + 3.5) + '" text-anchor="end">' + g + '</text>'; }
    keys.forEach(function (k, i) {
      var o = days[k] || { land: 0, miss: 0, crash: 0, start: 0 }, x = L + i * bw + bw * .18, w = bw * .64, y0 = T + ph;
      [['land', 'Landings'], ['miss', 'Missed approaches'], ['crash', 'Crashes']].forEach(function (s) {
        var h = ph * o[s[0]] / top; if (!h) return; var yy = y0 - h;
        svg += '<rect x="' + x.toFixed(1) + '" y="' + yy.toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + Math.max(h - 2, 1).toFixed(1) + '" rx="2" fill="' + C[s[0]] + '"/>'; y0 = yy;
      });
      if (i % 5 === 0 || i === keys.length - 1) svg += '<text x="' + (x + w / 2).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle">' + k.slice(5) + '</text>';
      svg += '<rect class="hit" tabindex="0" data-k="' + k + '" data-i="' + i + '" x="' + (L + i * bw).toFixed(1) + '" y="' + T + '" width="' + bw.toFixed(1) + '" height="' + ph + '"/>';
    });
    svg += '</svg>';
    var rows = keys.map(function (k) { var o = days[k] || { land: 0, miss: 0, crash: 0, start: 0 }; return '<tr><td>' + k + '</td><td>' + o.start + '</td><td>' + o.land + '</td><td>' + o.miss + '</td><td>' + o.crash + '</td></tr>'; }).join('');
    return { html: '<div class="legend"><span><i style="background:' + C.land + '"></i>Landings</span><span><i style="background:' + C.miss + '"></i>Missed approaches</span><span><i style="background:' + C.crash + '"></i>Crashes</span></div><div class="chart" id="dchart">' + svg + '<div class="tip" id="dtip"></div></div>' +
      '<details class="tbl"><summary>View as table</summary><table class="dt"><thead><tr><th>Day</th><th>Flights</th><th>Landings</th><th>Missed</th><th>Crashes</th></tr></thead><tbody>' + rows + '</tbody></table></details>', days: days, keys: keys };
  }

  function wireTip(dc) {
    var box = document.getElementById('dchart'), tip = document.getElementById('dtip'); if (!box) return;
    function show(el) {
      var k = el.getAttribute('data-k'), o = dc.days[k] || { land: 0, miss: 0, crash: 0, start: 0 }, rb = el.getBoundingClientRect(), bb = box.getBoundingClientRect();
      tip.innerHTML = '<b>' + k + '</b><br>Flights <b>' + o.start + '</b><br>Landings <b>' + o.land + '</b><br>Missed <b>' + o.miss + '</b><br>Crashes <b>' + o.crash + '</b>';
      tip.style.left = Math.min(Math.max(rb.left - bb.left + rb.width / 2, 70), bb.width - 70) + 'px'; tip.style.top = (rb.top - bb.top + 40) + 'px'; tip.classList.add('on');
    }
    box.querySelectorAll('rect.hit').forEach(function (r) { r.addEventListener('mouseenter', function () { show(r); }); r.addEventListener('focus', function () { show(r); }); r.addEventListener('mouseleave', function () { tip.classList.remove('on'); }); r.addEventListener('blur', function () { tip.classList.remove('on'); }); });
  }

  function render(d) {
    var starts = kindN(d, 'game_start'), att = kindN(d, 'landing_attempt'), land = kindN(d, 'landing'), crash = kindN(d, 'crash'), miss = kindN(d, 'missed_approach');
    var L = d.landings || {};
    var h = '';
    if (d.demo) h += '<p class="banner"><b>Sample data.</b> This is a layout preview, not real flights.</p>';
    h += '<p class="meta">UPDATED ' + new Date(d.updated).toLocaleString('en-AU', { dateStyle: 'medium', timeStyle: 'short' }).toUpperCase() + (d.since ? ' · COUNTING SINCE ' + new Date(d.since).toLocaleDateString('en-AU', { dateStyle: 'medium' }).toUpperCase() : '') + '</p>';
    h += '<div class="kpis">' + kpi('', 'Flights started', fmt(starts), 'All modes, including lessons and Plane Spotter', 'start') +
      kpi('', 'Landing attempts', fmt(att), 'Wheels touched, or an accident or go-around with the gear down', 'attempt') +
      kpi('ok', 'Successful landings', fmt(land), pcts(land, att) + ' of attempts', 'land') +
      kpi('bad', 'Crashes', fmt(crash), pcts(crash, att) + ' of attempts', 'crash') +
      kpi('warn', 'Missed approaches', fmt(miss), 'Go-arounds and overflights', 'miss') + '</div>';

    var dc = dailyChart(d);
    h += '<div class="grid">';
    h += '<section class="card wide"><h2>Outcomes per day</h2><p class="sub">Landings, missed approaches and crashes over the last 30 days.</p>' + dc.html + '</section>';

    var modes = d.modes.map(function (m) { return { n: MODES[m.mode] || m.mode || 'Unknown', v: m.n, s: pcts(m.n, starts) }; }).sort(function (a, b) { return b.v - a.v; });
    h += '<section class="card"><h2>Mode selections</h2><p class="sub">How often each way of flying was started.</p>' + bars(modes) + '</section>';

    var acNames = {}; d.aircraft.forEach(function (r) { acNames[r.ac] = 1; });
    var acl = Object.keys(acNames).map(function (a) { return { a: a, sel: sumKind(d.aircraft, 'ac', a, 'aircraft_select'), st: sumKind(d.aircraft, 'ac', a, 'game_start'), la: sumKind(d.aircraft, 'ac', a, 'landing'), cr: sumKind(d.aircraft, 'ac', a, 'crash'), at: sumKind(d.aircraft, 'ac', a, 'landing_attempt') }; });
    h += '<section class="card"><h2>Aircraft selected</h2><p class="sub">Times each aircraft card was chosen on the setup screen.</p>' + bars(acl.slice().sort(function (a, b) { return b.sel - a.sel; }).map(function (a) { return { n: ACS[a.a] || a.a, v: a.sel }; })) + '</section>';

    h += '<section class="card wide"><h2>Aircraft results</h2><p class="sub">Flights started, landings and crashes for each type. Success rate is landings divided by landing attempts.</p><table class="dt"><thead><tr><th>Aircraft</th><th>Flights</th><th>Attempts</th><th>Landings</th><th>Crashes</th><th>Success</th></tr></thead><tbody>' +
      acl.sort(function (a, b) { return b.st - a.st; }).map(function (a) { return '<tr><td>' + esc(ACS[a.a] || a.a) + '</td><td>' + fmt(a.st) + '</td><td>' + fmt(a.at) + '</td><td>' + fmt(a.la) + '</td><td>' + fmt(a.cr) + '</td><td>' + pcts(a.la, a.at) + '</td></tr>'; }).join('') + '</tbody></table></section>';

    var wxl = Object.keys(WXN).map(function (w) { return { w: w, st: sumKind(d.weather, 'wx', w, 'game_start'), at: sumKind(d.weather, 'wx', w, 'landing_attempt'), la: sumKind(d.weather, 'wx', w, 'landing'), cr: sumKind(d.weather, 'wx', w, 'crash') }; });
    h += '<section class="card"><h2>Weather flown</h2><p class="sub">Flights started in each weather preset.</p>' + bars(wxl.slice().sort(function (a, b) { return b.st - a.st; }).map(function (w) { return { n: WXN[w.w], v: w.st }; })) + '</section>';
    h += '<section class="card"><h2>Landing success by weather</h2><p class="sub">Landings as a share of attempts. Typhoon and fog are the hard ones.</p>' + bars(wxl.filter(function (w) { return w.at > 0; }).map(function (w) { return { n: WXN[w.w], v: Math.round(100 * w.la / w.at), s: '% of ' + fmt(w.at) }; }).sort(function (a, b) { return b.v - a.v; })) + '</section>';

    h += '<section class="card"><h2>What brings them down</h2><p class="sub">Most common crash causes.</p>' + bars(d.causes.map(function (c) { return { n: c.cause, v: c.n }; }), { alt: true }) + '</section>';
    var gm = {}; d.grades.forEach(function (g) { gm[g.grade] = g.n; });
    h += '<section class="card"><h2>Landing grades</h2><p class="sub">How the successful landings were graded.</p>' + bars(GRADES.map(function (g) { return { n: 'Grade ' + g, v: gm[g] || 0 }; })) + '</section>';

    var dn = ['day', 'night'].map(function (t) { return { n: t === 'day' ? 'Day' : 'Night', st: sumKind(d.tod, 'tod', t, 'game_start'), la: sumKind(d.tod, 'tod', t, 'landing'), cr: sumKind(d.tod, 'tod', t, 'crash') }; });
    h += '<section class="card"><h2>Day and night</h2><p class="sub">Flights, landings and crashes by time of day.</p><table class="dt"><thead><tr><th></th><th>Flights</th><th>Landings</th><th>Crashes</th></tr></thead><tbody>' + dn.map(function (r) { return '<tr><td>' + r.n + '</td><td>' + fmt(r.st) + '</td><td>' + fmt(r.la) + '</td><td>' + fmt(r.cr) + '</td></tr>'; }).join('') + '</tbody></table></section>';

    h += '<section class="card"><h2>Landing quality and learning</h2><p class="sub">Averages across all successful landings, and lesson uptake.</p><table class="dt"><tbody>' +
      '<tr><td>Average landing score</td><td>' + (L.avg_score != null ? Math.round(L.avg_score) + ' / 100' : '–') + '</td></tr>' +
      '<tr><td>Best landing score</td><td>' + (L.best_score != null ? L.best_score + ' / 100' : '–') + '</td></tr>' +
      '<tr><td>Average touchdown rate</td><td>' + (L.avg_fpm != null ? Math.round(L.avg_fpm) + ' fpm' : '–') + '</td></tr>' +
      '<tr><td>Average flight time to landing</td><td>' + (L.avg_secs != null ? dur(L.avg_secs) : '–') + '</td></tr>' +
      '<tr><td>Landings with autopilot</td><td>' + pcts(L.ap || 0, L.n || 0) + '</td></tr>' +
      '<tr><td>Lessons started / completed</td><td>' + fmt(kindN(d, 'lesson_start')) + ' / ' + fmt(kindN(d, 'lesson_complete')) + '</td></tr>' +
      '</tbody></table></section>';
    h += '</div><p class="note">Counts come from flights played on flykaitak.com and start from the day the stats feed went live. Autopilot landings count as landings. Plane Spotter flights count as flights started but never as landing attempts.</p>';
    app.innerHTML = h; wireTip(dc);
  }

  function msg(t) { app.innerHTML = '<p class="empty">' + t + '</p>'; }
  if (/[?&]demo\b/.test(location.search)) return render(demo());
  var api = window.FKT_API;
  if (!api) return msg('The stats feed is not connected yet. Check back soon.');
  fetch(api + '/stats').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
    if (!d.kinds || !d.kinds.length) return msg('No flights recorded yet. Be the first: <a href="/">fly the approach</a>.');
    render(d);
  }).catch(function () { msg('Could not load the stats right now. Try again in a minute.'); });
})();
