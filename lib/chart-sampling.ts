export function sampleLatestPointPerInterval<
  T extends { timestamp: string },
>(points: T[], intervalMinutes: number) {
  const intervalMs = intervalMinutes * 60 * 1000;
  const sampled = new Map<number, T>();

  for (const point of [...points].sort(
    (left, right) =>
      Date.parse(left.timestamp) - Date.parse(right.timestamp),
  )) {
    const timestamp = Date.parse(point.timestamp);
    if (!Number.isFinite(timestamp)) continue;
    const interval = Math.floor(timestamp / intervalMs);
    sampled.set(interval, point);
  }

  return [...sampled.values()];
}

export function latestContinuousSegment<T extends { timestamp: string }>(
  points: T[],
  maximumGapMinutes: number,
) {
  const maximumGapMs = maximumGapMinutes * 60 * 1000;
  const ordered = [...points]
    .filter((point) => Number.isFinite(Date.parse(point.timestamp)))
    .sort(
      (left, right) =>
        Date.parse(left.timestamp) - Date.parse(right.timestamp),
    );
  let segmentStart = 0;

  for (let index = 1; index < ordered.length; index += 1) {
    const gap =
      Date.parse(ordered[index].timestamp) -
      Date.parse(ordered[index - 1].timestamp);
    if (gap > maximumGapMs) segmentStart = index;
  }

  return ordered.slice(segmentStart);
}
