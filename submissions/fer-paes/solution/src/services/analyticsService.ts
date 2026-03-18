import { supabase } from '../lib/supabaseClient';

export interface KnowledgeOverview {
  total_documents:       number;
  published_documents:   number;
  total_chunks:          number;
  embedded_chunks:       number;
  queries_processed:     number;
  avg_feedback_rating:   number | null;
  total_gaps:            number;
}

export interface DocumentUsageStat {
  document_id:       string;
  document_title:    string | null;
  document_status:   string | null;
  usage_count:       number;
  avg_relevance:     number;
}

export interface ChunkUsageStat {
  chunk_id:          string;
  document_id:       string | null;
  document_title:    string | null;
  section_title:     string | null;
  usage_count:       number;
  avg_relevance:     number;
}

export interface QueryAnalyticsStat {
  query_text:   string;
  frequency:    number;
  avg_score:    number;
  last_seen:    string;
}

export interface ResolutionImpact {
  total_feedbacks:      number;
  avg_rating:           number | null;
  ai_resolved:          number;
  partially_resolved:   number;
  escalated:            number;
  resolution_rate:      number;
  by_source:            Record<string, number>;
}

export async function getKnowledgeOverview(): Promise<KnowledgeOverview> {
  const { data, error } = await supabase.rpc('get_knowledge_overview');
  if (error) throw new Error(error.message);
  return data as KnowledgeOverview;
}

export async function getDocumentUsageStats(limit = 10): Promise<DocumentUsageStat[]> {
  const { data, error } = await supabase.rpc('get_document_usage_stats', { p_limit: limit });
  if (error) throw new Error(error.message);
  return (data ?? []) as DocumentUsageStat[];
}

export async function getChunkUsageStats(limit = 10): Promise<ChunkUsageStat[]> {
  const { data, error } = await supabase.rpc('get_chunk_usage_stats', { p_limit: limit });
  if (error) throw new Error(error.message);
  return (data ?? []) as ChunkUsageStat[];
}

export async function getQueryAnalytics(limit = 15): Promise<QueryAnalyticsStat[]> {
  const { data, error } = await supabase.rpc('get_query_analytics', { p_limit: limit });
  if (error) throw new Error(error.message);
  return (data ?? []) as QueryAnalyticsStat[];
}

export async function getResolutionImpact(): Promise<ResolutionImpact> {
  const { data, error } = await supabase.rpc('get_resolution_impact');
  if (error) throw new Error(error.message);
  return data as ResolutionImpact;
}
