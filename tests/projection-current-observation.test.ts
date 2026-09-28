import assert from 'node:assert/strict';
import test from 'node:test';
import {
  HYDROMETRIC_MODEL_ID, HYDROMETRIC_MODEL_VERSION,
  projectionContradictedByObservation, readCurrentMucumObservation,
  type StationProjection,
} from '../lib/projection.ts';

const hour = (value: number) => `2026-09-28T${String(value).padStart(2, '0')}:00:00Z`;

function projection(levels = [6.5, 7.2, 7.8]): StationProjection {
  return {
    schema: 1, station: 'mucum', experimental: true, intervalMinutes: 15, horizonHours: 6,
    modelVersion: HYDROMETRIC_MODEL_VERSION, modelSha256: 'a'.repeat(64),
    archiveReceiptKey: 'projection/receipts/fixture.json', generatedAt: hour(18),
    referenceAt: hour(17), forecastStartLeadHours: 2,
    observation: { timestamp: hour(17), level: 5.5 },
    models: [{ id: HYDROMETRIC_MODEL_ID, label: 'Modelo hidrométrico',
      points: [19, 20, 21].map((target, index) => ({ timestamp: hour(target), level: levels[index] })) }],
  };
}

test('aceita só leitura datada da régua ANA de Muçum para confronto com previsão', () => {
  const reading = { code: '86510000', timestamp: '2026-09-28T15:00:00-03:00', level: 6.24, source: 'ANA/SNIRH' };
  assert.deepEqual(readCurrentMucumObservation(reading, Date.parse(hour(18)) + 1),
    { timestamp: reading.timestamp, level: 6.24, source: 'ANA/SNIRH' });
  assert.equal(readCurrentMucumObservation({ ...reading, code: 'DCRS-00091' }, Date.parse(hour(18)) + 1), null);
  assert.equal(readCurrentMucumObservation({ ...reading, timestamp: '2026-09-28T15:00:00' }, Date.parse(hour(18)) + 1), null);
  assert.equal(readCurrentMucumObservation({ ...reading, timestamp: hour(20) }, Date.parse(hour(18)) + 1), null);
});

test('suspende só a curva em alta já ultrapassada por leitura posterior do mesmo posto', () => {
  const now = Date.parse(hour(18)) + 30 * 60_000;
  const reading = { timestamp: hour(18), level: 6.7, source: 'ANA/SNIRH' };
  assert.equal(projectionContradictedByObservation(projection(), reading, now), true);
  assert.equal(projectionContradictedByObservation(projection(), { ...reading, level: 6.24 }, now), false);
  assert.equal(projectionContradictedByObservation(projection(), { ...reading, timestamp: hour(17) }, now), false);
  assert.equal(projectionContradictedByObservation(projection([5.4, 5.1, 4.8]), reading, now), false,
    'uma previsão de queda pode estar corretamente abaixo do nível atual');
  assert.equal(projectionContradictedByObservation(projection(), reading, Date.parse(hour(21)) + 1), false,
    'sem ponto futuro, a curva expirada é tratada separadamente');
});
