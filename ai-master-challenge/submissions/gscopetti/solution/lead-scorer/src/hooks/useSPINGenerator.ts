import { useMemo, useCallback, useState } from 'react';
import type {
  PipelineOpportunity,
  Account,
  Product,
  LeadReport,
} from '@/types';
import { buildSPINContext } from '@/utils/spin-context';
import {
  generateSPINScript,
  formatSPINScriptForDisplay,
  generateTalkingPoints,
} from '@/utils/spin-templates';

/**
 * Hook to generate SPIN Selling scripts for deals
 * Falls back to templates if API is unavailable
 */
export function useSPINGenerator(
  pipeline: PipelineOpportunity[],
  accounts: Account[],
  products: Product[]
) {
  const [claudeApiKey] = useState<string | null>(
    localStorage.getItem('ANTHROPIC_API_KEY') || null
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create lookup maps
  const accountMap = useMemo(() => {
    const map = new Map<string, Account>();
    for (const account of accounts) {
      if (account.account) {
        map.set(account.account, account);
      }
    }
    return map;
  }, [accounts]);

  const productMap = useMemo(() => {
    const map = new Map<string, Product>();
    for (const product of products) {
      map.set(product.product, product);
    }
    return map;
  }, [products]);

  /**
   * Generate script for a single deal
   */
  const generateForDeal = useCallback(
    async (dealScore: any): Promise<LeadReport | null> => {
      try {
        // Find the pipeline opportunity
        const deal = pipeline.find((d) => d.opportunity_id === dealScore.opportunity_id);
        if (!deal) return null;

        // Get account and product data
        const account = deal.account ? accountMap.get(deal.account) : undefined;
        const product = productMap.get(deal.product);

        // Build context
        const context = buildSPINContext(deal, pipeline, account, product, products);

        // Generate script (templates only, for now)
        // Note: API Claude integration would go here in future
        const script = generateSPINScript(context);

        const report: LeadReport = {
          account_score: undefined, // Only populated for account-level reports
          deal_score: dealScore,
          spin_script: script,
          context,
          generated_at: new Date(),
        };

        return report;
      } catch (err) {
        console.error('Error generating SPIN script:', err);
        return null;
      }
    },
    [pipeline, accountMap, productMap, products]
  );

  /**
   * Generate scripts for multiple deals (batch)
   */
  const generateBatch = useCallback(
    async (scores: any[]): Promise<LeadReport[]> => {
      setIsGenerating(true);
      setError(null);

      try {
        const reports: LeadReport[] = [];

        for (const score of scores) {
          const report = await generateForDeal(score);
          if (report) {
            reports.push(report);
          }
        }

        return reports;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(`Failed to generate SPIN scripts: ${errorMsg}`);
        return [];
      } finally {
        setIsGenerating(false);
      }
    },
    [generateForDeal]
  );

  /**
   * Try to use Claude API if key is available
   * Falls back to templates if not
   */
  const generateWithClaudeOption = useCallback(
    async (dealScore: any): Promise<LeadReport | null> => {
      const baseReport = await generateForDeal(dealScore);
      if (!baseReport) return null;

      // If Claude API key is available and user wants LLM enhancement
      if (claudeApiKey && (baseReport.context.wonDeals ?? 0) > 0) {
        // This would integrate with Claude API
        // For now, we use template-based approach
        // TODO: Implement Claude API call in future version
      }

      return baseReport;
    },
    [generateForDeal, claudeApiKey]
  );

  /**
   * Format report for display
   */
  const formatReport = useCallback((report: LeadReport): string => {
    const script = formatSPINScriptForDisplay(report.spin_script);
    const talkingPoints = generateTalkingPoints(report.context);

    let formatted = script + '\n\n---\n\n## 💡 TALKING POINTS\n\n';
    for (const point of talkingPoints) {
      formatted += `• ${point}\n`;
    }

    return formatted;
  }, []);

  /**
   * Export report as text (for copy-paste or download)
   */
  const exportReportAsText = useCallback((report: LeadReport): string => {
    const accountName = report.context.accountName;
    const productName = report.context.currentProduct;
    const dealStage = report.context.currentStage;

    let text = '';
    text += `RELATÓRIO DO LEAD: ${accountName}\n`;
    text += `Score: ${report.deal_score.score}/100 (${report.deal_score.tier})\n`;
    text += `Produto: ${productName} • Estágio: ${dealStage}\n`;
    text += `Gerado em: ${report.generated_at.toLocaleString()}\n`;
    text += '\n---\n\n';

    // Context summary
    text += 'CONTEXTO RÁPIDO:\n';
    text += `• Setor: ${report.context.sector || 'Unknown'}\n`;
    text += `• Tamanho: ${report.context.employees || 0} funcionários\n`;
    text += `• Win Rate: ${((report.context.winRate ?? 0) * 100).toFixed(0)}%\n`;
    text += `• Ticket Médio: $${(report.context.avgTicket ?? 0).toFixed(0)}\n`;
    text += `• Deals Ativos: ${report.context.activeDeals || 0}\n`;
    text += '\n---\n\n';

    // Script
    text += formatReport(report);

    return text;
  }, [formatReport]);

  return {
    generateForDeal,
    generateBatch,
    generateWithClaudeOption,
    formatReport,
    exportReportAsText,
    isGenerating,
    error,
    hasClaudeKey: !!claudeApiKey,
  };
}

/**
 * Hook to generate SPIN scripts for all qualifying deals
 * Only for deals with score >= 40 (Cool tier or better)
 */
export function useSPINReports(
  dealScores: any[],
  pipeline: PipelineOpportunity[],
  accounts: Account[],
  products: Product[]
): { reports: LeadReport[]; isLoading: boolean } {
  const generator = useSPINGenerator(pipeline, accounts, products);

  const reports = useMemo(() => {
    // Only generate for qualifying deals (score >= 40)
    const qualifyingScores = dealScores.filter((score) => score.score >= 40);

    // Generate synchronously using template approach
    return qualifyingScores
      .map((score) => {
        const deal = pipeline.find((d) => d.opportunity_id === score.opportunity_id);
        if (!deal) return null;

        const accountMap = new Map<string, Account>();
        for (const account of accounts) {
          if (account.account) {
            accountMap.set(account.account, account);
          }
        }

        const productMap = new Map<string, Product>();
        for (const product of products) {
          productMap.set(product.product, product);
        }

        const account = deal.account ? accountMap.get(deal.account) : undefined;
        const product = productMap.get(deal.product);

        const context = buildSPINContext(deal, pipeline, account, product, products);
        const script = generateSPINScript(context);

        const report: LeadReport = {
          deal_score: score,
          spin_script: script,
          context,
          generated_at: new Date(),
        };

        return report;
      })
      .filter((r): r is LeadReport => r !== null);
  }, [dealScores, pipeline, accounts, products]);

  return {
    reports,
    isLoading: generator.isGenerating,
  };
}
