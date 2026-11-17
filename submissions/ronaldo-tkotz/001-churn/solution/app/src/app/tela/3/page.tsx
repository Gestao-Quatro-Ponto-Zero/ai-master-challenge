import { requireUser } from "@/app/lib/auth";
import { lerFiltros, descreverFiltros } from "@/engine/filtros";
import {
  indicadores3,
  mensal3,
  ticketsPorPrioridade,
  notasSatisfacao,
  faixasResolucao,
  faixasResposta,
  recursosMaisUsados,
  recursosErros,
} from "@/engine/tela3";
import { TelaShell } from "@/app/components/telas/TelaShell";
import { Painel } from "@/app/components/telas/Painel";
import { Indicador, Cabecalho } from "@/app/components/telas/Indicador";
import { Barras, Colunas, Donut, LinhasMensais } from "@/app/components/telas/VisaoGraficos";
import { RecursosErros } from "@/app/components/telas/Tela2Graficos";

// Computed at request time from the read-only database — never prerendered.
export const dynamic = "force-dynamic";

const int = (n: number) => n.toLocaleString("pt-BR");
const dec = (n: number | null, casas = 1) => (n === null ? "—" : n.toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }));
const mil = (n: number) => (n >= 1000 ? `${(n / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mil` : int(n));
const share = (a: number, b: number) => (b ? `${dec((100 * a) / b)}%` : "—");

/**
 * Screen 3 — support and product usage (D34, D43). One screen, no scroll: the headline numbers,
 * three month-by-month lines, how the tickets split, and the features.
 */
export default async function Tela3({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const user = await requireUser();
  const f = lerFiltros(await searchParams);
  const k = indicadores3(f);
  const m = mensal3(f);
  const prioridade = ticketsPorPrioridade(f);
  const notas = notasSatisfacao(f);
  const resolucao = faixasResolucao(f);
  const resposta = faixasResposta(f);
  const maisUsados = recursosMaisUsados(f);
  const recursos = recursosErros(f);

  return (
    <TelaShell email={user.email} titulo="Suporte e uso do produto" subtitulo={`Jan/2023 a dez/2024 · ${descreverFiltros(f)}`} ajustar>
      <div className="grid h-full grid-cols-[minmax(0,1fr)] grid-rows-[auto_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.05fr)] gap-2">
        <Cabecalho>
          <Indicador rotulo="Tickets" valor={int(k.tickets)} nota={`em ${int(k.contasComTicket)} contas`} />
          <Indicador rotulo="Tickets escalados" valor={int(k.escalados)} nota={`${share(k.escalados, k.tickets)} dos tickets`} />
          <Indicador rotulo="Satisfação média (1 a 5)" valor={dec(k.satisfacao, 2)} nota={`${dec(k.semNotaPct)}% sem nota`} />
          <Indicador rotulo="Resolução média" valor={`${dec(k.resolucaoH)} h`} />
          <Indicador rotulo="1ª resposta média" valor={`${dec(k.respostaMin, 0)} min`} />
          <Indicador rotulo="Usos do produto" valor={mil(k.usos)} nota={`${int(k.horasUso)} horas de uso`} separa />
          <Indicador rotulo="Erros" valor={int(k.erros)} />
          <Indicador rotulo="Taxa de erro" valor={`${dec(k.taxaErroPct, 2)}%`} nota="erros por uso" />
        </Cabecalho>

        <div className="grid min-h-0 gap-2 lg:grid-cols-3">
          <Painel titulo="Tickets por mês" nota="tickets abertos no mês e quantos foram escalados" sql={[m.sqlTickets]}>
            <LinhasMensais
              meses={m.meses}
              series={[
                { nome: "Tickets", valores: m.tickets, tema: "volume" },
                { nome: "Escalados", valores: m.escalados, tema: "problema" },
              ]}
              formato="int"
            />
          </Painel>
          <Painel titulo="Satisfação média por mês" nota="nota de 1 a 5 dos tickets avaliados no mês" sql={[m.sqlTickets]}>
            <LinhasMensais meses={m.meses} series={[{ nome: "Satisfação média", valores: m.satisfacao, tema: "volume" }]} formato="dec" yMax={5} />
          </Painel>
          <Painel titulo="Uso do produto por mês" nota="usos de recursos registrados no mês" sql={[m.sqlUso]}>
            <LinhasMensais meses={m.meses} series={[{ nome: "Usos", valores: m.usos, tema: "volume" }]} formato="int" />
          </Painel>
        </div>

        <div className="grid min-h-0 grid-cols-2 gap-2 lg:grid-cols-4">
          <Painel titulo="Tickets por prioridade" nota="parte de cada prioridade no total de tickets" sql={[prioridade.sql]}>
            <Donut dados={prioridade.dados} formato="int" />
          </Painel>
          <Painel titulo="Notas de satisfação" nota="parte de cada nota no total de tickets" sql={[notas.sql]}>
            <Donut dados={notas.dados} formato="int" />
          </Painel>
          <Painel titulo="Tempo de resolução" nota="tickets por faixa de tempo até fechar" sql={[resolucao.sql]}>
            <Barras dados={resolucao.dados} formato="int" tema="receita" />
          </Painel>
          <Painel titulo="Tempo até a 1ª resposta" nota="tickets por faixa de tempo" sql={[resposta.sql]}>
            <Barras dados={resposta.dados} formato="int" tema="receita" />
          </Painel>
        </div>

        <div className="grid min-h-0 gap-2 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
          <Painel titulo="Recursos: uso × taxa de erro" nota="um ponto por recurso; o uso beta de cada recurso aparece separado" sql={[recursos.sql]}>
            <RecursosErros recursos={recursos.recursos} />
          </Painel>
          <Painel titulo="Os 10 recursos mais usados" nota="usos no período" sql={[maisUsados.sql]}>
            <Colunas dados={maisUsados.dados} formato="int" tema="receita" gradiente />
          </Painel>
        </div>
      </div>
    </TelaShell>
  );
}
