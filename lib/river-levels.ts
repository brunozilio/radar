import type { DatabaseSync } from "node:sqlite";
import { parseAnaRecords, parseSaceLevelRows, saoPauloDate } from "./hydro.ts";

export const ANA_LEVEL_ENDPOINT =
  "https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais";
export type LevelSource = "ANA/SNIRH" | "SACE/SGB";
export type LevelReading = {
  timestamp: string;
  level: number;
  levelCm: number;
  source: LevelSource;
};

export function parseLevelReadings(text: string, source: LevelSource, now = Date.now()): LevelReading[] {
  const rows = source === "SACE/SGB"
    ? parseSaceLevelRows(text)
    : parseAnaRecords(text).flatMap((row) => row.levelCm === null ? [] : [{
        timestamp: row.timestamp,
        levelCm: row.levelCm,
        level: Number((row.levelCm / 100).toFixed(2)),
      }]);
  return rows.filter((row) => {
    const time = Date.parse(row.timestamp);
    return Number.isFinite(row.levelCm) && row.levelCm > -9999 &&
      Number.isFinite(time) && time <= now && time >= now - 48 * 3_600_000;
  }).map((row) => ({ ...row, source }));
}

// Deliver each source as soon as it completes; a slow or unavailable provider
// must not hold back the other provider's new readings.
export async function collectLevelReadings(
  sensor: { code: string; csv: string },
  fetchText: (url: string, timeout: number, cacheBust: boolean) => Promise<string>,
  onReadings: (source: LevelSource, readings: LevelReading[]) => void,
  now = Date.now(),
) {
  const params = new URLSearchParams({
    codEstacao: sensor.code,
    dataInicio: saoPauloDate(new Date(now - 48 * 3_600_000)),
    dataFim: saoPauloDate(new Date(now)),
  });
  const sources: Array<{ source: LevelSource; url: string }> = [
    { source: "SACE/SGB", url: sensor.csv },
    { source: "ANA/SNIRH", url: `${ANA_LEVEL_ENDPOINT}?${params}` },
  ];
  return Promise.all(sources.map(async ({ source, url }) => {
    try {
      const rows = parseLevelReadings(await fetchText(url, 9_000, true), source, now);
      if (!rows.length) throw new Error("Nenhuma medição de nível válida nas últimas 48 horas");
      onReadings(source, rows);
      return { source, error: null };
    } catch (error) {
      return { source, error: error instanceof Error ? error.message : String(error) };
    }
  }));
}

// ANA and SACE retain independent histories in the existing persisted tables.
// Compare the measurement instant, never created_at or the request finish time.
// SACE wins ties consistently, keeping one point per instant in the chart.
export function readLevelHistory(database: DatabaseSync, station: string, hours: number, now = Date.now()) {
  return database.prepare(`
    WITH readings AS (
      SELECT timestamp, level, level_cm AS levelCm, 'SACE/SGB' AS source, 0 AS priority
      FROM sace_readings WHERE station = ?
      UNION ALL
      SELECT timestamp, level, raw_level AS levelCm, 'ANA/SNIRH' AS source, 1 AS priority
      FROM river_readings WHERE station = ? AND source = 'ANA/SNIRH'
    ), valid AS (
      SELECT *, julianday(timestamp) AS instant FROM readings
      WHERE level IS NOT NULL AND abs(level) < 1e308 AND levelCm > -9999
        AND julianday(timestamp) <= julianday(?)
    ), ranked AS (
      SELECT *, ROW_NUMBER() OVER (PARTITION BY instant ORDER BY priority) AS rank
      FROM valid
      WHERE instant >= (SELECT MAX(instant) - (? / 24.0) FROM valid)
    )
    SELECT timestamp, level, levelCm, source FROM ranked WHERE rank = 1 ORDER BY instant ASC
  `).all(station, station, new Date(now).toISOString(), hours) as LevelReading[];
}
