import { NextRequest, NextResponse } from "next/server";
import { callLLM, extractJSON, CONTENT_MODELS } from "@/lib/openrouter";
import { CONTENT_DRAFT_SYSTEM, buildDraftUserMessage } from "@/lib/prompts/content-draft";
import { CONTENT_CRITIQUE_SYSTEM, buildCritiqueUserMessage } from "@/lib/prompts/content-critique";
import { CONTENT_REFINEMENT_SYSTEM, buildRefinementUserMessage } from "@/lib/prompts/content-refinement";
import {
  DraftResponseSchema,
  CritiqueResponseSchema,
  RefinementResponseSchema,
  type DraftResponse,
  type CritiqueResponse,
  type RefinementResponse,
  type ContentDraftInput,
} from "@/lib/prompts/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      profile = "perfil_demo",
      platform = "Instagram",
      niche = "lifestyle",
      audience_age = "19-25",
      avg_engagement = 19.9,
      top_posts = ["Post sobre rotina matinal (20.3%)", "Carrossel de dicas (20.1%)", "Reels tutorial (20.0%)"],
      worst_posts = ["Foto produto genérica (19.5%)", "Story reposta (19.6%)", "Texto longo sem visual (19.7%)"],
      peak_hours = ["7h", "11h", "18h", "21h"],
      hashtag_combos = ["#skincare", "#rotina", "#dicas"],
    } = body;

    const draftInput: ContentDraftInput = {
      profile,
      platform,
      niche,
      audience_age,
      avg_engagement,
      top_posts,
      worst_posts,
      peak_hours,
    };

    // ===== STEP 1: DRAFT (Gemini 3 Flash) =====
    const draftResponse = await callLLM({
      system: CONTENT_DRAFT_SYSTEM,
      user: buildDraftUserMessage(draftInput),
      model: CONTENT_MODELS.draft,
      temperature: 0.9,
      maxTokens: 2000,
    });

    let draftResult: DraftResponse;
    try {
      const raw = extractJSON(draftResponse);
      draftResult = DraftResponseSchema.parse(raw);
    } catch {
      return NextResponse.json(
        { error: "Draft step failed validation", raw: draftResponse },
        { status: 500 }
      );
    }

    // ===== STEP 2: CRITIQUE (Claude Sonnet 4.5) =====
    const critiqueResponse = await callLLM({
      system: CONTENT_CRITIQUE_SYSTEM,
      user: buildCritiqueUserMessage({
        draft_output: draftResult,
        performance_data: `Perfil @${profile} | ${platform} | ${niche} | Público: ${audience_age} | Eng médio: ${avg_engagement}%`,
      }),
      model: CONTENT_MODELS.critique,
      temperature: 0.2,
      maxTokens: 1500,
    });

    let critiqueResult: CritiqueResponse;
    try {
      const raw = extractJSON(critiqueResponse);
      critiqueResult = CritiqueResponseSchema.parse(raw);
    } catch {
      return NextResponse.json(
        { error: "Critique step failed validation", draft: draftResult, raw: critiqueResponse },
        { status: 500 }
      );
    }

    // Filtrar ideias aprovadas
    const approvedIdeas = critiqueResult.top_picks.map((i) => draftResult.ideas[i]).filter(Boolean);

    if (approvedIdeas.length === 0) {
      return NextResponse.json({
        step: "critique",
        message: "Nenhuma ideia aprovada pela crítica. Tente novamente com parâmetros diferentes.",
        draft: draftResult,
        critique: critiqueResult,
      });
    }

    // ===== STEP 3: REFINEMENT (Gemini 3 Flash) =====
    const refinementResponse = await callLLM({
      system: CONTENT_REFINEMENT_SYSTEM,
      user: buildRefinementUserMessage({
        approved_ideas: approvedIdeas,
        profile_data: `@${profile} | ${platform} | ${niche} | ${audience_age} | Eng: ${avg_engagement}%`,
        hashtag_combos: hashtag_combos,
      }),
      model: CONTENT_MODELS.refinement,
      temperature: 0.4,
      maxTokens: 2500,
    });

    let refinementResult: RefinementResponse;
    try {
      const raw = extractJSON(refinementResponse);
      refinementResult = RefinementResponseSchema.parse(raw);
    } catch {
      return NextResponse.json(
        { error: "Refinement step failed validation", draft: draftResult, critique: critiqueResult, raw: refinementResponse },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      models_used: {
        draft: draftResponse._model_used,
        critique: critiqueResponse._model_used,
        refinement: refinementResponse._model_used,
      },
      draft: draftResult,
      critique: critiqueResult,
      scripts: refinementResult,
    });
  } catch (err) {
    console.error("Recommendations API error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Internal error" },
      { status: 500 }
    );
  }
}
