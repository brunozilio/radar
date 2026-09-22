import assert from "node:assert/strict";
import test from "node:test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { collectLevelReadings, parseLevelReadings, readLevelHistory } from "../lib/river-levels.ts";
import { SACE_LEVEL_SENSORS } from "../lib/hydro.ts";

const now = Date.parse("2026-09-21T18:00:00-03:00");
const xml = (time: string, value: string) => `<DadosHidrometereologicos><DataHora>${time}</DataHora><NivelFinal>${value}</NivelFinal></DadosHidrometereologicos>`;
const sensor = { code: "86510000", csv: "https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv" };

test("Encantado coleta sua régua ANA e o ponto 2 do SACE, sem usar a régua de Muçum", async () => {
  const encantado = SACE_LEVEL_SENSORS.find(item => item.city === "Encantado");
  assert.ok(encantado);
  const values: number[] = [];
  const result = await collectLevelReadings(encantado, async url => {
    if (new URL(url).hostname === "sace.sgb.gov.br") {
      assert.equal(new URL(url).pathname, "/api/dados/taquari_2_cota.csv");
      return "2026-09-21 17:30:00;1100";
    }
    assert.equal(new URL(url).searchParams.get("codEstacao"), "86720000");
    return xml("2026-09-21 17:45:00", "1120");
  }, (_, rows) => values.push(...rows.map(row => row.level)), now);
  assert.ok(result.every(source => source.error === null));
  assert.deepEqual(values.sort((a, b) => a - b), [11, 11.2]);
});

test("ANA: centímetros, ausência de nível, zero, timestamp inválido/futuro e sentinela", () => {
  const rows = parseLevelReadings([
    xml("2026-09-21 17:45:00", "1367"),
    xml("2026-09-21 17:30:00", ""),
    xml("2026-09-21 17:15:00", "0"),
    xml("2026-09-21 17:00:00", "NaN"),
    xml("2026-09-21 16:45:00", "-9999"),
    xml("invalid", "100"),
    xml("2026-09-22 17:45:00", "100"),
    xml("2026-09-18 17:45:00", "100"),
  ].join(""), "ANA/SNIRH", now);
  assert.deepEqual(rows.map(r => [r.timestamp, r.level, r.source]), [
    ["2026-09-21T17:45:00-03:00", 13.67, "ANA/SNIRH"],
    ["2026-09-21T17:15:00-03:00", 0, "ANA/SNIRH"],
  ]);
});

test("cada fonte publica imediatamente, sem esperar pela outra", async () => {
  let resolveAna!: (value: string) => void;
  let publishedSace!: () => void;
  const published = new Promise<void>(resolve => { publishedSace = resolve; });
  const ana = new Promise<string>(resolve => { resolveAna = resolve; });
  const sources: string[] = [];
  const collection = collectLevelReadings(sensor, async (url, timeout, cacheBust) => {
    assert.equal(timeout, 9000);
    assert.equal(cacheBust, true);
    if (url === sensor.csv) return "2026-09-21 17:30:00;1345";
    assert.equal(new URL(url).searchParams.get("codEstacao"), sensor.code);
    return ana;
  }, (source) => { sources.push(source); if (source === "SACE/SGB") publishedSace(); }, now);
  await published;
  assert.deepEqual(sources, ["SACE/SGB"]);
  resolveAna(xml("2026-09-21 17:45:00", "1367"));
  assert.ok((await collection).every(r => r.error === null));
  assert.deepEqual(sources, ["SACE/SGB", "ANA/SNIRH"]);
});

for (const failed of ["ANA/SNIRH", "SACE/SGB"]) {
  test(`falha em ${failed} preserva a outra fonte`, async () => {
    const sources: string[] = [];
    const results = await collectLevelReadings(sensor, async url => {
      const source = url === sensor.csv ? "SACE/SGB" : "ANA/SNIRH";
      if (source === failed) throw new Error("timeout");
      return source === "SACE/SGB" ? "2026-09-21 17:30:00;1345" : xml("2026-09-21 17:45:00", "1367");
    }, source => { sources.push(source); }, now);
    assert.equal(sources.length, 1);
    assert.notEqual(sources[0], failed);
    assert.equal(results.find(r => r.source === failed)?.error, "timeout");
  });
}

test("resposta vazia/HTML é identificada como erro, sem publicar leituras", async () => {
  const results = await collectLevelReadings(sensor, async () => "<html>indisponível</html>", () => assert.fail(), now);
  assert.ok(results.every(r => r.error));
});

test("banco real: mais recente por estação, empate SACE, fontes distintas, falhas e histórico", async () => {
  const directory = mkdtempSync(path.join(tmpdir(), "radar-levels-test-"));
  process.env.MONITORA_DATA_DIR = directory;
  process.env.MONITORA_DB_PATH = path.join(directory, "levels.sqlite");
  const { openWriterDatabase } = await import("../lib/database.ts");
  const database = openWriterDatabase();
  try {
    const addSace = (time: string, level: number, station = sensor.code) => database.prepare(
      "INSERT OR REPLACE INTO sace_readings VALUES (?, ?, ?, ?, ?)"
    ).run(station, time, level, level * 100, "2026-09-21T22:00:00Z");
    const addAna = (time: string, level: number | null, station = sensor.code, source = "ANA/SNIRH") => database.prepare(
      "INSERT OR REPLACE INTO river_readings VALUES (?, ?, ?, ?, NULL, 'unknown', ?, ?)"
    ).run(station, time, level, level === null ? null : level * 100, source, "2026-09-21T20:00:00Z");
    addSace("2026-09-21T17:30:00-03:00", 13.45);
    addAna("2026-09-21T17:45:00-03:00", 13.67);
    assert.equal(readLevelHistory(database, sensor.code, 3, now).at(-1)?.source, "ANA/SNIRH");
    // A delayed SACE response must not regress the current reading.
    addSace("2026-09-21T17:15:00-03:00", 13.22);
    assert.equal(readLevelHistory(database, sensor.code, 3, now).at(-1)?.level, 13.67);
    // Same instant with another offset; SACE wins deterministically.
    addSace("2026-09-21T20:45:00Z", 13.66);
    let history = readLevelHistory(database, sensor.code, 3, now);
    assert.equal(history.length, 3);
    assert.equal(history.at(-1)?.source, "SACE/SGB");
    assert.equal(history.at(-1)?.level, 13.66);
    addSace("2026-09-21T18:00:00-03:00", 13.9);
    assert.equal(readLevelHistory(database, sensor.code, 3, now).at(-1)?.level, 13.9);
    addAna("2026-09-21T18:01:00-03:00", 99); // future
    addAna("invalid", 99);
    addAna("2026-09-21T17:59:00-03:00", null);
    addAna("2026-09-21T18:00:00-03:00", 99, "86472600");
    addAna("2026-09-21T17:58:00-03:00", 99, sensor.code, "Rede RS");
    addAna("2026-09-21T13:00:00-03:00", 10);
    history = readLevelHistory(database, sensor.code, 3, now);
    assert.equal(history.length, 4);
    assert.equal(history.at(-1)?.level, 13.9);
    // Empty/failed fetches do not erase the last successful reading.
    await collectLevelReadings(sensor, async () => { throw new Error("offline"); }, () => assert.fail(), now);
    assert.deepEqual(readLevelHistory(database, sensor.code, 3, now), history);
    assert.equal(readLevelHistory(database, "86472600", 3, now).at(-1)?.source, "ANA/SNIRH");
    assert.deepEqual(readLevelHistory(database, "missing", 3, now), []);
  } finally {
    database.close();
    rmSync(directory, { recursive: true, force: true });
  }
});
