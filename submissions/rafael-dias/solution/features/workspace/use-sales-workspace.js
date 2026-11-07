"use client";

import { useEffect, useMemo, useState } from "react";
import { materialize, validateActivity } from "../../lib/workflow.mjs";
import { HEALTH_POLICY } from "../../lib/health.mjs";
import { ensureDailyPlan } from "../../lib/sales-guide.mjs";
import {
  createLocalWorkspaceRepository,
  WORKSPACE_KEY as STORE,
} from "../../lib/workspace-storage.mjs";
import { selectSellerWorkspace } from "../../lib/workspace-selectors.mjs";
export default function useSalesWorkspace(data) {
  const agents = useMemo(
    () =>
      [
        ...new Set([
          ...(data.historicalByAgent || []).map((d) => d.sales_agent),
          ...data.opportunities.map((d) => d.sales_agent),
        ]),
      ].sort(),
    [data],
  );
  const [agent, setAgent] = useState(agents[0]),
    [events, setEvents] = useState([]),
    [plans, setPlans] = useState({}),
    [ready, setReady] = useState(false),
    [error, setError] = useState(""),
    [collapsed, setCollapsed] = useState(false),
    [dark, setDark] = useState(false),
    [clock, setClock] = useState(null);
  useEffect(() => {
    function restore() {
      try {
        const saved = createLocalWorkspaceRepository(localStorage).load();
        if (saved) {
          setEvents(saved.events);
          if (agents.includes(saved.agent)) setAgent(saved.agent);
          setPlans(saved.plans);
        }
      } catch {
        setError(
          "Não foi possível ler as atividades salvas. Não serão sobrescritas; revise o armazenamento do navegador.",
        );
      }
    }
    restore();
    try {
      const prefs =
        createLocalWorkspaceRepository(localStorage).loadPreferences();
      setCollapsed(!!prefs.collapsed);
      setDark(!!prefs.dark);
    } catch {}
    setReady(true);
    setClock(new Date().toISOString());
    const timer = setInterval(() => setClock(new Date().toISOString()), 60000);
    const sync = (e) => {
      if (e.key === STORE) restore();
    };
    window.addEventListener("storage", sync);
    return () => {
      clearInterval(timer);
      window.removeEventListener("storage", sync);
    };
  }, [agents]);
  function setPreference(key, value) {
    const prefs = {
      collapsed,
      dark,
      [key]: value,
    };
    if (key === "collapsed") setCollapsed(value);
    else setDark(value);
    try {
      createLocalWorkspaceRepository(localStorage).savePreferences(prefs);
    } catch {}
  }
  function persist(next, nextAgent = agent, nextPlans = plans) {
    if (error) return false;
    try {
      createLocalWorkspaceRepository(localStorage).save({
        version: 2,
        agent: nextAgent,
        events: next,
        plans: nextPlans,
      });
      return true;
    } catch {
      setError(
        "O navegador não conseguiu salvar. Sua ação não foi concluída. Libere armazenamento e recarregue para tentar novamente.",
      );
      return false;
    }
  }
  function changeAgent(value) {
    setAgent(value);
    if (ready && !error) persist(events, value);
  }
  function record(deal, values) {
    if (!ready || error) return "O armazenamento não está disponível.";
    const issue = validateActivity(deal, values);
    if (issue) return issue;
    const e = {
      ...values,
      ...(values.dueAt
        ? {
            dueAt: new Date(values.dueAt).toISOString(),
          }
        : {}),
      occurredAt: values.occurredAt
        ? new Date(values.occurredAt).toISOString()
        : new Date().toISOString(),
      ...(values.pauseUntil
        ? { pauseUntil: new Date(values.pauseUntil).toISOString() }
        : {}),
      schemaVersion: 3,
      evidenceSource: "seller_declared",
      healthPolicyVersion: HEALTH_POLICY.version,
      recordedAt: new Date().toISOString(),
      id: crypto.randomUUID(),
      opportunityId: deal.opportunity_id,
      agent: deal.sales_agent,
      at: new Date().toISOString(),
    };
    const next = [...events, e];
    if (!persist(next)) return "Não foi possível salvar a atividade.";
    setEvents(next);
    setClock(e.at);
    return null;
  }
  const now = clock || new Date().toISOString();
  const all = useMemo(
    () =>
      data.opportunities.map((d) =>
        materialize(d, events, clock || new Date().toISOString()),
      ),
    [data, events, clock],
  );
  const {
    mine,
    open,
    agenda,
    due,
    planKey,
    progress,
    top,
    contactsToday,
    qualified,
  } = selectSellerWorkspace(all, agent, events, plans, now);
  useEffect(() => {
    if (!ready || !clock || error) return;
    const ensured = ensureDailyPlan(plans[planKey], mine, now, events);
    if (ensured === plans[planKey]) return;
    const nextPlans = {
      ...plans,
      [planKey]: ensured,
    };
    if (persist(events, agent, nextPlans)) setPlans(nextPlans);
  }, [ready, clock, error, planKey, plans, events, agent]);
  return {
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
    changeAgent,
    record,
  };
}
