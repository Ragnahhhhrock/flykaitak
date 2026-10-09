CREATE TABLE IF NOT EXISTS scores (
  id    TEXT PRIMARY KEY,
  name  TEXT NOT NULL,
  score INTEGER NOT NULL,
  grade TEXT,
  ac    TEXT,
  wx    TEXT,
  tod   TEXT,
  ts    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS scores_rank ON scores (score DESC, ts ASC);

-- Anonymous gameplay events for the public /stats/ dashboard. No IP, no user id.
CREATE TABLE IF NOT EXISTS events (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  ts    INTEGER NOT NULL,
  k     TEXT NOT NULL,
  mode  TEXT,
  ac    TEXT,
  wx    TEXT,
  tod   TEXT,
  cause TEXT,
  grade TEXT,
  score INTEGER,
  fpm   INTEGER,
  secs  INTEGER,
  ap    INTEGER
);
CREATE INDEX IF NOT EXISTS events_k_ts ON events (k, ts);
