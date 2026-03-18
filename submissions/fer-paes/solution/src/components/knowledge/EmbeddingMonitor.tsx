import { useState, useEffect, useCallback } from 'react';
import {
  Database, Loader2, CheckCircle2, AlertCircle, Clock,
  RefreshCw, Zap, Layers, BarChart2, Activity,
  FileText, ChevronRight,
} from 'lucide-react';
import { getEmbeddingStatusFromDb } from '../../services/embeddingService';
import { generateEmbeddings, reindexDocument } from '../../services/embeddingService';
import { processDocument } from '../../services/processingService';
import { getRetrievalStats, type RetrievalStats } from '../../services/retrievalService';
import { type KnowledgeDocumentRow } from '../../services/knowledgeService';

interface DocStatus {
  docId:           string;
  title:           string;
  status:          string;
  processingStatus: string;
  chunkCount:      number;
  embeddingStatus: string;
  loading:         boolean;
  error:           string;
}

interface Props {
  documents: KnowledgeDocumentRow[];
  onRefresh: () => void;
}

function StatCard({ icon: Icon, label, value, sub, color = 'text-white' }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-4">
      <div className="flex items-center gap-2.5 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className={`text-2xl font-semibold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}

function PipelineBar({ total, processed, embedded }: { total: number; processed: number; embedded: number }) {
  const pctProcessed = total > 0 ? (processed / total) * 100 : 0;
  const pctEmbedded  = total > 0 ? (embedded  / total) * 100 : 0;

  return (
    <div className="space-y-3">
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-slate-500">Processed</span>
          <span className="text-slate-400">{processed} / {total}</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all"
            style={{ width: `${pctProcessed}%` }}
          />
        </div>
      </div>
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-slate-500">Embedded</span>
          <span className="text-slate-400">{embedded} / {total}</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all"
            style={{ width: `${pctEmbedded}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function DocPipelineRow({ row, onProcess, onEmbed }: {
  row:       DocStatus;
  onProcess: () => void;
  onEmbed:   () => void;
}) {
  const isReady     = row.processingStatus === 'ready';
  const isEmbedded  = row.embeddingStatus  === 'embedded';

  return (
    <div className="flex items-center gap-4 px-5 py-3 hover:bg-white/2 transition-colors group">
      <div className="w-7 h-7 rounded-lg bg-slate-800 border border-white/8 flex items-center justify-center shrink-0">
        <FileText className="w-3.5 h-3.5 text-slate-600" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate max-w-xs">{row.title}</p>
        <p className="text-xs text-slate-600 mt-0.5">{row.chunkCount} chunk{row.chunkCount !== 1 ? 's' : ''}</p>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 w-28">
          {row.processingStatus === 'processing'   ? <Loader2     className="w-3 h-3 animate-spin text-amber-400" /> :
           row.processingStatus === 'ready'        ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> :
           row.processingStatus === 'error'        ? <AlertCircle  className="w-3 h-3 text-rose-400"    /> :
                                                     <Clock        className="w-3 h-3 text-slate-600"   />}
          <span className={`text-xs capitalize ${
            row.processingStatus === 'ready'      ? 'text-emerald-400' :
            row.processingStatus === 'processing' ? 'text-amber-400'   :
            row.processingStatus === 'error'      ? 'text-rose-400'    : 'text-slate-500'
          }`}>{row.processingStatus}</span>
        </div>

        <ChevronRight className="w-3 h-3 text-slate-700" />

        <div className="flex items-center gap-1.5 w-28">
          {row.embeddingStatus === 'embedding'  ? <Loader2     className="w-3 h-3 animate-spin text-amber-400"  /> :
           row.embeddingStatus === 'embedded'   ? <Database     className="w-3 h-3 text-blue-400"               /> :
           row.embeddingStatus === 'error'      ? <AlertCircle  className="w-3 h-3 text-rose-400"               /> :
                                                  <Clock        className="w-3 h-3 text-slate-600"              />}
          <span className={`text-xs capitalize ${
            row.embeddingStatus === 'embedded'  ? 'text-blue-400'  :
            row.embeddingStatus === 'embedding' ? 'text-amber-400' :
            row.embeddingStatus === 'error'     ? 'text-rose-400'  : 'text-slate-500'
          }`}>{row.embeddingStatus}</span>
        </div>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
        {row.loading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-500" />
        ) : (
          <>
            <button
              onClick={onProcess}
              title={isReady ? 'Reprocess' : 'Process'}
              className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
            >
              <Layers className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onEmbed}
              disabled={!isReady}
              title={isEmbedded ? 'Reindex' : 'Generate Embeddings'}
              className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 disabled:opacity-30 transition-colors"
            >
              <Database className="w-3.5 h-3.5" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default function EmbeddingMonitor({ documents, onRefresh }: Props) {
  const [rows,         setRows]         = useState<DocStatus[]>([]);
  const [retStats,     setRetStats]     = useState<RetrievalStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  const buildRows = useCallback(async () => {
    const initial: DocStatus[] = documents.map((d) => ({
      docId:           d.id,
      title:           d.title,
      status:          d.status,
      processingStatus: d.status,
      chunkCount:      d.chunk_count,
      embeddingStatus: 'unembedded',
      loading:         true,
      error:           '',
    }));
    setRows(initial);

    const updated = await Promise.all(
      documents.map(async (d) => {
        try {
          const embStatus = await getEmbeddingStatusFromDb(d.id);
          return {
            docId:           d.id,
            title:           d.title,
            status:          d.status,
            processingStatus: d.status,
            chunkCount:      d.chunk_count,
            embeddingStatus: embStatus,
            loading:         false,
            error:           '',
          };
        } catch {
          return {
            docId:           d.id,
            title:           d.title,
            status:          d.status,
            processingStatus: d.status,
            chunkCount:      d.chunk_count,
            embeddingStatus: 'unknown',
            loading:         false,
            error:           'Failed to load status',
          };
        }
      }),
    );
    setRows(updated);
  }, [documents]);

  useEffect(() => {
    buildRows();
    getRetrievalStats()
      .then(setRetStats)
      .catch(() => void 0)
      .finally(() => setLoadingStats(false));
  }, [buildRows]);

  async function handleProcess(docId: string) {
    setRows((prev) => prev.map((r) => r.docId === docId ? { ...r, loading: true } : r));
    try {
      await processDocument(docId);
      onRefresh();
      await buildRows();
    } catch { } finally {
      setRows((prev) => prev.map((r) => r.docId === docId ? { ...r, loading: false } : r));
    }
  }

  async function handleEmbed(docId: string) {
    setRows((prev) => prev.map((r) => r.docId === docId ? { ...r, loading: true } : r));
    try {
      const row = rows.find((r) => r.docId === docId);
      if (row?.embeddingStatus === 'embedded') await reindexDocument(docId);
      else await generateEmbeddings(docId);
      await buildRows();
    } catch { } finally {
      setRows((prev) => prev.map((r) => r.docId === docId ? { ...r, loading: false } : r));
    }
  }

  const totalDocs   = rows.length;
  const processed   = rows.filter((r) => r.processingStatus === 'ready').length;
  const embedded    = rows.filter((r) => r.embeddingStatus  === 'embedded').length;
  const errors      = rows.filter((r) => r.processingStatus === 'error' || r.embeddingStatus === 'error').length;
  const totalChunks = rows.reduce((s, r) => s + r.chunkCount, 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-5 gap-3">
        <StatCard icon={FileText}   label="Documents"  value={totalDocs}  />
        <StatCard icon={CheckCircle2} label="Processed" value={processed}  color="text-emerald-400" />
        <StatCard icon={Database}   label="Embedded"   value={embedded}   color="text-blue-400"    />
        <StatCard icon={Layers}     label="Chunks"     value={totalChunks.toLocaleString()} color="text-amber-400" />
        <StatCard icon={AlertCircle} label="Errors"    value={errors}     color={errors > 0 ? 'text-rose-400' : 'text-slate-500'} />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-slate-900/40 border border-white/6 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-slate-500" />
              <h3 className="text-sm font-semibold text-white">Processing Pipeline</h3>
            </div>
            <button
              onClick={() => { buildRows(); onRefresh(); }}
              className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
          <PipelineBar total={totalDocs} processed={processed} embedded={embedded} />
        </div>

        {!loadingStats && retStats && (
          <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <BarChart2 className="w-4 h-4 text-slate-500" />
              <h3 className="text-sm font-semibold text-white">Retrieval Stats</h3>
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-600">Total searches</span>
                <span className="text-slate-300">{retStats.total_searches?.toLocaleString() ?? '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Avg results</span>
                <span className="text-slate-300">{retStats.avg_result_count ?? '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Avg latency</span>
                <span className="text-slate-300">{retStats.avg_latency_ms ? `${retStats.avg_latency_ms}ms` : '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Avg top score</span>
                <span className="text-slate-300">{retStats.avg_top_score ? `${Math.round(retStats.avg_top_score * 100)}%` : '—'}</span>
              </div>
              <div className="h-px bg-white/6 my-1" />
              <div className="flex items-center gap-2 flex-wrap">
                {[
                  { label: 'Hybrid',   value: retStats.hybrid_searches,   color: 'bg-blue-500'    },
                  { label: 'Semantic', value: retStats.semantic_searches,  color: 'bg-emerald-500' },
                  { label: 'Keyword',  value: retStats.keyword_searches,   color: 'bg-amber-500'   },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${color}`} />
                    <span className="text-slate-600">{label}: <span className="text-slate-400">{value ?? 0}</span></span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {loadingStats && (
          <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5 flex items-center justify-center">
            <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
          </div>
        )}
      </div>

      <div className="bg-slate-900/40 border border-white/6 rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/6">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-white">Document Status</h3>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>Processing</span>
            <ChevronRight className="w-3 h-3 text-slate-700" />
            <span>Embedding</span>
          </div>
        </div>

        {rows.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Database className="w-8 h-8 text-slate-700 mb-3" />
            <p className="text-sm text-slate-500">No documents to monitor</p>
          </div>
        ) : (
          <div className="divide-y divide-white/4">
            {rows.map((row) => (
              <DocPipelineRow
                key={row.docId}
                row={row}
                onProcess={() => handleProcess(row.docId)}
                onEmbed={() => handleEmbed(row.docId)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
