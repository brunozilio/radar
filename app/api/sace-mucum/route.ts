import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

import { readLevelHistory } from "@/lib/river-levels";

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
    const row = readLevelHistory(database, "86510000", 1).at(-1);
    if (!row) {
      return NextResponse.json(
        { message: "Níveis ANA/SACE ainda não foram sincronizados" },
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
        levelCm: row.levelCm,
        source: row.source,
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
