import { z } from "zod";

// ============================================================
// Schemas de validação para outputs da LLM
// ============================================================

export const ContentIdeaSchema = z.object({
  title: z.string(),
  hook: z.string(),
  format: z.string(),
  cta: z.string(),
  hashtags: z.array(z.string()).max(5),
  best_time: z.string(),
  expected_engagement: z.string(),
});

export const DraftResponseSchema = z.object({
  ideas: z.array(ContentIdeaSchema).min(1).max(5),
});

export const EvaluationSchema = z.object({
  idea_index: z.number(),
  scores: z.object({
    originality: z.number().min(1).max(10),
    feasibility: z.number().min(1).max(10),
    alignment: z.number().min(1).max(10),
    risk: z.number().min(1).max(10),
  }),
  overall_score: z.number(),
  verdict: z.enum(["approved", "needs_revision", "rejected"]),
  justification: z.string(),
});

export const CritiqueResponseSchema = z.object({
  evaluations: z.array(EvaluationSchema).min(1),
  top_picks: z.array(z.number()),
});

export const ScriptSchema = z.object({
  title: z.string(),
  copy: z.string(),
  visual_spec: z.string(),
  hashtags: z.array(z.string()).max(5),
  publish_time: z.string(),
  cta: z.string(),
  thumbnail_description: z.string(),
});

export const RefinementResponseSchema = z.object({
  scripts: z.array(ScriptSchema).min(1),
});

export const InfluencerMessageSchema = z.object({
  message: z.string().max(500),
  tone: z.string(),
  key_points: z.array(z.string()),
});

// ============================================================
// Types derivados dos schemas
// ============================================================

export type ContentIdea = z.infer<typeof ContentIdeaSchema>;
export type DraftResponse = z.infer<typeof DraftResponseSchema>;
export type Evaluation = z.infer<typeof EvaluationSchema>;
export type CritiqueResponse = z.infer<typeof CritiqueResponseSchema>;
export type Script = z.infer<typeof ScriptSchema>;
export type RefinementResponse = z.infer<typeof RefinementResponseSchema>;
export type InfluencerMessage = z.infer<typeof InfluencerMessageSchema>;

// ============================================================
// Input types para os prompts
// ============================================================

export interface ContentDraftInput {
  profile: string;
  platform: string;
  niche: string;
  audience_age: string;
  avg_engagement: number;
  top_posts: string[];
  worst_posts: string[];
  peak_hours: string[];
}

export interface ContentCritiqueInput {
  draft_output: DraftResponse;
  performance_data: string;
}

export interface ContentRefinementInput {
  approved_ideas: ContentIdea[];
  profile_data: string;
  hashtag_combos: string[];
}

export interface InfluencerMessageInput {
  creator_name: string;
  score: number;
  action: "incentivar" | "manter" | "alinhar" | "reavaliar";
  avg_engagement: number;
  total_posts: number;
  trend: string;
  sponsorship_lift?: number;
}
