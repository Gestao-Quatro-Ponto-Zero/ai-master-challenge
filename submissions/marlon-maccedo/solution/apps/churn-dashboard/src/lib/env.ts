/**
 * Segredos e variáveis injetadas em runtime (Railway, Docker).
 * Usar `process.env['NOME']` (notação em colchetes) evita que o bundler do Next.js
 * substitua o valor no `next build` quando a variável não existe no estágio de build.
 */
export function getOpenRouterApiKey(): string | undefined {
  const v = process.env['OPENROUTER_API_KEY']
  if (v === undefined || v === '') return undefined
  return v
}
