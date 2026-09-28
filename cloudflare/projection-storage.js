// Extend the existing private R2 bridge only with the forecast's own keys.
export function isProjectionObjectKey(key) {
  if (key === "projection/refresh.json") return true;
  if (/^projection\/(?:receipts\/[A-Za-z0-9_-]{1,80}\.json|blobs\/[a-f0-9]{64}\.tar\.gz)$/.test(key)) return true;
  return /^projection\/(?:(?:latest\.json|history\.tar\.gz|audit\.tar\.gz)|(?:rounds|issues)\/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\.json)$/.test(key);
}

export function isImmutableProjectionObjectKey(key) {
  return /^projection\/(?:issues\/[^/]+\.json|receipts\/[A-Za-z0-9_-]{1,80}\.json|blobs\/[a-f0-9]{64}\.tar\.gz)$/.test(key);
}
