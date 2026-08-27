import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export const dynamic = "force-dynamic";

type RiverRow = {
  station: string;
  timestamp: string;
  level: number | null;
  raw_level: number | null;
  trend_value: number | null;
  trend: "rising" | "falling" | "stable";
};

export async function GET(request: Request) {
  const url = new URL(request.url);
  const mode = url.searchParams.get("mode") || "current";
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json(
      { status: "unavailable", message: "Worker ainda não inicializou o banco" },
      { status: 503 },
    );
  }
  try {
    const latest = database
      .prepare(`
        SELECT station, timestamp, level, raw_level, trend_value, trend
        FROM river_readings
        WHERE station = 'DCRS-00091'
        ORDER BY timestamp DESC
        LIMIT 1
      `)
      .get() as RiverRow | undefined;

    if (mode === "history") {
      const requested = Number(url.searchParams.get("hours") || 24);
      const hours = [1, 3, 6, 8, 12, 24, 48].includes(requested)
        ? requested
        : 24;
      const reference = latest ? Date.parse(latest.timestamp) : Date.now();
      const cutoff = new Date(reference - hours * 60 * 60 * 1000).toISOString();
      const rows = database
        .prepare(`
          SELECT timestamp, level
          FROM river_readings
          WHERE station = 'DCRS-00091'
            AND julianday(timestamp) >= julianday(?)
            AND level IS NOT NULL
          ORDER BY julianday(timestamp) ASC
        `)
        .all(cutoff) as Array<{ timestamp: string; level: number }>;
      return NextResponse.json(
        {
          station: "DCRS-00091",
          hours,
          points: rows,
          status: "sqlite-worker",
        },
        { headers: { "cache-control": "no-store, max-age=0" } },
      );
    }

    if (!latest) {
      return NextResponse.json(
        { status: "unavailable", message: "Aguardando primeira leitura ao vivo" },
        { status: 503 },
      );
    }
    return NextResponse.json(
      {
        station: latest.station,
        name: "Muçum/Encantado",
        basin: "Rio Taquari-Antas",
        latitude: -29.1682,
        longitude: -51.8868,
        level: latest.level,
        rawLevel: latest.raw_level,
        datumOffset: -32.7,
        trend: latest.trend,
        trendValue: latest.trend_value,
        timestamp: latest.timestamp,
        rain: {},
        source: "Defesa Civil RS / MKS",
        provenance: "sqlite-worker",
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
