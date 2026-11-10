// Rodar a rotina na hora (teste manual), com o mesmo segredo do cron. Se o dia já rodou, não roda de novo,
// a não ser com ?forcar=1: aí roda, registra "rotina_forcada" e não apaga nada (o cron diário nunca força).
import type { NextRequest } from "next/server";
import { responderRotina } from "@/server/motor/responder";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export const POST = (req: NextRequest) => responderRotina(req, "manual", { forcar: req.nextUrl.searchParams.get("forcar") === "1" });
