import { type ReactNode, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-hb font-semibold transition-all duration-200 text-sm active:scale-[0.98]',
  {
    variants: {
      variant: {
        primary: 'bg-hubspot-orange hover:bg-[#E54D2A] text-white shadow-sm',
        secondary: 'bg-white border-2 border-hubspot-orange text-hubspot-orange hover:bg-hubspot-peach/20',
        ghost: 'bg-transparent hover:bg-hubspot-gray-100 text-hubspot-dark',
        link: 'bg-transparent hover:text-hubspot-orange text-hubspot-orange hover:underline underline-offset-4 px-0',
        danger: 'bg-red-600 hover:bg-red-700 text-white',
        success: 'bg-green-600 hover:bg-green-700 text-white',
      },
      size: {
        xs: 'px-2 py-1 text-xs',
        sm: 'px-4 py-1.5 text-sm',
        md: 'px-8 py-4 text-base',
        lg: 'px-10 py-5 text-lg',
      },
      fullWidth: {
        true: 'w-full',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
  VariantProps<typeof buttonVariants> {
  children: ReactNode;
  isLoading?: boolean;
}

export function Button({
  variant,
  size,
  fullWidth,
  isLoading,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className={buttonVariants({ variant, size, fullWidth, className })}
      {...props}
    >
      {isLoading ? '⏳ Carregando...' : children}
    </button>
  );
}
