/**
 * Tier classification utility
 */

export type Tier = 'HOT' | 'WARM' | 'COOL' | 'COLD';

export interface TierInfo {
  tier: Tier;
  badge: string;
  color: string;
  bgColor: string;
  textColor: string;
  description: string;
  action: string;
}

const tierMap: Record<Tier, TierInfo> = {
  HOT: {
    tier: 'HOT',
    badge: '🔥 HOT',
    color: 'red',
    bgColor: 'bg-red-900',
    textColor: 'text-red-100',
    description: 'Hot Lead',
    action: 'Prioridade máxima — agendar contato esta semana',
  },
  WARM: {
    tier: 'WARM',
    badge: '🟡 WARM',
    color: 'yellow',
    bgColor: 'bg-yellow-900',
    textColor: 'text-yellow-100',
    description: 'Warm Lead',
    action: 'Bom potencial — nurturing ativo, follow-up quinzenal',
  },
  COOL: {
    tier: 'COOL',
    badge: '🔵 COOL',
    color: 'blue',
    bgColor: 'bg-blue-900',
    textColor: 'text-blue-100',
    description: 'Cool Lead',
    action: 'Potencial moderado — manter no radar, abordagem consultiva',
  },
  COLD: {
    tier: 'COLD',
    badge: '⚪ COLD',
    color: 'gray',
    bgColor: 'bg-slate-700',
    textColor: 'text-slate-100',
    description: 'Cold Lead',
    action: 'Baixa prioridade — revisar se vale manter no pipeline',
  },
};

/**
 * Assign tier based on numeric score (0-100)
 */
export function scoreToTier(score: number): Tier {
  if (score >= 80) return 'HOT';
  if (score >= 60) return 'WARM';
  if (score >= 40) return 'COOL';
  return 'COLD';
}

/**
 * Get tier information
 */
export function getTierInfo(tier: Tier): TierInfo {
  return tierMap[tier];
}

/**
 * Get all tiers info (for distribution charts)
 */
export function getAllTiersInfo(): TierInfo[] {
  return Object.values(tierMap);
}

/**
 * Get score range for a tier
 */
export function getTierScoreRange(tier: Tier): { min: number; max: number } {
  switch (tier) {
    case 'HOT':
      return { min: 80, max: 100 };
    case 'WARM':
      return { min: 60, max: 79 };
    case 'COOL':
      return { min: 40, max: 59 };
    case 'COLD':
      return { min: 0, max: 39 };
  }
}
