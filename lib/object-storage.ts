import {
  existsSync,
  mkdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

const OBJECT_STORAGE_URL = (
  process.env.OBJECT_STORAGE_URL || ""
).replace(/\/+$/, "");
const REMOTE_REFERENCE_PREFIX = "r2:";

export type StoredObjectMetadata = Record<string, string>;

export type StoredObjectListing = {
  key: string;
  httpMetadata?: {
    contentType?: string;
  };
  customMetadata?: StoredObjectMetadata;
};

function remoteUrl(key = "") {
  const encodedKey = key
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  return `${OBJECT_STORAGE_URL}/${encodedKey}`;
}

export function storedObjectReference(key: string) {
  return `${REMOTE_REFERENCE_PREFIX}${key}`;
}

function keyFromReference(reference: string) {
  return reference.startsWith(REMOTE_REFERENCE_PREFIX)
    ? reference.slice(REMOTE_REFERENCE_PREFIX.length)
    : null;
}

async function assertRemoteResponse(
  response: Response,
  operation: string,
) {
  if (response.ok) return;
  const detail = (await response.text().catch(() => "")).slice(0, 300);
  throw new Error(
    `${operation}: HTTP ${response.status}${detail ? ` — ${detail}` : ""}`,
  );
}

export function objectStorageEnabled() {
  return Boolean(OBJECT_STORAGE_URL);
}

export async function putStoredObject({
  key,
  bytes,
  mimeType,
  metadata,
  localPath,
}: {
  key: string;
  bytes: Buffer;
  mimeType: string;
  metadata: StoredObjectMetadata;
  localPath: string;
}) {
  if (!OBJECT_STORAGE_URL) {
    mkdirSync(path.dirname(localPath), { recursive: true });
    if (!existsSync(localPath)) {
      writeFileSync(localPath, bytes, { flag: "wx" });
    }
    return localPath;
  }

  const response = await fetch(remoteUrl(key), {
    method: "PUT",
    headers: {
      "content-type": mimeType,
      "x-monitora-metadata": Buffer.from(
        JSON.stringify(metadata),
        "utf8",
      ).toString("base64url"),
    },
    body: Uint8Array.from(bytes),
    signal: AbortSignal.timeout(30_000),
  });
  await assertRemoteResponse(response, `R2 PUT ${key}`);
  return storedObjectReference(key);
}

export async function storedObjectExists(reference: string) {
  const key = keyFromReference(reference);
  if (!key) return existsSync(reference);
  if (!OBJECT_STORAGE_URL) return false;

  const response = await fetch(remoteUrl(key), {
    method: "HEAD",
    signal: AbortSignal.timeout(10_000),
  });
  if (response.status === 404) return false;
  await assertRemoteResponse(response, `R2 HEAD ${key}`);
  return true;
}

export async function deleteStoredObject(reference: string) {
  const key = keyFromReference(reference);
  if (!key) {
    try {
      rmSync(reference);
    } catch {
      // A remoção é idempotente.
    }
    return;
  }
  await deleteStoredObjectByKey(key);
}

export async function deleteStoredObjectByKey(key: string) {
  if (!OBJECT_STORAGE_URL) return;
  const response = await fetch(remoteUrl(key), {
    method: "DELETE",
    signal: AbortSignal.timeout(15_000),
  });
  await assertRemoteResponse(response, `R2 DELETE ${key}`);
}

export async function listStoredObjects(prefix: string) {
  if (!OBJECT_STORAGE_URL) return [] as StoredObjectListing[];

  const objects: StoredObjectListing[] = [];
  let cursor = "";
  do {
    const requestUrl = new URL(`${OBJECT_STORAGE_URL}/`);
    requestUrl.searchParams.set("prefix", prefix);
    if (cursor) requestUrl.searchParams.set("cursor", cursor);
    const response = await fetch(requestUrl, {
      signal: AbortSignal.timeout(20_000),
    });
    await assertRemoteResponse(response, `R2 LIST ${prefix}`);
    const payload = (await response.json()) as {
      objects?: StoredObjectListing[];
      cursor?: string;
      truncated?: boolean;
    };
    objects.push(...(Array.isArray(payload.objects) ? payload.objects : []));
    cursor = payload.truncated ? payload.cursor || "" : "";
  } while (cursor);
  return objects;
}
