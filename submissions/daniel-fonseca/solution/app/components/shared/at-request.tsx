import { connection } from "next/server"

/**
 * Renderiza os filhos na requisição, nunca no build. As visões leem o Supabase, e o build da Vercel
 * não deve depender das variáveis do banco (antes das rotas reais, o searchParams já garantia isso).
 * As leituras continuam com "use cache" em tempo de execução.
 */
export async function AtRequest({ children }: { children: React.ReactNode }) {
  await connection()
  return <>{children}</>
}
