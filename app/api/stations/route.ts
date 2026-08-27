import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";
import {
  accumulatedRain,
  MUCUM_UPSTREAM_RAIN_STATIONS,
  severityFor,
  type AnaRecord,
} from "@/lib/hydro";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const requested = Number(new URL(request.url).searchParams.get("hours") || 24);
  const hours = [1, 3, 6, 8, 12, 24, 48].includes(requested)
    ? requested
    : 24;
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json(
      {
        hours,
        stations: [],
      },
      { status: 503 },
    );
  }

  try {
    const statement = database.prepare(`
      SELECT timestamp, rain, level_cm, discharge, quality
      FROM rain_readings
      WHERE station = ?
      ORDER BY timestamp DESC
    `);
    const stations = MUCUM_UPSTREAM_RAIN_STATIONS.map((station) => {
      const records = (statement.all(station.code) as Array<{
        timestamp: string;
        rain: number | null;
        level_cm: number | null;
        discharge: number | null;
        quality: AnaRecord["quality"];
      }>).map((row) => ({
        timestamp: row.timestamp,
        rain: row.rain,
        accumulatedRain: null,
        levelCm: row.level_cm,
        discharge: row.discharge,
        quality: row.quality,
      }));
      const latest = records[0] || null;
      const referenceMs = Date.now();
      const cutoff = referenceMs - hours * 60 * 60 * 1000;
      const rain = accumulatedRain(records, hours, referenceMs);
      const level =
        latest?.levelCm === null || latest?.levelCm === undefined
          ? null
          : Number((latest.levelCm / 100).toFixed(2));
      return {
        ...station,
        level,
        rain,
        discharge: latest?.discharge ?? null,
        timestamp: latest?.timestamp ?? null,
        quality: latest?.quality ?? "missing",
        severity: station.thresholds
          ? severityFor(level, station.thresholds)
          : "unavailable",
        samples: records.filter(
          (row) => Date.parse(row.timestamp) >= cutoff,
        ).length,
      };
    }).filter((station) => station.rain !== null);

    return NextResponse.json(
      { hours, generatedAt: new Date().toISOString(), stations },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
