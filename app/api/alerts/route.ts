import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export const dynamic = "force-dynamic";

export async function GET() {
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json(
      { alerts: [], message: "Banco de alertas indisponível" },
      { status: 503 },
    );
  }
  try {
    const now = new Date().toISOString();
    const hasSourceStatus = Boolean(
      database
        .prepare(`
          SELECT 1
          FROM sqlite_master
          WHERE type = 'table' AND name = 'source_status'
          LIMIT 1
        `)
        .get(),
    );
    const sourceRows = (hasSourceStatus
      ? database
          .prepare(`
            SELECT source, status, checked_at, message
            FROM source_status
            WHERE source IN ('defesa-civil', 'inmet')
          `)
          .all()
      : []) as Array<{
      source: "defesa-civil" | "inmet";
      status: "ok" | "error";
      checked_at: string;
      message: string | null;
    }>;
    const sourceStatus = new Map(sourceRows.map((row) => [row.source, row]));
    const sources = ([
      ["defesa-civil", "Defesa Civil RS"],
      ["inmet", "INMET"],
    ] as const).map(([id, name]) => {
      const row = sourceStatus.get(id);
      return {
        id,
        name,
        status: row?.status || "checking",
        checkedAt: row?.checked_at || null,
        message: row?.message || null,
      };
    });
    const collectionStatus = sources.some((source) => source.status === "error")
      ? "degraded"
      : sources.every((source) => source.status === "ok")
        ? "ok"
        : "checking";
    const rows = database
      .prepare(`
        SELECT
          alert.id,
          alert.title,
          alert.summary,
          alert.published_at,
          alert.valid_until,
          alert.severity,
          alert.href AS source_url,
          asset.id AS asset_id
        FROM alerts AS alert
        LEFT JOIN stored_assets AS asset
          ON asset.owner_type = 'alert-image'
          AND asset.owner_id = alert.id
        WHERE julianday(alert.valid_until) > julianday(?)
          AND julianday(alert.published_at) <= julianday(?)
        ORDER BY julianday(alert.published_at) DESC
      `)
      .all(now, now) as Array<{
      id: string;
      title: string;
      summary: string;
      published_at: string;
      valid_until: string;
      severity: "yellow" | "orange" | "red";
      source_url: string;
      asset_id: string | null;
    }>;
    return NextResponse.json(
      {
        status: collectionStatus,
        sources,
        alerts: rows.map((row) => {
          const imageUrl = row.asset_id
            ? `/api/assets/${row.asset_id}`
            : null;
          return {
            id: row.id,
            title: row.title,
            summary: row.summary,
            publishedAt: row.published_at,
            validUntil: row.valid_until,
            severity: row.severity,
            source: row.id.startsWith("inmet:")
              ? "INMET"
              : "Defesa Civil RS",
            sourceUrl: row.source_url,
            imageUrl,
            // Clientes antigos ainda tratam `href` estritamente como imagem.
            href: imageUrl || "/og-monitoramento.png",
          };
        }),
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
