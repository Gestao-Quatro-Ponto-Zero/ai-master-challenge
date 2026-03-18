import { useState, useEffect } from 'react';
import {
  ArrowLeft, Check, Upload, Globe, Clock, History,
  RotateCcw, Loader2, Tag as TagIcon, X,
  FileText, BookOpen, Clipboard, Wrench, FileQuestion,
  Layers, Zap, ChevronDown, ChevronUp, Hash, Database, Cpu,
} from 'lucide-react';
import {
  createDocument, updateDocument, publishDocument, archiveDocument, getDocument,
  type KnowledgeDocumentRow, type KnowledgeSource, type KnowledgeCategory,
  type KnowledgeTag, type KnowledgeVersion, type DocumentType, type PublishStatus,
  restoreVersion,
} from '../../services/knowledgeService';
import {
  processDocument, getDocumentChunks, getProcessingStatus,
  type DocumentChunk,
} from '../../services/processingService';
import {
  generateEmbeddings, reindexDocument, getEmbeddingStatusFromDb,
  type EmbeddingStatus,
} from '../../services/embeddingService';

const DOC_TYPES: { value: DocumentType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { value: 'article',   label: 'Article',    icon: FileText     },
  { value: 'faq',       label: 'FAQ',        icon: FileQuestion },
  { value: 'policy',    label: 'Policy',     icon: Clipboard    },
  { value: 'procedure', label: 'Procedure',  icon: Wrench       },
  { value: 'guide',     label: 'Guide',      icon: BookOpen     },
];

const PUBLISH_STYLES: Record<PublishStatus, string> = {
  draft:     'text-amber-400 bg-amber-500/10 border-amber-500/20',
  published: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  archived:  'text-slate-400 bg-slate-500/10 border-slate-500/20',
};

interface Props {
  documentId?: string | null;
  sources: KnowledgeSource[];
  categories: KnowledgeCategory[];
  tags: KnowledgeTag[];
  onBack: () => void;
  onSaved: () => void;
}

export default function DocumentEditor({ documentId, sources, categories, tags, onBack, onSaved }: Props) {
  const [title,       setTitle]       = useState('');
  const [content,     setContent]     = useState('');
  const [sourceId,    setSourceId]    = useState('');
  const [categoryId,  setCategoryId]  = useState('');
  const [docType,     setDocType]     = useState<DocumentType>('article');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [sourceName,  setSourceName]  = useState('');

  const [saving,      setSaving]      = useState(false);
  const [publishing,  setPublishing]  = useState(false);
  const [loading,     setLoading]     = useState(!!documentId);
  const [error,       setError]       = useState('');
  const [saveMsg,     setSaveMsg]     = useState('');

  const [doc,         setDoc]         = useState<KnowledgeDocumentRow | null>(null);
  const [versions,    setVersions]    = useState<KnowledgeVersion[]>([]);
  const [showVersions, setShowVersions] = useState(false);
  const [versionNote, setVersionNote] = useState('');
  const [showVersionNote, setShowVersionNote] = useState(false);
  const [restoringVer, setRestoringVer] = useState<string | null>(null);

  const [processingStatus, setProcessingStatus] = useState<string>('unprocessed');
  const [processing,       setProcessing]       = useState(false);
  const [chunks,           setChunks]           = useState<DocumentChunk[]>([]);
  const [showChunks,       setShowChunks]       = useState(false);
  const [chunksLoading,    setChunksLoading]    = useState(false);

  const [embeddingStatus,  setEmbeddingStatus]  = useState<string>('unembedded');
  const [embeddingInfo,    setEmbeddingInfo]    = useState<EmbeddingStatus | null>(null);
  const [embedding,        setEmbedding]        = useState(false);

  useEffect(() => {
    if (!documentId) return;
    setLoading(true);
    (async () => {
      try {
        const d = await getDocument(documentId);
        setDoc(d);
        setTitle(d.title);
        setContent(d.content);
        setSourceId(d.source_id ?? '');
        setCategoryId(d.category_id ?? '');
        setDocType(d.document_type);
        setSourceName(d.source ?? '');
        const tagIds = d.knowledge_document_tags?.map((t) => t.knowledge_tags.id) ?? [];
        setSelectedTags(tagIds);
        setVersions(d.versions ?? []);
        const status = await getProcessingStatus(d.id);
        setProcessingStatus(status);
        const embStatus = await getEmbeddingStatusFromDb(d.id);
        setEmbeddingStatus(embStatus);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [documentId]);

  function toggleTag(id: string) {
    setSelectedTags((prev) => prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]);
  }

  async function handleProcess() {
    if (!documentId) return;
    setProcessing(true); setError('');
    try {
      const result = await processDocument(documentId);
      setProcessingStatus('processed');
      setDoc((prev) => prev ? { ...prev, chunk_count: result.chunk_count } : prev);
      setSaveMsg(`Processed: ${result.chunk_count} chunks`);
      setTimeout(() => setSaveMsg(''), 3000);
      if (showChunks) {
        const res = await getDocumentChunks(documentId);
        setChunks(res.chunks);
      }
    } catch (e) {
      setProcessingStatus('error');
      setError((e as Error).message);
    } finally {
      setProcessing(false);
    }
  }

  async function loadChunks() {
    if (!documentId) return;
    if (showChunks) { setShowChunks(false); return; }
    setChunksLoading(true);
    try {
      const res = await getDocumentChunks(documentId);
      setChunks(res.chunks);
      setShowChunks(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setChunksLoading(false);
    }
  }

  async function handleEmbed(reindex = false) {
    if (!documentId) return;
    setEmbedding(true); setError('');
    try {
      const result = reindex
        ? await reindexDocument(documentId)
        : await generateEmbeddings(documentId);
      setEmbeddingStatus(result.embedding_status);
      setEmbeddingInfo(result);
      setSaveMsg(
        `Embedded: ${result.embedded_chunks} / ${result.total_chunks} chunks`,
      );
      setTimeout(() => setSaveMsg(''), 3500);
    } catch (e) {
      setEmbeddingStatus('error');
      setError((e as Error).message);
    } finally {
      setEmbedding(false);
    }
  }

  async function saveDraft(createVersion = false) {
    if (!title.trim()) { setError('Title is required'); return; }
    if (!content.trim()) { setError('Content is required'); return; }
    setSaving(true); setError(''); setSaveMsg('');
    try {
      if (documentId) {
        await updateDocument(documentId, {
          title, content, source: sourceName, source_id: sourceId || null,
          category_id: categoryId || null, document_type: docType,
          tag_ids: selectedTags, create_version: createVersion,
          change_summary: versionNote || undefined,
        });
        const updated = await getDocument(documentId);
        setDoc(updated);
        setVersions(updated.versions ?? []);
      } else {
        await createDocument({
          title, content, source: sourceName, source_id: sourceId || undefined,
          category_id: categoryId || undefined, document_type: docType,
          tag_ids: selectedTags,
        });
      }
      setSaveMsg(createVersion ? 'New version saved' : 'Draft saved');
      setVersionNote('');
      setShowVersionNote(false);
      setTimeout(() => setSaveMsg(''), 2500);
      if (!documentId) onSaved();
    } catch (e) { setError((e as Error).message); } finally { setSaving(false); }
  }

  async function handlePublish() {
    if (!documentId) { await saveDraft(); return; }
    setPublishing(true); setError('');
    try {
      await publishDocument(documentId);
      const updated = await getDocument(documentId);
      setDoc(updated);
      setSaveMsg('Document published');
      setTimeout(() => setSaveMsg(''), 2500);
      onSaved();
    } catch (e) { setError((e as Error).message); } finally { setPublishing(false); }
  }

  async function handleArchive() {
    if (!documentId) return;
    setPublishing(true); setError('');
    try {
      await archiveDocument(documentId);
      const updated = await getDocument(documentId);
      setDoc(updated);
      setSaveMsg('Document archived');
      setTimeout(() => setSaveMsg(''), 2500);
      onSaved();
    } catch (e) { setError((e as Error).message); } finally { setPublishing(false); }
  }

  async function handleRestoreVersion(ver: KnowledgeVersion) {
    if (!documentId) return;
    if (!confirm(`Restore v${ver.version_number}? A new version will be created.`)) return;
    setRestoringVer(ver.id);
    try {
      await restoreVersion(documentId, ver.content, ver.version_number);
      const updated = await getDocument(documentId);
      setDoc(updated);
      setContent(ver.content);
      setVersions(updated.versions ?? []);
      setSaveMsg(`Restored to v${ver.version_number}`);
      setTimeout(() => setSaveMsg(''), 2500);
    } catch (e) { setError((e as Error).message); } finally { setRestoringVer(null); }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-5 h-5 animate-spin text-slate-600" />
      </div>
    );
  }

  const publishStatus = doc?.publish_status ?? 'draft';
  const charCount = content.length;
  const estimatedChunks = Math.max(1, Math.ceil(charCount / 550));

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/6 shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 rounded-xl text-slate-500 hover:text-white hover:bg-white/8 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-white">{documentId ? 'Edit Document' : 'New Document'}</h2>
            {doc && (
              <span className={`text-xs px-2 py-0.5 rounded-lg border capitalize ${PUBLISH_STYLES[publishStatus]}`}>
                {publishStatus}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {saveMsg && <span className="text-xs text-emerald-400 animate-pulse">{saveMsg}</span>}
          {error   && <span className="text-xs text-rose-400">{error}</span>}

          {documentId && (
            <button onClick={() => setShowVersions((v) => !v)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm transition-colors ${showVersions ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white hover:bg-white/8'}`}>
              <History className="w-3.5 h-3.5" />
              <span>v{doc?.version_count ?? 1}</span>
            </button>
          )}

          {documentId && (
            <button onClick={() => setShowVersionNote((v) => !v)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/8 transition-colors">
              <Upload className="w-3.5 h-3.5" />New Version
            </button>
          )}

          {documentId && (
            <button onClick={handleProcess} disabled={processing}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm transition-colors ${processing ? 'text-slate-600 cursor-not-allowed' : 'text-slate-400 hover:text-white hover:bg-white/8'}`}>
              {processing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Layers className="w-3.5 h-3.5" />}
              {processing ? 'Processing…' : processingStatus === 'processed' ? 'Reprocess' : 'Process'}
            </button>
          )}

          <button onClick={() => saveDraft(false)} disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors">
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            Save Draft
          </button>

          {publishStatus !== 'published' ? (
            <button onClick={handlePublish} disabled={publishing}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors">
              {publishing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Globe className="w-3.5 h-3.5" />}
              Publish
            </button>
          ) : (
            <button onClick={handleArchive} disabled={publishing}
              className="flex items-center gap-1.5 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors">
              {publishing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <X className="w-3.5 h-3.5" />}
              Archive
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {showVersionNote && (
            <div className="flex items-center gap-3 bg-slate-800/60 border border-white/8 rounded-xl px-4 py-3">
              <History className="w-4 h-4 text-slate-500 shrink-0" />
              <input value={versionNote} onChange={(e) => setVersionNote(e.target.value)}
                placeholder="Describe what changed in this version (optional)…"
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-600 focus:outline-none" />
              <button onClick={() => saveDraft(true)} disabled={saving}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs text-white font-medium transition-colors">
                Save New Version
              </button>
            </div>
          )}

          <div>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Document title…"
              className="w-full bg-transparent text-2xl font-semibold text-white placeholder-slate-700 focus:outline-none border-b border-white/6 pb-3" />
          </div>

          <div>
            <label className="block text-xs text-slate-500 mb-2">Content</label>
            <textarea value={content} onChange={(e) => setContent(e.target.value)}
              rows={20} placeholder="Write your document content here…"
              className="w-full bg-slate-900/40 border border-white/6 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/30 leading-relaxed font-mono" />
            <div className="flex items-center gap-4 mt-2 text-xs text-slate-700">
              <span>{charCount.toLocaleString()} chars</span>
              <span>~{estimatedChunks} chunk{estimatedChunks !== 1 ? 's' : ''} for RAG</span>
            </div>
          </div>
        </div>

        <div className="w-72 shrink-0 border-l border-white/6 overflow-y-auto px-5 py-5 space-y-5">
          {showVersions && versions.length > 0 ? (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Version History</h4>
                <button onClick={() => setShowVersions(false)} className="text-slate-600 hover:text-white"><X className="w-3.5 h-3.5" /></button>
              </div>
              <div className="space-y-2">
                {versions.map((ver) => (
                  <div key={ver.id} className={`rounded-xl border p-3 ${ver.is_current ? 'border-blue-500/30 bg-blue-500/5' : 'border-white/6 bg-slate-800/30'}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-white">v{ver.version_number}</span>
                      {ver.is_current && <span className="text-xs text-blue-400">Current</span>}
                    </div>
                    <p className="text-xs text-slate-500 mb-1">
                      {new Date(ver.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </p>
                    {ver.change_summary && <p className="text-xs text-slate-600 italic mb-2">{ver.change_summary}</p>}
                    {!ver.is_current && (
                      <button onClick={() => handleRestoreVersion(ver)} disabled={!!restoringVer}
                        className="flex items-center gap-1 text-xs text-slate-500 hover:text-white transition-colors">
                        {restoringVer === ver.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
                        Restore
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Type</label>
                <div className="grid grid-cols-1 gap-1.5">
                  {DOC_TYPES.map(({ value, label, icon: Icon }) => (
                    <button key={value} onClick={() => setDocType(value)}
                      className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm transition-colors ${docType === value ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white hover:bg-white/4'}`}>
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Source</label>
                <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}
                  className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40">
                  <option value="">— None —</option>
                  {sources.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Category</label>
                <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40">
                  <option value="">— None —</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.parent_id ? '  ' : ''}{c.name}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Source URL</label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600 pointer-events-none" />
                  <input value={sourceName} onChange={(e) => setSourceName(e.target.value)}
                    placeholder="https://…" type="url"
                    className="w-full bg-slate-900/60 border border-white/8 rounded-xl pl-8 pr-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Tags</label>
                <div className="flex flex-wrap gap-1.5">
                  {tags.map((tag) => {
                    const selected = selectedTags.includes(tag.id);
                    return (
                      <button key={tag.id} onClick={() => toggleTag(tag.id)}
                        className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-colors border ${selected ? 'border-transparent text-white' : 'border-white/8 text-slate-500 hover:text-white bg-transparent'}`}
                        style={selected ? { backgroundColor: tag.color + '33', borderColor: tag.color + '66', color: tag.color } : {}}>
                        <TagIcon className="w-2.5 h-2.5" />
                        {tag.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              {doc && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Info</label>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Versions</span>
                        <span className="text-slate-400">{doc.version_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Updated</span>
                        <span className="text-slate-400">{new Date(doc.updated_at).toLocaleDateString()}</span>
                      </div>
                      <button onClick={() => setShowVersions(true)} className="flex items-center gap-1 text-slate-600 hover:text-white transition-colors mt-1">
                        <Clock className="w-3 h-3" />View version history
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Processing</label>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-600">Status</span>
                        <span className={`capitalize px-2 py-0.5 rounded-lg font-medium ${
                          processingStatus === 'processed'  ? 'text-emerald-400 bg-emerald-500/10' :
                          processingStatus === 'processing' ? 'text-amber-400  bg-amber-500/10'   :
                          processingStatus === 'error'      ? 'text-rose-400   bg-rose-500/10'    :
                          'text-slate-500 bg-slate-800/60'
                        }`}>{processingStatus}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-600">Chunks</span>
                        <span className="text-slate-400">{doc.chunk_count}</span>
                      </div>
                      <button onClick={handleProcess} disabled={processing}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs text-white bg-slate-700/80 hover:bg-slate-700 border border-white/8 disabled:opacity-50 transition-colors">
                        {processing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                        {processing ? 'Processing…' : processingStatus === 'processed' ? 'Reprocess' : 'Process Document'}
                      </button>

                      {doc.chunk_count > 0 && (
                        <button onClick={loadChunks} disabled={chunksLoading}
                          className="w-full flex items-center justify-center gap-1.5 text-xs text-slate-500 hover:text-white transition-colors">
                          {chunksLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : showChunks ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          {showChunks ? 'Hide chunks' : `View ${doc.chunk_count} chunk${doc.chunk_count !== 1 ? 's' : ''}`}
                        </button>
                      )}

                      {showChunks && chunks.length > 0 && (
                        <div className="space-y-2 max-h-64 overflow-y-auto pr-1 -mr-1">
                          {chunks.map((chunk) => (
                            <div key={chunk.id} className="bg-slate-800/50 border border-white/6 rounded-xl p-3">
                              <div className="flex items-center justify-between mb-1.5">
                                <div className="flex items-center gap-1.5">
                                  <Hash className="w-3 h-3 text-slate-600" />
                                  <span className="text-xs text-slate-500 font-mono">{chunk.chunk_index + 1}</span>
                                </div>
                                <span className="text-xs text-slate-700">{chunk.token_count}t</span>
                              </div>
                              {chunk.section_title && (
                                <p className="text-xs text-blue-400 mb-1 truncate">{chunk.section_title}</p>
                              )}
                              <p className="text-xs text-slate-500 leading-relaxed line-clamp-3">{chunk.chunk_text}</p>
                              {(chunk.metadata.keywords ?? []).length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {(chunk.metadata.keywords ?? []).slice(0, 4).map((kw) => (
                                    <span key={kw} className="text-xs px-1.5 py-0.5 bg-slate-900/60 text-slate-600 rounded-md">{kw}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Embeddings</label>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-600">Status</span>
                        <span className={`capitalize px-2 py-0.5 rounded-lg font-medium ${
                          embeddingStatus === 'embedded'   ? 'text-emerald-400 bg-emerald-500/10' :
                          embeddingStatus === 'embedding'  ? 'text-amber-400  bg-amber-500/10'   :
                          embeddingStatus === 'error'      ? 'text-rose-400   bg-rose-500/10'    :
                          'text-slate-500 bg-slate-800/60'
                        }`}>{embeddingStatus}</span>
                      </div>

                      {embeddingInfo && (
                        <>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-600">Embedded</span>
                            <span className="text-slate-400">{embeddingInfo.embedded_chunks} / {embeddingInfo.total_chunks}</span>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-600">Model</span>
                            <span className="text-slate-500 font-mono">{embeddingInfo.model}</span>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-600">Indexed</span>
                            <span className={embeddingInfo.is_indexed ? 'text-emerald-400' : 'text-slate-600'}>{embeddingInfo.is_indexed ? 'Yes' : 'No'}</span>
                          </div>
                        </>
                      )}

                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEmbed(false)}
                          disabled={embedding || processingStatus !== 'processed'}
                          title={processingStatus !== 'processed' ? 'Process document first' : ''}
                          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs text-white bg-slate-700/80 hover:bg-slate-700 border border-white/8 disabled:opacity-40 transition-colors">
                          {embedding ? <Loader2 className="w-3 h-3 animate-spin" /> : <Database className="w-3 h-3" />}
                          {embeddingStatus === 'embedded' ? 'Update' : 'Embed'}
                        </button>
                        {embeddingStatus === 'embedded' && (
                          <button
                            onClick={() => handleEmbed(true)}
                            disabled={embedding}
                            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs text-slate-400 hover:text-white bg-transparent hover:bg-white/6 border border-white/8 disabled:opacity-40 transition-colors">
                            {embedding ? <Loader2 className="w-3 h-3 animate-spin" /> : <Cpu className="w-3 h-3" />}
                            Reindex
                          </button>
                        )}
                      </div>

                      {processingStatus !== 'processed' && (
                        <p className="text-xs text-slate-700 text-center">Process document first to enable embedding</p>
                      )}
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
