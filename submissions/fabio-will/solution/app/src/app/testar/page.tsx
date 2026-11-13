import type { Metadata } from 'next'
import { TicketTester } from '@/components/TicketTester'

export const metadata: Metadata = { title: 'Testar ticket' }

export default function TestPage() {
  return (
    <>
      <section className="hero">
        <div className="wrap">
          <p className="eyebrow">Teste ao vivo</p>
          <h1>
            Cole um ticket. Veja a <span className="accent">decisão</span> e o porquê.
          </h1>
          <p className="lede">
            É o mesmo roteador da fila, treinado em 33 mil tickets reais de TI e testado em 7 mil que ele nunca viu. Experimente os casos difíceis:
            português, erro de digitação e pedido de direito de administrador.
          </p>
        </div>
      </section>
      <section className="section">
        <div className="wrap">
          <TicketTester />
        </div>
      </section>
    </>
  )
}
