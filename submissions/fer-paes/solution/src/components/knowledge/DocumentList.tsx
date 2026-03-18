import { useState, useRef, useEffect } from 'react';
import {
  FileText, Trash2, Pencil, Layers, CheckCircle2, Clock,
  AlertCircle, Loader2, FolderOpen, Tag as TagIcon, Globe,
  MoreHorizontal, Zap, Database, Eye, X,
  CheckCheck, Archive,
} from 'lucide-react';
import {
  deleteDocument, publishDocument, archiveDocument,
  type KnowledgeDocumentRow, type PublishStatus, type ProcessingStatus,
} from '../../services/knowledgeService';
import { processDocument } from '../../services/processingService';
import { generateEmbeddings } from '../../services/embeddingService';

interface Props {
  documents:   KnowledgeDocumentRow[];
  loading:     boolean;
  onRefresh:   () => void;
  onEdit:      (doc: KnowledgeDocumentRow) => void;
  onViewChunks?: (doc: KnowledgeDocumentRow) => void;
}

const PROC_CFG: Record<ProcessingStatus, { cls: string; label: string }> = {
  ready:      { cls: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', label: 'Ready'      },
  processing: { cls: 'text-amber-400  bg-amber-500/10  border-amber-500/20',    label: 'Processing' },
  pending:    { cls: 'text-slate-500  bg-slate-500/10  border-slate-500/20',    label: 'Pending'    },
  error:      { cls: 'text-rose-400   bg-rose-500/10   border-rose-500/20',     label: 'Error'      },
};

const PUB_CFG: Record<PublishStatus, { cls: string; label: string }> = {
  draft:     { cls: 'text-amber-400  bg-amber-500/10  border-amber-500/20',   label: 'Draft'     },
  published: { cls: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', label: 'Published' },
  archived:  { cls: 'text-slate-400  bg-slate-500/10  border-slate-500/20',   label: 'Archived'  },
};

function ActionMenu({
  doc, onEdit, onViewChunks, onRefresh,
}: {
  doc: KnowledgeDocumentRow;
  onEdit: (d: KnowledgeDocumentRow) => void;
  onViewChunks?: (d: KnowledgeDocumentRow) => void;
  onRefresh: () => void;
}) {
  const [open,       setOpen]       = useState(false);
  const [processing, setProcessing] = useState(false);
  const [embedding,  setEmbedding]  = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [deleting,   setDeleting]   = useState(false);
  const [publishing, setPublishing] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  async function handleProcess() {
    setOpen(false); setProcessing(true);
    try { await processDocument(doc.id); onRefresh(); }
    catch { } finally { setProcessing(false); }
  }

  async function handleEmbed() {
    setOpen(false); setEmbedding(true);
    try { await generateEmbeddings(doc.id); onRefresh(); }
    catch { } finally { setEmbedding(false); }
  }

  async function handlePublish() {
    setOpen(false); setPublishing(true);
    try {
      if (doc.publish_status === 'published') await archiveDocument(doc.id);
      else await publishDocument(doc.id);
      onRefresh();
    } catch { } finally { setPublishing(false); }
  }

  async function handleDelete() {
    setDeleting(true);
    try { await deleteDocument(doc.id); onRefresh(); }
    catch { } finally { setDeleting(false); setConfirming(false); setOpen(false); }
  }

  const busy = processing || embedding || publishing || deleting;

  return (
    <div ref={ref} className="relative flex items-center gap-1">
      {(processing || embedding || publishing) && (
        <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-500" />
      )}

      <button
        onClick={() => onEdit(doc)}
        className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
        title="Edit"
      >
        <Pencil className="w-3.5 h-3.5" />
      </button>

      <button
        onClick={() => setOpen((v) => !v)}
        disabled={busy}
        className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors"
      >
        <MoreHorizontal className="w-3.5 h-3.5" />
      </button>

      {open && (
        <div className="absolute right-0 top-8 z-50 w-48 bg-slate-800 border border-white/10 rounded-xl shadow-xl overflow-hidden">
          {onViewChunks && doc.chunk_count > 0 && (
            <button
              onClick={() => { setOpen(false); onViewChunks(doc); }}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-slate-300 hover:text-white hover:bg-white/6 transition-colors"
            >
              <Eye className="w-3.5 h-3.5 text-slate-500" />
              View {doc.chunk_count} Chunk{doc.chunk_count !== 1 ? 's' : ''}
            </button>
          )}

          <button
            onClick={handleProcess}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-slate-300 hover:text-white hover:bg-white/6 transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            {doc.status === 'ready' ? 'Reprocess' : 'Process Document'}
          </button>

          <button
            onClick={handleEmbed}
            disabled={doc.status !== 'ready'}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-slate-300 hover:text-white hover:bg-white/6 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Database className="w-3.5 h-3.5 text-slate-500" />
            Generate Embeddings
          </button>

          <div className="h-px bg-white/6 my-1" />

          <button
            onClick={handlePublish}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-slate-300 hover:text-white hover:bg-white/6 transition-colors"
          >
            {doc.publish_status === 'published'
              ? <><Archive className="w-3.5 h-3.5 text-slate-500" />Archive</>
              : <><CheckCheck className="w-3.5 h-3.5 text-emerald-500" />Publish</>
            }
          </button>

          <div className="h-px bg-white/6 my-1" />

          {confirming ? (
            <div className="px-3 py-2.5 flex items-center justify-between gap-2">
              <span className="text-xs text-rose-400">Delete?</span>
              <div className="flex gap-1.5">
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-2 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs disabled:opacity-40 transition-colors"
                >
                  {deleting ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Yes'}
                </button>
                <button
                  onClick={() => setConfirming(false)}
                  className="px-2 py-1 rounded-lg text-slate-400 hover:text-white text-xs transition-colors"
                >
                  No
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function PipelineStatus({ status }: { status: ProcessingStatus }) {
  const cfg = PROC_CFG[status] ?? PROC_CFG.pending;
  return (
    <div className="flex items-center gap-1.5">
      {status === 'processing' ? (
        <Loader2 className="w-2.5 h-2.5 animate-spin text-amber-400 shrink-0" />
      ) : status === 'ready' ? (
        <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
      ) : status === 'error' ? (
        <AlertCircle className="w-2.5 h-2.5 text-rose-400 shrink-0" />
      ) : (
        <Clock className="w-2.5 h-2.5 text-slate-500 shrink-0" />
      )}
      <span className={`text-xs border px-1.5 py-0.5 rounded-md ${cfg.cls}`}>{cfg.label}</span>
    </div>
  );
}

export default function DocumentList({ documents, loading, onRefresh, onEdit, onViewChunks }: Props) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-5 h-5 animate-spin text-slate-600" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-12 h-12 rounded-2xl bg-slate-800 border border-white/8 flex items-center justify-center mb-3">
          <FileText className="w-6 h-6 text-slate-600" />
        </div>
        <p className="text-slate-400 font-medium">No documents yet</p>
        <p className="text-sm text-slate-600 mt-1">Create a new document to start building the knowledge base.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/40 border border-white/6 rounded-2xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/6">
            {['Title', 'Category / Source', 'Type', 'Pipeline', 'Chunks', 'Published', 'Updated', ''].map((h) => (
              <th key={h} className="text-left px-4 py-3 text-xs font-medium text-slate-500 first:pl-5 last:pr-4">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/4">
          {documents.map((doc) => {
            const pub  = PUB_CFG[doc.publish_status]  ?? PUB_CFG.draft;
            const tags = doc.knowledge_document_tags?.map((t) => t.knowledge_tags) ?? [];

            return (
              <tr key={doc.id} className="hover:bg-white/2 transition-colors group">
                <td className="px-4 py-3 pl-5">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-slate-800 border border-white/8 flex items-center justify-center shrink-0">
                      <FileText className="w-3.5 h-3.5 text-slate-500" />
                    </div>
                    <div className="min-w-0">
                      <p
                        className="text-sm text-white font-medium truncate max-w-[180px] cursor-pointer hover:text-blue-300 transition-colors"
                        onClick={() => onEdit(doc)}
                      >
                        {doc.title}
                      </p>
                      {tags.length > 0 && (
                        <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                          {tags.slice(0, 2).map((t) => (
                            <span
                              key={t.id}
                              className="flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded-md"
                              style={{ backgroundColor: t.color + '22', color: t.color }}
                            >
                              <TagIcon className="w-2 h-2" />{t.name}
                            </span>
                          ))}
                          {tags.length > 2 && <span className="text-xs text-slate-700">+{tags.length - 2}</span>}
                        </div>
                      )}
                    </div>
                  </div>
                </td>

                <td className="px-4 py-3">
                  <div className="space-y-1">
                    {doc.knowledge_categories?.name && (
                      <div className="flex items-center gap-1.5 text-xs text-slate-400">
                        <FolderOpen className="w-3 h-3 text-slate-600 shrink-0" />
                        <span className="truncate max-w-[100px]">{doc.knowledge_categories.name}</span>
                      </div>
                    )}
                    {doc.knowledge_sources?.name ? (
                      <div className="flex items-center gap-1.5 text-xs text-slate-600">
                        <Globe className="w-2.5 h-2.5 shrink-0" />
                        <span className="truncate max-w-[100px]">{doc.knowledge_sources.name}</span>
                      </div>
                    ) : doc.source ? (
                      <a
                        href={doc.source}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1 text-xs text-blue-400 hover:underline"
                      >
                        <Globe className="w-2.5 h-2.5 shrink-0" />Link
                      </a>
                    ) : null}
                    {!doc.knowledge_categories?.name && !doc.knowledge_sources?.name && !doc.source && (
                      <span className="text-xs text-slate-700">—</span>
                    )}
                  </div>
                </td>

                <td className="px-4 py-3">
                  <span className="text-xs text-slate-500 capitalize">{doc.document_type}</span>
                </td>

                <td className="px-4 py-3">
                  <PipelineStatus status={doc.status} />
                </td>

                <td className="px-4 py-3">
                  {doc.chunk_count > 0 ? (
                    <button
                      onClick={() => onViewChunks?.(doc)}
                      className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors group/chunk"
                    >
                      <Zap className="w-3 h-3 text-slate-600 group-hover/chunk:text-amber-400 transition-colors" />
                      <span>{doc.chunk_count}</span>
                    </button>
                  ) : (
                    <span className="text-xs text-slate-700">—</span>
                  )}
                </td>

                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-md border ${pub.cls}`}>{pub.label}</span>
                </td>

                <td className="px-4 py-3 text-xs text-slate-600 whitespace-nowrap">
                  {new Date(doc.updated_at ?? doc.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                </td>

                <td className="px-4 py-3 pr-4">
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ActionMenu doc={doc} onEdit={onEdit} onViewChunks={onViewChunks} onRefresh={onRefresh} />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
