import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";
import {
  SACE_LEVEL_SENSORS,
  SACE_STATIONS,
  severityFor,
} from "@/lib/hydro";

export const dynamic = "force-dynamic";

type LevelRow = {
  timestamp: string;
  level: number;
};

const DCRS_SENSOR = {
  id: "dcrs-00091",
  code: "DCRS-00091",
  city: "Muçum",
  name: "Sensor na Barra do Guaporé",
  source: "Rede RS",
} as const;

export async function GET(request: Request) {
  const requested = Number(
    new URL(request.url).searchParams.get("hours") || 24,
  );
  const hours = [1, 3, 6, 8, 12, 24, 48].includes(requested)
    ? requested
    : 24;
  const historyHours = Math.max(hours, 3);
  const database = openReaderDatabase();

  if (!database) {
    return NextResponse.json(
      { stations: [], message: "Worker ainda não inicializou o banco" },
      { status: 503 },
    );
  }

  try {
    const dcrsHistory = database
      .prepare(`
        SELECT timestamp, level
        FROM river_readings
        WHERE station = ?
          AND level IS NOT NULL
          AND julianday(timestamp) >= (
            SELECT MAX(julianday(timestamp)) - (? / 24.0)
            FROM river_readings
            WHERE station = ?
          )
        ORDER BY julianday(timestamp) ASC
      `)
      .all(
        DCRS_SENSOR.code,
        historyHours,
        DCRS_SENSOR.code,
      ) as LevelRow[];

    const saceStatement = database.prepare(`
      SELECT timestamp, level
      FROM sace_readings
      WHERE station = ?
        AND julianday(timestamp) >= (
          SELECT MAX(julianday(timestamp)) - (? / 24.0)
          FROM sace_readings
          WHERE station = ?
        )
      ORDER BY julianday(timestamp) ASC
    `);

    const stations = [
      {
        ...DCRS_SENSOR,
        current: dcrsHistory.at(-1) || null,
        history: dcrsHistory,
        thresholds: null,
        severity: "unavailable",
      },
      ...SACE_LEVEL_SENSORS.map((sensor) => {
        const history = saceStatement.all(
          sensor.code,
          historyHours,
          sensor.code,
        ) as LevelRow[];
        const current = history.at(-1) || null;
        const thresholds =
          SACE_STATIONS.find((station) => station.code === sensor.code)
            ?.thresholds ?? null;
        return {
          id: sensor.id,
          code: sensor.code,
          city: sensor.city,
          name: sensor.name,
          source: "SACE/SGB",
          current,
          history,
          thresholds,
          severity: thresholds
            ? severityFor(current?.level ?? null, thresholds)
            : "unavailable",
        };
      }),
    ];

    return NextResponse.json(
      {
        hours,
        stations,
        provenance: "sqlite-worker",
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
