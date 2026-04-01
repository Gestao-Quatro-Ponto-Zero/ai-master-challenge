import { Card } from '@/components/ui';
import type { ScoreFactor } from '@/types';

export interface ScoreBreakdownProps {
  factors: ScoreFactor[];
  totalScore?: number;
}

export function ScoreBreakdown({
  factors,
  totalScore,
}: ScoreBreakdownProps) {
  const total = totalScore || factors.reduce((sum, f) => sum + f.contribution, 0);

  return (
    <div className="space-y-4">
      {factors.map((factor, idx) => (
        <Card key={idx} variant="default" padding="md" className="bg-white border-hubspot-gray-200">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <p className="font-bold text-hubspot-black">{factor.name}</p>
              <p className="text-xs font-medium text-hubspot-dark/50 mt-1">
                {factor.explanation}
              </p>
            </div>
            <div className="text-right ml-4">
              <p className="font-bold text-lg text-hubspot-orange">
                +{factor.contribution.toFixed(1)}
              </p>
              <p className="text-[10px] font-bold text-hubspot-dark/40 uppercase tracking-tighter">Peso: {factor.weight}%</p>
            </div>
          </div>

          {/* Visual Progress Bar */}
          <div className="h-1.5 w-full bg-hubspot-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-hubspot-orange transition-all duration-1000"
              style={{ width: `${(factor.normalized_value ?? 0) * 100}%` }}
            />
          </div>

          {/* Raw value display */}
          <div className="flex justify-between mt-2 text-[10px] font-bold text-hubspot-dark/40 uppercase tracking-widest">
            <span>{factor.raw_value}</span>
            <span>{((factor.normalized_value ?? 0) * 100).toFixed(0)}% de potencial</span>
          </div>
        </Card>
      ))}

      {/* Total Score Summary */}
      <Card variant="default" padding="lg" className="bg-hubspot-peach/20 border-hubspot-orange/30 border-2">
        <div className="flex justify-between items-center">
          <span className="font-bold text-hubspot-dark uppercase tracking-widest text-sm">Score Final Acumulado</span>
          <span className="text-4xl font-bold text-hubspot-orange tracking-tighter">
            {total.toFixed(0)} <span className="text-sm text-hubspot-dark/40">/ 100</span>
          </span>
        </div>
      </Card>
    </div>
  );
}
