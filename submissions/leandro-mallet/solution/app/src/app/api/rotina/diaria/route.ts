// Rotina diária do score, chamada pelo cron da Vercel (vercel.json: todo dia às 06:00 UTC = 03:00 de Brasília).
// Protegida por CRON_SECRET (Authorization: Bearer). Idempotente pelo dia de negócio.
import type { NextRequest } from "next/server";
import { responderRotina } from "@/server/motor/responder";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export const GET = (req: NextRequest) => responderRotina(req, "cron");
