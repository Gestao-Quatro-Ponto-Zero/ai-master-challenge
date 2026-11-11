import type { Metadata } from "next"
import { IBM_Plex_Mono, Libre_Baskerville, Manrope } from "next/font/google"

import { SiteFooter } from "@/components/shell/site-footer"
import { ThemeProvider } from "@/components/shell/theme-provider"
import { TopBar } from "@/components/shell/top-bar"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"

import "./globals.css"

const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope", display: "swap" })
const baskerville = Libre_Baskerville({ subsets: ["latin"], weight: ["400", "700"], variable: "--font-baskerville", display: "swap" })
const plexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono", display: "swap" })

export const metadata: Metadata = {
  title: { default: "Triagem Inteligente — Case AI Master", template: "%s · Triagem Inteligente" },
  description:
    "Diagnóstico da operação de suporte, triagem de tickets com RAG em 3 caminhos (resposta automática, revisão humana, somente humano) e estimativa de economia.",
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" suppressHydrationWarning className={`${manrope.variable} ${baskerville.variable} ${plexMono.variable} h-full`}>
      <body className="flex min-h-full flex-col">
        <ThemeProvider>
          <TooltipProvider>
            <TopBar />
            <main className="pb-mobile-nav mx-auto w-full max-w-7xl flex-1 px-4 pt-8 sm:px-6 sm:pt-10">{children}</main>
            <SiteFooter />
            <Toaster position="top-center" />
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
