"use client";

import { useState } from "react";
import { PlatformChart } from "./platform-chart";
import { CreatorTierChart } from "./creator-tier-chart";
import { TopCombinations } from "./top-combinations";
import { PersonaCards } from "./persona-cards";
import { TemporalAnalysis } from "./temporal-analysis";
import { MarketAnalysis } from "./market-analysis";

/* eslint-disable @typescript-eslint/no-explicit-any */

interface Props {
  platType: any[];
  tiers: any[];
  top: any[];
  bottom: any[];
  personas: any[];
  dow: any[];
  hour: any[];
  locEng: any[];
  brPlat: any[];
  brContent: any[];
  brAge: any[];
}

type Section = "plataforma" | "publico" | "timing" | "mercados";

export function EngagementDeepDive(props: Props) {
  const [openSection, setOpenSection] = useState<Section | null>("plataforma");

  function toggle(s: Section) {
    setOpenSection(openSection === s ? null : s);
  }

  return (
    <div className="space-y-3">
      {/* Plataforma & Formato */}
      <CollapsibleSection
        title="Plataforma e Formato"
        description="Qual plataforma e tipo de conteúdo gera mais engajamento"
        isOpen={openSection === "plataforma"}
        onToggle={() => toggle("plataforma")}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <PlatformChart data={props.platType} />
          <CreatorTierChart data={props.tiers} />
        </div>
        <TopCombinations topData={props.top} bottomData={props.bottom} />
      </CollapsibleSection>

      {/* Público-alvo */}
      <CollapsibleSection
        title="Público-alvo"
        description="Personas por faixa etária e suas preferencias"
        isOpen={openSection === "publico"}
        onToggle={() => toggle("publico")}
      >
        <PersonaCards personas={props.personas} />
      </CollapsibleSection>

      {/* Timing */}
      <CollapsibleSection
        title="Quando Postar"
        description="Melhores dias e horarios para publicar"
        isOpen={openSection === "timing"}
        onToggle={() => toggle("timing")}
      >
        <TemporalAnalysis dowData={props.dow} hourData={props.hour} />
      </CollapsibleSection>

      {/* Mercados */}
      <CollapsibleSection
        title="Mercados"
        description="Brasil vs mercados internacionais"
        isOpen={openSection === "mercados"}
        onToggle={() => toggle("mercados")}
      >
        <MarketAnalysis
          locationData={props.locEng}
          brazilPlatform={props.brPlat}
          brazilContentType={props.brContent}
          brazilAge={props.brAge}
        />
      </CollapsibleSection>
    </div>
  );
}

function CollapsibleSection({ title, description, isOpen, onToggle, children }: {
  title: string; description: string; isOpen: boolean; onToggle: () => void; children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-slate-50 transition-colors"
      >
        <div>
          <h3 className="text-sm font-semibold text-[#0F1B2D]">{title}</h3>
          <p className="text-xs text-slate-400 mt-0.5">{description}</p>
        </div>
        <span className={`text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`}>
          &#9662;
        </span>
      </button>
      {isOpen && (
        <div className="p-5 pt-0 space-y-4 border-t border-slate-100">
          {children}
        </div>
      )}
    </div>
  );
}
