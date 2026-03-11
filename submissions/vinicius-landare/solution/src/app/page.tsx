"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OverviewCards } from "@/components/dashboard/overview-cards";
import { PlatformChart } from "@/components/dashboard/platform-chart";
import { SponsorshipAnalysis } from "@/components/dashboard/sponsorship-analysis";
import { PersonaCards } from "@/components/dashboard/persona-cards";
import { CreatorTierChart } from "@/components/dashboard/creator-tier-chart";
import { TopCombinations } from "@/components/dashboard/top-combinations";
import { TemporalAnalysis } from "@/components/dashboard/temporal-analysis";
import { Recommendations } from "@/components/dashboard/recommendations";
import { MarketAnalysis } from "@/components/dashboard/market-analysis";
import { AuthGate } from "@/components/dashboard/auth-gate";

export default function Dashboard() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && sessionStorage.getItem("sm_auth") === "1") {
      setAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (!authenticated) return;
    Promise.all([
      fetch("/data/dashboard_summary.json").then(r => r.json()),
      fetch("/data/h1_sponsored_vs_organic.json").then(r => r.json()),
      fetch("/data/h2_creator_tiers.json").then(r => r.json()),
      fetch("/data/h3_top20_combinations.json").then(r => r.json()),
      fetch("/data/h3_bottom20_combinations.json").then(r => r.json()),
      fetch("/data/temporal_day_of_week.json").then(r => r.json()),
      fetch("/data/temporal_hour.json").then(r => r.json()),
      fetch("/data/h3_platform_content_type.json").then(r => r.json()),
      fetch("/data/sponsorship_roi.json").then(r => r.json()),
      fetch("/data/h4_location_engagement.json").then(r => r.json()),
      fetch("/data/h4_brazil_platform.json").then(r => r.json()),
      fetch("/data/h4_brazil_content_type.json").then(r => r.json()),
      fetch("/data/h4_brazil_age.json").then(r => r.json()),
    ]).then(([summary, sponsored, tiers, top, bottom, dow, hour, platType, roi, locEng, brPlat, brContent, brAge]) => {
      setData({ summary, sponsored, tiers, top, bottom, dow, hour, platType, roi, locEng, brPlat, brContent, brAge });
    });
  }, [authenticated]);

  if (!authenticated) {
    return <AuthGate onAuth={() => setAuthenticated(true)} />;
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#F7F8FA]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-[#E8734A] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-500 text-sm">Carregando painel...</p>
        </div>
      </div>
    );
  }

  const summary = data.summary as {
    total_posts: number; total_creators: number; avg_engagement_rate: number;
    platforms: string[]; date_range: { start: string; end: string };
    sponsored_pct: number; personas: Record<string, unknown>[];
  };

  return (
    <div className="min-h-screen bg-[#F7F8FA]">
      {/* Header G4 style — navy gradient */}
      <header className="bg-gradient-to-r from-[#0F1B2D] to-[#1A2D47] text-white">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Image src="/logo-g4.png" alt="G4" width={120} height={66} className="h-10 w-auto" priority />
              <div className="h-8 w-px bg-white/20" />
              <div>
                <h1 className="text-lg font-semibold tracking-tight">Social Metrics</h1>
                <p className="text-xs text-white/60">
                  {summary.total_posts.toLocaleString("pt-BR")} publicações · {summary.total_creators.toLocaleString("pt-BR")} criadores
                </p>
              </div>
            </div>
            <div className="hidden md:flex gap-2">
              {summary.platforms.map((p: string) => (
                <span key={p} className="px-3 py-1 bg-white/10 text-white/80 rounded-full text-xs font-medium backdrop-blur-sm border border-white/10">
                  {p}
                </span>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        <OverviewCards summary={summary} />

        <Tabs defaultValue="performance" className="space-y-4">
          <TabsList className="bg-white border border-slate-200 shadow-sm p-1 rounded-xl grid w-full grid-cols-6">
            <TabsTrigger value="performance" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs sm:text-sm transition-colors">
              Desempenho
            </TabsTrigger>
            <TabsTrigger value="sponsorship" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs sm:text-sm transition-colors">
              Patrocínio
            </TabsTrigger>
            <TabsTrigger value="personas" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs sm:text-sm transition-colors">
              Público-alvo
            </TabsTrigger>
            <TabsTrigger value="markets" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs sm:text-sm transition-colors">
              Mercados
            </TabsTrigger>
            <TabsTrigger value="temporal" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs sm:text-sm transition-colors">
              Quando Postar
            </TabsTrigger>
            <TabsTrigger value="recommendations" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs sm:text-sm transition-colors">
              Plano de Ação
            </TabsTrigger>
          </TabsList>

          <TabsContent value="performance" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <PlatformChart data={data.platType as Record<string, unknown>[]} />
              <CreatorTierChart data={data.tiers as Record<string, unknown>[]} />
            </div>
            <TopCombinations topData={data.top as Record<string, unknown>[]} bottomData={data.bottom as Record<string, unknown>[]} />
          </TabsContent>

          <TabsContent value="sponsorship" className="space-y-4">
            <SponsorshipAnalysis
              generalData={data.sponsored as Record<string, unknown>[]}
              roiData={data.roi as Record<string, unknown>[]}
            />
          </TabsContent>

          <TabsContent value="personas" className="space-y-4">
            <PersonaCards personas={summary.personas} />
          </TabsContent>

          <TabsContent value="markets" className="space-y-4">
            <MarketAnalysis
              locationData={data.locEng as Record<string, unknown>[]}
              brazilPlatform={data.brPlat as Record<string, unknown>[]}
              brazilContentType={data.brContent as Record<string, unknown>[]}
              brazilAge={data.brAge as Record<string, unknown>[]}
            />
          </TabsContent>

          <TabsContent value="temporal" className="space-y-4">
            <TemporalAnalysis dowData={data.dow as Record<string, unknown>[]} hourData={data.hour as Record<string, unknown>[]} />
          </TabsContent>

          <TabsContent value="recommendations" className="space-y-4">
            <Recommendations personas={summary.personas} />
          </TabsContent>
        </Tabs>

        <footer className="text-center text-[11px] text-slate-400 py-6 border-t border-slate-200">
          Challenge 004 — Estratégia Social Media · Análise de {summary.total_posts.toLocaleString("pt-BR")} publicações
        </footer>
      </main>
    </div>
  );
}
