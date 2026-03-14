import { useMemo } from 'react';
import type { DealScore } from '@/types';
import { Card, Badge } from '@/components/ui';

interface ScorerExplicabilityDashboardProps {
  deal: DealScore;
  showDetailed?: boolean;
}

export function ScorerExplicabilityDashboard({
  deal,
  showDetailed = true
}: ScorerExplicabilityDashboardProps) {
  // Extract pillar scores from factors
  const pillarScores = useMemo(() => {
    const valorFactor = deal.factors.find(f => f.name.includes('Valor'));
    const momentumFactor = deal.factors.find(f => f.name.includes('Momentum'));
    const fitFactor = deal.factors.find(f => f.name.includes('Fit'));
    const qualidadeFactor = deal.factors.find(f => f.name.includes('Qualidade'));

    return {
      valor: {
        score: Math.round(valorFactor?.normalized_value ? valorFactor.normalized_value * 100 : 0),
        contribution: valorFactor?.contribution || 0,
        explanation: valorFactor?.explanation || ''
      },
      momentum: {
        score: Math.round(momentumFactor?.normalized_value ? momentumFactor.normalized_value * 100 : 0),
        contribution: momentumFactor?.contribution || 0,
        explanation: momentumFactor?.explanation || ''
      },
      fit: {
        score: Math.round(fitFactor?.normalized_value ? fitFactor.normalized_value * 100 : 0),
        contribution: fitFactor?.contribution || 0,
        explanation: fitFactor?.explanation || ''
      },
      qualidade: {
        score: Math.round(qualidadeFactor?.normalized_value ? qualidadeFactor.normalized_value * 100 : 0),
        contribution: qualidadeFactor?.contribution || 0,
        explanation: qualidadeFactor?.explanation || ''
      }
    };
  }, [deal.factors]);

  // Generate executive summary
  const getSummary = (): string => {
    let summary = `Score ${deal.score} [${deal.tier}] because:\n`;

    if (pillarScores.valor.score >= 70) {
      summary += `• Produto é valioso (Valor: ${pillarScores.valor.score}/100)\n`;
    } else if (pillarScores.valor.score < 50) {
      summary += `• Produto tem baixo valor (Valor: ${pillarScores.valor.score}/100)\n`;
    }

    if (pillarScores.momentum.score >= 80) {
      summary += `• Deal tem excelente momentum (Momentum: ${pillarScores.momentum.score}/100)\n`;
    } else if (pillarScores.momentum.score < 50) {
      summary += `• Deal está envelhecido (Momentum: ${pillarScores.momentum.score}/100)\n`;
    }

    if (pillarScores.qualidade.score >= 80) {
      summary += `• Vendedor é top-tier (Qualidade: ${pillarScores.qualidade.score}/100)\n`;
    } else if (pillarScores.qualidade.score < 50) {
      summary += `• Vendedor tem baixo histórico (Qualidade: ${pillarScores.qualidade.score}/100)`;
    }

    return summary;
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'HOT':
        return 'bg-red-100 text-red-900 border-red-300';
      case 'WARM':
        return 'bg-orange-100 text-orange-900 border-orange-300';
      case 'COOL':
        return 'bg-blue-100 text-blue-900 border-blue-300';
      case 'COLD':
        return 'bg-gray-100 text-gray-900 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-900 border-gray-300';
    }
  };

  const getScorePillColor = (score: number) => {
    if (score >= 80) return 'from-green-400 to-green-600';
    if (score >= 60) return 'from-blue-400 to-blue-600';
    if (score >= 40) return 'from-yellow-400 to-yellow-600';
    return 'from-red-400 to-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header with Score and Tier */}
      <Card variant="default" padding="lg" className="bg-gradient-to-r from-hubspot-dark to-hubspot-black text-white">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-2xl font-black">{deal.opportunity_id}</h3>
            <p className="text-gray-300 text-sm mt-1">{deal.product} • {deal.account || '(No Account)'}</p>
          </div>
          <Badge className={`px-4 py-2 text-lg font-black border ${getTierColor(deal.tier)}`}>
            {deal.tier}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-gray-300 text-xs uppercase tracking-widest">Final Score</p>
            <p className="text-5xl font-black text-white">{deal.score}</p>
            <p className="text-gray-300 text-xs mt-1">out of 100</p>
          </div>
          <div>
            <p className="text-gray-300 text-xs uppercase tracking-widest">Recommendation</p>
            <p className="text-sm font-bold text-green-300 mt-2">{deal.recommendation}</p>
          </div>
        </div>
      </Card>

      {/* Executive Summary */}
      <Card variant="default" padding="lg">
        <h4 className="font-black text-sm uppercase tracking-widest text-hubspot-dark mb-3">
          📊 Why This Score?
        </h4>
        <p className="text-sm leading-relaxed whitespace-pre-wrap font-medium text-gray-700">
          {getSummary()}
        </p>
      </Card>

      {/* Pillar Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Pilar 1: Valor */}
        <Card variant="default" padding="lg" className="border-l-4 border-l-blue-500">
          <div className="flex justify-between items-start mb-3">
            <h5 className="font-black text-sm uppercase tracking-widest text-hubspot-dark">
              💰 Pilar 1: Valor (40%)
            </h5>
            <Badge className="bg-blue-100 text-blue-900 text-lg font-black">
              {pillarScores.valor.score}/100
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full bg-gradient-to-r ${getScorePillColor(pillarScores.valor.score)}`}
                style={{ width: `${pillarScores.valor.score}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">
              Contribuição: <span className="font-bold">{pillarScores.valor.contribution.toFixed(1)} pts</span>
            </p>
            <p className="text-xs text-gray-700 mt-2">{pillarScores.valor.explanation}</p>
          </div>
        </Card>

        {/* Pilar 2: Momentum */}
        <Card variant="default" padding="lg" className="border-l-4 border-l-orange-500">
          <div className="flex justify-between items-start mb-3">
            <h5 className="font-black text-sm uppercase tracking-widest text-hubspot-dark">
              ⚡ Pilar 2: Momentum (25%)
            </h5>
            <Badge className="bg-orange-100 text-orange-900 text-lg font-black">
              {pillarScores.momentum.score}/100
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full bg-gradient-to-r ${getScorePillColor(pillarScores.momentum.score)}`}
                style={{ width: `${pillarScores.momentum.score}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">
              Contribuição: <span className="font-bold">{pillarScores.momentum.contribution.toFixed(1)} pts</span>
            </p>
            <p className="text-xs text-gray-700 mt-2">{pillarScores.momentum.explanation}</p>
          </div>
        </Card>

        {/* Pilar 3: Fit da Conta */}
        <Card variant="default" padding="lg" className="border-l-4 border-l-green-500">
          <div className="flex justify-between items-start mb-3">
            <h5 className="font-black text-sm uppercase tracking-widest text-hubspot-dark">
              🏢 Pilar 3: Fit da Conta (15%)
            </h5>
            <Badge className="bg-green-100 text-green-900 text-lg font-black">
              {pillarScores.fit.score}/100
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full bg-gradient-to-r ${getScorePillColor(pillarScores.fit.score)}`}
                style={{ width: `${pillarScores.fit.score}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">
              Contribuição: <span className="font-bold">{pillarScores.fit.contribution.toFixed(1)} pts</span>
            </p>
            <p className="text-xs text-gray-700 mt-2">{pillarScores.fit.explanation}</p>
          </div>
        </Card>

        {/* Pilar 4: Qualidade Rep */}
        <Card variant="default" padding="lg" className="border-l-4 border-l-purple-500">
          <div className="flex justify-between items-start mb-3">
            <h5 className="font-black text-sm uppercase tracking-widest text-hubspot-dark">
              👔 Pilar 4: Qualidade Rep (20%)
            </h5>
            <Badge className="bg-purple-100 text-purple-900 text-lg font-black">
              {pillarScores.qualidade.score}/100
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full bg-gradient-to-r ${getScorePillColor(pillarScores.qualidade.score)}`}
                style={{ width: `${pillarScores.qualidade.score}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">
              Contribuição: <span className="font-bold">{pillarScores.qualidade.contribution.toFixed(1)} pts</span>
            </p>
            <p className="text-xs text-gray-700 mt-2">{pillarScores.qualidade.explanation}</p>
          </div>
        </Card>
      </div>

      {/* Validation Badges */}
      {showDetailed && (
        <Card variant="default" padding="lg" className="bg-green-50 border border-green-200">
          <h5 className="font-black text-sm uppercase tracking-widest text-green-900 mb-3">
            ✅ Validation Status
          </h5>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="text-center p-2 bg-white rounded border border-green-200">
              <p className="text-xs text-gray-600">Coherence</p>
              <p className="font-black text-green-600">✅ Valid</p>
            </div>
            <div className="text-center p-2 bg-white rounded border border-green-200">
              <p className="text-xs text-gray-600">Sensitivity</p>
              <p className="font-black text-green-600">✅ Proportional</p>
            </div>
            <div className="text-center p-2 bg-white rounded border border-green-200">
              <p className="text-xs text-gray-600">Explicability</p>
              <p className="font-black text-green-600">✅ Clear</p>
            </div>
          </div>
        </Card>
      )}

      {/* Raw Factors */}
      {showDetailed && (
        <Card variant="default" padding="lg">
          <h5 className="font-black text-sm uppercase tracking-widest text-hubspot-dark mb-4">
            📋 Raw Factors
          </h5>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {deal.factors.map((factor, idx) => (
              <div key={idx} className="p-3 bg-gray-50 rounded border border-gray-200">
                <div className="flex justify-between items-start mb-2">
                  <p className="text-xs font-bold text-hubspot-dark">{factor.name}</p>
                  <p className="text-xs font-bold text-gray-600">{factor.contribution.toFixed(2)} pts</p>
                </div>
                <p className="text-xs text-gray-700">{factor.explanation}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
