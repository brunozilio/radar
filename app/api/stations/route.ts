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
      LIMIT 600
    `);
    const referenceMs = Date.now();
    const cutoff = referenceMs - hours * 60 * 60 * 1000;
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
      const validRecords = records.filter(
        (row) => row.rain !== null && Number.isFinite(row.rain) && row.rain >= 0,
      );
      const windowRecords = validRecords.filter((row) => {
        const time = Date.parse(row.timestamp);
        return time >= cutoff && time <= referenceMs;
      });
      const recentTimes = validRecords
        .map((row) => Date.parse(row.timestamp))
        .filter((time) => Number.isFinite(time) && time >= referenceMs - 48 * 60 * 60 * 1000 && time <= referenceMs)
        .sort((a, b) => a - b);
      const intervals = recentTimes.slice(1).map((time, index) =>
        (time - recentTimes[index]) / 60_000,
      ).filter((minutes) => minutes >= 5 && minutes <= 90).sort((a, b) => a - b);
      const cadenceMinutes = Math.max(
        15,
        Math.min(60, intervals.length ? intervals[Math.floor(intervals.length / 2)] : 60),
      );
      const expectedSamples = Math.max(1, Math.round((hours * 60) / cadenceMinutes));
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
        timestamp: windowRecords[0]?.timestamp ?? null,
        quality: windowRecords[0]?.quality ?? "missing",
        severity: station.thresholds
          ? severityFor(level, station.thresholds)
          : "unavailable",
        samples: windowRecords.length,
        expectedSamples,
        coverage: Math.min(1, Number((windowRecords.length / expectedSamples).toFixed(2))),
      };
    });

    return NextResponse.json(
      { hours, generatedAt: new Date().toISOString(), stations },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
