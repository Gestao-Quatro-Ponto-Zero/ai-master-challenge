import { useState } from 'react';
import {
  Search, Loader2, Zap, FileText, BarChart2,
  SlidersHorizontal, Layers, Hash, Clock, BookOpen, Copy, Check,
} from 'lucide-react';
import {
  searchKnowledgeRetrieval, buildKnowledgeContext,
  type RetrievalResult, type RetrievalStrategy,
} from '../../services/retrievalService';

const STRATEGIES: { value: RetrievalStrategy; label: string; desc: string }[] = [
  { value: 'hybrid',   label: 'Hybrid',   desc: 'Vector + keyword (recommended)' },
  { value: 'semantic', label: 'Semantic',  desc: 'Vector similarity only'         },
  { value: 'keyword',  label: 'Keyword',   desc: 'Full-text search only'          },
];

const MATCH_COLORS: Record<string, string> = {
  hybrid:   'text-blue-400 bg-blue-500/10 border-blue-500/20',
  semantic: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  keyword:  'text-amber-400 bg-amber-500/10 border-amber-500/20',
};

function ScoreBar({ value, matchType }: { value: number; matchType: string }) {
  const pct   = Math.min(100, Math.round(value * 100));
  const color =
    matchType === 'semantic' ? 'bg-emerald-500' :
    matchType === 'keyword'  ? 'bg-amber-500'   : 'bg-blue-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 font-mono w-8 text-right">{pct}%</span>
    </div>
  );
}

function ResultCard({ result, index }: { result: RetrievalResult; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const preview = result.chunk_text.slice(0, 220);
  const hasMore = result.chunk_text.length > 220;

  return (
    <div className="bg-slate-900/60 border border-white/8 rounded-xl overflow-hidden hover:border-white/14 transition-colors">
      <div className="px-5 py-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-6 h-6 rounded-md bg-slate-800 border border-white/8 flex items-center justify-center shrink-0">
              <span className="text-xs text-slate-500 font-mono">{index + 1}</span>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 mb-0.5">
                <FileText className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                <span className="text-sm font-medium text-white truncate">{result.document_title}</span>
              </div>
              {result.section_title && (
                <div className="flex items-center gap-1 ml-5">
                  <Hash className="w-3 h-3 text-slate-400 shrink-0" />
                  <span className="text-xs text-slate-400 truncate">{result.section_title}</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className={`text-xs px-2 py-0.5 rounded-md border capitalize font-medium ${MATCH_COLORS[result.match_type] ?? MATCH_COLORS.hybrid}`}>
              {result.match_type}
            </span>
            <span className="text-xs text-slate-400 font-mono">#{result.chunk_index + 1}</span>
          </div>
        </div>

        <ScoreBar value={result.score} matchType={result.match_type} />

        {result.match_type === 'hybrid' && (
          <div className="flex gap-4 mt-1.5">
            <span className="text-xs text-slate-400">
              sem <span className="text-slate-500">{Math.round(result.semantic_score * 100)}%</span>
            </span>
            <span className="text-xs text-slate-400">
              kw <span className="text-slate-500">{Math.round(result.keyword_score * 100)}%</span>
            </span>
          </div>
        )}

        <p className="text-sm text-slate-300 leading-relaxed mt-3">
          {expanded ? result.chunk_text : preview}
          {!expanded && hasMore && '…'}
        </p>

        {hasMore && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="mt-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            {expanded ? 'Show less' : `+${result.chunk_text.length - 220} chars`}
          </button>
        )}
      </div>
    </div>
  );
}

function ContextView({ context }: { context: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(context);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400">RAG context — ready to inject into LLM prompt</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="bg-slate-950 border border-white/8 rounded-xl p-4 text-xs text-slate-400 leading-relaxed whitespace-pre-wrap font-mono overflow-y-auto max-h-96">
        {context}
      </pre>
    </div>
  );
}

type Tab = 'results' | 'context';

export default function SearchPanel() {
  const [query,        setQuery]        = useState('');
  const [strategy,     setStrategy]     = useState<RetrievalStrategy>('hybrid');
  const [topK,         setTopK]         = useState(5);
  const [threshold,    setThreshold]    = useState(0.25);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading,      setLoading]      = useState(false);
  const [results,      setResults]      = useState<RetrievalResult[] | null>(null);
  const [context,      setContext]      = useState('');
  const [latencyMs,    setLatencyMs]    = useState(0);
  const [searchedQuery, setSearchedQuery] = useState('');
  const [error,        setError]        = useState('');
  const [tab,          setTab]          = useState<Tab>('results');

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setResults(null);
    setContext('');
    try {
      const [searchRes, ctxRes] = await Promise.all([
        searchKnowledgeRetrieval(query.trim(), topK, strategy, threshold),
        buildKnowledgeContext(query.trim(), topK, strategy, threshold),
      ]);
      setResults(searchRes.results);
      setContext(ctxRes.context);
      setLatencyMs(searchRes.latency_ms);
      setSearchedQuery(query.trim());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  const EXAMPLE_QUERIES = [
    'What is the refund policy?',
    'How do I reset my password?',
    'Cancel subscription',
    'Shipping delivery time',
  ];

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="space-y-3">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question or describe what you're looking for…"
            className="w-full bg-slate-800 border border-white/8 rounded-xl pl-11 pr-32 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-medium transition-colors"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuery(q)}
                className="px-2.5 py-1 rounded-lg bg-slate-800 border border-white/6 text-xs text-slate-300 hover:text-white hover:border-white/14 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setShowAdvanced((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors shrink-0"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Advanced
          </button>
        </div>

        {showAdvanced && (
          <div className="p-4 bg-slate-800/40 border border-white/6 rounded-xl space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Search Strategy</label>
              <div className="grid grid-cols-3 gap-2">
                {STRATEGIES.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => setStrategy(s.value)}
                    className={`flex flex-col items-start px-3 py-2.5 rounded-xl border text-left transition-all ${
                      strategy === s.value
                        ? 'bg-blue-600/20 border-blue-500/40 text-white'
                        : 'bg-slate-900/40 border-white/6 text-slate-300 hover:border-white/14 hover:text-white'
                    }`}
                  >
                    <span className="text-xs font-medium">{s.label}</span>
                    <span className="text-xs opacity-60 mt-0.5 leading-tight">{s.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Max results: {topK}</label>
                <input
                  type="range" min={1} max={10} value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <div className="flex justify-between text-xs text-slate-400 mt-0.5"><span>1</span><span>10</span></div>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">
                  Min similarity: {Math.round(threshold * 100)}%
                  {strategy === 'keyword' && <span className="text-slate-400 ml-1">(semantic only)</span>}
                </label>
                <input
                  type="range" min={0} max={90} value={Math.round(threshold * 100)}
                  onChange={(e) => setThreshold(Number(e.target.value) / 100)}
                  className="w-full accent-blue-500"
                  disabled={strategy === 'keyword'}
                />
                <div className="flex justify-between text-xs text-slate-400 mt-0.5"><span>0%</span><span>90%</span></div>
              </div>
            </div>
          </div>
        )}
      </form>

      {error && (
        <div className="px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
          {error}
        </div>
      )}

      {results !== null && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-slate-500" />
                <span className="text-sm font-medium text-white">
                  {results.length} result{results.length !== 1 ? 's' : ''}
                </span>
              </div>
              <span className="text-slate-400">·</span>
              <span className="text-sm text-slate-300 truncate max-w-48">"{searchedQuery}"</span>
              <span className="text-slate-400">·</span>
              <div className="flex items-center gap-1 text-xs text-slate-400">
                <Clock className="w-3 h-3" />
                {latencyMs}ms
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-md border capitalize font-medium ${MATCH_COLORS[strategy]}`}>
                {strategy}
              </span>
            </div>

            {results.length > 0 && (
              <div className="flex bg-slate-800/60 rounded-xl border border-white/8 p-0.5">
                <button
                  onClick={() => setTab('results')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${tab === 'results' ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'}`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  Chunks
                </button>
                <button
                  onClick={() => setTab('context')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${tab === 'context' ? 'bg-slate-700 text-white' : 'text-slate-300 hover:text-white'}`}
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  Context
                </button>
              </div>
            )}
          </div>

          {results.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center bg-slate-900/40 border border-white/6 rounded-2xl">
              <Search className="w-8 h-8 text-slate-400 mb-3" />
              <p className="text-slate-400 font-medium">No results found</p>
              <p className="text-sm text-slate-400 mt-1">
                Try a different strategy, lower the similarity threshold, or upload more documents.
              </p>
            </div>
          ) : tab === 'results' ? (
            <div className="space-y-3">
              {results.map((r, i) => (
                <ResultCard key={r.chunk_id} result={r} index={i} />
              ))}
            </div>
          ) : (
            <ContextView context={context} />
          )}
        </div>
      )}
    </div>
  );
}
