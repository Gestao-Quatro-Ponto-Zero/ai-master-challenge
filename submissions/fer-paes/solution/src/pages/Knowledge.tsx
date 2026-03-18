import { useState, useEffect, useCallback } from 'react';
import {
  BookOpen, Plus, Search, Layers, FileText, Globe, FolderOpen,
  RefreshCw, Tag as TagIcon, Loader2, X, Upload, Activity, MessageSquare, BarChart2,
} from 'lucide-react';
import {
  listDocuments, listSources, listCategories, listTags,
  createTag, deleteTag,
  type KnowledgeDocumentRow, type KnowledgeStats,
  type KnowledgeSource, type KnowledgeCategory, type KnowledgeTag,
} from '../services/knowledgeService';
import DocumentList            from '../components/knowledge/DocumentList';
import DocumentEditor          from '../components/knowledge/DocumentEditor';
import DocumentIngestionPanel  from '../components/knowledge/DocumentIngestionPanel';
import SourceManager           from '../components/knowledge/SourceManager';
import CategoryManager         from '../components/knowledge/CategoryManager';
import SearchPanel             from '../components/knowledge/SearchPanel';
import ChunkViewer             from '../components/knowledge/ChunkViewer';
import EmbeddingMonitor        from '../components/knowledge/EmbeddingMonitor';
import FeedbackPanel            from '../components/knowledge/FeedbackPanel';
import KnowledgeAnalyticsPage  from '../components/knowledge/KnowledgeAnalyticsPage';

type Tab = 'documents' | 'sources' | 'categories' | 'tags' | 'search' | 'pipeline' | 'feedback' | 'analytics';

const TAG_COLORS = [
  '#ef4444','#f97316','#f59e0b','#84cc16','#10b981','#06b6d4',
  '#3b82f6','#8b5cf6','#ec4899','#6b7280',
];

function StatCard({ icon: Icon, label, value, sub, color = 'text-slate-400' }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded-xl bg-slate-800 border border-white/8 flex items-center justify-center">
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <p className={`text-2xl font-semibold ${color === 'text-slate-400' ? 'text-white' : color}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function Knowledge() {
  const [tab,        setTab]        = useState<Tab>('documents');
  const [documents,  setDocuments]  = useState<KnowledgeDocumentRow[]>([]);
  const [sources,    setSources]    = useState<KnowledgeSource[]>([]);
  const [categories, setCategories] = useState<KnowledgeCategory[]>([]);
  const [tags,       setTags]       = useState<KnowledgeTag[]>([]);
  const [stats,      setStats]      = useState<KnowledgeStats | null>(null);
  const [loading,    setLoading]    = useState(true);

  const [editDocId,      setEditDocId]      = useState<string | null | undefined>(undefined);
  const [showIngest,     setShowIngest]     = useState(false);
  const [chunkViewerDoc, setChunkViewerDoc] = useState<KnowledgeDocumentRow | null>(null);

  const [newTagName,  setNewTagName]  = useState('');
  const [newTagColor, setNewTagColor] = useState(TAG_COLORS[0]);
  const [tagSaving,   setTagSaving]   = useState(false);
  const [tagDeleting, setTagDeleting] = useState<string | null>(null);
  const [tagError,    setTagError]    = useState('');

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [docsData, srcs, cats, tgs] = await Promise.all([
        listDocuments(), listSources(), listCategories(), listTags(),
      ]);
      setDocuments(docsData.documents);
      setStats(docsData.stats);
      setSources(srcs);
      setCategories(cats);
      setTags(tgs);
    } catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  async function handleCreateTag() {
    if (!newTagName.trim()) { setTagError('O nome da tag é obrigatório'); return; }
    setTagSaving(true); setTagError('');
    try {
      await createTag(newTagName, newTagColor);
      setNewTagName(''); setNewTagColor(TAG_COLORS[0]);
      const updated = await listTags();
      setTags(updated);
    } catch (e) { setTagError((e as Error).message); } finally { setTagSaving(false); }
  }

  async function handleDeleteTag(id: string) {
    setTagDeleting(id);
    try { await deleteTag(id); setTags((t) => t.filter((x) => x.id !== id)); }
    catch (e) { alert((e as Error).message); }
    finally { setTagDeleting(null); }
  }

  const isEditing = editDocId !== undefined;

  const tabs: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'documents',  label: 'Documentos',  icon: FileText   },
    { id: 'sources',    label: 'Fontes',      icon: Globe      },
    { id: 'categories', label: 'Categorias',  icon: FolderOpen },
    { id: 'tags',       label: 'Tags',        icon: TagIcon    },
    { id: 'search',     label: 'Buscar',      icon: Search     },
    { id: 'pipeline',   label: 'Pipeline',    icon: Activity      },
    { id: 'feedback',   label: 'Feedback',    icon: MessageSquare },
    { id: 'analytics',  label: 'Análises',    icon: BarChart2     },
  ];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {!isEditing && (
        <>
          <div className="px-8 py-5 border-b border-white/6 shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-white">Base de Conhecimento</h1>
                  <p className="text-sm text-slate-300 mt-0.5">Organize e publique conteúdo para agentes com RAG</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={loadAll} disabled={loading}
                  className="p-2 rounded-xl hover:bg-white/6 text-slate-400 hover:text-white transition-colors disabled:opacity-40">
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </button>
                {tab === 'documents' && (
                  <>
                    <button onClick={() => setShowIngest(true)}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium transition-colors">
                      <Upload className="w-4 h-4" />Importar
                    </button>
                    <button onClick={() => setEditDocId(null)}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors">
                      <Plus className="w-4 h-4" />Novo Documento
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="px-8 py-4 border-b border-white/6 shrink-0">
            <div className="grid grid-cols-6 gap-3">
              <StatCard icon={FileText}   label="Total"      value={stats?.total     ?? documents.length} />
              <StatCard icon={Globe}      label="Publicados"  value={stats?.published ?? 0}  color="text-emerald-400" />
              <StatCard icon={FileText}   label="Rascunhos"     value={stats?.draft     ?? 0}  color="text-amber-400" />
              <StatCard icon={Layers}     label="Fragmentos"     value={stats?.chunks?.toLocaleString() ?? '—'} sub="Segmentos RAG" />
              <StatCard icon={Globe}      label="Fontes"    value={sources.length} />
              <StatCard icon={FolderOpen} label="Categorias" value={categories.length} />
            </div>
          </div>

          <div className="px-8 pt-4 border-b border-white/6 shrink-0">
            <div className="flex items-center gap-1 bg-slate-800/40 border border-white/6 rounded-xl p-1 w-fit">
              {tabs.map(({ id, label, icon: Icon }) => (
                <button key={id} onClick={() => setTab(id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === id ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-300 hover:text-white'}`}>
                  <Icon className="w-3.5 h-3.5" />{label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      <div className={`flex-1 ${isEditing ? 'flex flex-col overflow-hidden' : 'overflow-y-auto px-8 py-6'}`}>
        {isEditing ? (
          <DocumentEditor
            documentId={editDocId}
            sources={sources}
            categories={categories}
            tags={tags}
            onBack={() => setEditDocId(undefined)}
            onSaved={() => { loadAll(); setEditDocId(undefined); }}
          />
        ) : (
          <>
            {tab === 'documents' && (
              <DocumentList
                documents={documents}
                loading={loading}
                onRefresh={loadAll}
                onEdit={(doc) => setEditDocId(doc.id)}
                onViewChunks={(doc) => setChunkViewerDoc(doc)}
              />
            )}

            {tab === 'sources' && (
              <SourceManager sources={sources} onRefresh={async () => { setSources(await listSources()); }} />
            )}

            {tab === 'categories' && (
              <CategoryManager categories={categories} onRefresh={async () => { setCategories(await listCategories()); }} />
            )}

            {tab === 'tags' && (
              <div className="space-y-5">
                <div className="bg-slate-800/60 border border-white/8 rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-4">Nova Tag</h3>
                  {tagError && <p className="text-xs text-rose-400 mb-3">{tagError}</p>}
                  <div className="flex items-end gap-3">
                    <div className="flex-1">
                      <label className="block text-xs text-slate-400 mb-1.5">Nome</label>
                      <input value={newTagName} onChange={(e) => setNewTagName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleCreateTag()}
                        placeholder="e.g. returns"
                        className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-400 mb-1.5">Cor</label>
                      <div className="flex gap-1.5 flex-wrap w-52">
                        {TAG_COLORS.map((c) => (
                          <button key={c} onClick={() => setNewTagColor(c)}
                            className={`w-6 h-6 rounded-lg transition-transform hover:scale-110 ${newTagColor === c ? 'ring-2 ring-white/40 ring-offset-1 ring-offset-slate-900' : ''}`}
                            style={{ backgroundColor: c }} />
                        ))}
                      </div>
                    </div>
                    <button onClick={handleCreateTag} disabled={tagSaving}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors shrink-0">
                      {tagSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                      Adicionar Tag
                    </button>
                  </div>
                </div>

                {tags.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-14 bg-slate-800/20 border border-white/6 rounded-2xl text-center">
                    <TagIcon className="w-10 h-10 text-slate-500 mb-3" />
                    <p className="text-sm text-slate-400">Nenhuma tag ainda</p>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {tags.map((tag) => (
                      <div key={tag.id} className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/8 bg-slate-800/40 group">
                        <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: tag.color }} />
                        <span className="text-sm text-white">{tag.name}</span>
                        <button onClick={() => handleDeleteTag(tag.id)} disabled={tagDeleting === tag.id}
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-rose-400 ml-1">
                          {tagDeleting === tag.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {tab === 'search'   && <SearchPanel />}

            {tab === 'pipeline' && (
              <EmbeddingMonitor documents={documents} onRefresh={loadAll} />
            )}

            {tab === 'feedback'   && <FeedbackPanel />}

            {tab === 'analytics' && <KnowledgeAnalyticsPage />}
          </>
        )}
      </div>

      {chunkViewerDoc && (
        <ChunkViewer
          document={chunkViewerDoc}
          onClose={() => setChunkViewerDoc(null)}
        />
      )}

      {showIngest && (
        <DocumentIngestionPanel
          sources={sources}
          categories={categories}
          tags={tags}
          onClose={() => setShowIngest(false)}
          onSuccess={(docId) => {
            setShowIngest(false);
            loadAll();
            setEditDocId(docId);
          }}
        />
      )}
    </div>
  );
}
