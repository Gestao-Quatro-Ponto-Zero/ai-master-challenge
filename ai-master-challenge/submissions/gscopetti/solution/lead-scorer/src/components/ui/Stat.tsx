import { type ReactNode, type HTMLAttributes } from 'react';

export interface StatProps extends HTMLAttributes<HTMLDivElement> {
  label: string;
  value: ReactNode;
  subtitle?: ReactNode;
  icon?: ReactNode;
  highlight?: boolean;
}

export function Stat({
  label,
  value,
  subtitle,
  icon,
  highlight,
  className,
  ...props
}: StatProps) {
  return (
    <div
      className={`p-5 rounded-hb transition-all duration-200 ${highlight
          ? 'bg-hubspot-peach/30 border-2 border-hubspot-orange/20 shadow-sm'
          : 'bg-white border border-hubspot-gray-200'
        } ${className}`}
      {...props}
    >
      <div className="flex items-center gap-3 mb-1">
        {icon && <div className="text-xl text-hubspot-orange">{icon}</div>}
        <p className="text-xs font-bold text-hubspot-dark uppercase tracking-wider opacity-60 font-sans">{label}</p>
      </div>
      <p className="text-3xl font-bold text-hubspot-black tracking-tight">{value}</p>
      {subtitle && <p className="text-xs text-hubspot-dark/50 mt-2 font-medium">{subtitle}</p>}
    </div>
  );
}
