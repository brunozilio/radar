import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizeInmetBrasiliaTimestamp,
  parseInmetAlerts,
} from "../lib/inmet-alerts.ts";

function fixture(overrides: Record<string, unknown> = {}) {
  return {
    id: 55501,
    descricao: "Tempestade",
    severidade: "Perigo Potencial",
    inicio: "2026-08-27 00:00",
    fim: "2026-08-27 23:59",
    geocodes: "4306809,4312609,4315800",
    riscos: ["Chuva intensa e queda de granizo."],
    instrucoes: ["Evite áreas abertas."],
    ...overrides,
  };
}

test("parseInmetAlerts normaliza um aviso oficial que inclui Muçum", () => {
  const alerts = parseInmetAlerts({ hoje: [fixture()], futuro: [] });

  assert.deepEqual(alerts, [
    {
      id: "inmet:55501",
      title: "Tempestade",
      summary: "Chuva intensa e queda de granizo.",
      publishedAt: "2026-08-27T00:00:00-03:00",
      validUntil: "2026-08-27T23:59:00-03:00",
      severity: "yellow",
      source: "INMET",
      sourceUrl: "https://avisos.inmet.gov.br/55501",
      imageUrl: null,
    },
  ]);
});

test("o geocode de Muçum precisa ser um token exato", () => {
  const alerts = parseInmetAlerts({
    hoje: [
      fixture({ id: 1, geocodes: "14312609", municipios: "Muçum - RS" }),
      fixture({ id: 2, geocodes: "43126090", municipios: "Muçum - RS" }),
      fixture({ id: 3, geocodes: "4300000", municipios: "Muçum - RS" }),
    ],
    futuro: [],
  });

  assert.deepEqual(alerts, []);
});

test("mantém avisos futuros e mapeia as três severidades", () => {
  const alerts = parseInmetAlerts({
    hoje: [
      fixture({ id: "yellow", severidade: "Perigo Potencial" }),
      fixture({ id: "orange", severidade: "Perigo" }),
    ],
    futuro: [
      fixture({
        id: "red",
        severidade: "Grande Perigo",
        inicio: "2026-08-28 08:30",
        fim: "2026-08-29 12:00",
        geocodes: [4312609],
      }),
    ],
  });

  assert.deepEqual(
    alerts.map(({ id, severity, publishedAt, validUntil }) => ({
      id,
      severity,
      publishedAt,
      validUntil,
    })),
    [
      {
        id: "inmet:yellow",
        severity: "yellow",
        publishedAt: "2026-08-27T00:00:00-03:00",
        validUntil: "2026-08-27T23:59:00-03:00",
      },
      {
        id: "inmet:orange",
        severity: "orange",
        publishedAt: "2026-08-27T00:00:00-03:00",
        validUntil: "2026-08-27T23:59:00-03:00",
      },
      {
        id: "inmet:red",
        severity: "red",
        publishedAt: "2026-08-28T08:30:00-03:00",
        validUntil: "2026-08-29T12:00:00-03:00",
      },
    ],
  );
});

test("datas locais inválidas não são convertidas", () => {
  assert.equal(normalizeInmetBrasiliaTimestamp("2026-02-29 12:00"), null);
  assert.equal(normalizeInmetBrasiliaTimestamp("2026-08-27T12:00:00Z"), null);
  assert.deepEqual(
    parseInmetAlerts({
      hoje: [fixture({ inicio: "2026-13-01 00:00" })],
      futuro: [],
    }),
    [],
  );
});
