import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";
import { framesWithinLatestHour } from "@/lib/media-window";

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
        SELECT id, captured_at
        FROM media_frames
        WHERE kind = 'radar-concordia'
          AND source_key LIKE 'radar-sc:CHP:0:basin-overlay-v2:%'
          AND julianday(captured_at) >= julianday(?)
          AND julianday(captured_at) <= julianday(?)
        ORDER BY julianday(captured_at) ASC, julianday(created_at) ASC
        LIMIT 60
      `)
      .all(cutoff, now) as Array<{ id: string; captured_at: string }>;
    const frames = framesWithinLatestHour(
      rows.map((row) => ({
        id: row.id,
        timestamp: row.captured_at,
        src: `/api/media/${row.id}`,
      })),
      nowMs,
    );
    return NextResponse.json(
      { frames },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
