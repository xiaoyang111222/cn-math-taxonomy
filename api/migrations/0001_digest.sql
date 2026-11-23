-- 每周学习周报：给已上线的库补列和表。只跑一次：
--   wrangler d1 execute math-pansgo --remote --file=api/migrations/0001_digest.sql
-- 新建的库直接跑 api/schema.sql 即可（已含这些列），不需要再跑这个文件。
ALTER TABLE users ADD COLUMN digest_opt_out INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN digest_token TEXT;

CREATE TABLE IF NOT EXISTS digest_log (
  user_id  INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  week_key TEXT    NOT NULL,
  sent_at  INTEGER NOT NULL,
  PRIMARY KEY (user_id, week_key)
);
