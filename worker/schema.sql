-- D1 schema for the comments Worker. Run once (Cloudflare dashboard -> D1 -> your database -> Console).
CREATE TABLE IF NOT EXISTS comments (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  page       TEXT    NOT NULL,                 -- e.g. /blog/2022-08-24/
  parent_id  INTEGER,                          -- top-level comment this one belongs to (NULL = top level)
  reply_to   INTEGER,                          -- the comment actually answered (for "回覆 XXX")
  name       TEXT    NOT NULL,
  email      TEXT    NOT NULL DEFAULT '',      -- private: never returned by the public API
  avatar     TEXT    NOT NULL DEFAULT '',      -- keyed hash of the email (public, cannot be reversed without PEPPER)
  body       TEXT    NOT NULL,
  status     TEXT    NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'spam')),
  is_owner   INTEGER NOT NULL DEFAULT 0,
  ip_hash    TEXT    NOT NULL DEFAULT '',      -- keyed hash of the IP, only used for rate limiting
  created_at INTEGER NOT NULL                  -- unix milliseconds
);
CREATE INDEX IF NOT EXISTS idx_comments_page   ON comments (page, status, created_at);
CREATE INDEX IF NOT EXISTS idx_comments_email  ON comments (email, status);
CREATE INDEX IF NOT EXISTS idx_comments_ip     ON comments (ip_hash, created_at);

CREATE TABLE IF NOT EXISTS blocked (
  email TEXT PRIMARY KEY
);
