export const INMET_MUCUM_GEOCODE = "4312609";

const INMET_ALERTS_URL = "https://avisos.inmet.gov.br";

export type InmetAlert = {
  id: string;
  title: string;
  summary: string;
  publishedAt: string;
  validUntil: string;
  severity: "yellow" | "orange" | "red";
  source: "INMET";
  sourceUrl: string;
  imageUrl: null;
};

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function cleanText(value: unknown) {
  return typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "";
}

function textItems(value: unknown) {
  if (Array.isArray(value)) {
    return value.map(cleanText).filter(Boolean);
  }
  const text = cleanText(value);
  return text ? [text] : [];
}

function hasExactGeocode(value: unknown, expected: string): boolean {
  if (Array.isArray(value)) {
    return value.some((item) => hasExactGeocode(item, expected));
  }
  if (typeof value !== "string" && typeof value !== "number") return false;

  return String(value)
    .match(/\d+/g)
    ?.some((token) => token === expected) ?? false;
}

function severityFromInmet(
  value: unknown,
): InmetAlert["severity"] | null {
  const severity = cleanText(value).toLocaleLowerCase("pt-BR");
  if (severity === "perigo potencial") return "yellow";
  if (severity === "perigo") return "orange";
  if (severity === "grande perigo") return "red";
  return null;
}

/**
 * Converts the local timestamps returned by the INMET warning feed to an ISO
 * timestamp while retaining the Brasília offset used by the source.
 */
export function normalizeInmetBrasiliaTimestamp(value: unknown) {
  if (typeof value !== "string") return null;
  const match = value
    .trim()
    .match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$/);
  if (!match) return null;

  const [, yearText, monthText, dayText, hourText, minuteText] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const lastDayOfMonth =
    month >= 1 && month <= 12
      ? new Date(Date.UTC(year, month, 0)).getUTCDate()
      : 0;

  if (
    day < 1 ||
    day > lastDayOfMonth ||
    hour < 0 ||
    hour > 23 ||
    minute < 0 ||
    minute > 59
  ) {
    return null;
  }

  return `${yearText}-${monthText}-${dayText}T${hourText}:${minuteText}:00-03:00`;
}

function parseAlert(value: unknown, municipalityGeocode: string) {
  if (!isRecord(value) || !hasExactGeocode(value.geocodes, municipalityGeocode)) {
    return null;
  }

  const rawId =
    typeof value.id === "number" || typeof value.id === "string"
      ? String(value.id).trim()
      : "";
  const title = cleanText(value.descricao);
  const publishedAt = normalizeInmetBrasiliaTimestamp(value.inicio);
  const validUntil = normalizeInmetBrasiliaTimestamp(value.fim);
  const severity = severityFromInmet(value.severidade);
  if (!rawId || !title || !publishedAt || !validUntil || !severity) return null;

  const risks = textItems(value.riscos);
  const instructions = textItems(value.instrucoes);
  const summary = risks.join(" ") || instructions.join(" ") || title;

  return {
    id: `inmet:${rawId}`,
    title,
    summary,
    publishedAt,
    validUntil,
    severity,
    source: "INMET",
    sourceUrl: `${INMET_ALERTS_URL}/${encodeURIComponent(rawId)}`,
    imageUrl: null,
  } satisfies InmetAlert;
}

/**
 * Parses both current and upcoming warnings. Time-based filtering belongs to
 * the API that serves the stored warnings, so tomorrow's warnings are kept.
 */
export function parseInmetAlerts(
  payload: unknown,
  municipalityGeocode = INMET_MUCUM_GEOCODE,
) {
  if (!isRecord(payload) || !/^\d{7}$/.test(municipalityGeocode)) return [];

  const today = Array.isArray(payload.hoje) ? payload.hoje : [];
  const future = Array.isArray(payload.futuro) ? payload.futuro : [];
  const unique = new Map<string, InmetAlert>();

  for (const candidate of [...today, ...future]) {
    const alert = parseAlert(candidate, municipalityGeocode);
    if (alert) unique.set(alert.id, alert);
  }

  return [...unique.values()].sort(
    (left, right) => Date.parse(left.publishedAt) - Date.parse(right.publishedAt),
  );
}
