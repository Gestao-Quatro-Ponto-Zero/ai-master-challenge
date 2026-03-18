import { useState, useEffect, useCallback } from 'react';
import {
  MessageSquare, TrendingUp, AlertTriangle, ThumbsUp,
  ThumbsDown, Minus, RefreshCw, Loader2, BarChart2,
  Search, Layers, Zap, ChevronRight,
} from 'lucide-react';
import {
  getFeedbackStats, getKnowledgeGaps, getRecentFeedback, getTopChunkUsage,
  type FeedbackStats, type KnowledgeGap, type KnowledgeFeedback, type ChunkUsageStat,
} from '../../services/feedbackService';

function StatCard({ icon: Icon, label, value, sub, color = 'text-white' }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string; value: string | number | null; sub?: string; color?: string;
}) {
  return (
    <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className={`text-2xl font-semibold ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}

function RatingBadge({ rating }: { rating: number }) {
  const stars  = Math.round(rating);
  const color  = rating >= 4 ? 'text-emerald-400' : rating >= 3 ? 'text-amber-400' : 'text-rose-400';
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <svg key={n} viewBox="0 0 16 16" className={`w-3 h-3 fill-current ${n <= stars ? color : 'text-slate-700'}`}>
          <path d="M8 12.3L3.1 15l.9-5.4L.4 6l5.5-.8L8 .3l2.1 4.9 5.5.8-4 3.9.9 5.4z" />
        </svg>
      ))}
      <span className={`text-xs ml-0.5 ${color}`}>{rating.toFixed(1)}</span>
    </div>
  );
}

function SentimentBar({ positive, neutral, negative }: { positive: number; neutral: number; negative: number }) {
  const total = positive + neutral + negative;
  if (total === 0) return <p className="text-xs text-slate-600">No feedback yet</p>;

  const pct = (n: number) => Math.round((n / total) * 100);

  return (
    <div className="space-y-3">
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <div className="flex items-center gap-1.5 text-emerald-400"><ThumbsUp className="w-3 h-3" />Positive</div>
          <span className="text-slate-400">{positive} ({pct(positive)}%)</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${pct(positive)}%` }} />
        </div>
      </div>
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <div className="flex items-center gap-1.5 text-amber-400"><Minus className="w-3 h-3" />Neutral</div>
          <span className="text-slate-400">{neutral} ({pct(neutral)}%)</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${pct(neutral)}%` }} />
        </div>
      </div>
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <div className="flex items-center gap-1.5 text-rose-400"><ThumbsDown className="w-3 h-3" />Negative</div>
          <span className="text-slate-400">{negative} ({pct(negative)}%)</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-rose-500 rounded-full transition-all" style={{ width: `${pct(negative)}%` }} />
        </div>
      </div>
    </div>
  );
}

function FeedbackRow({ fb }: { fb: KnowledgeFeedback }) {
  const stars = fb.rating;
  const color = stars >= 4 ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
              : stars >= 3 ? 'text-amber-400  bg-amber-500/10  border-amber-500/20'
                           : 'text-rose-400   bg-rose-500/10   border-rose-500/20';
  const Icon  = stars >= 4 ? ThumbsUp : stars >= 3 ? Minus : ThumbsDown;
  const label = stars >= 4 ? (stars === 5 ? 'Excellent' : 'Good') : stars >= 3 ? 'Partial' : stars === 2 ? 'Incomplete' : 'Not helpful';

  return (
    <div className="flex items-start gap-3 px-5 py-3.5 hover:bg-white/2 transition-colors border-b border-white/4 last:border-0">
      <div className={`mt-0.5 flex items-center gap-1.5 px-2 py-1 rounded-lg border text-xs font-medium shrink-0 ${color}`}>
        <Icon className="w-3 h-3" />
        {label}
      </div>
      <div className="flex-1 min-w-0">
        {fb.feedback_text ? (
          <p className="text-sm text-slate-300 leading-relaxed line-clamp-2">"{fb.feedback_text}"</p>
        ) : (
          <p className="text-xs text-slate-600 italic">No comment</p>
        )}
        <div className="flex items-center gap-3 mt-1 text-xs text-slate-600">
          <span className="capitalize">{fb.feedback_source}</span>
          {fb.ticket_id && (
            <>
              <ChevronRight className="w-3 h-3 text-slate-700" />
              <span className="font-mono">{fb.ticket_id.slice(0, 8)}</span>
            </>
          )}
          <span className="ml-auto">{new Date(fb.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
        </div>
      </div>
    </div>
  );
}

function GapRow({ gap, rank }: { gap: KnowledgeGap; rank: number }) {
  const urgency = gap.frequency >= 10 ? 'text-rose-400' : gap.frequency >= 5 ? 'text-amber-400' : 'text-slate-500';
  return (
    <div className="flex items-center gap-3 px-5 py-3 hover:bg-white/2 transition-colors border-b border-white/4 last:border-0 group">
      <span className="text-xs font-mono text-slate-700 w-5 shrink-0">{rank}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-300 truncate">{gap.query}</p>
        <p className="text-xs text-slate-600 mt-0.5">
          Last seen {new Date(gap.last_seen).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
        </p>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <AlertTriangle className={`w-3 h-3 ${urgency}`} />
        <span className={`text-sm font-semibold tabular-nums ${urgency}`}>{gap.frequency}×</span>
      </div>
    </div>
  );
}

function ChunkUsageRow({ stat, rank }: { stat: ChunkUsageStat; rank: number }) {
  return (
    <div className="flex items-center gap-3 px-5 py-3 hover:bg-white/2 transition-colors border-b border-white/4 last:border-0">
      <span className="text-xs font-mono text-slate-700 w-5 shrink-0">{rank}</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-mono text-slate-400 truncate">{stat.chunk_id.slice(0, 16)}…</p>
        {stat.document_id && (
          <p className="text-xs text-slate-600 mt-0.5 font-mono">{stat.document_id.slice(0, 8)}</p>
        )}
      </div>
      <div className="flex items-center gap-3 shrink-0 text-xs">
        <div className="flex items-center gap-1 text-amber-400">
          <Zap className="w-3 h-3" />
          <span className="font-semibold tabular-nums">{stat.use_count}</span>
        </div>
        <span className="text-slate-600">{(stat.avg_score * 100).toFixed(0)}% avg</span>
      </div>
    </div>
  );
}

export default function FeedbackPanel() {
  const [stats,      setStats]      = useState<FeedbackStats | null>(null);
  const [gaps,       setGaps]       = useState<KnowledgeGap[]>([]);
  const [feedback,   setFeedback]   = useState<KnowledgeFeedback[]>([]);
  const [chunkUsage, setChunkUsage] = useState<ChunkUsageStat[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [activeTab,  setActiveTab]  = useState<'gaps' | 'feedback' | 'chunks'>('gaps');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, g, f, c] = await Promise.all([
        getFeedbackStats(),
        getKnowledgeGaps(20),
        getRecentFeedback(30),
        getTopChunkUsage(10),
      ]);
      setStats(s);
      setGaps(g);
      setFeedback(f);
      setChunkUsage(c);
    } catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-slate-500" />
          <h3 className="text-sm font-semibold text-white">Knowledge Feedback</h3>
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
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-5 h-5 animate-spin text-slate-600" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-5 gap-3">
            <StatCard icon={MessageSquare} label="Total Feedback"  value={stats?.total        ?? 0} />
            <StatCard icon={TrendingUp}   label="Avg Rating"      value={stats?.avg_rating != null ? stats.avg_rating.toFixed(1) : null} sub="out of 5" color="text-blue-400" />
            <StatCard icon={ThumbsUp}     label="Positive"        value={stats?.positive     ?? 0} color="text-emerald-400" />
            <StatCard icon={AlertTriangle} label="Knowledge Gaps" value={stats?.total_gaps   ?? 0} color="text-amber-400"   />
            <StatCard icon={Layers}       label="Chunk Uses"      value={stats?.total_chunk_uses ?? 0} color="text-slate-400" />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-900/40 border border-white/6 rounded-2xl p-5 col-span-1">
              <div className="flex items-center gap-2 mb-4">
                <BarChart2 className="w-4 h-4 text-slate-500" />
                <h4 className="text-sm font-semibold text-white">Sentiment</h4>
              </div>
              {stats ? (
                <SentimentBar
                  positive={stats.positive}
                  neutral={stats.neutral}
                  negative={stats.negative}
                />
              ) : (
                <p className="text-xs text-slate-600">No data</p>
              )}
              {stats?.avg_rating != null && (
                <div className="mt-4 pt-4 border-t border-white/6">
                  <p className="text-xs text-slate-500 mb-1.5">Overall rating</p>
                  <RatingBadge rating={stats.avg_rating} />
                </div>
              )}
            </div>

            <div className="col-span-2 bg-slate-900/40 border border-white/6 rounded-2xl overflow-hidden">
              <div className="flex items-center gap-1 px-4 pt-4 pb-0">
                {([
                  { id: 'gaps',     label: 'Knowledge Gaps', icon: Search  },
                  { id: 'feedback', label: 'Recent Feedback', icon: MessageSquare },
                  { id: 'chunks',   label: 'Top Chunks',     icon: Layers  },
                ] as const).map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    onClick={() => setActiveTab(id)}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                      activeTab === id ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-white'
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                    {label}
                    {id === 'gaps'     && gaps.length     > 0 && <span className="ml-1 px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-xs">{gaps.length}</span>}
                    {id === 'feedback' && feedback.length > 0 && <span className="ml-1 px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-xs">{feedback.length}</span>}
                  </button>
                ))}
              </div>

              <div className="mt-3 max-h-72 overflow-y-auto">
                {activeTab === 'gaps' && (
                  gaps.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-10 text-center">
                      <Search className="w-7 h-7 text-slate-700 mb-2" />
                      <p className="text-sm text-slate-500">No knowledge gaps detected</p>
                      <p className="text-xs text-slate-700 mt-1">Gaps appear when queries return no relevant chunks</p>
                    </div>
                  ) : (
                    <div>
                      {gaps.map((gap, i) => (
                        <GapRow key={gap.id} gap={gap} rank={i + 1} />
                      ))}
                    </div>
                  )
                )}

                {activeTab === 'feedback' && (
                  feedback.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-10 text-center">
                      <MessageSquare className="w-7 h-7 text-slate-700 mb-2" />
                      <p className="text-sm text-slate-500">No feedback yet</p>
                      <p className="text-xs text-slate-700 mt-1">Feedback appears after operators rate AI responses</p>
                    </div>
                  ) : (
                    <div>
                      {feedback.map((fb) => (
                        <FeedbackRow key={fb.id} fb={fb} />
                      ))}
                    </div>
                  )
                )}

                {activeTab === 'chunks' && (
                  chunkUsage.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-10 text-center">
                      <Layers className="w-7 h-7 text-slate-700 mb-2" />
                      <p className="text-sm text-slate-500">No chunk usage recorded</p>
                      <p className="text-xs text-slate-700 mt-1">Usage is logged when agents retrieve knowledge</p>
                    </div>
                  ) : (
                    <div>
                      {chunkUsage.map((stat, i) => (
                        <ChunkUsageRow key={stat.chunk_id} stat={stat} rank={i + 1} />
                      ))}
                    </div>
                  )
                )}
              </div>
            </div>
          </div>

          {gaps.length > 0 && (
            <div className="bg-amber-500/5 border border-amber-500/15 rounded-2xl p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-amber-300 mb-1">
                    {gaps.length} knowledge gap{gaps.length !== 1 ? 's' : ''} detected
                  </p>
                  <p className="text-xs text-amber-400/70 leading-relaxed">
                    These queries returned no relevant knowledge during retrieval. Consider creating new documents to cover
                    {gaps.length <= 3
                      ? ': ' + gaps.slice(0, 3).map((g) => `"${g.query}"`).join(', ')
                      : ` these topics. The top query "${gaps[0].query}" has appeared ${gaps[0].frequency} times.`}
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
