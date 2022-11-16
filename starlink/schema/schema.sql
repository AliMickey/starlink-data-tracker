DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS users_password_reset;
DROP TABLE IF EXISTS users_api_keys;
DROP TABLE IF EXISTS firmware;
DROP TABLE IF EXISTS speedtests;
DROP TABLE IF EXISTS network;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE,
  password TEXT NOT NULL,
  totp TEXT,
  role TEXT,
  time_zone TEXT,
  activated BOOLEAN,
  discord_id TEXT
);

CREATE TABLE users_password_reset (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reset_key TEXT UNIQUE NOT NULL,
  date_time TEXT NOT NULL,
  activated BOOLEAN NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE users_api_keys (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT UNIQUE NOT NULL,
  date_time TEXT NOT NULL,
  source TEXT NOT NULL,
  name TEXT NOT NULL,
  use_counter INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
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
  upload DECIMAL,
  source TEXT,
  distance INTEGER,
  user_id INTEGER,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE network (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT NOT NULL,
  protocol_type TEXT NOT NULL,
  date_seen TEXT,
  country TEXT
);