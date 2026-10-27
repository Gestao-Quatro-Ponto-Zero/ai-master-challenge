import type { Metadata } from "next";
import { Suspense } from "react";
import { PipelineView } from "@/components/pipeline-view";

export const metadata: Metadata = { title: "Pipeline" };

export default function PipelinePage(props: PageProps<"/pipeline">) {
  return (
    <Suspense fallback={<p className="text-secondary">Carregando o pipeline…</p>}>
      <Pipeline searchParams={props.searchParams} />
    </Suspense>
  );
}

async function Pipeline({ searchParams }: { searchParams: PageProps<"/pipeline">["searchParams"] }) {
  return (
    <PipelineView
      params={await searchParams}
      basePath="/pipeline"
      title="Pipeline"
      description="Todos os deals abertos, ordenados por valor esperado. Filtre por vendedor, time, produto ou momento; o link guarda os filtros."
    />
  );
}
