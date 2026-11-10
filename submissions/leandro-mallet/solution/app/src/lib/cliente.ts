// Chamada às rotas do app a partir do navegador. Nunca lança: devolve a frase de erro pronta para a tela.
export interface Resposta<T> {
  ok: boolean;
  status: number;
  dados?: T;
  erro?: string;
  codigo?: string;
}

export async function pedir<T = Record<string, unknown>>(
  url: string,
  metodo: "GET" | "POST" | "PATCH" | "DELETE" = "GET",
  corpo?: unknown,
): Promise<Resposta<T>> {
  try {
    const r = await fetch(url, {
      method: metodo,
      headers: corpo === undefined ? undefined : { "content-type": "application/json" },
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
      cache: "no-store",
    });
    const json = (await r.json().catch(() => ({}))) as { erro?: string; codigo?: string } & T;
    if (!r.ok) return { ok: false, status: r.status, erro: json.erro ?? "Não foi possível concluir. Tente de novo.", codigo: json.codigo };
    return { ok: true, status: r.status, dados: json };
  } catch {
    return { ok: false, status: 0, erro: "Sem conexão com o servidor. Confira a internet e tente de novo." };
  }
}
