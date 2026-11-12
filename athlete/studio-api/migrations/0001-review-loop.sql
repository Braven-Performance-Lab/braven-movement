-- Braven Studio review loop, phase A (specification 4: ACC-2, ACC-3, ACC-5, FBK-1, FBK-2,
-- FBK-4, FBK-6, SAFE-4).
--
-- Four things are stored: who may come in, which athlete versions exist, what was said about
-- them, and a record of each act. The rules that must never be broken are triggers here and not
-- only checks in the Worker, so that a later route, a script or a console session cannot break
-- them by forgetting.

-- An invitation is the only way in. `email` is lower case. A row is open while it has neither a
-- redeemed_at nor a revoked_at, and one address has one open row at most.
CREATE TABLE IF NOT EXISTS invitations (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  email       TEXT NOT NULL CHECK (email = lower(email)),
  role        TEXT NOT NULL CHECK (role IN ('reviewer', 'author', 'owner')),
  invited_by  TEXT NOT NULL,
  created_at  INTEGER NOT NULL,
  redeemed_at INTEGER,
  redeemed_by TEXT,
  revoked_at  INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS invitations_one_open ON invitations (email)
  WHERE redeemed_at IS NULL AND revoked_at IS NULL;

-- One row per account, keyed by the Firebase uid: the same uid Braven Tactics sees, so a person
-- is one identity in the two products (ACC-4). A removed person keeps the row, because their
-- comments keep an author.
CREATE TABLE IF NOT EXISTS members (
  uid        TEXT PRIMARY KEY,
  email      TEXT NOT NULL,
  name       TEXT,
  role       TEXT NOT NULL CHECK (role IN ('reviewer', 'author', 'owner')),
  joined_at  INTEGER NOT NULL,
  removed_at INTEGER
);
CREATE TRIGGER IF NOT EXISTS members_never_deleted BEFORE DELETE ON members
BEGIN SELECT RAISE(ABORT, 'a member is removed by date and never deleted'); END;

-- An athlete version. `id` is the sha256 of the bytes of athlete-manifest.json, which covers the
-- model, the movement library (the phases) and the clip times. `manifest` is that text.
CREATE TABLE IF NOT EXISTS versions (
  id            TEXT PRIMARY KEY CHECK (length(id) = 64),
  model_sha256  TEXT NOT NULL CHECK (length(model_sha256) = 64),
  revision      INTEGER,
  manifest      TEXT NOT NULL,
  state         TEXT NOT NULL CHECK (state IN ('draft', 'published')),
  created_by    TEXT NOT NULL,
  created_at    INTEGER NOT NULL,
  published_by  TEXT,
  published_at  INTEGER
);
CREATE INDEX IF NOT EXISTS versions_published ON versions (state, published_at DESC);
CREATE TRIGGER IF NOT EXISTS versions_published_fixed BEFORE UPDATE ON versions
WHEN OLD.state = 'published'
BEGIN SELECT RAISE(ABORT, 'a published version does not change'); END;
CREATE TRIGGER IF NOT EXISTS versions_never_deleted BEFORE DELETE ON versions
BEGIN SELECT RAISE(ABORT, 'a version is never deleted'); END;

-- A comment. It belongs to one clip in one version at one time or time range, and that never
-- changes (FBK-1, SAFE-4). An answer is a new row with parent_id set.
CREATE TABLE IF NOT EXISTS comments (
  id            TEXT PRIMARY KEY,
  version_id    TEXT NOT NULL REFERENCES versions (id),
  model_sha256  TEXT NOT NULL,
  clip_id       TEXT NOT NULL,
  t_start       REAL NOT NULL CHECK (t_start >= 0),
  t_end         REAL CHECK (t_end IS NULL OR t_end > t_start),
  kind          TEXT NOT NULL CHECK (kind IN ('looks-wrong', 'technique-wrong', 'question', 'approve', 'answer')),
  body          TEXT NOT NULL,
  body_part     TEXT,
  phase         TEXT,
  camera_view   TEXT,
  camera        TEXT,
  parent_id     TEXT REFERENCES comments (id),
  author_uid    TEXT NOT NULL REFERENCES members (uid),
  created_at    INTEGER NOT NULL,
  CHECK ((kind = 'answer') = (parent_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS comments_by_clip ON comments (clip_id, version_id, created_at);
CREATE INDEX IF NOT EXISTS comments_by_version ON comments (version_id, created_at);
CREATE TRIGGER IF NOT EXISTS comments_no_update BEFORE UPDATE ON comments
BEGIN SELECT RAISE(ABORT, 'comments are append-only'); END;
CREATE TRIGGER IF NOT EXISTS comments_no_delete BEFORE DELETE ON comments
BEGIN SELECT RAISE(ABORT, 'comments are append-only'); END;

-- Who did what and when (ACC-5). `subject` is the id of the thing acted on.
CREATE TABLE IF NOT EXISTS events (
  id         TEXT PRIMARY KEY,
  at         INTEGER NOT NULL,
  actor_uid  TEXT NOT NULL,
  action     TEXT NOT NULL,
  subject    TEXT NOT NULL,
  detail     TEXT
);
CREATE INDEX IF NOT EXISTS events_by_subject ON events (subject, at);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
