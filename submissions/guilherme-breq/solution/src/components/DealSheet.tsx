"use client";

import { motion } from "motion/react";
import type { Deal } from "@/lib/data";
import { formatInt, formatPct } from "@/lib/format";
import type { Mark } from "@/lib/marks";
import { cyclePhase, type Step, type Window } from "@/lib/playbook";
import { formatUSD, MOMENTUM_WEIGHT, VALUE_WEIGHT, WINDOW_ALERT_DAYS } from "@/lib/scoring";
import { SavedNote } from "./ui";

const PHASE_LABEL = { antes: "Ainda cedo", decisao: "Fase de decisão", depois: "Passou da fase de decisão" } as const;

/** Ficha do deal: o que fazer agora e, em três cartões, por que este deal e por que agora. */
export function DealSheet({
  deal,
  step,
  position,
  win,
  maxCycle,
  curve,
  catalog,
  globalWinRate,
  mark,
  onMark,
  onBack,
}: {
  deal: Deal;
  step: Step;
  /** Ex.: "Ligar · 1 de 4". */
  position: string;
  win: Window;
  maxCycle: number;
  curve: number[];
  catalog: { min: number; max: number };
  globalWinRate: number;
  mark: Mark | undefined;
  onMark: (m: Mark | null) => void;
  onBack: () => void;
}) {
  const age = deal.ageDays ?? 0;
  const left = deal.daysLeft ?? 0;
  const phase = cyclePhase(age, win);
  const unlinked = !deal.account;

  return (
    <motion.article initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }} aria-labelledby="ficha-titulo">
      <div className="flex items-center justify-between gap-3 text-sm text-ink-3">
        <button type="button" onClick={onBack} className="-ml-2 inline-flex min-h-11 items-center px-2 font-semibold text-ink min-[900px]:hidden">
          ← Fila
        </button>
        <span className="text-[13px] font-bold uppercase tracking-wider text-gold-ink">{position}</span>
        <span>score {deal.score}</span>
      </div>

      <h1 id="ficha-titulo" tabIndex={-1} className="mb-2.5 mt-3 text-[40px] font-extrabold leading-none tracking-[-0.035em] text-ink outline-none min-[900px]:mt-5 min-[900px]:text-6xl">
        {deal.account ?? deal.product}
      </h1>
      <p className="flex flex-wrap gap-x-4 gap-y-0.5 text-sm text-ink-2">
        <span>{deal.product}</span>
        <span>{deal.sector ? `setor ${deal.sector}` : "sem setor"}</span>
        <span>
          {deal.region} · {deal.manager}
        </span>
        <span>{deal.id}</span>
        {unlinked && <span className="font-semibold text-brick">conta não vinculada no CRM</span>}
      </p>

      <section aria-label="O que fazer" className="on-navy my-7 flex flex-col gap-4 rounded-2xl bg-navy-deep px-5 py-4 text-fg min-[900px]:flex-row min-[900px]:items-center min-[900px]:justify-between min-[900px]:gap-5 min-[900px]:pl-6">
        <div>
          <p className="text-[13px] font-bold uppercase tracking-widest text-gold-hi">O que fazer</p>
          <p className="mt-0.5 text-xl font-bold leading-snug">{step.text}</p>
        </div>
        {mark ? (
          <div className="flex flex-wrap items-center gap-3">
            <p className={`text-sm font-semibold ${mark === "morto" ? "text-risk" : "text-gold-hi"}`} role="status">
              {mark === "feito" ? "Feito" : mark === "adiado" ? "Adiado para o fim da fila" : "Marcado: não está vivo"}
            </p>
            <button type="button" onClick={() => onMark(null)} className="min-h-11 rounded-[10px] border border-line-strong px-4 text-sm font-semibold text-fg hover:border-gold-hi">
              Desfazer
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => onMark("feito")} className="min-h-11 flex-1 rounded-[10px] border border-gold bg-gold px-4 text-sm font-bold text-navy-deep hover:bg-gold-hi">
              Feito
            </button>
            <button type="button" onClick={() => onMark("adiado")} className="min-h-11 flex-1 rounded-[10px] border border-line-strong px-4 text-sm font-semibold text-fg hover:border-gold-hi">
              Adiar
            </button>
            <button type="button" onClick={() => onMark("morto")} className="min-h-11 flex-1 whitespace-nowrap rounded-[10px] border border-line-strong px-4 text-sm font-semibold text-fg hover:border-gold-hi">
              Não está vivo
            </button>
          </div>
        )}
      </section>
      <SavedNote className="-mt-4 mb-6 text-ink-3" />

      <h2 className="mb-3 text-[13px] font-bold uppercase tracking-[0.14em] text-ink-3">Por que este deal, e por que agora</h2>
      <div className="grid gap-3.5 min-[900px]:grid-cols-3">
        <Card title="Quanto vale" big={formatUSD(deal.price)}>
          <p>
            {deal.price >= catalog.max ? "O ticket mais alto do catálogo. " : deal.valuePts >= 40 ? "Ticket alto. " : deal.valuePts >= 20 ? "Ticket médio. " : "Ticket baixo. "}
            O valor pesa em escala log: cada vez que o preço dobra, o deal ganha o mesmo tanto de pontos.
          </p>
          <PriceRule price={deal.price} catalog={catalog} />
          <Pts>
            {deal.valuePts} de {VALUE_WEIGHT} pontos
          </Pts>
        </Card>

        <Card title="Em que momento está" big={`dia ${age}`}>
          <p>
            {formatPct(deal.pDecide ?? 0)} dos deals com {age} dias se decidem no mês seguinte.{" "}
            {phase === "decisao" && `Está na fase de decisão (dias ${win.start} a ${win.end}).`}
            {phase === "antes" && `Ainda cedo: a fase de decisão começa no dia ${win.start}.`}
            {phase === "depois" && `Já saiu da fase de decisão (dias ${win.start} a ${win.end}).`}
          </p>
          <MomentCurve curve={curve} win={win} maxCycle={maxCycle} age={age} p={deal.pDecide ?? 0} phase={PHASE_LABEL[phase]} />
          <Pts>
            {deal.momentumPts} de {MOMENTUM_WEIGHT} pontos
          </Pts>
        </Card>

        <Card title="Quanto tempo resta" big={left === 1 ? "1 dia" : `${formatInt(left)} dias`}>
          <p>
            Até o dia {maxCycle}, o maior ciclo que já fechou. Depois disso, nenhum deal do histórico fechou.
            {left <= WINDOW_ALERT_DAYS && " A janela está fechando."}
          </p>
          <TimeBar age={age} maxCycle={maxCycle} left={left} />
          <span className="mt-3.5 block text-[13px] font-bold text-ink-3">não entra no score; desempata</span>
        </Card>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-rule bg-card px-5 py-3.5 text-sm text-ink-2">
        <b className="text-[26px] font-extrabold text-ink">{deal.score}</b>
        <span>pontos de 100</span>
        <span
          role="img"
          aria-label={`${deal.valuePts} pontos de valor e ${deal.momentumPts} de momento`}
          className="flex h-2.5 min-w-40 flex-1 basis-full overflow-hidden rounded-full bg-ink/10 min-[900px]:basis-0"
        >
          <i className="block h-full bg-blue" style={{ width: `${deal.valuePts}%` }} />
          <i className="block h-full bg-gold" style={{ width: `${deal.momentumPts}%` }} />
        </span>
        <span>
          {deal.valuePts} valor + {deal.momentumPts} momento
        </span>
      </div>

      <div className="mt-4 border-l-[3px] border-brick bg-brick/5 px-5 py-4 text-sm text-ink-2">
        <b className="text-brick">O que o score não sabe.</b> A chance de ganhar é {formatPct(globalWinRate)} para qualquer deal: vendedor, produto, setor e idade não mudaram isso no
        backtest, então ela não entra aqui. E o CRM não registra o último contato, o sinal que mais falta para medir “esfriar”.
      </div>
    </motion.article>
  );
}

function Card({ title, big, children }: { title: string; big: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-rule bg-card p-5 text-sm text-ink-2 [&_p]:m-0">
      <h3 className="text-[13px] font-bold">{title}</h3>
      <span className="mb-1 mt-2.5 block text-4xl font-extrabold leading-[1.1] tracking-[-0.03em] text-ink">{big}</span>
      {children}
    </section>
  );
}

const Pts = ({ children }: { children: React.ReactNode }) => <span className="mt-3.5 block text-[13px] font-bold text-gold-ink">{children}</span>;

/** Régua log de preço do catálogo, com o deal marcado. */
function PriceRule({ price, catalog }: { price: number; catalog: { min: number; max: number } }) {
  const span = Math.log(catalog.max) - Math.log(catalog.min);
  const t = span > 0 ? Math.min(1, Math.max(0, (Math.log(price) - Math.log(catalog.min)) / span)) : 1;
  const x = 4 + t * 272;
  return (
    <svg viewBox="0 0 280 50" className="mt-3.5 block h-auto w-full" role="img" aria-label={`Régua de preço do catálogo, de ${formatUSD(catalog.min)} a ${formatUSD(catalog.max)}; este deal está em ${formatUSD(price)}.`}>
      <line x1="4" x2="276" y1="16" y2="16" stroke="var(--color-ink)" strokeOpacity=".15" strokeWidth="6" strokeLinecap="round" />
      <line x1="4" x2={x} y1="16" y2="16" stroke="var(--color-blue)" strokeWidth="6" strokeLinecap="round" />
      <circle cx={x} cy="16" r="7" fill="var(--color-blue)" stroke="#fff" strokeWidth="2" />
      <text x="4" y="46" fontSize="15" className="fill-ink-3">
        {formatUSD(catalog.min)}
      </text>
      <text x="276" y="46" fontSize="15" textAnchor="end" className="fill-ink-3">
        {formatUSD(catalog.max)}
      </text>
    </svg>
  );
}

/** Curva de decisão por idade, com a fase de decisão em faixa e o ponto do deal. */
function MomentCurve({ curve, win, maxCycle, age, p, phase }: { curve: number[]; win: Window; maxCycle: number; age: number; p: number; phase: string }) {
  const W = 280;
  const H = 106;
  const mx = Math.max(...curve);
  const cx = (a: number) => 4 + (a / maxCycle) * (W - 8);
  const cy = (v: number) => H - 18 - (v / mx) * (H - 30);
  const path = curve.map((v, a) => `${a ? "L" : "M"}${cx(a).toFixed(1)},${cy(v).toFixed(1)}`).join("");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="mt-3.5 block h-auto w-full" role="img" aria-label={`Curva de decisão por idade. Este deal está no dia ${age}: ${phase.toLowerCase()}.`}>
      <rect x={cx(win.start)} y="4" width={cx(win.end) - cx(win.start)} height={H - 22} fill="var(--color-gold)" opacity=".22" />
      <path d={path} fill="none" stroke="var(--color-ink)" strokeWidth="1.8" />
      <line x1={cx(age)} x2={cx(age)} y1="4" y2={H - 18} stroke="var(--color-ink)" strokeDasharray="2 3" />
      <circle cx={cx(age)} cy={cy(p)} r="5" fill="var(--color-ink)" stroke="#fff" strokeWidth="2" />
      <text x="4" y={H - 3} fontSize="15" className="fill-ink-3">
        dia 0
      </text>
      <text x={W - 4} y={H - 3} fontSize="15" textAnchor="end" className="fill-brick">
        dia {maxCycle}
      </text>
    </svg>
  );
}

function TimeBar({ age, maxCycle, left }: { age: number; maxCycle: number; left: number }) {
  const w = 272;
  const done = Math.min(1, age / maxCycle) * w;
  const zone = (WINDOW_ALERT_DAYS / maxCycle) * w;
  return (
    <svg viewBox="0 0 280 50" className="mt-3.5 block h-auto w-full" role="img" aria-label={`${age} dias corridos de ${maxCycle}; restam ${left}.`}>
      <rect x="4" y="10" width={w} height="12" rx="6" fill="var(--color-ink)" fillOpacity=".08" />
      <rect x="4" y="10" width={done} height="12" rx="6" fill="var(--color-ink)" fillOpacity=".75" />
      <rect x={4 + w - zone} y="10" width={zone} height="12" fill="var(--color-brick)" fillOpacity=".4" />
      <text x="4" y="46" fontSize="15" className="fill-ink-3">
        engajou há {age} dias
      </text>
      <text x="276" y="46" fontSize="15" textAnchor="end" className="fill-brick">
        limite
      </text>
    </svg>
  );
}
