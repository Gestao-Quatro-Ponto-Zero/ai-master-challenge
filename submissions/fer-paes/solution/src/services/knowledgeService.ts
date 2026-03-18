import { supabase } from '../lib/supabaseClient';

export type SourceType = 'manual_upload' | 'web_import' | 'api_import' | 'notion' | 'google_docs' | 'faq';
export type DocumentType = 'article' | 'faq' | 'policy' | 'procedure' | 'guide';
export type PublishStatus = 'draft' | 'published' | 'archived';
export type ProcessingStatus = 'pending' | 'processing' | 'ready' | 'error';

export interface KnowledgeSource {
  id: string;
  name: string;
  description: string;
  source_type: SourceType;
  is_active: boolean;
  created_at: string;
}

export interface KnowledgeCategory {
  id: string;
  name: string;
  description: string;
  parent_id: string | null;
  sort_order: number;
  created_at: string;
  children?: KnowledgeCategory[];
}

export interface KnowledgeTag {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface KnowledgeVersion {
  id: string;
  document_id: string;
  version_number: number;
  content: string;
  change_summary: string;
  created_by: string | null;
  is_current: boolean;
  created_at: string;
}

export interface KnowledgeDocumentRow {
  id: string;
  title: string;
  source: string;
  content: string;
  chunk_count: number;
  status: ProcessingStatus;
  source_id: string | null;
  category_id: string | null;
  document_type: DocumentType;
  publish_status: PublishStatus;
  created_by: string | null;
  version_count: number;
  created_at: string;
  updated_at: string;
  knowledge_sources?: { name: string; source_type: string } | null;
  knowledge_categories?: { name: string } | null;
  knowledge_document_tags?: { knowledge_tags: { id: string; name: string; color: string } }[];
}

export interface KnowledgeStats {
  total: number;
  ready: number;
  chunks: number;
  embeddings: number;
  published: number;
  draft: number;
}

export interface SearchResult {
  document_id: string;
  document_title: string;
  chunk_index: number;
  chunk_text: string;
  similarity: number;
}

async function ragFetch(path: string, options: RequestInit = {}): Promise<Record<string, unknown>> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey    = import.meta.env.VITE_SUPABASE_ANON_KEY as string;
  const res = await fetch(`${supabaseUrl}/functions/v1/rag-engine${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? anonKey}`,
      Apikey: anonKey,
      ...(options.headers ?? {}),
    },
  });
  const data = await res.json();
  if (!res.ok && data.error) throw new Error(data.error);
  return data as Record<string, unknown>;
}

export async function listDocuments(): Promise<{ documents: KnowledgeDocumentRow[]; stats: KnowledgeStats }> {
  const { data, error } = await supabase
    .from('knowledge_documents')
    .select(`
      id, title, source, content, chunk_count, status,
      source_id, category_id, document_type, publish_status,
      created_by, version_count, created_at, updated_at,
      knowledge_sources!source_id(name, source_type),
      knowledge_categories!category_id(name),
      knowledge_document_tags(knowledge_tags(id, name, color))
    `)
    .order('created_at', { ascending: false });

  if (error) throw new Error(error.message);
  const docs = (data ?? []) as KnowledgeDocumentRow[];

  const stats: KnowledgeStats = {
    total:      docs.length,
    ready:      docs.filter((d) => d.status === 'ready').length,
    chunks:     docs.reduce((a, d) => a + d.chunk_count, 0),
    embeddings: docs.reduce((a, d) => a + d.chunk_count, 0),
    published:  docs.filter((d) => d.publish_status === 'published').length,
    draft:      docs.filter((d) => d.publish_status === 'draft').length,
  };
  return { documents: docs, stats };
}

export async function getDocument(id: string): Promise<KnowledgeDocumentRow & { versions: KnowledgeVersion[] }> {
  const [docRes, versRes] = await Promise.all([
    supabase
      .from('knowledge_documents')
      .select(`
        id, title, source, content, chunk_count, status,
        source_id, category_id, document_type, publish_status,
        created_by, version_count, created_at, updated_at,
        knowledge_sources!source_id(name, source_type),
        knowledge_categories!category_id(name),
        knowledge_document_tags(knowledge_tags(id, name, color))
      `)
      .eq('id', id)
      .maybeSingle(),
    supabase
      .from('knowledge_versions')
      .select('*')
      .eq('document_id', id)
      .order('version_number', { ascending: false }),
  ]);

  if (docRes.error) throw new Error(docRes.error.message);
  if (!docRes.data) throw new Error('Document not found');
  return { ...(docRes.data as KnowledgeDocumentRow), versions: (versRes.data ?? []) as KnowledgeVersion[] };
}

export async function createDocument(params: {
  title: string;
  content: string;
  source?: string;
  source_id?: string;
  category_id?: string;
  document_type?: DocumentType;
  tag_ids?: string[];
  change_summary?: string;
}): Promise<KnowledgeDocumentRow> {
  const { data: session } = await supabase.auth.getSession();
  const userId = session?.session?.user?.id;

  const { data: doc, error: docErr } = await supabase
    .from('knowledge_documents')
    .insert({
      title:          params.title,
      content:        params.content,
      source:         params.source ?? '',
      source_id:      params.source_id ?? null,
      category_id:    params.category_id ?? null,
      document_type:  params.document_type ?? 'article',
      publish_status: 'draft',
      created_by:     userId ?? null,
      version_count:  1,
    })
    .select()
    .single();

  if (docErr) throw new Error(docErr.message);
  const docRow = doc as KnowledgeDocumentRow;

  await supabase.from('knowledge_versions').insert({
    document_id:    docRow.id,
    version_number: 1,
    content:        params.content,
    change_summary: params.change_summary ?? 'Initial version',
    created_by:     userId ?? null,
    is_current:     true,
  });

  if (params.tag_ids?.length) {
    await supabase.from('knowledge_document_tags').insert(
      params.tag_ids.map((tid) => ({ document_id: docRow.id, tag_id: tid }))
    );
  }

  return docRow;
}

export async function updateDocument(id: string, params: {
  title?: string;
  content?: string;
  source?: string;
  source_id?: string | null;
  category_id?: string | null;
  document_type?: DocumentType;
  tag_ids?: string[];
  change_summary?: string;
  create_version?: boolean;
}): Promise<void> {
  const { data: session } = await supabase.auth.getSession();
  const userId = session?.session?.user?.id;

  const updates: Record<string, unknown> = { updated_at: new Date().toISOString() };
  if (params.title         != null) updates.title         = params.title;
  if (params.source        != null) updates.source        = params.source;
  if (params.source_id     !== undefined) updates.source_id     = params.source_id;
  if (params.category_id   !== undefined) updates.category_id   = params.category_id;
  if (params.document_type != null) updates.document_type = params.document_type;
  if (params.content       != null) updates.content       = params.content;

  if (params.create_version && params.content != null) {
    const { data: latestVer } = await supabase
      .from('knowledge_versions')
      .select('version_number')
      .eq('document_id', id)
      .order('version_number', { ascending: false })
      .limit(1)
      .maybeSingle();

    const nextNum = ((latestVer as { version_number: number } | null)?.version_number ?? 0) + 1;

    await supabase.from('knowledge_versions').update({ is_current: false }).eq('document_id', id);

    await supabase.from('knowledge_versions').insert({
      document_id: id, version_number: nextNum,
      content: params.content, change_summary: params.change_summary ?? '',
      created_by: userId ?? null, is_current: true,
    });

    updates.version_count = nextNum;
  }

  const { error } = await supabase.from('knowledge_documents').update(updates).eq('id', id);
  if (error) throw new Error(error.message);

  if (params.tag_ids != null) {
    await supabase.from('knowledge_document_tags').delete().eq('document_id', id);
    if (params.tag_ids.length > 0) {
      await supabase.from('knowledge_document_tags').insert(
        params.tag_ids.map((tid) => ({ document_id: id, tag_id: tid }))
      );
    }
  }
}

export async function publishDocument(id: string): Promise<void> {
  const { error } = await supabase.from('knowledge_documents')
    .update({ publish_status: 'published', updated_at: new Date().toISOString() }).eq('id', id);
  if (error) throw new Error(error.message);
}

export async function archiveDocument(id: string): Promise<void> {
  const { error } = await supabase.from('knowledge_documents')
    .update({ publish_status: 'archived', updated_at: new Date().toISOString() }).eq('id', id);
  if (error) throw new Error(error.message);
}

export async function deleteDocument(id: string): Promise<void> {
  const { error } = await supabase.from('knowledge_documents').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function getDocumentVersions(documentId: string): Promise<KnowledgeVersion[]> {
  const { data, error } = await supabase
    .from('knowledge_versions').select('*').eq('document_id', documentId)
    .order('version_number', { ascending: false });
  if (error) throw new Error(error.message);
  return (data ?? []) as KnowledgeVersion[];
}

export async function restoreVersion(documentId: string, content: string, originalVersionNumber: number): Promise<void> {
  const { data: session } = await supabase.auth.getSession();
  const userId = session?.session?.user?.id;

  const { data: latestVer } = await supabase
    .from('knowledge_versions').select('version_number').eq('document_id', documentId)
    .order('version_number', { ascending: false }).limit(1).maybeSingle();

  const nextNum = ((latestVer as { version_number: number } | null)?.version_number ?? 0) + 1;

  await supabase.from('knowledge_versions').update({ is_current: false }).eq('document_id', documentId);
  await supabase.from('knowledge_versions').insert({
    document_id: documentId, version_number: nextNum,
    content, change_summary: `Restored from v${originalVersionNumber}`,
    created_by: userId ?? null, is_current: true,
  });
  await supabase.from('knowledge_documents').update({
    content, version_count: nextNum, updated_at: new Date().toISOString(),
  }).eq('id', documentId);
}

export async function listSources(): Promise<KnowledgeSource[]> {
  const { data, error } = await supabase.from('knowledge_sources').select('*').order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as KnowledgeSource[];
}

export async function createSource(params: { name: string; description?: string; source_type?: SourceType }): Promise<KnowledgeSource> {
  const { data, error } = await supabase.from('knowledge_sources')
    .insert({ name: params.name, description: params.description ?? '', source_type: params.source_type ?? 'manual_upload' })
    .select().single();
  if (error) throw new Error(error.message);
  return data as KnowledgeSource;
}

export async function updateSource(id: string, params: Partial<Omit<KnowledgeSource, 'id' | 'created_at'>>): Promise<void> {
  const { error } = await supabase.from('knowledge_sources').update(params).eq('id', id);
  if (error) throw new Error(error.message);
}

export async function deleteSource(id: string): Promise<void> {
  const { error } = await supabase.from('knowledge_sources').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function listCategories(): Promise<KnowledgeCategory[]> {
  const { data, error } = await supabase.from('knowledge_categories').select('*').order('sort_order').order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as KnowledgeCategory[];
}

export async function createCategory(params: { name: string; description?: string; parent_id?: string | null }): Promise<KnowledgeCategory> {
  const { data, error } = await supabase.from('knowledge_categories')
    .insert({ name: params.name, description: params.description ?? '', parent_id: params.parent_id ?? null })
    .select().single();
  if (error) throw new Error(error.message);
  return data as KnowledgeCategory;
}

export async function updateCategory(id: string, params: Partial<Omit<KnowledgeCategory, 'id' | 'created_at' | 'children'>>): Promise<void> {
  const { error } = await supabase.from('knowledge_categories').update(params).eq('id', id);
  if (error) throw new Error(error.message);
}

export async function deleteCategory(id: string): Promise<void> {
  const { error } = await supabase.from('knowledge_categories').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function listTags(): Promise<KnowledgeTag[]> {
  const { data, error } = await supabase.from('knowledge_tags').select('*').order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as KnowledgeTag[];
}

export async function createTag(name: string, color?: string): Promise<KnowledgeTag> {
  const { data, error } = await supabase.from('knowledge_tags')
    .insert({ name: name.toLowerCase().trim(), color: color ?? '#6b7280' })
    .select().single();
  if (error) throw new Error(error.message);
  return data as KnowledgeTag;
}

export async function deleteTag(id: string): Promise<void> {
  const { error } = await supabase.from('knowledge_tags').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function addDocumentViaRag(params: { title: string; content: string; source?: string }): Promise<{ document_id: string }> {
  const data = await ragFetch('/documents', {
    method: 'POST',
    body: JSON.stringify({ title: params.title, content: params.content, source: params.source ?? '' }),
  });
  return data as { document_id: string };
}

export async function searchKnowledge(params: { query: string; top_k?: number; threshold?: number }): Promise<SearchResult[]> {
  const data = await ragFetch('/search', {
    method: 'POST',
    body: JSON.stringify({ query: params.query, top_k: params.top_k ?? 5, threshold: params.threshold ?? 0.5 }),
  });
  return (data.results ?? []) as SearchResult[];
}
