import { InfoTip } from '@/components/InfoTip'
import { QueueBoard } from '@/components/QueueBoard'
import queue from '@/data/queue.json'
import stress from '@/data/stress.json'
import { EXPLAIN } from '@/lib/glossary'
import { num, pct } from '@/lib/labels'
import type { QueueTicket, StressReport } from '@/lib/types'

const report = stress as unknown as StressReport

export default function QueuePage() {
  const b = report.baseline
  const tested = Math.round(Object.values(b.tiers).reduce((s, t) => s + t.share, 0) * 7176)
  return (
    <>
      <section className="hero">
        <div className="wrap">
          <p className="eyebrow">Redesign de suporte · fila do agente</p>
          <h1>
            O ticket já chega <span className="accent">triado.</span>
          </h1>
          <p className="lede">
            O roteador lê o ticket, escolhe a fila e diz o quanto confia. Quando a confiança é alta, segue direto. Quando não é, uma pessoa decide com
            as duas filas mais prováveis na mão. Pedido de acesso privilegiado e conteúdo de RH passam sempre por gente.
          </p>
          <div className="stats" role="list">
            <div className="stat" role="listitem">
              <b>{pct(b.tiers.auto.share, 0)}</b>
              <span>
                dos tickets seguem sozinhos, com {pct(b.tiers.auto.precision ?? 0, 0)} de precisão <InfoTip label="automático" text={EXPLAIN.auto} />
              </span>
            </div>
            <div className="stat" role="listitem">
              <b>{pct(b.tiers.assist.share, 0)}</b>
              <span>
                vão para o agente com 2 sugestões; a certa está nelas em {pct(b.assist_top2_accuracy, 0)} <InfoTip label="assistido" text={EXPLAIN.assist} />
              </span>
            </div>
            <div className="stat" role="listitem">
              <b>{pct(b.tiers.human.share, 0)}</b>
              <span>
                vão para triagem humana desde o início <InfoTip label="humano" text={EXPLAIN.human} />
              </span>
            </div>
            <div className="stat" role="listitem">
              <b>{num(tested)}</b>
              <span>
                tickets reais de teste, nunca vistos no treino <InfoTip label="conjunto de teste" text={EXPLAIN.testSet} />
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">Amostra da fila</p>
            <h2>
              Abra um ticket e veja a <span className="accent">decisão</span> e o porquê
              <InfoTip
                label="amostra da fila"
                text="Amostra estratificada do conjunto de teste: tickets escolhidos para mostrar cada rota e cada trava. As colunas ordenam com um clique."
              />
            </h2>
            <p>
              São {queue.length} tickets reais do conjunto de teste, escolhidos para mostrar todos os caminhos: automático, assistido, humano e cada
              trava de segurança. Confirme, troque a fila ou escale, como o agente faria.
            </p>
          </div>
          <QueueBoard tickets={queue as QueueTicket[]} />
        </div>
      </section>
    </>
  )
}
