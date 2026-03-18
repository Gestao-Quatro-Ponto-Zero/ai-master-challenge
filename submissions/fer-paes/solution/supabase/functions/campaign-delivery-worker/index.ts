import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface PendingDelivery {
  id:             string;
  campaign_id:    string;
  customer_id:    string;
  customer_name:  string;
  customer_email: string;
  customer_phone: string;
  channel:        string;
  message_body:   string | null;
  retry_count:    number;
}

async function simulateSend(delivery: PendingDelivery): Promise<{ success: boolean; error?: string }> {
  const failRate = delivery.retry_count >= 2 ? 0.05 : 0.08;
  if (Math.random() < failRate) {
    return { success: false, error: `Delivery failed for channel ${delivery.channel}` };
  }
  return { success: true };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );

    const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
    const batchSize: number = body.batch_size ?? 50;

    const { data: pendingData, error: fetchError } = await supabase.rpc(
      "get_pending_deliveries",
      { p_limit: batchSize },
    );

    if (fetchError) {
      return new Response(
        JSON.stringify({ error: fetchError.message }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    const pending = (pendingData ?? []) as PendingDelivery[];
    const results: { id: string; status: string; channel: string; error?: string }[] = [];

    for (const delivery of pending) {
      await supabase.rpc("update_delivery_status", {
        p_id:     delivery.id,
        p_status: "sending",
        p_error:  null,
      });

      const result = await simulateSend(delivery);

      if (result.success) {
        await supabase.rpc("update_delivery_status", {
          p_id:     delivery.id,
          p_status: "sent",
          p_error:  null,
        });

        await new Promise((r) => setTimeout(r, 20));

        await supabase.rpc("update_delivery_status", {
          p_id:     delivery.id,
          p_status: "delivered",
          p_error:  null,
        });

        results.push({ id: delivery.id, status: "delivered", channel: delivery.channel });
      } else {
        await supabase.rpc("update_delivery_status", {
          p_id:     delivery.id,
          p_status: "failed",
          p_error:  result.error,
        });

        results.push({ id: delivery.id, status: "failed", channel: delivery.channel, error: result.error });
      }
    }

    const summary = {
      processed: results.length,
      delivered: results.filter((r) => r.status === "delivered").length,
      failed:    results.filter((r) => r.status === "failed").length,
      results,
      ran_at:    new Date().toISOString(),
    };

    return new Response(
      JSON.stringify(summary),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : String(err) }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }
});
