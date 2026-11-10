/** Chamadas do navegador às rotas /api/* do Console. Erros viram ApiFailure com a mensagem da rota. */
export class ApiFailure extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

async function handle<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const fallback = res.status === 429 ? "Limite de uso atingido. Tente novamente mais tarde." : "Algo falhou. Tente novamente."
    throw new ApiFailure((data as { error?: string }).error ?? fallback, res.status)
  }
  return data as T
}

export async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
  return handle<T>(res)
}

export async function getJson<T>(url: string): Promise<T> {
  return handle<T>(await fetch(url, { cache: "no-store" }))
}

export function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Algo falhou. Tente novamente."
}
