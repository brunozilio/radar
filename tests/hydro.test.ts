import assert from "node:assert/strict";
import test from "node:test";

import { parseSaceLevelRows, SACE_LEVEL_SENSORS } from "../lib/hydro.ts";

test("parseSaceLevelRows converte o CSV atual do SGB de centímetros para metros", () => {
  const rows = parseSaceLevelRows(`data_hora_medicao;indice
2026-08-27 08:45:00;321.00
2026-08-27 09:00:00;322,50
`);

  assert.deepEqual(rows, [
    {
      timestamp: "2026-08-27T08:45:00-03:00",
      level: 3.21,
      levelCm: 321,
    },
    {
      timestamp: "2026-08-27T09:00:00-03:00",
      level: 3.23,
      levelCm: 322.5,
    },
  ]);
});

test("as estações SACE usam o feed ativo do SGB", () => {
  for (const sensor of SACE_LEVEL_SENSORS) {
    const url = new URL(sensor.csv);
    assert.equal(url.hostname, "sace.sgb.gov.br");
    assert.match(url.pathname, /^\/api\/dados\/taquari_\d+_cota\.csv$/);
  }
});
