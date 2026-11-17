import { lerFiltros, descreverFiltros } from "@/engine/filtros";
import { b11, b12, b13 } from "@/engine/tela1";
import { requireUser } from "@/app/lib/auth";
import { TelaShell } from "@/app/components/telas/TelaShell";
import { Bloco, Numero } from "@/app/components/telas/Bloco";
import { ChurnContagens, ChurnTaxas, Satisfacao, UsoTotal, UsoSetor } from "@/app/components/telas/Tela1Graficos";

// Computed at request time from the read-only database — never prerendered.
export const dynamic = "force-dynamic";

const int = (n: number) => n.toLocaleString("pt-BR");
const usd = (n: number) => `US$ ${Math.round(n).toLocaleString("pt-BR")}`;

/** Screen 1 of the design: the three claims, checked against the data (B1.1–B1.3). */
export default async function TelaAfirmacoes({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const user = await requireUser();
  const f = lerFiltros(await searchParams);
  const c = b11(f);
  const s = b12(f);
  const u = b13(f);
  const pctSemNota = (x: { tickets: number; semNota: number }) =>
    x.tickets ? `${((100 * x.semNota) / x.tickets).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%` : "—";

  return (
    <TelaShell
      email={user.email}
      titulo="As três afirmações: o churn subiu, a satisfação está ok, o uso cresceu"
      subtitulo={`Jan/2023 a dez/2024 · ${descreverFiltros(f)}`}
    >
      <div className="flex flex-col gap-4">
        <Bloco
          codigo="B1.1"
          pergunta="O churn subiu?"
          nivel="contas e eventos por mês"
          limite={`há duas taxas. Contas com evento sem assinatura vigente no mês (${int(c.contasForaDaBase)} no período) entram numa e não na outra; elas diferem em ${int(c.mesesQueDiferem)} de 24 meses. Nenhum alerta de registro muda o churn por evento.`}
          sql={[c.sql, c.mrrPerdido.sql]}
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <div className="mb-1 text-[12px] font-medium text-foreground">Contas com evento e eventos por mês</div>
              <ChurnContagens meses={c.meses} contas={c.contasComEvento} eventos={c.eventos} />
            </div>
            <div>
              <div className="mb-1 text-[12px] font-medium text-foreground">Taxa de churn de contas por mês</div>
              <ChurnTaxas meses={c.meses} taxa={c.taxa} taxaNaBase={c.taxaNaBase} />
            </div>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
              <Numero rotulo="Eventos no período" valor={int(c.totalEventos)} />
              <Numero
                rotulo="MRR das contas com evento"
                valor={usd(c.mrrPerdido.mrr)}
                nota={`${int(c.mrrPerdido.contas)} contas · soma das assinaturas dessas contas`}
              />
          </div>
        </Bloco>

        <div className="grid gap-4 lg:grid-cols-2">
          <Bloco
            codigo="B1.2"
            pergunta="A satisfação está ok?"
            nivel="ticket"
            limite={`a escala só vai de 3 a 5, e muitos tickets não têm nota. ${int(s.ticketsT08)} tickets foram abertos antes do cadastro da conta.`}
            sql={[s.sql, s.totaisSql]}
          >
            <Satisfacao trimestres={s.trimestres} n3={s.nota3} n4={s.nota4} n5={s.nota5} sem={s.semNota} />
            <div className="grid grid-cols-2 gap-2">
              <Numero
                rotulo="Com registros em alerta"
                valor={`${int(s.comAlerta.tickets)} tickets`}
                nota={`${int(s.comAlerta.semNota)} sem nota (${pctSemNota(s.comAlerta)})`}
              />
              <Numero
                rotulo="Sem os tickets anteriores ao cadastro"
                valor={`${int(s.semAlerta.tickets)} tickets`}
                nota={`${int(s.semAlerta.semNota)} sem nota (${pctSemNota(s.semAlerta)})`}
              />
            </div>
          </Bloco>

          <Bloco
            codigo="B1.3"
            pergunta="O uso cresceu? Para todos?"
            nivel="registro de uso"
            limite={`${int(u.registrosT06)} registros caem fora do período da assinatura e ${int(u.registrosE13)} são registros repetidos. Serve para volume por mês, não para sequência.`}
            sql={[u.sql, u.setorSql]}
          >
            <UsoTotal meses={u.meses} com={u.comAlerta} sem={u.semAlerta} />
            <div className="grid grid-cols-2 gap-2">
              <Numero rotulo="Com registros em alerta" valor={`${int(u.totalCom)} registros`} />
              <Numero rotulo="Sem registros em alerta" valor={`${int(u.totalSem)} registros`} />
            </div>
            <div>
              <div className="mb-1 text-[12px] font-medium text-foreground">
                Por setor ({f.alerta === "sem" ? "sem" : "com"} registros em alerta)
              </div>
              <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
                {u.porSetor.map((p) => (
                  <div key={p.setor} className="rounded-lg border border-edge bg-surface/40 p-2">
                    <div className="text-[11px] text-muted">{p.setor}</div>
                    <UsoSetor meses={u.meses} valores={p.valores} />
                  </div>
                ))}
              </div>
            </div>
          </Bloco>
        </div>
      </div>
    </TelaShell>
  );
}
