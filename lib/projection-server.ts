import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdir, readFile, readdir, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { isHydrometricProjection, mucumProjection, readProjectionShadowState, type Projection, type ProjectionShadowState } from "./projection.ts";
import { listStoredObjects, objectStorageEnabled, putStoredObject, putImmutableStoredObject } from "./object-storage.ts";

import { flushProjectionArchive, requireArchivedReceipt } from "./projection-archive.ts";

const directory = path.join(process.env.MONITORA_DATA_DIR || path.join(process.cwd(), ".data"), "projection");
const runtime = process.env.PROJECTION_RUNTIME_DIR || path.join(process.cwd(), "projection-runtime");
export type ProjectionRefresh = { status: "published" | "waiting_for_data" | "already_calculated"; referenceAt: string; checkedReferenceAt?: string; generatedAt?: string; missing?: string[]; shadow?: ProjectionShadowState };
export type ProjectionRefreshState = (ProjectionRefresh | { status: "failed"; shadow?: ProjectionShadowState }) & { checkedAt: string };
let active: Promise<ProjectionRefresh> | undefined;

class ArchivedProjectionFailure extends Error {
  shadow?: ProjectionShadowState;
  constructor(cause: unknown, shadow?: ProjectionShadowState) {
    super("Projection calculation failed", { cause });
    this.shadow = shadow;
  }
}

export async function readProjectionRefreshState(): Promise<ProjectionRefreshState | null> {
  let value: ProjectionRefreshState;
  if (objectStorageEnabled()) {
    const response = await fetch(`${process.env.OBJECT_STORAGE_URL}/projection/refresh.json`, { cache: "no-store", signal: AbortSignal.timeout(10_000) });
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Projection refresh storage: ${response.status}`);
    value = await response.json();
  } else {
    try { value = JSON.parse(await readFile(path.join(directory, "refresh.json"), "utf8")); }
    catch (error) { if ((error as NodeJS.ErrnoException).code === "ENOENT") return null; throw error; }
  }
  if (!value || !["published", "waiting_for_data", "already_calculated", "failed"].includes(value.status) || !Number.isFinite(Date.parse(value.checkedAt))) throw new Error("Invalid projection refresh state");
  const { shadow: untrustedShadow, ...state } = value;
  const shadow = readProjectionShadowState(untrustedShadow, value.checkedAt);
  return { ...state, ...(shadow ? { shadow } : {}) };
}

async function saveRefreshState(result: ProjectionRefresh | { status: "failed"; shadow?: ProjectionShadowState }) {
  const bytes = Buffer.from(JSON.stringify({ ...result, checkedAt: new Date().toISOString() }));
  await mkdir(directory, { recursive: true });
  if (objectStorageEnabled()) await putStoredObject({ key: "projection/refresh.json", bytes, mimeType: "application/json", metadata: {}, localPath: path.join(directory, "refresh.json") });
  await writeFile(path.join(directory, "refresh.pending.json"), bytes);
  await rename(path.join(directory, "refresh.pending.json"), path.join(directory, "refresh.json"));
}

export async function readProjection(round?: string): Promise<Projection | null> {
  if (round && (!Number.isFinite(Date.parse(round)) || new Date(round).toISOString() !== round)) throw new Error("Invalid round");
  const key = round ? `rounds/${round}.json` : "latest.json";
  let data: unknown;
  if (objectStorageEnabled()) {
    const response = await fetch(`${process.env.OBJECT_STORAGE_URL}/projection/${key}`, { cache: "no-store", signal: AbortSignal.timeout(10_000) });
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Projection storage: ${response.status}`);
    data = await response.json();
  } else {
    try { data = JSON.parse(await readFile(path.join(directory, key), "utf8")); }
    catch (error) { if ((error as NodeJS.ErrnoException).code === "ENOENT") return null; throw error; }
  }
  const projection = mucumProjection(data);
  if (!projection) throw new Error("Invalid stored projection");
  return projection;
}

export async function listProjectionRounds(): Promise<string[]> {
  let keys: string[];
  if (objectStorageEnabled()) keys = (await listStoredObjects("projection/rounds/")).map(object => object.key.split("/").at(-1)!);
  else {
    try { keys = await readdir(path.join(directory, "rounds")); }
    catch (error) { if ((error as NodeJS.ErrnoException).code === "ENOENT") return []; throw error; }
  }
  return keys.filter(k => k.endsWith(".json")).map(k => k.slice(0, -5)).filter(k => Number.isFinite(Date.parse(k))).sort().reverse();
}

async function calculate(): Promise<ProjectionRefresh> {
  await flushProjectionArchive(directory);
  const referenceAt = new Date(Math.floor(Date.now() / 3_600_000) * 3_600_000).toISOString();
  // Check durable published state as well as the in-process lock: containers restart.
  const previous = await readProjection();
  if (previous && isHydrometricProjection(previous) && Date.parse(previous.referenceAt) >= Date.parse(referenceAt)) {
    const shadow = (await readProjectionRefreshState().catch(() => null))?.shadow;
    return { status: "already_calculated", referenceAt: previous.referenceAt, generatedAt: previous.generatedAt, ...(shadow ? { shadow } : {}) };
  }
  const attemptId = randomUUID();
  await mkdir(directory, { recursive: true });
  let calculationError: unknown;
  try { await new Promise<void>((resolve, reject) => {
    const args = [path.join(runtime, "scripts/hydro_site_projection.py"), "--state", directory, "--attempt-id", attemptId, "--reference", referenceAt];
    if (previous && isHydrometricProjection(previous)) args.push("--after-reference", previous.referenceAt);
    const child = spawn(process.env.PROJECTION_PYTHON || "/opt/projection-venv/bin/python", args, {
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PYTHONUNBUFFERED: "1", OMP_NUM_THREADS: "2", OPENBLAS_NUM_THREADS: "2" },
    });
    let tail = "";
    const consume = (data: Buffer) => { tail = (tail + data.toString()).slice(-2500); };
    child.stdout.on("data", consume);
    child.stderr.on("data", consume);
    let killTimer: NodeJS.Timeout | undefined;
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      killTimer = setTimeout(() => child.kill("SIGKILL"), 90_000);
    }, 11 * 60_000);
    child.once("error", error => { clearTimeout(timer); clearTimeout(killTimer); reject(error); });
    child.once("exit", code => {
      clearTimeout(timer); clearTimeout(killTimer);
      if (code === 0) resolve();
      else { console.error("[projection] calculation failed", tail); reject(new Error("Projection calculation failed")); }
    });
  }); } catch (error) { calculationError = error; }
  // Even a blocked or failed calculation owns durable evidence.
  await flushProjectionArchive(directory);
  const status = JSON.parse(await readFile(path.join(directory, "refresh-status.json"), "utf8"));
  if (status.attemptId !== attemptId || Date.parse(status.checkedReferenceAt) !== Date.parse(referenceAt)) throw new Error("Invalid refresh attempt");
  await requireArchivedReceipt(directory, status.archiveReceiptKey, status);
  // The receipt is confirmed before any experimental status becomes public.
  // Reject mismatched receipts and strip predictions, raw sources and errors.
  const shadow = status.shadow?.archiveReceiptKey === status.archiveReceiptKey ?
    readProjectionShadowState(status.shadow) ?? undefined : undefined;
  if (calculationError) throw new ArchivedProjectionFailure(calculationError, shadow);
  if (status.status === "waiting_for_data") {
    if (!Array.isArray(status.missing) || !status.missing.every((item: unknown) => typeof item === "string")) throw new Error("Invalid missing-data report");
    const waitingReference = Date.parse(status.referenceAt);
    if (!Number.isFinite(waitingReference) || waitingReference > Date.parse(referenceAt) || waitingReference < Date.parse(referenceAt) - 3 * 3_600_000) throw new Error("Invalid waiting reference");
    return { status: "waiting_for_data", referenceAt: status.referenceAt, checkedReferenceAt: referenceAt, generatedAt: previous?.generatedAt, missing: status.missing, ...(shadow ? { shadow } : {}) };
  }
  if (status.status !== "calculated") throw new Error("Projection did not calculate");
  const calculated = mucumProjection(JSON.parse(await readFile(path.join(directory, "result.json"), "utf8")));
  if (!calculated || calculated.generatedAt !== status.generatedAt || Date.parse(calculated.referenceAt) !== Date.parse(status.referenceAt) || (Date.now() - Date.parse(calculated.generatedAt) > 60 * 60_000 || Date.parse(calculated.generatedAt) > Date.now())) throw new Error("Invalid calculated projection");
  const hydrometric = isHydrometricProjection(calculated);
  if (hydrometric && calculated.archiveReceiptKey !== status.archiveReceiptKey) throw new Error("Hydrometric projection receipt does not match calculation");
  const selectedReference = Date.parse(calculated.referenceAt);
  // A late complete hour keeps its own identity; it can never replace a newer
  // published origin or be used outside the bounded operational window.
  if (selectedReference > Date.parse(referenceAt) || Date.now() - selectedReference > 3 * 3_600_000 ||
      (previous && (selectedReference < Date.parse(previous.referenceAt) ||
        (selectedReference === Date.parse(previous.referenceAt) && !(hydrometric && !isHydrometricProjection(previous)))))) throw new Error("Invalid selected reference");
  if (calculated.models.some(model => model.points.some(point => Date.parse(point.timestamp) <= Date.now()))) throw new Error("Forecast target elapsed before publication");
  const projection = calculated;
  const bytes = Buffer.from(JSON.stringify(projection));
  const roundKey = `rounds/${new Date(projection.referenceAt).toISOString()}.json`;
  if (objectStorageEnabled()) {
    // The frozen hydrometric model and its observations are already included in
    // the immutable runtime/attempt receipt. Only the legacy model needs these
    // mutable training checkpoints for its next refresh.
    for (const filename of hydrometric ? [] : ["history.tar.gz", "audit.tar.gz"]) {
      await putStoredObject({ key: `projection/${filename}`, bytes: await readFile(path.join(directory, filename)), mimeType: "application/gzip", metadata: {}, localPath: path.join(directory, filename) });
    }
    if (projection.models.some(model => model.points.some(point => Date.parse(point.timestamp) <= Date.now()))) throw new Error("Forecast target elapsed during upload");
    await putImmutableStoredObject({ key: `projection/issues/${projection.generatedAt}.json`, bytes, mimeType: "application/json", localPath: path.join(directory, "issues", `${projection.generatedAt}.json`) });
    await putStoredObject({ key: `projection/${roundKey}`, bytes, mimeType: "application/json", metadata: {}, localPath: path.join(directory, roundKey) });
    // Uploads may cross the hour: an elapsed target must not become a new issue.
    if (projection.models.some(model => model.points.some(point => Date.parse(point.timestamp) <= Date.now()))) throw new Error("Forecast target elapsed during upload");
    // Publish last, only after the complete history and model result are durable.
    await putStoredObject({ key: "projection/latest.json", bytes, mimeType: "application/json", metadata: {}, localPath: path.join(directory, "latest.json") });
  }
  await mkdir(path.join(directory, "rounds"), { recursive: true });
  await writeFile(path.join(directory, "round.pending.json"), bytes);
  await rename(path.join(directory, "round.pending.json"), path.join(directory, roundKey));
  await writeFile(path.join(directory, "latest.pending.json"), bytes);
  await rename(path.join(directory, "latest.pending.json"), path.join(directory, "latest.json"));
  console.log("[projection] published", projection.generatedAt);
  return { status: "published", referenceAt: projection.referenceAt, checkedReferenceAt: referenceAt, generatedAt: projection.generatedAt, ...(shadow ? { shadow } : {}) };
}

export function refreshProjection(): Promise<ProjectionRefresh> {
  if (!active) active = calculate().then(async result => {
    await saveRefreshState(result);
    return result;
  }).catch(async error => {
    try { await saveRefreshState({ status: "failed", ...(error instanceof ArchivedProjectionFailure && error.shadow ? { shadow: error.shadow } : {}) }); }
    catch (storageError) { console.error("[projection] could not persist refresh state", storageError instanceof Error ? storageError.message : "Unknown storage error"); }
    throw error;
  }).finally(() => { active = undefined; });
  return active;
}
