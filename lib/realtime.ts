export type RealtimeLevelReading = {
  station: string;
  timestamp: string;
  rawLevel: number | null;
  level: number | null;
  trendValue: number | null;
  trend: "rising" | "falling" | "stable";
};

export type LevelHistoryPoint = {
  timestamp: string;
  level: number;
};

export type MetricHistoryPoint = {
  timestamp: string;
  value: number;
};

export function resolveMetricTrend(
  oneHourChange: number | null,
  realtimeTrend?: "rising" | "falling" | "stable" | null,
) {
  if (oneHourChange !== null) {
    if (oneHourChange >= 0.01) return "rising" as const;
    if (oneHourChange <= -0.01) return "falling" as const;
    return "stable" as const;
  }
  return realtimeTrend || "stable";
}

type RealtimeStation = {
  codigo?: unknown;
  timestamp?: unknown;
  data?: {
    rio?: {
      rio_nivel?: { value?: unknown };
      rio_nivel_tendencia?: { value?: unknown };
    };
  };
};

function finiteNumber(value: unknown) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function calculateOneHourMetricChange(
  current: { timestamp: string; value: number | null } | null,
  history: MetricHistoryPoint[],
  maximumDistanceMinutes = 10,
) {
  if (current?.value === null || current?.value === undefined) return null;
  const currentTime = Date.parse(current.timestamp);
  if (!Number.isFinite(currentTime)) return null;

  const targetTime = currentTime - 60 * 60 * 1000;
  let reference: MetricHistoryPoint | null = null;
  let referenceDistance = Number.POSITIVE_INFINITY;

  for (const point of history) {
    if (!Number.isFinite(point.value)) continue;
    const pointTime = Date.parse(point.timestamp);
    if (!Number.isFinite(pointTime) || pointTime > currentTime) continue;
    const distance = Math.abs(pointTime - targetTime);
    if (distance < referenceDistance) {
      reference = point;
      referenceDistance = distance;
    }
  }

  if (
    !reference ||
    referenceDistance > maximumDistanceMinutes * 60 * 1000
  ) {
    return null;
  }

  return Number((current.value - reference.value).toFixed(3));
}

export function calculateOneHourLevelChange(
  current: Pick<RealtimeLevelReading, "timestamp" | "level"> | null,
  history: LevelHistoryPoint[],
  maximumDistanceMinutes = 10,
) {
  return calculateOneHourMetricChange(
    current
      ? {
          timestamp: current.timestamp,
          value: current.level,
        }
      : null,
    history.map((point) => ({
      timestamp: point.timestamp,
      value: point.level,
    })),
    maximumDistanceMinutes,
  );
}

export function extractRealtimeLevel(
  payload: unknown,
  stationCode: string,
  datumOffset: number,
): RealtimeLevelReading | null {
  if (!payload || typeof payload !== "object") return null;
  const root = payload as {
    data?: {
      nowcasting_unique?: {
        qualle_meteorologia?: RealtimeStation | RealtimeStation[];
      };
    };
  };
  const value = root.data?.nowcasting_unique?.qualle_meteorologia;
  const stations = Array.isArray(value) ? value : value ? [value] : [];
  const station = stations.find((item) => item.codigo === stationCode);
  if (!station || typeof station.timestamp !== "string") return null;

  const rawLevel = finiteNumber(station.data?.rio?.rio_nivel?.value);
  const trendValue = finiteNumber(
    station.data?.rio?.rio_nivel_tendencia?.value,
  );
  const level =
    rawLevel === null
      ? null
      : Number((rawLevel + datumOffset).toFixed(3));

  return {
    station: stationCode,
    timestamp: station.timestamp,
    rawLevel,
    level,
    trendValue,
    trend:
      trendValue === null || Math.abs(trendValue) < 0.01
        ? "stable"
        : trendValue > 0
          ? "rising"
          : "falling",
  };
}
