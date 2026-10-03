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
