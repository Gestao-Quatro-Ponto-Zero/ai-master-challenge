"use client";

import { MotionConfig } from "motion/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { PipelineData } from "@/lib/data";
import { decisionWindow } from "@/lib/scoring";
import { agentOptions, EMPTY_SELECTION, teamRows, type Selection } from "@/lib/selection";
import { useLastAgent, useMarks } from "@/lib/useMarks";
import { Entry } from "./Entry";
import { HowItWorks } from "./HowItWorks";
import { TeamView } from "./TeamView";
import { WorkView } from "./WorkView";
import { Brand } from "./ui";

type Screen = "entrada" | "fila" | "time" | "como";

/**
 * Três telas, uma por papel: entrada ("quem está abrindo?"), fila do vendedor e visão do time.
 * "Como o score funciona" abre por cima e volta para a tela de onde veio.
 */
export function Dashboard({ data }: { data: PipelineData }) {
  const [sel, setSel] = useState<Selection>(EMPTY_SELECTION);
  const [teamMode, setTeamMode] = useState(false);
  const [showHow, setShowHow] = useState(false);
  const { marks, setMark } = useMarks();
  const { agent: remembered, remember, forget } = useLastAgent();
  // Depois de "Trocar" ou "Time" a fila lembrada não reabre sozinha nesta sessão.
  const [away, setAway] = useState(false);
  const interacted = useRef(false);

  const win = useMemo(() => decisionWindow(data.decideCurve), [data.decideCurve]);
  const rows = useMemo(() => teamRows(data.deals, data.agents), [data.deals, data.agents]);

  // Quem abriu antes volta direto para a fila dele (o nome vem do localStorage, então só depois da hidratação).
  const restorable = remembered && data.agents.some((a) => a.name === remembered) ? remembered : "";
  const activeAgent = sel.agent || (!away && !teamMode ? restorable : "");
  const screen: Screen = showHow ? "como" : activeAgent ? "fila" : teamMode ? "time" : "entrada";

  // Ao trocar de tela, o foco vai para o título dela (leitor de tela e teclado), menos na carga que reabre a fila lembrada.
  const lastScreen = useRef<Screen>(screen);
  useEffect(() => {
    if (lastScreen.current === screen) return;
    lastScreen.current = screen;
    if (!interacted.current) return;
    document.getElementById("tela-titulo")?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [screen]);

  const update = useCallback(
    (next: Partial<Selection>) => {
      setSel((s) => {
        const merged = { ...s, ...next };
        // Mantém a cascata coerente: trocar região/manager limpa o que deixou de caber.
        if ("region" in next && merged.manager && !data.agents.some((a) => a.manager === merged.manager && (!merged.region || a.region === merged.region))) merged.manager = "";
        if (merged.agent && !agentOptions(data.agents, { ...merged, agent: "" }).some((a) => a.name === merged.agent)) merged.agent = "";
        if (next.agent) {
          const a = data.agents.find((x) => x.name === next.agent);
          if (a) Object.assign(merged, { region: a.region, manager: a.manager });
        }
        return merged;
      });
    },
    [data.agents],
  );

  const pickAgent = (agent: string) => {
    interacted.current = true;
    remember(agent);
    setAway(false);
    setTeamMode(false);
    update({ agent });
  };
  // "Trocar": esquece o vendedor deste navegador (máquina compartilhada) e volta à entrada.
  const goHome = () => {
    interacted.current = true;
    forget();
    setAway(true);
    setTeamMode(false);
    setSel(EMPTY_SELECTION);
  };
  const goTeam = () => {
    interacted.current = true;
    setAway(true);
    setTeamMode(true);
    setSel(EMPTY_SELECTION);
  };
  const openHow = () => {
    interacted.current = true;
    setShowHow(true);
  };

  return (
    <MotionConfig reducedMotion="user">
      {screen === "como" ? (
        <div className="mx-auto max-w-5xl px-4 pb-20 pt-6 sm:px-6 sm:pt-8">
          <header className="flex items-center justify-between gap-3">
            <Brand />
            <button type="button" onClick={() => setShowHow(false)} className="min-h-11 text-sm font-semibold text-fg-2 underline-offset-4 hover:text-gold-hi hover:underline">
              ← Voltar
            </button>
          </header>
          <h1 id="tela-titulo" tabIndex={-1} className="mb-6 mt-8 text-4xl font-extrabold tracking-tight outline-none">
            Como o score funciona
          </h1>
          <HowItWorks curve={data.decideCurve} maxCycle={data.maxCycleDays} globalWinRate={data.globalWinRate} />
        </div>
      ) : screen === "fila" ? (
        <WorkView
          key={activeAgent}
          data={data}
          agent={activeAgent}
          win={win}
          marks={marks}
          setMark={setMark}
          onChangeAgent={goHome}
          onTeam={goTeam}
          onHow={openHow}
        />
      ) : screen === "time" ? (
        <TeamView data={data} sel={sel} update={update} onPickAgent={pickAgent} onHome={goHome} onHow={openHow} />
      ) : (
        <Entry rows={rows} today={data.today} onPick={pickAgent} onTeam={goTeam} onHow={openHow} />
      )}
    </MotionConfig>
  );
}
