export const PROJECTION_STATIONS = { mucum: "Muçum", encantado: "Encantado", "santa-tereza": "Santa Tereza" } as const;
export type ProjectionStation = keyof typeof PROJECTION_STATIONS;
export type ProjectionShadowState = {
  status: "calculated" | "unavailable";
  generatedAt: string;
  referenceAt?: string;
  archiveReceiptKey: string;
  modelVersion: "mucum-hydrometry-shadow-v1";
};

// Only operational metadata is public. A shadow result must never acquire the
// points or publication identity of the primary forecast through this channel.
export function readProjectionShadowState(value: unknown, checkedAt = new Date().toISOString()): ProjectionShadowState | null {
  if (!value || typeof value !== "object") return null;
  const shadow = value as Record<string, unknown>;
  const timestamp = (input: unknown) => typeof input === "string" && /T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(input) ? Date.parse(input) : NaN;
  const generated = timestamp(shadow.generatedAt);
  const checked = timestamp(checkedAt);
  const reference = timestamp(shadow.referenceAt);
  if (!["calculated", "unavailable"].includes(shadow.status as string) ||
      shadow.modelVersion !== "mucum-hydrometry-shadow-v1" ||
      !Number.isFinite(generated) || !Number.isFinite(checked) || generated > checked ||
      typeof shadow.archiveReceiptKey !== "string" || !/^projection\/receipts\/[A-Za-z0-9_-]{1,80}\.json$/.test(shadow.archiveReceiptKey) ||
      (shadow.status === "calculated" && shadow.referenceAt === undefined) ||
      (shadow.referenceAt !== undefined && (!Number.isFinite(reference) || reference % 3_600_000 !== 0 ||
        reference > generated || generated - reference > 3 * 3_600_000))) return null;
  return {
    status: shadow.status as ProjectionShadowState["status"], generatedAt: shadow.generatedAt as string,
    ...(shadow.referenceAt !== undefined ? { referenceAt: shadow.referenceAt as string } : {}),
    archiveReceiptKey: shadow.archiveReceiptKey, modelVersion: "mucum-hydrometry-shadow-v1",
  };
}

export type ProjectionRefreshState = {
  status: "published" | "waiting_for_data" | "already_calculated" | "failed";
  checkedAt: string;
  referenceAt?: string;
  checkedReferenceAt?: string;
  generatedAt?: string;
  missing?: string[];
  shadow?: ProjectionShadowState;
};
const EXTRA_STATIONS = ["encantado", "santa-tereza"] as const;
const MODEL_IDS = { mucum: "radar_arvores_live_candidate", encantado: "radar_encantado_v1", "santa-tereza": "radar_santa_tereza_v1" } as const;
export const HYDROMETRIC_MODEL_ID = "radar_mucum_hydrometry_v1";
export const HYDROMETRIC_MODEL_VERSION = "mucum-hydrometry-public-v1";

export type StationProjection = {
  schema: 1;
  station?: ProjectionStation;
  modelVersion?: string;
  modelSha256?: string;
  archiveReceiptKey?: string;
  generatedAt: string;
  referenceAt: string;
  experimental: true;
  intervalMinutes: 15;
  horizonHours: 6;
  // A delayed issue keeps its original reference and only publishes the
  // contiguous targets that were still future at generation time.
  forecastStartLeadHours?: number;
  observation: { timestamp: string; level: number };
  models: { id: string; label: string; points: { timestamp: string; level: number }[] }[];
};

export type Projection = StationProjection & {
  encantado?: StationProjection | null;
  "santa-tereza"?: StationProjection | null;
  stationErrors?: Partial<Record<ProjectionStation, string>>;
};

export function isHydrometricProjection(projection: StationProjection | null | undefined): boolean {
  return projection?.models?.[0]?.id === HYDROMETRIC_MODEL_ID;
}

// Retain Muçum's metadata when reading old multi-city documents, but never
// serve or republish the retired forecasts (or their stale failure flags).
export function mucumProjection(value: unknown): Projection | null {
  if (!value || typeof value !== "object") return null;
  const projection = { ...value } as Projection;
  delete projection.encantado;
  delete projection["santa-tereza"];
  delete projection.stationErrors;
  return validProjection(projection) ? projection : null;
}

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
  const firstLead = p.forecastStartLeadHours === undefined ? 1 : p.forecastStartLeadHours;
  if (!Number.isInteger(firstLead) || firstLead < 1 || firstLead > p.horizonHours ||
      firstLead !== Math.floor((generated - reference) / 3_600_000) + 1) return false;
  const hydrometric = isHydrometricProjection(p);
  if (hydrometric) {
    const explicitTimestamp = (input: unknown) => typeof input === "string" && /T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(input);
    if (station !== "mucum" || p.station !== "mucum" || p.modelVersion !== HYDROMETRIC_MODEL_VERSION ||
        typeof p.modelSha256 !== "string" || !/^[a-f0-9]{64}$/.test(p.modelSha256) ||
        typeof p.archiveReceiptKey !== "string" || !/^projection\/receipts\/[A-Za-z0-9_-]{1,80}\.json$/.test(p.archiveReceiptKey) ||
        !explicitTimestamp(p.generatedAt) || !explicitTimestamp(p.referenceAt) || !explicitTimestamp(p.observation.timestamp) ||
        reference % 3_600_000 !== 0 || generated - reference > 3 * 3_600_000 ||
        Date.parse(p.observation.timestamp) !== reference ||
        !Array.isArray(p.models[0].points) || !p.models[0].points.every(point => point && explicitTimestamp(point.timestamp))) return false;
  }
  return [hydrometric ? HYDROMETRIC_MODEL_ID : MODEL_IDS[station]].every(id => {
    const model = p.models.find(m => m?.id === id);
    return model && Array.isArray(model.points) && model.points.length === p.horizonHours - firstLead + 1 && model.points.every((point, i, points) =>
      point && Number.isFinite(point.level) && Number.isFinite(Date.parse(point.timestamp)) &&
      Date.parse(point.timestamp) > generated &&
      Date.parse(point.timestamp) === reference + (i + firstLead) * 3_600_000 &&
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

export type CurrentMucumObservation = { timestamp: string; level: number; source: string };

export function readCurrentMucumObservation(value: unknown, now = Date.now()): CurrentMucumObservation | null {
  if (!value || typeof value !== "object") return null;
  const observation = value as Record<string, unknown>;
  if (observation.code !== "86510000" || typeof observation.timestamp !== "string" ||
      !/T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(observation.timestamp) ||
      !Number.isFinite(Date.parse(observation.timestamp)) || Date.parse(observation.timestamp) > now ||
      typeof observation.level !== "number" || !Number.isFinite(observation.level) ||
      typeof observation.source !== "string" || !observation.source) return null;
  return { timestamp: observation.timestamp, level: observation.level, source: observation.source };
}

// Only flag a direct contradiction: a newer reading from the same gauge has
// already exceeded the next future point of a forecast that predicted a rise.
// Do not change any predicted level or extrapolate from the observed trend.
export function projectionContradictedByObservation(
  projection: StationProjection,
  observation: CurrentMucumObservation | null,
  now = Date.now(),
): boolean {
  if (!observation || Date.parse(observation.timestamp) <= Date.parse(projection.referenceAt)) return false;
  const points = projection.models[0]?.points ?? [];
  const nextIndex = points.findIndex(point => Date.parse(point.timestamp) > now);
  const next = points[nextIndex];
  const previousLevel = nextIndex > 0 ? points[nextIndex - 1].level : projection.observation.level;
  return Boolean(next && Date.parse(observation.timestamp) < Date.parse(next.timestamp) &&
    next.level > previousLevel && observation.level > next.level);
}
