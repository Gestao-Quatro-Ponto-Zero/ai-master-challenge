import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey, X-API-Key",
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function err(message: string, status = 400, code?: string) {
  return json({ error: message, ...(code ? { code } : {}) }, status);
}

async function hashKey(key: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(key);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const startedAt = Date.now();

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  const url = new URL(req.url);
  const path = url.pathname.replace(/^.*\/channel-ingest/, "");
  const ipAddress = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? null;

  let apiKeyRecord: { id: string; key_prefix: string; scopes: string[]; channel_type: string | null } | null = null;
  let requestBody: Record<string, unknown> = {};
  let responseData: unknown = null;
  let responseStatus = 200;
  let errorMessage: string | null = null;

  async function logRequest() {
    try {
      await supabase.from("integration_logs").insert({
        api_key_id: apiKeyRecord?.id ?? null,
        key_prefix: apiKeyRecord?.key_prefix ?? null,
        endpoint: `/channel-ingest${path}`,
        method: req.method,
        status_code: responseStatus,
        ip_address: ipAddress,
        request_payload: requestBody,
        response_payload: responseData as Record<string, unknown> | null,
        error_message: errorMessage,
        duration_ms: Date.now() - startedAt,
      });

      if (apiKeyRecord?.id) {
        await supabase.rpc("increment_api_key_count", { key_id: apiKeyRecord.id });
      }
    } catch {
    }
  }

  async function respond(response: Response): Promise<Response> {
    responseStatus = response.status;
    try {
      const clone = response.clone();
      responseData = await clone.json().catch(() => null);
    } catch {
    }
    await logRequest();
    return response;
  }

  try {
    if (req.method !== "POST") {
      errorMessage = "Method not allowed";
      responseStatus = 405;
      await logRequest();
      return err("Method not allowed", 405);
    }

    const rawApiKey = req.headers.get("x-api-key") ?? req.headers.get("X-API-Key");
    const authHeader = req.headers.get("authorization") ?? "";
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "";

    const isSupabaseAuth =
      authHeader.startsWith("Bearer ") &&
      authHeader.slice(7) !== anonKey &&
      authHeader.length > 40;

    if (!rawApiKey && !isSupabaseAuth) {
      errorMessage = "Authentication required";
      responseStatus = 401;
      await logRequest();
      return err("Authentication required. Provide X-API-Key header.", 401, "MISSING_API_KEY");
    }

    if (rawApiKey) {
      const keyHash = await hashKey(rawApiKey);
      const keyPrefix = rawApiKey.slice(0, 16);

      const { data: keyData } = await supabase
        .from("api_keys")
        .select("id, key_prefix, scopes, channel_type, is_active, expires_at, rate_limit_per_minute")
        .eq("key_hash", keyHash)
        .maybeSingle();

      if (!keyData) {
        errorMessage = "Invalid API key";
        responseStatus = 401;
        await logRequest();
        return err("Invalid API key.", 401, "INVALID_API_KEY");
      }

      if (!keyData.is_active) {
        errorMessage = "API key is inactive";
        responseStatus = 401;
        await logRequest();
        return err("This API key has been deactivated.", 401, "KEY_INACTIVE");
      }

      if (keyData.expires_at && new Date(keyData.expires_at) < new Date()) {
        errorMessage = "API key expired";
        responseStatus = 401;
        await logRequest();
        return err("This API key has expired.", 401, "KEY_EXPIRED");
      }

      if (!keyData.scopes.includes("channel:ingest")) {
        errorMessage = "Missing scope: channel:ingest";
        responseStatus = 403;
        await logRequest();
        return err("This key does not have the 'channel:ingest' scope.", 403, "INSUFFICIENT_SCOPE");
      }

      const channelType = path.replace("/", "");
      if (keyData.channel_type && keyData.channel_type !== channelType) {
        errorMessage = `Key restricted to channel: ${keyData.channel_type}`;
        responseStatus = 403;
        await logRequest();
        return err(
          `This key is restricted to the '${keyData.channel_type}' channel.`,
          403,
          "CHANNEL_MISMATCH",
        );
      }

      apiKeyRecord = { id: keyData.id, key_prefix: keyPrefix, scopes: keyData.scopes, channel_type: keyData.channel_type };
    }

    let body: Record<string, unknown>;
    try {
      body = await req.json();
      requestBody = body;
    } catch {
      return respond(err("Invalid JSON body"));
    }

    async function getChannelByType(type: string) {
      const { data, error } = await supabase
        .from("channels")
        .select("*")
        .eq("type", type)
        .eq("is_active", true)
        .maybeSingle();
      if (error) throw new Error(error.message);
      return data;
    }

    async function identifyOrCreateCustomer(payload: {
      name?: string | null;
      email?: string | null;
      phone?: string | null;
      external_id?: string | null;
      external_source?: string | null;
    }) {
      let customer = null;

      if (payload.external_id) {
        const q = supabase
          .from("customers")
          .select("*")
          .eq("external_id", payload.external_id);
        if (payload.external_source) q.eq("external_source", payload.external_source);
        const { data } = await q.maybeSingle();
        if (data) customer = data;
      }

      if (!customer && payload.email) {
        const { data } = await supabase
          .from("customers")
          .select("*")
          .eq("email", payload.email)
          .maybeSingle();
        if (data) customer = data;
      }

      if (!customer && payload.phone) {
        const { data } = await supabase
          .from("customers")
          .select("*")
          .eq("phone", payload.phone)
          .maybeSingle();
        if (data) customer = data;
      }

      if (!customer) {
        const { data, error } = await supabase
          .from("customers")
          .insert({
            name: payload.name ?? null,
            email: payload.email ?? null,
            phone: payload.phone ?? null,
            external_id: payload.external_id ?? null,
            external_source: payload.external_source ?? null,
          })
          .select()
          .single();
        if (error) throw new Error(error.message);
        customer = data;
      }

      return customer;
    }

    async function findOpenTicket(customerId: string, channelId: string) {
      const { data } = await supabase
        .from("tickets")
        .select("id, status, conversations(*)")
        .eq("customer_id", customerId)
        .eq("channel_id", channelId)
        .not("status", "in", '("closed","resolved")')
        .order("updated_at", { ascending: false })
        .limit(1)
        .maybeSingle();
      return data;
    }

    async function createTicket(
      customerId: string,
      channelId: string,
      subject: string | null,
      initialMessage: string,
      priority: string,
      source: string,
    ) {
      const { data: ticket, error: ticketError } = await supabase
        .from("tickets")
        .insert({
          customer_id: customerId,
          channel_id: channelId,
          subject: subject ?? null,
          status: "open",
          priority,
          source,
        })
        .select()
        .single();
      if (ticketError) throw new Error(ticketError.message);

      const now = new Date().toISOString();
      const { data: conv, error: convError } = await supabase
        .from("conversations")
        .insert({ ticket_id: ticket.id, started_at: now, last_message_at: now })
        .select()
        .single();
      if (convError) throw new Error(convError.message);

      const { data: msg, error: msgError } = await supabase
        .from("messages")
        .insert({
          conversation_id: conv.id,
          sender_type: "customer",
          sender_id: customerId,
          message: initialMessage,
          message_type: "text",
        })
        .select("id")
        .single();
      if (msgError) throw new Error(msgError.message);

      return { ticket, conv, messageId: msg.id };
    }

    async function addMessage(
      convId: string,
      customerId: string,
      content: string,
      messageType: string,
      attachments: { file_url: string; file_type: string; file_size: number }[],
    ) {
      const { data: msg, error: msgError } = await supabase
        .from("messages")
        .insert({
          conversation_id: convId,
          sender_type: "customer",
          sender_id: customerId,
          message: content,
          message_type: messageType ?? "text",
        })
        .select("id")
        .single();
      if (msgError) throw new Error(msgError.message);

      if (attachments && attachments.length > 0) {
        await supabase.from("attachments").insert(
          attachments.map((a) => ({
            message_id: msg.id,
            file_url: a.file_url,
            file_type: a.file_type,
            file_size: a.file_size,
          })),
        );
      }

      const now = new Date().toISOString();
      await supabase
        .from("conversations")
        .update({ last_message_at: now })
        .eq("id", convId);

      return msg.id;
    }

    async function ingest(normalized: {
      channel: string;
      external_id: string;
      customer: { name?: string | null; email?: string | null; phone?: string | null };
      message: { content: string; type?: string; attachments?: unknown[] };
      subject?: string | null;
      priority?: string;
    }) {
      const channel = await getChannelByType(normalized.channel);
      if (!channel) throw new Error(`No active channel found for type: ${normalized.channel}`);

      const customer = await identifyOrCreateCustomer({
        name: normalized.customer.name,
        email: normalized.customer.email,
        phone: normalized.customer.phone,
        external_id: normalized.external_id,
        external_source: normalized.channel,
      });

      const existing = await findOpenTicket(customer.id, channel.id);
      let result: {
        ticket_id: string;
        customer_id: string;
        conversation_id: string;
        message_id: string;
        is_new_ticket: boolean;
        is_new_customer: boolean;
      };

      if (existing) {
        const convId = Array.isArray(existing.conversations)
          ? existing.conversations[0]?.id
          : (existing.conversations as { id: string } | null)?.id;

        if (!convId) throw new Error("Existing ticket has no conversation");

        const messageId = await addMessage(
          convId,
          customer.id,
          normalized.message.content,
          normalized.message.type ?? "text",
          (normalized.message.attachments ?? []) as {
            file_url: string;
            file_type: string;
            file_size: number;
          }[],
        );

        result = {
          ticket_id: existing.id,
          customer_id: customer.id,
          conversation_id: convId,
          message_id: messageId,
          is_new_ticket: false,
          is_new_customer: false,
        };
      } else {
        const created = await createTicket(
          customer.id,
          channel.id,
          normalized.subject ?? null,
          normalized.message.content,
          normalized.priority ?? "medium",
          normalized.channel,
        );

        result = {
          ticket_id: created.ticket.id,
          customer_id: customer.id,
          conversation_id: created.conv.id,
          message_id: created.messageId,
          is_new_ticket: true,
          is_new_customer: !existing,
        };
      }

      return result;
    }

    if (path === "/chat") {
      const { session_id, name, email, phone, message } = body as {
        session_id?: string;
        name?: string;
        email?: string;
        phone?: string;
        message?: string;
      };

      if (!session_id) return respond(err("session_id is required"));
      if (!message) return respond(err("message is required"));

      const result = await ingest({
        channel: "chat",
        external_id: session_id,
        customer: { name: name ?? null, email: email ?? null, phone: phone ?? null },
        message: { content: message, type: "text", attachments: [] },
      });

      return respond(json(result, 200));
    }

    if (path === "/email") {
      const { from_email, from_name, subject, body: emailBody, attachments } = body as {
        from_email?: string;
        from_name?: string;
        subject?: string;
        body?: string;
        attachments?: unknown[];
      };

      if (!from_email) return respond(err("from_email is required"));
      if (!emailBody) return respond(err("body is required"));

      const result = await ingest({
        channel: "email",
        external_id: from_email,
        customer: { name: from_name ?? null, email: from_email, phone: null },
        message: { content: emailBody, type: "text", attachments: attachments ?? [] },
        subject: subject ?? null,
      });

      return respond(json(result, 200));
    }

    if (path === "/api") {
      const { external_id, customer, message: msg, subject, priority } = body as {
        external_id?: string;
        customer?: { name?: string; email?: string; phone?: string; external_id?: string };
        message?: { content?: string; type?: string; attachments?: unknown[] };
        subject?: string;
        priority?: string;
      };

      if (!external_id) return respond(err("external_id is required"));
      if (!msg?.content) return respond(err("message.content is required"));

      const result = await ingest({
        channel: "api",
        external_id,
        customer: {
          name: customer?.name ?? null,
          email: customer?.email ?? null,
          phone: customer?.phone ?? null,
        },
        message: {
          content: msg.content,
          type: msg.type ?? "text",
          attachments: msg.attachments ?? [],
        },
        subject: subject ?? null,
        priority,
      });

      return respond(json(result, 200));
    }

    errorMessage = "Not found";
    return respond(err("Not found", 404));
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Internal server error";
    errorMessage = msg;
    responseStatus = 500;
    await logRequest();
    return json({ error: msg }, 500);
  }
});
