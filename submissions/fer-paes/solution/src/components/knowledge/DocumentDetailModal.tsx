import { useState, useEffect } from 'react';
import { X, FileText, Layers, Link, Clock, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { getDocument, type KnowledgeDocumentDetail } from '../../services/knowledgeService';

interface Props {
  documentId: string;
  onClose: () => void;
}

function ChunkCard({ chunk, index }: { chunk: { id: string; chunk_text: string; chunk_index: number }; index: number }) {
  const [open, setOpen] = useState(index === 0);
  return (
    <div className="border border-white/6 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/4 transition-colors"
      >
        <div className="w-6 h-6 rounded-md bg-slate-800 border border-white/8 flex items-center justify-center shrink-0">
          <span className="text-xs text-slate-500 font-mono">{chunk.chunk_index + 1}</span>
        </div>
        <span className="flex-1 text-left text-xs text-slate-400 truncate">{chunk.chunk_text.slice(0, 80)}…</span>
        <span className="text-xs text-slate-600 shrink-0 mr-2">{chunk.chunk_text.length} chars</span>
        {open ? <ChevronDown className="w-3.5 h-3.5 text-slate-600 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
      </button>
      {open && (
        <div className="px-4 pb-4 pt-0 border-t border-white/6 bg-slate-900/40">
          <p className="text-sm text-slate-300 leading-relaxed pt-3 whitespace-pre-wrap">{chunk.chunk_text}</p>
        </div>
      )}
    </div>
  );
}

export default function DocumentDetailModal({ documentId, onClose }: Props) {
  const [doc, setDoc] = useState<KnowledgeDocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const data = await getDocument(documentId);
        setDoc(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setLoading(false);
      }
    })();
  }, [documentId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-slate-800 border border-white/8 flex items-center justify-center">
              <FileText className="w-4 h-4 text-slate-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold">{doc?.title ?? 'Document'}</h2>
              {doc?.source && (
                <a href={doc.source} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                  <Link className="w-2.5 h-2.5" />
                  {doc.source.slice(0, 60)}{doc.source.length > 60 ? '…' : ''}
                </a>
              )}
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/6 text-slate-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          {loading && (
            <div className="flex items-center gap-2 text-slate-600 py-8 justify-center">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Loading document…</span>
            </div>
          )}

          {error && (
            <div className="px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
              {error}
            </div>
          )}

          {doc && !loading && (
            <div className="space-y-5">
              <div className="grid grid-cols-3 gap-3">
                {[
                  { icon: Layers, label: 'Chunks', value: doc.chunk_count },
                  { icon: FileText, label: 'Characters', value: doc.content?.length?.toLocaleString() ?? '—' },
                  { icon: Clock, label: 'Added', value: new Date(doc.created_at).toLocaleDateString() },
                ].map(({ icon: Icon, label, value }) => (
                  <div key={label} className="bg-slate-800/60 border border-white/6 rounded-xl p-3 text-center">
                    <Icon className="w-4 h-4 text-slate-500 mx-auto mb-1" />
                    <p className="text-lg font-semibold text-white">{value}</p>
                    <p className="text-xs text-slate-600">{label}</p>
                  </div>
                ))}
              </div>

              <div>
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-slate-500" />
                  Chunks ({doc.knowledge_chunks?.length ?? 0})
                </h3>
                <div className="space-y-2">
                  {(doc.knowledge_chunks ?? [])
                    .sort((a, b) => a.chunk_index - b.chunk_index)
                    .map((chunk, i) => (
                      <ChunkCard key={chunk.id} chunk={chunk} index={i} />
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
