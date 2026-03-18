import { supabase } from '../lib/supabaseClient';

export interface ChunkUsageRecord {
  chunk_id?:        string | null;
  document_id?:     string | null;
  agent_run_id?:    string | null;
  ticket_id?:       string | null;
  conversation_id?: string | null;
  query_text?:      string;
  relevance_score?: number;
}

export interface FeedbackRecord {
  ticket_id?:        string | null;
  conversation_id?:  string | null;
  agent_run_id?:     string | null;
  agent_id?:         string | null;
  rating:            number;
  feedback_text?:    string;
  feedback_source?:  'operator' | 'customer' | 'admin';
}

export interface KnowledgeFeedback {
  id:               string;
  ticket_id:        string | null;
  conversation_id:  string | null;
  agent_run_id:     string | null;
  agent_id:         string | null;
  rating:           number;
  feedback_text:    string;
  feedback_source:  string;
  created_by:       string | null;
  created_at:       string;
}

export interface KnowledgeGap {
  id:         string;
  query:      string;
  frequency:  number;
  last_seen:  string;
  created_at: string;
}

export interface FeedbackStats {
  total:             number;
  avg_rating:        number | null;
  positive:          number;
  neutral:           number;
  negative:          number;
  total_gaps:        number;
  total_chunk_uses:  number;
}

export interface ChunkUsageStat {
  chunk_id:       string;
  document_id:    string | null;
  use_count:      number;
  avg_score:      number;
  document_title?: string;
}

export async function logChunkUsage(records: ChunkUsageRecord[]): Promise<void> {
  if (!records.length) return;
  const { error } = await supabase
    .from('knowledge_chunk_usage')
    .insert(records.map((r) => ({
      chunk_id:        r.chunk_id        ?? null,
      document_id:     r.document_id     ?? null,
      agent_run_id:    r.agent_run_id    ?? null,
      ticket_id:       r.ticket_id       ?? null,
      conversation_id: r.conversation_id ?? null,
      query_text:      r.query_text      ?? '',
      relevance_score: r.relevance_score ?? 0,
    })));
  if (error) throw new Error(error.message);
}

export async function collectFeedback(record: FeedbackRecord): Promise<KnowledgeFeedback> {
  const { data: sessionData } = await supabase.auth.getSession();
  const userId = sessionData?.session?.user?.id ?? null;

  const { data, error } = await supabase
    .from('knowledge_feedback')
    .insert({
      ticket_id:       record.ticket_id       ?? null,
      conversation_id: record.conversation_id ?? null,
      agent_run_id:    record.agent_run_id    ?? null,
      agent_id:        record.agent_id        ?? null,
      rating:          record.rating,
      feedback_text:   record.feedback_text   ?? '',
      feedback_source: record.feedback_source ?? 'operator',
      created_by:      userId,
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data as KnowledgeFeedback;
}

export async function registerKnowledgeGap(query: string): Promise<void> {
  const { error } = await supabase.rpc('upsert_knowledge_gap', { p_query: query });
  if (error) throw new Error(error.message);
}

export async function getFeedbackStats(): Promise<FeedbackStats> {
  const { data, error } = await supabase.rpc('get_feedback_stats');
  if (error) throw new Error(error.message);
  return data as FeedbackStats;
}

export async function getKnowledgeGaps(limit = 20): Promise<KnowledgeGap[]> {
  const { data, error } = await supabase
    .from('knowledge_gaps')
    .select('*')
    .order('frequency', { ascending: false })
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as KnowledgeGap[];
}

export async function getRecentFeedback(limit = 30): Promise<KnowledgeFeedback[]> {
  const { data, error } = await supabase
    .from('knowledge_feedback')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as KnowledgeFeedback[];
}

export async function getTicketFeedback(ticketId: string): Promise<KnowledgeFeedback | null> {
  const { data, error } = await supabase
    .from('knowledge_feedback')
    .select('*')
    .eq('ticket_id', ticketId)
    .order('created_at', { ascending: false })
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as KnowledgeFeedback | null;
}

export async function getTopChunkUsage(limit = 10): Promise<ChunkUsageStat[]> {
  const { data, error } = await supabase
    .from('knowledge_chunk_usage')
    .select('chunk_id, document_id, relevance_score')
    .order('created_at', { ascending: false })
    .limit(500);

  if (error) throw new Error(error.message);

  const rows = (data ?? []) as { chunk_id: string | null; document_id: string | null; relevance_score: number }[];

  const map = new Map<string, { document_id: string | null; scores: number[] }>();
  for (const row of rows) {
    if (!row.chunk_id) continue;
    const existing = map.get(row.chunk_id);
    if (existing) {
      existing.scores.push(row.relevance_score);
    } else {
      map.set(row.chunk_id, { document_id: row.document_id, scores: [row.relevance_score] });
    }
  }

  const stats: ChunkUsageStat[] = [];
  for (const [chunk_id, { document_id, scores }] of map) {
    stats.push({
      chunk_id,
      document_id,
      use_count: scores.length,
      avg_score: scores.reduce((s, v) => s + v, 0) / scores.length,
    });
  }

  stats.sort((a, b) => b.use_count - a.use_count);
  return stats.slice(0, limit);
}
