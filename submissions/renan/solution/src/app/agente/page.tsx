import type { Metadata } from "next";
import { Suspense } from "react";
import { AgentChat } from "@/components/agent-chat";
import { asOptions, SelectField, SubmitButton } from "@/components/select-field";
import { PageHeader } from "@/components/ui";
import { buildInsights } from "@/lib/agent/insights";
import { options, parseFilters } from "@/lib/pipeline";

export const metadata: Metadata = { title: "Agente Gestor" };

export default function AgentPage(props: PageProps<"/agente">) {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Agente Gestor"
        description="Seu analista de dados de vendas: o Radar avisa o que exige ação sem você perguntar, e o agente responde perguntas com números, gráficos e os deals do pipeline. Só dados da Régua."
      />
      <Suspense fallback={<p className="text-secondary">Calculando o radar…</p>}>
        <Agent searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

async function Agent({ searchParams }: { searchParams: PageProps<"/agente">["searchParams"] }) {
  const { agent, manager } = parseFilters(await searchParams);
  return (
    <>
      <form method="get" className="flex flex-wrap items-end gap-3">
        <SelectField name="vendedor" label="Vendedor" value={agent} options={asOptions(options.agents)} allLabel="Todo o time" className="w-[min(100%,16rem)]" />
        <SelectField name="manager" label="Manager" value={manager} options={asOptions(options.managers)} allLabel="Todos" className="w-[min(100%,14rem)]" />
        <SubmitButton>Analisar</SubmitButton>
      </form>
      <AgentChat key={`${agent}-${manager}`} agent={agent} insights={buildInsights({ agent, manager })} />
    </>
  );
}
