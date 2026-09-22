import { listProjectionRounds, readProjection } from "@/lib/projection-server";
import { projectionForStation, projectionIsStale } from "@/lib/projection";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const round = params.get("round") || undefined;
  const station = params.get("station") || "mucum";
  if (station !== "mucum" && station !== "encantado" && station !== "santa-tereza") return Response.json({ message: "Estação inválida" }, { status: 400 });
  if (round && (!Number.isFinite(Date.parse(round)) || new Date(round).toISOString() !== round)) return Response.json({ message: "Rodada inválida" }, { status: 400 });
  try {
    const [stored, rounds] = await Promise.all([readProjection(round), listProjectionRounds()]);
    const projection = projectionForStation(stored, station, round);
    const failed = Boolean(stored?.stationErrors?.[station]);
    return Response.json({ projection, rounds, failed, stale: failed || (projection ? projectionIsStale(projection) : false) }, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ message: "Projeção temporariamente indisponível" }, { status: 503 });
  }
}
