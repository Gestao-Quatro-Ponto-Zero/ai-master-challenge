import "server-only"

import { createClient, type SupabaseClient } from "@supabase/supabase-js"

import { env } from "@/lib/env"

let client: SupabaseClient | null = null

/**
 * Cliente Supabase do servidor, com a service role (ignora o RLS, que está fechado para anon).
 * Uso exclusivo em Server Components, Server Functions e Route Handlers (PRD §7).
 */
export function supabaseServer(): SupabaseClient {
  if (!client) {
    client = createClient(env.supabaseUrl(), env.supabaseServiceRoleKey(), {
      auth: { persistSession: false, autoRefreshToken: false },
      global: { headers: { "x-application-name": "triagem-case-ai-master" } },
    })
  }
  return client
}
