/** Corrige textos legados sem acentuação (mensagens salvas antes da correção). */
export function normalizePtBr(text: string): string {
  return text
    .replace(/\bOla\b/g, "Olá")
    .replace(/\bVoce\b/g, "Você")
    .replace(/\bvoce\b/g, "você")
    .replace(/\bja\b/g, "já")
    .replace(/\brecebera\b/g, "receberá")
    .replace(/\batualizacoes\b/g, "atualizações")
    .replace(/\bConfianca\b/g, "Confiança")
    .replace(/\bconfianca\b/g, "confiança")
    .replace(/\bnao\b/g, "não")
    .replace(/\bportugues\b/g, "português")
    .replace(/\bconfirmacao\b/g, "confirmação")
    .replace(/\bClassificacao\b/g, "Classificação")
    .replace(/\bRevisao\b/g, "Revisão");
}
