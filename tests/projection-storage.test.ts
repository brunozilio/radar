import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";

test("rodadas mantêm seus valores históricos e rejeitam caminhos arbitrários", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "projection-storage-"));
  process.env.MONITORA_DATA_DIR = directory;
  delete process.env.OBJECT_STORAGE_URL;
  try {
    const { readProjection, listProjectionRounds, refreshProjection } = await import("../lib/projection-server.ts");
    assert.equal(await readProjection(), null);
    const rounds = path.join(directory, "projection/rounds");
    await mkdir(rounds, { recursive: true });
    for (const hour of [19, 20]) {
      const referenceAt = `2026-09-21T${hour}:00:00.000Z`;
      const projection = { schema: 1, experimental: true, intervalMinutes: 15, horizonHours: 6, referenceAt, generatedAt: `2026-09-21T${hour}:05:00Z`, observation: { timestamp: referenceAt, level: hour }, models: [{ id: "radar_arvores_live_candidate", label: "Modelo de previsão", points: Array.from({ length: 6 }, (_, i) => ({ timestamp: new Date(Date.parse(referenceAt) + (i + 1) * 3600000).toISOString(), level: hour + i })) }] };
      await writeFile(path.join(rounds, `${referenceAt}.json`), JSON.stringify(projection));
    }
    assert.deepEqual(await listProjectionRounds(), ["2026-09-21T20:00:00.000Z", "2026-09-21T19:00:00.000Z"]);
    assert.equal((await readProjection("2026-09-21T19:00:00.000Z"))?.observation.level, 19);
    assert.equal((await readProjection("2026-09-21T20:00:00.000Z"))?.observation.level, 20);
    await assert.rejects(readProjection("../../arbitrary"), /Invalid round/);
    const saved = await readProjection("2026-09-21T20:00:00.000Z");
    await writeFile(path.join(directory, "projection/latest.json"), JSON.stringify(saved));
    process.env.PROJECTION_PYTHON = "/definitely-not-an-installed-python";
    await assert.rejects(refreshProjection(), /ENOENT/);
    assert.deepEqual(await readProjection(), saved);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
