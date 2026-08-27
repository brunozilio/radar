import { createHash } from "node:crypto";
import {
  mkdirSync,
  readFileSync,
} from "node:fs";
import path from "node:path";
import type { SQLInputValue } from "node:sqlite";
import sharp from "sharp";
import { createWorker, OEM } from "tesseract.js";
import WebSocket, { WebSocketServer } from "ws";
import {
  extractDefenseCivilAlertCandidates,
  extractDefenseCivilImage,
  isDefenseCivilAlertRelevant,
  parseDefenseCivilArticle,
} from "../lib/alerts.ts";
import {
  INMET_MUCUM_GEOCODE,
  parseInmetAlerts,
} from "../lib/inmet-alerts.ts";
import {
  ASSET_DIRECTORY,
  DATA_DIRECTORY,
  MEDIA_DIRECTORY,
  openWriterDatabase,
} from "../lib/database.ts";
import {
  deleteStoredObject,
  deleteStoredObjectByKey,
  listStoredObjects,
  objectStorageEnabled,
  putStoredObject,
  storedObjectExists,
  storedObjectReference,
  type StoredObjectMetadata,
} from "../lib/object-storage.ts";
import {
  dcrsHistoricQuery,
  parseDcrsHistoric,
} from "../lib/dcrs-history.ts";
import {
  accumulatedRain,
  parseAnaRecords,
  parseSaceLevelRows,
  MUCUM_UPSTREAM_RAIN_STATIONS,
  SACE_LEVEL_SENSORS,
  saoPauloDate,
} from "../lib/hydro.ts";
import type {
  AlertRainWindow,
  AlertRuleKind,
} from "../lib/alert-rules.ts";
import { extractRealtimeLevel } from "../lib/realtime.ts";
import {
  CERAN_PLANT_SOURCES,
  cptecSatelliteTimestamp,
  epagriRadarTimestamp,
  inmetSatelliteTimestamp,
  parseCeranTable,
  parseRadarTimestampText,
  parseSaceBulletins,
} from "../lib/sources.ts";

const database = openWriterDatabase();
const livePort = Number(process.env.LIVE_WS_PORT || 3001);
const liveServer = new WebSocketServer({ port: livePort });
const timers: NodeJS.Timeout[] = [];
let stopped = false;
let dcrsSocket: WebSocket | null = null;
let dcrsRetry: NodeJS.Timeout | null = null;
const tesseractCache = path.join(DATA_DIRECTORY, "tesseract");
mkdirSync(tesseractCache, { recursive: true });
const radarOcrWorker = createWorker("eng", OEM.LSTM_ONLY, {
  cachePath: tesseractCache,
});
let ocrQueue: Promise<void> = Promise.resolve();
const defenseCivilCardTextCache = new Map<string, string>();

const RADAR_BASE =
  "https://statics.climatempo.com.br/radar_poa/pngs/latest";
const EPAGRI_RADAR_BASE =
  "https://ciram.epagri.sc.gov.br/radar/rest/radar";
const EPAGRI_RADAR_KIND = "radar-concordia";
const EPAGRI_RADAR_CODE = "CHP";
const EPAGRI_RADAR_PRODUCT = "0";
const EPAGRI_RADAR_REGION_VERSION = "basin-overlay-v2";
const EPAGRI_RADAR_SOURCE_EXTENT = {
  left: -55.0710069,
  bottom: -29.2106056,
  right: -50.1335368,
  top: -24.8625699,
};
const EPAGRI_RADAR_VIEW_EXTENT = {
  ...EPAGRI_RADAR_SOURCE_EXTENT,
  bottom: -29.45,
};
const EPAGRI_RADAR_WIDTH = 859;
const EPAGRI_RADAR_HEIGHT = 758;
const INMET_API = "https://apisat.inmet.gov.br";
const INMET_ALERTS_SOURCE =
  "https://apiprevmet3.inmet.gov.br/avisos/ativos";
const INMET_SATELLITE_PRODUCT = "TN";
const INMET_SATELLITE_KIND = "satellite-enhanced";
const CPTEC_SATELLITE_LOGS =
  "https://sigma.cptec.inpe.br/logs/1222/20";
const CPTEC_SATELLITE_MAP =
  "https://maps.cptec.inpe.br/mapserv";
const CPTEC_SATELLITE_REGION_VERSION = "taquari-v2";
const BULLETINS_SOURCE =
  "https://www.sgb.gov.br/sace/boletins.php?idbacia=9";
const ALERTS_SOURCE =
  "https://www.defesacivil.rs.gov.br/_service/conteudo/pagedlistfilho";
const ANA_ENDPOINT =
  "https://www.ana.gov.br/telemetria1ws/ServiceANA.asmx/DadosHidrometeorologicosGerais";
const DCRS_ENDPOINT =
  "wss://redehidrometeorologica.defesacivil.rs.gov.br/graphql";
const DCRS_HTTP_ENDPOINT =
  "https://redehidrometeorologica.defesacivil.rs.gov.br/graphql";
const DCRS_STATION = "DCRS-00091";
const DCRS_CLIENT = "casa-militar-defesa-civil-rs";
const DCRS_OFFSET = -32.7;
const DATABASE_STORAGE_URL =
  process.env.DATABASE_STORAGE_URL || "";
const PERSISTENCE_SCHEMA_VERSION = "d1-r2-v1";
const HYDRO_PERSIST_URL = process.env.HYDRO_PERSIST_URL || "";
const PUSH_DISPATCH_URL = process.env.PUSH_DISPATCH_URL || "";
const PUSH_INTERNAL_SECRET = process.env.PUSH_INTERNAL_SECRET || "";
const MAX_PDF_BYTES = 30 * 1024 * 1024;
const MAX_ALERT_IMAGE_BYTES = 12 * 1024 * 1024;
let d1MutationQueue: Promise<void> = Promise.resolve();

type D1Parameter = string | number | null;
type D1Command = {
  sql: string;
  params?: D1Parameter[];
};

async function withD1Mutation<T>(job: () => Promise<T>) {
  const task = d1MutationQueue.then(job);
  d1MutationQueue = task.then(
    () => undefined,
    () => undefined,
  );
  return task;
}

async function runD1Batch(commands: D1Command[]) {
  if (!DATABASE_STORAGE_URL || !commands.length) {
    return [] as Array<{
      results: Array<Record<string, unknown>>;
      success: boolean;
      meta: { changes?: number };
    }>;
  }
  const response = await fetch(DATABASE_STORAGE_URL, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ statements: commands }),
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) {
    throw new Error(
      `D1 respondeu HTTP ${response.status}: ` +
        (await response.text()).slice(0, 300),
    );
  }
  const payload = (await response.json()) as {
    results?: Array<{
      results?: Array<Record<string, unknown>>;
      success?: boolean;
      meta?: { changes?: number };
    }>;
  };
  return (payload.results || []).map((result) => ({
    results: result.results || [],
    success: Boolean(result.success),
    meta: result.meta || {},
  }));
}

async function runD1Commands(commands: D1Command[]) {
  const results = [];
  for (let index = 0; index < commands.length; index += 100) {
    results.push(
      ...(await runD1Batch(commands.slice(index, index + 100))),
    );
  }
  return results;
}

function mediaObjectKey(id: string) {
  return `media/${id}`;
}

function assetObjectKey(id: string) {
  return `assets/${id}`;
}

function alertImageObjectKey(ownerId: string) {
  return `alert-images/${createHash("sha256").update(ownerId).digest("hex")}`;
}

async function storeMediaObject({
  id,
  extension,
  bytes,
  mimeType,
  kind,
  capturedAt,
  sourceUrl,
  sourceKey,
  createdAt,
}: {
  id: string;
  extension: string;
  bytes: Buffer;
  mimeType: string;
  kind: "radar" | "radar-concordia" | "satellite-enhanced";
  capturedAt: string;
  sourceUrl: string;
  sourceKey: string;
  createdAt: string;
}) {
  return putStoredObject({
    key: mediaObjectKey(id),
    bytes,
    mimeType,
    localPath: path.join(MEDIA_DIRECTORY, `${id}.${extension}`),
    metadata: {
      schema: "media-v1",
      id,
      kind,
      capturedAt,
      sourceUrl,
      sourceKey,
      createdAt,
    },
  });
}

async function storeAssetObject({
  id,
  extension,
  bytes,
  mimeType,
  ownerType,
  ownerId,
  fileName,
  sourceUrl,
  createdAt,
}: {
  id: string;
  extension: string;
  bytes: Buffer;
  mimeType: string;
  ownerType: StoredAssetOwner;
  ownerId: string;
  fileName: string;
  sourceUrl: string;
  createdAt: string;
}) {
  const metadata: StoredObjectMetadata = {
    schema: "asset-v1",
    id,
    ownerType,
    ownerId,
    fileName,
    sourceUrl,
    createdAt,
  };
  const reference = await putStoredObject({
    key: assetObjectKey(id),
    bytes,
    mimeType,
    localPath: path.join(ASSET_DIRECTORY, `${id}.${extension}`),
    metadata,
  });
  if (objectStorageEnabled() && ownerType === "alert-image") {
    await putStoredObject({
      key: alertImageObjectKey(ownerId),
      bytes,
      mimeType,
      localPath: path.join(ASSET_DIRECTORY, `${id}.${extension}`),
      metadata,
    });
  }
  return reference;
}

const DCRS_SUBSCRIPTION = `
subscription NivelDoRioEmTempoReal {
  nowcasting_unique(clients: ["${DCRS_CLIENT}"]) {
    qualle_meteorologia {
      codigo
      timestamp
      data {
        rio {
          rio_nivel { value }
          rio_nivel_tendencia { value }
        }
      }
    }
  }
}`;

function nowIso() {
  return new Date().toISOString();
}

type PushDispatch = {
  type: "alert" | "bulletin" | "metric";
  id: string;
  title: string;
  body: string;
  url: string;
  severity?: "yellow" | "orange" | "red";
  metricKind?: AlertRuleKind;
  sourceId?: string;
  sourceName?: string;
  value?: number;
  windowHours?: AlertRainWindow | null;
};

type AlertTarget = {
  kind: AlertRuleKind;
  sourceId: string;
  windowHours: AlertRainWindow | null;
};

let alertTargetsCache:
  | { expiresAt: number; targets: AlertTarget[] }
  | undefined;

type PersistentRiverReading = {
  station: string;
  timestamp: string;
  level: number;
  rawLevel: number | null;
  trendValue: number | null;
  trend: "rising" | "falling" | "stable";
  source: string;
  createdAt: string;
};

async function persistRiverReadings(readings: PersistentRiverReading[]) {
  if (
    !HYDRO_PERSIST_URL ||
    !PUSH_INTERNAL_SECRET ||
    !readings.length
  ) {
    return;
  }
  const response = await fetch(HYDRO_PERSIST_URL, {
    method: "POST",
    cache: "no-store",
    headers: {
      authorization: `Bearer ${PUSH_INTERNAL_SECRET}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({ readings }),
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) {
    throw new Error(`Persistência DCRS: HTTP ${response.status}`);
  }
}

async function synchronizePersistentRiverHistory() {
  if (!HYDRO_PERSIST_URL || !PUSH_INTERNAL_SECRET) return;
  try {
    const response = await fetch(HYDRO_PERSIST_URL, {
      cache: "no-store",
      headers: {
        authorization: `Bearer ${PUSH_INTERNAL_SECRET}`,
      },
      signal: AbortSignal.timeout(20_000),
    });
    if (!response.ok) {
      throw new Error(`restauração HTTP ${response.status}`);
    }
    const payload = (await response.json()) as {
      readings?: PersistentRiverReading[];
    };
    let restored = 0;
    for (const reading of payload.readings || []) {
      restored += Number(
        insertRiverReading.run(
          reading.station,
          reading.timestamp,
          reading.level,
          reading.rawLevel,
          reading.trendValue,
          reading.trend,
          reading.source,
          reading.createdAt,
        ).changes,
      );
    }

    const local = database
      .prepare(`
        SELECT station, timestamp, level, raw_level, trend_value, trend, source,
               created_at
        FROM river_readings
        WHERE station = ?
          AND level IS NOT NULL
          AND julianday(timestamp) >= julianday(?, '-48 hours')
        ORDER BY julianday(timestamp) ASC
      `)
      .all(DCRS_STATION, nowIso()) as Array<{
      station: string;
      timestamp: string;
      level: number;
      raw_level: number | null;
      trend_value: number | null;
      trend: PersistentRiverReading["trend"];
      source: string;
      created_at: string;
    }>;
    for (let index = 0; index < local.length; index += 500) {
      await persistRiverReadings(
        local.slice(index, index + 500).map((reading) => ({
          station: reading.station,
          timestamp: reading.timestamp,
          level: reading.level,
          rawLevel: reading.raw_level,
          trendValue: reading.trend_value,
          trend: reading.trend,
          source: reading.source,
          createdAt: reading.created_at,
        })),
      );
    }
    console.log(
      `[worker] DCRS-00091: ${restored} leitura(s) restaurada(s) do armazenamento persistente`,
    );
  } catch (error) {
    console.error(
      "[worker] DCRS-00091: sincronização persistente indisponível:",
      error instanceof Error ? error.message : error,
    );
  }
}

async function dispatchPush(event: PushDispatch) {
  if (!PUSH_DISPATCH_URL || !PUSH_INTERNAL_SECRET) return;
  try {
    const response = await fetch(PUSH_DISPATCH_URL, {
      method: "POST",
      cache: "no-store",
      headers: {
        authorization: `Bearer ${PUSH_INTERNAL_SECRET}`,
        "content-type": "application/json",
      },
      body: JSON.stringify(event),
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    console.error(
      `[worker] Web Push ${event.type} ${event.id}:`,
      error instanceof Error ? error.message : error,
    );
  }
}

async function alertTargets(kind: AlertRuleKind) {
  if (!PUSH_DISPATCH_URL || !PUSH_INTERNAL_SECRET) return [];
  if (!alertTargetsCache || alertTargetsCache.expiresAt <= Date.now()) {
    const url = new URL("/api/push/targets", PUSH_DISPATCH_URL);
    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        authorization: `Bearer ${PUSH_INTERNAL_SECRET}`,
      },
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) {
      throw new Error(`Destinos de alertas: HTTP ${response.status}`);
    }
    const payload = (await response.json()) as {
      targets?: AlertTarget[];
    };
    alertTargetsCache = {
      expiresAt: Date.now() + 15_000,
      targets: Array.isArray(payload.targets) ? payload.targets : [],
    };
  }
  return alertTargetsCache.targets.filter((target) => target.kind === kind);
}

function broadcast(type: string, payload: unknown) {
  const message = JSON.stringify({ type, payload, sentAt: nowIso() });
  for (const client of liveServer.clients) {
    if (client.readyState === WebSocket.OPEN) client.send(message);
  }
}

const latestMediaTimestamp = database.prepare(`
  SELECT captured_at
  FROM media_frames
  WHERE kind = ?
  ORDER BY julianday(captured_at) DESC
  LIMIT 1
`);

function broadcastMediaUpdate(
  type: "radar" | "radar-sc" | "satellite",
  kind: "radar" | "radar-concordia" | "satellite-enhanced",
  insertedFrames: number,
) {
  if (!insertedFrames) return;
  const latest = latestMediaTimestamp.get(kind) as
    | { captured_at: string }
    | undefined;
  const payload = {
    inserted: insertedFrames,
    latestTimestamp: latest?.captured_at || null,
    storage: objectStorageEnabled() ? "r2" : "local",
  };
  console.log(
    `[worker] ${type}: ${insertedFrames} novo(s) quadro(s); ` +
      `mais recente ${payload.latestTimestamp || "indisponível"}`,
  );
  broadcast(type, payload);
}

function inserted(
  statement: ReturnType<typeof database.prepare>,
  ...values: SQLInputValue[]
) {
  return Number(statement.run(...values).changes) > 0;
}

const insertMedia = database.prepare(`
  INSERT OR IGNORE INTO media_frames
    (id, kind, captured_at, file_path, mime_type, source_url, source_key, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);
const hasMediaSource = database.prepare(
  "SELECT 1 FROM media_frames WHERE source_key = ? LIMIT 1",
);
const hasMediaId = database.prepare(
  "SELECT 1 FROM media_frames WHERE id = ? LIMIT 1",
);
const storedAssetByOwner = database.prepare(`
  SELECT id, file_path, source_url
  FROM stored_assets
  WHERE owner_type = ? AND owner_id = ?
  LIMIT 1
`);
const upsertStoredAsset = database.prepare(`
  INSERT INTO stored_assets
    (id, owner_type, owner_id, file_path, file_name, mime_type, source_url,
     created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  ON CONFLICT(owner_type, owner_id) DO UPDATE SET
    id = excluded.id,
    file_path = excluded.file_path,
    file_name = excluded.file_name,
    mime_type = excluded.mime_type,
    source_url = excluded.source_url,
    created_at = excluded.created_at
`);
const updateMediaTimestamp = database.prepare(`
  UPDATE media_frames
  SET captured_at = ?
  WHERE source_key = ? AND captured_at <> ?
`);
const updateMediaFilePath = database.prepare(`
  UPDATE media_frames
  SET file_path = ?
  WHERE id = ?
`);
const updateAssetFilePath = database.prepare(`
  UPDATE stored_assets
  SET file_path = ?
  WHERE id = ?
`);

function validStoredDate(value: string | undefined) {
  return Boolean(value && Number.isFinite(Date.parse(value)));
}

async function restoreObjectStorageIndex() {
  if (!objectStorageEnabled()) return;

  const [mediaObjects, assetObjects] = await Promise.all([
    listStoredObjects("media/"),
    listStoredObjects("assets/"),
  ]);
  let restoredMedia = 0;
  let restoredAssets = 0;

  database.exec("BEGIN IMMEDIATE");
  try {
    for (const object of mediaObjects) {
      const metadata = object.customMetadata;
      const id = object.key.match(/^media\/([a-f0-9]{64})$/)?.[1];
      const mimeType = object.httpMetadata?.contentType;
      if (
        !id ||
        metadata?.schema !== "media-v1" ||
        metadata.id !== id ||
        !["radar", "radar-concordia", "satellite-enhanced"].includes(
          metadata.kind || "",
        ) ||
        !validStoredDate(metadata.capturedAt) ||
        !validStoredDate(metadata.createdAt) ||
        !metadata.sourceUrl ||
        !metadata.sourceKey ||
        !mimeType
      ) {
        continue;
      }
      restoredMedia += Number(
        insertMedia.run(
          id,
          metadata.kind,
          metadata.capturedAt,
          storedObjectReference(object.key),
          mimeType,
          metadata.sourceUrl,
          metadata.sourceKey,
          metadata.createdAt,
        ).changes,
      );
    }

    for (const object of assetObjects.sort(
      (left, right) =>
        Date.parse(left.customMetadata?.createdAt || "") -
        Date.parse(right.customMetadata?.createdAt || ""),
    )) {
      const metadata = object.customMetadata;
      const id = object.key.match(/^assets\/([a-f0-9]{64})$/)?.[1];
      const mimeType = object.httpMetadata?.contentType;
      if (
        !id ||
        metadata?.schema !== "asset-v1" ||
        metadata.id !== id ||
        (metadata.ownerType !== "alert-image" &&
          metadata.ownerType !== "bulletin-pdf") ||
        !metadata.ownerId ||
        !metadata.fileName ||
        !metadata.sourceUrl ||
        !validStoredDate(metadata.createdAt) ||
        !mimeType
      ) {
        continue;
      }
      upsertStoredAsset.run(
        id,
        metadata.ownerType,
        metadata.ownerId,
        storedObjectReference(object.key),
        metadata.fileName,
        mimeType,
        metadata.sourceUrl,
        metadata.createdAt,
      );
      restoredAssets += 1;
    }
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }

  console.log(
    `[worker] R2: índice persistente restaurado com ${restoredMedia} quadro(s) e ` +
      `${restoredAssets} arquivo(s)`,
  );
}

async function migrateLocalFilesToObjectStorage() {
  if (!objectStorageEnabled()) return;
  const mediaRows = database.prepare(`
    SELECT id, kind, captured_at, file_path, mime_type, source_url, source_key,
           created_at
    FROM media_frames
    WHERE file_path NOT LIKE 'r2:%'
  `).all() as Array<{
    id: string;
    kind: "radar" | "radar-concordia" | "satellite-enhanced";
    captured_at: string;
    file_path: string;
    mime_type: string;
    source_url: string;
    source_key: string;
    created_at: string;
  }>;
  const assetRows = database.prepare(`
    SELECT id, owner_type, owner_id, file_path, file_name, mime_type,
           source_url, created_at
    FROM stored_assets
    WHERE file_path NOT LIKE 'r2:%'
  `).all() as Array<{
    id: string;
    owner_type: StoredAssetOwner;
    owner_id: string;
    file_path: string;
    file_name: string;
    mime_type: string;
    source_url: string;
    created_at: string;
  }>;
  let migratedMedia = 0;
  let migratedAssets = 0;

  for (const row of mediaRows) {
    if (!(await storedObjectExists(row.file_path))) continue;
    const extension =
      path.extname(row.file_path).slice(1) ||
      (row.mime_type.includes("jpeg") ? "jpg" : "png");
    const reference = await storeMediaObject({
      id: row.id,
      extension,
      bytes: readFileSync(row.file_path),
      mimeType: row.mime_type,
      kind: row.kind,
      capturedAt: row.captured_at,
      sourceUrl: row.source_url,
      sourceKey: row.source_key,
      createdAt: row.created_at,
    });
    updateMediaFilePath.run(reference, row.id);
    await deleteStoredObject(row.file_path);
    migratedMedia += 1;
  }

  for (const row of assetRows) {
    if (!(await storedObjectExists(row.file_path))) continue;
    const extension =
      path.extname(row.file_path).slice(1) ||
      (row.mime_type === "application/pdf" ? "pdf" : "jpg");
    const reference = await storeAssetObject({
      id: row.id,
      extension,
      bytes: readFileSync(row.file_path),
      mimeType: row.mime_type,
      ownerType: row.owner_type,
      ownerId: row.owner_id,
      fileName: row.file_name,
      sourceUrl: row.source_url,
      createdAt: row.created_at,
    });
    updateAssetFilePath.run(reference, row.id);
    await deleteStoredObject(row.file_path);
    migratedAssets += 1;
  }

  console.log(
    `[worker] R2: migração inicial enviou ${migratedMedia} quadro(s) e ` +
      `${migratedAssets} arquivo(s)`,
  );
}

database.prepare(`
  UPDATE media_frames
  SET
    captured_at = strftime('%Y-%m-%dT%H:%M:%fZ', captured_at, '-3 hours'),
    source_key = replace(source_key, 'T03:00:00.000Z', '')
  WHERE kind = 'satellite-enhanced'
    AND source_key LIKE 'satellite:TN:%T03:00:00.000Z:%'
`).run();

type StoredAssetOwner = "alert-image" | "bulletin-pdf";

type StoredAssetResult = {
  id: string;
  created: boolean;
};

async function existingStoredAsset(
  ownerType: StoredAssetOwner,
  ownerId: string,
  expectedSourceUrl?: string,
) {
  const stored = storedAssetByOwner.get(ownerType, ownerId) as
    | { id: string; file_path: string; source_url: string }
    | undefined;
  return stored &&
    (!expectedSourceUrl || stored.source_url === expectedSourceUrl) &&
    (await storedObjectExists(stored.file_path))
    ? stored
    : null;
}

async function downloadStoredAsset({
  ownerType,
  ownerId,
  sourceUrl,
  kind,
  referer,
}: {
  ownerType: StoredAssetOwner;
  ownerId: string;
  sourceUrl: string;
  kind: "image" | "pdf";
  referer?: string;
}): Promise<StoredAssetResult | null> {
  const existing = await existingStoredAsset(
    ownerType,
    ownerId,
    sourceUrl,
  );
  if (existing) return { id: existing.id, created: false };

  try {
    const response = await fetch(sourceUrl, {
      cache: "no-store",
      headers: {
        accept:
          kind === "pdf"
            ? "application/pdf"
            : "image/png,image/jpeg,image/webp",
        "cache-control": "no-cache, no-store",
        pragma: "no-cache",
        ...(referer ? { referer } : {}),
        "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
      },
      signal: AbortSignal.timeout(kind === "pdf" ? 20_000 : 12_000),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const declaredLength = Number(response.headers.get("content-length") || 0);
    const maxBytes =
      kind === "pdf" ? MAX_PDF_BYTES : MAX_ALERT_IMAGE_BYTES;
    if (declaredLength > maxBytes) {
      throw new Error("arquivo acima do limite");
    }

    const bytes = Buffer.from(await response.arrayBuffer());
    if (!bytes.length || bytes.length > maxBytes) {
      throw new Error("arquivo vazio ou acima do limite");
    }

    const responseType = (
      response.headers.get("content-type") || ""
    ).split(";")[0].trim().toLocaleLowerCase();
    let mimeType: string;
    let extension: string;
    if (kind === "pdf") {
      if (!bytes.subarray(0, 5).equals(Buffer.from("%PDF-"))) {
        throw new Error("conteúdo não é PDF");
      }
      mimeType = "application/pdf";
      extension = "pdf";
    } else {
      if (!["image/jpeg", "image/png", "image/webp"].includes(responseType)) {
        throw new Error(`formato de imagem inválido: ${responseType || "ausente"}`);
      }
      const metadata = await sharp(bytes).metadata();
      if (!metadata.width || !metadata.height) {
        throw new Error("imagem inválida");
      }
      mimeType = responseType;
      extension =
        responseType === "image/png"
          ? "png"
          : responseType === "image/webp"
            ? "webp"
            : "jpg";
    }

    const id = createHash("sha256")
      .update(ownerType)
      .update("\0")
      .update(ownerId)
      .update("\0")
      .update(bytes)
      .digest("hex");
    const previous = storedAssetByOwner.get(ownerType, ownerId) as
      | { id: string; file_path: string }
      | undefined;
    const fileName =
      kind === "pdf" ? `boletim-${id.slice(0, 12)}.pdf` : `alerta-${id.slice(0, 12)}.${extension}`;
    const createdAt = nowIso();
    const filePath = await storeAssetObject({
      id,
      extension,
      bytes,
      mimeType,
      ownerType,
      ownerId,
      fileName,
      sourceUrl,
      createdAt,
    });
    upsertStoredAsset.run(
      id,
      ownerType,
      ownerId,
      filePath,
      fileName,
      mimeType,
      sourceUrl,
      createdAt,
    );
    if (previous?.file_path && previous.file_path !== filePath) {
      try {
        await deleteStoredObject(previous.file_path);
      } catch {
        // A nova cópia já está registrada; a limpeza tentará novamente depois.
      }
    }
    return { id, created: true };
  } catch (error) {
    console.error(
      `[worker] ${ownerType} ${ownerId}:`,
      error instanceof Error ? error.message : error,
    );
    return null;
  }
}

async function ensureBulletinPdf(id: string, href: string) {
  const url = new URL(href);
  if (
    url.protocol !== "https:" ||
    url.hostname !== "www.sgb.gov.br" ||
    !url.pathname.startsWith("/sace/boletins/Taquari/") ||
    !url.pathname.toLocaleLowerCase().endsWith(".pdf")
  ) {
    return null;
  }
  return downloadStoredAsset({
    ownerType: "bulletin-pdf",
    ownerId: id,
    sourceUrl: url.toString(),
    kind: "pdf",
  });
}

async function ensureAlertImage(
  id: string,
  href: string,
  articleHtml?: string,
  knownImageUrl?: string | null,
) {
  const pageUrl = new URL(href);
  if (
    pageUrl.protocol !== "https:" ||
    pageUrl.hostname !== "www.defesacivil.rs.gov.br"
  ) {
    return null;
  }
  try {
    const imageUrl =
      knownImageUrl ||
      extractDefenseCivilImage(
        articleHtml || (await fetchText(pageUrl.toString(), 10_000, true)),
        pageUrl.toString(),
      );
    if (!imageUrl) return null;
    return downloadStoredAsset({
      ownerType: "alert-image",
      ownerId: id,
      sourceUrl: imageUrl,
      kind: "image",
      referer: pageUrl.toString(),
    });
  } catch (error) {
    console.error(
      `[worker] alert-image ${id}:`,
      error instanceof Error ? error.message : error,
    );
    return null;
  }
}

const insertRiverReading = database.prepare(`
  INSERT OR IGNORE INTO river_readings
    (station, timestamp, level, raw_level, trend_value, trend, source, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

type RiverSeed = {
  station: string;
  source: string;
  datumOffset: number;
  exportedAt: string;
  readings: Array<{
    timestamp: string;
    level: number;
    rawLevel: number | null;
    trendValue: number | null;
    trend: "rising" | "falling" | "stable";
    createdAt: string;
  }>;
};

function seedDcrsHistory() {
  const seed = JSON.parse(
    readFileSync(
      new URL("./seeds/dcrs-00091.json", import.meta.url),
      "utf8",
    ),
  ) as RiverSeed;
  if (seed.station !== DCRS_STATION || seed.datumOffset !== DCRS_OFFSET) {
    throw new Error("Base inicial DCRS-00091 incompatível");
  }

  const now = Date.now();
  const retentionCutoff = now - 48 * 60 * 60 * 1000;
  const futureTolerance = now + 5 * 60 * 1000;
  let insertedRows = 0;

  database.exec("BEGIN IMMEDIATE");
  try {
    for (const reading of seed.readings) {
      const readingTime = Date.parse(reading.timestamp);
      if (
        !Number.isFinite(readingTime) ||
        readingTime < retentionCutoff ||
        readingTime > futureTolerance ||
        !Number.isFinite(reading.level)
      ) {
        continue;
      }
      insertedRows += Number(
        insertRiverReading.run(
          seed.station,
          reading.timestamp,
          reading.level,
          reading.rawLevel,
          reading.trendValue,
          reading.trend,
          seed.source,
          reading.createdAt || seed.exportedAt,
        ).changes,
      );
    }
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }

  const first = seed.readings.at(0)?.timestamp || "indisponível";
  const last = seed.readings.at(-1)?.timestamp || "indisponível";
  console.log(
    `[worker] DCRS-00091: base inicial ${insertedRows} nova(s) leitura(s), ` +
      `período ${first} — ${last}`,
  );
}

seedDcrsHistory();

const insertSaceReading = database.prepare(`
  INSERT OR IGNORE INTO sace_readings
    (station, timestamp, level, level_cm, created_at)
  VALUES (?, ?, ?, ?, ?)
`);
const insertRainReading = database.prepare(`
  INSERT OR IGNORE INTO rain_readings
    (station, timestamp, rain, level_cm, discharge, quality, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);
const insertCeranReading = database.prepare(`
  INSERT OR IGNORE INTO ceran_readings
    (plant_id, timestamp, upstream_level, downstream_level, inflow, turbined,
     spilled, residual, outflow, status, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);
const insertBulletin = database.prepare(`
  INSERT INTO bulletins
    (id, title, published_at, status, href, created_at)
  VALUES (?, ?, ?, ?, ?, ?)
  ON CONFLICT(id) DO UPDATE SET
    title = excluded.title,
    published_at = excluded.published_at,
    status = excluded.status,
    href = excluded.href,
    created_at = excluded.created_at
`);
const bulletinsAtPublishedTime = database.prepare(`
  SELECT id, href
  FROM bulletins
  WHERE published_at = ?
`);
const deleteBulletinsAtPublishedTime = database.prepare(`
  DELETE FROM bulletins
  WHERE published_at = ?
`);
const upsertAlert = database.prepare(`
  INSERT INTO alerts
    (id, title, summary, published_at, valid_until, severity, href, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  ON CONFLICT(id) DO UPDATE SET
    title = excluded.title,
    summary = excluded.summary,
    published_at = excluded.published_at,
    valid_until = excluded.valid_until,
    severity = excluded.severity,
    href = excluded.href
`);
const upsertSourceStatus = database.prepare(`
  INSERT INTO source_status (source, status, checked_at, message)
  VALUES (?, ?, ?, ?)
  ON CONFLICT(source) DO UPDATE SET
    status = excluded.status,
    checked_at = excluded.checked_at,
    message = excluded.message
`);

type AlertSourceId = "defesa-civil" | "inmet";

function recordAlertSourceStatus(
  source: AlertSourceId,
  status: "ok" | "error",
  message: string | null = null,
) {
  upsertSourceStatus.run(
    source,
    status,
    nowIso(),
    message ? message.slice(0, 500) : null,
  );
}

async function reconcileSourceAlerts(
  source: AlertSourceId,
  knownIds: string[],
) {
  const uniqueIds = [...new Set(knownIds)];
  // O gateway interno do D1 aceita no máximo 32 parâmetros por comando.
  if (uniqueIds.length > 31) {
    console.warn(
      `[worker] reconciliação ${source}: muitos IDs; mantendo registros existentes`,
    );
    return;
  }
  await withD1Mutation(async () => {
    const sourcePredicate =
      source === "inmet" ? "id LIKE 'inmet:%'" : "id NOT LIKE 'inmet:%'";
    const placeholders = uniqueIds.map(() => "?").join(", ");
    const sql = `
      DELETE FROM alerts
      WHERE ${sourcePredicate}
        AND valid_until > ?
        ${uniqueIds.length ? `AND id NOT IN (${placeholders})` : ""}
    `;
    const params = [nowIso(), ...uniqueIds];
    database.prepare(sql).run(...params);
    const results = await runD1Batch([{ sql, params }]);
    if (
      DATABASE_STORAGE_URL &&
      (results.length !== 1 || !results[0].success)
    ) {
      throw new Error(`reconciliação ${source} não foi confirmada no D1`);
    }
  });
}

type PersistentTableName =
  | "river_readings"
  | "sace_readings"
  | "rain_readings"
  | "ceran_readings";

const d1SyncWatermarks: Record<PersistentTableName, string> = {
  river_readings: new Date(
    Date.now() - 48 * 60 * 60 * 1000,
  ).toISOString(),
  sace_readings: new Date(
    Date.now() - 48 * 60 * 60 * 1000,
  ).toISOString(),
  rain_readings: new Date(
    Date.now() - 48 * 60 * 60 * 1000,
  ).toISOString(),
  ceran_readings: new Date(
    Date.now() - 48 * 60 * 60 * 1000,
  ).toISOString(),
};

async function restorePersistentDatabase() {
  if (!DATABASE_STORAGE_URL) return;
  const dataCutoff = new Date(
    Date.now() - 48 * 60 * 60 * 1000,
  ).toISOString();
  const now = nowIso();
  const results = await runD1Batch([
    {
      sql: `
        SELECT station, timestamp, level, raw_level, trend_value, trend,
               source, created_at
        FROM river_readings
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
      `,
      params: [dataCutoff],
    },
    {
      sql: `
        SELECT station, timestamp, level, level_cm, created_at
        FROM sace_readings
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
      `,
      params: [dataCutoff],
    },
    {
      sql: `
        SELECT station, timestamp, rain, level_cm, discharge, quality,
               created_at
        FROM rain_readings
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
      `,
      params: [dataCutoff],
    },
    {
      sql: `
        SELECT plant_id, timestamp, upstream_level, downstream_level, inflow,
               turbined, spilled, residual, outflow, status, created_at
        FROM ceran_readings
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
      `,
      params: [dataCutoff],
    },
    {
      sql: `
        SELECT id, title, published_at, status, href, created_at
        FROM bulletins
        WHERE published_at IS NOT NULL AND published_at >= ?
        ORDER BY published_at ASC
      `,
      params: [dataCutoff],
    },
    {
      sql: `
        SELECT id, title, summary, published_at, valid_until, severity, href,
               created_at
        FROM alerts
        WHERE valid_until > ?
        ORDER BY published_at ASC
      `,
      params: [now],
    },
  ]);
  if (results.length !== 6 || results.some((result) => !result.success)) {
    throw new Error("restauração D1 retornou um lote incompleto");
  }

  database.exec("BEGIN IMMEDIATE");
  try {
    for (const row of results[0].results) {
      insertRiverReading.run(
        row.station as string,
        row.timestamp as string,
        (row.level as number | null) ?? null,
        (row.raw_level as number | null) ?? null,
        (row.trend_value as number | null) ?? null,
        row.trend as string,
        row.source as string,
        row.created_at as string,
      );
    }
    for (const row of results[1].results) {
      insertSaceReading.run(
        row.station as string,
        row.timestamp as string,
        row.level as number,
        row.level_cm as number,
        row.created_at as string,
      );
    }
    for (const row of results[2].results) {
      insertRainReading.run(
        row.station as string,
        row.timestamp as string,
        (row.rain as number | null) ?? null,
        (row.level_cm as number | null) ?? null,
        (row.discharge as number | null) ?? null,
        row.quality as string,
        row.created_at as string,
      );
    }
    for (const row of results[3].results) {
      insertCeranReading.run(
        row.plant_id as string,
        row.timestamp as string,
        row.upstream_level as number,
        row.downstream_level as number,
        row.inflow as number,
        row.turbined as number,
        row.spilled as number,
        row.residual as number,
        row.outflow as number,
        row.status as string,
        row.created_at as string,
      );
    }
    for (const row of results[4].results) {
      insertBulletin.run(
        row.id as string,
        row.title as string,
        row.published_at as string,
        row.status as string,
        row.href as string,
        row.created_at as string,
      );
    }
    for (const row of results[5].results) {
      upsertAlert.run(
        row.id as string,
        row.title as string,
        row.summary as string,
        row.published_at as string,
        row.valid_until as string,
        row.severity as string,
        row.href as string,
        row.created_at as string,
      );
    }
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }

  console.log(
    `[worker] D1: cache restaurado com ` +
      `${results.slice(0, 4).reduce((total, result) => total + result.results.length, 0)} ` +
      `medição(ões), ${results[4].results.length} boletim(ns) e ` +
      `${results[5].results.length} alerta(s)`,
  );
}

function rowsCreatedSince<T extends Record<string, unknown>>(
  table: PersistentTableName,
) {
  return database
    .prepare(`
      SELECT *
      FROM ${table}
      WHERE julianday(created_at) > julianday(?)
      ORDER BY julianday(created_at) ASC
    `)
    .all(d1SyncWatermarks[table]) as T[];
}

async function synchronizePersistentDatabaseUnlocked() {
  if (!DATABASE_STORAGE_URL) return;
  const riverRows = rowsCreatedSince<{
    station: string;
    timestamp: string;
    level: number | null;
    raw_level: number | null;
    trend_value: number | null;
    trend: string;
    source: string;
    created_at: string;
  }>("river_readings");
  const saceRows = rowsCreatedSince<{
    station: string;
    timestamp: string;
    level: number;
    level_cm: number;
    created_at: string;
  }>("sace_readings");
  const rainRows = rowsCreatedSince<{
    station: string;
    timestamp: string;
    rain: number | null;
    level_cm: number | null;
    discharge: number | null;
    quality: string;
    created_at: string;
  }>("rain_readings");
  const ceranRows = rowsCreatedSince<{
    plant_id: string;
    timestamp: string;
    upstream_level: number;
    downstream_level: number;
    inflow: number;
    turbined: number;
    spilled: number;
    residual: number;
    outflow: number;
    status: string;
    created_at: string;
  }>("ceran_readings");
  const bulletinRows = database
    .prepare("SELECT * FROM bulletins")
    .all() as Array<{
    id: string;
    title: string;
    published_at: string | null;
    status: string;
    href: string;
    created_at: string;
  }>;
  const alertRows = database
    .prepare("SELECT * FROM alerts")
    .all() as Array<{
    id: string;
    title: string;
    summary: string;
    published_at: string;
    valid_until: string;
    severity: string;
    href: string;
    created_at: string;
  }>;

  const commands: D1Command[] = [
    ...riverRows.map((row) => ({
      sql: `
        INSERT OR REPLACE INTO river_readings
          (station, timestamp, level, raw_level, trend_value, trend, source,
           created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `,
      params: [
        row.station,
        row.timestamp,
        row.level,
        row.raw_level,
        row.trend_value,
        row.trend,
        row.source,
        row.created_at,
      ],
    })),
    ...saceRows.map((row) => ({
      sql: `
        INSERT OR REPLACE INTO sace_readings
          (station, timestamp, level, level_cm, created_at)
        VALUES (?, ?, ?, ?, ?)
      `,
      params: [
        row.station,
        row.timestamp,
        row.level,
        row.level_cm,
        row.created_at,
      ],
    })),
    ...rainRows.map((row) => ({
      sql: `
        INSERT OR REPLACE INTO rain_readings
          (station, timestamp, rain, level_cm, discharge, quality, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `,
      params: [
        row.station,
        row.timestamp,
        row.rain,
        row.level_cm,
        row.discharge,
        row.quality,
        row.created_at,
      ],
    })),
    ...ceranRows.map((row) => ({
      sql: `
        INSERT OR REPLACE INTO ceran_readings
          (plant_id, timestamp, upstream_level, downstream_level, inflow,
           turbined, spilled, residual, outflow, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `,
      params: [
        row.plant_id,
        row.timestamp,
        row.upstream_level,
        row.downstream_level,
        row.inflow,
        row.turbined,
        row.spilled,
        row.residual,
        row.outflow,
        row.status,
        row.created_at,
      ],
    })),
    ...bulletinRows.map((row) => ({
      sql: `
        INSERT OR REPLACE INTO bulletins
          (id, title, published_at, status, href, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
      `,
      params: [
        row.id,
        row.title,
        row.published_at,
        row.status,
        row.href,
        row.created_at,
      ],
    })),
    ...alertRows.map((row) => ({
      sql: `
        INSERT OR REPLACE INTO alerts
          (id, title, summary, published_at, valid_until, severity, href,
           created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `,
      params: [
        row.id,
        row.title,
        row.summary,
        row.published_at,
        row.valid_until,
        row.severity,
        row.href,
        row.created_at,
      ],
    })),
  ];

  const dataCutoff = new Date(
    Date.now() - 48 * 60 * 60 * 1000,
  ).toISOString();
  commands.push(
    ...([
      "river_readings",
      "sace_readings",
      "rain_readings",
      "ceran_readings",
    ] as const).map((table) => ({
      sql: `DELETE FROM ${table} WHERE timestamp < ?`,
      params: [dataCutoff],
    })),
    {
      sql: `
        DELETE FROM bulletins
        WHERE published_at IS NULL OR published_at < ?
      `,
      params: [dataCutoff],
    },
    {
      sql: "DELETE FROM alerts WHERE valid_until <= ?",
      params: [nowIso()],
    },
  );

  const results = await runD1Commands(commands);
  if (results.some((result) => !result.success)) {
    throw new Error("sincronização D1 retornou falha");
  }
  for (const [table, rows] of Object.entries({
    river_readings: riverRows,
    sace_readings: saceRows,
    rain_readings: rainRows,
    ceran_readings: ceranRows,
  }) as Array<[PersistentTableName, Array<{ created_at: string }>]>) {
    const latest = rows.at(-1)?.created_at;
    if (latest) d1SyncWatermarks[table] = latest;
  }
  const synchronized =
    riverRows.length +
    saceRows.length +
    rainRows.length +
    ceranRows.length +
    bulletinRows.length +
    alertRows.length;
  if (synchronized) {
    console.log(`[worker] D1: ${synchronized} registro(s) sincronizado(s)`);
  }
}

async function synchronizePersistentDatabase() {
  return withD1Mutation(synchronizePersistentDatabaseUnlocked);
}

async function fetchText(
  url: string,
  timeout = 10_000,
  cacheBust = false,
) {
  const requestUrl = new URL(url);
  if (cacheBust) {
    requestUrl.searchParams.set("_", Date.now().toString(36));
  }
  const response = await fetch(requestUrl, {
    cache: "no-store",
    headers: {
      accept: "text/html,text/plain,text/csv,application/xml",
      "cache-control": "no-cache, no-store",
      pragma: "no-cache",
      "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
    },
    signal: AbortSignal.timeout(timeout),
  });
  if (!response.ok) throw new Error(`${url} respondeu HTTP ${response.status}`);
  return response.text();
}

async function recognizeText(bytes: Buffer, whitelist = "") {
  const recognition = ocrQueue.then(async () => {
    const worker = await radarOcrWorker;
    await worker.setParameters({ tessedit_char_whitelist: whitelist });
    const result = await worker.recognize(bytes);
    return result.data.text;
  });
  ocrQueue = recognition.then(
    () => undefined,
    () => undefined,
  );
  return recognition;
}

async function readDefenseCivilCardText(
  alertId: string,
  imageUrl: string,
  referer: string,
) {
  const cacheKey = `${alertId}\0${imageUrl}`;
  const cached = defenseCivilCardTextCache.get(cacheKey);
  if (cached) return cached;

  try {
    const url = new URL(imageUrl);
    if (
      url.protocol !== "https:" ||
      !["defesacivil.rs.gov.br", "www.defesacivil.rs.gov.br"].includes(
        url.hostname,
      )
    ) {
      return "";
    }
    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        accept: "image/png,image/jpeg,image/webp",
        referer,
        "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
      },
      signal: AbortSignal.timeout(12_000),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const declaredLength = Number(response.headers.get("content-length") || 0);
    if (declaredLength > MAX_ALERT_IMAGE_BYTES) {
      throw new Error("imagem acima do limite");
    }
    const bytes = Buffer.from(await response.arrayBuffer());
    if (!bytes.length || bytes.length > MAX_ALERT_IMAGE_BYTES) {
      throw new Error("imagem vazia ou acima do limite");
    }

    const metadata = await sharp(bytes).metadata();
    if (!metadata.width || !metadata.height) throw new Error("imagem inválida");
    const top = Math.floor(metadata.height * 0.67);
    const crop = await sharp(bytes)
      .extract({
        left: 0,
        top,
        width: Math.max(1, Math.floor(metadata.width * 0.62)),
        height: Math.max(1, Math.min(
          metadata.height - top,
          Math.floor(metadata.height * 0.24),
        )),
      })
      .grayscale()
      .normalize()
      .resize({ width: 1_300 })
      .png()
      .toBuffer();
    const text = (
      await recognizeText(
        crop,
        "0123456789/ aAVIGENCIvigencia-",
      )
    ).trim();
    if (text) defenseCivilCardTextCache.set(cacheKey, text);
    return text;
  } catch (error) {
    console.error(
      `[worker] OCR alerta ${alertId}:`,
      error instanceof Error ? error.message : error,
    );
    return "";
  }
}

async function radarTimestamp(bytes: Buffer) {
  const metadata = await sharp(bytes).metadata();
  if (!metadata.width || !metadata.height) return null;
  const crop = await sharp(bytes)
    .extract({
      left: Math.floor(metadata.width * 0.59),
      top: Math.floor(metadata.height * 0.81),
      width: Math.floor(metadata.width * 0.34),
      height: Math.floor(metadata.height * 0.09),
    })
    .grayscale()
    .normalize()
    .resize({ width: 1_300 })
    .png()
    .toBuffer();
  return parseRadarTimestampText(
    await recognizeText(crop, "0123456789/: "),
  );
}

async function ingestRadar() {
  const cacheBust = Date.now().toString(36);
  const slots = await Promise.all(
    Array.from({ length: 24 }, async (_, offset) => {
      const index = offset + 1;
      const sourceUrl = `${RADAR_BASE}/radar_poa_${index}.png`;
      const requestUrl = `${sourceUrl}?_=${cacheBust}`;
      const response = await fetch(requestUrl, {
        method: "HEAD",
        cache: "no-store",
        headers: {
          "cache-control": "no-cache, no-store",
          pragma: "no-cache",
        },
        signal: AbortSignal.timeout(8_000),
      });
      if (!response.ok) throw new Error(`Radar ${index}: HTTP ${response.status}`);
      const etag = response.headers.get("etag")?.replaceAll('"', "");
      const modified = response.headers.get("last-modified") || "";
      return {
        index,
        sourceUrl,
        requestUrl,
        sourceKey: `radar:${etag || `${sourceUrl}:${modified}`}`,
        modifiedMs: Date.parse(modified),
      };
    }),
  );

  const candidates: Array<{
    id: string;
    bytes: Buffer;
    mimeType: string;
    sourceUrl: string;
    sourceKey: string;
    capturedAt: string;
  }> = [];
  const candidateIds = new Set<string>();

  for (const slot of slots.sort((a, b) => b.index - a.index)) {
    if (hasMediaSource.get(slot.sourceKey)) continue;
    const response = await fetch(slot.requestUrl, {
      cache: "no-store",
      headers: {
        "cache-control": "no-cache, no-store",
        pragma: "no-cache",
      },
      signal: AbortSignal.timeout(15_000),
    });
    if (!response.ok) continue;
    const bytes = Buffer.from(await response.arrayBuffer());
    const id = createHash("sha256").update(bytes).digest("hex");
    if (hasMediaId.get(id) || candidateIds.has(id)) continue;
    const capturedAt = await radarTimestamp(bytes);
    if (!capturedAt) {
      console.error(
        `[worker] radar: horário não reconhecido em ${slot.sourceUrl}`,
      );
      continue;
    }
    candidateIds.add(id);
    candidates.push({
      id,
      bytes,
      mimeType: response.headers.get("content-type") || "image/png",
      sourceUrl: slot.sourceUrl,
      sourceKey: slot.sourceKey,
      capturedAt,
    });
  }

  let changes = 0;
  for (const candidate of candidates.sort(
    (a, b) => Date.parse(a.capturedAt) - Date.parse(b.capturedAt),
  )) {
    const createdAt = nowIso();
    const filePath = await storeMediaObject({
      id: candidate.id,
      extension: "png",
      bytes: candidate.bytes,
      mimeType: candidate.mimeType,
      kind: "radar",
      capturedAt: candidate.capturedAt,
      sourceUrl: candidate.sourceUrl,
      sourceKey: candidate.sourceKey,
      createdAt,
    });
    if (
      inserted(
        insertMedia,
        candidate.id,
        "radar",
        candidate.capturedAt,
        filePath,
        candidate.mimeType,
        candidate.sourceUrl,
        candidate.sourceKey,
        createdAt,
      )
    ) {
      changes += 1;
    }
  }
  broadcastMediaUpdate("radar", "radar", changes);
}

let epagriBaseMapPromise: Promise<Buffer> | null = null;

function epagriBaseMap() {
  if (epagriBaseMapPromise) return epagriBaseMapPromise;
  const requestUrl = new URL(
    "https://server.arcgisonline.com/ArcGIS/rest/services/" +
      "Canvas/World_Light_Gray_Base/MapServer/export",
  );
  requestUrl.search = new URLSearchParams({
    bbox: [
      EPAGRI_RADAR_VIEW_EXTENT.left,
      EPAGRI_RADAR_VIEW_EXTENT.bottom,
      EPAGRI_RADAR_VIEW_EXTENT.right,
      EPAGRI_RADAR_VIEW_EXTENT.top,
    ].join(","),
    bboxSR: "4326",
    imageSR: "4326",
    size: `${EPAGRI_RADAR_WIDTH},${EPAGRI_RADAR_HEIGHT}`,
    format: "png32",
    f: "image",
  }).toString();
  epagriBaseMapPromise = fetch(requestUrl, {
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`Mapa-base do Radar SC: HTTP ${response.status}`);
    }
    return Buffer.from(await response.arrayBuffer());
  });
  epagriBaseMapPromise.catch(() => {
    epagriBaseMapPromise = null;
  });
  return epagriBaseMapPromise;
}

async function ingestEpagriRadar() {
  const listUrl = new URL(`${EPAGRI_RADAR_BASE}/getUltimasImagens`);
  listUrl.search = new URLSearchParams({
    prod: EPAGRI_RADAR_PRODUCT,
    radar: EPAGRI_RADAR_CODE,
    data: "",
    _: Date.now().toString(36),
  }).toString();
  const listResponse = await fetch(listUrl, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      "cache-control": "no-cache, no-store",
      pragma: "no-cache",
      "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
    },
    signal: AbortSignal.timeout(12_000),
  });
  if (!listResponse.ok) {
    throw new Error(`Radar SC respondeu HTTP ${listResponse.status}`);
  }
  const files = (await listResponse.json()) as string[];
  const baseMap = await epagriBaseMap();
  let changes = 0;

  for (const fileName of files) {
    const capturedAt = epagriRadarTimestamp(fileName);
    if (!capturedAt) continue;
    const sourceKey =
      `radar-sc:${EPAGRI_RADAR_CODE}:${EPAGRI_RADAR_PRODUCT}:` +
      `${EPAGRI_RADAR_REGION_VERSION}:${fileName}`;
    if (hasMediaSource.get(sourceKey)) continue;

    const imageUrl = new URL(`${EPAGRI_RADAR_BASE}/getImagem`);
    imageUrl.search = new URLSearchParams({
      prod: EPAGRI_RADAR_PRODUCT,
      radar: EPAGRI_RADAR_CODE,
      file: fileName,
      _: Date.now().toString(36),
    }).toString();
    const imageResponse = await fetch(imageUrl, {
      cache: "no-store",
      headers: {
        "cache-control": "no-cache, no-store",
        pragma: "no-cache",
        "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
      },
      signal: AbortSignal.timeout(20_000),
    });
    if (!imageResponse.ok) continue;
    const radarBytes = Buffer.from(await imageResponse.arrayBuffer());
    const radarLayerHeight = Math.round(
      ((EPAGRI_RADAR_SOURCE_EXTENT.top -
        EPAGRI_RADAR_SOURCE_EXTENT.bottom) /
        (EPAGRI_RADAR_VIEW_EXTENT.top -
          EPAGRI_RADAR_VIEW_EXTENT.bottom)) *
        EPAGRI_RADAR_HEIGHT,
    );
    const radarLayer = await sharp(radarBytes)
      .resize({
        width: EPAGRI_RADAR_WIDTH,
        height: radarLayerHeight,
        fit: "fill",
      })
      .png()
      .toBuffer();
    const bytes = await sharp(baseMap)
      .composite([{ input: radarLayer, top: 0, left: 0 }])
      .jpeg({ quality: 88 })
      .toBuffer();
    const id = createHash("sha256").update(bytes).digest("hex");
    if (hasMediaId.get(id)) continue;
    const createdAt = nowIso();
    const filePath = await storeMediaObject({
      id,
      extension: "jpg",
      bytes,
      mimeType: "image/jpeg",
      kind: EPAGRI_RADAR_KIND,
      capturedAt,
      sourceUrl: imageUrl.toString(),
      sourceKey,
      createdAt,
    });
    if (
      inserted(
        insertMedia,
        id,
        EPAGRI_RADAR_KIND,
        capturedAt,
        filePath,
        "image/jpeg",
        imageUrl.toString(),
        sourceKey,
        createdAt,
      )
    ) {
      changes += 1;
    }
  }
  broadcastMediaUpdate("radar-sc", EPAGRI_RADAR_KIND, changes);
}

type InmetOption = { sigla: string };
type InmetImage = { base64?: string };
type CptecSatelliteLog = {
  fileDate?: string;
  fileTime?: string;
  filePath?: string;
  url?: string;
};

async function inmetJson<T>(pathName: string) {
  const requestUrl = new URL(`${INMET_API}${pathName}`);
  requestUrl.searchParams.set("_", Date.now().toString(36));
  const response = await fetch(requestUrl, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      "cache-control": "no-cache, no-store",
      pragma: "no-cache",
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`INMET respondeu HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

async function ingestInmetSatellite() {
  const dates = await inmetJson<InmetOption[]>(
    `/datas/GOES/S/${INMET_SATELLITE_PRODUCT}`,
  );
  const slots: Array<{
    date: string;
    dateKey: string;
    hour: string;
    timestamp: string;
  }> = [];
  for (const option of dates.slice(0, 2)) {
    const date = option.sigla.slice(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) continue;
    const hours = await inmetJson<InmetOption[]>(
      `/horas/GOES/S/${INMET_SATELLITE_PRODUCT}/${encodeURIComponent(date)}`,
    );
    for (const { sigla: hour } of hours) {
      const timestamp = inmetSatelliteTimestamp(date, hour);
      if (timestamp) {
        slots.push({ date, dateKey: option.sigla, hour, timestamp });
      }
    }
  }

  let changes = 0;
  const recentSlots = slots
    .sort((left, right) => Date.parse(right.timestamp) - Date.parse(left.timestamp))
    .slice(0, 50)
    .reverse();
  for (const { date, dateKey, hour, timestamp } of recentSlots) {
    const sourceKey =
      `satellite:${INMET_SATELLITE_PRODUCT}:${date}:${hour}`;
    const legacySourceKey =
      `satellite:${INMET_SATELLITE_PRODUCT}:${dateKey}:${hour}`;
    const existingSourceKey = [sourceKey, legacySourceKey].find((key) =>
      hasMediaSource.get(key),
    );
    if (existingSourceKey) {
      changes += Number(
        updateMediaTimestamp.run(
          timestamp,
          existingSourceKey,
          timestamp,
        ).changes,
      );
      continue;
    }
    const image = await inmetJson<InmetImage>(
      `/GOES/S/${INMET_SATELLITE_PRODUCT}/${encodeURIComponent(date)}/${encodeURIComponent(hour)}`,
    );
    const match = image.base64?.match(
      /^data:(image\/(?:jpeg|jpg|png));base64,(.+)$/,
    );
    if (!match) continue;
    const bytes = Buffer.from(match[2], "base64");
    const id = createHash("sha256").update(bytes).digest("hex");
    if (hasMediaId.get(id)) continue;
    const extension = match[1].includes("png") ? "png" : "jpg";
    const mimeType =
      match[1] === "image/jpg" ? "image/jpeg" : match[1];
    const sourceUrl =
      `${INMET_API}/GOES/S/${INMET_SATELLITE_PRODUCT}/${date}/${hour}`;
    const createdAt = nowIso();
    const filePath = await storeMediaObject({
      id,
      extension,
      bytes,
      mimeType,
      kind: INMET_SATELLITE_KIND,
      capturedAt: timestamp,
      sourceUrl,
      sourceKey,
      createdAt,
    });
    if (
      inserted(
        insertMedia,
        id,
        INMET_SATELLITE_KIND,
        timestamp,
        filePath,
        mimeType,
        sourceUrl,
        sourceKey,
        createdAt,
      )
    ) {
      changes += 1;
    }
  }
  return changes;
}

async function ingestCptecSatellite() {
  const requestUrl = new URL(CPTEC_SATELLITE_LOGS);
  requestUrl.searchParams.set("_", Date.now().toString(36));
  const response = await fetch(requestUrl, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      "cache-control": "no-cache, no-store",
      pragma: "no-cache",
      "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    throw new Error(`CPTEC respondeu HTTP ${response.status}`);
  }
  const logs = (await response.json()) as CptecSatelliteLog[];
  let changes = 0;

  for (const log of logs.slice().reverse()) {
    if (!log.url || !log.filePath || !log.fileDate || !log.fileTime) continue;
    const timestamp = cptecSatelliteTimestamp(log.fileDate, log.fileTime);
    if (!timestamp) continue;
    const sourceKey =
      `satellite:CPTEC:1222:${CPTEC_SATELLITE_REGION_VERSION}:` +
      `${log.fileDate}:${log.fileTime}`;
    if (hasMediaSource.get(sourceKey)) continue;

    const mapUrl = new URL(CPTEC_SATELLITE_MAP);
    mapUrl.search = new URLSearchParams({
      map: "/oper/share/webdsa/sigma.map",
      SERVICE: "WMS",
      VERSION: "1.1.1",
      REQUEST: "GetMap",
      LAYERS: "img_1222,paisescinza,estadoscinza",
      STYLES: "",
      SRS: "EPSG:4326",
      BBOX: "-60,-36,-45,-22",
      WIDTH: "1024",
      HEIGHT: "768",
      FORMAT: "image/png",
      TRANSPARENT: "FALSE",
      img_1222: log.filePath,
      _: Date.now().toString(36),
    }).toString();
    const imageResponse = await fetch(mapUrl, {
      cache: "no-store",
      headers: {
        "cache-control": "no-cache, no-store",
        pragma: "no-cache",
        "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
      },
      signal: AbortSignal.timeout(20_000),
    });
    if (!imageResponse.ok) continue;
    const bytes = Buffer.from(await imageResponse.arrayBuffer());
    const id = createHash("sha256").update(bytes).digest("hex");
    if (hasMediaId.get(id)) continue;
    const mimeType =
      imageResponse.headers.get("content-type") || "image/png";
    const extension = mimeType.includes("png") ? "png" : "jpg";
    const createdAt = nowIso();
    const filePath = await storeMediaObject({
      id,
      extension,
      bytes,
      mimeType,
      kind: INMET_SATELLITE_KIND,
      capturedAt: timestamp,
      sourceUrl: log.url,
      sourceKey,
      createdAt,
    });
    if (
      inserted(
        insertMedia,
        id,
        INMET_SATELLITE_KIND,
        timestamp,
        filePath,
        mimeType,
        log.url,
        sourceKey,
        createdAt,
      )
    ) {
      changes += 1;
    }
  }
  return changes;
}

async function ingestSatellite() {
  const results = await Promise.allSettled([
    ingestInmetSatellite(),
    ingestCptecSatellite(),
  ]);
  let changes = 0;
  for (const result of results) {
    if (result.status === "fulfilled") {
      changes += result.value;
    } else {
      const message =
        result.reason instanceof Error
          ? result.reason.message
          : String(result.reason);
      console.error(`[worker] satélite redundante: ${message}`);
    }
  }
  broadcastMediaUpdate(
    "satellite",
    INMET_SATELLITE_KIND,
    changes,
  );
}

async function ingestSace() {
  const cutoff = Date.now() - 48 * 60 * 60 * 1000;
  let changes = 0;
  const latestReadings: Array<{
    sourceId: string;
    sourceName: string;
    timestamp: string;
    level: number;
  }> = [];
  await Promise.allSettled(
    SACE_LEVEL_SENSORS.map(async (sensor) => {
      const rows = parseSaceLevelRows(
        await fetchText(sensor.csv, 8_000, true),
      );
      const latest = rows.reduce<(typeof rows)[number] | null>(
        (current, row) =>
          !current || Date.parse(row.timestamp) > Date.parse(current.timestamp)
            ? row
            : current,
        null,
      );
      for (const row of rows) {
        if (Date.parse(row.timestamp) < cutoff) continue;
        if (
          inserted(
            insertSaceReading,
            sensor.code,
            row.timestamp,
            row.level,
            row.levelCm,
            nowIso(),
          )
        ) {
          changes += 1;
          if (
            latest?.timestamp === row.timestamp &&
            Date.now() - Date.parse(row.timestamp) <= 20 * 60 * 1000
          ) {
            latestReadings.push({
              sourceId: sensor.code,
              sourceName: `${sensor.city} — ${sensor.name}`,
              timestamp: row.timestamp,
              level: row.level,
            });
          }
        }
      }
    }),
  );
  if (changes) {
    broadcast("sace", {
      inserted: changes,
      stations: SACE_LEVEL_SENSORS.map((sensor) => sensor.code),
    });
  }
  const configured = new Set(
    (await alertTargets("river_level")).map((target) => target.sourceId),
  );
  await Promise.allSettled(
    latestReadings
      .filter((reading) => configured.has(reading.sourceId))
      .map((reading) =>
        dispatchPush({
          type: "metric",
          id: `river-${reading.sourceId}-${reading.timestamp}`,
          title: "Nível do rio atingiu o valor configurado",
          body: `${reading.sourceName}: ${reading.level.toFixed(2).replace(".", ",")} m.`,
          url: "/#niveis-do-rio",
          metricKind: "river_level",
          sourceId: reading.sourceId,
          sourceName: reading.sourceName,
          value: reading.level,
          windowHours: null,
        }),
      ),
  );
}

async function ingestBulletins() {
  const bulletins = parseSaceBulletins(
    await fetchText(BULLETINS_SOURCE, 10_000, true),
  );
  const cutoff = Date.now() - 48 * 60 * 60 * 1000;
  let changes = 0;
  const notifications: PushDispatch[] = [];
  for (const bulletin of bulletins) {
    if (!bulletin.date || Date.parse(bulletin.date) < cutoff) continue;
    const stored = bulletinsAtPublishedTime.all(bulletin.date) as Array<{
      id: string;
      href: string;
    }>;
    const unchanged =
      stored.length === 1 && stored[0].href === bulletin.href;
    const localPdf = await ensureBulletinPdf(
      bulletin.id,
      bulletin.href,
    );
    if (!localPdf) continue;
    if (unchanged) {
      changes += Number(localPdf.created);
      continue;
    }

    changes += Number(
      deleteBulletinsAtPublishedTime.run(bulletin.date).changes,
    );
    if (
      inserted(
        insertBulletin,
        bulletin.id,
        bulletin.title,
        bulletin.date,
        bulletin.status,
        bulletin.href,
        nowIso(),
      )
    ) {
      changes += 1;
      notifications.push({
        type: "bulletin",
        id: bulletin.id,
        title: "Novo boletim do Rio Taquari",
        body: bulletin.title,
        url: `/api/assets/${localPdf.id}`,
      });
    }
  }
  if (changes) broadcast("bulletins", { inserted: changes });
  await Promise.allSettled(notifications.map(dispatchPush));
}

async function ingestDefenseCivilAlerts() {
  const params = new URLSearchParams({
    id: "7064",
    templatename: "pagina.listapagina.padrao",
    currentPage: "1",
    pageSize: "50",
    "fields[]": "Titulo,TituloCurto,Texto",
    "form[ordem]": "RECENTES",
    _: Date.now().toString(36),
  });
  const response = await fetch(`${ALERTS_SOURCE}?${params}`, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      "cache-control": "no-cache, no-store",
      pragma: "no-cache",
      referer: "https://www.defesacivil.rs.gov.br/avisos-e-alertas",
      "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`Alertas: HTTP ${response.status}`);
  const payload = (await response.json()) as { body?: unknown };
  if (
    typeof payload.body !== "string" ||
    !/<article\b/i.test(payload.body)
  ) {
    throw new Error("listagem da Defesa Civil em formato inesperado");
  }
  const allCandidates = extractDefenseCivilAlertCandidates(payload.body);
  if (!allCandidates.length) {
    throw new Error("nenhum artigo reconhecido na listagem da Defesa Civil");
  }
  const recentCutoff = Date.now() - 14 * 24 * 60 * 60 * 1_000;
  const candidates = allCandidates
    .filter((candidate) => Date.parse(candidate.publishedAt) >= recentCutoff);
  const processed = await Promise.allSettled(
    candidates.map(async (candidate) => {
      const articleHtml = await fetchText(candidate.href, 10_000, true);
      const combined = `${candidate.title} ${candidate.summary} ${articleHtml}`;
      if (!isDefenseCivilAlertRelevant(combined)) return null;

      const imageUrl = extractDefenseCivilImage(articleHtml, candidate.href);
      const cardText = imageUrl
        ? await readDefenseCivilCardText(
            candidate.id,
            imageUrl,
            candidate.href,
          )
        : "";
      const alert = parseDefenseCivilArticle(
        articleHtml,
        candidate,
        Date.now(),
        cardText,
      );
      if (!alert) {
        const expiredAlert = parseDefenseCivilArticle(
          articleHtml,
          candidate,
          0,
          cardText,
        );
        if (expiredAlert) return null;
        throw new Error(`${candidate.id}: vigência não reconhecida`);
      }

      const publishedAt = new Date(alert.publishedAt).toISOString();
      const validUntil = new Date(alert.validUntil).toISOString();
      upsertAlert.run(
        alert.id,
        alert.title,
        alert.summary,
        publishedAt,
        validUntil,
        alert.severity,
        alert.sourceUrl,
        nowIso(),
      );
      const storedImage = await ensureAlertImage(
        alert.id,
        alert.sourceUrl,
        articleHtml,
        alert.imageUrl,
      );
      return {
        alert: { ...alert, publishedAt, validUntil },
        storedImage,
      };
    }),
  );
  const failures = processed.filter(
    (result): result is PromiseRejectedResult => result.status === "rejected",
  );
  for (const failure of failures) {
    console.error(
      "[worker] artigo da Defesa Civil:",
      failure.reason instanceof Error ? failure.reason.message : failure.reason,
    );
  }
  const alerts = processed.flatMap((result) =>
    result.status === "fulfilled" && result.value ? [result.value] : [],
  );
  const storedImageCount = alerts.filter(
    ({ storedImage }) => storedImage?.created,
  ).length;
  if (storedImageCount) {
    console.log(
      `[worker] alertas: ${storedImageCount} nova(s) imagem(ns) armazenada(s) ` +
        (objectStorageEnabled() ? "no R2" : "localmente"),
    );
  }
  await Promise.allSettled(
    alerts.map(({ alert }) =>
      dispatchPush({
        type: "alert",
        id: alert.id,
        title: "Novo alerta da Defesa Civil",
        body: alert.title.replace(/^Defesa Civil alerta:\s*/i, ""),
        url: "/",
        severity: alert.severity,
      }),
    ),
  );
  if (failures.length) {
    throw new Error(
      `${failures.length} artigo(s) recente(s) da Defesa Civil não puderam ser analisados`,
    );
  }
  await reconcileSourceAlerts(
    "defesa-civil",
    candidates.map((candidate) => candidate.id),
  );
  return { activeCount: alerts.length, storedImageCount };
}

function validInmetGeocodeField(value: unknown): boolean {
  if (typeof value === "string" || typeof value === "number") return true;
  return Array.isArray(value) && value.every(validInmetGeocodeField);
}

function inmetGeocodeFieldIncludes(value: unknown, expected: string): boolean {
  if (Array.isArray(value)) {
    return value.some((item) => inmetGeocodeFieldIncludes(item, expected));
  }
  if (typeof value !== "string" && typeof value !== "number") return false;
  return String(value).match(/\d+/g)?.includes(expected) ?? false;
}

async function ingestInmetAlerts() {
  const response = await fetch(INMET_ALERTS_SOURCE, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      "cache-control": "no-cache, no-store",
      pragma: "no-cache",
      "user-agent": "Monitoramento-Rio-Taquari-Worker/1.0",
    },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`INMET: HTTP ${response.status}`);

  const payload = await response.json();
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("resposta do INMET em formato inesperado");
  }
  const feed = payload as { hoje?: unknown; futuro?: unknown };
  if (!Array.isArray(feed.hoje) || !Array.isArray(feed.futuro)) {
    throw new Error("listas de avisos do INMET ausentes");
  }
  const rawAlerts = [...feed.hoje, ...feed.futuro];
  const validFeedShape = rawAlerts.every(
    (item) => {
      if (item === null || typeof item !== "object" || Array.isArray(item)) {
        return false;
      }
      const alert = item as Record<string, unknown>;
      return (
        (typeof alert.id === "string" || typeof alert.id === "number") &&
        String(alert.id).trim().length > 0 &&
        typeof alert.inicio === "string" &&
        typeof alert.fim === "string" &&
        typeof alert.descricao === "string" &&
        typeof alert.severidade === "string" &&
        validInmetGeocodeField(alert.geocodes)
      );
    },
  );
  if (!validFeedShape) {
    throw new Error("avisos do INMET em formato inesperado");
  }

  const expectedMucumIds = new Set(
    rawAlerts.flatMap((item) => {
      const alert = item as Record<string, unknown>;
      return inmetGeocodeFieldIncludes(
        alert.geocodes,
        INMET_MUCUM_GEOCODE,
      )
        ? [`inmet:${String(alert.id).trim()}`]
        : [];
    }),
  );
  const parsedAlerts = parseInmetAlerts(payload);
  const parsedIds = new Set(parsedAlerts.map((alert) => alert.id));
  const unparsedMucumIds = [...expectedMucumIds].filter(
    (id) => !parsedIds.has(id),
  );
  if (unparsedMucumIds.length) {
    throw new Error(
      `${unparsedMucumIds.length} aviso(s) do INMET para Muçum não puderam ser analisados`,
    );
  }

  const now = Date.now();
  const alerts = parsedAlerts.map((alert) => ({
    ...alert,
    publishedAt: new Date(alert.publishedAt).toISOString(),
    validUntil: new Date(alert.validUntil).toISOString(),
  }));
  for (const alert of alerts) {
    upsertAlert.run(
      alert.id,
      alert.title,
      alert.summary,
      alert.publishedAt,
      alert.validUntil,
      alert.severity,
      alert.sourceUrl,
      nowIso(),
    );
  }
  await reconcileSourceAlerts(
    "inmet",
    alerts.map((alert) => alert.id),
  );

  const activeAlerts = alerts.filter(
    (alert) =>
      Date.parse(alert.publishedAt) <= now &&
      Date.parse(alert.validUntil) > now,
  );
  await Promise.allSettled(
    activeAlerts.map((alert) =>
      dispatchPush({
        type: "alert",
        id: alert.id,
        title: "Novo alerta do INMET",
        body: alert.title,
        url: "/",
        severity: alert.severity,
      }),
    ),
  );
  return { activeCount: activeAlerts.length, storedCount: alerts.length };
}

async function trackAlertSource<T>(
  source: AlertSourceId,
  job: () => Promise<T>,
) {
  try {
    const result = await job();
    recordAlertSourceStatus(source, "ok");
    return result;
  } catch (error) {
    recordAlertSourceStatus(
      source,
      "error",
      error instanceof Error ? error.message : String(error),
    );
    throw error;
  }
}

async function ingestAlerts() {
  const sources = await Promise.allSettled([
    trackAlertSource("defesa-civil", ingestDefenseCivilAlerts),
    trackAlertSource("inmet", ingestInmetAlerts),
  ]);
  for (const [index, result] of sources.entries()) {
    if (result.status === "rejected") {
      console.error(
        `[worker] alertas ${index === 0 ? "Defesa Civil" : "INMET"}:`,
        result.reason instanceof Error ? result.reason.message : result.reason,
      );
    }
  }
  if (sources.every((result) => result.status === "rejected")) {
    throw new Error("Defesa Civil e INMET indisponíveis");
  }
  const activeCount = sources.reduce(
    (count, result) =>
      count + (result.status === "fulfilled" ? result.value.activeCount : 0),
    0,
  );
  broadcast("alerts", { count: activeCount });
}

async function ingestCeran() {
  let changes = 0;
  const latestReadings: Array<{
    sourceId: string;
    sourceName: string;
    timestamp: string;
    outflow: number;
  }> = [];
  await Promise.all(
    Object.values(CERAN_PLANT_SOURCES).map(async (plant) => {
      const rows = parseCeranTable(
        await fetchText(plant.source, 10_000, true),
      );
      const latest = rows.reduce<(typeof rows)[number] | null>(
        (current, row) =>
          !current || Date.parse(row.timestamp) > Date.parse(current.timestamp)
            ? row
            : current,
        null,
      );
      const cutoff = Date.now() - 48 * 60 * 60 * 1000;
      for (const row of rows) {
        if (Date.parse(row.timestamp) < cutoff) continue;
        if (
          inserted(
            insertCeranReading,
            plant.id,
            row.timestamp,
            row.upstreamLevel,
            row.downstreamLevel,
            row.inflow,
            row.turbined,
            row.spilled,
            row.residual,
            row.outflow,
            row.status,
            nowIso(),
          )
        ) {
          changes += 1;
          if (
            latest?.timestamp === row.timestamp &&
            Date.now() - Date.parse(row.timestamp) <= 2 * 60 * 60 * 1000
          ) {
            latestReadings.push({
              sourceId: plant.id,
              sourceName: plant.name,
              timestamp: row.timestamp,
              outflow: row.outflow,
            });
          }
        }
      }
    }),
  );
  if (changes) broadcast("ceran", { inserted: changes });
  const configured = new Set(
    (await alertTargets("ceran_outflow")).map((target) => target.sourceId),
  );
  await Promise.allSettled(
    latestReadings
      .filter((reading) => configured.has(reading.sourceId))
      .map((reading) =>
        dispatchPush({
          type: "metric",
          id: `ceran-${reading.sourceId}-${reading.timestamp}`,
          title: "Vazão da hidrelétrica atingiu o valor configurado",
          body: `${reading.sourceName}: ${reading.outflow.toFixed(1).replace(".", ",")} m³/s.`,
          url: "/#hidreletricas",
          metricKind: "ceran_outflow",
          sourceId: reading.sourceId,
          sourceName: reading.sourceName,
          value: reading.outflow,
          windowHours: null,
        }),
      ),
  );
}

async function ingestRain() {
  const end = new Date();
  const start = new Date(end.getTime() - 54 * 60 * 60 * 1000);
  let changes = 0;
  const targets = await alertTargets("rain_accumulation");
  await Promise.allSettled(
    MUCUM_UPSTREAM_RAIN_STATIONS.map(async (station) => {
      const stationTargets = targets.filter(
        (target) => target.sourceId === station.code && target.windowHours,
      );
      const params = new URLSearchParams({
        codEstacao: station.code,
        dataInicio: saoPauloDate(start),
        dataFim: saoPauloDate(end),
      });
      const records = parseAnaRecords(
        await fetchText(`${ANA_ENDPOINT}?${params}`, 9_000),
      );
      const cutoff = Date.now() - 48 * 60 * 60 * 1000;
      let stationChanged = false;
      for (const row of records) {
        if (Date.parse(row.timestamp) < cutoff) continue;
        if (
          inserted(
            insertRainReading,
            station.code,
            row.timestamp,
            row.rain,
            row.levelCm,
            row.discharge,
            row.quality,
            nowIso(),
          )
        ) {
          changes += 1;
          stationChanged = true;
        }
      }
      const latest = records.reduce<(typeof records)[number] | null>(
        (current, row) =>
          !current || Date.parse(row.timestamp) > Date.parse(current.timestamp)
            ? row
            : current,
        null,
      );
      if (!stationChanged || !latest || !stationTargets.length) return;
      await Promise.allSettled(
        stationTargets.map(async (target) => {
          const windowHours = target.windowHours!;
          const rain = accumulatedRain(records, windowHours, Date.now());
          if (rain === null) return;
          await dispatchPush({
            type: "metric",
            id: `rain-${station.code}-${windowHours}h-${latest.timestamp}`,
            title: "Chuva acumulada atingiu o valor configurado",
            body: `${station.city} — ${station.name}: ${rain.toFixed(1).replace(".", ",")} mm em ${windowHours}h.`,
            url: "/#chuva-acumulada",
            metricKind: "rain_accumulation",
            sourceId: station.code,
            sourceName: `${station.city} — ${station.name}`,
            value: rain,
            windowHours,
          });
        }),
      );
    }),
  );
  if (changes) broadcast("rain", { inserted: changes });
}

async function ingestDcrsHistoric() {
  const end = new Date();
  const start = new Date(end.getTime() - 48 * 60 * 60 * 1000);
  const response = await fetch(DCRS_HTTP_ENDPOINT, {
    method: "POST",
    cache: "no-store",
    headers: {
      "content-type": "application/json",
      origin: "https://redehidrometeorologica.defesacivil.rs.gov.br",
      referer: "https://redehidrometeorologica.defesacivil.rs.gov.br/Mapa",
      "user-agent": "Mozilla/5.0 Monitoramento Rio Taquari",
    },
    body: JSON.stringify({
      operationName: "Historic",
      query: dcrsHistoricQuery(DCRS_STATION, start, end),
    }),
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) {
    throw new Error(`Histórico DCRS: HTTP ${response.status}`);
  }
  const payload = await response.json();
  const readings = parseDcrsHistoric(
    payload,
    DCRS_STATION,
    DCRS_OFFSET,
  );
  if (!readings.length) {
    throw new Error("Histórico DCRS retornou sem leituras válidas");
  }

  const createdAt = nowIso();
  let changes = 0;
  const persistent = readings.map((reading) => ({
    station: DCRS_STATION,
    timestamp: reading.timestamp,
    level: reading.level,
    rawLevel: reading.rawLevel,
    trendValue: reading.trendValue,
    trend: reading.trend,
    source: "Defesa Civil RS / MKS Historic",
    createdAt,
  }));
  for (const reading of persistent) {
    changes += Number(
      insertRiverReading.run(
        reading.station,
        reading.timestamp,
        reading.level,
        reading.rawLevel,
        reading.trendValue,
        reading.trend,
        reading.source,
        reading.createdAt,
      ).changes,
    );
  }
  for (let index = 0; index < persistent.length; index += 500) {
    await persistRiverReadings(persistent.slice(index, index + 500));
  }
  if (changes) {
    broadcast("river-history", { inserted: changes });
  }
}

function storeRiverReading(reading: ReturnType<typeof extractRealtimeLevel>) {
  if (!reading || reading.level === null) return;
  const createdAt = nowIso();
  if (
    inserted(
      insertRiverReading,
      reading.station,
      reading.timestamp,
      reading.level,
      reading.rawLevel,
      reading.trendValue,
      reading.trend,
      "Defesa Civil RS / MKS",
      createdAt,
    )
  ) {
    broadcast("river", reading);
    void persistRiverReadings([
      {
        ...reading,
        level: reading.level,
        source: "Defesa Civil RS / MKS",
        createdAt,
      },
    ]).catch((error) => {
      console.error(
        "[worker] DCRS-00091: falha ao persistir leitura:",
        error instanceof Error ? error.message : error,
      );
    });
    void alertTargets("river_level")
      .then((targets) => {
        if (!targets.some((target) => target.sourceId === DCRS_STATION)) return;
        return dispatchPush({
          type: "metric",
          id: `river-${DCRS_STATION}-${reading.timestamp}`,
          title: "Nível do rio atingiu o valor configurado",
          body: `Muçum — Sensor na Barra do Guaporé: ${reading.level!.toFixed(2).replace(".", ",")} m.`,
          url: "/#niveis-do-rio",
          metricKind: "river_level",
          sourceId: DCRS_STATION,
          sourceName: "Muçum — Sensor na Barra do Guaporé",
          value: reading.level!,
          windowHours: null,
        });
      })
      .catch((error) => {
        console.error(
          "[worker] alerta DCRS-00091:",
          error instanceof Error ? error.message : error,
        );
      });
  }
}

function connectDcrs() {
  if (stopped) return;
  dcrsSocket = new WebSocket(DCRS_ENDPOINT, "graphql-transport-ws");
  let acknowledged = false;
  const watchdog = setTimeout(() => dcrsSocket?.close(), 15_000);
  dcrsSocket.on("open", () => {
    dcrsSocket?.send(JSON.stringify({ type: "connection_init", payload: {} }));
  });
  dcrsSocket.on("message", (raw) => {
    try {
      const message = JSON.parse(raw.toString());
      if (message.type === "ping") {
        dcrsSocket?.send(
          JSON.stringify({ type: "pong", payload: message.payload }),
        );
        return;
      }
      if (message.type === "connection_ack") {
        acknowledged = true;
        clearTimeout(watchdog);
        dcrsSocket?.send(
          JSON.stringify({
            id: "dcrs-00091",
            type: "subscribe",
            payload: { query: DCRS_SUBSCRIPTION },
          }),
        );
        return;
      }
      if (message.type === "next") {
        storeRiverReading(
          extractRealtimeLevel(message.payload, DCRS_STATION, DCRS_OFFSET),
        );
      }
    } catch {
      // Frames inválidos não interrompem a assinatura.
    }
  });
  dcrsSocket.on("close", () => {
    clearTimeout(watchdog);
    if (stopped) return;
    dcrsRetry = setTimeout(connectDcrs, acknowledged ? 2_000 : 8_000);
  });
  dcrsSocket.on("error", () => dcrsSocket?.close());
}

async function cleanup() {
  const mediaCutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const dataCutoff = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString();
  const oldMedia = database
    .prepare(
      "SELECT file_path FROM media_frames WHERE julianday(captured_at) < julianday(?)",
    )
    .all(mediaCutoff) as Array<{ file_path: string }>;
  for (const { file_path: filePath } of oldMedia) {
    try {
      await deleteStoredObject(filePath);
    } catch (error) {
      console.error(
        `[worker] retenção de mídia ${filePath}:`,
        error instanceof Error ? error.message : error,
      );
    }
  }
  database
    .prepare(
      "DELETE FROM media_frames WHERE julianday(captured_at) < julianday(?)",
    )
    .run(mediaCutoff);
  for (const table of [
    "river_readings",
    "sace_readings",
    "rain_readings",
    "ceran_readings",
  ]) {
    database
      .prepare(
        `DELETE FROM ${table} WHERE julianday(timestamp) < julianday(?)`,
      )
      .run(dataCutoff);
  }
  database
    .prepare(
      "DELETE FROM bulletins WHERE published_at IS NULL OR julianday(published_at) < julianday(?)",
    )
    .run(dataCutoff);
  database
    .prepare(
      "DELETE FROM alerts WHERE julianday(valid_until) < julianday(?)",
    )
    .run(nowIso());
  const orphanAssets = database
    .prepare(`
      SELECT file_path, owner_type, owner_id
      FROM stored_assets AS asset
      WHERE
        (
          asset.owner_type = 'bulletin-pdf'
          AND NOT EXISTS (
            SELECT 1 FROM bulletins WHERE id = asset.owner_id
          )
        )
        OR
        (
          asset.owner_type = 'alert-image'
          AND NOT EXISTS (
            SELECT 1 FROM alerts WHERE id = asset.owner_id
          )
        )
    `)
    .all() as Array<{
      file_path: string;
      owner_type: StoredAssetOwner;
      owner_id: string;
    }>;
  for (const asset of orphanAssets) {
    try {
      await deleteStoredObject(asset.file_path);
      if (
        objectStorageEnabled() &&
        asset.owner_type === "alert-image"
      ) {
        await deleteStoredObjectByKey(
          alertImageObjectKey(asset.owner_id),
        );
      }
    } catch (error) {
      console.error(
        `[worker] retenção de arquivo ${asset.file_path}:`,
        error instanceof Error ? error.message : error,
      );
    }
  }
  database.prepare(`
    DELETE FROM stored_assets
    WHERE
      (
        owner_type = 'bulletin-pdf'
        AND NOT EXISTS (
          SELECT 1 FROM bulletins WHERE id = stored_assets.owner_id
        )
      )
      OR
      (
        owner_type = 'alert-image'
        AND NOT EXISTS (
          SELECT 1 FROM alerts WHERE id = stored_assets.owner_id
        )
      )
  `).run();
}

async function runJob(name: string, job: () => Promise<void> | void) {
  try {
    await job();
  } catch (error) {
    if (stopped) return;
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[worker] ${name}: ${message}`);
  }
}

function every(name: string, interval: number, job: () => Promise<void> | void) {
  let running = false;
  const tick = async () => {
    if (running || stopped) return;
    running = true;
    try {
      await runJob(name, job);
    } finally {
      running = false;
    }
  };
  void tick();
  timers.push(setInterval(() => void tick(), interval));
}

await runJob("restauração D1", restorePersistentDatabase);
await runJob("restauração R2", restoreObjectStorageIndex);
await runJob("migração local para R2", migrateLocalFilesToObjectStorage);
await runJob("sincronização D1", synchronizePersistentDatabase);
console.log(`[worker] persistência ativa: ${PERSISTENCE_SCHEMA_VERSION}`);

liveServer.on("connection", (socket) => {
  socket.send(JSON.stringify({ type: "ready", sentAt: nowIso() }));
  for (const [type, kind] of [
    ["radar", "radar"],
    ["radar-sc", EPAGRI_RADAR_KIND],
    ["satellite", INMET_SATELLITE_KIND],
  ] as const) {
    const latest = latestMediaTimestamp.get(kind) as
      | { captured_at: string }
      | undefined;
    socket.send(
      JSON.stringify({
        type,
        payload: {
          inserted: 0,
          latestTimestamp: latest?.captured_at || null,
          storage: objectStorageEnabled() ? "r2" : "local",
          reason: "connected",
        },
        sentAt: nowIso(),
      }),
    );
  }
});
liveServer.on("listening", () => {
  console.log(`[worker] WebSocket em ws://localhost:${livePort}`);
});

every("radar", 30_000, ingestRadar);
every("radar SC", 30_000, ingestEpagriRadar);
every("satélite", 30_000, ingestSatellite);
every("boletins", 60_000, ingestBulletins);
every("alertas", 60_000, ingestAlerts);
every("SACE Muçum", 60_000, ingestSace);
every("CERAN", 5 * 60_000, ingestCeran);
every("chuva ANA", 15 * 60_000, ingestRain);
every("histórico DCRS", 5 * 60_000, ingestDcrsHistoric);
every(
  "persistência DCRS",
  15 * 60_000,
  synchronizePersistentRiverHistory,
);
every("persistência D1", 30_000, synchronizePersistentDatabase);
every("retenção", 60 * 60_000, cleanup);
connectDcrs();

async function shutdown() {
  if (stopped) return;
  stopped = true;
  for (const timer of timers) clearInterval(timer);
  if (dcrsRetry) clearTimeout(dcrsRetry);
  dcrsSocket?.close();
  liveServer.close();
  try {
    const worker = await radarOcrWorker;
    await worker.terminate();
  } finally {
    database.close();
    process.exit(0);
  }
}

process.once("SIGINT", () => void shutdown());
process.once("SIGTERM", () => void shutdown());
