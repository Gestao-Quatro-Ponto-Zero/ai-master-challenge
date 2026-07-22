import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("next/dynamic", () => ({
  default: () => function MockGraph(props: unknown) {
    const { onSelect } = props as { onSelect: (id: string) => void };
    return <button onClick={() => onSelect("eventtype_churn")}>Nó simulado do grafo</button>;
  }
}));

import { AppShell } from "@/components/AppShell";
import { EmptyState, ErrorState, GovernanceChecklist, MetricCard } from "@/components/ui";
import { JourneyExplorer } from "@/components/JourneyExplorer";
import { GraphExplorer } from "@/components/GraphExplorer";
import { WatchlistTable } from "@/components/WatchlistExplorer";
import { ExperimentExplorer } from "@/components/ExperimentExplorer";
import { GuidedDemo } from "@/components/GuidedDemo";
import { formatStructuredLabel } from "@/lib/format";
import journeyPayload from "@/public/data/journey_samples.json";
import graphNodes from "@/public/data/graph_nodes.json";
import graphEdges from "@/public/data/graph_edges.json";
import watchlistPayload from "@/public/data/watchlist_items_demo.json";
import experimentRegistry from "@/public/data/experiment_registry.json";
import experimentDetails from "@/public/data/experiment_details.json";
import type { Experiment, JourneySample, WatchlistItem } from "@/lib/types";

const demoSteps = [
  { step: 1, route: "/", title: "O problema", sentence: "Eventos fragmentados ocultam a jornada do cliente.", metric: "35.586 eventos processados", insight: "Fontes brutas exigem governança.", limitation: "Somente captura histórica." },
  { step: 2, route: "/quality", title: "Qualidade antes da interpretação", sentence: "A qualidade é controlada.", metric: "13.927 eventos utilizáveis", insight: "Alertas permanecem visíveis.", limitation: "A população principal inclui alertas." }
];

describe("experiência do dashboard", () => {
  beforeEach(() => vi.clearAllMocks());

  test("card executivo usa formatação e contexto em português", () => {
    render(<MetricCard metric={{ label: "Jornadas", value: 4221, context: "Em todos os escopos governados" }} />);
    expect(screen.getByText("4.221")).toBeVisible();
    expect(screen.getByText("Em todos os escopos governados")).toBeVisible();
  });

  test("navegação principal expõe todas as áreas em português", () => {
    render(<AppShell><p>Conteúdo</p></AppShell>);
    expect(screen.getByRole("navigation")).toBeVisible();
    expect(screen.getByRole("link", { name: "Qualidade dos dados" })).toHaveAttribute("href", "/quality");
    expect(screen.getByRole("link", { name: "Grafo" })).toHaveAttribute("href", "/graph");
    expect(screen.getAllByRole("link", { name: /demonstração guiada/i }).length).toBeGreaterThan(0);
  });

  test("menu responsivo abre e fecha com rótulos acessíveis", async () => {
    const user = userEvent.setup();
    render(<AppShell><p>Conteúdo</p></AppShell>);
    await user.click(screen.getByRole("button", { name: "Abrir navegação" }));
    expect(screen.getByRole("button", { name: "Fechar navegação" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Fechar navegação" }));
  });

  test("estados vazio e de erro são legíveis em português", () => {
    const { rerender } = render(<EmptyState title="Sem dados" message="Nenhum item corresponde." />);
    expect(screen.getByRole("status")).toHaveTextContent("Nenhum item corresponde");
    rerender(<ErrorState title="Indisponível" message="Artefato local ausente." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Artefato local ausente");
  });

  test("explorador seleciona perfis anônimos sem expor chaves", async () => {
    const user = userEvent.setup();
    const samples = journeyPayload.samples as JourneySample[];
    render(<JourneyExplorer samples={samples} />);
    expect(screen.getAllByText("Perfil A — sem churn observado").length).toBeGreaterThan(0);
    await user.selectOptions(screen.getByLabelText("Perfil anônimo"), samples[1].account_key);
    expect(screen.getAllByText("Perfil B — churn recorrente").length).toBeGreaterThan(0);
    for (const sample of samples) expect(screen.queryByText(sample.account_key)).not.toBeInTheDocument();
  });

  test("filtros de jornada expõem estado vazio e permitem recuperação", async () => {
    const user = userEvent.setup();
    render(<JourneyExplorer samples={journeyPayload.samples as JourneySample[]} />);
    await user.selectOptions(screen.getByLabelText("Desfecho observado"), "RECURRING_CHURN");
    await user.selectOptions(screen.getByLabelText("Taxonomia da jornada"), "HIGH_VALUE_LOW_USAGE");
    expect(screen.getByText("Nenhuma jornada corresponde a estes filtros.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Redefinir filtros" }));
    expect(screen.getByLabelText("Perfil anônimo")).toBeVisible();
  });

  test("filtros e detalhe selecionado do grafo funcionam", async () => {
    const user = userEvent.setup();
    render(<GraphExplorer nodeData={graphNodes as never} edgeData={graphEdges as never} />);
    expect(screen.getByText(/explicitamente truncada/i)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Nó simulado do grafo" }));
    expect(screen.getByRole("heading", { name: "Churn" })).toBeVisible();
    await user.selectOptions(screen.getByLabelText("Modo do grafo"), "pattern-explorer");
    expect(screen.getByText(/selecione um nó ou aresta/i)).toBeVisible();
  });

  test("fila separa revisão comportamental e de qualidade", async () => {
    const user = userEvent.setup();
    const items = watchlistPayload.items as WatchlistItem[];
    render(<WatchlistTable items={items} />);
    expect(screen.getByRole("button", { name: "Revisão comportamental" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Revisão de qualidade dos dados" }));
    expect(screen.getAllByText(/revisão de qualidade dos dados/i).length).toBeGreaterThan(0);
    for (const item of items) expect(screen.queryByText(item.account_key)).not.toBeInTheDocument();
  });

  test("detalhe da fila explicita a fronteira de decisão humana", async () => {
    const user = userEvent.setup();
    const items = watchlistPayload.items as WatchlistItem[];
    render(<WatchlistTable items={items} />);
    await user.click(screen.getAllByRole("button", { name: "Ver evidência" })[0]);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Revisão humana obrigatória: Sim")).toBeVisible();
    expect(within(dialog).getByText("Intervenção automática: Não permitida")).toBeVisible();
    expect(within(dialog).queryByText(items[0].account_key)).not.toBeInTheDocument();
  });

  test("cards de experimento preservam o status não testado", () => {
    render(<ExperimentExplorer registry={experimentRegistry.experiments as Experiment[]} details={experimentDetails.experiments as Experiment[]} />);
    expect(screen.getAllByText("Não testado")).toHaveLength(8);
    expect(screen.getByText("Pronto para revisão")).toBeVisible();
    expect(formatStructuredLabel("STATUS_DESCONHECIDO")).toBe("STATUS_DESCONHECIDO");
  });

  test("detalhe do experimento expõe amostra e limite de execução", async () => {
    const user = userEvent.setup();
    render(<ExperimentExplorer registry={experimentRegistry.experiments as Experiment[]} details={experimentDetails.experiments as Experiment[]} />);
    await user.click(screen.getAllByRole("button", { name: /abrir detalhes do experimento/i })[0]);
    expect(screen.getByRole("dialog")).toHaveTextContent("Nenhum experimento foi executado");
    expect(screen.getByText("Atribuição simulada")).toBeVisible();
  });

  test("checklist de governança renderiza controles aprovados", () => {
    render(<GovernanceChecklist checks={[{ label: "Sem PII", passed: true }, { label: "Revisão humana", passed: true }]} />);
    expect(screen.getByText("Sem PII")).toBeVisible();
    expect(screen.getByText("Revisão humana")).toBeVisible();
  });

  test("demonstração guiada avança pela narrativa em português", async () => {
    const user = userEvent.setup();
    render(<GuidedDemo steps={demoSteps} duration="2–4" />);
    expect(screen.getByText("O problema")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /próxima/i }));
    expect(screen.getByText("Qualidade antes da interpretação")).toBeVisible();
  });
});
