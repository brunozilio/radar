export const PROJECTION_STATIONS = { mucum: "Muçum", encantado: "Encantado", "santa-tereza": "Santa Tereza" } as const;
export type ProjectionStation = keyof typeof PROJECTION_STATIONS;
const EXTRA_STATIONS = ["encantado", "santa-tereza"] as const;
const MODEL_IDS = { mucum: "radar_arvores_live_candidate", encantado: "radar_encantado_v1", "santa-tereza": "radar_santa_tereza_v1" } as const;

export type StationProjection = {
  schema: 1;
  station?: ProjectionStation;
  generatedAt: string;
  referenceAt: string;
  experimental: true;
  intervalMinutes: 15;
  horizonHours: 6;
  observation: { timestamp: string; level: number };
  models: { id: string; label: string; points: { timestamp: string; level: number }[] }[];
};

export type Projection = StationProjection & {
  encantado?: StationProjection | null;
  "santa-tereza"?: StationProjection | null;
  stationErrors?: Partial<Record<ProjectionStation, string>>;
};

export function validProjection(value: unknown, station: ProjectionStation = "mucum"): value is Projection {
  if (!value || typeof value !== "object") return false;
  const p = value as Projection;
  // Legacy documents belong only to Muçum. Never relabel another gauge's model.
  if (station !== "mucum" ? p.station !== station : p.station !== undefined && p.station !== station) return false;
  if (station === "mucum" && EXTRA_STATIONS.some(city => p[city] != null && !validProjection(p[city], city))) return false;
  const generated = Date.parse(p.generatedAt);
  const reference = Date.parse(p.referenceAt);
  if (p.schema !== 1 || p.experimental !== true || p.intervalMinutes !== 15 || p.horizonHours !== 6 ||
      !Number.isFinite(generated) || !Number.isFinite(reference) || reference > generated ||
      !p.observation || !Number.isFinite(p.observation.level) ||
      !Number.isFinite(Date.parse(p.observation.timestamp)) ||
      Date.parse(p.observation.timestamp) > reference ||
      !Array.isArray(p.models) || p.models.length !== 1) return false;
  return [MODEL_IDS[station]].every(id => {
    const model = p.models.find(m => m?.id === id);
    return model && Array.isArray(model.points) && model.points.length === 6 && model.points.every((point, i, points) =>
      point && Number.isFinite(point.level) && Number.isFinite(Date.parse(point.timestamp)) &&
      Date.parse(point.timestamp) > generated &&
      Date.parse(point.timestamp) === reference + (i + 1) * 3_600_000 &&
      (i === 0 || Date.parse(point.timestamp) > Date.parse(points[i - 1].timestamp)));
  });
}

export function projectionForStation(projection: Projection | null, station: ProjectionStation, round?: string): StationProjection | null {
  const selected = station === "mucum" ? projection : projection?.[station] ?? null;
  // A retained station issue belongs to its original round, even when
  // Muçum has advanced. Do not invent a successful city round on failure.
  if (round && selected && Date.parse(selected.referenceAt) !== Date.parse(round)) return null;
  return selected;
}

export function preserveStationProjections(next: Projection, previous: Projection | null): Projection {
  const result: Projection = { ...next, stationErrors: {} };
  for (const station of EXTRA_STATIONS) {
    if (!next[station]) {
      result[station] = previous?.[station] ?? null;
      result.stationErrors![station] = `Previsão de ${PROJECTION_STATIONS[station]} temporariamente indisponível.`;
    }
  }
  return result;
}

export function projectionIsStale(projection: StationProjection, now = Date.now()) {
  return now - Date.parse(projection.generatedAt) > 30 * 60_000 ||
    now - Date.parse(projection.observation.timestamp) > 150 * 60_000;
}
