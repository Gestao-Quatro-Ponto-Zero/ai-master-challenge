import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("next/dynamic", () => ({
  default: () => function MockGraph(props: unknown) {
    const { onSelect } = props as { onSelect: (id: string) => void };
    return <button onClick={() => onSelect("eventtype_churn")}>Mock graph node</button>;
  }
}));

import { AppShell } from "@/components/AppShell";
import { EmptyState, ErrorState, GovernanceChecklist, MetricCard } from "@/components/ui";
import { JourneyExplorer } from "@/components/JourneyExplorer";
import { GraphExplorer } from "@/components/GraphExplorer";
import { WatchlistTable } from "@/components/WatchlistExplorer";
import { ExperimentExplorer } from "@/components/ExperimentExplorer";
import { GuidedDemo } from "@/components/GuidedDemo";
import journeyPayload from "@/public/data/journey_samples.json";
import graphNodes from "@/public/data/graph_nodes.json";
import graphEdges from "@/public/data/graph_edges.json";
import watchlistPayload from "@/public/data/watchlist_items_demo.json";
import experimentRegistry from "@/public/data/experiment_registry.json";
import experimentDetails from "@/public/data/experiment_details.json";
import demoStory from "@/public/data/demo_story.json";
import type { Experiment, JourneySample, WatchlistItem } from "@/lib/types";

describe("dashboard experience", () => {
  beforeEach(() => vi.clearAllMocks());

  test("overview metric card renders value with context", () => {
    render(<MetricCard metric={{ label: "Journeys", value: 4221, context: "Across governed scopes" }} />);
    expect(screen.getByText("4,221")).toBeVisible();
    expect(screen.getByText("Across governed scopes")).toBeVisible();
  });

  test("primary navigation exposes all seven areas and guided demo", () => {
    render(<AppShell><p>Content</p></AppShell>);
    expect(screen.getByRole("navigation")).toBeVisible();
    expect(screen.getByRole("link", { name: "Data & Quality" })).toHaveAttribute("href", "/quality");
    expect(screen.getByRole("link", { name: "JourneyGraph" })).toHaveAttribute("href", "/graph");
    expect(screen.getAllByRole("link", { name: /guided demo/i }).length).toBeGreaterThan(0);
  });

  test("responsive menu can open and close", async () => {
    const user = userEvent.setup();
    render(<AppShell><p>Content</p></AppShell>);
    await user.click(screen.getByRole("button", { name: "Open navigation" }));
    expect(screen.getByRole("button", { name: "Close navigation" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Close navigation" }));
  });

  test("empty and error states are readable", () => {
    const { rerender } = render(<EmptyState title="No data" message="Nothing matches." />);
    expect(screen.getByRole("status")).toHaveTextContent("Nothing matches");
    rerender(<ErrorState title="Unavailable" message="Local artifact missing." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Local artifact missing");
  });

  test("journey explorer selects anonymous accounts", async () => {
    const user = userEvent.setup();
    const samples = journeyPayload.samples as JourneySample[];
    render(<JourneyExplorer samples={samples} />);
    expect(screen.getByText(samples[0].account_key)).toBeVisible();
    await user.selectOptions(screen.getByLabelText("Anonymous account"), samples[1].account_key);
    expect(screen.getByText(samples[1].account_key)).toBeVisible();
    expect(screen.queryByText(/A-[0-9a-f]/i)).not.toBeInTheDocument();
  });

  test("journey filters expose an empty state and recover", async () => {
    const user = userEvent.setup();
    render(<JourneyExplorer samples={journeyPayload.samples as JourneySample[]} />);
    await user.selectOptions(screen.getByLabelText("Observed outcome"), "RECURRING_CHURN");
    await user.selectOptions(screen.getByLabelText("Journey taxonomy"), "HIGH_VALUE_LOW_USAGE");
    expect(screen.getByText("No journey matches these filters.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Reset filters" }));
    expect(screen.getByLabelText("Anonymous account")).toBeVisible();
  });

  test("graph filters and selected node detail work", async () => {
    const user = userEvent.setup();
    render(<GraphExplorer nodeData={graphNodes as never} edgeData={graphEdges as never} />);
    expect(screen.getByText(/explicitly truncated/i)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Mock graph node" }));
    expect(screen.getByRole("heading", { name: "CHURN" })).toBeVisible();
    await user.selectOptions(screen.getByLabelText("Graph mode"), "pattern-explorer");
    expect(screen.getByText(/select a node or edge/i)).toBeVisible();
  });

  test("watchlist separates behavioral and quality review", async () => {
    const user = userEvent.setup();
    render(<WatchlistTable items={watchlistPayload.items as WatchlistItem[]} />);
    expect(screen.getByRole("button", { name: "Behavioral watchlist" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Data quality review" }));
    expect(screen.getAllByText(/data quality review/i).length).toBeGreaterThan(0);
  });

  test("watchlist drawer states the human decision boundary", async () => {
    const user = userEvent.setup();
    render(<WatchlistTable items={watchlistPayload.items as WatchlistItem[]} />);
    await user.click(screen.getAllByRole("button", { name: "View evidence" })[0]);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Requires human review: Yes")).toBeVisible();
    expect(within(dialog).getByText("Automatic intervention: Not allowed")).toBeVisible();
  });

  test("experiment cards retain untested status", () => {
    render(<ExperimentExplorer registry={experimentRegistry.experiments as Experiment[]} details={experimentDetails.experiments as Experiment[]} />);
    expect(screen.getAllByText("Untested")).toHaveLength(8);
    expect(screen.getByText("Ready For Review")).toBeVisible();
  });

  test("experiment detail exposes sample and execution boundary", async () => {
    const user = userEvent.setup();
    render(<ExperimentExplorer registry={experimentRegistry.experiments as Experiment[]} details={experimentDetails.experiments as Experiment[]} />);
    await user.click(screen.getAllByRole("button", { name: /open experiment detail/i })[0]);
    expect(screen.getByRole("dialog")).toHaveTextContent("No experiment has been executed");
    expect(screen.getByText("Simulated assignment")).toBeVisible();
  });

  test("governance checklist renders passed controls", () => {
    render(<GovernanceChecklist checks={[{ label: "No PII", passed: true }, { label: "Human review", passed: true }]} />);
    expect(screen.getByText("No PII")).toBeVisible();
    expect(screen.getByText("Human review")).toBeVisible();
  });

  test("guided demo advances through narrative steps", async () => {
    const user = userEvent.setup();
    render(<GuidedDemo steps={demoStory.steps} duration={demoStory.duration_minutes} />);
    expect(screen.getByText("The problem")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText("Data quality before prediction")).toBeVisible();
  });
});
