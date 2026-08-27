const SINGLE_POINT_PADDING_MS = 30 * 60 * 1000;

export function timeSeriesBounds(timestamps: number[]) {
  const valid = timestamps.filter(Number.isFinite).sort((a, b) => a - b);
  if (!valid.length) return null;

  const min = valid[0];
  const max = valid[valid.length - 1];
  if (min !== max) return { min, max };

  return {
    min: min - SINGLE_POINT_PADDING_MS,
    max: max + SINGLE_POINT_PADDING_MS,
  };
}
