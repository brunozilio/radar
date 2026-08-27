import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export const dynamic = "force-dynamic";

export async function GET() {
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json({ alerts: [] }, { status: 503 });
  }
  try {
    const rows = database
      .prepare(`
        SELECT
          alert.id,
          alert.title,
          alert.summary,
          alert.published_at,
          alert.valid_until,
          alert.severity,
          asset.id AS asset_id
        FROM alerts AS alert
        LEFT JOIN stored_assets AS asset
          ON asset.owner_type = 'alert-image'
          AND asset.owner_id = alert.id
        WHERE julianday(alert.valid_until) > julianday(?)
        ORDER BY julianday(alert.published_at) DESC
      `)
      .all(new Date().toISOString()) as Array<{
      id: string;
      title: string;
      summary: string;
      published_at: string;
      valid_until: string;
      severity: "yellow" | "orange" | "red";
      asset_id: string | null;
    }>;
    return NextResponse.json(
      {
        alerts: rows.map((row) => ({
          id: row.id,
          title: row.title,
          summary: row.summary,
          publishedAt: row.published_at,
          validUntil: row.valid_until,
          severity: row.severity,
          href: row.asset_id
            ? `/api/assets/${row.asset_id}`
            : `/api/alerts/image?id=${encodeURIComponent(row.id)}`,
        })),
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
