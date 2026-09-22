// A failed image must not abort the remaining frames or delay publication of
// frames that already succeeded. Bound concurrency to avoid flooding providers.
export async function collectMediaItems<T>(
  items: T[],
  collect: (item: T) => Promise<number>,
  onError: (error: unknown, item: T) => void,
  concurrency = 3,
) {
  let position = 0;
  let changes = 0;
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, async () => {
    while (position < items.length) {
      const item = items[position++];
      try {
        const inserted = await collect(item);
        changes += inserted;
      } catch (error) {
        onError(error, item);
      }
    }
  }));
  return changes;
}

export function recentMediaItems<T extends { timestamp: string }>(items: T[], now = Date.now()) {
  return items.filter(({ timestamp }) => {
    const time = Date.parse(timestamp);
    return Number.isFinite(time) && time <= now && time >= now - 3 * 60 * 60 * 1000;
  }).sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
}
