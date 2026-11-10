import { Estado } from "@/components/Estado";
import { FiltroLivre, Seletor } from "@/components/Filtros";
import { FiltrosEquipe } from "@/components/FiltrosEquipe";
import { Quadro } from "@/components/Quadro";
import { CONFIG } from "@/lib/config";
import { juntar } from "@/lib/filtro/etiquetas";
import { lerEtiquetas, lerFiltrosEquipe } from "@/server/parametros";
import { colunasPipeline, contextoFiltro, escopoDe, somenteLeitura, type Ordem } from "@/server/repositorio";
import { exigirUsuario } from "@/server/sessao";

export const metadata = { title: "Pipeline" };

const ORDENS: { valor: Ordem; rotulo: string }[] = [
  { valor: "nota", rotulo: "Nota" },
  { valor: "valor", rotulo: "Valor esperado" },
  { valor: "dias_sem_contato", rotulo: "Dias sem contato" },
  { valor: "dias_aberto", rotulo: "Mais tempo aberto" },
  { valor: "abertura", rotulo: "Abertura mais recente" },
];

type Params = { f?: string; ordem?: string; n?: string; regiao?: string; manager?: string; vendedor?: string };

export default async function Pagina({ searchParams }: { searchParams: Promise<Params> }) {
  const p = await searchParams;
  const usuario = await exigirUsuario("/pipeline");
  const filtros = await lerFiltrosEquipe(usuario, p);
  const etiquetas = lerEtiquetas(p.f);
  const ordem = ORDENS.find((o) => o.valor === p.ordem)?.valor ?? "nota";
  const limite = Math.min(Math.max(Number(p.n) || CONFIG.cartoesPorColuna, CONFIG.cartoesPorColuna), 500);
  const [colunas, contexto] = await Promise.all([
    colunasPipeline(escopoDe(usuario, filtros), juntar(etiquetas), ordem, limite),
    contextoFiltro("pipeline", usuario),
  ]);
  const total = colunas.reduce((a, c) => a + c.total, 0);

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-2xl font-bold">Pipeline</h1>
        <FiltrosEquipe filtros={filtros} />
      </div>
      <div className="flex flex-wrap items-start gap-3">
        <FiltroLivre contexto={contexto} etiquetas={etiquetas} exemplo="super hot sem contato" />
        <Seletor nome="ordem" rotulo="Ordenar" valor={ordem} opcoes={ORDENS} />
      </div>
      {total === 0 ? (
        etiquetas.length ? (
          <Estado titulo="Nenhum deal com estes filtros" texto="Remova uma etiqueta acima ou limpe os filtros para ver o pipeline inteiro." />
        ) : (
          <Estado titulo="Nenhum deal aberto" texto="Não há deals em prospecção nem em negociação neste perfil. Quando um lead novo entrar, ele aparece aqui." />
        )
      ) : (
        <Quadro colunas={colunas} papel={usuario.papel} somenteLeitura={somenteLeitura()} mostrarVendedor={usuario.papel !== "vendedor"} />
      )}
    </div>
  );
}
