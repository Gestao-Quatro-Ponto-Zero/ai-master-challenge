'use client'

import Image from 'next/image'

interface LogoProps {
  size?: number
  variant?: 'light' | 'dark'
  showWordmark?: boolean
}

export default function Logo({
  size = 32,
  variant = 'light',
  showWordmark = true,
}: LogoProps) {
  const textColor = variant === 'light' ? '#ffffff' : '#001f35'

  return (
    <div className="flex items-center gap-2.5" aria-label="G4 Business logo">
      <Image
        src="/logo-g4.png"
        alt="G4 Business"
        width={size}
        height={size}
        className="object-contain"
        priority
      />
      {showWordmark && (
        <span
          className="font-sans font-bold tracking-tight select-none"
          style={{
            color: textColor,
            fontSize: `${Math.round(size * 0.56)}px`,
            lineHeight: 1,
            letterSpacing: '-0.01em',
          }}
        >
          G4 Business
        </span>
      )}
    </div>
  )
}
