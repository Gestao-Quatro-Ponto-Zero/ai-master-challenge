import { type ReactNode, type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { getTierInfo } from '@/utils/tiers';
import type { TierType } from '@/types';

const badgeVariants = cva(
  'inline-flex items-center justify-center px-4 py-1.5 rounded-full text-xs font-bold tracking-wide uppercase',
  {
    variants: {
      variant: {
        HOT: 'bg-hubspot-orange/10 border border-hubspot-orange/30 text-hubspot-orange',
        WARM: 'bg-yellow-500/10 border border-yellow-500/30 text-yellow-600',
        COOL: 'bg-blue-500/10 border border-blue-500/30 text-blue-600',
        COLD: 'bg-hubspot-gray-200/50 border border-hubspot-gray-200 text-hubspot-dark/60',
      },
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
  VariantProps<typeof badgeVariants> {
  children?: ReactNode;
  tier?: TierType;
}

export function Badge({
  variant,
  tier,
  className,
  children,
  ...props
}: BadgeProps) {
  // If tier is provided, get the emoji representation
  if (tier) {
    const tierInfo = getTierInfo(tier);
    return (
      <div
        className={badgeVariants({ variant: tier, className })}
        {...props}
      >
        {tierInfo.badge}
      </div>
    );
  }

  // Otherwise use variant (HOT, WARM, COOL, COLD)
  const variantType = (variant as TierType) || 'COLD';
  return (
    <div
      className={badgeVariants({ variant: variantType, className })}
      {...props}
    >
      {children}
    </div>
  );
}
