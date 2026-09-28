import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";
import { readLatestDcrsReading } from "../lib/dcrs-history.ts";

test("leitura atual da Rede RS compara instantes apesar de fusos diferentes", () => {
  const database = new DatabaseSync(":memory:");
  database.exec(`
    CREATE TABLE river_readings (
      station TEXT, timestamp TEXT, level REAL, raw_level REAL,
      trend_value REAL, trend TEXT, created_at TEXT
    )
  `);
  const insert = database.prepare(`
    INSERT INTO river_readings VALUES ('DCRS-00091', ?, ?, ?, 0, 'rising', ?)
  `);
  try {
    insert.run("2026-09-28T16:15:12.000+00:00", 6.16, 38.86, "2026-09-28T16:15:20Z");
    insert.run("2026-09-28T13:22:32.000-03:00", 6.22, 38.92, "2026-09-28T16:22:40Z");
    insert.run("2026-09-28T14:00:00.000-03:00", 99, 131.7, "2026-09-28T16:23:00Z");
    assert.equal(
      readLatestDcrsReading(database, Date.parse("2026-09-28T16:30:00Z"))?.level,
      6.22,
    );
  } finally {
    database.close();
  }
});
