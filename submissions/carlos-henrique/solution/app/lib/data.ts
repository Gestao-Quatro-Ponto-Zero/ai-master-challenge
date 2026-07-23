import "server-only";
import { promises as fs } from "node:fs";
import path from "node:path";
import { z } from "zod";
const payloadSchema = z.record(z.unknown());
export async function loadData<T>(name: string): Promise<T> {
  if (!/^[a-z0-9_-]+\.json$/.test(name)) throw new Error("Arquivo de dados do dashboard não permitido");
  const filePath = path.join(process.cwd(), "public", "data", name);
  try { const source = await fs.readFile(filePath, "utf8"); return payloadSchema.parse(JSON.parse(source)) as T; }
  catch (error) { const message = error instanceof Error ? error.message : "Erro desconhecido nos dados locais"; throw new Error(`Seção indisponível: ${name}. ${message}`); }
}
