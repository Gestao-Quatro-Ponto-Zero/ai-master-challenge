import React from 'react'
import { clsx } from 'clsx'

type BadgeVariant = 'primary' | 'gold' | 'dark' | 'success' | 'muted' | 'navy' | 'green' | 'gray'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}

const variantStyles: Record<BadgeVariant, string> = {
  primary: 'bg-[rgba(175,67,50,0.12)] text-primary',
  gold: 'bg-[rgba(185,145,91,0.15)] text-accent',
  dark: 'bg-[rgba(15,26,69,0.08)] text-secondary',
  navy: 'bg-secondary text-white',
  success: 'bg-[rgba(37,211,102,0.12)] text-success',
  green: 'bg-[rgba(37,211,102,0.15)] text-[#1a9e53]',
  gray: 'bg-[rgba(96,112,138,0.12)] text-text-muted',
  muted: 'bg-[rgba(96,112,138,0.10)] text-text-muted',
}

export default function Badge({ variant = 'primary', children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}
