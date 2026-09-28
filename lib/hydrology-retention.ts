import type { DatabaseSync } from "node:sqlite";

// This window bounds the startup cache only. It is not a retention policy.
export const HYDROLOGY_CACHE_HOURS = 48;
export function hydrologyCacheCutoff(now = Date.now()) {
  return new Date(now - HYDROLOGY_CACHE_HOURS * 3_600_000).toISOString();
}

const TABLE_COLUMNS = {
  river_readings: ["station", "timestamp", "level", "raw_level", "trend_value", "trend", "source", "created_at"],
  sace_readings: ["station", "timestamp", "level", "level_cm", "created_at"],
  rain_readings: ["station", "timestamp", "rain", "level_cm", "discharge", "quality", "created_at"],
  ceran_readings: ["plant_id", "timestamp", "upstream_level", "downstream_level", "inflow", "turbined", "spilled", "residual", "outflow", "status", "created_at"],
} as const;
export type HydrologyTable = keyof typeof TABLE_COLUMNS;
export type HydrologyCommand = { sql: string; params: Array<string | number | null> };
type Reading = Record<string, string | number | null>;
type PendingReading = { sequence: number; table: HydrologyTable; reading: Reading };
export type HydrologySyncBatch = {
  consumer: "d1" | "dcrs";
  throughSequence: number | null;
  readings: PendingReading[];
};

// Measurement and receipt timestamps are data, never synchronization cursors.
// A durable insertion sequence also captures backfills and equal created_at values.
// The queue stores keys, not another copy of all measured values.
export function initializeHydrologySync(database: DatabaseSync) {
  database.exec("BEGIN IMMEDIATE");
  try {
    database.exec(`
      CREATE TABLE IF NOT EXISTS hydrology_sync_queue (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        reading_key TEXT NOT NULL,
        timestamp TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS hydrology_sync_state (
        consumer TEXT PRIMARY KEY,
        sequence INTEGER NOT NULL
      );
    `);
    const initialized = database.prepare("SELECT 1 FROM hydrology_sync_state WHERE consumer = 'initialized-v1'").get();
    for (const [table, columns] of Object.entries(TABLE_COLUMNS)) {
      const key = columns[0];
      if (!initialized) {
        // First migration sends the whole surviving local backlog, regardless of age.
        database.exec(`INSERT INTO hydrology_sync_queue (table_name, reading_key, timestamp)
          SELECT '${table}', ${key}, timestamp FROM ${table}`);
      }
      for (const event of ["INSERT", "UPDATE"]) {
        database.exec(`CREATE TRIGGER IF NOT EXISTS hydrology_sync_${table}_${event.toLowerCase()}
          AFTER ${event} ON ${table} BEGIN
            INSERT INTO hydrology_sync_queue (table_name, reading_key, timestamp)
            VALUES ('${table}', NEW.${key}, NEW.timestamp);
          END;`);
      }
    }
    database.prepare("INSERT OR IGNORE INTO hydrology_sync_state VALUES ('initialized-v1', 0)").run();
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
}

export function readHydrologySyncBatch(database: DatabaseSync, consumer: "d1" | "dcrs", limit = 500): HydrologySyncBatch {
  if (!Number.isInteger(limit) || limit < 1 || limit > 500) throw new Error("Lote hidrológico deve conter de 1 a 500 registros");
  const cursor = database.prepare("SELECT sequence FROM hydrology_sync_state WHERE consumer = ?").get(consumer)?.sequence ?? 0;
  const queued = database.prepare(`SELECT sequence, table_name, reading_key, timestamp
    FROM hydrology_sync_queue WHERE sequence > ?
    ${consumer === "dcrs" ? "AND table_name = 'river_readings' AND reading_key = 'DCRS-00091'" : ""}
    ORDER BY sequence LIMIT ?`).all(cursor, limit) as Array<{
      sequence: number; table_name: HydrologyTable; reading_key: string; timestamp: string;
    }>;
  const statements = new Map<HydrologyTable, ReturnType<DatabaseSync["prepare"]>>();
  const readings = queued.map((entry) => {
    let statement = statements.get(entry.table_name);
    if (!statement) {
      const columns = TABLE_COLUMNS[entry.table_name];
      if (!columns) throw new Error("Tabela inválida na fila hidrológica");
      statement = database.prepare(`SELECT ${columns.join(", ")} FROM ${entry.table_name} WHERE ${columns[0]} = ? AND timestamp = ?`);
      statements.set(entry.table_name, statement);
    }
    const reading = statement.get(entry.reading_key, entry.timestamp) as Reading | undefined;
    if (!reading) throw new Error(`Medição ausente na fila hidrológica: ${entry.table_name}/${entry.sequence}`);
    return { sequence: entry.sequence, table: entry.table_name, reading };
  });
  return { consumer, throughSequence: queued.at(-1)?.sequence ?? null, readings };
}

export function hydrologySyncCommands(batch: HydrologySyncBatch): HydrologyCommand[] {
  return batch.readings.map(({ table, reading }) => {
    const columns = TABLE_COLUMNS[table];
    return {
      sql: `INSERT OR REPLACE INTO ${table} (${columns.join(", ")}) VALUES (${columns.map(() => "?").join(", ")})`,
      params: columns.map((column) => reading[column]),
    };
  });
}

// Call only after every remote statement was positively acknowledged. Retrying an
// interrupted batch is idempotent; an empty/partial response must not lose records.
export function acknowledgeHydrologySync(database: DatabaseSync, batch: HydrologySyncBatch, acknowledgements: Array<{ success: boolean }>) {
  if (acknowledgements.length !== batch.readings.length || acknowledgements.some((result) => !result.success)) {
    throw new Error("Sincronização hidrológica incompleta; lote preservado para nova tentativa");
  }
  if (batch.throughSequence === null) return;
  database.prepare(`INSERT INTO hydrology_sync_state (consumer, sequence) VALUES (?, ?)
    ON CONFLICT(consumer) DO UPDATE SET sequence = max(sequence, excluded.sequence)`)
    .run(batch.consumer, batch.throughSequence);
}
