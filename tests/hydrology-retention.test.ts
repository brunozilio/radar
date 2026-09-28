import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { DatabaseSync, type SQLInputValue } from "node:sqlite";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";
import {
  acknowledgeHydrologySync,
  hydrologyCacheCutoff,
  hydrologySyncCommands,
  initializeHydrologySync,
  readHydrologySyncBatch,
  type HydrologyCommand,
} from "../lib/hydrology-retention.ts";

// Use the actual application schema, but never open its database or start the worker.
const databaseSource = readFileSync(new URL("../lib/database.ts", import.meta.url), "utf8");
const schema = databaseSource.match(/const SCHEMA = `([\s\S]*?)`;/)![1];
const workerSource = readFileSync(new URL("../scripts/worker.ts", import.meta.url), "utf8");
const edgeSource = readFileSync(new URL("../cloudflare/index.js", import.meta.url), "utf8");
const old = "2024-05-04T12:00:00-03:00";
const received = "2026-09-22T20:00:00Z";

function memoryDatabase() {
  const database = new DatabaseSync(":memory:");
  database.exec(schema);
  return database;
}
function seed(database: DatabaseSync, timestamp = old) {
  database.prepare("INSERT INTO river_readings VALUES ('DCRS-00091', ?, 12, 4470, 0, 'stable', 'Rede RS', ?)").run(timestamp, received);
  database.prepare("INSERT INTO sace_readings VALUES ('86510000', ?, 12, 1200, ?)").run(timestamp, received);
  database.prepare("INSERT INTO rain_readings VALUES ('86510000', ?, 0, 1200, 100, 'Dado aprovado', ?)").run(timestamp, received);
  database.prepare("INSERT INTO ceran_readings VALUES ('14-de-julho', ?, 20, 10, 100, 80, 10, 10, 100, 'normal', ?)").run(timestamp, received);
}
function apply(database: DatabaseSync, commands: HydrologyCommand[]) {
  return commands.map(({ sql, params }) => {
    database.prepare(sql).run(...params);
    return { success: true, results: [] };
  });
}
function workerFunction(name: string, endMarker: string, bindings: Record<string, unknown>) {
  const start = workerSource.indexOf(`async function ${name}(`);
  const end = workerSource.indexOf(endMarker, start);
  assert.ok(start >= 0 && end > start);
  const compiled = ts.transpileModule(workerSource.slice(start, end), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
  }).outputText;
  return vm.runInNewContext(`${compiled}\n${name}`, {
    console: { log() {}, error() {} }, nowIso: () => new Date().toISOString(), ...bindings,
  }) as (...args: unknown[]) => Promise<void>;
}

test("backlog de todas as idades e quatro fontes chega ao arquivo, com cursor persistente", () => {
  const local = memoryDatabase();
  const remote = memoryDatabase();
  try {
    seed(local);
    initializeHydrologySync(local);
    const batch = readHydrologySyncBatch(local, "d1");
    assert.equal(batch.readings.length, 4);
    assert.ok(batch.readings.every(({ reading }) => reading.timestamp === old));
    const commands = hydrologySyncCommands(batch);
    assert.ok(commands.every(({ sql }) => !/\bDELETE\b/i.test(sql)));
    acknowledgeHydrologySync(local, batch, apply(remote, commands));
    // Reopening initialization must not enqueue or send the surviving history again.
    initializeHydrologySync(local);
    assert.equal(readHydrologySyncBatch(local, "d1").readings.length, 0);
    for (const table of ["river_readings", "sace_readings", "rain_readings", "ceran_readings"]) {
      assert.equal(remote.prepare(`SELECT timestamp FROM ${table}`).get()?.timestamp, old);
      assert.equal(local.prepare(`SELECT timestamp FROM ${table}`).get()?.timestamp, old);
    }
    assert.equal(readHydrologySyncBatch(local, "dcrs").readings.length, 1);
  } finally { local.close(); remote.close(); }
});

test("lotes limitados não saltam timestamps iguais, backfill tardio nem atualização", () => {
  const database = memoryDatabase();
  try {
    initializeHydrologySync(database);
    const insert = database.prepare("INSERT INTO sace_readings VALUES (?, ?, 12, 1200, ?)");
    for (let index = 0; index < 501; index++) insert.run(`station-${index}`, old, received);
    const first = readHydrologySyncBatch(database, "d1");
    assert.equal(first.readings.length, 500);
    acknowledgeHydrologySync(database, first, first.readings.map(() => ({ success: true })));
    insert.run("late", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z");
    initializeHydrologySync(database);
    const next = readHydrologySyncBatch(database, "d1");
    assert.deepEqual(next.readings.map(({ reading }) => reading.station), ["station-500", "late"]);
    acknowledgeHydrologySync(database, next, next.readings.map(() => ({ success: true })));
    database.prepare("UPDATE sace_readings SET level = 13 WHERE station = 'late'").run();
    const revision = readHydrologySyncBatch(database, "d1");
    assert.equal(revision.readings.length, 1);
    assert.equal(revision.readings[0].reading.level, 13);
    assert.equal(revision.readings[0].reading.created_at, "2020-01-02T00:00:00Z");
  } finally { database.close(); }
});

test("falha ou resposta parcial não avança cursor; reenvio confirmado é idempotente", () => {
  const local = memoryDatabase();
  const remote = memoryDatabase();
  try {
    seed(local); initializeHydrologySync(local);
    const batch = readHydrologySyncBatch(local, "d1");
    const commands = hydrologySyncCommands(batch);
    apply(remote, commands.slice(0, 2));
    assert.throws(() => acknowledgeHydrologySync(local, batch, [{ success: true }]), /incompleta/);
    assert.throws(() => acknowledgeHydrologySync(local, batch, batch.readings.map((_, index) => ({ success: index !== 2 }))), /incompleta/);
    assert.deepEqual(readHydrologySyncBatch(local, "d1"), batch);
    acknowledgeHydrologySync(local, batch, apply(remote, commands));
    for (const table of ["river_readings", "sace_readings", "rain_readings", "ceran_readings"]) {
      assert.equal(remote.prepare(`SELECT COUNT(*) AS count FROM ${table}`).get()?.count, 1);
    }
  } finally { local.close(); remote.close(); }
});

test("limpeza e sincronização reais preservam observações antigas em SQLite e D1", async () => {
  const local = memoryDatabase();
  const remote = memoryDatabase();
  try {
    seed(local); seed(remote, "2023-09-05T12:00:00-03:00");
    initializeHydrologySync(local);
    const emitted: string[] = [];
    const recordingDatabase = { prepare(sql: string) { emitted.push(sql); return local.prepare(sql); } };
    const cleanup = workerFunction("cleanup", "async function runJob", {
      database: recordingDatabase,
      deleteStoredObject: () => assert.fail("No test fixture contains media to delete"),
    });
    await cleanup();
    const sync = workerFunction("synchronizePersistentDatabaseUnlocked", "async function synchronizePersistentDatabase()", {
      database: local, DATABASE_STORAGE_URL: "https://local.test/never-fetched",
      readHydrologySyncBatch, hydrologySyncCommands, acknowledgeHydrologySync,
      runD1Commands: async (commands: HydrologyCommand[]) => {
        emitted.push(...commands.map(({ sql }) => sql));
        return apply(remote, commands);
      },
    });
    await sync();
    assert.ok(emitted.every(sql => !/DELETE\s+FROM\s+(river_readings|sace_readings|rain_readings|ceran_readings)/i.test(sql)));
    for (const table of ["river_readings", "sace_readings", "rain_readings", "ceran_readings"]) {
      assert.equal(local.prepare(`SELECT COUNT(*) AS count FROM ${table}`).get()?.count, 1);
      assert.equal(remote.prepare(`SELECT COUNT(*) AS count FROM ${table}`).get()?.count, 2);
    }
  } finally { local.close(); remote.close(); }
});

test("GET DCRS restaura somente o cache recente sem apagar os anos anteriores", async () => {
  const database = new DatabaseSync(":memory:");
  database.exec(schema.replaceAll("river_readings", "dcrs_river_readings"));
  const statements: string[] = [];
  const insert = database.prepare("INSERT INTO dcrs_river_readings VALUES ('DCRS-00091', ?, 12, 4470, 0, 'stable', 'Rede RS', ?)");
  insert.run(old, received);
  insert.run(new Date(Date.now() - 3_600_000).toISOString(), new Date().toISOString());
  const prepare = (sql: string) => {
    statements.push(sql);
    return { bind: (...params: SQLInputValue[]) => ({
      all: async () => ({ results: database.prepare(sql).all(...params) }),
      run: async () => ({ success: true, meta: database.prepare(sql).run(...params) }),
    }) };
  };
  const code = edgeSource.slice(edgeSource.indexOf("function parsePersistentRiverReading("), edgeSource.indexOf("var MonitoramentoContainer ="));
  const handle = vm.runInNewContext(`${code}\nhandleRiverPersistenceRequest`, {
    __name() {}, hasInternalAuthorization: () => true,
    json: (value: unknown, status = 200) => Response.json(value, { status }),
  }) as (request: Request, env: unknown) => Promise<Response>;
  try {
    const response = await handle(new Request("https://local.test/api/internal/river-readings"), { PUSH_DB: { prepare } });
    const payload = await response.json();
    assert.equal(payload.readings.length, 1);
    assert.equal(database.prepare("SELECT COUNT(*) AS count FROM dcrs_river_readings").get()?.count, 2);
    assert.ok(statements.every(sql => !/\bDELETE\b/i.test(sql)));
  } finally { database.close(); }
});

test("restauração D1 não baixa anos em boot e não remove o arquivo remoto", async () => {
  const local = memoryDatabase();
  const remote = memoryDatabase();
  try {
    seed(remote); seed(remote, new Date().toISOString());
    const inserts = {
      insertRiverReading: local.prepare("INSERT OR IGNORE INTO river_readings VALUES (?, ?, ?, ?, ?, ?, ?, ?)"),
      insertSaceReading: local.prepare("INSERT OR IGNORE INTO sace_readings VALUES (?, ?, ?, ?, ?)"),
      insertRainReading: local.prepare("INSERT OR IGNORE INTO rain_readings VALUES (?, ?, ?, ?, ?, ?, ?)"),
      insertCeranReading: local.prepare("INSERT OR IGNORE INTO ceran_readings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"),
    };
    const restore = workerFunction("restorePersistentDatabase", "async function synchronizePersistentDatabaseUnlocked", {
      database: local, DATABASE_STORAGE_URL: "https://local.test/never-fetched", hydrologyCacheCutoff, ...inserts,
      runD1Batch: async (commands: HydrologyCommand[]) => commands.map(({ sql, params }) => ({
        success: true, results: remote.prepare(sql).all(...params),
      })),
    });
    await restore();
    for (const table of ["river_readings", "sace_readings", "rain_readings", "ceran_readings"]) {
      assert.equal(local.prepare(`SELECT COUNT(*) AS count FROM ${table}`).get()?.count, 1);
      assert.equal(remote.prepare(`SELECT COUNT(*) AS count FROM ${table}`).get()?.count, 2);
    }
  } finally { local.close(); remote.close(); }
});

test("DCRS confirma o lote completo e rejeita falha parcial ou truncamento", async () => {
  const code = edgeSource.slice(edgeSource.indexOf("function parsePersistentRiverReading("), edgeSource.indexOf("var MonitoramentoContainer ="));
  const handle = vm.runInNewContext(`${code}\nhandleRiverPersistenceRequest`, {
    __name() {}, hasInternalAuthorization: () => true,
    json: (value: unknown, status = 200) => Response.json(value, { status }),
  }) as (request: Request, env: unknown) => Promise<Response>;
  const reading = { station: "DCRS-00091", timestamp: old, level: 12, rawLevel: 4470, trendValue: 0, trend: "stable", source: "Rede RS", createdAt: received };
  const request = (count: number) => new Request("https://local.test/api/internal/river-readings", {
    method: "POST", body: JSON.stringify({ readings: Array.from({ length: count }, () => reading) }),
  });
  const env = (count: number) => ({ PUSH_DB: {
    prepare: () => ({ bind: () => ({}) }),
    batch: async () => Array.from({ length: count }, () => ({ success: true, meta: { changes: 0 } })),
  } });
  assert.equal((await handle(request(2), env(1))).status, 503);
  assert.equal((await handle(request(501), env(500))).status, 400);
  assert.deepEqual(await (await handle(request(2), env(2))).json(), { accepted: 2, inserted: 0 });

  const persist = workerFunction("persistRiverReadings", "async function synchronizePersistentRiverHistory", {
    HYDRO_PERSIST_URL: "https://local.test/never-fetched", PUSH_INTERNAL_SECRET: "test-only",
    AbortSignal,
    fetch: async () => Response.json({ accepted: 1 }),
  });
  await assert.rejects(persist([reading, reading]), /não confirmado integralmente/);
});

test("sincronização DCRS envia medições antigas sem reenviar após confirmação", async () => {
  const database = memoryDatabase();
  try {
    seed(database); initializeHydrologySync(database);
    const sent: Array<Array<{ timestamp: string }>> = [];
    const sync = workerFunction("synchronizePersistentRiverHistory", "async function dispatchPush", {
      database, HYDRO_PERSIST_URL: "https://local.test/never-fetched", PUSH_INTERNAL_SECRET: "test-only", AbortSignal,
      insertRiverReading: database.prepare("INSERT OR IGNORE INTO river_readings VALUES (?, ?, ?, ?, ?, ?, ?, ?)"),
      readHydrologySyncBatch, acknowledgeHydrologySync,
      fetch: async () => Response.json({ readings: [] }),
      persistRiverReadings: async (readings: Array<{ timestamp: string }>) => { sent.push(readings); },
    });
    await sync();
    await sync();
    assert.equal(sent.length, 1);
    assert.equal(sent[0][0].timestamp, old);
    assert.equal(readHydrologySyncBatch(database, "dcrs").readings.length, 0);
    assert.equal(readHydrologySyncBatch(database, "d1").readings.length, 4);
  } finally { database.close(); }
});

test("DCRS repetido não aumenta a fila; atualização explícita replica no D1 e o destino legado conserva o original", async () => {
  const local = memoryDatabase();
  const generic = memoryDatabase();
  const legacy = new DatabaseSync(":memory:");
  legacy.exec(schema.replaceAll("river_readings", "dcrs_river_readings"));
  try {
    seed(local); initializeHydrologySync(local);
    const initial = readHydrologySyncBatch(local, "d1");
    acknowledgeHydrologySync(local, initial, apply(generic, hydrologySyncCommands(initial)));
    const firstDcrs = readHydrologySyncBatch(local, "dcrs");
    acknowledgeHydrologySync(local, firstDcrs, firstDcrs.readings.map(() => ({ success: true })));
    const repeat = local.prepare("INSERT OR IGNORE INTO river_readings VALUES ('DCRS-00091', ?, 99, 4470, 0, 'stable', 'Rede RS', ?)");
    for (let index = 0; index < 1000; index++) repeat.run(old, received);
    assert.equal(readHydrologySyncBatch(local, "d1").readings.length, 0);
    assert.equal(readHydrologySyncBatch(local, "dcrs").readings.length, 0);
    assert.equal(local.prepare("SELECT level FROM river_readings").get()?.level, 12);

    const code = edgeSource.slice(edgeSource.indexOf("function parsePersistentRiverReading("), edgeSource.indexOf("var MonitoramentoContainer ="));
    const handle = vm.runInNewContext(`${code}\nhandleRiverPersistenceRequest`, {
      __name() {}, hasInternalAuthorization: () => true,
      json: (value: unknown, status = 200) => Response.json(value, { status }),
    }) as (request: Request, env: unknown) => Promise<Response>;
    const env = { PUSH_DB: {
      prepare: (sql: string) => ({ bind: (...params: SQLInputValue[]) => () => legacy.prepare(sql).run(...params) }),
      batch: async (statements: Array<() => { changes: number | bigint }>) => statements.map(run => ({ success: true, meta: run() })),
    } };
    const post = (level: number) => handle(new Request("https://local.test/api/internal/river-readings", {
      method: "POST", body: JSON.stringify({ readings: [{ station: "DCRS-00091", timestamp: old, level, rawLevel: 4470, trendValue: 0, trend: "stable", source: "Rede RS", createdAt: received }] }),
    }), env);
    assert.deepEqual(await (await post(12)).json(), { accepted: 1, inserted: 1 });
    local.prepare("UPDATE river_readings SET level = 13 WHERE station = 'DCRS-00091'").run();
    const corrected = readHydrologySyncBatch(local, "d1");
    assert.equal(corrected.readings.length, 1);
    acknowledgeHydrologySync(local, corrected, apply(generic, hydrologySyncCommands(corrected)));
    assert.equal(generic.prepare("SELECT level FROM river_readings").get()?.level, 13);
    assert.equal(readHydrologySyncBatch(local, "dcrs").readings[0].reading.level, 13);
    assert.deepEqual(await (await post(13)).json(), { accepted: 1, inserted: 0 });
    assert.equal(legacy.prepare("SELECT level FROM dcrs_river_readings").get()?.level, 12);
  } finally { local.close(); generic.close(); legacy.close(); }
});
