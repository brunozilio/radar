// Extend the existing private R2 bridge only with the forecast's own keys.
export function isProjectionObjectKey(key) {
  return /^projection\/(?:(?:latest\.json|history\.tar\.gz|audit\.tar\.gz)|(?:rounds|issues)\/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})\.json)$/.test(key);
}
