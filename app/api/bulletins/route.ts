import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export const dynamic = "force-dynamic";

export async function GET() {
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json({ bulletins: [] }, { status: 503 });
  }
  try {
    const cutoff = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString();
    const rows = database
      .prepare(`
        SELECT id, title, published_at, status, asset_id
        FROM (
          SELECT
            bulletin.id,
            bulletin.title,
            bulletin.published_at,
            bulletin.status,
            bulletin.created_at,
            asset.id AS asset_id,
            ROW_NUMBER() OVER (
              PARTITION BY bulletin.published_at
              ORDER BY julianday(bulletin.created_at) DESC
            ) AS revision_rank
          FROM bulletins AS bulletin
          INNER JOIN stored_assets AS asset
            ON asset.owner_type = 'bulletin-pdf'
            AND asset.owner_id = bulletin.id
          WHERE
            julianday(bulletin.published_at) >= julianday(?)
            AND bulletin.href LIKE 'https://www.sgb.gov.br/sace/boletins/Taquari/%.pdf'
        )
        WHERE revision_rank = 1
        ORDER BY julianday(published_at) DESC
      `)
      .all(cutoff) as Array<{
      id: string;
      title: string;
      published_at: string;
      status: string;
      asset_id: string;
    }>;
    return NextResponse.json(
      {
        bulletins: rows.map((row, index) => ({
          id: row.id,
          title: row.title,
          date: row.published_at,
          status: index === 0 ? "Último boletim" : row.status,
          href: `/api/assets/${row.asset_id}`,
          latest: index === 0,
        })),
      },
      { headers: { "cache-control": "no-store, max-age=0" } },
    );
  } finally {
    database.close();
  }
}
