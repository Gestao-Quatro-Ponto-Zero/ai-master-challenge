import React from 'react'
import { clsx } from 'clsx'

interface CardProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
  hoverable?: boolean
  killerPulse?: boolean
}

export default function Card({
  children,
  className,
  onClick,
  hoverable = false,
  killerPulse = false,
}: CardProps) {
  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
      className={clsx(
        'bg-surface border rounded-lg shadow-md',
        'border-[rgba(0,31,53,0.15)]',
        hoverable && 'cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-accent hover:border-2',
        killerPulse && 'killer-deal',
        onClick && !hoverable && 'cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  )
}
