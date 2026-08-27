"use client";

import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BellRing,
  Database,
  Download,
  Eye,
  ExternalLink,
  FileText,
  Maximize2,
  Plus,
  Settings2,
  Trash2,
  Waves,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Chart as ChartInstance } from "chart.js";
import { timeSeriesBounds } from "@/lib/charts";
import type { LayerGroup, Map as LeafletMap } from "leaflet";
import {
  latestContinuousSegment,
  sampleLatestPointPerInterval,
} from "@/lib/chart-sampling";
import {
  framesWithinLatestHour,
  synchronizeFramesByTimestamp,
} from "@/lib/media-window";
import {
  calculateOneHourMetricChange,
  resolveMetricTrend,
} from "@/lib/realtime";
import { formatDate } from "@/lib/time";
import {
  ALERT_RULE_SOURCES,
  type AlertRule,
  type AlertRuleKind,
  type AlertRuleSource,
  type AlertRuleSeverity,
} from "@/lib/alert-rules";

const WINDOWS = [1, 3, 6, 8, 12, 24, 48] as const;
type WindowHours = (typeof WINDOWS)[number];
const RIVER_WINDOWS: readonly WindowHours[] = [3, 6, 8, 12];
const MUCUM_CONTINGENCY_PLAN_URL =
  "https://mucum.rs.gov.br/portal/defesa-civil/PLANO%20DE%20CONTING%C3%8ANCIA%20DE%20MU%C3%87UM%20-%20DEFESA%20CIVIL.pdf";
type LiveTopic =
  | "radar"
  | "radar-sc"
  | "satellite"
  | "bulletins"
  | "alerts"
  | "river-history"
  | "sace"
  | "ceran"
  | "rain";
type PushUiState =
  | "checking"
  | "unsupported"
  | "unsubscribed"
  | "subscribed"
  | "blocked"
  | "working"
  | "error";
type PushPreferences = {
  rules: AlertRule[];
  sources: AlertRuleSource[];
};
type PushPreferencesState =
  | "idle"
  | "loading"
  | "saving"
  | "saved"
  | "error";
type InstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};
const CERAN_PLANTS = [
  { id: "castro", name: "UHE Castro Alves", city: "Nova Pádua" },
  { id: "monte", name: "UHE Monte Claro", city: "Veranópolis" },
  { id: "julho", name: "UHE 14 de Julho", city: "Cotiporã" },
] as const;
type PlantId = (typeof CERAN_PLANTS)[number]["id"];
const ALERT_KIND_LABEL: Record<AlertRuleKind, string> = {
  river_level: "Nível do rio",
  ceran_outflow: "Vazão de hidrelétrica",
  rain_accumulation: "Chuva acumulada",
};
const ALERT_SEVERITY_OPTION: Array<{
  value: AlertRuleSeverity;
  label: string;
}> = [
  { value: "attention", label: "Atenção — notificação silenciosa" },
  { value: "alert", label: "Alerta — notificação prioritária" },
  { value: "emergency", label: "Emergência — sirene e vibração" },
];

function vapidKeyToUint8Array(value: string) {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  const decoded = window.atob(base64);
  const bytes = new Uint8Array(decoded.length);
  for (let index = 0; index < decoded.length; index += 1) {
    bytes[index] = decoded.charCodeAt(index);
  }
  return bytes;
}

const SILENT_AUDIO_RESET_SECONDS = 18;
const EMERGENCY_AUDIO_START_SECONDS = 24;
const EMERGENCY_AUDIO_DURATION_SECONDS = 10;

function createAlertAudioTrackUrl() {
  const sampleRate = 22_050;
  const durationSeconds =
    EMERGENCY_AUDIO_START_SECONDS + EMERGENCY_AUDIO_DURATION_SECONDS;
  const bytesPerSample = 2;
  const sampleCount = sampleRate * durationSeconds;
  const dataSize = sampleCount * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  const writeAscii = (offset: number, value: string) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeAscii(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeAscii(8, "WAVE");
  writeAscii(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true);
  view.setUint16(32, bytesPerSample, true);
  view.setUint16(34, 16, true);
  writeAscii(36, "data");
  view.setUint32(40, dataSize, true);

  let phase = 0;
  for (let index = 0; index < sampleCount; index += 1) {
    const time = index / sampleRate;
    if (time < EMERGENCY_AUDIO_START_SECONDS) {
      // Mantém uma faixa real aberta sem produzir som perceptível.
      view.setInt16(44 + index * bytesPerSample, index % 2 ? 1 : -1, true);
      continue;
    }

    const alarmTime = time - EMERGENCY_AUDIO_START_SECONDS;
    const cyclePosition = (alarmTime % 1.6) / 1.6;
    const triangle =
      cyclePosition < 0.5 ? cyclePosition * 2 : (1 - cyclePosition) * 2;
    const smoothSweep = triangle * triangle * (3 - 2 * triangle);
    const frequency = 680 + 820 * smoothSweep;
    phase += (2 * Math.PI * frequency) / sampleRate;

    const globalFade = Math.min(
      1,
      alarmTime / 0.025,
      (EMERGENCY_AUDIO_DURATION_SECONDS - alarmTime) / 0.06,
    );
    const urgencyPulse = 0.82 + 0.18 * Math.sin(2 * Math.PI * 7 * alarmTime);
    const siren =
      0.7 * Math.sin(phase) +
      0.22 * Math.sin(phase * 2) +
      0.08 * Math.sin(phase * 3);
    const sample = Math.max(
      -1,
      Math.min(1, siren * urgencyPulse * globalFade * 0.96),
    );
    view.setInt16(
      44 + index * bytesPerSample,
      Math.round(sample * 32_767),
      true,
    );
  }

  return URL.createObjectURL(new Blob([buffer], { type: "audio/wav" }));
}

type CurrentStation = {
  station: string;
  name: string;
  basin: string;
  latitude: number;
  longitude: number;
  level: number | null;
  trend: "rising" | "falling" | "stable";
  trendValue: number | null;
  timestamp: string;
  rain: Record<string, number | null>;
  source: string;
  provenance: string;
};

type HistoryPoint = { timestamp: string; level: number };

type RiverThresholds = {
  attention: number;
  alert: number;
  flood: number;
};

type RiverSeverity =
  | "normal"
  | "attention"
  | "alert"
  | "flood"
  | "unavailable";

type RiverSensor = {
  id: string;
  code: string;
  city: string;
  name: string;
  source: string;
  current: HistoryPoint | null;
  history: HistoryPoint[];
  thresholds: RiverThresholds | null;
  severity: RiverSeverity;
};

const RIVER_CITIES = [
  {
    city: "Muçum",
    sensors: ["sace-86510000", "dcrs-00091"],
  },
  {
    city: "Santa Tereza",
    sensors: ["sace-86472600", "sace-86472000"],
  },
  {
    city: "Guaporé",
    sensors: ["sace-86560000", "sace-86500000"],
  },
] as const;

type Station = {
  code: string;
  city: string;
  name: string;
  latitude: number;
  longitude: number;
  river: string;
  thresholds?: { attention: number; alert: number; flood: number };
  level: number | null;
  rain: number | null;
  timestamp: string | null;
  severity: "normal" | "attention" | "alert" | "flood" | "unavailable";
  quality: string;
  samples: number;
};

type Bulletin = {
  id: string;
  title: string;
  date: string | null;
  status: string;
  href: string;
  latest: boolean;
};

type ActiveAlert = {
  id: string;
  title: string;
  summary: string;
  publishedAt: string;
  validUntil: string;
  severity: "yellow" | "orange" | "red";
  source: "INMET" | "Defesa Civil RS";
  sourceUrl: string;
  imageUrl: string | null;
};

type AlertsLoadState = "loading" | "ready" | "error";

const ALERT_SEVERITY_LABEL: Record<ActiveAlert["severity"], string> = {
  yellow: "Atenção",
  orange: "Risco alto",
  red: "Risco severo",
};

function alertDisplayTitle(title: string) {
  return title.replace(/^(?:Defesa Civil|INMET) alerta:\s*/i, "");
}

type SatelliteFrame = {
  id: string;
  timestamp: string;
  src: string;
  provider?: "inmet" | "cptec";
};

type BasinOverlayMode =
  | "radar-poa"
  | "radar-sc"
  | "satellite-inmet"
  | "satellite-cptec";

type GeographicPoint = {
  longitude: number;
  latitude: number;
};

type BasinReferencePoint = GeographicPoint & {
  label: string;
};

type BasinOverlayViewport = {
  width: number;
  height: number;
  left: number;
  right: number;
  top: number;
  bottom: number;
  fit: "meet" | "slice";
};

type BasinLabelPlacement = {
  dx: number;
  dy: number;
  anchor: "start" | "end";
};

const BASIN_UPSTREAM_BOUNDARY: GeographicPoint[] = [
  { longitude: -51.86722, latitude: -29.16694 },
  { longitude: -52.08, latitude: -29.08 },
  { longitude: -52.3, latitude: -28.93 },
  { longitude: -52.43, latitude: -28.7 },
  { longitude: -52.36, latitude: -28.42 },
  { longitude: -52.18, latitude: -28.2 },
  { longitude: -51.92, latitude: -28.02 },
  { longitude: -51.58, latitude: -27.91 },
  { longitude: -51.25, latitude: -27.98 },
  { longitude: -51.02, latitude: -28.15 },
  { longitude: -50.72, latitude: -28.22 },
  { longitude: -50.45, latitude: -28.36 },
  { longitude: -50.18, latitude: -28.52 },
  { longitude: -50.04, latitude: -28.76 },
  { longitude: -50.04, latitude: -29.02 },
  { longitude: -50.18, latitude: -29.25 },
  { longitude: -50.48, latitude: -29.32 },
  { longitude: -50.82, latitude: -29.27 },
  { longitude: -51.12, latitude: -29.2 },
  { longitude: -51.4, latitude: -29.16 },
  { longitude: -51.65, latitude: -29.18 },
];

const BASIN_REFERENCE_POINTS: BasinReferencePoint[] = [
  {
    label: "Muçum",
    latitude: -29.16694,
    longitude: -51.86722,
  },
  {
    label: "Guaporé",
    latitude: -28.8456,
    longitude: -51.8906,
  },
  {
    label: "Ibiraiaras",
    latitude: -28.37277,
    longitude: -51.63277,
  },
  {
    label: "Vacaria",
    latitude: -28.5175,
    longitude: -50.95361,
  },
  {
    label: "Passo Tainhas",
    latitude: -28.88269,
    longitude: -50.39594,
  },
  {
    label: "Santa Tereza",
    latitude: -29.09807,
    longitude: -51.69956,
  },
];

const BASIN_OVERLAY_VIEWPORTS: Record<
  BasinOverlayMode,
  BasinOverlayViewport
> = {
  "radar-poa": {
    width: 2000,
    height: 1400,
    left: -54.3,
    right: -48.09,
    top: -27.8,
    bottom: -32,
    fit: "meet",
  },
  "radar-sc": {
    width: 859,
    height: 758,
    left: -55.0710069,
    right: -50.1335368,
    top: -24.8625699,
    bottom: -29.45,
    fit: "meet",
  },
  "satellite-cptec": {
    width: 1024,
    height: 768,
    left: -60,
    right: -45,
    top: -22,
    bottom: -36,
    fit: "slice",
  },
  "satellite-inmet": {
    width: 1024,
    height: 768,
    left: -75,
    right: -35,
    top: -12,
    bottom: -40,
    fit: "slice",
  },
};

const BASIN_LABEL_PLACEMENTS: Record<
  BasinOverlayMode,
  Record<string, BasinLabelPlacement>
> = {
  "radar-poa": {
    Muçum: { dx: -66, dy: 45, anchor: "end" },
    Guaporé: { dx: -72, dy: 2, anchor: "end" },
    Ibiraiaras: { dx: -50, dy: -46, anchor: "end" },
    Vacaria: { dx: 48, dy: -48, anchor: "start" },
    "Passo Tainhas": { dx: 64, dy: 8, anchor: "start" },
    "Santa Tereza": { dx: 62, dy: 45, anchor: "start" },
  },
  "radar-sc": {
    Muçum: { dx: -66, dy: 45, anchor: "end" },
    Guaporé: { dx: -72, dy: 2, anchor: "end" },
    Ibiraiaras: { dx: -50, dy: -46, anchor: "end" },
    Vacaria: { dx: 48, dy: -48, anchor: "start" },
    "Passo Tainhas": { dx: 64, dy: 8, anchor: "start" },
    "Santa Tereza": { dx: 62, dy: 45, anchor: "start" },
  },
  "satellite-cptec": {
    Muçum: { dx: -66, dy: 45, anchor: "end" },
    Guaporé: { dx: -72, dy: 2, anchor: "end" },
    Ibiraiaras: { dx: -50, dy: -46, anchor: "end" },
    Vacaria: { dx: 48, dy: -48, anchor: "start" },
    "Passo Tainhas": { dx: 64, dy: 8, anchor: "start" },
    "Santa Tereza": { dx: 62, dy: 45, anchor: "start" },
  },
  "satellite-inmet": {
    Muçum: { dx: 12, dy: -12, anchor: "start" },
  },
};

function projectBasinPoint(
  point: GeographicPoint,
  viewport: BasinOverlayViewport,
) {
  return {
    x:
      ((point.longitude - viewport.left) /
        (viewport.right - viewport.left)) *
      viewport.width,
    y:
      ((viewport.top - point.latitude) /
        (viewport.top - viewport.bottom)) *
      viewport.height,
  };
}

function BasinUpstreamOverlay({ mode }: { mode: BasinOverlayMode }) {
  const viewport = BASIN_OVERLAY_VIEWPORTS[mode];
  const unit = viewport.width / 1000;
  const boundary = BASIN_UPSTREAM_BOUNDARY.map((point, index) => {
    const projected = projectBasinPoint(point, viewport);
    return `${index === 0 ? "M" : "L"} ${projected.x.toFixed(1)} ${projected.y.toFixed(1)}`;
  }).join(" ");
  const showAllLabels = mode !== "satellite-inmet";
  const referencePoints = showAllLabels
    ? BASIN_REFERENCE_POINTS
    : BASIN_REFERENCE_POINTS.filter((point) => point.label === "Muçum");

  return (
    <svg
      className="basin-overlay"
      viewBox={`0 0 ${viewport.width} ${viewport.height}`}
      preserveAspectRatio={`xMidYMid ${viewport.fit}`}
      role="img"
      aria-label="Área contribuinte de referência a montante de Muçum"
    >
      <title>Área contribuinte de referência a montante de Muçum</title>
      <desc>
        Contorno cartográfico de referência e cidades situadas no setor da
        Bacia Taquari-Antas a montante de Muçum.
      </desc>
      <path
        className="basin-boundary-underlay"
        d={`${boundary} Z`}
        strokeWidth={5.5 * unit}
      />
      <path
        className="basin-boundary"
        d={`${boundary} Z`}
        strokeWidth={2.4 * unit}
        strokeDasharray={`${7 * unit} ${5 * unit}`}
      />
      {referencePoints.map((point) => {
        const projected = projectBasinPoint(point, viewport);
        const placement =
          BASIN_LABEL_PLACEMENTS[mode][point.label] ||
          ({ dx: 8, dy: -6, anchor: "start" } as const);
        return (
          <g
            className={`basin-reference-point ${
              point.label === "Muçum" ? "basin-reference-point--outlet" : ""
            }`}
            key={point.label}
            transform={`translate(${projected.x.toFixed(1)} ${projected.y.toFixed(1)})`}
          >
            <title>{point.label}</title>
            <circle
              className="basin-reference-ring"
              r={(point.label === "Muçum" ? 5.4 : 3.7) * unit}
              strokeWidth={1.8 * unit}
            />
            <circle
              className="basin-reference-dot"
              r={(point.label === "Muçum" ? 2.4 : 1.7) * unit}
            />
            <line
              className="basin-reference-leader"
              x1={placement.dx > 0 ? 4 * unit : -4 * unit}
              y1={placement.dy > 0 ? 4 * unit : -4 * unit}
              x2={placement.dx * unit}
              y2={placement.dy * unit}
              strokeWidth={1.2 * unit}
            />
            <text
              x={placement.dx * unit}
              y={placement.dy * unit}
              textAnchor={placement.anchor}
              fontSize={18 * unit}
            >
              {point.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

type CeranRow = {
  timestamp: string;
  upstreamLevel: number;
  downstreamLevel: number;
  inflow: number;
  turbined: number;
  spilled: number;
  residual: number;
  outflow: number;
  status: "Normal" | "Vertendo";
};

type CeranPayload = {
  plant: { id: string; name: string };
  current: CeranRow | null;
  history: CeranRow[];
  source: string;
  fetchedAt?: string;
  message?: string;
};

function formatNumber(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function formatAdaptiveNumber(
  value: number | null | undefined,
  maximumFractionDigits = 2,
) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(value);
}

function formatOneHourLevelChange(value: number) {
  const absolute = Math.abs(value);
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  if (absolute >= 1) {
    return `${sign}${formatAdaptiveNumber(absolute, 2)} m`;
  }
  return `${sign}${formatAdaptiveNumber(absolute * 100, 1)} cm`;
}

function dayKey(value: string | Date) {
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("sv-SE", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function WindowSelector({
  value,
  onChange,
  label = "Janela de tempo",
  options = WINDOWS,
}: {
  value: WindowHours;
  onChange: (value: WindowHours) => void;
  label?: string;
  options?: readonly WindowHours[];
}) {
  return (
    <div className="time-selector" role="group" aria-label={label}>
      {options.map((hours) => (
        <button
          key={hours}
          type="button"
          className={value === hours ? "active" : ""}
          onClick={() => onChange(hours)}
          aria-pressed={value === hours}
        >
          {hours}h
        </button>
      ))}
    </div>
  );
}

function ModuleHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="module-header">
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {action}
    </div>
  );
}

function AnimatedNumber({
  value,
  digits = 2,
  readingKey,
}: {
  value: number | null | undefined;
  digits?: number;
  readingKey?: string;
}) {
  const [displayed, setDisplayed] = useState<number | null>(
    value ?? null,
  );
  const displayedRef = useRef<number | null>(value ?? null);

  useEffect(() => {
    const target = value ?? null;
    if (target === displayedRef.current) return;

    if (target === null || displayedRef.current === null) {
      displayedRef.current = target;
      setDisplayed(target);
      return;
    }

    const from = displayedRef.current;
    const startedAt = performance.now();
    let frame = 0;
    const animate = (now: number) => {
      const progress = Math.min((now - startedAt) / 480, 1);
      const eased = 1 - (1 - progress) ** 3;
      const next = from + (target - from) * eased;
      displayedRef.current = next;
      setDisplayed(next);
      if (progress < 1) {
        frame = window.requestAnimationFrame(animate);
      } else {
        displayedRef.current = target;
        setDisplayed(target);
      }
    };
    frame = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(frame);
  }, [readingKey, value]);

  const formatted = formatNumber(displayed, digits);

  return (
    <strong
      className="animated-number"
      key={readingKey || formatted}
      aria-label={formatted}
      aria-live="polite"
      data-reading-key={readingKey}
    >
      {Array.from(formatted).map((character, index) => (
        <span
          aria-hidden="true"
          className="animated-digit"
          key={index}
          style={{ "--digit-index": index } as React.CSSProperties}
        >
          {character}
        </span>
      ))}
    </strong>
  );
}

function RiverThresholdLegend({
  thresholds,
}: {
  thresholds: RiverThresholds;
}) {
  const entries = [
    {
      key: "attention",
      label: "Atenção",
      value: thresholds.attention,
    },
    {
      key: "alert",
      label: "Alerta",
      value: thresholds.alert,
    },
    {
      key: "flood",
      label: "Inundação",
      value: thresholds.flood,
    },
  ] as const;

  return (
    <div className="river-threshold-legend" aria-label="Limites do nível do rio">
      {entries.map((entry) => (
        <span
          aria-label={`${entry.label}: ${formatNumber(entry.value, 0)} metros`}
          className={`river-threshold ${entry.key}`}
          key={entry.key}
        >
          {entry.label} · {formatNumber(entry.value, 0)} m
        </span>
      ))}
    </div>
  );
}

function updateRiverChartInstance(
  chart: ChartInstance,
  points: HistoryPoint[],
  hours: WindowHours,
  fitAvailableRange: boolean,
) {
  const reference = Math.max(
    ...points.map((point) => Date.parse(point.timestamp)),
  );
  const requestedStart = reference - hours * 60 * 60 * 1000;
  const firstPoint = Math.min(
    ...points.map((point) => Date.parse(point.timestamp)),
  );
  const start =
    fitAvailableRange && firstPoint > requestedStart
      ? firstPoint === reference
        ? reference - 15 * 60 * 1000
        : firstPoint
      : requestedStart;
  const dataset = chart.data.datasets[0];
  dataset.data = points.map((point) => ({
    x: Date.parse(point.timestamp),
    y: point.level,
  }));
  (dataset as typeof dataset & { pointRadius: number }).pointRadius =
    points.length < 5 ? 3 : 0;
  const xScale = chart.options.scales?.x as
    | {
        min?: number;
        max?: number;
        ticks?: { maxTicksLimit?: number };
      }
    | undefined;
  if (xScale) {
    xScale.min = start;
    xScale.max = reference;
    if (xScale.ticks) xScale.ticks.maxTicksLimit = hours <= 8 ? 7 : 6;
  }
  chart.update();
}

function RiverChart({
  points,
  hours,
  compact = false,
  label,
  fitAvailableRange = false,
}: {
  points: HistoryPoint[];
  hours: WindowHours;
  compact?: boolean;
  label?: string;
  fitAvailableRange?: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartInstance | null>(null);
  const pointsRef = useRef(points);
  const hoursRef = useRef(hours);
  const renderedSeriesRef = useRef("");
  const hasPoints = points.length > 0;

  useEffect(() => {
    pointsRef.current = points;
    hoursRef.current = hours;
  }, [hours, points]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!canvasRef.current) return;
      const { Chart, LineController, LineElement, PointElement, LinearScale, Tooltip, Filler } =
        await import("chart.js");
      Chart.register(
        LineController,
        LineElement,
        PointElement,
        LinearScale,
        Tooltip,
        Filler,
      );
      if (cancelled || !canvasRef.current) return;
      const initialPoints = pointsRef.current;
      const initialHours = hoursRef.current;
      const reference = initialPoints.length
        ? Math.max(...initialPoints.map((point) => Date.parse(point.timestamp)))
        : Date.now();
      const requestedStart = reference - initialHours * 60 * 60 * 1000;
      const firstPoint = initialPoints.length
        ? Math.min(
            ...initialPoints.map((point) => Date.parse(point.timestamp)),
          )
        : requestedStart;
      const start =
        fitAvailableRange && firstPoint > requestedStart
          ? firstPoint === reference
            ? reference - 15 * 60 * 1000
            : firstPoint
          : requestedStart;
      chartRef.current?.destroy();
      chartRef.current = new Chart(canvasRef.current, {
        type: "line",
        data: {
          datasets: [
            {
              label: "Nível (m)",
              data: initialPoints.map((point) => ({
                x: Date.parse(point.timestamp),
                y: point.level,
              })),
              borderColor: "#4ca8ff",
              backgroundColor: "rgba(76, 168, 255, .12)",
              pointBackgroundColor: "#b8dcff",
              pointBorderWidth: 0,
              pointRadius: initialPoints.length < 5 ? 3 : 0,
              pointHoverRadius: 4,
              borderWidth: 2,
              tension: 0.28,
              fill: true,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 480, easing: "easeOutQuart" },
          interaction: { intersect: false, mode: "index" },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "#111b27",
              borderColor: "#263548",
              borderWidth: 1,
              titleColor: "#91a4ba",
              bodyColor: "#f5f8fb",
              callbacks: {
                title: (items) => {
                  const value = items[0]?.parsed.x;
                  return value === null || value === undefined
                    ? ""
                    : formatDate(new Date(value).toISOString());
                },
                label: (context) => `${formatNumber(context.parsed.y, 2)} m`,
              },
            },
          },
          scales: {
            x: {
              type: "linear",
              min: start,
              max: reference,
              grid: { display: false },
              ticks: {
                color: "#72859a",
                maxTicksLimit: initialHours <= 8 ? 7 : 6,
                callback: (value) =>
                  formatDate(
                    new Date(Number(value)).toISOString(),
                    hoursRef.current > 24,
                  ),
              },
              border: { display: false },
            },
            y: {
              beginAtZero: false,
              grid: { color: "rgba(120, 144, 168, .12)" },
              ticks: {
                color: "#72859a",
                precision: 2,
                callback: (value) =>
                  `${formatAdaptiveNumber(Number(value), 2)} m`,
              },
              border: { display: false },
            },
          },
        },
      });
    })();
    return () => {
      cancelled = true;
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, [fitAvailableRange, hasPoints]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !points.length) return;
    const seriesSignature = `${hours}|${points
      .map((point) => `${point.timestamp}:${point.level}`)
      .join("|")}`;
    if (seriesSignature === renderedSeriesRef.current) return;
    renderedSeriesRef.current = seriesSignature;
    updateRiverChartInstance(chart, points, hours, fitAvailableRange);
  }, [fitAvailableRange, hours, points]);

  return (
    <div className={`chart-wrap${compact ? " compact" : ""}`}>
      {points.length === 0 ? (
        <div className="empty-state">
          <Database size={22} />
          <strong>Aguardando leituras</strong>
        </div>
      ) : (
        <canvas
          ref={canvasRef}
          aria-label={
            label || `Evolução do nível nas últimas ${hours} horas`
          }
        />
      )}
    </div>
  );
}

function parseCeranTimestamp(value: string) {
  const normalized = Date.parse(value);
  if (Number.isFinite(normalized)) return normalized;
  const match = value.match(
    /^(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}):(\d{2}):(\d{2})$/,
  );
  if (!match) return Number.NaN;
  const [, day, month, year, hour, minute, second] = match;
  return Date.parse(`${year}-${month}-${day}T${hour}:${minute}:${second}-03:00`);
}

function DamOutflowChart({
  rows,
  plantName,
}: {
  rows: CeranRow[];
  plantName: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartInstance | null>(null);

  useEffect(() => {
    let cancelled = false;
    const points = rows
      .map((row) => ({
        x: parseCeranTimestamp(row.timestamp),
        y: row.outflow,
      }))
      .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
      .sort((a, b) => a.x - b.x);
    const timeBounds = timeSeriesBounds(points.map((point) => point.x));

    (async () => {
      if (!canvasRef.current || !points.length) return;
      const {
        Chart,
        LineController,
        LineElement,
        PointElement,
        LinearScale,
        Tooltip,
        Filler,
      } = await import("chart.js");
      Chart.register(
        LineController,
        LineElement,
        PointElement,
        LinearScale,
        Tooltip,
        Filler,
      );
      if (cancelled || !canvasRef.current) return;

      chartRef.current?.destroy();
      chartRef.current = new Chart(canvasRef.current, {
        type: "line",
        data: {
          datasets: [
            {
              label: "Vazão defluente (m³/s)",
              data: points,
              borderColor: "#4ca8ff",
              backgroundColor: "rgba(76, 168, 255, .12)",
              pointBackgroundColor: "#b8dcff",
              pointBorderWidth: 0,
              pointRadius: 0,
              pointHoverRadius: 4,
              borderWidth: 2,
              tension: 0.28,
              fill: true,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 350 },
          interaction: { intersect: false, mode: "index" },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: "#111b27",
              borderColor: "#263548",
              borderWidth: 1,
              titleColor: "#91a4ba",
              bodyColor: "#f5f8fb",
              callbacks: {
                title: (items) => {
                  const value = items[0]?.parsed.x;
                  return value === null || value === undefined
                    ? ""
                    : formatDate(new Date(value).toISOString());
                },
                label: (context) =>
                  `${formatNumber(context.parsed.y, 2)} m³/s`,
              },
            },
          },
          scales: {
            x: {
              type: "linear",
              bounds: "data",
              min: timeBounds?.min,
              max: timeBounds?.max,
              grid: { display: false },
              ticks: {
                color: "#72859a",
                maxTicksLimit: 3,
                callback: (value) =>
                  formatDate(new Date(Number(value)).toISOString(), true),
              },
              border: { display: false },
            },
            y: {
              beginAtZero: false,
              grid: { color: "rgba(120, 144, 168, .12)" },
              ticks: {
                color: "#72859a",
                maxTicksLimit: 5,
                callback: (value) =>
                  new Intl.NumberFormat("pt-BR", {
                    notation: "compact",
                    maximumFractionDigits: 1,
                  }).format(Number(value)),
              },
              border: { display: false },
            },
          },
        },
      });
    })();

    return () => {
      cancelled = true;
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, [rows]);

  return (
    <div className="plant-chart">
      {rows.length ? (
        <canvas
          ref={canvasRef}
          aria-label={`Evolução da vazão defluente da ${plantName}`}
        />
      ) : (
        <div className="empty-state">
          <Database size={22} />
          <strong>Aguardando medições</strong>
        </div>
      )}
    </div>
  );
}

const MEDIA_POLL_INTERVAL_MS = 30_000;
const MEDIA_FRAME_INTERVAL_MS = 900;
const MEDIA_LAST_FRAME_HOLD_MS = 10_000;

function useSynchronizedWeatherFrames(
  radarRefreshToken: number,
  satelliteRefreshToken: number,
) {
  const [frames, setFrames] = useState<
    Array<{
      timestamp: string;
      radar: SatelliteFrame;
      satellite: SatelliteFrame;
    }>
  >([]);
  const [framePosition, setFramePosition] = useState(0);
  const framesRef = useRef<
    Array<{
      timestamp: string;
      radar: SatelliteFrame;
      satellite: SatelliteFrame;
    }>
  >([]);
  const framePositionRef = useRef(0);

  useEffect(() => {
    let active = true;
    let loading = false;

    const refreshFrames = async () => {
      if (loading) return;
      loading = true;
      try {
        const cacheBuster = Date.now();
        const requestOptions: RequestInit = {
          cache: "no-store",
          headers: {
            "cache-control": "no-cache, no-store",
            pragma: "no-cache",
          },
        };
        const [radarResponse, satelliteResponse] = await Promise.all([
          fetch(`/api/radar?_=${cacheBuster}`, requestOptions),
          fetch(`/api/satellite?_=${cacheBuster}`, requestOptions),
        ]);
        const [radarPayload, satellitePayload] = await Promise.all([
          radarResponse.json(),
          satelliteResponse.json(),
        ]);
        if (!radarResponse.ok || !satelliteResponse.ok) {
          throw new Error("Fonte meteorológica indisponível");
        }
        if (!active) return;
        const radarFrames = framesWithinLatestHour<SatelliteFrame>(
          Array.isArray(radarPayload.frames) ? radarPayload.frames : [],
        );
        const satelliteFrames = framesWithinLatestHour<SatelliteFrame>(
          Array.isArray(satellitePayload.frames) ? satellitePayload.frames : [],
        );
        const nextFrames = synchronizeFramesByTimestamp(
          radarFrames,
          satelliteFrames,
        );
        const previousFrames = framesRef.current;
        const currentTimestamp =
          previousFrames[framePositionRef.current]?.timestamp;
        const preservedPosition = currentTimestamp
          ? nextFrames.findIndex(
              (frame) => frame.timestamp === currentTimestamp,
            )
          : -1;
        const nextPosition =
          previousFrames.length === 0
            ? 0
            : preservedPosition >= 0
              ? preservedPosition
              : Math.min(
                  framePositionRef.current,
                  Math.max(0, nextFrames.length - 1),
                );

        framesRef.current = nextFrames;
        framePositionRef.current = nextPosition;
        setFrames(nextFrames);
        setFramePosition(nextPosition);

        for (const frame of nextFrames) {
          for (const source of [frame.radar.src, frame.satellite.src]) {
            const image = new Image();
            image.src = source;
          }
        }
      } catch {
        // Mantém os quadros já armazenados durante falhas transitórias.
      } finally {
        loading = false;
      }
    };

    void refreshFrames();
    const poller = window.setInterval(
      () => void refreshFrames(),
      MEDIA_POLL_INTERVAL_MS,
    );
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [radarRefreshToken, satelliteRefreshToken]);

  useEffect(() => {
    if (frames.length < 2) return;
    const delay =
      framePosition >= frames.length - 1
        ? MEDIA_LAST_FRAME_HOLD_MS
        : MEDIA_FRAME_INTERVAL_MS;
    const timer = window.setTimeout(() => {
      const nextPosition =
        framePositionRef.current >= framesRef.current.length - 1
          ? 0
          : framePositionRef.current + 1;
      framePositionRef.current = nextPosition;
      setFramePosition(nextPosition);
    }, delay);
    return () => window.clearTimeout(timer);
  }, [framePosition, frames.length]);

  return {
    frames,
    currentFrames: frames[framePosition] || frames[0],
  };
}

function useIndependentWeatherFrames(
  endpoint: string,
  refreshToken: number,
) {
  const [frames, setFrames] = useState<SatelliteFrame[]>([]);
  const [framePosition, setFramePosition] = useState(0);
  const framesRef = useRef<SatelliteFrame[]>([]);
  const framePositionRef = useRef(0);

  useEffect(() => {
    let active = true;
    let loading = false;
    const refreshFrames = async () => {
      if (loading) return;
      loading = true;
      try {
        const response = await fetch(`${endpoint}?_=${Date.now()}`, {
          cache: "no-store",
          headers: {
            "cache-control": "no-cache, no-store",
            pragma: "no-cache",
          },
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.message || "Fonte indisponível");
        }
        if (!active) return;
        const nextFrames = framesWithinLatestHour<SatelliteFrame>(
          Array.isArray(payload.frames) ? payload.frames : [],
        );
        const currentId =
          framesRef.current[framePositionRef.current]?.id;
        const preservedPosition = currentId
          ? nextFrames.findIndex((frame) => frame.id === currentId)
          : -1;
        const nextPosition =
          framesRef.current.length === 0
            ? 0
            : preservedPosition >= 0
              ? preservedPosition
              : Math.min(
                  framePositionRef.current,
                  Math.max(0, nextFrames.length - 1),
                );
        framesRef.current = nextFrames;
        framePositionRef.current = nextPosition;
        setFrames(nextFrames);
        setFramePosition(nextPosition);
        for (const frame of nextFrames) {
          const image = new Image();
          image.src = frame.src;
        }
      } catch {
        // Mantém os quadros locais durante falhas transitórias da fonte.
      } finally {
        loading = false;
      }
    };
    void refreshFrames();
    const poller = window.setInterval(
      () => void refreshFrames(),
      MEDIA_POLL_INTERVAL_MS,
    );
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [endpoint, refreshToken]);

  useEffect(() => {
    if (frames.length < 2) return;
    const delay =
      framePosition >= frames.length - 1
        ? MEDIA_LAST_FRAME_HOLD_MS
        : MEDIA_FRAME_INTERVAL_MS;
    const timer = window.setTimeout(() => {
      const nextPosition =
        framePositionRef.current >= framesRef.current.length - 1
          ? 0
          : framePositionRef.current + 1;
      framePositionRef.current = nextPosition;
      setFramePosition(nextPosition);
    }, delay);
    return () => window.clearTimeout(timer);
  }, [framePosition, frames.length]);

  return frames[framePosition] || frames[0];
}

function ExpandableMediaFrame({
  title,
  currentFrame,
  frameClassName,
  imageAlt,
  emptyMessage,
  variant,
  renderOverlay,
}: {
  title: string;
  currentFrame?: SatelliteFrame;
  frameClassName: "media-frame" | "satellite-frame";
  imageAlt: (frame: SatelliteFrame) => string;
  emptyMessage: string;
  variant: "radar-poa" | "radar-sc" | "satellite";
  renderOverlay: (frame: SatelliteFrame) => React.ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const titleId = `expanded-${variant}-title`;

  useEffect(() => {
    if (!expanded) return;
    const previousOverflow = document.body.style.overflow;
    const trigger = frameRef.current;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setExpanded(false);
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", closeOnEscape);
    closeButtonRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
      trigger?.focus();
    };
  }, [expanded]);

  const renderMedia = (frame: SatelliteFrame) => (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={frame.src} alt={imageAlt(frame)} />
      {renderOverlay(frame)}
    </>
  );

  return (
    <>
      <div
        className={`${frameClassName} ${currentFrame ? "expandable-media-frame" : ""}`}
        ref={frameRef}
        role={currentFrame ? "button" : undefined}
        tabIndex={currentFrame ? 0 : undefined}
        aria-label={currentFrame ? `Ampliar ${title}` : undefined}
        onClick={() => currentFrame && setExpanded(true)}
        onKeyDown={(event) => {
          if (
            currentFrame &&
            (event.key === "Enter" || event.key === " ")
          ) {
            event.preventDefault();
            setExpanded(true);
          }
        }}
      >
        {currentFrame ? (
          <>
            {renderMedia(currentFrame)}
            <span className="media-expand-hint" aria-hidden="true">
              <Maximize2 size={13} />
            </span>
          </>
        ) : (
          <div className="empty-state">
            <Database size={22} />
            <strong>{emptyMessage}</strong>
          </div>
        )}
      </div>
      {expanded && currentFrame && (
        <div
          className="media-modal-backdrop"
          onMouseDown={() => setExpanded(false)}
        >
          <section
            className="media-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header>
              <div>
                <h2 id={titleId}>{title}</h2>
                <time>{formatDate(currentFrame.timestamp)}</time>
              </div>
              <button
                ref={closeButtonRef}
                type="button"
                onClick={() => setExpanded(false)}
                aria-label="Fechar imagem ampliada"
              >
                <X size={20} />
              </button>
            </header>
            <div
              className={`media-modal-frame media-modal-frame--${variant}`}
            >
              {renderMedia(currentFrame)}
            </div>
          </section>
        </div>
      )}
    </>
  );
}

function WeatherPlayer({
  currentFrame,
}: {
  currentFrame?: SatelliteFrame;
}) {
  return (
    <section className="panel media-panel">
      <ModuleHeader title="Radar Porto Alegre" />
      <ExpandableMediaFrame
        title="Radar Porto Alegre"
        currentFrame={currentFrame}
        frameClassName="media-frame"
        imageAlt={(frame) =>
          `Radar meteorológico em ${formatDate(frame.timestamp)}`
        }
        emptyMessage="Aguardando imagens do radar"
        variant="radar-poa"
        renderOverlay={() => <BasinUpstreamOverlay mode="radar-poa" />}
      />
      <time className="media-time">
        {currentFrame ? formatDate(currentFrame.timestamp) : "—"}
      </time>
    </section>
  );
}

function SatellitePanel({
  currentFrame,
}: {
  currentFrame?: SatelliteFrame;
}) {
  return (
    <section className="panel media-panel satellite-panel">
      <ModuleHeader title="Satélite" />
      <ExpandableMediaFrame
        title="Satélite"
        currentFrame={currentFrame}
        frameClassName="satellite-frame"
        imageAlt={(frame) =>
          `Satélite GOES sobre a região Sul em ${formatDate(frame.timestamp)}`
        }
        emptyMessage="Imagem de satélite indisponível"
        variant="satellite"
        renderOverlay={(frame) => (
          <BasinUpstreamOverlay
            mode={`satellite-${frame.provider || "inmet"}`}
          />
        )}
      />
      <time className="media-time">
        {currentFrame ? formatDate(currentFrame.timestamp) : "—"}
      </time>
    </section>
  );
}

function ConcordiaRadarPanel({
  currentFrame,
}: {
  currentFrame?: SatelliteFrame;
}) {
  return (
    <section className="panel media-panel">
      <ModuleHeader title="Radar Concórdia" />
      <ExpandableMediaFrame
        title="Radar Concórdia"
        currentFrame={currentFrame}
        frameClassName="media-frame"
        imageAlt={(frame) =>
          `Radar meteorológico de Concórdia em ${formatDate(frame.timestamp)}`
        }
        emptyMessage="Aguardando imagens de Concórdia"
        variant="radar-sc"
        renderOverlay={() => <BasinUpstreamOverlay mode="radar-sc" />}
      />
      <time className="media-time">
        {currentFrame ? formatDate(currentFrame.timestamp) : "—"}
      </time>
    </section>
  );
}

function SynchronizedWeatherPanels({
  radarRefreshToken,
  concordiaRefreshToken,
  satelliteRefreshToken,
}: {
  radarRefreshToken: number;
  concordiaRefreshToken: number;
  satelliteRefreshToken: number;
}) {
  const { currentFrames } = useSynchronizedWeatherFrames(
    radarRefreshToken,
    satelliteRefreshToken,
  );
  const concordiaFrame = useIndependentWeatherFrames(
    "/api/radar-sc",
    concordiaRefreshToken,
  );

  return (
    <section className="split-grid">
      <WeatherPlayer currentFrame={currentFrames?.radar} />
      <ConcordiaRadarPanel currentFrame={concordiaFrame} />
      <SatellitePanel currentFrame={currentFrames?.satellite} />
    </section>
  );
}

function useLeafletMap(
  containerRef: React.RefObject<HTMLDivElement | null>,
  center: [number, number],
  zoom: number,
) {
  const mapRef = useRef<LeafletMap | null>(null);
  const layerRef = useRef<LayerGroup | null>(null);
  const [ready, setReady] = useState(false);
  const [centerLatitude, centerLongitude] = center;

  useEffect(() => {
    let active = true;
    (async () => {
      if (!containerRef.current || mapRef.current) return;
      const L = await import("leaflet");
      if (!active || !containerRef.current) return;
      const map = L.map(containerRef.current, {
        center: [centerLatitude, centerLongitude],
        zoom,
        zoomControl: true,
        attributionControl: true,
      });
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        {
          maxZoom: 19,
          attribution: "&copy; OpenStreetMap &copy; CARTO",
        },
      ).addTo(map);
      mapRef.current = map;
      layerRef.current = L.layerGroup().addTo(map);
      setReady(true);
      window.setTimeout(() => map.invalidateSize(), 0);
    })();
    return () => {
      active = false;
      mapRef.current?.remove();
      mapRef.current = null;
      layerRef.current = null;
      setReady(false);
    };
  }, [centerLatitude, centerLongitude, containerRef, zoom]);

  return { mapRef, layerRef, ready };
}

function RainMap({
  stations,
  hours,
}: {
  stations: Station[];
  hours: WindowHours;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { mapRef, layerRef, ready } = useLeafletMap(containerRef, [-29.1, -51.45], 8);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!mapRef.current || !layerRef.current) return;
      const L = await import("leaflet");
      if (!active || !layerRef.current) return;
      layerRef.current.clearLayers();
      const colorForRain = (rain: number) =>
        rain < 50 ? "#3b9cff" : rain <= 80 ? "#facc15" : "#f05252";
      const readableStations = stations.filter(
        (station): station is Station & { rain: number } =>
          station.rain !== null,
      );
      readableStations.forEach((station) => {
        const color = colorForRain(station.rain);
        const icon = L.divIcon({
          className: "leaflet-custom-icon",
          html: `<span class="rain-marker" style="--marker:${color}"><b>${Math.round(station.rain)}</b><small>mm</small></span>`,
          iconSize: [48, 48],
          iconAnchor: [24, 24],
        });
        L.marker([station.latitude, station.longitude], { icon })
          .bindPopup(
            `<div class="map-popup"><strong>${station.city}</strong><span>${station.name}</span><dl><dt>Chuva ${hours}h</dt><dd>${formatNumber(station.rain, 1)} mm</dd><dt>Amostras</dt><dd>${station.samples}</dd><dt>Atualização</dt><dd>${formatDate(station.timestamp)}</dd></dl></div>`,
          )
          .addTo(layerRef.current!);
      });
    })();
    return () => {
      active = false;
    };
  }, [hours, layerRef, mapRef, ready, stations]);

  return <div ref={containerRef} className="leaflet-map" aria-label="Mapa de chuva acumulada na Bacia do Taquari" />;
}

function ExpandableRainMap({
  stations,
  hours,
}: {
  stations: Station[];
  hours: WindowHours;
}) {
  const [expanded, setExpanded] = useState(false);
  const expandButtonRef = useRef<HTMLButtonElement | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const titleId = "expanded-rain-map-title";

  useEffect(() => {
    if (!expanded) return;
    const previousOverflow = document.body.style.overflow;
    const trigger = expandButtonRef.current;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setExpanded(false);
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", closeOnEscape);
    closeButtonRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
      trigger?.focus();
    };
  }, [expanded]);

  return (
    <>
      <div className="map-wrap map-wrap--expandable">
        <RainMap stations={stations} hours={hours} />
        <button
          ref={expandButtonRef}
          className="map-expand-button"
          type="button"
          onClick={() => setExpanded(true)}
          aria-label="Ampliar mapa de chuva acumulada"
          title="Ampliar mapa"
        >
          <Maximize2 size={15} />
        </button>
      </div>
      {expanded && (
        <div
          className="media-modal-backdrop"
          onMouseDown={() => setExpanded(false)}
        >
          <section
            className="media-modal rain-map-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header>
              <div>
                <h2 id={titleId}>Chuva acumulada</h2>
                <time>Últimas {hours}h</time>
              </div>
              <button
                ref={closeButtonRef}
                type="button"
                onClick={() => setExpanded(false)}
                aria-label="Fechar mapa ampliado"
              >
                <X size={20} />
              </button>
            </header>
            <div className="rain-map-modal-frame">
              <RainMap stations={stations} hours={hours} />
            </div>
          </section>
        </div>
      )}
    </>
  );
}

export default function Home() {
  const [current, setCurrent] = useState<CurrentStation | null>(null);
  const [currentError, setCurrentError] = useState<string | null>(null);
  const [connection, setConnection] = useState<
    "connecting" | "live" | "polling" | "offline"
  >("connecting");
  const [freshnessNow, setFreshnessNow] = useState(() => Date.now());
  const [chartHours, setChartHours] = useState<WindowHours>(3);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [riverSensors, setRiverSensors] = useState<RiverSensor[]>([]);
  const [rainHours, setRainHours] = useState<WindowHours>(24);
  const [stations, setStations] = useState<Station[]>([]);
  const [alerts, setAlerts] = useState<ActiveAlert[]>([]);
  const [alertsLoadState, setAlertsLoadState] =
    useState<AlertsLoadState>("loading");
  const [alertsStatusMessage, setAlertsStatusMessage] =
    useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<ActiveAlert | null>(null);
  const alertDialogRef = useRef<HTMLElement | null>(null);
  const alertCloseButtonRef = useRef<HTMLButtonElement | null>(null);
  const alertTriggerRef = useRef<HTMLButtonElement | null>(null);
  const [bulletins, setBulletins] = useState<Bulletin[]>([]);
  const [liveVersions, setLiveVersions] = useState<Record<LiveTopic, number>>({
    radar: 0,
    "radar-sc": 0,
    satellite: 0,
    bulletins: 0,
    alerts: 0,
    "river-history": 0,
    sace: 0,
    ceran: 0,
    rain: 0,
  });
  const riverHistoryVersion = liveVersions["river-history"];
  const [ceranPlants, setCeranPlants] = useState<
    Partial<Record<PlantId, CeranPayload>>
  >({});
  const [pushState, setPushState] = useState<PushUiState>("checking");
  const [pushPreferences, setPushPreferences] = useState<PushPreferences>({
    rules: [],
    sources: ALERT_RULE_SOURCES,
  });
  const [pushPreferencesState, setPushPreferencesState] =
    useState<PushPreferencesState>("idle");
  const [pushPreferencesOpen, setPushPreferencesOpen] = useState(false);
  const [alertRulesDraft, setAlertRulesDraft] = useState<AlertRule[]>([]);
  const [alarmTestCountdown, setAlarmTestCountdown] = useState<number | null>(
    null,
  );
  const [alarmTestMessage, setAlarmTestMessage] = useState("");
  const [appInstalled, setAppInstalled] = useState(false);
  const [installAvailable, setInstallAvailable] = useState(false);
  const installPromptRef = useRef<InstallPromptEvent | null>(null);
  const persistentAlertAudioRef = useRef<HTMLAudioElement | null>(null);
  const persistentAlertAudioUrlRef = useRef<string | null>(null);
  const persistentAlertAudioRequestedRef = useRef(false);
  const persistentAlertAudioModeRef = useRef<"silent" | "alarm">("silent");
  const alarmTestTimerRef = useRef<number | null>(null);
  const alarmTestIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    const standaloneMedia = window.matchMedia("(display-mode: standalone)");
    const navigatorWithStandalone = navigator as Navigator & {
      standalone?: boolean;
    };
    const updateInstalledState = () => {
      setAppInstalled(
        standaloneMedia.matches || navigatorWithStandalone.standalone === true,
      );
    };
    const captureInstallPrompt = (event: Event) => {
      event.preventDefault();
      installPromptRef.current = event as InstallPromptEvent;
      setInstallAvailable(true);
    };
    const markAsInstalled = () => {
      installPromptRef.current = null;
      setInstallAvailable(false);
      setAppInstalled(true);
    };

    updateInstalledState();
    standaloneMedia.addEventListener("change", updateInstalledState);
    window.addEventListener("beforeinstallprompt", captureInstallPrompt);
    window.addEventListener("appinstalled", markAsInstalled);
    return () => {
      standaloneMedia.removeEventListener("change", updateInstalledState);
      window.removeEventListener("beforeinstallprompt", captureInstallPrompt);
      window.removeEventListener("appinstalled", markAsInstalled);
    };
  }, []);

  const installApp = useCallback(async () => {
    const installPrompt = installPromptRef.current;
    if (!installPrompt) return;

    setInstallAvailable(false);
    await installPrompt.prompt();
    const choice = await installPrompt.userChoice;
    if (installPromptRef.current === installPrompt) {
      installPromptRef.current = null;
    }
    if (choice.outcome === "accepted") setAppInstalled(true);
  }, []);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    void navigator.serviceWorker
      .register("/push-worker.js", { scope: "/" })
      .catch(() => undefined);
  }, []);

  const stopPersistentAlertAudio = useCallback(() => {
    persistentAlertAudioRequestedRef.current = false;
    persistentAlertAudioModeRef.current = "silent";
    const audio = persistentAlertAudioRef.current;
    persistentAlertAudioRef.current = null;
    if (audio) {
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
      audio.remove();
    }
    if (persistentAlertAudioUrlRef.current) {
      URL.revokeObjectURL(persistentAlertAudioUrlRef.current);
      persistentAlertAudioUrlRef.current = null;
    }
    if ("mediaSession" in navigator) {
      navigator.mediaSession.playbackState = "none";
      navigator.mediaSession.metadata = null;
    }
  }, []);

  const startPersistentAlertAudio = useCallback(async () => {
    let audio = persistentAlertAudioRef.current;
    if (!audio) {
      const url = createAlertAudioTrackUrl();
      const newAudio = new Audio(url);
      newAudio.loop = true;
      newAudio.preload = "auto";
      newAudio.volume = 1;
      newAudio.muted = false;
      newAudio.setAttribute("playsinline", "");
      newAudio.setAttribute("aria-hidden", "true");
      newAudio.style.display = "none";
      newAudio.addEventListener("timeupdate", () => {
        if (
          persistentAlertAudioModeRef.current === "silent" &&
          newAudio.currentTime >= SILENT_AUDIO_RESET_SECONDS
        ) {
          newAudio.currentTime = 0;
        }
      });
      newAudio.addEventListener("ended", () => {
        persistentAlertAudioModeRef.current = "silent";
        if (!persistentAlertAudioRequestedRef.current) return;
        newAudio.loop = true;
        newAudio.currentTime = 0;
        newAudio.volume = 1;
        void newAudio.play().catch(() => undefined);
        if ("mediaSession" in navigator) {
          navigator.mediaSession.metadata = new MediaMetadata({
            title: "Alarme sonoro ativo",
            artist: "Monitoramento do Rio Taquari",
          });
          navigator.mediaSession.playbackState = "playing";
        }
      });
      document.body.append(newAudio);
      persistentAlertAudioRef.current = newAudio;
      persistentAlertAudioUrlRef.current = url;
      audio = newAudio;
    }

    await audio.play().catch(() => undefined);

    if (audio.paused) return;
    if ("mediaSession" in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: "Alarme sonoro ativo",
        artist: "Monitoramento do Rio Taquari",
      });
      navigator.mediaSession.playbackState = "playing";
    }
  }, []);

  const primeAlertAudio = useCallback(() => {
    void startPersistentAlertAudio();
  }, [startPersistentAlertAudio]);

  const playAlertSound = useCallback(async () => {
    await startPersistentAlertAudio();
    const audio = persistentAlertAudioRef.current;
    if (!audio) return;
    persistentAlertAudioModeRef.current = "alarm";
    audio.loop = false;
    audio.muted = false;
    audio.volume = 1;
    audio.currentTime = EMERGENCY_AUDIO_START_SECONDS;
    await audio.play().catch(() => undefined);
    if (!audio.paused && "mediaSession" in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: "🚨 Alarme de emergência",
        artist: "Monitoramento do Rio Taquari",
      });
      navigator.mediaSession.playbackState = "playing";
    }
  }, [startPersistentAlertAudio]);

  const clearAlarmTestTimers = useCallback(() => {
    if (alarmTestTimerRef.current !== null) {
      window.clearTimeout(alarmTestTimerRef.current);
      alarmTestTimerRef.current = null;
    }
    if (alarmTestIntervalRef.current !== null) {
      window.clearInterval(alarmTestIntervalRef.current);
      alarmTestIntervalRef.current = null;
    }
  }, []);

  useEffect(
    () => () => {
      clearAlarmTestTimers();
    },
    [clearAlarmTestTimers],
  );

  const persistentAlertAudioEnabled = pushState === "subscribed";

  useEffect(() => {
    if (!persistentAlertAudioEnabled) {
      stopPersistentAlertAudio();
      return;
    }

    persistentAlertAudioRequestedRef.current = true;
    const activateAudio = () => {
      if (persistentAlertAudioRequestedRef.current) {
        void startPersistentAlertAudio();
      }
    };
    void startPersistentAlertAudio();
    window.addEventListener("pointerdown", activateAudio, true);
    window.addEventListener("keydown", activateAudio, true);
    window.addEventListener("focus", activateAudio);
    window.addEventListener("pageshow", activateAudio);
    document.addEventListener("visibilitychange", activateAudio);
    const keepAliveTimer = window.setInterval(activateAudio, 10_000);
    return () => {
      window.removeEventListener("pointerdown", activateAudio, true);
      window.removeEventListener("keydown", activateAudio, true);
      window.removeEventListener("focus", activateAudio);
      window.removeEventListener("pageshow", activateAudio);
      document.removeEventListener("visibilitychange", activateAudio);
      window.clearInterval(keepAliveTimer);
    };
  }, [
    persistentAlertAudioEnabled,
    startPersistentAlertAudio,
    stopPersistentAlertAudio,
  ]);

  useEffect(
    () => () => {
      stopPersistentAlertAudio();
    },
    [stopPersistentAlertAudio],
  );

  const loadPushPreferences = useCallback(async (endpoint: string) => {
    setPushPreferencesState("loading");
    try {
      const response = await fetch(
        "/api/push/preferences",
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ endpoint }),
        },
      );
      const preferences = (await response.json()) as PushPreferences;
      if (!response.ok) throw new Error("Preferências indisponíveis");
      setPushPreferences(preferences);
      setPushPreferencesState("idle");
    } catch {
      setPushPreferencesState("error");
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function preparePush() {
      if (
        !("serviceWorker" in navigator) ||
        !("PushManager" in window) ||
        !("Notification" in window)
      ) {
        if (active) setPushState("unsupported");
        return;
      }
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription =
          await registration.pushManager.getSubscription();
        if (!active) return;
        if (Notification.permission === "denied") {
          setPushState("blocked");
        } else {
          setPushState(subscription ? "subscribed" : "unsubscribed");
          if (subscription) {
            void loadPushPreferences(subscription.endpoint);
          }
        }
      } catch {
        if (active) setPushState("error");
      }
    }
    void preparePush();
    return () => {
      active = false;
    };
  }, [loadPushPreferences]);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    const handleWorkerMessage = (event: MessageEvent) => {
      if (event.data?.type === "play-alert-sound") {
        void playAlertSound();
      }
    };
    navigator.serviceWorker.addEventListener("message", handleWorkerMessage);
    return () =>
      navigator.serviceWorker.removeEventListener(
        "message",
        handleWorkerMessage,
      );
  }, [playAlertSound]);

  useEffect(() => {
    const timer = window.setInterval(
      () => setFreshnessNow(Date.now()),
      10_000,
    );
    return () => window.clearInterval(timer);
  }, []);

  const togglePush = useCallback(async () => {
    if (
      pushState === "checking" ||
      pushState === "working" ||
      pushState === "unsupported" ||
      pushState === "blocked"
    ) {
      return;
    }
    setPushState("working");
    try {
      const registration = await navigator.serviceWorker.ready;
      const existing = await registration.pushManager.getSubscription();
      if (existing) {
        const response = await fetch("/api/push/subscribe", {
          method: "DELETE",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ endpoint: existing.endpoint }),
        });
        if (!response.ok) throw new Error("Falha ao remover a inscrição");
        await existing.unsubscribe();
        setPushState("unsubscribed");
        setPushPreferencesOpen(false);
        setPushPreferences({ rules: [], sources: ALERT_RULE_SOURCES });
        return;
      }

      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setPushState(permission === "denied" ? "blocked" : "unsubscribed");
        return;
      }
      const keyResponse = await fetch("/api/push/public-key", {
        cache: "no-store",
      });
      const keyPayload = (await keyResponse.json()) as {
        publicKey?: string;
      };
      if (!keyResponse.ok || !keyPayload.publicKey) {
        throw new Error("Chave de notificação indisponível");
      }
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: vapidKeyToUint8Array(keyPayload.publicKey),
      });
      const response = await fetch("/api/push/subscribe", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(subscription.toJSON()),
      });
      if (!response.ok) {
        await subscription.unsubscribe();
        throw new Error("Falha ao salvar a inscrição");
      }
      setPushState("subscribed");
      setPushPreferences({ rules: [], sources: ALERT_RULE_SOURCES });
      setPushPreferencesState("idle");
    } catch {
      setPushState("error");
    }
  }, [pushState]);

  const openPushPreferences = useCallback(() => {
    setAlertRulesDraft(pushPreferences.rules);
    setPushPreferencesState("idle");
    setPushPreferencesOpen(true);
  }, [pushPreferences]);

  const addAlertRule = useCallback(() => {
    setAlertRulesDraft((current) => [
      ...current,
      {
        id: `rule_${crypto.randomUUID().replaceAll("-", "")}`,
        kind: "river_level",
        sourceId: "86510000",
        threshold: 9,
        windowHours: null,
        severity: "attention",
        enabled: true,
      },
    ]);
    setPushPreferencesState("idle");
  }, []);

  const updateAlertRule = useCallback(
    (id: string, patch: Partial<AlertRule>) => {
      setAlertRulesDraft((current) =>
        current.map((rule) => {
          if (rule.id !== id) return rule;
          const next = { ...rule, ...patch };
          if (patch.kind && patch.kind !== rule.kind) {
            const firstSource = pushPreferences.sources.find(
              (source) => source.kind === patch.kind,
            );
            next.sourceId = firstSource?.id || "";
            next.windowHours =
              patch.kind === "rain_accumulation" ? 24 : null;
          }
          return next;
        }),
      );
      setPushPreferencesState("idle");
    },
    [pushPreferences.sources],
  );

  const removeAlertRule = useCallback((id: string) => {
    setAlertRulesDraft((current) =>
      current.filter((rule) => rule.id !== id),
    );
    setPushPreferencesState("idle");
  }, []);

  const savePushPreferences = useCallback(async () => {
    if (
      alertRulesDraft.some(
        (rule) =>
          !Number.isFinite(rule.threshold) ||
          rule.threshold <= 0 ||
          !rule.sourceId,
      )
    ) {
      setPushPreferencesState("error");
      return;
    }
    setPushPreferencesState("saving");
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription =
        await registration.pushManager.getSubscription();
      if (!subscription) throw new Error("Inscrição indisponível");
      const response = await fetch("/api/push/preferences", {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          rules: alertRulesDraft,
        }),
      });
      const preferences = (await response.json()) as PushPreferences;
      if (!response.ok) throw new Error("Falha ao salvar preferências");
      setPushPreferences(preferences);
      setAlertRulesDraft(preferences.rules);
      setPushPreferencesState("saved");
    } catch {
      setPushPreferencesState("error");
    }
  }, [alertRulesDraft]);

  const testAlarm = useCallback(() => {
    if (alarmTestCountdown !== null) return;
    clearAlarmTestTimers();
    primeAlertAudio();
    setAlarmTestCountdown(0);
    setAlarmTestMessage("Solicitando o teste...");

    void (async () => {
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription =
          await registration.pushManager.getSubscription();
        if (!subscription) throw new Error("Inscrição indisponível");
        const response = await fetch("/api/push/test", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });
        const payload = (await response.json()) as {
          delayMs?: number;
          sendAt?: string;
        };
        if (!response.ok) {
          throw new Error("Falha ao agendar o teste pela API");
        }
        const scheduledSendAt = Date.parse(payload.sendAt || "");
        const deadline = Number.isFinite(scheduledSendAt)
          ? scheduledSendAt
          : Date.now() + (payload.delayMs || 5_000);
        const remainingMs = Math.max(0, deadline - Date.now());
        setAlarmTestCountdown(
          Math.max(1, Math.ceil(remainingMs / 1_000)),
        );
        setAlarmTestMessage(
          "Teste aceito. O alarme será enviado em 5 segundos.",
        );
        alarmTestIntervalRef.current = window.setInterval(() => {
          setAlarmTestCountdown(
            Math.max(1, Math.ceil((deadline - Date.now()) / 1_000)),
          );
        }, 200);
        alarmTestTimerRef.current = window.setTimeout(() => {
          clearAlarmTestTimers();
          setAlarmTestCountdown(null);
          setAlarmTestMessage("O alarme de teste foi disparado.");
        }, remainingMs);
      } catch {
        clearAlarmTestTimers();
        setAlarmTestCountdown(null);
        setAlarmTestMessage(
          "Não foi possível agendar o teste neste dispositivo.",
        );
      }
    })();
  }, [
    alarmTestCountdown,
    clearAlarmTestTimers,
    primeAlertAudio,
  ]);

  const pushLabel =
    pushState === "subscribed"
      ? "Notificações ativas"
      : pushState === "working" || pushState === "checking"
        ? "Verificando…"
        : pushState === "blocked"
          ? "Notificações bloqueadas"
          : pushState === "unsupported"
            ? "Notificações indisponíveis"
            : pushState === "error"
              ? "Tentar notificações"
              : "Ativar notificações";

  const recordPoint = useCallback((point: HistoryPoint) => {
    setHistory((existing) => {
      const merged = [...existing.filter((item) => item.timestamp !== point.timestamp), point]
        .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp))
        .filter((item) => Date.now() - Date.parse(item.timestamp) <= 48 * 60 * 60 * 1000);
      try {
        localStorage.setItem("dcrs-00091-session-history-v2", JSON.stringify(merged));
      } catch {
        // Storage is an enhancement; the in-memory series remains available.
      }
      return merged;
    });
  }, []);

  const applyCurrent = useCallback(
    (payload: CurrentStation) => {
      setCurrent(payload);
      setCurrentError(null);
      if (payload.level !== null) {
        recordPoint({ timestamp: payload.timestamp, level: payload.level });
      }
    },
    [recordPoint],
  );

  const fetchCurrent = useCallback(async () => {
    try {
      const response = await fetch("/api/defesa-civil?mode=current", { cache: "no-store" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Fonte indisponível");
      applyCurrent(payload);
      setConnection((state) => (state === "live" ? state : "polling"));
    } catch (error) {
      setCurrentError(error instanceof Error ? error.message : "Falha na fonte");
      setConnection((state) => (state === "live" ? state : "offline"));
    }
  }, [applyCurrent]);

  useEffect(() => {
    const restore = window.setTimeout(() => {
      try {
        const stored = localStorage.getItem("dcrs-00091-session-history-v2");
        if (stored) setHistory(JSON.parse(stored));
      } catch {
        // Invalid or blocked browser storage is ignored safely.
      }
    }, 0);
    return () => window.clearTimeout(restore);
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(fetchCurrent, 0);
    const poller = window.setInterval(fetchCurrent, 60_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(poller);
    };
  }, [fetchCurrent]);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retry: number | null = null;
    let stopped = false;
    let reconnectAttempts = 0;
    const topics = new Set([
      "radar",
      "radar-sc",
      "satellite",
      "bulletins",
      "alerts",
      "river-history",
      "sace",
      "ceran",
      "rain",
    ]);

    const connect = () => {
      if (stopped) return;
      setConnection("connecting");
      const configured = process.env.NEXT_PUBLIC_LIVE_WS_URL;
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const liveUrl =
        configured || `${protocol}//${window.location.host}/api/live`;
      try {
        socket = new WebSocket(liveUrl);
      } catch {
        setConnection("polling");
        const delay = Math.min(1_000 * 2 ** reconnectAttempts, 30_000);
        reconnectAttempts += 1;
        retry = window.setTimeout(connect, delay);
        return;
      }
      socket.onopen = () => {
        reconnectAttempts = 0;
        setConnection("live");
      };
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as {
            type?: string;
            payload?: Record<string, unknown>;
          };
          if (message.type === "river" && message.payload) {
            const level =
              typeof message.payload.level === "number"
                ? message.payload.level
                : null;
            const timestamp = message.payload.timestamp;
            if (typeof timestamp !== "string") return;
            applyCurrent({
                station: "DCRS-00091",
                name: "Muçum/Encantado",
                basin: "Rio Taquari-Antas",
                latitude: -29.1682,
                longitude: -51.8868,
                level,
                trend:
                  message.payload.trend === "rising" ||
                  message.payload.trend === "falling"
                    ? message.payload.trend
                    : "stable",
                trendValue:
                  typeof message.payload.trendValue === "number"
                    ? message.payload.trendValue
                    : null,
                timestamp,
                rain: {},
                source: "Defesa Civil RS / MKS",
                provenance: "sqlite-websocket",
            });
            return;
          }
          if (message.type && topics.has(message.type)) {
            const topic = message.type as LiveTopic;
            setLiveVersions((versions) => ({
              ...versions,
              [topic]: versions[topic] + 1,
            }));
          }
        } catch {
          // Mensagens inválidas não interrompem a conexão local.
        }
      };
      socket.onerror = () => socket?.close();
      socket.onclose = () => {
        if (stopped) return;
        setConnection("polling");
        const delay = Math.min(1_000 * 2 ** reconnectAttempts, 30_000);
        reconnectAttempts += 1;
        retry = window.setTimeout(connect, delay);
      };
    };
    connect();
    return () => {
      stopped = true;
      if (retry) window.clearTimeout(retry);
      socket?.close();
    };
  }, [applyCurrent]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const historyHours = Math.max(chartHours, 3);
        const response = await fetch(`/api/defesa-civil?mode=history&hours=${historyHours}`, {
          cache: "no-store",
        });
        const payload = await response.json();
        if (!active) return;
        if (Array.isArray(payload.points) && payload.points.length) {
          setHistory((session) => {
            const combined = [...payload.points, ...session];
            return combined.filter(
              (point, index, all) =>
                index === all.findIndex((candidate) => candidate.timestamp === point.timestamp),
            );
          });
        }
      } catch {
        // O registro contínuo das leituras ao vivo permanece ativo.
      }
    })();
    return () => {
      active = false;
    };
  }, [chartHours]);

  useEffect(() => {
    let active = true;
    const refreshStations = () => {
      fetch(`/api/stations?hours=${rainHours}`, { cache: "no-store" })
        .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.message || "Fonte indisponível");
        if (active) setStations(payload.stations || []);
      })
      .catch(() => {
        // Mantém a última leitura durante falhas transitórias.
      });
    };
    refreshStations();
    const poller = window.setInterval(refreshStations, 60_000);
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [liveVersions.rain, rainHours]);

  useEffect(() => {
    let active = true;
    const refreshRiverSensors = async () => {
      try {
        const response = await fetch(
          `/api/river-levels?hours=${Math.max(chartHours, 3)}`,
          { cache: "no-store" },
        );
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.message || "Níveis indisponíveis");
        }
        if (active) setRiverSensors(payload.stations || []);
      } catch {
        // Mantém a última série recebida durante falhas transitórias.
      }
    };

    void refreshRiverSensors();
    const poller = window.setInterval(refreshRiverSensors, 60_000);
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [chartHours, liveVersions.sace, riverHistoryVersion]);

  useEffect(() => {
    let active = true;
    const refreshAlerts = async () => {
      try {
        const response = await fetch("/api/alerts", { cache: "no-store" });
        const payload = (await response.json()) as {
          alerts?: ActiveAlert[];
          message?: string;
          status?: "ok" | "checking" | "degraded";
          sources?: Array<{
            name: string;
            status: "ok" | "checking" | "error";
          }>;
        };
        if (!response.ok || !Array.isArray(payload.alerts)) {
          throw new Error(payload.message || "Alertas indisponíveis");
        }
        if (active) {
          setAlerts(payload.alerts);
          const failedSources = (payload.sources || [])
            .filter((source) => source.status === "error")
            .map((source) => source.name);
          setAlertsLoadState(
            payload.status === "degraded"
              ? "error"
              : payload.status === "checking"
                ? "loading"
                : "ready",
          );
          setAlertsStatusMessage(
            failedSources.length
              ? `Falha temporária na consulta: ${failedSources.join(" e ")}.`
              : null,
          );
        }
      } catch {
        if (active) {
          setAlertsLoadState("error");
          setAlertsStatusMessage(
            "Não foi possível consultar os alertas oficiais agora.",
          );
        }
        // Mantém alertas já recebidos durante falhas transitórias.
      }
    };
    void refreshAlerts();
    const poller = window.setInterval(refreshAlerts, 60_000);
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [liveVersions.alerts]);

  useEffect(() => {
    if (!selectedAlert) return;
    const previousOverflow = document.body.style.overflow;
    const trigger = alertTriggerRef.current;
    const handleDialogKeys = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSelectedAlert(null);
        return;
      }
      if (event.key !== "Tab" || !alertDialogRef.current) return;
      const focusable = [...alertDialogRef.current.querySelectorAll<HTMLElement>(
        "a[href], button:not([disabled]), [tabindex]:not([tabindex='-1'])",
      )].filter((element) => element.getClientRects().length > 0);
      const first = focusable.at(0);
      const last = focusable.at(-1);
      if (!first || !last) return;
      if (!alertDialogRef.current.contains(document.activeElement)) {
        event.preventDefault();
        first.focus();
      } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleDialogKeys);
    alertCloseButtonRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleDialogKeys);
      trigger?.focus();
    };
  }, [selectedAlert]);

  useEffect(() => {
    let active = true;
    const refreshBulletins = () => {
      fetch("/api/bulletins", { cache: "no-store" })
        .then((response) => response.json())
        .then((payload) => {
        if (!active) return;
        const today = dayKey(new Date());
        const yesterday = dayKey(new Date(Date.now() - 24 * 60 * 60 * 1000));
        setBulletins(
          (payload.bulletins || []).filter(
            (bulletin: Bulletin) =>
              bulletin.date &&
              [today, yesterday].includes(dayKey(bulletin.date)),
          ).slice(0, 1),
        );
      })
      .catch(() => {
        // Mantém boletins já recebidos durante falhas transitórias.
      });
    };
    refreshBulletins();
    const poller = window.setInterval(refreshBulletins, 60_000);
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [liveVersions.bulletins]);

  useEffect(() => {
    let active = true;
    const refreshCeran = () => {
      Promise.allSettled(
        CERAN_PLANTS.map(async ({ id }) => {
          const response = await fetch(`/api/ceran?plant=${id}`, {
            cache: "no-store",
          });
          if (!response.ok) throw new Error(`Usina ${id} indisponível`);
          return [id, (await response.json()) as CeranPayload] as const;
        }),
      ).then((results) => {
        const entries = results.flatMap((result) =>
          result.status === "fulfilled" ? [result.value] : [],
        );
        if (active) {
          setCeranPlants((existing) => ({
            ...existing,
            ...Object.fromEntries(entries),
          }));
        }
      });
    };
    refreshCeran();
    const poller = window.setInterval(refreshCeran, 60_000);
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [liveVersions.ceran]);

  const displayedRiverSensors = useMemo(() => {
    const byId = new Map(riverSensors.map((sensor) => [sensor.id, sensor]));
    const storedDcrs = byId.get("dcrs-00091");
    const dcrsHistory = [...(storedDcrs?.history || []), ...history]
      .filter(
        (point, index, all) =>
          index ===
          all.findIndex(
            (candidate) => candidate.timestamp === point.timestamp,
          ),
      )
      .sort(
        (left, right) =>
          Date.parse(left.timestamp) - Date.parse(right.timestamp),
      );

    if (current || storedDcrs) {
      byId.set("dcrs-00091", {
        id: "dcrs-00091",
        code: "DCRS-00091",
        city: "Muçum",
        name: "Sensor na Barra do Guaporé",
        source: "Rede RS",
        current:
          current?.level !== null && current?.level !== undefined
            ? { timestamp: current.timestamp, level: current.level }
            : storedDcrs?.current || null,
        history: dcrsHistory,
        thresholds: null,
        severity: "unavailable",
      });
    }

    return byId;
  }, [current, history, riverSensors]);

  const riverGroups = RIVER_CITIES.map((group) => ({
    city: group.city,
    sensors: group.sensors.flatMap((id) => {
      const sensor = displayedRiverSensors.get(id);
      return sensor ? [sensor] : [];
    }),
  }));
  return (
    <main>
      {installAvailable && !appInstalled && (
        <aside className="install-banner" aria-label="Instalar aplicativo">
          <div className="install-banner-content">
            <span className="install-banner-copy">
              Acompanhe o Rio Taquari direto da tela inicial.
            </span>
            <button type="button" onClick={installApp}>
              <Download size={15} aria-hidden="true" />
              Instalar aplicativo
            </button>
          </div>
        </aside>
      )}
      <div className="dashboard-shell">
        <section className="page-intro">
          <h1>Monitoramento</h1>
          {pushState !== "unsupported" && (
            <div className="push-actions">
              <button
                type="button"
                className={`push-toggle ${pushState === "subscribed" ? "active" : ""}`}
                onClick={togglePush}
                disabled={
                  pushState === "checking" ||
                  pushState === "working" ||
                  pushState === "blocked"
                }
                aria-pressed={pushState === "subscribed"}
                title={
                  pushState === "subscribed"
                    ? "Desativar alertas e boletins neste dispositivo"
                    : pushLabel
                }
              >
                <Bell size={16} aria-hidden="true" />
                <span>{pushLabel}</span>
              </button>
              {pushState === "subscribed" && (
                <button
                  type="button"
                  className="push-configure"
                  onClick={openPushPreferences}
                  disabled={pushPreferencesState === "loading"}
                >
                  <Settings2 size={16} aria-hidden="true" />
                  <span>Configurar alertas</span>
                </button>
              )}
            </div>
          )}
        </section>

        <section className="alerts-section" aria-label="Alertas ativos para Muçum e Vale do Taquari">
          <div className="alerts-heading">
            <AlertTriangle size={16} />
            <span>Alertas ativos</span>
          </div>
          <div className="alerts-list">
            {alertsLoadState === "loading" && !alerts.length ? (
              <p>Consultando Defesa Civil e INMET…</p>
            ) : alerts.length ? (
              alerts.map((alert) => (
                <button
                  type="button"
                  className={`alert-item ${alert.severity}`}
                  key={alert.id}
                  onClick={(event) => {
                    alertTriggerRef.current = event.currentTarget;
                    setSelectedAlert(alert);
                  }}
                  aria-haspopup="dialog"
                >
                  <span className="alert-copy">
                    <span className="alert-meta">
                      <span className="alert-severity">
                        {ALERT_SEVERITY_LABEL[alert.severity]}
                      </span>
                      <span className="alert-source">{alert.source}</span>
                    </span>
                    <span className="alert-title">
                      {alertDisplayTitle(alert.title)}
                    </span>
                  </span>
                  <time>Válido até {formatDate(alert.validUntil)}</time>
                  <Eye className="alert-open-icon" size={17} aria-hidden="true" />
                </button>
              ))
            ) : alertsLoadState === "error" ? (
              <p role="alert">
                {alertsStatusMessage ||
                  "Não foi possível consultar os alertas oficiais agora."} A
                coleta tentará novamente automaticamente.
              </p>
            ) : (
              <p>Nenhum alerta ativo para Muçum nas fontes consultadas.</p>
            )}
            {alertsLoadState === "error" && alerts.length > 0 && (
              <p role="status">
                {alertsStatusMessage || "A atualização falhou"} Os últimos
                alertas recebidos continuam visíveis.
              </p>
            )}
          </div>
        </section>

        {bulletins.length > 0 && (
          <section className="bulletins-strip" aria-label="Boletins">
            <div className="bulletins-heading">
              <FileText size={16} />
              <span>Boletins</span>
            </div>
            <div className="bulletin-strip-list">
              {bulletins.map((bulletin) => (
                <article
                  key={bulletin.id}
                  className={`bulletin-item ${bulletin.latest ? "latest" : ""}`}
                >
                  <span className="bulletin-file-icon" aria-hidden="true">
                    <FileText size={18} />
                  </span>
                  <span className="bulletin-copy">
                    <span className="bulletin-title">{bulletin.title}</span>
                  </span>
                  <time>{formatDate(bulletin.date)}</time>
                  <a
                    className="bulletin-view"
                    href={bulletin.href}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Visualizar ${bulletin.title}`}
                  >
                    <Eye size={15} />
                    Visualizar
                  </a>
                </article>
              ))}
            </div>
          </section>
        )}

        {selectedAlert && (
          <div
            className="alert-modal-backdrop"
            onMouseDown={() => setSelectedAlert(null)}
          >
            <section
              ref={alertDialogRef}
              className="alert-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="alert-modal-title"
              onMouseDown={(event) => event.stopPropagation()}
            >
              <header>
                <div>
                  <span className="alert-modal-badges">
                    <span className={`alert-severity ${selectedAlert.severity}`}>
                      {ALERT_SEVERITY_LABEL[selectedAlert.severity]}
                    </span>
                    <span className="alert-source">{selectedAlert.source}</span>
                  </span>
                  <h2 id="alert-modal-title">
                    {alertDisplayTitle(selectedAlert.title)}
                  </h2>
                </div>
                <button
                  ref={alertCloseButtonRef}
                  type="button"
                  onClick={() => setSelectedAlert(null)}
                  aria-label="Fechar alerta"
                >
                  <X size={20} />
                </button>
              </header>
              {selectedAlert.imageUrl ? (
                <div className="alert-image">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={selectedAlert.imageUrl}
                    alt={`Imagem oficial: ${alertDisplayTitle(selectedAlert.title)}`}
                  />
                </div>
              ) : (
                <div className="alert-no-image">
                  <AlertTriangle size={34} aria-hidden="true" />
                  <p>
                    Este aviso do {selectedAlert.source} não possui uma imagem
                    oficial. Consulte os detalhes diretamente na fonte.
                  </p>
                  <a
                    href={selectedAlert.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Abrir aviso oficial
                    <ExternalLink size={14} aria-hidden="true" />
                  </a>
                </div>
              )}
              <footer>
                <div className="alert-modal-summary">
                  <p>{selectedAlert.summary}</p>
                  <a
                    href={selectedAlert.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Fonte: {selectedAlert.source}
                    <ExternalLink size={12} aria-hidden="true" />
                  </a>
                </div>
                <time>Válido até {formatDate(selectedAlert.validUntil)}</time>
              </footer>
            </section>
          </div>
        )}

        {pushPreferencesOpen && (
          <div
            className="alert-modal-backdrop"
            onMouseDown={() => setPushPreferencesOpen(false)}
          >
            <section
              className="alert-modal alert-settings-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="alert-settings-title"
              onMouseDown={(event) => event.stopPropagation()}
            >
              <header>
                <div>
                  <h2 id="alert-settings-title">Configurar alertas</h2>
                </div>
                <button
                  type="button"
                  onClick={() => setPushPreferencesOpen(false)}
                  aria-label="Fechar configurações de alertas"
                >
                  <X size={20} />
                </button>
              </header>
              <div className="alert-settings-form">
                <div className="alert-rules-heading">
                  <div>
                    <strong>Regras deste dispositivo</strong>
                    <small>
                      Cada regra dispara uma vez e rearma quando o valor baixa.
                    </small>
                  </div>
                  <button type="button" onClick={addAlertRule}>
                    <Plus size={15} aria-hidden="true" />
                    Nova regra
                  </button>
                </div>
                <div className="alert-rules-list">
                  {alertRulesDraft.length ? (
                    alertRulesDraft.map((rule, index) => {
                      const sources = pushPreferences.sources.filter(
                        (source) => source.kind === rule.kind,
                      );
                      const selectedSource =
                        sources.find(
                          (source) => source.id === rule.sourceId,
                        ) || sources[0];
                      return (
                        <article
                          className={`alert-rule-card ${rule.severity}`}
                          key={rule.id}
                        >
                          <header>
                            <strong>Regra {index + 1}</strong>
                            <label className="alert-rule-enabled">
                              <input
                                type="checkbox"
                                checked={rule.enabled}
                                onChange={(event) =>
                                  updateAlertRule(rule.id, {
                                    enabled: event.target.checked,
                                  })
                                }
                              />
                              <span>{rule.enabled ? "Ativa" : "Pausada"}</span>
                            </label>
                            <button
                              type="button"
                              onClick={() => removeAlertRule(rule.id)}
                              aria-label={`Excluir regra ${index + 1}`}
                            >
                              <Trash2 size={15} />
                            </button>
                          </header>
                          <div className="alert-rule-grid">
                            <label>
                              <span>Monitorar</span>
                              <select
                                value={rule.kind}
                                onChange={(event) =>
                                  updateAlertRule(rule.id, {
                                    kind: event.target.value as AlertRuleKind,
                                  })
                                }
                              >
                                {Object.entries(ALERT_KIND_LABEL).map(
                                  ([value, label]) => (
                                    <option value={value} key={value}>
                                      {label}
                                    </option>
                                  ),
                                )}
                              </select>
                            </label>
                            <label className="alert-rule-source">
                              <span>Fonte e localidade</span>
                              <select
                                value={rule.sourceId}
                                onChange={(event) =>
                                  updateAlertRule(rule.id, {
                                    sourceId: event.target.value,
                                  })
                                }
                              >
                                {sources.map((source) => (
                                  <option value={source.id} key={source.id}>
                                    {source.location} — {source.name}
                                  </option>
                                ))}
                              </select>
                            </label>
                            {rule.kind === "rain_accumulation" && (
                              <label>
                                <span>Janela acumulada</span>
                                <select
                                  value={rule.windowHours || 24}
                                  onChange={(event) =>
                                    updateAlertRule(rule.id, {
                                      windowHours: Number(
                                        event.target.value,
                                      ) as AlertRule["windowHours"],
                                    })
                                  }
                                >
                                  {WINDOWS.map((hours) => (
                                    <option value={hours} key={hours}>
                                      {hours} horas
                                    </option>
                                  ))}
                                </select>
                              </label>
                            )}
                            <label>
                              <span>Valor de disparo</span>
                              <span className="alert-rule-value">
                                <input
                                  type="number"
                                  inputMode="decimal"
                                  min="0.01"
                                  step="0.01"
                                  value={
                                    Number.isFinite(rule.threshold)
                                      ? rule.threshold
                                      : ""
                                  }
                                  onChange={(event) =>
                                    updateAlertRule(rule.id, {
                                      threshold:
                                        event.target.value === ""
                                          ? Number.NaN
                                          : Number(event.target.value),
                                    })
                                  }
                                />
                                <strong>{selectedSource?.unit || ""}</strong>
                              </span>
                            </label>
                            <label className="alert-rule-severity">
                              <span>Nível do alerta</span>
                              <select
                                value={rule.severity}
                                onChange={(event) =>
                                  updateAlertRule(rule.id, {
                                    severity: event.target
                                      .value as AlertRuleSeverity,
                                  })
                                }
                              >
                                {ALERT_SEVERITY_OPTION.map((option) => (
                                  <option
                                    value={option.value}
                                    key={option.value}
                                  >
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            </label>
                          </div>
                        </article>
                      );
                    })
                  ) : (
                    <div className="alert-rules-empty">
                      <Bell size={20} aria-hidden="true" />
                      <p>Nenhuma regra configurada neste dispositivo.</p>
                      <button type="button" onClick={addAlertRule}>
                        Criar primeira regra
                      </button>
                    </div>
                  )}
                </div>
                <p className="alert-severity-help">
                  <strong>Atenção</strong> e <strong>Alerta</strong> não tocam
                  sirene. Somente regras de <strong>Emergência</strong> ativam
                  o alarme persistente e a vibração.
                </p>
                <div className="alarm-test">
                  <button
                    type="button"
                    onClick={testAlarm}
                    disabled={alarmTestCountdown !== null}
                  >
                    <BellRing size={17} aria-hidden="true" />
                    {alarmTestCountdown === null
                      ? "Testar alarme"
                      : alarmTestCountdown === 0
                        ? "Agendando..."
                      : `Alarme em ${alarmTestCountdown}s`}
                  </button>
                  {alarmTestMessage ? (
                    <small role="status">{alarmTestMessage}</small>
                  ) : null}
                </div>
              </div>
              <footer className="alert-settings-footer">
                <span role="status">
                  {pushPreferencesState === "saved"
                    ? `${alertRulesDraft.length} regra(s) salva(s).`
                    : pushPreferencesState === "error"
                      ? "Não foi possível salvar. Confira as fontes e os valores."
                      : pushPreferencesState === "loading"
                        ? "Carregando configurações…"
                        : ""}
                </span>
                <button
                  type="button"
                  onClick={savePushPreferences}
                  disabled={pushPreferencesState === "saving"}
                >
                  {pushPreferencesState === "saving"
                    ? "Salvando…"
                    : "Salvar configurações"}
                </button>
              </footer>
            </section>
          </div>
        )}

        <section
          className="panel river-monitoring-panel"
          id="niveis-do-rio"
        >
          <ModuleHeader
            title="Níveis do rio"
            action={
              <WindowSelector
                value={chartHours}
                onChange={setChartHours}
                options={RIVER_WINDOWS}
              />
            }
          />
          <div className="river-city-grid">
            {riverGroups.map((group) => (
              <article className="river-city-card" key={group.city}>
                <div className="river-city-heading">
                  <h3>{group.city}</h3>
                  {group.city === "Muçum" && (
                    <a
                      className="contingency-plan-link"
                      href={MUCUM_CONTINGENCY_PLAN_URL}
                      target="_blank"
                      rel="noreferrer"
                      aria-label="Visualizar Plano de Contingência de Muçum"
                    >
                      <Eye size={14} />
                      Plano de contingência
                    </a>
                  )}
                </div>
                <div className="river-sensor-stack">
                  {group.sensors.map((sensor) => {
                    const isRealtimeDcrs = sensor.id === "dcrs-00091";
                    const realtimeReadingAge = sensor.current
                      ? freshnessNow - Date.parse(sensor.current.timestamp)
                      : Number.POSITIVE_INFINITY;
                    const isRealtimeActive =
                      isRealtimeDcrs &&
                      (connection === "live" || connection === "polling") &&
                      Number.isFinite(realtimeReadingAge) &&
                      realtimeReadingAge >= -30_000 &&
                      realtimeReadingAge <= 90_000;
                    const chartPoints = isRealtimeDcrs
                      ? sampleLatestPointPerInterval(
                          latestContinuousSegment(sensor.history, 30),
                          15,
                        )
                      : sensor.history;
                    const oneHourChange = calculateOneHourMetricChange(
                      sensor.current
                        ? {
                            timestamp: sensor.current.timestamp,
                            value: sensor.current.level,
                          }
                        : null,
                      sensor.history.map((point) => ({
                        timestamp: point.timestamp,
                        value: point.level,
                      })),
                    );
                    const trendDirection = resolveMetricTrend(
                      oneHourChange,
                      isRealtimeDcrs ? current?.trend : null,
                    );
                    const trend =
                      trendDirection === "rising"
                        ? {
                            label: "Subindo",
                            icon: <ArrowUpRight size={15} />,
                            className: "rising",
                          }
                        : trendDirection === "falling"
                          ? {
                              label: "Baixando",
                              icon: <ArrowDownRight size={15} />,
                              className: "falling",
                            }
                          : {
                              label: "Estável",
                              icon: <Waves size={15} />,
                              className: "stable",
                            };

                    return (
                      <section className="river-sensor-card" key={sensor.id}>
                        <div className="river-sensor-summary">
                          <span className="river-sensor-name">
                            <span>{sensor.name}</span>
                            {isRealtimeActive && (
                              <span
                                className="realtime-indicator"
                                role="status"
                                aria-label="Atualizando em tempo real"
                                title="Atualizando em tempo real"
                              >
                                <span aria-hidden="true" />
                              </span>
                            )}
                          </span>
                          <div className="level-value">
                            <AnimatedNumber
                              value={sensor.current?.level}
                              digits={2}
                              readingKey={sensor.current?.timestamp}
                            />
                            <span>m</span>
                          </div>
                          <div className={`trend-pill ${trend.className}`}>
                            {trend.icon}
                            <span>{trend.label}</span>
                            <small>
                              {oneHourChange === null
                                ? isRealtimeDcrs
                                  ? "tendência em tempo real"
                                  : "1h indisponível"
                                : `${formatOneHourLevelChange(oneHourChange)} última hora`}
                            </small>
                          </div>
                          <time className="river-time">
                            {formatDate(
                              sensor.current?.timestamp,
                              true,
                              isRealtimeDcrs,
                            )}
                          </time>
                          {sensor.thresholds && (
                            <RiverThresholdLegend
                              thresholds={sensor.thresholds}
                            />
                          )}
                        </div>
                        <div className="river-sensor-chart">
                          <RiverChart
                            points={chartPoints}
                            hours={chartHours}
                            compact
                            fitAvailableRange={isRealtimeDcrs}
                            label={`Evolução do nível no ${sensor.name}, ${group.city}, nas últimas ${chartHours} horas`}
                          />
                        </div>
                      </section>
                    );
                  })}
                </div>
              </article>
            ))}
          </div>
          {currentError && (
            <div className="inline-error">
              <AlertTriangle size={15} />
              {currentError}
            </div>
          )}
        </section>

        <SynchronizedWeatherPanels
          radarRefreshToken={liveVersions.radar}
          concordiaRefreshToken={liveVersions["radar-sc"]}
          satelliteRefreshToken={liveVersions.satellite}
        />

        <section
          className="map-bulletin-grid single-panel"
          id="chuva-acumulada"
        >
          <article className="panel map-panel">
            <ModuleHeader
              title="Chuva acumulada"
              action={
                <WindowSelector
                  value={rainHours}
                  onChange={(hours) => {
                    setRainHours(hours);
                  }}
                  label="Janela de chuva acumulada"
                />
              }
            />
            <ExpandableRainMap stations={stations} hours={rainHours} />
            <div className="map-legend">
              <span><i className="rain-low" /> Fraca &lt; 50 mm</span>
              <span><i className="rain-watch" /> Atenção 50–80 mm</span>
              <span><i className="rain-critical" /> Crítica &gt; 80 mm</span>
            </div>
          </article>
        </section>

        <section className="panel ceran-panel" id="hidreletricas">
          <ModuleHeader
            title="Barragens"
          />
          <div className="ceran-grid">
            {CERAN_PLANTS.map(({ id, name, city }) => {
              const plantData = ceranPlants[id];
              const outflowChange = calculateOneHourMetricChange(
                plantData?.current
                  ? {
                      timestamp: plantData.current.timestamp,
                      value: plantData.current.outflow,
                    }
                  : null,
                (plantData?.history || []).map((row) => ({
                  timestamp: row.timestamp,
                  value: row.outflow,
                })),
              );
              const outflowTrend =
                outflowChange !== null && outflowChange >= 0.01
                  ? {
                      label: "Subindo",
                      icon: <ArrowUpRight size={15} />,
                      className: "rising",
                    }
                  : outflowChange !== null && outflowChange <= -0.01
                    ? {
                        label: "Baixando",
                        icon: <ArrowDownRight size={15} />,
                        className: "falling",
                      }
                    : {
                        label: "Estável",
                        icon: <Waves size={15} />,
                        className: "stable",
                      };
              return (
                <article className="plant-card" key={id}>
                  <h3>
                    <span>{plantData?.plant.name || name}</span>
                    <small>{city}</small>
                  </h3>
                  <div className="plant-current">
                    <span>Vazão defluente</span>
                    <strong>
                      {formatNumber(plantData?.current?.outflow)}
                      <small> m³/s</small>
                    </strong>
                    <div className={`trend-pill plant-trend ${outflowTrend.className}`}>
                      {outflowTrend.icon}
                      <span>{outflowTrend.label}</span>
                      <small>
                        {outflowChange === null
                          ? "1h indisponível"
                          : `${outflowChange > 0 ? "+" : outflowChange < 0 ? "−" : ""}${formatAdaptiveNumber(Math.abs(outflowChange), 2)} m³/s última hora`}
                      </small>
                    </div>
                    <time>{formatDate(plantData?.current?.timestamp)}</time>
                  </div>
                  <DamOutflowChart
                    rows={plantData?.history || []}
                    plantName={plantData?.plant.name || name}
                  />
                </article>
              );
            })}
          </div>
        </section>

        <section className="manifesto" aria-labelledby="manifesto-title">
          <div className="manifesto-heading">
            <h2 id="manifesto-title">Informação clara também protege.</h2>
          </div>

          <div className="manifesto-body">
            <p>
              Em momentos de risco, informações importantes ficam espalhadas
              entre diferentes sites e redes sociais. Conteúdos antigos também
              podem reaparecer como se fossem atuais, gerando dúvida e
              preocupação.
            </p>
            <p>
              Este sistema reúne, em um só lugar, dados atualizados sobre rios,
              chuva, barragens, alertas, radar e satélite. As informações vêm da
              ANA/SNIRH, SACE/SGB, Defesa Civil do RS, CERAN, INMET, CPTEC/INPE,
              Climatempo e Epagri/Ciram.
            </p>
            <p>
              É uma ferramenta de apoio para facilitar o acesso à informação.
              Em uma emergência, siga sempre as orientações oficiais.
            </p>
          </div>

          <p className="manifesto-signature">Bruno Zilio</p>
        </section>

      </div>
    </main>
  );
}
