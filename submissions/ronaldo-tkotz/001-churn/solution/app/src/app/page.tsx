import { tableInventory } from "@/engine/dashboard";
import { activeDataset } from "@/engine/datasets";
import { lerFiltros, descreverFiltros } from "@/engine/filtros";
import {
  indicadores,
  crescimentoMensal,
  receitaPorSetor,
  receitaPorPlano,
  receitaPorPais,
  receitaNovaVsPerdida,
  contasPagasTrial,
  idadeMedia,
} from "@/engine/visaoGeral";
import { requireUser } from "@/app/lib/auth";
import { Sidebar } from "./components/dashboard/Sidebar";
import { TopBar } from "./components/dashboard/TopBar";
import { ConnectDialog } from "./components/dashboard/ConnectDialog";
import { DataSourceDialog } from "./components/dashboard/DataSourceDialog";
import { ConversationCanvas } from "./components/dashboard/ConversationCanvas";
import { CustomDatasetBrief } from "./components/dashboard/CustomDatasetBrief";
import { TelaShell } from "./components/telas/TelaShell";
import { Indicador } from "./components/telas/Indicador";
import { Painel } from "./components/telas/Painel";
import { Colunas, CrescimentoMensal, Donut, IdadeMedia, ReceitaNovaPerdida } from "./components/telas/VisaoGraficos";

// Computed at request time from the read-only database — never prerendered.
export const dynamic = "force-dynamic";

const int = (n: number) => n.toLocaleString("pt-BR");
const usdMi = (n: number) => `US$ ${(n / 1e6).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mi`;
const pct = (n: number) => `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
const mesBr = (m: string) => {
  const [y, mm] = m.split("-");
  return `${["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][Number(mm) - 1]}/${y}`;
};


export default async function Home({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const user = await requireUser();
  const active = activeDataset(user.id);

  // An uploaded database: the screens read the RavenStack views, so the surface goes to
  // the schema-agnostic chat — still fully grounded.
  if (!active.is_default) {
    const userCtx = { userId: user.id };
    const tables = tableInventory(userCtx);
    const ctx = { source: active.label, tableCount: tables.length, asOf: "", firstDate: "", lastDate: "" };
    return (
      <div className="flex h-screen overflow-hidden bg-background">
        <div className="hidden lg:block">
          <Sidebar email={user.email} />
        </div>
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar ctx={ctx} tables={tables} />
          <main className="flex min-h-0 flex-1 gap-4 overflow-hidden p-4">
            <ConversationCanvas idleBrief={<CustomDatasetBrief label={active.label} tables={tables} />} />
          </main>
        </div>
        <ConnectDialog />
        <DataSourceDialog />
      </div>
    );
  }

  const f = lerFiltros(await searchParams);
  const k = indicadores(f);
  const cresc = crescimentoMensal(f);
  const rSetor = receitaPorSetor(f);
  const rPlano = receitaPorPlano(f);
  const rPais = receitaPorPais(f);
  const share = (a: number, b: number) => (b ? pct(Math.round((1000 * a) / b) / 10) : "—");
  const receita = receitaNovaVsPerdida(f);
  const pagasTrial = contasPagasTrial(f);
  const idade = idadeMedia(f);
  const ate = receita.mesesAteCruzamento;
  const previsao = !receita.mesCruzamento
    ? "no ritmo de 2024, a perda não alcança a receita nova"
    : ate !== null && ate <= 0
      ? `no ritmo de 2024, a perda já alcançou a receita nova em ${mesBr(receita.mesCruzamento)}`
      : `a perda alcança a receita nova em ${mesBr(receita.mesCruzamento)} (${ate} ${ate === 1 ? "mês" : "meses"}), no ritmo de 2024`;

  return (
    <TelaShell email={user.email} titulo="Visão geral" subtitulo={`Jan/2023 a dez/2024 · ${descreverFiltros(f)}`} ajustar>
      <div className="grid h-full grid-cols-[minmax(0,1fr)] grid-rows-[auto_minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,0.95fr)] gap-2">
        <section className="flex min-w-0 flex-wrap overflow-hidden rounded-lg border border-edge bg-panel py-1 xl:flex-nowrap">
          <Indicador rotulo="Total de contas" valor={int(k.contas)} />
          <Indicador rotulo="Contas com churn" valor={int(k.contasFlag)} nota={`${share(k.contasFlag, k.contas)} do total`} />
          <Indicador rotulo="Eventos de churn" valor={int(k.eventos)} separa />
          <Indicador rotulo="Contas com evento de churn" valor={int(k.contasComChurn)} nota={`${share(k.contasComChurn, k.contas)} das contas`} />
          <Indicador rotulo={`Churn rate ${mesBr(k.ultimoMes)}`} valor={pct(k.taxaUltimoMes)} nota={`média 2024: ${pct(k.mediaTaxa2024)}`} />
          <Indicador rotulo="Total de assinaturas" valor={int(k.assinaturas)} separa />
          <Indicador rotulo="Assinaturas encerradas" valor={int(k.assinaturasEncerradas)} nota={`em ${int(k.contasComAssinaturaEncerrada)} contas`} />
          <Indicador rotulo="Receita mensal (MRR)" valor={usdMi(k.mrrAtivo)} nota={`ARR ${usdMi(12 * k.mrrAtivo)}`} />
        </section>

        <div className="grid min-h-0 gap-2 lg:grid-cols-2">
          <Painel titulo="Crescimento mês a mês: contas × churn" nota={`variação % sobre o mês anterior, desde ${mesBr(cresc.primeiroMes)}`} sql={[cresc.sql]}>
            <CrescimentoMensal meses={cresc.meses} contas={cresc.contas} churn={cresc.churn} tendContas={cresc.tendContas} tendChurn={cresc.tendChurn} />
          </Painel>
          <Painel titulo="Receita nova × receita perdida, por mês" nota={previsao} sql={[receita.sql]}>
            <ReceitaNovaPerdida
              meses={receita.meses}
              nova={receita.nova}
              perdida={receita.perdida}
              tendNova={receita.tendNova}
              tendPerdida={receita.tendPerdida}
              inicioProjecao={receita.inicioProjecao}
              cruzamento={
                receita.mesCruzamento
                  ? { index: receita.meses.indexOf(receita.mesCruzamento), label: `cruzam em ${mesBr(receita.mesCruzamento)}` }
                  : null
              }
            />
          </Painel>
        </div>

        <Painel titulo="Idade média da base, por mês" nota="em meses, no fim de cada mês, de jan/2023 a dez/2024" sql={[idade.sql]}>
          <IdadeMedia meses={idade.meses} contas={idade.contas} assinaturas={idade.assinaturas} />
        </Painel>

        <div className="grid min-h-0 grid-cols-2 gap-2 lg:grid-cols-4">
          <Painel titulo="Receita por plano" nota="MRR das assinaturas ativas" sql={[rPlano.sql]}>
            <Donut dados={rPlano.dados} formato="usd" recorte={{ universo: "assinatura", dim: "plano_assin" }} />
          </Painel>
          <Painel titulo="Contas pagas × trial" nota="% do total de contas" sql={[pagasTrial.sql]}>
            <Donut dados={pagasTrial.dados.map((d) => ({ ...d, chave: d.label === "Trial" ? "Sim" : "Não" }))} formato="int" recorte={{ universo: "conta", dim: "trial_conta" }} />
          </Painel>
          <Painel titulo="Receita por indústria" nota="MRR das assinaturas ativas, US$" sql={[rSetor.sql]}>
            <Colunas dados={rSetor.dados} formato="usd" tema="receita" recorte={{ universo: "conta", dim: "setor" }} />
          </Painel>
          <Painel titulo="Receita por país" nota="MRR das assinaturas ativas, US$" sql={[rPais.sql]}>
            <Colunas dados={rPais.dados} formato="usd" tema="receita" recorte={{ universo: "conta", dim: "pais" }} />
          </Painel>
        </div>
      </div>
    </TelaShell>
  );
}
