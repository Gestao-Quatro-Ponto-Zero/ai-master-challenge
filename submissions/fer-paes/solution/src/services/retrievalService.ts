import { supabase } from '../lib/supabaseClient';

export type RetrievalStrategy = 'semantic' | 'keyword' | 'hybrid';

export interface RetrievalResult {
  chunk_id:        string;
  document_id:     string;
  chunk_text:      string;
  chunk_index:     number;
  section_title:   string;
  document_title:  string;
  document_source: string;
  score:           number;
  semantic_score:  number;
  keyword_score:   number;
  match_type:      'semantic' | 'keyword' | 'hybrid';
}

export interface SearchResponse {
  query:      string;
  strategy:   RetrievalStrategy;
  results:    RetrievalResult[];
  total:      number;
  latency_ms: number;
  context?:   string;
}

export interface ContextResponse {
  query:      string;
  strategy:   RetrievalStrategy;
  context:    string;
  sources:    { document_title: string; section_title: string; score: number }[];
  total:      number;
  latency_ms: number;
}

export interface RetrievalStats {
  total_searches:    number;
  semantic_searches: number;
  keyword_searches:  number;
  hybrid_searches:   number;
  avg_result_count:  number;
  avg_latency_ms:    number;
  avg_top_score:     number;
}

async function retFetch(
  path:   string,
  method: 'GET' | 'POST',
  body?:  unknown,
): Promise<unknown> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token      = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey    = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  const res = await fetch(`${supabaseUrl}/functions/v1/retrieval-service${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? anonKey}`,
      Apikey: anonKey,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const data = await res.json();
  if (!res.ok) throw new Error((data as { error?: string }).error ?? `HTTP ${res.status}`);
  return data;
}

export async function searchKnowledgeRetrieval(
  query:     string,
  topK      = 5,
  strategy:  RetrievalStrategy = 'hybrid',
  threshold = 0.25,
  includeContext = false,
): Promise<SearchResponse> {
  return retFetch('/search', 'POST', {
    query,
    top_k: topK,
    strategy,
    threshold,
    include_context: includeContext,
  }) as Promise<SearchResponse>;
}

export async function buildKnowledgeContext(
  query:     string,
  topK      = 5,
  strategy:  RetrievalStrategy = 'hybrid',
  threshold = 0.25,
  format:    'plain' | 'structured' = 'structured',
): Promise<ContextResponse> {
  return retFetch('/context', 'POST', {
    query,
    top_k: topK,
    strategy,
    threshold,
    format,
  }) as Promise<ContextResponse>;
}

export async function testRetrieval(
  query:    string,
  strategy: RetrievalStrategy = 'hybrid',
  topK     = 3,
): Promise<SearchResponse & { context: string }> {
  const params = new URLSearchParams({ query, strategy, top_k: String(topK) });
  return retFetch(`/test?${params}`, 'GET') as Promise<SearchResponse & { context: string }>;
}

export async function getRetrievalStats(): Promise<RetrievalStats> {
  return retFetch('/stats', 'GET') as Promise<RetrievalStats>;
}
