/**
 * POST /api/slack/report?type=morning|evening
 *
 * Loads deals, builds Slack Block Kit message, sends to webhook URL
 * stored in Supabase app_settings (or SLACK_WEBHOOK_URL env fallback).
 */

import { NextRequest, NextResponse } from "next/server";
import { loadDeals, calcAgentWinRates, loadPipeline } from "@/lib/data";
import { scoreDeals } from "@/lib/scoring";
import { buildMorningBlocks, buildEveningBlocks, sendSlackBlocks } from "@/lib/slack";
import { supabaseAdmin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

async function getWebhookUrl(): Promise<string | null> {
  // Env var takes priority (useful for CI/CD and Vercel)
  if (process.env.SLACK_WEBHOOK_URL) return process.env.SLACK_WEBHOOK_URL;

  // Fall back to Supabase app_settings
  const { data } = await supabaseAdmin
    .from("app_settings")
    .select("value")
    .eq("key", "slack_webhook_url")
    .limit(1)
    .single();

  return data?.value ?? null;
}

export async function POST(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const type = searchParams.get("type") ?? "morning";

  if (type !== "morning" && type !== "evening") {
    return NextResponse.json(
      { error: "Parâmetro 'type' deve ser 'morning' ou 'evening'." },
      { status: 400 }
    );
  }

  const webhookUrl = await getWebhookUrl();
  if (!webhookUrl) {
    return NextResponse.json(
      { error: "Slack não configurado. Cole a URL do webhook em Admin → 📡 Slack." },
      { status: 503 }
    );
  }

  try {
    const [rawDeals, pipeline] = await Promise.all([loadDeals(), loadPipeline()]);
    const winRates = calcAgentWinRates(pipeline);
    const deals    = scoreDeals(rawDeals, winRates);

    const blocks = type === "morning"
      ? buildMorningBlocks(deals)
      : buildEveningBlocks(deals);

    await sendSlackBlocks(webhookUrl, blocks);

    const active = deals.filter((d) => d.deal_stage === "Engaging" || d.deal_stage === "Prospecting");
    return NextResponse.json({ ok: true, type, sent: active.length });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
