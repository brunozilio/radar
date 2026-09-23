import assert from "node:assert/strict";
import test from "node:test";
import { validProjection, mucumProjection, projectionIsStale, projectionForStation, preserveStationProjections, type Projection } from "../lib/projection.ts";
import { runProjectionSchedule } from "../cloudflare/projection-schedule.js";
import { isProjectionObjectKey } from "../cloudflare/projection-storage.js";

function fixture(): Projection {
  return { schema: 1, experimental: true, intervalMinutes: 15, horizonHours: 6, generatedAt: "2026-09-21T21:05:00Z", referenceAt: "2026-09-21T21:00:00Z", observation: { timestamp: "2026-09-21T21:00:00Z", level: 12 }, models: [{ id: "radar_arvores_live_candidate", label: "Modelo de previsão", points: Array.from({ length: 6 }, (_, i) => ({ timestamp: new Date(Date.parse("2026-09-21T21:00:00Z") + (i + 1) * 3600000).toISOString(), level: 12 + i / 10 })) }] };
}

function encantadoFixture(): Projection {
  const p = fixture();
  p.station = "encantado";
  p.observation.level = 7;
  p.models[0].id = "radar_encantado_v1";
  return p;
}

function delayedFixture(firstLead = 3): Projection {
  const p = fixture();
  p.generatedAt = new Date(Date.parse(p.referenceAt) + (firstLead - 1) * 3_600_000 + 5 * 60_000).toISOString();
  p.forecastStartLeadHours = firstLead;
  p.models[0].points = p.models[0].points.slice(firstLead - 1);
  return p;
}

test("publicação de Muçum descarta previsões antigas sem alterar o histórico nem os metadados", () => {
  const mucum = { ...delayedFixture(), archiveReceiptKey: "projection/receipts/fixture.json" };
  const legacy = { ...mucum, encantado: { invalid: true }, "santa-tereza": { invalid: true }, stationErrors: { encantado: "unavailable" } };
  const before = structuredClone(legacy);
  assert.deepEqual(mucumProjection(legacy), mucum);
  assert.deepEqual(legacy, before);
  assert.equal(mucumProjection(encantadoFixture()), null);
  assert.equal(mucumProjection({ ...mucum, station: "santa-tereza" }), null);
  assert.equal(mucumProjection({ ...mucum, models: [] }), null);
  assert.equal(mucumProjection(null), null);
});

test("cada cidade exige sua própria identidade e modelo, inclusive em rodadas antigas", () => {
  const legacy = fixture();
  assert.equal(projectionForStation(legacy, "encantado"), null);
  assert.equal(validProjection(legacy, "encantado"), false);
  const encantado = encantadoFixture();
  assert.equal(validProjection(encantado, "encantado"), true);
  assert.equal(validProjection(encantado), false);
  const both = { ...legacy, encantado };
  assert.equal(validProjection(both), true);
  assert.equal(projectionForStation(both, "mucum")?.observation.level, 12);
  assert.equal(projectionForStation(both, "encantado")?.observation.level, 7);
  encantado.models[0].id = "radar_arvores_live_candidate";
  assert.equal(validProjection(both), false);
});

test("falha em Encantado preserva a emissão anterior e sinaliza atraso sem descartar Muçum", () => {
  const previous = { ...fixture(), encantado: encantadoFixture() };
  const next = fixture();
  next.observation.level = 13;
  const saved = preserveStationProjections(next, previous);
  assert.equal(saved.observation.level, 13);
  assert.deepEqual(saved.encantado, previous.encantado);
  assert.ok(saved.stationErrors?.encantado);
  assert.equal(saved.encantado?.generatedAt, previous.encantado.generatedAt);
  assert.equal(projectionForStation(saved, "encantado", "2026-09-21T22:00:00.000Z"), null);
  assert.deepEqual(projectionForStation(saved, "encantado", "2026-09-21T21:00:00.000Z"), previous.encantado);
  assert.equal(preserveStationProjections(next, null).encantado, null);
  const recovered = { ...next, encantado: encantadoFixture() };
  assert.equal(preserveStationProjections(recovered, saved).stationErrors?.encantado, undefined);
});

test("Santa Tereza tem modelo próprio e falhas são isoladas por cidade", () => {
  const santa = fixture();
  santa.station = "santa-tereza";
  santa.models[0].id = "radar_santa_tereza_v1";
  santa.observation.level = 8;
  const previous = { ...fixture(), encantado: encantadoFixture(), "santa-tereza": santa };
  assert.ok(validProjection(previous));
  assert.ok(validProjection(santa, "santa-tereza"));
  assert.equal(validProjection(santa, "encantado"), false);
  assert.equal(projectionForStation(fixture(), "santa-tereza"), null);
  const next = { ...fixture(), encantado: encantadoFixture() };
  const retained = preserveStationProjections(next, previous);
  assert.deepEqual(projectionForStation(retained, "santa-tereza"), santa);
  assert.ok(retained.stationErrors?.["santa-tereza"]);
  assert.equal(retained.stationErrors?.encantado, undefined);
  const recovered = preserveStationProjections(previous, retained);
  assert.deepEqual(recovered.stationErrors, {});
  santa.models[0].id = "radar_encantado_v1";
  assert.equal(validProjection(previous), false);
});

test("ponte R2 aceita somente os arquivos de previsão previstos, sem travessia", () => {
  for (const key of ["projection/latest.json", "projection/history.tar.gz", "projection/audit.tar.gz", "projection/rounds/2026-09-22T00:00:00.000Z.json", "projection/issues/2026-09-21T21:19:00.123456-03:00.json"]) assert.equal(isProjectionObjectKey(key), true, key);
  for (const key of ["projection/../assets/file", "projection/rounds/../../latest.json", "projection/private.json", "projection/rounds/not-a-date.json", "other/latest.json"]) assert.equal(isProjectionObjectKey(key), false, key);
});

test("sem declaração de atraso aceita somente seis alvos horários finitos e ainda futuros", () => {
  assert.ok(validProjection(fixture()));
  const short = fixture(); short.models[0].points = short.models[0].points.slice(0, 5);
  assert.equal(validProjection(short), false);
  const beyond = fixture(); beyond.models[0].points.push({ timestamp: "2026-09-22T04:00:00Z", level: 15 });
  assert.equal(validProjection(beyond), false);
  const bad = fixture(); bad.models[0].points[2].level = NaN;
  assert.equal(validProjection(bad), false);
  const disorder = fixture(); disorder.models[0].points.reverse();
  assert.equal(validProjection(disorder), false);
  const future = fixture(); future.observation.timestamp = "2026-09-21T21:15:00Z";
  assert.equal(validProjection(future), false);
});

test("atraso declarado conserva a referência e todos os alvos ainda futuros até H+6", () => {
  for (let firstLead = 1; firstLead <= 6; firstLead++) {
    const p = delayedFixture(firstLead);
    assert.ok(validProjection(p), `H+${firstLead}`);
    assert.equal(p.models[0].points.length, 7 - firstLead);
    assert.equal(p.referenceAt, "2026-09-21T21:00:00Z");
    assert.equal(p.observation.timestamp, p.referenceAt);
    assert.equal(Date.parse(p.models[0].points.at(-1)!.timestamp), Date.parse(p.referenceAt) + 6 * 3_600_000);
  }
  const undeclared = delayedFixture();
  delete undeclared.forecastStartLeadHours;
  assert.equal(validProjection(undeclared), false);
  const fullLegacy = fixture(); fullLegacy.generatedAt = "2026-09-21T22:05:00Z";
  assert.equal(validProjection(fullLegacy), false);
});

test("a primeira antecedência é exatamente a primeira hora futura na emissão", () => {
  const p = delayedFixture();
  p.generatedAt = "2026-09-21T23:00:00Z";
  assert.ok(validProjection(p));
  p.generatedAt = "2026-09-21T22:59:59.999Z";
  assert.equal(validProjection(p), false, "não pode omitir H+2 quando ainda é futuro");
  p.generatedAt = "2026-09-22T00:00:00Z";
  assert.equal(validProjection(p), false, "não pode incluir um alvo que coincide com a emissão");
  p.generatedAt = "2026-09-22T03:00:00Z";
  assert.equal(validProjection(p), false, "não publica quando todos os alvos venceram");
});

test("rejeita atraso inválido, lacunas, prefixos cortados e extensão além de H+6", () => {
  for (const forecastStartLeadHours of [0, 7, 1.5, NaN, "3", null]) {
    assert.equal(validProjection({ ...delayedFixture(), forecastStartLeadHours }), false, String(forecastStartLeadHours));
  }
  const mismatched = delayedFixture(); mismatched.forecastStartLeadHours = 4;
  assert.equal(validProjection(mismatched), false);
  const short = delayedFixture(); short.models[0].points.pop();
  assert.equal(validProjection(short), false);
  const gap = delayedFixture(); gap.models[0].points[1].timestamp = gap.models[0].points[2].timestamp;
  assert.equal(validProjection(gap), false);
  const beyond = delayedFixture(); beyond.models[0].points.push({ timestamp: "2026-09-22T04:00:00Z", level: 13 });
  assert.equal(validProjection(beyond), false);
  const bad = delayedFixture(); bad.models[0].points[0].level = Infinity;
  assert.equal(validProjection(bad), false);
});

test("cada cidade valida o próprio atraso e preserva sua emissão original", () => {
  const mucum = delayedFixture(3);
  const encantado = { ...delayedFixture(2), station: "encantado" as const };
  encantado.models[0].id = "radar_encantado_v1";
  const previous = { ...mucum, encantado };
  assert.ok(validProjection(previous));
  const retained = preserveStationProjections(delayedFixture(4), previous);
  assert.ok(validProjection(retained));
  assert.equal(retained.encantado?.forecastStartLeadHours, 2);
  assert.equal(retained.encantado?.generatedAt, encantado.generatedAt);
  assert.deepEqual(retained.encantado?.models[0].points, encantado.models[0].points);
  delete encantado.forecastStartLeadHours;
  assert.equal(validProjection(previous), false);
});

test("marca atraso sem invalidar rodadas históricas", () => {
  const p = fixture();
  assert.equal(projectionIsStale(p, Date.parse(p.generatedAt) + 15 * 60000), false);
  assert.equal(projectionIsStale(p, Date.parse(p.generatedAt) + 31 * 60000), true);
  assert.ok(validProjection(p));
});

test("cron chama apenas o endpoint interno autenticado e propaga falhas", async () => {
  const env = { MONITORAMENTO: {}, PUSH_INTERNAL_SECRET: "local-test-only" };
  await runProjectionSchedule(env, (binding: unknown, name: string) => {
    assert.equal(binding, env.MONITORAMENTO); assert.equal(name, "rio-taquari");
    return { fetch: async (request: Request) => {
      assert.equal(new URL(request.url).pathname, "/api/internal/projection-refresh");
      assert.equal(request.method, "POST");
      assert.equal(request.headers.get("authorization"), "Bearer local-test-only");
      return Response.json({ generatedAt: fixture().generatedAt });
    } };
  });
  await assert.rejects(runProjectionSchedule(env, () => ({ fetch: async () => new Response(null, { status: 503 }) })), /503/);
});
