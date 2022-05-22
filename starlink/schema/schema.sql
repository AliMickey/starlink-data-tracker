DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS firmware;
DROP TABLE IF EXISTS speedtests;
DROP TABLE IF EXISTS speedtest_stats;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE firmware (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_added TEXT NOT NULL,
  type TEXT NOT NULL,
  version_info TEXT NOT NULL,
  reddit_thread TEXT
);

CREATE TABLE speedtests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date_added TEXT NOT NULL,
  date_run TEXT NOT NULL,
  url TEXT NOT NULL,
  country TEXT,
  server TEXT,
  latency DECIMAL,
  download DECIMAL,
  upload DECIMAL
);

CREATE TABLE speedtest_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  period TEXT NOT NULL,
  count INTEGER,
  latency_avg DECIMAL,
  latency_max DECIMAL,
  latency_min DECIMAL,
  download_avg DECIMAL,
  download_max DECIMAL,
  download_min DECIMAL,
  upload_avg DECIMAL,
  upload_max DECIMAL,
  upload_min DECIMAL
);

-- Initial setup
INSERT INTO speedtest_stats (period)
VALUES ('day'), ('week'), ('month'), ('year'), ('all');