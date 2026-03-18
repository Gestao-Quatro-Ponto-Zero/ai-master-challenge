import { useState, useEffect } from 'react';
import {
  X, Layers, Hash, Loader2, FileText, Tag as TagIcon,
  ChevronDown, ChevronUp, Search, AlertCircle,
} from 'lucide-react';
import { getDocumentChunks, type DocumentChunk } from '../../services/processingService';
import { type KnowledgeDocumentRow } from '../../services/knowledgeService';

interface Props {
  document: KnowledgeDocumentRow;
  onClose:  () => void;
}

function ChunkCard({ chunk, index, expanded, onToggle }: {
  chunk:    DocumentChunk;
  index:    number;
  expanded: boolean;
  onToggle: () => void;
}) {
  const keywords = chunk.metadata?.keywords ?? [];
  const preview  = chunk.chunk_text.slice(0, 200);
  const hasMore  = chunk.chunk_text.length > 200;

  return (
    <div className="bg-slate-900/60 border border-white/8 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-white/3 transition-colors"
      >
        <div className="w-7 h-7 rounded-lg bg-slate-800 border border-white/8 flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-xs font-mono text-slate-500">{index + 1}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            {chunk.section_title && (
              <div className="flex items-center gap-1.5 text-xs text-blue-400">
                <Hash className="w-3 h-3" />
                <span className="truncate max-w-xs">{chunk.section_title}</span>
              </div>
            )}
            <div className="flex items-center gap-3 ml-auto shrink-0">
              <span className="text-xs text-slate-600 font-mono">{chunk.token_count}t</span>
              <span className="text-xs text-slate-700">{chunk.chunk_text.length} chars</span>
              {expanded
                ? <ChevronUp className="w-3.5 h-3.5 text-slate-600" />
                : <ChevronDown className="w-3.5 h-3.5 text-slate-600" />
              }
            </div>
          </div>

          <p className="text-sm text-slate-400 leading-relaxed">
            {expanded ? chunk.chunk_text : preview}
            {!expanded && hasMore && <span className="text-slate-600">…</span>}
          </p>

          {expanded && keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {keywords.map((kw) => (
                <span key={kw} className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-md bg-slate-800 border border-white/6 text-slate-500">
                  <TagIcon className="w-2.5 h-2.5" />{kw}
                </span>
              ))}
            </div>
          )}

          {expanded && chunk.metadata?.strategy && (
            <div className="mt-2 flex items-center gap-1 text-xs text-slate-700">
              strategy: <span className="text-slate-600 font-mono">{chunk.metadata.strategy}</span>
            </div>
          )}
        </div>
      </button>
    </div>
  );
}

export default function ChunkViewer({ document: doc, onClose }: Props) {
  const [chunks,   setChunks]   = useState<DocumentChunk[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState('');
  const [filter,   setFilter]   = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    (async () => {
      try {
        const res = await getDocumentChunks(doc.id);
        setChunks(res.chunks);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, [doc.id]);

  function toggleChunk(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function expandAll() {
    setExpanded(new Set(chunks.map((c) => c.id)));
  }

  function collapseAll() {
    setExpanded(new Set());
  }

  const filteredChunks = filter.trim()
    ? chunks.filter(
        (c) =>
          c.chunk_text.toLowerCase().includes(filter.toLowerCase()) ||
          (c.section_title ?? '').toLowerCase().includes(filter.toLowerCase()) ||
          (c.metadata?.keywords ?? []).some((k) => k.toLowerCase().includes(filter.toLowerCase())),
      )
    : chunks;

  const totalTokens   = chunks.reduce((s, c) => s + c.token_count, 0);
  const totalSections = new Set(chunks.map((c) => c.section_title).filter(Boolean)).size;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-3xl max-h-[90vh] flex flex-col bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/25 flex items-center justify-center">
              <Layers className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-sm font-semibold text-white truncate max-w-xs">{doc.title}</span>
              </div>
              {!loading && (
                <div className="flex items-center gap-3 mt-0.5">
                  <span className="text-xs text-slate-500">{chunks.length} chunks</span>
                  <span className="text-slate-700">·</span>
                  <span className="text-xs text-slate-600">{totalTokens.toLocaleString()} tokens</span>
                  {totalSections > 0 && (
                    <>
                      <span className="text-slate-700">·</span>
                      <span className="text-xs text-slate-600">{totalSections} section{totalSections !== 1 ? 's' : ''}</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl text-slate-500 hover:text-white hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {!loading && chunks.length > 0 && (
          <div className="px-6 py-3 border-b border-white/6 shrink-0">
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600" />
                <input
                  type="text"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder="Filter chunks by text, section, or keyword…"
                  className="w-full bg-slate-800 border border-white/8 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                />
              </div>
              <button onClick={expandAll} className="text-xs text-slate-500 hover:text-white transition-colors whitespace-nowrap">
                Expand all
              </button>
              <button onClick={collapseAll} className="text-xs text-slate-500 hover:text-white transition-colors whitespace-nowrap">
                Collapse all
              </button>
            </div>
            {filter && (
              <p className="text-xs text-slate-600 mt-1.5">
                {filteredChunks.length} of {chunks.length} chunks match
              </p>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-5 h-5 animate-spin text-slate-600" />
            </div>
          ) : error ? (
            <div className="flex items-center gap-2 px-4 py-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-sm text-rose-400">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          ) : chunks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Layers className="w-8 h-8 text-slate-700 mb-3" />
              <p className="text-slate-500 font-medium">No chunks yet</p>
              <p className="text-xs text-slate-600 mt-1">Process this document to generate chunks.</p>
            </div>
          ) : filteredChunks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="w-7 h-7 text-slate-700 mb-2" />
              <p className="text-sm text-slate-500">No chunks match your filter</p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredChunks.map((chunk, i) => (
                <ChunkCard
                  key={chunk.id}
                  chunk={chunk}
                  index={filter ? chunks.indexOf(chunk) : i}
                  expanded={expanded.has(chunk.id)}
                  onToggle={() => toggleChunk(chunk.id)}
                />
              ))}
            </div>
          )}
        </div>

        {!loading && chunks.length > 0 && (
          <div className="px-6 py-3 border-t border-white/6 shrink-0">
            <div className="flex items-center gap-4 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-500" />
                <span>Avg {Math.round(totalTokens / chunks.length)}t per chunk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-blue-500" />
                <span>~{Math.round(totalTokens / 750)} pages</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-amber-500" />
                <span>{chunks.reduce((s, c) => s + c.chunk_text.length, 0).toLocaleString()} total chars</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
