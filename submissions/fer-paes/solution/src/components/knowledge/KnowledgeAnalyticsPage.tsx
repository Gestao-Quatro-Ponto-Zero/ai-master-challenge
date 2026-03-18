import { useState, useEffect, useCallback } from 'react';
import {
  BarChart2, FileText, Layers, Search, AlertTriangle, ThumbsUp,
  ThumbsDown, Minus, RefreshCw, Loader2, TrendingUp, Zap,
  BookOpen, CheckCircle, Clock, MessageSquare,
} from 'lucide-react';
import {
  getKnowledgeOverview, getDocumentUsageStats, getChunkUsageStats,
  getQueryAnalytics, getResolutionImpact,
  type KnowledgeOverview, type DocumentUsageStat, type ChunkUsageStat,
  type QueryAnalyticsStat, type ResolutionImpact,
} from '../../services/analyticsService';
import { getKnowledgeGaps, type KnowledgeGap } from '../../services/feedbackService';

function OverviewCard({ icon: Icon, label, value, sub, color = 'text-white' }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number | null;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-3.5 h-3.5 ${color}`} />
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className={`text-2xl font-semibold tabular-nums ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}

function HorizBar({ label, value, max, color, sub }: {
  label: string; value: number; max: number; color: string; sub?: string;
}) {
  const pct = max > 0 ? Math.max(2, Math.round((value / max) * 100)) : 0;
  return (
    <div className="flex items-center gap-3">
      <div className="w-36 shrink-0 truncate text-xs text-slate-300">{label}</div>
      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="text-right shrink-0 min-w-[3rem]">
        <span className="text-xs font-semibold tabular-nums text-white">{value}</span>
        {sub && <span className="text-xs text-slate-600 ml-1">{sub}</span>}
      </div>
    </div>
  );
}

function ResolutionRing({ rate }: { rate: number }) {
  const r    = 32;
  const circ = 2 * Math.PI * r;
  const dash = (rate / 100) * circ;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="88" height="88" viewBox="0 0 88 88">
        <circle cx="44" cy="44" r={r} fill="none" stroke="#1e293b" strokeWidth="10" />
        <circle
          cx="44" cy="44" r={r}
          fill="none" stroke="#10b981" strokeWidth="10"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 44 44)"
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
      </svg>
      <div className="absolute text-center">
        <p className="text-lg font-bold text-white leading-none">{rate}%</p>
        <p className="text-xs text-slate-500 mt-0.5">resolved</p>
      </div>
    </div>
  );
}

function SectionHeader({ icon: Icon, title, badge }: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  badge?: number;
}) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-4 h-4 text-slate-500" />
      <h4 className="text-sm font-semibold text-white">{title}</h4>
      {badge != null && badge > 0 && (
        <span className="px-1.5 py-0.5 rounded-full bg-white/8 text-xs text-slate-400 tabular-nums">{badge}</span>
      )}
    </div>
  );
}

function EmptyState({ icon: Icon, text }: { icon: React.ComponentType<{ className?: string }>; text: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center gap-2">
      <Icon className="w-7 h-7 text-slate-700" />
      <p className="text-xs text-slate-600">{text}</p>
    </div>
  );
}

export default function KnowledgeAnalyticsPage() {
  const [overview,   setOverview]   = useState<KnowledgeOverview | null>(null);
  const [docStats,   setDocStats]   = useState<DocumentUsageStat[]>([]);
  const [chunkStats, setChunkStats] = useState<ChunkUsageStat[]>([]);
  const [queries,    setQueries]    = useState<QueryAnalyticsStat[]>([]);
  const [impact,     setImpact]     = useState<ResolutionImpact | null>(null);
  const [gaps,       setGaps]       = useState<KnowledgeGap[]>([]);
  const [loading,    setLoading]    = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ov, ds, cs, qs, imp, gs] = await Promise.all([
        getKnowledgeOverview(),
        getDocumentUsageStats(10),
        getChunkUsageStats(10),
        getQueryAnalytics(15),
        getResolutionImpact(),
        getKnowledgeGaps(15),
      ]);
      setOverview(ov);
      setDocStats(ds);
      setChunkStats(cs);
      setQueries(qs);
      setImpact(imp);
      setGaps(gs);
    } catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const maxDocUsage   = docStats[0]?.usage_count   ?? 1;
  const maxChunkUsage = chunkStats[0]?.usage_count  ?? 1;
  const maxQueryFreq  = queries[0]?.frequency       ?? 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-slate-500" />
          <h3 className="text-sm font-semibold text-white">Knowledge Analytics</h3>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="p-1.5 rounded-xl text-slate-600 hover:text-white hover:bg-white/8 disabled:opacity-40 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-5 h-5 animate-spin text-slate-600" />
        </div>
      ) : (
        <>
          {/* Overview Cards */}
          <div className="grid grid-cols-4 gap-3 xl:grid-cols-7">
            <OverviewCard icon={BookOpen}    label="Documents"   value={overview?.total_documents    ?? 0} />
            <OverviewCard icon={CheckCircle} label="Published"   value={overview?.published_documents ?? 0} color="text-emerald-400" />
            <OverviewCard icon={Layers}      label="Chunks"      value={overview?.total_chunks        ?? 0} color="text-slate-400"   />
            <OverviewCard icon={Zap}         label="Embedded"    value={overview?.embedded_chunks     ?? 0} color="text-blue-400"    />
            <OverviewCard icon={Search}      label="Queries"     value={overview?.queries_processed   ?? 0} color="text-slate-300"   />
            <OverviewCard
              icon={TrendingUp}
              label="Avg Rating"
              value={overview?.avg_feedback_rating != null ? overview.avg_feedback_rating.toFixed(1) : null}
              sub="out of 5"
              color="text-amber-400"
            />
            <OverviewCard icon={AlertTriangle} label="Gaps"      value={overview?.total_gaps          ?? 0} color="text-rose-400"    />
          </div>

          {/* Mid row: Documents + Impact */}
          <div className="grid grid-cols-3 gap-4">
            {/* Top Documents */}
            <div className="col-span-2 bg-slate-900/40 border border-white/6 rounded-2xl p-5">
              <SectionHeader icon={FileText} title="Most Used Documents" badge={docStats.length} />
              {docStats.length === 0 ? (
                <EmptyState icon={FileText} text="No document usage recorded yet" />
              ) : (
                <div className="space-y-3">
                  {docStats.map((d) => (
                    <HorizBar
                      key={d.document_id}
                      label={d.document_title ?? d.document_id.slice(0, 12) + '…'}
                      value={d.usage_count}
                      max={maxDocUsage}
                      color="bg-blue-500"
                      sub="uses"
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Resolution Impact */}
            <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5">
              <SectionHeader icon={CheckCircle} title="Resolution Impact" />
              {impact == null || impact.total_feedbacks === 0 ? (
                <EmptyState icon={MessageSquare} text="No feedback data yet" />
              ) : (
                <div className="flex flex-col items-center gap-5">
                  <ResolutionRing rate={Number(impact.resolution_rate)} />
                  <div className="w-full space-y-2.5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 text-emerald-400"><ThumbsUp   className="w-3 h-3" />AI Resolved</div>
                      <span className="font-semibold tabular-nums text-white">{impact.ai_resolved}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 text-amber-400"><Minus       className="w-3 h-3" />Partial</div>
                      <span className="font-semibold tabular-nums text-white">{impact.partially_resolved}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 text-rose-400"><ThumbsDown  className="w-3 h-3" />Escalated</div>
                      <span className="font-semibold tabular-nums text-white">{impact.escalated}</span>
                    </div>
                    {impact.avg_rating != null && (
                      <div className="pt-2 border-t border-white/6 flex items-center justify-between text-xs">
                        <span className="text-slate-500">Avg rating</span>
                        <div className="flex items-center gap-1 text-amber-400">
                          {[1,2,3,4,5].map((n) => (
                            <svg key={n} viewBox="0 0 16 16" className={`w-3 h-3 fill-current ${n <= Math.round(impact.avg_rating!) ? 'text-amber-400' : 'text-slate-700'}`}>
                              <path d="M8 12.3L3.1 15l.9-5.4L.4 6l5.5-.8L8 .3l2.1 4.9 5.5.8-4 3.9.9 5.4z" />
                            </svg>
                          ))}
                          <span className="font-semibold ml-0.5">{Number(impact.avg_rating).toFixed(1)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Bottom row: Queries + Chunks + Gaps */}
          <div className="grid grid-cols-3 gap-4">
            {/* Top Queries */}
            <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5">
              <SectionHeader icon={Search} title="Top Queries" badge={queries.length} />
              {queries.length === 0 ? (
                <EmptyState icon={Search} text="No queries recorded yet" />
              ) : (
                <div className="space-y-3">
                  {queries.map((q) => (
                    <div key={q.query_text} className="space-y-1.5">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs text-slate-300 leading-relaxed flex-1 min-w-0 truncate">{q.query_text}</p>
                        <span className="text-xs font-semibold tabular-nums text-white shrink-0">{q.frequency}×</span>
                      </div>
                      <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-slate-500 rounded-full"
                          style={{ width: `${Math.max(4, Math.round((q.frequency / maxQueryFreq) * 100))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Top Chunks */}
            <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5">
              <SectionHeader icon={Layers} title="Top Chunks" badge={chunkStats.length} />
              {chunkStats.length === 0 ? (
                <EmptyState icon={Layers} text="No chunk usage recorded yet" />
              ) : (
                <div className="space-y-2">
                  {chunkStats.map((c, i) => (
                    <div key={c.chunk_id} className="flex items-center gap-2.5 py-1.5 border-b border-white/4 last:border-0">
                      <span className="text-xs font-mono text-slate-700 w-4 shrink-0">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-slate-300 truncate">
                          {c.section_title ?? (c.document_title ?? 'Unknown document')}
                        </p>
                        {c.document_title && c.section_title && (
                          <p className="text-xs text-slate-600 truncate mt-0.5">{c.document_title}</p>
                        )}
                      </div>
                      <div className="flex flex-col items-end shrink-0 gap-0.5">
                        <div className="flex items-center gap-1">
                          <Zap className="w-2.5 h-2.5 text-amber-400" />
                          <span className="text-xs font-semibold tabular-nums text-white">{c.usage_count}</span>
                        </div>
                        <div className="h-1 w-16 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-amber-500 rounded-full"
                            style={{ width: `${Math.max(4, Math.round((c.usage_count / maxChunkUsage) * 100))}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Knowledge Gaps */}
            <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5">
              <SectionHeader icon={AlertTriangle} title="Knowledge Gaps" badge={gaps.length} />
              {gaps.length === 0 ? (
                <EmptyState icon={AlertTriangle} text="No knowledge gaps detected" />
              ) : (
                <div className="space-y-0">
                  {gaps.map((g) => {
                    const urgency = g.frequency >= 10 ? 'bg-rose-500/15 text-rose-300 border-rose-500/20'
                                  : g.frequency >= 5  ? 'bg-amber-500/15 text-amber-300 border-amber-500/20'
                                                      : 'bg-slate-500/15 text-slate-400 border-slate-500/20';
                    const dot     = g.frequency >= 10 ? 'bg-rose-400'
                                  : g.frequency >= 5  ? 'bg-amber-400' : 'bg-slate-500';
                    return (
                      <div key={g.id} className="flex items-center gap-2.5 py-2 border-b border-white/4 last:border-0">
                        <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${dot}`} />
                        <p className="text-xs text-slate-300 flex-1 min-w-0 truncate">{g.query}</p>
                        <span className={`px-1.5 py-0.5 rounded-lg border text-xs font-semibold tabular-nums shrink-0 ${urgency}`}>
                          {g.frequency}×
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
              {gaps.length >= 15 && (
                <p className="text-xs text-slate-600 mt-3 text-center">Showing top 15 gaps</p>
              )}
            </div>
          </div>

          {/* Index coverage indicator */}
          {overview && overview.total_chunks > 0 && (
            <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5">
              <SectionHeader icon={Zap} title="Embedding Coverage" />
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-2">
                    <span className="text-slate-500">Indexed chunks</span>
                    <span className="text-slate-300 tabular-nums">
                      {overview.embedded_chunks} / {overview.total_chunks}
                    </span>
                  </div>
                  <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-700"
                      style={{ width: `${Math.round((overview.embedded_chunks / overview.total_chunks) * 100)}%` }}
                    />
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <p className="text-2xl font-bold text-blue-400 tabular-nums">
                    {Math.round((overview.embedded_chunks / overview.total_chunks) * 100)}%
                  </p>
                  <p className="text-xs text-slate-600">coverage</p>
                </div>
              </div>
              {overview.embedded_chunks < overview.total_chunks && (
                <div className="mt-3 flex items-center gap-2 text-xs text-amber-400/80">
                  <Clock className="w-3 h-3 shrink-0" />
                  <span>
                    {overview.total_chunks - overview.embedded_chunks} chunk
                    {overview.total_chunks - overview.embedded_chunks !== 1 ? 's' : ''} pending embedding.
                    Run the embedding pipeline to improve retrieval quality.
                  </span>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
