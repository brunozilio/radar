import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";
import { framesFromMostRecentProvider } from "@/lib/media-window";

export const dynamic = "force-dynamic";

export async function GET() {
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json(
      { frames: [], message: "Worker ainda não inicializou o banco" },
      { status: 503 },
    );
  }
  try {
    const nowMs = Date.now();
    const now = new Date(nowMs).toISOString();
    const cutoff = new Date(nowMs - 3 * 60 * 60 * 1000).toISOString();
    const rows = database
      .prepare(`
        SELECT id, captured_at, source_url
        FROM media_frames
        WHERE kind = 'satellite-enhanced'
          AND julianday(captured_at) >= julianday(?)
          AND julianday(captured_at) <= julianday(?)
        ORDER BY julianday(captured_at) ASC, julianday(created_at) ASC
        LIMIT 60
      `)
      .all(cutoff, now) as Array<{
        id: string;
        captured_at: string;
        source_url: string;
      }>;
    const frames = framesFromMostRecentProvider(
      rows.map((row) => ({
        id: row.id,
        timestamp: row.captured_at,
        src: `/api/media/${row.id}`,
        provider: row.source_url.includes("cptec.inpe.br")
          ? "cptec"
          : "inmet",
      })),
      nowMs,
      "inmet",
    );
    return NextResponse.json(
      { frames },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
