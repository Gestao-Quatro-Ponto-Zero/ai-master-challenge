import { type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const progressBarVariants = cva(
  'w-full bg-slate-800 rounded-full overflow-hidden',
  {
    variants: {
      size: {
        xs: 'h-1',
        sm: 'h-2',
        md: 'h-3',
        lg: 'h-4',
      },
      color: {
        blue: 'bg-blue-900/20',
        green: 'bg-green-900/20',
        red: 'bg-red-900/20',
        yellow: 'bg-yellow-900/20',
      },
    },
    defaultVariants: {
      size: 'sm',
      color: 'blue',
    },
  }
);

const fillVariants = cva(
  'h-full rounded-full transition-all duration-300',
  {
    variants: {
      color: {
        blue: 'bg-blue-500',
        green: 'bg-green-500',
        red: 'bg-red-500',
        yellow: 'bg-yellow-500',
      },
    },
    defaultVariants: {
      color: 'blue',
    },
  }
);

export interface ProgressBarProps
  extends Omit<HTMLAttributes<HTMLDivElement>, 'color'>,
    VariantProps<typeof progressBarVariants> {
  value: number;
  max?: number;
  showLabel?: boolean;
}

export function ProgressBar({
  value,
  max = 100,
  size,
  color,
  showLabel,
  className,
  ...props
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);

  // Determine color based on percentage if not explicitly set
  let fillColor: 'blue' | 'green' | 'red' | 'yellow' = color || 'blue';
  if (!color) {
    if (percentage >= 80) fillColor = 'green';
    else if (percentage >= 50) fillColor = 'blue';
    else if (percentage >= 25) fillColor = 'yellow';
    else fillColor = 'red';
  }

  return (
    <div>
      <div
        className={progressBarVariants({ size, color, className })}
        {...props}
      >
        <div
          className={fillVariants({ color: fillColor })}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <p className="text-xs text-slate-400 mt-1">
          {value.toFixed(0)} / {max}
        </p>
      )}
    </div>
  );
}
