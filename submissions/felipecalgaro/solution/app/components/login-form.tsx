"use client";

import { useMemo, useState } from "react";

import type { SalesAgentOption } from "@/utils/sales-team";

type LoginFormProps = {
  salesAgents: SalesAgentOption[];
  action: (formData: FormData) => Promise<void>;
};

export function LoginForm({ salesAgents, action }: LoginFormProps) {
  const [filterManager, setFilterManager] = useState("all");
  const [filterOffice, setFilterOffice] = useState("all");
  const [selectedAgent, setSelectedAgent] = useState("");

  const managers = useMemo(
    () => Array.from(new Set(salesAgents.map((a) => a.manager))).sort(),
    [salesAgents],
  );

  const offices = useMemo(
    () => Array.from(new Set(salesAgents.map((a) => a.regionalOffice))).sort(),
    [salesAgents],
  );

  const filteredAgents = useMemo(() => {
    return salesAgents.filter(
      (agent) =>
        (filterManager === "all" || agent.manager === filterManager) &&
        (filterOffice === "all" || agent.regionalOffice === filterOffice),
    );
  }, [salesAgents, filterManager, filterOffice]);

  function handleManagerChange(value: string) {
    setFilterManager(value);
    setSelectedAgent("");
  }

  function handleOfficeChange(value: string) {
    setFilterOffice(value);
    setSelectedAgent("");
  }

  return (
    <form action={action} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <label className="block space-y-1.5">
          <span className="text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
            Gestor
          </span>
          <select
            className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-900 outline-none transition focus:border-stone-950"
            onChange={(e) => handleManagerChange(e.target.value)}
            value={filterManager}
          >
            <option value="all">Todos os gestores</option>
            {managers.map((manager) => (
              <option key={manager} value={manager}>
                {manager}
              </option>
            ))}
          </select>
        </label>

        <label className="block space-y-1.5">
          <span className="text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
            Região
          </span>
          <select
            className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-900 outline-none transition focus:border-stone-950"
            onChange={(e) => handleOfficeChange(e.target.value)}
            value={filterOffice}
          >
            <option value="all">Todas as regiões</option>
            {offices.map((office) => (
              <option key={office} value={office}>
                {office}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="block space-y-1.5" htmlFor="salesAgent">
        <span className="text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
          Vendedor
        </span>
        <select
          className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2.5 text-sm text-stone-900 outline-none transition focus:border-stone-950"
          id="salesAgent"
          name="salesAgent"
          onChange={(e) => setSelectedAgent(e.target.value)}
          required
          value={selectedAgent}
        >
          <option disabled value="">
            {filteredAgents.length === 0
              ? "Nenhum vendedor encontrado"
              : "Escolha um vendedor"}
          </option>
          {filteredAgents.map((agent) => (
            <option key={agent.name} value={agent.name}>
              {agent.name}
            </option>
          ))}
        </select>
      </label>

      <button
        className="w-full rounded-2xl bg-stone-950 px-5 py-3 text-sm font-semibold text-stone-50 transition hover:bg-stone-800"
        type="submit"
      >
        Entrar
      </button>
    </form>
  );
}
