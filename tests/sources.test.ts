import assert from "node:assert/strict";
import test from "node:test";

import {
  EPAGRI_RADAR_BASE,
  epagriRadarTimestamp,
  parseEpagriRadarFiles,
} from "../lib/sources.ts";

test("fonte do radar de Concórdia aponta para a Defesa Civil de SC", () => {
  const source = new URL(EPAGRI_RADAR_BASE);

  assert.equal(source.hostname, "sifap.defesacivil.sc.gov.br");
  assert.equal(source.pathname, "/radarsc/rest/radar");
});

test("horário do arquivo CHP é interpretado em UTC", () => {
  assert.equal(
    epagriRadarTimestamp("2026082819180400dBZ.cappi_top.png"),
    "2026-08-28T19:18:04.000Z",
  );
  assert.equal(
    epagriRadarTimestamp("2026023119180400dBZ.cappi_top.png"),
    null,
  );
});

test("lista do radar aceita somente nomes de imagem seguros e válidos", () => {
  assert.deepEqual(
    parseEpagriRadarFiles([
      "2026082819180400dBZ.cappi_top.png",
      "2026082819180400dBZ.cappi_top.png",
      "../../segredo.png",
      "resposta.html",
      null,
    ]),
    ["2026082819180400dBZ.cappi_top.png"],
  );
  assert.deepEqual(parseEpagriRadarFiles({ files: [] }), []);
});
