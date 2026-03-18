import { supabase } from '../lib/supabaseClient';

export interface EmbeddingStatus {
  document_id:      string;
  total_chunks:     number;
  embedded_chunks:  number;
  pending_chunks:   number;
  embedding_status: string;
  provider:         string;
  model:            string;
  is_indexed:       boolean;
}

export interface EmbeddingResult extends EmbeddingStatus {
  embedded: number;
  skipped:  number;
  errors:   number;
  total:    number;
}

async function embFetch(path: string, method: 'GET' | 'POST', body?: unknown): Promise<unknown> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token      = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey    = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  const res = await fetch(`${supabaseUrl}/functions/v1/embedding-pipeline${path}`, {
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

export async function generateEmbeddings(documentId: string): Promise<EmbeddingResult> {
  return embFetch(`/${documentId}/generate`, 'POST') as Promise<EmbeddingResult>;
}

export async function reindexDocument(documentId: string): Promise<EmbeddingResult> {
  return embFetch(`/${documentId}/reindex`, 'POST') as Promise<EmbeddingResult>;
}

export async function getEmbeddingStatus(documentId: string): Promise<EmbeddingStatus> {
  return embFetch(`/${documentId}/status`, 'GET') as Promise<EmbeddingStatus>;
}

export async function getEmbeddingStatusFromDb(documentId: string): Promise<string> {
  const { data } = await supabase
    .from('knowledge_documents')
    .select('embedding_status')
    .eq('id', documentId)
    .maybeSingle();
  return (data as { embedding_status?: string } | null)?.embedding_status ?? 'unembedded';
}
