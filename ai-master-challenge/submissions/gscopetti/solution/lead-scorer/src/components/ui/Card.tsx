import { type ReactNode, type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const cardVariants = cva(
  'rounded-xl border transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'bg-white border-hubspot-gray-200',
        elevated: 'bg-white border-hubspot-gray-200 shadow-md',
        interactive: 'bg-white border-hubspot-gray-200 hover:border-hubspot-orange hover:shadow-lg cursor-pointer',
      },
      padding: {
        none: 'p-0',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'md',
    },
  }
);

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
  VariantProps<typeof cardVariants> {
  children: ReactNode;
}

export function Card({
  variant,
  padding,
  className,
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cardVariants({ variant, padding, className })}
      {...props}
    >
      {children}
    </div>
  );
}
