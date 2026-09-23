import { listProjectionRounds, readProjection, readProjectionRefreshState } from "@/lib/projection-server";
import { projectionForStation, projectionIsStale } from "@/lib/projection";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const round = params.get("round") || undefined;
  const station = params.get("station") || "mucum";
  if (station !== "mucum") return Response.json({ message: "Previsão disponível apenas para Muçum" }, { status: 400 });
  if (round && (!Number.isFinite(Date.parse(round)) || new Date(round).toISOString() !== round)) return Response.json({ message: "Rodada inválida" }, { status: 400 });
  try {
    const [stored, rounds, refresh] = await Promise.all([readProjection(round), listProjectionRounds(), readProjectionRefreshState().catch(() => null)]);
    const projection = projectionForStation(stored, station, round);
    const failed = !round && refresh?.status === "failed";
    return Response.json({ projection, rounds, refresh: round ? null : refresh, failed, stale: failed || (projection ? projectionIsStale(projection) : false) }, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ message: "Projeção temporariamente indisponível" }, { status: 503 });
  }
}
