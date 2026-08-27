import { existsSync, readFileSync } from "node:fs";
import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const id = new URL(request.url).searchParams.get("id");
  if (!id) {
    return NextResponse.json({ message: "Alerta inválido" }, { status: 400 });
  }

  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json({ message: "Alerta indisponível" }, { status: 503 });
  }

  try {
    const row = database
      .prepare(`
        SELECT asset.file_path, asset.mime_type
        FROM alerts AS alert
        INNER JOIN stored_assets AS asset
          ON asset.owner_type = 'alert-image'
          AND asset.owner_id = alert.id
        WHERE alert.id = ?
          AND julianday(alert.valid_until) > julianday(?)
        LIMIT 1
      `)
      .get(id, new Date().toISOString()) as
      | { file_path: string; mime_type: string }
      | undefined;
    if (!row || !existsSync(/* turbopackIgnore: true */ row.file_path)) {
      return NextResponse.json(
        { message: "Imagem do alerta não encontrada" },
        { status: 404 },
      );
    }

    return new NextResponse(
      readFileSync(/* turbopackIgnore: true */ row.file_path),
      {
        headers: {
          "content-type": row.mime_type,
          "content-disposition": "inline",
          "cache-control": "public, max-age=300, stale-while-revalidate=3600",
          "x-content-type-options": "nosniff",
        },
      },
    );
  } finally {
    database.close();
  }
}
