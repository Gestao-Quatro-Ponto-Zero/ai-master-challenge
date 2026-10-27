import type { Metadata } from "next";
import { Suspense } from "react";
import { PipelineView } from "@/components/pipeline-view";
import { count } from "@/lib/format";
import { history } from "@/lib/pipeline";

export const metadata: Metadata = { title: "Parados" };

export default function StalledPage(props: PageProps<"/parados">) {
  return (
    <Suspense fallback={<p className="text-secondary">Carregando a fila…</p>}>
      <Stalled searchParams={props.searchParams} />
    </Suspense>
  );
}

async function Stalled({ searchParams }: { searchParams: PageProps<"/parados">["searchParams"] }) {
  return (
    <PipelineView
      params={await searchParams}
      basePath="/parados"
      title="Fila de revisão"
      description={`Deals abertos há mais de ${history.maxCycle} dias. Nenhum dos ${count(history.closedDeals)} deals já fechados levou tanto tempo: confirme com o cliente se ainda há projeto ou desqualifique para limpar a previsão.`}
      fixed={{ momentum: "stalled" }}
    />
  );
}
