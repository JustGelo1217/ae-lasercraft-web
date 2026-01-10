-- =========================
-- MATERIAL GUIDE TABLES
-- =========================

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    thickness TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS material_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL,
    process TEXT NOT NULL,      -- 'engrave' or 'cut'
    intensity TEXT,             -- 'light', 'medium', 'dark' (NULL for cut)
    power INTEGER NOT NULL,
    speed INTEGER,
    passes INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE TABLE IF NOT EXISTS user_settings (
  user_id INTEGER PRIMARY KEY,
  settings TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;

