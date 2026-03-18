import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface DueSchedule {
  id:               string;
  campaign_id:      string;
  campaign_name:    string;
  campaign_status:  string;
  schedule_type:    string;
  cron_expression:  string | null;
  event_type:       string | null;
  next_run_at:      string | null;
  last_run_at:      string | null;
  execution_count:  number;
}

function parseCronToNext(expr: string): string | null {
  try {
    const parts = expr.trim().split(/\s+/);
    if (parts.length !== 5) return null;

    const [min, hour, dom, month, dow] = parts;
    const now = new Date();

    if (min !== '*' && hour !== '*' && dom === '*' && month === '*' && dow === '*') {
      const next = new Date(now);
      next.setSeconds(0);
      next.setMilliseconds(0);
      next.setMinutes(parseInt(min));
      next.setHours(parseInt(hour));
      if (next <= now) next.setDate(next.getDate() + 1);
      return next.toISOString();
    }

    if (min !== '*' && hour !== '*' && dom === '*' && month === '*' && dow !== '*') {
      const targetDow = parseInt(dow);
      const next = new Date(now);
      next.setSeconds(0);
      next.setMilliseconds(0);
      next.setMinutes(parseInt(min));
      next.setHours(parseInt(hour));
      const diff = (targetDow - next.getDay() + 7) % 7 || 7;
      next.setDate(next.getDate() + diff);
      return next.toISOString();
    }

    if (min !== '*' && hour !== '*' && dom !== '*' && month === '*' && dow === '*') {
      const next = new Date(now);
      next.setSeconds(0);
      next.setMilliseconds(0);
      next.setMinutes(parseInt(min));
      next.setHours(parseInt(hour));
      next.setDate(parseInt(dom));
      if (next <= now) next.setMonth(next.getMonth() + 1);
      return next.toISOString();
    }

    if (min !== '*' && hour === '*') {
      const next = new Date(now);
      next.setSeconds(0);
      next.setMilliseconds(0);
      next.setMinutes(parseInt(min));
      if (next <= now) next.setTime(next.getTime() + 3600 * 1000);
      return next.toISOString();
    }

    const next = new Date(now.getTime() + 60 * 60 * 1000);
    return next.toISOString();
  } catch {
    return null;
  }
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

    const { data: dueData, error: dueError } = await supabase.rpc("get_due_schedules");

    if (dueError) {
      return new Response(
        JSON.stringify({ error: dueError.message }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }

    const dueSchedules = (dueData ?? []) as DueSchedule[];
    const results: { id: string; campaign: string; status: string; next?: string | null }[] = [];

    for (const schedule of dueSchedules) {
      try {
        let nextRunAt: string | null = null;

        if (schedule.schedule_type === "recurring" && schedule.cron_expression) {
          nextRunAt = parseCronToNext(schedule.cron_expression);
        }

        const { error: markError } = await supabase.rpc("mark_schedule_executed", {
          p_id:          schedule.id,
          p_next_run_at: nextRunAt,
        });

        if (markError) throw new Error(markError.message);

        if (schedule.campaign_status === "scheduled") {
          await supabase.rpc("activate_campaign", { p_id: schedule.campaign_id })
            .catch(() => {});
        }

        results.push({
          id:       schedule.id,
          campaign: schedule.campaign_name,
          status:   "executed",
          next:     nextRunAt,
        });
      } catch (err) {
        results.push({
          id:       schedule.id,
          campaign: schedule.campaign_name,
          status:   `error: ${err instanceof Error ? err.message : String(err)}`,
        });
      }
    }

    return new Response(
      JSON.stringify({
        processed: results.length,
        results,
        ran_at:    new Date().toISOString(),
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : String(err) }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }
});
