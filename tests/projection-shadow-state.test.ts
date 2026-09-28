import assert from 'node:assert/strict';
import test from 'node:test';
import { readProjectionShadowState } from '../lib/projection.ts';

const checkedAt = '2026-09-23T13:04:00Z';
const valid = {
  status: 'calculated', generatedAt: '2026-09-23T10:02:00-03:00',
  referenceAt: '2026-09-23T08:00:00-03:00',
  archiveReceiptKey: 'projection/receipts/attempt-1.json',
  modelVersion: 'mucum-hydrometry-shadow-v1',
};

test('shadow expõe somente metadata, preservando seus próprios horários', () => {
  assert.deepEqual(readProjectionShadowState({ ...valid, points: [{ level: 99 }], sources: [], reason: 'private' }, checkedAt), valid);
  const unavailable = { ...valid, status: 'unavailable' };
  delete (unavailable as Partial<typeof valid>).referenceAt;
  assert.deepEqual(readProjectionShadowState(unavailable, checkedAt), unavailable);
});

test('shadow exige modelo, status, recibo e horários explícitos válidos', () => {
  for (const patch of [
    { status: 'published' }, { modelVersion: 'another-model' }, { generatedAt: 'invalid' },
    { generatedAt: '2026-09-23T10:02:00' }, { generatedAt: '2026-09-23T13:05:00Z' },
    { referenceAt: undefined }, { referenceAt: '2026-09-23T08:00:00' },
    { referenceAt: '2026-09-23T11:00:00-03:00' }, { referenceAt: '2026-09-23T08:01:00-03:00' },
    { referenceAt: '2026-09-23T07:00:00-03:00' }, { archiveReceiptKey: 'projection/receipts/../private.json' },
    { archiveReceiptKey: '' },
  ]) assert.equal(readProjectionShadowState({ ...valid, ...patch }, checkedAt), null, JSON.stringify(patch));
  assert.equal(readProjectionShadowState(valid, 'invalid'), null);
  assert.equal(readProjectionShadowState(null, checkedAt), null);
});
