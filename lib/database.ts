import { existsSync, mkdirSync } from "node:fs";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";

export const DATA_DIRECTORY =
  process.env.MONITORA_DATA_DIR ||
  path.join(/* turbopackIgnore: true */ process.cwd(), ".data");
export const MEDIA_DIRECTORY = path.join(
  /* turbopackIgnore: true */ DATA_DIRECTORY,
  "media",
);
export const ASSET_DIRECTORY = path.join(
  /* turbopackIgnore: true */ DATA_DIRECTORY,
  "assets",
);
export const DATABASE_PATH =
  process.env.MONITORA_DB_PATH ||
  path.join(
    /* turbopackIgnore: true */ DATA_DIRECTORY,
    "monitoramento.sqlite",
  );

const SCHEMA = `
  CREATE TABLE IF NOT EXISTS media_frames (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS media_frames_kind_time
    ON media_frames(kind, captured_at DESC);

  CREATE TABLE IF NOT EXISTS stored_assets (
    id TEXT PRIMARY KEY,
    owner_type TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(owner_type, owner_id)
  );
  CREATE INDEX IF NOT EXISTS stored_assets_owner
    ON stored_assets(owner_type, owner_id);

  CREATE TABLE IF NOT EXISTS river_readings (
    station TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    level REAL,
    raw_level REAL,
    trend_value REAL,
    trend TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(station, timestamp)
  );
  CREATE INDEX IF NOT EXISTS river_readings_time
    ON river_readings(station, timestamp DESC);

  CREATE TABLE IF NOT EXISTS sace_readings (
    station TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    level REAL NOT NULL,
    level_cm REAL NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(station, timestamp)
  );
  CREATE INDEX IF NOT EXISTS sace_readings_time
    ON sace_readings(station, timestamp DESC);

  CREATE TABLE IF NOT EXISTS rain_readings (
    station TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    rain REAL,
    level_cm REAL,
    discharge REAL,
    quality TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(station, timestamp)
  );
  CREATE INDEX IF NOT EXISTS rain_readings_time
    ON rain_readings(station, timestamp DESC);

  CREATE TABLE IF NOT EXISTS ceran_readings (
    plant_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    upstream_level REAL NOT NULL,
    downstream_level REAL NOT NULL,
    inflow REAL NOT NULL,
    turbined REAL NOT NULL,
    spilled REAL NOT NULL,
    residual REAL NOT NULL,
    outflow REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(plant_id, timestamp)
  );
  CREATE INDEX IF NOT EXISTS ceran_readings_time
    ON ceran_readings(plant_id, timestamp DESC);

  CREATE TABLE IF NOT EXISTS bulletins (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    published_at TEXT,
    status TEXT NOT NULL,
    href TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS bulletins_time
    ON bulletins(published_at DESC);

  CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    published_at TEXT NOT NULL,
    valid_until TEXT NOT NULL,
    severity TEXT NOT NULL,
    href TEXT NOT NULL,
    created_at TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS alerts_validity
    ON alerts(valid_until DESC);

  CREATE TABLE IF NOT EXISTS source_status (
    source TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    message TEXT
  );
`;

export function openWriterDatabase() {
  mkdirSync(/* turbopackIgnore: true */ MEDIA_DIRECTORY, {
    recursive: true,
  });
  mkdirSync(/* turbopackIgnore: true */ ASSET_DIRECTORY, {
    recursive: true,
  });
  const database = new DatabaseSync(
    /* turbopackIgnore: true */ DATABASE_PATH,
  );
  database.exec("PRAGMA journal_mode = WAL;");
  database.exec("PRAGMA synchronous = NORMAL;");
  database.exec("PRAGMA busy_timeout = 5000;");
  database.exec(SCHEMA);
  return database;
}

export function openReaderDatabase() {
  if (!existsSync(/* turbopackIgnore: true */ DATABASE_PATH)) return null;
  const database = new DatabaseSync(
    /* turbopackIgnore: true */ DATABASE_PATH,
    { readOnly: true },
  );
  database.exec("PRAGMA query_only = ON;");
  database.exec("PRAGMA busy_timeout = 5000;");
  return database;
}
