import fs from "node:fs/promises";
export async function loadData() {
  const local = JSON.parse(
    await fs.readFile(process.cwd() + "/data/prepared.json", "utf8"),
  );
  if (process.env.DATA_SOURCE !== "supabase") return local;
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY)
    throw Error("Configure as credenciais do Supabase no servidor.");
  const { createClient } = await import("@supabase/supabase-js");
  const db = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY,
    { auth: { persistSession: false, autoRefreshToken: false } },
  );
  const rows = [];
  for (let offset = 0; ; offset += 500) {
    const { data, error } = await db
      .from("lead_opportunities")
      .select("opportunity_id,payload")
      .order("opportunity_id")
      .range(offset, offset + 499);
    if (error) throw Error("Não foi possível consultar o Supabase.");
    rows.push(...data.map((r) => r.payload));
    if (data.length < 500) break;
  }
  if (rows.length !== local.summary.open)
    throw Error(
      "Importação incompleta: execute db:import para carregar o snapshot.",
    );
  return { ...local, source: "supabase", opportunities: rows };
}
