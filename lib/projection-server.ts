import { spawn } from "node:child_process";
import { mkdir, readFile, readdir, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import { preserveStationProjections, validProjection, type Projection } from "./projection.ts";
import { listStoredObjects, objectStorageEnabled, putStoredObject } from "./object-storage.ts";

const directory = path.join(process.env.MONITORA_DATA_DIR || path.join(process.cwd(), ".data"), "projection");
const runtime = process.env.PROJECTION_RUNTIME_DIR || path.join(process.cwd(), "projection-runtime");
let active: Promise<Projection> | undefined;

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
  if (!validProjection(data)) throw new Error("Invalid stored projection");
  return data;
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

async function calculate(): Promise<Projection> {
  await mkdir(directory, { recursive: true });
  await new Promise<void>((resolve, reject) => {
    const child = spawn(process.env.PROJECTION_PYTHON || "/opt/projection-venv/bin/python", [path.join(runtime, "scripts/hydro_site_projection.py"), "--state", directory], {
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PYTHONUNBUFFERED: "1", OMP_NUM_THREADS: "2", OPENBLAS_NUM_THREADS: "2" },
    });
    let tail = "";
    const consume = (data: Buffer) => { tail = (tail + data.toString()).slice(-2500); };
    child.stdout.on("data", consume);
    child.stderr.on("data", consume);
    const timer = setTimeout(() => child.kill("SIGKILL"), 12 * 60_000);
    child.once("error", error => { clearTimeout(timer); reject(error); });
    child.once("exit", code => {
      clearTimeout(timer);
      if (code === 0) resolve();
      else { console.error("[projection] calculation failed", tail); reject(new Error("Projection calculation failed")); }
    });
  });
  const calculated: unknown = JSON.parse(await readFile(path.join(directory, "result.json"), "utf8"));
  if (!validProjection(calculated) || Date.now() - Date.parse(calculated.generatedAt) > 15 * 60_000) throw new Error("Invalid calculated projection");
  const previous = calculated.encantado && calculated["santa-tereza"] ? null : await readProjection().catch(() => null);
  const projection = preserveStationProjections(calculated, previous);
  const bytes = Buffer.from(JSON.stringify(projection));
  const roundKey = `rounds/${new Date(projection.referenceAt).toISOString()}.json`;
  if (objectStorageEnabled()) {
    for (const filename of ["history.tar.gz", "audit.tar.gz"]) {
      await putStoredObject({ key: `projection/${filename}`, bytes: await readFile(path.join(directory, filename)), mimeType: "application/gzip", metadata: {}, localPath: path.join(directory, filename) });
    }
    await putStoredObject({ key: `projection/issues/${projection.generatedAt}.json`, bytes, mimeType: "application/json", metadata: {}, localPath: path.join(directory, "unused.json") });
    await putStoredObject({ key: `projection/${roundKey}`, bytes, mimeType: "application/json", metadata: {}, localPath: path.join(directory, roundKey) });
    // Publish last, only after the complete history and model result are durable.
    await putStoredObject({ key: "projection/latest.json", bytes, mimeType: "application/json", metadata: {}, localPath: path.join(directory, "latest.json") });
  }
  await mkdir(path.join(directory, "rounds"), { recursive: true });
  await writeFile(path.join(directory, "round.pending.json"), bytes);
  await rename(path.join(directory, "round.pending.json"), path.join(directory, roundKey));
  await writeFile(path.join(directory, "latest.pending.json"), bytes);
  await rename(path.join(directory, "latest.pending.json"), path.join(directory, "latest.json"));
  console.log("[projection] published", projection.generatedAt);
  return projection;
}

export function refreshProjection(): Promise<Projection> {
  if (!active) active = calculate().finally(() => { active = undefined; });
  return active;
}
