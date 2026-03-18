import { supabase } from '../lib/supabaseClient';

export type IngestFormat = 'text' | 'html' | 'markdown' | 'json';

export interface IngestResult {
  document_id: string;
  title: string;
  char_count: number;
  format: IngestFormat;
  source_url?: string;
  filename?: string;
  suggested_title?: string;
}

async function ingestFetch(path: string, body: Record<string, unknown>): Promise<IngestResult> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token     = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey   = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  const res = await fetch(`${supabaseUrl}/functions/v1/document-ingest${path}`, {
    method:  'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? anonKey}`,
      Apikey: anonKey,
    },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
  return data as IngestResult;
}

export async function ingestManual(params: {
  title: string;
  content: string;
  format?: IngestFormat;
  source?: string;
  source_id?: string;
  category_id?: string;
  document_type?: string;
  tag_ids?: string[];
}): Promise<IngestResult> {
  return ingestFetch('', {
    title:          params.title,
    content:        params.content,
    format:         params.format ?? 'text',
    source:         params.source ?? '',
    source_id:      params.source_id,
    category_id:    params.category_id,
    document_type:  params.document_type,
    tag_ids:        params.tag_ids,
  });
}

export async function ingestUrl(params: {
  url: string;
  title?: string;
  source_id?: string;
  category_id?: string;
  document_type?: string;
  tag_ids?: string[];
}): Promise<IngestResult> {
  return ingestFetch('/url', {
    url:           params.url,
    title:         params.title ?? '',
    source_id:     params.source_id,
    category_id:   params.category_id,
    document_type: params.document_type,
    tag_ids:       params.tag_ids,
  });
}

export async function ingestFile(params: {
  file: File;
  title?: string;
  source?: string;
  source_id?: string;
  category_id?: string;
  document_type?: string;
  tag_ids?: string[];
}): Promise<IngestResult> {
  const buffer  = await params.file.arrayBuffer();
  const bytes   = new Uint8Array(buffer);
  const binary  = bytes.reduce((acc, b) => acc + String.fromCharCode(b), '');
  const content_base64 = btoa(binary);

  return ingestFetch('/file', {
    filename:       params.file.name,
    content_base64,
    title:          params.title ?? '',
    source:         params.source ?? '',
    source_id:      params.source_id,
    category_id:    params.category_id,
    document_type:  params.document_type,
    tag_ids:        params.tag_ids,
  });
}

export function detectClientFormat(content: string): IngestFormat {
  const trimmed = content.trimStart();
  if (trimmed.startsWith('<')) return 'html';
  if (/^#{1,6} /m.test(trimmed)) return 'markdown';
  try { JSON.parse(content); return 'json'; } catch { /* not json */ }
  return 'text';
}
