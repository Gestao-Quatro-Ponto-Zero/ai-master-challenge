"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OverviewCards } from "@/components/dashboard/overview-cards";
import { AuthGate } from "@/components/dashboard/auth-gate";
import { ZAPIConfig } from "@/components/dashboard/zapi-config";
import { ExecutiveSummary } from "@/components/dashboard/executive-summary";
import { EngagementDeepDive } from "@/components/dashboard/engagement-deep-dive";
import { SponsorshipVerdict } from "@/components/dashboard/sponsorship-verdict";
import { ContentCalendar } from "@/components/dashboard/content-calendar";
import { InfluencerRanking } from "@/components/dashboard/influencer-ranking";
import { ProfileAnalysis } from "@/components/dashboard/profile-analysis";

/* eslint-disable @typescript-eslint/no-explicit-any */

export default function Dashboard() {
  const [data, setData] = useState<Record<string, any> | null>(null);
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
      fetch("/data/paid_traffic_summary.json").then(r => r.json()).catch(() => null),
      fetch("/data/campaign_roi.json").then(r => r.json()).catch(() => null),
      fetch("/data/budget_allocation.json").then(r => r.json()).catch(() => null),
      fetch("/data/influencer_ranking.json").then(r => r.json()).catch(() => null),
      fetch("/data/general_stats.json").then(r => r.json()).catch(() => null),
    ]).then(([
      summary, sponsored, tiers, top, bottom, dow, hour, platType, roi, locEng, brPlat, brContent, brAge,
      paidTrafficSummary, campaignRoi, budgetAllocation, influencerRanking, generalStats,
    ]) => {
      setData({
        summary, sponsored, tiers, top, bottom, dow, hour, platType, roi, locEng, brPlat, brContent, brAge,
        paidTrafficSummary, campaignRoi, budgetAllocation, influencerRanking, generalStats,
      });
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

  const extractData = (d: any) => d?.data || d;

  return (
    <div className="min-h-screen bg-[#F7F8FA]">
      {/* Header */}
      <header className="bg-gradient-to-r from-[#0F1B2D] to-[#1A2D47] text-white">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Image src="/logo-g4.png" alt="G4" width={120} height={66} className="h-10 w-auto" priority />
              <div className="h-8 w-px bg-white/20" />
              <div>
                <h1 className="text-lg font-semibold tracking-tight">G4 Strategy</h1>
                <p className="text-xs text-white/60">
                  {summary.total_posts.toLocaleString("pt-BR")} publicações analisadas
                </p>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-2">
              <ZAPIConfig />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        <OverviewCards summary={summary} />

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="bg-white border border-slate-200 shadow-sm p-1 rounded-xl flex w-full">
            <TabsTrigger value="overview" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs transition-colors flex-1">
              Visão Geral
            </TabsTrigger>
            <TabsTrigger value="engagement" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs transition-colors flex-1">
              Engajamento
            </TabsTrigger>
            <TabsTrigger value="sponsorship" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs transition-colors flex-1">
              Patrocínio
            </TabsTrigger>
            <TabsTrigger value="calendar" className="rounded-lg data-[state=active]:bg-[#E8734A] data-[state=active]:text-white text-xs transition-colors flex-1">
              Calendário
            </TabsTrigger>
            <TabsTrigger value="influencers" className="rounded-lg data-[state=active]:bg-[#0F1B2D] data-[state=active]:text-white text-xs transition-colors flex-1">
              Influenciadores
            </TabsTrigger>
            <TabsTrigger value="profile" className="rounded-lg data-[state=active]:bg-[#E8734A] data-[state=active]:text-white text-xs transition-colors flex-1">
              Análise de Perfil
            </TabsTrigger>
          </TabsList>

          {/* Tab 1: Visão Geral */}
          <TabsContent value="overview" className="space-y-4">
            <ExecutiveSummary
              stats={data.generalStats}
              topCombinations={extractData(data.top)}
              bottomCombinations={extractData(data.bottom)}
              sponsoredData={extractData(data.sponsored)}
              paidTrafficSummary={data.paidTrafficSummary}
              temporalDow={extractData(data.dow)}
              temporalHour={extractData(data.hour)}
            />
          </TabsContent>

          {/* Tab 2: Engajamento (merge de 4 tabs antigas) */}
          <TabsContent value="engagement" className="space-y-4">
            <EngagementDeepDive
              platType={extractData(data.platType)}
              tiers={extractData(data.tiers)}
              top={extractData(data.top)}
              bottom={extractData(data.bottom)}
              personas={summary.personas}
              dow={extractData(data.dow)}
              hour={extractData(data.hour)}
              locEng={extractData(data.locEng)}
              brPlat={extractData(data.brPlat)}
              brContent={extractData(data.brContent)}
              brAge={extractData(data.brAge)}
            />
          </TabsContent>

          {/* Tab 3: Patrocínio (merge) */}
          <TabsContent value="sponsorship" className="space-y-4">
            <SponsorshipVerdict
              generalData={extractData(data.sponsored)}
              roiData={extractData(data.roi)}
              paidTrafficSummary={data.paidTrafficSummary}
              campaignRoi={data.campaignRoi}
              budgetAllocation={data.budgetAllocation}
            />
          </TabsContent>

          {/* Tab 4: Calendário */}
          <TabsContent value="calendar" className="space-y-4">
            <ContentCalendar />
          </TabsContent>

          {/* Tab 5: Influenciadores */}
          <TabsContent value="influencers" className="space-y-4">
            {data.influencerRanking ? (
              <InfluencerRanking rankingData={data.influencerRanking} />
            ) : (
              <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center">
                <p className="text-xs text-slate-400">Execute python analysis/06_influencer_ranking.py para gerar o ranking</p>
              </div>
            )}
          </TabsContent>

          {/* Tab 6: Análise de Perfil */}
          <TabsContent value="profile" className="space-y-4">
            <ProfileAnalysis />
          </TabsContent>
        </Tabs>

        <footer className="text-center text-[11px] text-slate-400 py-6 border-t border-slate-200">
          G4 Strategy · Social Media
        </footer>
      </main>
    </div>
  );
}
