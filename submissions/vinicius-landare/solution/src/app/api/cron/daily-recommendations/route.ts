import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { callLLM, extractJSON, CONTENT_MODELS } from "@/lib/openrouter";
import { CONTENT_DRAFT_SYSTEM, buildDraftUserMessage } from "@/lib/prompts/content-draft";
import { CONTENT_CRITIQUE_SYSTEM, buildCritiqueUserMessage } from "@/lib/prompts/content-critique";
import { CONTENT_REFINEMENT_SYSTEM, buildRefinementUserMessage } from "@/lib/prompts/content-refinement";
import { DraftResponseSchema, CritiqueResponseSchema, RefinementResponseSchema, type DraftResponse } from "@/lib/prompts/types";
import { addEntries, addToHistory, getHistorySummaryForPrompt, readCalendar, type CalendarEntry } from "@/lib/calendar-store";

const MAX_RETRIES = 3;

/**
 * Carrega insights do dataset para contextualizar as recomendações.
 */
function loadDatasetContext(): string {
  const dataDir = path.join(process.cwd(), "public", "data");
  const lines: string[] = ["DADOS DO DATASET (52.214 posts analisados):"];

  try {
    // Top combinações
    const top = JSON.parse(fs.readFileSync(path.join(dataDir, "h3_top20_combinations.json"), "utf-8"));
    const topData = (top.data || top).slice(0, 5);
    lines.push("\nMELHORES COMBINAÇÕES (plataforma × formato × categoria × idade):");
    for (const c of topData) {
      lines.push(`- ${c.platform} + ${c.content_type} + ${c.content_category} para ${c.audience_age_distribution}: ${c.avg_engagement_rate?.toFixed(2)}% engagement`);
    }

    // Bottom combinações
    const bottom = JSON.parse(fs.readFileSync(path.join(dataDir, "h3_bottom20_combinations.json"), "utf-8"));
    const bottomData = (bottom.data || bottom).slice(-3);
    lines.push("\nPIORES COMBINAÇÕES (evitar):");
    for (const c of bottomData) {
      lines.push(`- ${c.platform} + ${c.content_type} + ${c.content_category} para ${c.audience_age_distribution}: ${c.avg_engagement_rate?.toFixed(2)}%`);
    }

    // Temporal
    const dow = JSON.parse(fs.readFileSync(path.join(dataDir, "temporal_day_of_week.json"), "utf-8"));
    const dowData = (dow.data || dow).sort((a: Record<string, number>, b: Record<string, number>) => b.avg_engagement_rate - a.avg_engagement_rate);
    lines.push(`\nMELHORES DIAS: ${dowData.slice(0, 3).map((d: Record<string, unknown>) => d.day_of_week).join(", ")}`);

    const hour = JSON.parse(fs.readFileSync(path.join(dataDir, "temporal_hour.json"), "utf-8"));
    const hourData = (hour.data || hour).sort((a: Record<string, number>, b: Record<string, number>) => b.avg_engagement_rate - a.avg_engagement_rate);
    lines.push(`MELHORES HORÁRIOS: ${hourData.slice(0, 4).map((h: Record<string, unknown>) => `${h.hour}h`).join(", ")}`);

    // Hashtags
    const hashtags = JSON.parse(fs.readFileSync(path.join(dataDir, "top_hashtags.json"), "utf-8"));
    const hashData = (hashtags.data || hashtags).slice(0, 5);
    if (hashData.length > 0) {
      lines.push(`\nHASHTAGS COM MELHOR PERFORMANCE: ${hashData.map((h: Record<string, unknown>) => h.hashtag_list || h.hashtag).join(", ")}`);
    }

    // Patrocínio
    const sponsored = JSON.parse(fs.readFileSync(path.join(dataDir, "paid_traffic_summary.json"), "utf-8"));
    if (sponsored.kpis) {
      lines.push(`\nPATROCÍNIO: Lift geral ${sponsored.kpis.lift_geral_pp > 0 ? "+" : ""}${sponsored.kpis.lift_geral_pp?.toFixed(3)}%. ${sponsored.pct_roi_positive?.toFixed(0)}% das categorias com ROI positivo.`);
    }
  } catch {
    lines.push("\n(Alguns dados do dataset não puderam ser carregados)");
  }

  lines.push("\nIMPORTANTE: Baseie suas recomendações nestes dados. Cada conteúdo sugerido deve explicar QUAL dado do dataset justifica a escolha (ex: 'Baseado nos dados: vídeos de beauty para 19-25 no Instagram têm 20.08% de engagement').");

  return lines.join("\n");
}

/**
 * Carrega as top combinações do dataset para definir o mix semanal.
 */
function loadTopCombinations(): Array<{ platform: string; content_type: string; content_category: string; audience_age_distribution: string; avg_engagement_rate: number }> {
  try {
    const raw = fs.readFileSync(path.join(process.cwd(), "public", "data", "h3_top20_combinations.json"), "utf-8");
    const parsed = JSON.parse(raw);
    return parsed.data || parsed;
  } catch {
    return [
      { platform: "Instagram", content_type: "image", content_category: "beauty", audience_age_distribution: "19-25", avg_engagement_rate: 20 },
      { platform: "TikTok", content_type: "video", content_category: "lifestyle", audience_age_distribution: "19-25", avg_engagement_rate: 20 },
      { platform: "YouTube", content_type: "video", content_category: "tech", audience_age_distribution: "26-35", avg_engagement_rate: 20 },
    ];
  }
}

/**
 * Define o mix semanal baseado nas top performances do dataset.
 * Só gera para dias da semana atual que ainda não têm conteúdo agendado.
 */
function buildWeeklyMix(occupiedDates: Set<string>, targetMonday?: string) {
  const topCombos = loadTopCombinations();
  const peakHours = ["7:00", "11:00", "18:00", "21:00"];

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Usar a semana alvo enviada pelo frontend, ou calcular a semana atual
  let monday: Date;
  if (targetMonday) {
    monday = new Date(targetMonday + "T00:00:00");
  } else {
    const dayOfWeek = today.getDay();
    monday = new Date(today);
    monday.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
  }
  monday.setHours(0, 0, 0, 0);

  // Todos os dias da semana alvo >= hoje
  const allWeekDates: string[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    if (d >= today) allWeekDates.push(d.toISOString().split("T")[0]);
  }

  // Dias vazios (prioridade) e dias já preenchidos (podem acumular)
  const emptyDates = allWeekDates.filter((d) => !occupiedDates.has(d));
  const filledDates = allWeekDates.filter((d) => occupiedDates.has(d));

  // Ordem: primeiro os vazios (obrigatório preencher), depois os preenchidos (acumular)
  const targetDates = [...emptyDates, ...filledDates];

  const slots: Array<{
    platform: string;
    niche: string;
    audience: string;
    format: string;
    date: string;
    time: string;
    engagement: number;
    isAccumulating: boolean;
  }> = [];

  const usedPlatforms = new Set<string>();

  for (const combo of topCombos) {
    if (slots.length >= targetDates.length) break;
    if (usedPlatforms.size < 3 && usedPlatforms.has(combo.platform)) continue;
    usedPlatforms.add(combo.platform);

    const date = targetDates[slots.length];
    slots.push({
      platform: combo.platform,
      niche: combo.content_category,
      audience: combo.audience_age_distribution,
      format: combo.content_type,
      date,
      time: peakHours[slots.length % peakHours.length],
      engagement: combo.avg_engagement_rate,
      isAccumulating: occupiedDates.has(date),
    });
  }

  // Garantir ao menos 1 slot por dia vazio se topCombos foi insuficiente
  for (const date of emptyDates) {
    if (slots.some((s) => s.date === date)) continue;
    const combo = topCombos[slots.length % topCombos.length];
    slots.push({
      platform: combo.platform,
      niche: combo.content_category,
      audience: combo.audience_age_distribution,
      format: combo.content_type,
      date,
      time: peakHours[slots.length % peakHours.length],
      engagement: combo.avg_engagement_rate,
      isAccumulating: false,
    });
  }

  return {
    slots,
    emptyDates,
    filledDates,
    totalDaysInWeek: allWeekDates.length,
  };
}

export const maxDuration = 300; // 5 min timeout

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const targetMonday: string | undefined = body.targetMonday;

    // Dias já ocupados na semana alvo
    const calendar = readCalendar();
    const occupiedDates = new Set(
      (calendar.entries || [])
        .filter((e) => e.status === "pendente" || e.status === "aprovado")
        .map((e) => e.scheduled_date)
    );

    const { slots, emptyDates, filledDates, totalDaysInWeek } = buildWeeklyMix(occupiedDates, targetMonday);

    if (slots.length === 0) {
      return NextResponse.json({
        success: true,
        message: "Nenhum dia disponível para gerar conteúdo esta semana.",
        weekStatus: { occupied: occupiedDates.size, empty: 0, total: totalDaysInWeek, filled: 0, fullWeek: true },
        generated: 0,
      });
    }

    const historySummary = getHistorySummaryForPrompt();
    const datasetContext = loadDatasetContext();
    const allEntries: CalendarEntry[] = [];

    console.log(`[cron] Dias vazios: ${emptyDates.join(", ") || "nenhum"}`);
    console.log(`[cron] Dias preenchidos (acumular): ${filledDates.join(", ") || "nenhum"}`);
    console.log(`[cron] Iniciando geração para ${slots.length} slots...`);

    // Agrupar slots por plataforma/nicho para gerar em batch
    const grouped: Record<string, typeof slots> = {};
    for (const slot of slots) {
      const key = `${slot.platform}|${slot.niche}|${slot.audience}`;
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(slot);
    }

    const groupKeys = Object.keys(grouped);
    let groupIndex = 0;

    for (const [, groupSlots] of Object.entries(grouped)) {
      groupIndex++;
      const { platform, niche, audience, format } = groupSlots[0];
      console.log(`[cron] Grupo ${groupIndex}/${groupKeys.length}: ${platform}/${niche}/${audience}`);

      let approvedIdeas: DraftResponse["ideas"] = [];
      let lastDraftIdeas: DraftResponse["ideas"] = [];

      for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        const draftTemp = Math.min(0.9 + attempt * 0.05, 1.0);
        console.log(`[cron]   Draft tentativa ${attempt + 1}/${MAX_RETRIES}...`);

        const draftRes = await callLLM({
          system: CONTENT_DRAFT_SYSTEM + "\n\n" + datasetContext + "\n\n" + historySummary
            + (attempt > 0 ? `\n\nATENÇÃO: Tentativa ${attempt + 1}. Seja MAIS CRIATIVO e ORIGINAL.` : ""),
          user: buildDraftUserMessage({
            profile: "g4_social",
            platform,
            niche,
            audience_age: audience,
            avg_engagement: 19.9,
            top_posts: [
              `Post ${format} sobre ${niche} com alta interação (20.3%)`,
              `Carrossel de dicas de ${niche} (20.1%)`,
              `Reels tutorial de ${niche} (20.0%)`,
            ],
            worst_posts: [
              "Foto produto genérica (19.5%)",
              "Repost sem contexto (19.6%)",
              "Texto longo sem visual (19.7%)",
            ],
            peak_hours: groupSlots.map((s) => s.time.replace(":00", "h")),
          }),
          model: CONTENT_MODELS.draft,
          temperature: draftTemp,
          maxTokens: 2000,
        });

        let draft;
        try {
          draft = DraftResponseSchema.parse(extractJSON(draftRes));
        } catch (parseErr) {
          console.error(`[cron] Draft parse error na tentativa ${attempt + 1}:`, parseErr);
          continue; // Tentar novamente
        }
        lastDraftIdeas = draft.ideas;

        console.log(`[cron]   Draft OK. Critique...`);
        const critiqueRes = await callLLM({
          system: CONTENT_CRITIQUE_SYSTEM,
          user: buildCritiqueUserMessage({
            draft_output: draft,
            performance_data: `@g4_social | ${platform} | ${niche} | Público: ${audience} | Eng médio: 19.9% | Formato ideal: ${format}`,
          }),
          model: CONTENT_MODELS.critique,
          temperature: 0.2,
          maxTokens: 1500,
        });

        let critique;
        try {
          critique = CritiqueResponseSchema.parse(extractJSON(critiqueRes));
        } catch (parseErr) {
          console.error(`[cron] Critique parse error na tentativa ${attempt + 1}:`, parseErr);
          continue;
        }

        // Salvar reprovadas no histórico
        for (const ev of critique.evaluations) {
          if (ev.overall_score < 7 || ev.verdict !== "approved") {
            const idea = draft.ideas[ev.idea_index];
            if (idea) {
              addToHistory({
                id: `rejected-${Date.now()}-${ev.idea_index}`,
                generated_at: new Date().toISOString(),
                status: "pendente",
                scheduled_date: "", scheduled_time: "",
                platform, niche, audience,
                script: { title: idea.title, copy: "", visual_spec: "", hashtags: idea.hashtags, cta: idea.cta, thumbnail_description: "", publish_time: "" },
                scores: { originality: ev.scores.originality, feasibility: ev.scores.feasibility, alignment: ev.scores.alignment, overall: ev.overall_score },
                approved_by: null, approved_at: null,
              }, "nota_baixa");
            }
          }
        }

        const qualified = critique.evaluations.filter((e) => e.overall_score >= 7);
        approvedIdeas = qualified.map((e) => draft.ideas[e.idea_index]).filter(Boolean);

        if (approvedIdeas.length > 0) break;
      }

      // Se nenhuma passou, usar as melhores disponíveis
      if (approvedIdeas.length === 0) {
        approvedIdeas = lastDraftIdeas.slice(0, 2);
      }

      approvedIdeas = approvedIdeas.slice(0, groupSlots.length);

      // Refinement
      console.log(`[cron]   ${approvedIdeas.length} ideias aprovadas. Refinement...`);
      const refinementRes = await callLLM({
        system: CONTENT_REFINEMENT_SYSTEM,
        user: buildRefinementUserMessage({
          approved_ideas: approvedIdeas,
          profile_data: `@g4_social | ${platform} | ${niche} | ${audience} | Eng: 19.9% | Formato: ${format}`,
          hashtag_combos: [`#${niche}`, "#dicas", "#trending"],
        }),
        model: CONTENT_MODELS.refinement,
        temperature: 0.4,
        maxTokens: 2500,
      });

      const refinement = RefinementResponseSchema.parse(extractJSON(refinementRes));

      const now = new Date().toISOString();
      for (let i = 0; i < refinement.scripts.length && i < groupSlots.length; i++) {
        const script = refinement.scripts[i];
        const slot = groupSlots[i];

        allEntries.push({
          id: `${slot.date}-${slot.platform.slice(0,3).toLowerCase()}-${groupIndex}-${i + 1}-${Math.random().toString(36).slice(2, 7)}`,
          generated_at: now,
          status: "pendente",
          scheduled_date: slot.date,
          scheduled_time: slot.time,
          platform: slot.platform,
          niche: slot.niche,
          audience: slot.audience,
          script: {
            title: script.title,
            copy: script.copy,
            visual_spec: script.visual_spec,
            hashtags: script.hashtags,
            cta: script.cta,
            thumbnail_description: script.thumbnail_description,
            publish_time: script.publish_time,
          },
          scores: { originality: 0, feasibility: 0, alignment: 0, overall: 0 },
          approved_by: null,
          approved_at: null,
        });
      }
    }

    if (allEntries.length > 0) {
      addEntries(allEntries);
    }

    return NextResponse.json({
      success: true,
      generated: allEntries.length,
      weekStatus: {
        occupied: occupiedDates.size,
        empty: emptyDates.length,
        filled: allEntries.length,
        accumulated: slots.filter((s) => s.isAccumulating).length,
        total: totalDaysInWeek,
        fullWeek: emptyDates.length === 0,
      },
      mix: slots.map((s) => `${s.platform}/${s.niche}/${s.audience} (${s.engagement.toFixed(2)}%) → ${s.date} ${s.time}`),
      entries: allEntries.map((e) => ({ id: e.id, title: e.script.title, platform: e.platform, date: e.scheduled_date })),
    });
  } catch (err) {
    console.error("Cron daily-recommendations error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Falha ao gerar recomendações" },
      { status: 500 }
    );
  }
}
