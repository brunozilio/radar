const ONE_HOUR_MS = 60 * 60 * 1000;
const MAX_SOURCE_DELAY_MS = 90 * 60 * 1000;

export function framesWithinLatestHour<T extends { timestamp: string }>(
  frames: T[],
  now = Date.now(),
) {
  const valid = frames
    .filter((frame) => {
      const timestamp = Date.parse(frame.timestamp);
      return Number.isFinite(timestamp) && timestamp <= now;
    })
    .sort(
      (left, right) =>
        Date.parse(left.timestamp) - Date.parse(right.timestamp),
    );
  const uniqueByTimestamp = new Map<number, T>();
  for (const frame of valid) {
    uniqueByTimestamp.set(Date.parse(frame.timestamp), frame);
  }
  const unique = [...uniqueByTimestamp.values()];
  const newestTimestamp = Date.parse(unique.at(-1)?.timestamp || "");
  if (
    !Number.isFinite(newestTimestamp) ||
    now - newestTimestamp > MAX_SOURCE_DELAY_MS
  ) {
    return [];
  }
  const cutoff = newestTimestamp - ONE_HOUR_MS;
  return unique.filter((frame) => Date.parse(frame.timestamp) >= cutoff);
}

export function framesFromMostRecentProvider<
  T extends { timestamp: string; provider: string },
>(frames: T[], now = Date.now(), preferredProvider = "") {
  const framesByProvider = new Map<string, T[]>();
  for (const frame of frames) {
    const providerFrames = framesByProvider.get(frame.provider) || [];
    providerFrames.push(frame);
    framesByProvider.set(frame.provider, providerFrames);
  }

  return [...framesByProvider.entries()]
    .map(([provider, providerFrames]) => ({
      provider,
      frames: framesWithinLatestHour(providerFrames, now),
    }))
    .filter(({ frames: providerFrames }) => providerFrames.length > 0)
    .sort((left, right) => {
      const leftLatest = Date.parse(left.frames.at(-1)?.timestamp || "");
      const rightLatest = Date.parse(right.frames.at(-1)?.timestamp || "");
      if (rightLatest !== leftLatest) return rightLatest - leftLatest;
      if (left.provider === preferredProvider) return -1;
      if (right.provider === preferredProvider) return 1;
      return left.provider.localeCompare(right.provider);
    })[0]?.frames || [];
}

export function synchronizeFramesByTimestamp<
  R extends { timestamp: string },
  S extends { timestamp: string },
>(radarFrames: R[], satelliteFrames: S[]) {
  const satelliteByTimestamp = new Map(
    satelliteFrames.map((frame) => [Date.parse(frame.timestamp), frame]),
  );

  return radarFrames.flatMap((radar) => {
    const timestamp = Date.parse(radar.timestamp);
    const satellite = satelliteByTimestamp.get(timestamp);
    return satellite
      ? [{ timestamp: radar.timestamp, radar, satellite }]
      : [];
  });
}
