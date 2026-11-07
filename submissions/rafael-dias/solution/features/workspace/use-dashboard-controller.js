"use client";

import { useEffect, useState } from "react";
import { isClosed } from "../../lib/workflow.mjs";
import { moveIntent } from "../../lib/presentation.mjs";
import { eventNames } from "../../lib/activity.mjs";
import { selectResultsScope } from "../../lib/workspace-selectors.mjs";
import useSalesWorkspace from "./use-sales-workspace";
export default function useDashboardController(data) {
  const workspace = useSalesWorkspace(data);
  const {
    agents,
    agent,
    events,
    ready,
    error,
    collapsed,
    dark,
    clock,
    now,
    all,
    mine,
    open,
    agenda,
    due,
    progress,
    top,
    contactsToday,
    qualified,
    setPreference,
  } = workspace;
  const [view, setView] = useState("today"),
    [toast, setToast] = useState(""),
    [selected, setSelected] = useState(null),
    [moveAction, setMoveAction] = useState(null),
    [dragged, setDragged] = useState(null),
    [dropTarget, setDropTarget] = useState(null),
    [query, setQuery] = useState(""),
    [queue, setQueue] = useState("focus"),
    [scope, setScope] = useState("mine"),
    [manager, setManager] = useState(""),
    [region, setRegion] = useState(""),
    [limit, setLimit] = useState(20);
  function changeAgent(value) {
    workspace.changeAgent(value);
    setSelected(null);
    setLimit(20);
  }
  function record(deal, values) {
    const issue = workspace.record(deal, values);
    if (issue) return issue;
    setToast(
      `${eventNames[values.type]}. ${values.dueAt ? "Próximo passo agendado." : "Carteira atualizada."}`,
    );
    return null;
  }
  function openDeal(id) {
    setMoveAction(null);
    setSelected(id);
  }
  function handleDrop(e, target) {
    e.preventDefault();
    const id = e.dataTransfer.getData("text/plain") || dragged;
    setDragged(null);
    setDropTarget(null);
    const deal = mine.find((d) => d.opportunity_id === id);
    if (!deal) return;
    const intent = moveIntent(deal, target);
    if (intent.error) {
      setToast(intent.error);
      return;
    }
    if (intent.noop) return;
    setMoveAction(intent.action);
    setSelected(id);
    setToast("Confirme o resultado para concluir a mudança de etapa.");
  }
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 5000);
    return () => clearTimeout(t);
  }, [toast]);
  const openCounts = Object.fromEntries(
    agents.map((a) => [
      a,
      all.filter((d) => d.sales_agent === a && !isClosed(d)).length,
    ]),
  );
  const detail = all.find((d) => d.opportunity_id === selected);
  const scoped = selectResultsScope(all, {
    scope,
    agent,
    manager,
    region,
  });
  const titles = {
    today: "Meu dia",
    pipeline: "Meu pipeline",
    results: "Resultados",
    method: "Entenda suas prioridades",
  };
  function showDailyProgress() {
    setView("today");
    requestAnimationFrame(() =>
      document.getElementById("daily-checkpoints")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      }),
    );
  }
  function exportActivities() {
    const blob = new Blob(
        [
          JSON.stringify(
            {
              exportedAt: now,
              referenceDate: data.asOf,
              events,
            },
            null,
            2,
          ),
        ],
        {
          type: "application/json",
        },
      ),
      a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "g4-sales-priority-atividades.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  return {
    agents,
    agent,
    view,
    events,
    ready,
    error,
    toast,
    selected,
    moveAction,
    dropTarget,
    collapsed,
    dark,
    query,
    queue,
    scope,
    manager,
    region,
    limit,
    clock,
    now,
    all,
    mine,
    open,
    agenda,
    due,
    progress,
    top,
    openCounts,
    contactsToday,
    qualified,
    detail,
    scoped,
    titles,
    setView,
    setLimit,
    setQuery,
    setQueue,
    setScope,
    setManager,
    setRegion,
    setDragged,
    setDropTarget,
    setSelected,
    setMoveAction,
    setPreference,
    openDeal,
    handleDrop,
    changeAgent,
    record,
    showDailyProgress,
    exportActivities,
  };
}
