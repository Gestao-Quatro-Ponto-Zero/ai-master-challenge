import Link from "next/link";
import { TabelaContas } from "@/components/Contas";
import { Estado } from "@/components/Estado";
import { FiltroLivre, Seletor } from "@/components/Filtros";
import { FiltrosEquipe } from "@/components/FiltrosEquipe";
import { LotesRecentes } from "@/components/LotesRecentes";
import { NovoLead } from "@/components/NovoLead";
import { TabelaLeads } from "@/components/TabelaLeads";
import { dinheiroCurto, plural } from "@/lib/calculos";
import { CONFIG } from "@/lib/config";
import { juntar } from "@/lib/filtro/etiquetas";
import { lerEtiquetas, lerFiltrosEquipe } from "@/server/parametros";
import {
  buscarContas, buscarDeals, contextoFiltro, escopoDe, listarProdutos, listarTags, podeEditarContas, somenteLeitura, type Ordem, type OrdemContas,
} from "@/server/repositorio";
import { exigirUsuario } from "@/server/sessao";

export const metadata = { title: "Leads" };

const ORDENS: { valor: Ordem; rotulo: string }[] = [
  { valor: "padrao_leads", rotulo: "Abertos primeiro" },
  { valor: "nota", rotulo: "Nota" },
  { valor: "valor", rotulo: "Valor" },
  { valor: "abertura", rotulo: "Abertura mais recente" },
  { valor: "dias_sem_contato", rotulo: "Dias sem contato" },
  { valor: "fechamento", rotulo: "Fechamento mais recente" },
  { valor: "vendedor", rotulo: "Vendedor" },
  { valor: "lead", rotulo: "Lead (A–Z)" },
];
const ORDENS_CONTAS: { valor: OrdemContas; rotulo: string }[] = [
  { valor: "receita", rotulo: "Receita ganha" },
  { valor: "compras", rotulo: "Compras" },
  { valor: "abertos", rotulo: "Deals abertos" },
  { valor: "bonus", rotulo: "Bônus" },
  { valor: "nome", rotulo: "Empresa (A–Z)" },
];

type Params = { aba?: string; f?: string; ordem?: string; n?: string; regiao?: string; manager?: string; vendedor?: string };

export default async function Pagina({ searchParams }: { searchParams: Promise<Params> }) {
  const p = await searchParams;
  const usuario = await exigirUsuario("/leads");
  const contas = p.aba === "contas";
  const etiquetas = lerEtiquetas(p.f);
  const aba = (ativa: boolean) => `border-b-2 px-4 py-2 text-sm font-semibold ${ativa ? "border-marinho text-marinho" : "border-fundo text-texto-2 hover:text-marinho"}`;

  const cabecalho = (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold">Leads</h1>
        <nav aria-label="Abas de Leads" className="mt-2 flex gap-1 border-b border-linha">
          <Link href="/leads" aria-current={contas ? undefined : "page"} className={aba(!contas)}>
            Leads
          </Link>
          <Link href="/leads?aba=contas" aria-current={contas ? "page" : undefined} className={aba(contas)}>
            Contas
          </Link>
        </nav>
      </div>
    </div>
  );

  if (contas) {
    const ordem = ORDENS_CONTAS.find((o) => o.valor === p.ordem)?.valor ?? "receita";
    const [lista, contexto] = await Promise.all([buscarContas(juntar(etiquetas), ordem), contextoFiltro("contas", usuario)]);
    return (
      <div className="grid gap-4">
        {cabecalho}
        <div className="flex flex-wrap items-start gap-3">
          <FiltroLivre contexto={contexto} etiquetas={etiquetas} exemplo="varejo com deal aberto" />
          <Seletor nome="ordem" rotulo="Ordenar" valor={ordem} opcoes={ORDENS_CONTAS} />
        </div>
        <p className="text-sm text-texto-2">
          {plural(lista.length, "empresa", "empresas")} · {dinheiroCurto(lista.reduce((a, c) => a + c.receitaGanha, 0))} em receita ganha
        </p>
        <TabelaContas contas={lista} empresas={contexto.empresas} podeEditar={podeEditarContas()} />
      </div>
    );
  }

  const filtros = await lerFiltrosEquipe(usuario, p);
  const ordem = ORDENS.find((o) => o.valor === p.ordem)?.valor ?? "padrao_leads";
  const limite = Math.min(Math.max(Number(p.n) || CONFIG.porPagina, CONFIG.porPagina), 1000);
  const [pagina, contexto, tags, produtos] = await Promise.all([
    buscarDeals(escopoDe(usuario, filtros), juntar(etiquetas), ordem, 0, limite),
    contextoFiltro("leads", usuario),
    listarTags(),
    listarProdutos(),
  ]);
  const leitura = somenteLeitura();

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        {cabecalho}
        <div className="flex flex-wrap items-center gap-3">
          <FiltrosEquipe filtros={filtros} />
          {leitura ? null : <LotesRecentes />}
          {leitura ? null : <NovoLead papel={usuario.papel} produtos={produtos} empresas={contexto.empresas} vendedores={contexto.vendedores} />}
        </div>
      </div>
      <div className="flex flex-wrap items-start gap-3">
        <FiltroLivre contexto={contexto} etiquetas={etiquetas} exemplo="ganhos em 2017 varejo" />
        <Seletor nome="ordem" rotulo="Ordenar" valor={ordem} opcoes={ORDENS} />
      </div>
      <p className="text-sm text-texto-2">{plural(pagina.total, "lead", "leads")} neste filtro.</p>
      {pagina.total === 0 ? (
        etiquetas.length ? (
          <Estado titulo="Nenhum lead com estes filtros" texto="Remova uma etiqueta acima ou limpe os filtros para ver a base inteira." />
        ) : (
          <Estado titulo="Ainda não há leads" texto="Cadastre o primeiro lead no botão Novo lead." />
        )
      ) : (
        <TabelaLeads
          linhas={pagina.linhas}
          total={pagina.total}
          papel={usuario.papel}
          somenteLeitura={leitura}
          mostrarVendedor={usuario.papel !== "vendedor"}
          tags={tags}
          filtro={{ f: p.f, regiao: filtros.regiao, manager: filtros.manager, vendedor: filtros.vendedor }}
        />
      )}
    </div>
  );
}
