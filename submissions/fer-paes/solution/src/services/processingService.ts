import { supabase } from '../lib/supabaseClient';

export interface DocumentChunk {
  id:            string;
  chunk_index:   number;
  chunk_text:    string;
  token_count:   number;
  section_title: string;
  metadata:      {
    document_title?: string;
    section?:        string | null;
    keywords?:       string[];
    strategy?:       string;
    token_count?:    number;
  };
  created_at: string;
}

export interface ProcessResult {
  document_id:   string;
  chunk_count:   number;
  section_count: number;
  total_tokens:  number;
  strategy:      string;
}

export interface ChunksResult {
  chunks: DocumentChunk[];
  count:  number;
}

async function processFetch(path: string, method: 'GET' | 'POST', body?: unknown): Promise<unknown> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token      = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey    = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  const res = await fetch(`${supabaseUrl}/functions/v1/document-process${path}`, {
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

export async function processDocument(documentId: string, versionId?: string): Promise<ProcessResult> {
  return processFetch(`/${documentId}`, 'POST', { document_id: documentId, version_id: versionId }) as Promise<ProcessResult>;
}

export async function getDocumentChunks(documentId: string): Promise<ChunksResult> {
  return processFetch(`/${documentId}/chunks`, 'GET') as Promise<ChunksResult>;
}

export async function getProcessingStatus(documentId: string): Promise<string> {
  const { data } = await supabase
    .from('knowledge_documents')
    .select('processing_status')
    .eq('id', documentId)
    .maybeSingle();
  return (data as { processing_status?: string } | null)?.processing_status ?? 'unprocessed';
}
