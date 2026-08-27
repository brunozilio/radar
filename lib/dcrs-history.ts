export type DcrsHistoricReading = {
  timestamp: string;
  rawLevel: number;
  level: number;
  trendValue: number | null;
  trend: "rising" | "falling" | "stable";
};

export function graphqlUtcDate(date: Date) {
  return date.toISOString().slice(0, 19).replace("T", " ");
}

export function dcrsHistoricQuery(
  stationCode: string,
  start: Date,
  end: Date,
) {
  return `query Historic {
    historic(
      system: Qualle_Hidrometeorologia
      client: "casa-militar-defesa-civil-rs"
      stationCode: "${stationCode}"
      startDate: "${graphqlUtcDate(start)}"
      endDate: "${graphqlUtcDate(end)}"
      interval: MIN_5
    )
  }`;
}

export function parseDcrsHistoric(
  payload: unknown,
  stationCode: string,
  datumOffset: number,
) {
  const items = (
    payload as {
      data?: {
        historic?: {
          items?: unknown;
        };
      };
    }
  )?.data?.historic?.items;
  if (!Array.isArray(items)) return [];

  const readings = items.flatMap((value) => {
    const item = value as {
      ts?: unknown;
      codigo?: unknown;
      rio_nivel?: unknown;
      rio_variacao?: unknown;
    };
    if (
      item.codigo !== stationCode ||
      typeof item.ts !== "string" ||
      !Number.isFinite(Date.parse(item.ts)) ||
      typeof item.rio_nivel !== "number" ||
      !Number.isFinite(item.rio_nivel)
    ) {
      return [];
    }
    const trendValue =
      typeof item.rio_variacao === "number" &&
      Number.isFinite(item.rio_variacao)
        ? item.rio_variacao
        : null;
    return [
      {
        timestamp: item.ts,
        rawLevel: item.rio_nivel,
        level: Number((item.rio_nivel + datumOffset).toFixed(2)),
        trendValue,
        trend:
          trendValue === null || Math.abs(trendValue) < 0.005
            ? "stable"
            : trendValue > 0
              ? "rising"
              : "falling",
      } satisfies DcrsHistoricReading,
    ];
  });

  return readings
    .filter(
      (reading, index, all) =>
        index ===
        all.findIndex(
          (candidate) => candidate.timestamp === reading.timestamp,
        ),
    )
    .sort(
      (left, right) =>
        Date.parse(left.timestamp) - Date.parse(right.timestamp),
    );
}
