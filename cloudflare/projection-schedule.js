export async function runProjectionSchedule(env, getContainer) {
  const container = getContainer(env.MONITORAMENTO, "rio-taquari");
  const response = await container.fetch(new Request("http://container/api/internal/projection-refresh", {
    method: "POST",
    headers: { authorization: `Bearer ${env.PUSH_INTERNAL_SECRET}` },
    signal: AbortSignal.timeout(13 * 60_000),
  }));
  if (!response.ok) throw new Error(`Projection refresh returned ${response.status}`);
  console.log("[projection] scheduled refresh completed", await response.json());
}
