import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Triagem Inteligente de Suporte',
    short_name: 'Triagem AI',
    description: 'Protótipo de triagem inteligente de chamados de suporte com ML — G4 AI Master Challenge',
    start_url: '/',
    display: 'standalone',
    background_color: '#f5f7fa',
    theme_color: '#1e3a5f',
    icons: [
      { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
    ],
  }
}
