import { Card, Badge, Button } from '@/components/ui';
import type { DealScore } from '@/types';

export interface LeadCardProps {
  deal: DealScore;
  onView?: (deal: DealScore) => void;
}

export function LeadCard({
  deal,
  onView,
}: LeadCardProps) {
  return (
    <Card
      variant="interactive"
      padding="lg"
      className="flex flex-col h-full bg-white border-2 border-hubspot-gray-200 hover:border-hubspot-orange transition-all group shadow-sm hover:shadow-2xl"
      onClick={() => onView?.(deal)}
    >
      {/* Header: Company + Score + Badge */}
      <div className="flex justify-between items-start mb-8">
        <div className="flex-1">
          <h3 className="text-2xl font-black text-hubspot-black truncate leading-none mb-2 tracking-tighter group-hover:text-hubspot-orange transition-colors">
            {deal.account || 'Prospect'}
          </h3>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-black text-hubspot-black/40 uppercase tracking-[0.2em]">
              {deal.product}
            </span>
            <Badge tier={deal.tier} />
          </div>
        </div>
      </div>

      {/* Score Display */}
      <div className="mb-8 p-6 bg-hubspot-gray-100/50 rounded-hb border-2 border-hubspot-gray-200/50 group-hover:bg-white transition-colors">
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-6xl font-black text-hubspot-black tracking-tighter">
            {deal.score}
          </span>
          <span className="text-sm font-black text-hubspot-black/30 uppercase tracking-widest">Score</span>
        </div>
        <p className="text-sm font-bold text-hubspot-black/70 mt-4 leading-relaxed line-clamp-2 italic">
          "{deal.recommendation}"
        </p>
      </div>

      {/* Action Buttons */}
      <div className="mt-auto flex flex-col gap-4">
        <Button
          variant="primary"
          size="md"
          fullWidth
          className="font-black uppercase tracking-[0.2em] text-[10px] py-6 shadow-lg shadow-hubspot-orange/20"
          onClick={(e) => {
            e.stopPropagation();
            onView?.(deal);
          }}
        >
          Analisar Oportunidade →
        </Button>
      </div>
    </Card>
  );
}
