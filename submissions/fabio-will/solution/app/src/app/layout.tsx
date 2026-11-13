import type { Metadata, Viewport } from 'next'
import { Libre_Baskerville, Manrope } from 'next/font/google'
import { SiteHeader } from '@/components/SiteHeader'
import './globals.css'

// Fonts are downloaded at build time and served from this origin: no third-party request at runtime.
// Manrope is a variable font: one file covers weights 200 to 800.
const manrope = Manrope({ subsets: ['latin'], variable: '--font-manrope', display: 'swap' })
const libre = Libre_Baskerville({ subsets: ['latin'], weight: '400', style: 'italic', variable: '--font-libre', display: 'swap' })

export const metadata: Metadata = {
  title: { default: 'Mesa de Suporte', template: '%s · Mesa de Suporte' },
  description: 'Protótipo de triagem de tickets com IA e revisão humana. Case do AI Master Challenge do G4, desafio 002.',
  robots: { index: false, follow: false },
}

export const viewport: Viewport = {
  themeColor: '#001f35',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${manrope.variable} ${libre.variable}`}>
      <body>
        <a className="skip" href="#conteudo">
          Pular para o conteúdo
        </a>
        <SiteHeader />
        <main id="conteudo">{children}</main>
        <footer className="site-footer">
          <div className="wrap">
            <span>Protótipo de Fábio Will para o AI Master Challenge do G4. Não é um produto oficial do G4.</span>
            <span>Dados: Kaggle, licença CC0. Nada do que você digita sai do navegador.</span>
          </div>
        </footer>
      </body>
    </html>
  )
}
