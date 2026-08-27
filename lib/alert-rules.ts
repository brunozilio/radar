import {
  MUCUM_UPSTREAM_RAIN_STATIONS,
  SACE_LEVEL_SENSORS,
} from "./hydro.ts";
import { CERAN_PLANT_SOURCES } from "./sources.ts";

export const ALERT_RULE_KINDS = [
  "river_level",
  "ceran_outflow",
  "rain_accumulation",
] as const;
export type AlertRuleKind = (typeof ALERT_RULE_KINDS)[number];

export const ALERT_RULE_SEVERITIES = [
  "attention",
  "alert",
  "emergency",
] as const;
export type AlertRuleSeverity = (typeof ALERT_RULE_SEVERITIES)[number];

export const ALERT_RAIN_WINDOWS = [1, 3, 6, 8, 12, 24, 48] as const;
export type AlertRainWindow = (typeof ALERT_RAIN_WINDOWS)[number];

export type AlertRule = {
  id: string;
  kind: AlertRuleKind;
  sourceId: string;
  threshold: number;
  windowHours: AlertRainWindow | null;
  severity: AlertRuleSeverity;
  enabled: boolean;
};

export type AlertRuleSource = {
  kind: AlertRuleKind;
  id: string;
  name: string;
  location: string;
  unit: "m" | "m³/s" | "mm";
};

export const ALERT_RULE_SOURCES: AlertRuleSource[] = [
  {
    kind: "river_level",
    id: "DCRS-00091",
    name: "Sensor na Barra do Guaporé",
    location: "Muçum",
    unit: "m",
  },
  ...SACE_LEVEL_SENSORS.map((sensor) => ({
    kind: "river_level" as const,
    id: sensor.code,
    name: sensor.name,
    location: sensor.city,
    unit: "m" as const,
  })),
  ...Object.values(CERAN_PLANT_SOURCES).map((plant) => ({
    kind: "ceran_outflow" as const,
    id: plant.id,
    name: plant.name,
    location:
      plant.id === "castro"
        ? "Nova Pádua"
        : plant.id === "monte"
          ? "Veranópolis"
          : "Cotiporã",
    unit: "m³/s" as const,
  })),
  ...MUCUM_UPSTREAM_RAIN_STATIONS.map((station) => ({
    kind: "rain_accumulation" as const,
    id: station.code,
    name: station.name,
    location: station.city,
    unit: "mm" as const,
  })),
];

export function findAlertRuleSource(
  kind: AlertRuleKind,
  sourceId: string,
) {
  return ALERT_RULE_SOURCES.find(
    (source) => source.kind === kind && source.id === sourceId,
  );
}

export function normalizeAlertRule(value: unknown): AlertRule | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Partial<AlertRule>;
  if (
    typeof candidate.id !== "string" ||
    !/^[A-Za-z0-9_-]{8,80}$/.test(candidate.id) ||
    !ALERT_RULE_KINDS.includes(candidate.kind as AlertRuleKind) ||
    typeof candidate.sourceId !== "string" ||
    !findAlertRuleSource(candidate.kind as AlertRuleKind, candidate.sourceId) ||
    typeof candidate.threshold !== "number" ||
    !Number.isFinite(candidate.threshold) ||
    candidate.threshold <= 0 ||
    candidate.threshold > 100_000 ||
    !ALERT_RULE_SEVERITIES.includes(
      candidate.severity as AlertRuleSeverity,
    ) ||
    typeof candidate.enabled !== "boolean"
  ) {
    return null;
  }
  const kind = candidate.kind as AlertRuleKind;
  const windowHours =
    kind === "rain_accumulation"
      ? candidate.windowHours
      : null;
  if (
    kind === "rain_accumulation" &&
    !ALERT_RAIN_WINDOWS.includes(windowHours as AlertRainWindow)
  ) {
    return null;
  }
  return {
    id: candidate.id,
    kind,
    sourceId: candidate.sourceId,
    threshold: Math.round(candidate.threshold * 100) / 100,
    windowHours: windowHours as AlertRainWindow | null,
    severity: candidate.severity as AlertRuleSeverity,
    enabled: candidate.enabled,
  };
}

export function alertRuleDecision(
  value: number,
  threshold: number,
  isActive: boolean,
) {
  if (!Number.isFinite(value) || !Number.isFinite(threshold)) return "ignore";
  if (value < threshold) return isActive ? "reset" : "ignore";
  return isActive ? "ignore" : "trigger";
}
