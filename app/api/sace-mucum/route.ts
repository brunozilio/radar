import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export const dynamic = "force-dynamic";

export async function GET() {
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json(
      { message: "Worker ainda não inicializou o banco" },
      { status: 503 },
    );
  }
  try {
    const row = database
      .prepare(`
        SELECT timestamp, level, level_cm
        FROM sace_readings
        WHERE station = '86510000'
        ORDER BY timestamp DESC
        LIMIT 1
      `)
      .get() as
      | { timestamp: string; level: number; level_cm: number }
      | undefined;
    if (!row) {
      return NextResponse.json(
        { message: "SACE ainda não foi sincronizado" },
        { status: 503 },
      );
    }
    return NextResponse.json(
      {
        code: "86510000",
        city: "Muçum",
        name: "Muçum",
        timestamp: row.timestamp,
        level: row.level,
        levelCm: row.level_cm,
        source: "SACE/SGB",
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
