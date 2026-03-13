/**
 * /api/admin/settings
 *
 * GET  — returns { slack_configured: bool, slack_webhook_masked?: string }
 * POST — { key: "slack_webhook_url", value: "https://..." } → upserts to app_settings
 *
 * Requires `app_settings` table in Supabase:
 *   CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMPTZ DEFAULT NOW());
 */

import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export const dynamic = "force-dynamic";

const TABLE = "app_settings";

function maskUrl(url: string): string {
  // Show first 40 chars then "..."
  return url.length > 40 ? url.substring(0, 40) + "…" : url;
}

export async function GET() {
  const { data, error } = await supabaseAdmin
    .from(TABLE)
    .select("key, value")
    .eq("key", "slack_webhook_url")
    .limit(1);

  if (error) {
    const missing = error.message?.toLowerCase().includes("does not exist") ||
                    error.code === "42P01" ||
                    (error as { details?: string }).details?.includes("does not exist");
    if (missing) {
      return NextResponse.json({ slack_configured: false, table_missing: true });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const row = data?.[0];
  if (!row?.value) {
    return NextResponse.json({ slack_configured: false });
  }

  return NextResponse.json({
    slack_configured: true,
    slack_webhook_masked: maskUrl(row.value),
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json() as { key: string; value: string };

  if (!body.key || !body.value) {
    return NextResponse.json({ error: "key e value são obrigatórios." }, { status: 400 });
  }

  const { error } = await supabaseAdmin
    .from(TABLE)
    .upsert({ key: body.key, value: body.value, updated_at: new Date().toISOString() });

  if (error) {
    const missing = error.message?.toLowerCase().includes("does not exist") ||
                    error.code === "42P01";
    if (missing) {
      return NextResponse.json({ error: "table_missing" }, { status: 404 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ success: true });
}
