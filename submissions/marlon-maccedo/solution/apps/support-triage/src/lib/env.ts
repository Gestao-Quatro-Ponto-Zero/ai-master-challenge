/** Runtime env (Railway). Colchetes evitam inlining no `next build`. */
export function getOpenRouterApiKey(): string | undefined {
  const v = process.env['OPENROUTER_API_KEY']
  if (v === undefined || v === '') return undefined
  return v
}
