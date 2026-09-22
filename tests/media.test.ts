import assert from "node:assert/strict";
import test from "node:test";
import { collectMediaItems, recentMediaItems } from "../lib/media-collection.ts";
import { framesFromMostRecentProvider, framesWithinLatestHour, retainAvailableFrames } from "../lib/media-window.ts";

const now = Date.parse("2026-09-21T21:00:00Z");
const frame = (time: string, provider = "inmet") => ({
  id: `${provider}:${time}`, timestamp: `2026-09-21T${time}:00Z`, provider,
});

test("prioriza imagens novas e ignora backlog antigo, datas inválidas e futuras", () => {
  assert.deepEqual(recentMediaItems([
    frame("08:10"), frame("20:30"), frame("18:00"), frame("21:00"),
    frame("21:10"), { ...frame("20:00"), timestamp: "invalid" },
  ], now).map(f => f.timestamp), [
    "2026-09-21T21:00:00Z", "2026-09-21T20:30:00Z", "2026-09-21T18:00:00Z",
  ]);
});

test("falha de download não interrompe os próximos quadros", async () => {
  const stored: number[] = [];
  const failed: number[] = [];
  const changes = await collectMediaItems([1, 2, 3, 4], async item => {
    if (item === 1 || item === 3) throw new Error("HTTP 503");
    stored.push(item);
    return 1;
  }, (_, item) => failed.push(item));
  assert.equal(changes, 2);
  assert.deepEqual(stored.sort(), [2, 4]);
  assert.deepEqual(failed.sort(), [1, 3]);
});

test("quadro lento não impede publicação dos demais; concorrência é limitada", async () => {
  let release!: () => void;
  const slow = new Promise<void>(resolve => { release = resolve; });
  let signal!: () => void;
  const published = new Promise<void>(resolve => { signal = resolve; });
  let active = 0;
  let maxActive = 0;
  const stored: number[] = [];
  const collection = collectMediaItems([1, 2, 3, 4], async item => {
    maxActive = Math.max(maxActive, ++active);
    if (item === 1) await slow;
    stored.push(item);
    active--;
    if (item === 4) signal();
    return 1;
  }, () => assert.fail(), 2);
  await published;
  assert.deepEqual(stored, [2, 3, 4]);
  assert.equal(maxActive, 2);
  release();
  assert.equal(await collection, 4);
});

test("radar permanece disponível com satélite vazio ou em horário diferente", () => {
  const radar = [frame("20:25", "radar"), frame("20:35", "radar")];
  const satellite = [frame("20:10"), frame("20:40")];
  assert.equal(retainAvailableFrames([], radar, now).length, 2);
  assert.equal(retainAvailableFrames([], [], now).length, 0);
  assert.equal(retainAvailableFrames([], satellite, now).length, 2);
});

test("resposta vazia ou atrasada preserva último lote recente; lote novo substitui", () => {
  const cached = [frame("20:10"), frame("20:40")];
  assert.deepEqual(retainAvailableFrames(cached, [], now), cached);
  assert.deepEqual(retainAvailableFrames(cached, [frame("20:30")], now), cached);
  const newer = [frame("20:50", "cptec")];
  assert.deepEqual(retainAvailableFrames(cached, newer, now), newer);
  assert.deepEqual(retainAvailableFrames(cached, [], now + 2 * 60 * 60 * 1000), []);
});

test("satélite usa provedor com imagem recente mesmo se o preferido está antigo", () => {
  const newest = frame("20:40", "cptec");
  assert.deepEqual(framesFromMostRecentProvider([frame("18:00"), newest], now, "inmet"), [newest]);
  assert.deepEqual(framesFromMostRecentProvider([frame("20:40"), newest], now, "inmet"), [frame("20:40")]);
});

test("janela ordena lote decrescente da API, elimina duplicações e limita animação a uma hora", () => {
  assert.deepEqual(framesWithinLatestHour([
    frame("20:40"), frame("20:30"), frame("20:30"), frame("19:40"), frame("19:30"),
  ], now).map(f => f.timestamp), [
    "2026-09-21T19:40:00Z", "2026-09-21T20:30:00Z", "2026-09-21T20:40:00Z",
  ]);
});

test("NOAA extrai data UTC do dia do ano e aceita somente o setor e resolução esperados", async () => {
  const { parseNoaaSatelliteFrames } = await import("../lib/sources.ts");
  const url = (stamp: string) => `https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/ssa/13/${stamp}_GOES19-ABI-ssa-13-1800x1080.jpg`;
  const valid = url("20262642130");
  const html = [valid, valid, url("20263662130"), url("20262642530"),
    url("20262642170"), url("20262642130").replace("/ssa/", "/pr/"),
    url("20262642130").replace("1800x1080", "900x540")].join("\n");
  assert.deepEqual(parseNoaaSatelliteFrames(html), [{ sourceUrl: valid, timestamp: "2026-09-21T21:30:00.000Z" }]);
  const leap = url("20243660000");
  assert.equal(parseNoaaSatelliteFrames(leap)[0].timestamp, "2024-12-31T00:00:00.000Z");
  const newest = frame("20:50", "noaa");
  assert.deepEqual(framesFromMostRecentProvider([frame("20:40"), newest], now, "inmet"), [newest]);
});
