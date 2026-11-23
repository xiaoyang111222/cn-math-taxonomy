-- math.pansgo.com 账号与云同步。只存账号、验证码哈希、会话哈希和 6 份同步数据；题库不进 D1。
-- 时间一律是 Unix 毫秒。本地建库：wrangler d1 execute math-pansgo --local --file=api/schema.sql
-- 已上线的库不会因为这里的 CREATE TABLE IF NOT EXISTS 多出新列：users 的 digest_opt_out / digest_token
-- 要另跑 api/migrations/0001_digest.sql（只跑一次，列已存在会报错）。

CREATE TABLE IF NOT EXISTS users (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  email           TEXT    NOT NULL UNIQUE,
  created_at      INTEGER NOT NULL,
  mail_consent    INTEGER NOT NULL DEFAULT 0,
  mkt_consent     INTEGER NOT NULL DEFAULT 0,
  mail_consent_at INTEGER,
  mkt_consent_at  INTEGER,
  digest_opt_out  INTEGER NOT NULL DEFAULT 0,
  digest_token    TEXT
);

CREATE TABLE IF NOT EXISTS otp_codes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  email      TEXT    NOT NULL,
  code_hash  TEXT    NOT NULL,
  expires_at INTEGER NOT NULL,
  used       INTEGER NOT NULL DEFAULT 0,
  attempts   INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  ip         TEXT
);
CREATE INDEX IF NOT EXISTS idx_otp_email_created ON otp_codes (email, created_at);
CREATE INDEX IF NOT EXISTS idx_otp_ip_created ON otp_codes (ip, created_at);

CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id    INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at);

CREATE TABLE IF NOT EXISTS sync_data (
  user_id    INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  dataset    TEXT    NOT NULL,
  payload    TEXT    NOT NULL,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, dataset)
);

-- 每周学习周报的发送日志：同一用户同一 ISO 周（Asia/Shanghai，如 2026-W48）只发一次。
CREATE TABLE IF NOT EXISTS digest_log (
  user_id  INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  week_key TEXT    NOT NULL,
  sent_at  INTEGER NOT NULL,
  PRIMARY KEY (user_id, week_key)
);
