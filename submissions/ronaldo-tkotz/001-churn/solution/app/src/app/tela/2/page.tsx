import { requireUser } from "@/app/lib/auth";
import { lerFiltros, descreverFiltros } from "@/engine/filtros";
import { churnPorSetor, churnPorOrigem, churnPorPais, motivosChurn } from "@/engine/visaoGeral";
import { composicaoPlano, composicaoCobranca, composicaoTrial, motivoPt } from "@/engine/tela2";
import { TelaShell } from "@/app/components/telas/TelaShell";
import { Painel } from "@/app/components/telas/Painel";
import { Colunas, Donut } from "@/app/components/telas/VisaoGraficos";

// Computed at request time from the read-only database — never prerendered.
export const dynamic = "force-dynamic";

const CONTAS = "% das contas com churn";

/**
 * Screen 2 — "O que está causando o churn?" (D34): churn broken down by every attribute the base
 * has, one chart each, on one screen with no scroll. Five or more bars are columns (D32).
 */
export default async function Tela2({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const user = await requireUser();
  const f = lerFiltros(await searchParams);
  const setor = churnPorSetor(f);
  const origem = churnPorOrigem(f);
  const pais = churnPorPais(f);
  const motivos = motivosChurn(f);
  const plano = composicaoPlano(f);
  const cobranca = composicaoCobranca(f);
  const trial = composicaoTrial(f);

  return (
    <TelaShell email={user.email} titulo="O que está causando o churn?" subtitulo={`Jan/2023 a dez/2024 · ${descreverFiltros(f)}`} ajustar>
      <div className="grid h-full grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1.5fr)_minmax(0,1fr)] gap-2">
        <div className="grid min-h-0 grid-cols-2 gap-2 lg:grid-cols-4">
          <Painel titulo="Churn por indústria" nota={CONTAS} sql={[setor.sql]}>
            <Colunas dados={setor.dados} formato="pct" tema="churn" gradiente />
          </Painel>
          <Painel titulo="Churn por origem" nota={CONTAS} sql={[origem.sql]}>
            <Colunas dados={origem.dados} formato="pct" tema="churn" gradiente />
          </Painel>
          <Painel titulo="Churn por país" nota={CONTAS} sql={[pais.sql]}>
            <Colunas dados={pais.dados} formato="pct" tema="churn" gradiente />
          </Painel>
          <Painel titulo="Eventos de churn por motivo" nota="motivo declarado no cancelamento" sql={[motivos.sql]}>
            <Colunas dados={motivos.dados.map((d) => ({ ...d, label: motivoPt(d.label) }))} formato="int" tema="churn" gradiente />
          </Painel>
        </div>

        <div className="grid min-h-0 grid-cols-3 gap-2">
          <Painel titulo="Churn por plano" nota="parte de cada plano nas contas com churn" sql={[plano.sql]}>
            <Donut dados={plano.dados} formato="int" />
          </Painel>
          <Painel titulo="Churn por tipo de cobrança" nota="parte de cada cobrança nas assinaturas com churn" sql={[cobranca.sql]}>
            <Donut dados={cobranca.dados} formato="int" />
          </Painel>
          <Painel titulo="Churn no teste × no pago" nota="parte de trial e pagas nas contas com churn" sql={[trial.sql]}>
            <Donut dados={trial.dados} formato="int" />
          </Painel>
        </div>
      </div>
    </TelaShell>
  );
}
