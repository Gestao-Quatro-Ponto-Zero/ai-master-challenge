import type { SPINContext, SPINScript } from '@/types';
import { formatContextForDisplay, getContextInsights } from '@/utils/spin-context';

/**
 * Generate SPIN Selling script from context
 * Returns complete 4-section script
 */
export function generateSPINScript(context: SPINContext): SPINScript {
  const formatted = formatContextForDisplay(context);

  return {
    situation: generateSituation(context, formatted),
    problem: generateProblem(context, formatted),
    implication: generateImplication(context, formatted),
    need_payoff: generateNeedPayoff(context, formatted),
  };
}

/**
 * === SITUAÇÃO (S) ===
 * Establish understanding of account context
 */
function generateSituation(context: SPINContext, formatted: Record<string, string>): string {
  // Variant 1: Account with history
  if ((context.totalDeals ?? 0) > 0 && (context.wonDeals ?? 0) > 0) {
    const productContext =
      context.topProduct && context.topProduct !== 'our solutions'
        ? `Vocês já conhecem bem nosso ${context.topProduct} — como tem sido a experiência?`
        : 'Vocês já utilizam soluções similares — como tem sido a experiência?';

    return `Como empresa do setor de ${formatted.sector} com ${formatted.employees} funcionários em ${formatted.location}, vocês provavelmente lidam com desafios de escala e integração. ${productContext}`;
  }

  // Variant 2: Account with known product
  if (context.currentProduct) {
    const prodName = context.currentProduct.includes('GTK')
      ? 'plataforma GTK'
      : context.currentProduct.includes('MG')
        ? 'solução MG'
        : context.currentProduct.includes('GTX')
          ? 'suite GTX'
          : context.currentProduct;

    return `Como empresa do setor de ${formatted.sector} com ${formatted.employees} funcionários, imagino que vocês estejam avaliando a ${prodName}. Normalmente, empresas do seu porte buscam [benefício-chave dessa solução]. É esse o cenário de vocês?`;
  }

  // Variant 3: Generic prospect
  return `Como empresa do setor de ${formatted.sector} com ${formatted.employees} funcionários, vocês provavelmente lidam com [desafio típico do setor]. Como é atualmente a situação de vocês com isso?`;
}

/**
 * === PROBLEMA (P) ===
 * Identify difficulties, problems, dissatisfaction
 */
function generateProblem(context: SPINContext, formatted: Record<string, string>): string {
  // Variant 1: Has lost deals
  if ((context.failedProducts?.length ?? 0) > 0) {
    const productNames = context.failedProducts?.slice(0, 2).join(' e ') || 'alguns produtos';
    return `Vi que em oportunidades anteriores com ${productNames}, os deals não avançaram. Que desafios vocês enfrentaram naquela época? Houve questões técnicas, de orçamento, ou de timing?`;
  }

  // Variant 2: Low win rate
  if ((context.winRate ?? 0) < 0.5 && (context.totalDeals ?? 0) >= 3) {
    return `Notei que em alguns deals anteriores, não conseguimos chegar a um acordo. Qual foi o principal motivo? Seria interessante entender o que impediu para que a gente não cometa o mesmo erro dessa vez.`;
  }

  // Variant 3: Has active deals but stalled
  if ((context.daysInPipeline ?? 0) > 90) {
    return `Vi que este deal está há ${formatted.daysInPipeline} dias em pipeline. O que tem impedido de avançar? Existem pontos de dúvida sobre a solução ou é mais questão de priorização?`;
  }

  // Variant 4: Generic problem
  return `Outras contas do setor de ${formatted.sector} costumam enfrentar [desafio típico: integração, custo operacional, capacitação]. Isso também é uma preocupação para vocês?`;
}

/**
 * === IMPLICAÇÃO (I) ===
 * Explore consequences and implications
 */
function generateImplication(context: SPINContext, formatted: Record<string, string>): string {
  // Variant 1: High ticket value
  if ((context.avgTicket ?? 0) > 5000) {
    const impactValue = Math.round((context.avgTicket ?? 0) * 0.2); // Estimate 20% impact
    return `Considerando que vocês têm investimentos na faixa de ${formatted.avgTicket} em soluções similares, cada decisão tem impacto relevante. Se a solução atual não está entregando, o custo de manter as coisas como estão por mais 6 meses pode significar $${impactValue.toLocaleString()} em oportunidades perdidas ou ineficiência operacional.`;
  }

  // Variant 2: Low win rate with revenue lost
  if ((context.winRate ?? 0) < 0.5 && (context.lostRevenue ?? 0) > 0) {
    return `Vocês já perderam ${formatted.lostRevenue} em deals que não fecharam. Com um padrão assim, continuar com a abordagem atual pode significar mais perdas. Qual seria o impacto disso nos próximos trimestres?`;
  }

  // Variant 3: Scale with employees
  if ((context.employees ?? 0) > 1000) {
    return `Com ${formatted.employees} funcionários utilizando [solução], a escala amplifica bastante qualquer ineficiência. Se a ferramenta atual não está acompanhando o crescimento, quanto tempo e dinheiro vocês estão deixando na mesa?`;
  }

  // Variant 4: Generic implication with cycle time
  if ((context.avgCycleTime ?? 0) > 0) {
    const cycleMonths = Math.round((context.avgCycleTime ?? 0) / 30);
    return `Com um ciclo de venda de ${cycleMonths} meses para fechar deals, qualquer atraso impacta diretamente a receita. Se conseguíssemos reduzir esse ciclo em 20%, qual seria o efeito na sua meta anual?`;
  }

  // Variant 5: Generic
  return `O investimento em uma solução inadequada não é apenas sobre o custo inicial — é sobre a produtividade, compliance e oportunidades perdidas ao longo do tempo. Vocês já quantificaram esse impacto?`;
}

/**
 * === NECESSIDADE-PAYOFF (N) ===
 * Build value around solving the problem
 */
function generateNeedPayoff(context: SPINContext, formatted: Record<string, string>): string {
  // Variant 1: With cross-sell opportunity
  if ((context.missingProducts?.length ?? 0) > 0) {
    const newSeries = context.missingProducts?.[0] || 'nova série';
    return `Vocês já tiveram sucesso com ${context.topProduct || 'nossos produtos'}. Se estendêssemos isso para a série ${newSeries}, qual seria o impacto? Clientes similares do setor de ${formatted.sector} viram [resultado específico: tempo reduzido, custo diminuído] dentro de 4 meses com essa abordagem.`;
  }

  // Variant 2: With win rate context
  if ((context.winRate ?? 0) >= 0.7 && (context.totalDeals ?? 0) > 0) {
    return `Considerando que vocês têm um histórico de sucesso com nossos produtos (${formatted.winRate} de fechamento), faz sentido explorarmos como esta solução pode complementar a estratégia atual. Se conseguíssemos manter esse mesmo nível de satisfação, como mudaria a priorização para vocês neste trimestre?`;
  }

  // Variant 3: With lost revenue recovery
  if ((context.lostRevenue ?? 0) > 0) {
    const recoveryTarget = Math.round((context.lostRevenue ?? 0) * 0.5); // 50% recovery goal
    return `Se conseguíssemos recuperar até ${formatted.lostRevenue} em oportunidades que ficaram para trás — ou evitar perder mais — qual seria o valor disso para o negócio? Clientes com perfil similar já recuperaram até $${recoveryTarget.toLocaleString()} em receita com essa mudança.`;
  }

  // Variant 4: Generic need-payoff
  return `Se conseguíssemos resolver [problema identificado], qual seria o impacto mais importante para vocês: redução de custos, aumento de velocidade, ou melhoria na qualidade? E como isso afetaria os objetivos do seu time?`;
}

/**
 * Format complete SPIN script with markdown formatting
 */
export function formatSPINScriptForDisplay(script: SPINScript): string {
  return `
## 📋 SCRIPT SPIN SELLING

### [S] SITUAÇÃO
${script.situation}

### [P] PROBLEMA
${script.problem}

### [I] IMPLICAÇÃO
${script.implication}

### [N] NECESSIDADE-PAYOFF
${script.need_payoff}
`.trim();
}

/**
 * Generate brief summary of SPIN script for preview
 */
export function generateSPINSummary(context: SPINContext): string {
  const insights = getContextInsights(context);

  if (insights.length === 0) {
    return 'Lead com potencial de desenvolvimento.';
  }

  return insights.slice(0, 2).join(' • ');
}

/**
 * Generate talking points from context
 */
export function generateTalkingPoints(context: SPINContext): string[] {
  const points: string[] = [];

  // Win rate talking point
  if ((context.winRate ?? 0) > 0.6) {
    points.push(`Histórico de sucesso: ${((context.winRate ?? 0) * 100).toFixed(0)}% das propostas fecham com êxito`);
  }

  // Top product talking point
  if (context.topProduct) {
    points.push(
      `Solução favorita: ${context.topProduct} foi o produto com melhor performance nas vendas anteriores`
    );
  }

  // Ticket size talking point
  if ((context.avgTicket ?? 0) > 0) {
    points.push(`Escala de investimento: média de $${(context.avgTicket ?? 0).toFixed(0)} por oportunidade fechada`);
  }

  // Cross-sell opportunity
  if ((context.missingProducts?.length ?? 0) > 0) {
    points.push(
      `Oportunidade: ${context.missingProducts?.slice(0, 2).join(', ')} não foram explorados — potencial de expansão`
    );
  }

  // Cycle time talking point
  if ((context.avgCycleTime ?? 0) > 30 && (context.avgCycleTime ?? 0) < 180) {
    points.push(`Ciclo típico: ${Math.round(context.avgCycleTime ?? 0)} dias do primeiro contato ao fechamento`);
  }

  // Active deals talking point
  if ((context.activeDeals ?? 0) > 1) {
    points.push(`Pipeline ativo: ${context.activeDeals} oportunidades em andamento — relacionamento forte`);
  }

  return points.slice(0, 5); // Top 5 talking points
}
