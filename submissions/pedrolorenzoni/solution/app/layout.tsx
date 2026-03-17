import type { Metadata } from 'next'
import { Manrope, Inter, Libre_Baskerville } from 'next/font/google'
import { AuthProvider } from '../context/AuthContext'
import './globals.css'

const manrope = Manrope({
  subsets: ['latin'],
  weight: ['200', '300', '400', '500', '600', '700', '800'],
  variable: '--font-manrope',
  display: 'swap',
})

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '600'],
  variable: '--font-inter',
  display: 'swap',
})

const libreBaskerville = Libre_Baskerville({
  subsets: ['latin'],
  weight: ['400'],
  style: ['italic'],
  variable: '--font-baskerville',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'G4 Business — CRM Sales Analytics',
  description: 'Dashboard de análise de pipeline de vendas e métricas de CRM para G4 Business',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="pt-BR"
      className={`${manrope.variable} ${inter.variable} ${libreBaskerville.variable}`}
    >
      <body className="font-sans bg-bg text-text-main antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
