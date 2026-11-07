import fs from "node:fs/promises";
import { createClient } from "@supabase/supabase-js";
if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY)
  throw Error("Preencha .env.local antes de importar.");
const db = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY,
  { auth: { persistSession: false } },
);
const { opportunities } = JSON.parse(
  await fs.readFile("data/prepared.json", "utf8"),
);
for (let i = 0; i < opportunities.length; i += 200) {
  const { error } = await db.from("lead_opportunities").upsert(
    opportunities.slice(i, i + 200).map((payload) => ({
      opportunity_id: payload.opportunity_id,
      payload,
    })),
  );
  if (error) throw error;
}
console.log(`Importadas ${opportunities.length} oportunidades públicas.`);
