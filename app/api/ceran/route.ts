import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";
import { CERAN_PLANT_SOURCES } from "@/lib/sources";

export const dynamic = "force-dynamic";

type PlantId = keyof typeof CERAN_PLANT_SOURCES;

export async function GET(request: Request) {
  const requested = new URL(request.url).searchParams.get("plant") as PlantId;
  const plant = CERAN_PLANT_SOURCES[requested] || CERAN_PLANT_SOURCES.castro;
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json(
      { plant, current: null, history: [] },
      { status: 503 },
    );
  }
  try {
    const cutoff = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString();
    const rows = database
      .prepare(`
        SELECT timestamp, upstream_level, downstream_level, inflow, turbined,
               spilled, residual, outflow, status
        FROM ceran_readings
        WHERE plant_id = ? AND julianday(timestamp) >= julianday(?)
        ORDER BY julianday(timestamp) DESC
      `)
      .all(plant.id, cutoff) as Array<{
      timestamp: string;
      upstream_level: number;
      downstream_level: number;
      inflow: number;
      turbined: number;
      spilled: number;
      residual: number;
      outflow: number;
      status: string;
    }>;
    const history = rows.map((row) => ({
      timestamp: row.timestamp,
      upstreamLevel: row.upstream_level,
      downstreamLevel: row.downstream_level,
      inflow: row.inflow,
      turbined: row.turbined,
      spilled: row.spilled,
      residual: row.residual,
      outflow: row.outflow,
      status: row.status,
    }));
    return NextResponse.json(
      {
        plant: { id: plant.id, name: plant.name },
        current: history[0] || null,
        history,
        provenance: "sqlite-worker",
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
