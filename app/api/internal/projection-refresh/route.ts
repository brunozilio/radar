import { timingSafeEqual } from "node:crypto";
import { refreshProjection } from "@/lib/projection-server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request) {
  const secret = process.env.PUSH_INTERNAL_SECRET;
  const supplied = request.headers.get("authorization") || "";
  const expected = secret ? `Bearer ${secret}` : "";
  if (!expected || Buffer.byteLength(supplied) !== Buffer.byteLength(expected) ||
      !timingSafeEqual(Buffer.from(supplied), Buffer.from(expected))) {
    return Response.json({ message: "Não autorizado" }, { status: 401 });
  }
  try {
    const result = await refreshProjection();
    return Response.json(result);
  } catch (error) {
    console.error("[projection] refresh failed", error instanceof Error ? error.message : "Unknown refresh error");
    return Response.json({ message: "Falha no cálculo; última projeção preservada" }, { status: 503 });
  }
}
