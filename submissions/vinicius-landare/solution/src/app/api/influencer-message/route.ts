import { NextRequest, NextResponse } from "next/server";
import { callLLM, extractJSON } from "@/lib/openrouter";
import { INFLUENCER_MESSAGE_SYSTEM, buildInfluencerUserMessage } from "@/lib/prompts/influencer-message";
import { InfluencerMessageSchema } from "@/lib/prompts/types";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      creator_name,
      score,
      action,
      avg_engagement,
      total_posts,
      trend = "estável",
      sponsorship_lift,
    } = body;

    if (!creator_name || score === undefined || !action) {
      return NextResponse.json(
        { error: "Missing required fields: creator_name, score, action" },
        { status: 400 }
      );
    }

    const response = await callLLM({
      system: INFLUENCER_MESSAGE_SYSTEM,
      user: buildInfluencerUserMessage({
        creator_name,
        score,
        action,
        avg_engagement: avg_engagement ?? 0,
        total_posts: total_posts ?? 0,
        trend,
        sponsorship_lift,
      }),
      temperature: 0.3,
      maxTokens: 800,
    });

    const raw = extractJSON(response);
    const result = InfluencerMessageSchema.parse(raw);

    return NextResponse.json({
      success: true,
      model_used: response._model_used,
      ...result,
    });
  } catch (err) {
    console.error("Influencer message API error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Internal error" },
      { status: 500 }
    );
  }
}
