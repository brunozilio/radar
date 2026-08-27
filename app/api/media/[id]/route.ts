import { existsSync, readFileSync } from "node:fs";
import { NextResponse } from "next/server";
import { openReaderDatabase } from "@/lib/database";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  if (!/^[a-f0-9]{64}$/.test(id)) {
    return NextResponse.json({ message: "Imagem inválida" }, { status: 400 });
  }
  const database = openReaderDatabase();
  if (!database) {
    return NextResponse.json({ message: "Imagem indisponível" }, { status: 404 });
  }
  try {
    const row = database
      .prepare(
        "SELECT file_path, mime_type FROM media_frames WHERE id = ? LIMIT 1",
      )
      .get(id) as { file_path: string; mime_type: string } | undefined;
    if (!row || !existsSync(row.file_path)) {
      return NextResponse.json(
        { message: "Imagem não encontrada" },
        { status: 404 },
      );
    }
    return new NextResponse(
      readFileSync(/* turbopackIgnore: true */ row.file_path),
      {
      headers: {
        "content-type": row.mime_type,
        "cache-control": "public, max-age=86400, immutable",
      },
      },
    );
  } finally {
    database.close();
  }
}
