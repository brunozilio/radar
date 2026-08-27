import { existsSync, readFileSync } from "node:fs";
import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  if (!/^[a-f0-9]{64}$/.test(id)) {
    return NextResponse.json({ message: "Arquivo inválido" }, { status: 400 });
  }

  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json({ message: "Arquivo indisponível" }, { status: 404 });
  }

  try {
    const row = database
      .prepare(`
        SELECT file_path, file_name, mime_type
        FROM stored_assets
        WHERE id = ?
        LIMIT 1
      `)
      .get(id) as
      | { file_path: string; file_name: string; mime_type: string }
      | undefined;
    if (!row || !existsSync(/* turbopackIgnore: true */ row.file_path)) {
      return NextResponse.json(
        { message: "Arquivo não encontrado" },
        { status: 404 },
      );
    }

    return new NextResponse(
      readFileSync(/* turbopackIgnore: true */ row.file_path),
      {
        headers: {
          "content-type": row.mime_type,
          "content-disposition": `inline; filename="${row.file_name}"`,
          "cache-control": "public, max-age=86400, immutable",
          "x-content-type-options": "nosniff",
        },
      },
    );
  } finally {
    database.close();
  }
}
