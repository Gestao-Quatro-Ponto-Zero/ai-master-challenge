"use client"

import { ThemeProvider as NextThemes } from "next-themes"

/** Tema claro (paper) por padrão; escuro como opção (PRD §6). */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemes attribute="class" defaultTheme="light" enableSystem={false} disableTransitionOnChange>
      {children}
    </NextThemes>
  )
}
