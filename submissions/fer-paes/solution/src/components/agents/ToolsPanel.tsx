import { useState, useEffect, useCallback } from 'react';
import {
  Wrench, Play, Loader2, CheckCircle2, XCircle, Clock,
  ChevronRight, Code2, RefreshCw, Search, Zap, Hash,
} from 'lucide-react';
import {
  getAllTools, executeTool,
  CATEGORY_LABELS, CATEGORY_COLORS,
  type ToolDefinition, type ExecuteToolResult,
} from '../../services/agentToolsService';

const TOOL_ICONS: Record<string, string> = {
  search_knowledge_base: '📚',
  lookup_customer: '👤',
  get_ticket_info: '🎫',
  update_ticket_status: '🔄',
  add_ticket_note: '📝',
  create_ticket: '➕',
  lookup_order: '📦',
  escalate_to_human: '🙋',
};

function SchemaViewer({ schema }: { schema: ToolDefinition['input_schema'] }) {
  const props = schema?.properties ?? {};
  const required = schema?.required ?? [];
  const entries = Object.entries(props);

  if (entries.length === 0) {
    return <p className="text-xs text-slate-600 italic">No parameters required</p>;
  }

  return (
    <div className="space-y-2">
      {entries.map(([key, val]) => (
        <div key={key} className="flex items-start gap-3">
          <div className="shrink-0 mt-0.5">
            <span className="text-xs font-mono text-slate-300">{key}</span>
            {required.includes(key) && (
              <span className="ml-1 text-rose-400 text-xs">*</span>
            )}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 font-mono">{val.type}</span>
              {val.enum && val.enum.map((e) => (
                <span key={e} className="text-xs px-1.5 py-0.5 rounded bg-slate-800 border border-white/6 text-slate-500 font-mono">{e}</span>
              ))}
            </div>
            {val.description && (
              <p className="text-xs text-slate-500 mt-0.5">{val.description}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function ToolArgForm({
  tool,
  onExecute,
  executing,
}: {
  tool: ToolDefinition;
  onExecute: (args: Record<string, string>) => void;
  executing: boolean;
}) {
  const props = tool.input_schema?.properties ?? {};
  const required = tool.input_schema?.required ?? [];
  const entries = Object.entries(props);

  const [args, setArgs] = useState<Record<string, string>>({});

  useEffect(() => {
    setArgs({});
  }, [tool.name]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onExecute(args);
  }

  if (entries.length === 0) {
    return (
      <button
        onClick={() => onExecute({})}
        disabled={executing}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-medium transition-colors"
      >
        {executing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
        Execute
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {entries.map(([key, val]) => (
        <div key={key}>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">
            <span className="font-mono">{key}</span>
            {required.includes(key) && <span className="text-rose-400 ml-0.5">*</span>}
            {val.description && <span className="ml-2 font-normal text-slate-600">{val.description}</span>}
          </label>
          {val.enum ? (
            <select
              value={args[key] ?? ''}
              onChange={(e) => setArgs((p) => ({ ...p, [key]: e.target.value }))}
              className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
            >
              <option value="">Select…</option>
              {val.enum.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={args[key] ?? ''}
              onChange={(e) => setArgs((p) => ({ ...p, [key]: e.target.value }))}
              placeholder={`Enter ${key}…`}
              className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
            />
          )}
        </div>
      ))}
      <div className="pt-1">
        <button
          type="submit"
          disabled={executing || required.some((k) => !args[k]?.trim())}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
        >
          {executing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
          {executing ? 'Executing…' : 'Execute Tool'}
        </button>
      </div>
    </form>
  );
}

function ResultViewer({ result }: { result: ExecuteToolResult }) {
  const isError = !!result.error;
  return (
    <div className={`rounded-xl border overflow-hidden ${isError ? 'border-rose-500/20 bg-rose-500/5' : 'border-emerald-500/20 bg-emerald-500/5'}`}>
      <div className={`flex items-center gap-2 px-3 py-2 border-b ${isError ? 'border-rose-500/15' : 'border-emerald-500/15'}`}>
        {isError
          ? <XCircle className="w-3.5 h-3.5 text-rose-400" />
          : <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
        <span className={`text-xs font-medium ${isError ? 'text-rose-400' : 'text-emerald-400'}`}>
          {isError ? 'Error' : 'Result'}
        </span>
        <div className="ml-auto flex items-center gap-1 text-slate-600">
          <Clock className="w-3 h-3" />
          <span className="text-xs">{result.duration_ms}ms</span>
        </div>
      </div>
      <div className="p-3">
        <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap break-all leading-relaxed">
          {isError ? result.error : JSON.stringify(result.result, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function ToolCard({
  tool,
  selected,
  onClick,
}: {
  tool: ToolDefinition;
  selected: boolean;
  onClick: () => void;
}) {
  const cat = CATEGORY_COLORS[tool.category] ?? CATEGORY_COLORS.general;
  const emoji = TOOL_ICONS[tool.name] ?? '🔧';
  const paramCount = Object.keys(tool.input_schema?.properties ?? {}).length;

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-xl border p-3.5 transition-all ${
        selected
          ? 'border-blue-500/40 bg-blue-500/8 ring-1 ring-blue-500/20'
          : 'border-white/6 bg-slate-900/40 hover:bg-slate-800/60 hover:border-white/12'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-slate-800 border border-white/8 flex items-center justify-center text-sm shrink-0">
          {emoji}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-white truncate">{tool.display_name}</span>
            <span className={`shrink-0 text-xs px-1.5 py-0.5 rounded-md border ${cat.bg} ${cat.text} ${cat.border}`}>
              {CATEGORY_LABELS[tool.category] ?? tool.category}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed line-clamp-2">{tool.description}</p>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-xs text-slate-700 font-mono">{tool.name}</span>
            <span className="text-xs text-slate-700">·</span>
            <span className="text-xs text-slate-700">{paramCount} param{paramCount !== 1 ? 's' : ''}</span>
          </div>
        </div>
        {selected && <ChevronRight className="w-4 h-4 text-blue-400 shrink-0 mt-1" />}
      </div>
    </button>
  );
}

export default function ToolsPanel() {
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [selectedTool, setSelectedTool] = useState<ToolDefinition | null>(null);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<ExecuteToolResult | null>(null);
  const [execError, setExecError] = useState('');
  const [activeTab, setActiveTab] = useState<'schema' | 'test'>('schema');
  const [contextTicketId, setContextTicketId] = useState('');
  const [showContext, setShowContext] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAllTools();
      setTools(data);
      if (!selectedTool && data.length > 0) setSelectedTool(data[0]);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [selectedTool]);

  useEffect(() => { load(); }, []);

  async function handleExecute(args: Record<string, string>) {
    if (!selectedTool) return;
    setExecuting(true);
    setResult(null);
    setExecError('');
    try {
      const res = await executeTool({
        tool_name: selectedTool.name,
        arguments: args,
        context: contextTicketId ? { ticket_id: contextTicketId } : undefined,
      });
      setResult(res);
    } catch (err) {
      setExecError(err instanceof Error ? err.message : 'Execution failed');
    } finally {
      setExecuting(false);
    }
  }

  const categories = ['all', ...Array.from(new Set(tools.map((t) => t.category)))];

  const filtered = tools.filter((t) => {
    const matchesCat = filterCategory === 'all' || t.category === filterCategory;
    const q = search.toLowerCase();
    const matchesSearch = !q || t.name.includes(q) || t.display_name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q);
    return matchesCat && matchesSearch;
  });

  const grouped = filtered.reduce<Record<string, ToolDefinition[]>>((acc, t) => {
    (acc[t.category] = acc[t.category] ?? []).push(t);
    return acc;
  }, {});

  return (
    <div className="flex gap-0 h-full overflow-hidden">
      <div className="w-80 shrink-0 border-r border-white/6 flex flex-col overflow-hidden">
        <div className="p-4 border-b border-white/6 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tools…"
              className="w-full bg-slate-800 border border-white/8 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
            />
          </div>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
            {categories.map((cat) => {
              const catColor = CATEGORY_COLORS[cat];
              const isActive = filterCategory === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setFilterCategory(cat)}
                  className={`shrink-0 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? cat === 'all' ? 'bg-blue-600 text-white' : `${catColor?.bg} ${catColor?.text} border ${catColor?.border}`
                      : 'text-slate-500 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  {cat === 'all' ? 'All' : CATEGORY_LABELS[cat] ?? cat}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="flex items-center gap-2 text-slate-600 text-xs py-4">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Loading tools…
            </div>
          ) : Object.entries(grouped).length === 0 ? (
            <p className="text-xs text-slate-600 py-4">No tools match your search.</p>
          ) : (
            Object.entries(grouped).map(([cat, catTools]) => (
              <div key={cat}>
                {filterCategory === 'all' && (
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${CATEGORY_COLORS[cat]?.dot ?? 'bg-slate-500'}`} />
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                      {CATEGORY_LABELS[cat] ?? cat}
                    </p>
                  </div>
                )}
                <div className="space-y-2">
                  {catTools.map((tool) => (
                    <ToolCard
                      key={tool.id}
                      tool={tool}
                      selected={selectedTool?.id === tool.id}
                      onClick={() => { setSelectedTool(tool); setResult(null); setExecError(''); }}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="p-3 border-t border-white/6">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-600">{tools.length} tools registered</span>
            <button onClick={load} disabled={loading} className="p-1.5 rounded-lg hover:bg-white/6 text-slate-600 hover:text-white transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {!selectedTool ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="w-12 h-12 rounded-2xl bg-slate-800 border border-white/8 flex items-center justify-center mb-3">
              <Wrench className="w-6 h-6 text-slate-600" />
            </div>
            <p className="text-slate-400 font-medium">Select a tool</p>
            <p className="text-sm text-slate-600 mt-1">Choose a tool from the list to view its schema and test it.</p>
          </div>
        ) : (
          <div className="p-6 max-w-3xl">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-slate-800 border border-white/8 flex items-center justify-center text-xl shrink-0">
                {TOOL_ICONS[selectedTool.name] ?? '🔧'}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-lg font-semibold text-white">{selectedTool.display_name}</h2>
                  <span className={`text-xs px-2 py-0.5 rounded-md border ${CATEGORY_COLORS[selectedTool.category]?.bg} ${CATEGORY_COLORS[selectedTool.category]?.text} ${CATEGORY_COLORS[selectedTool.category]?.border}`}>
                    {CATEGORY_LABELS[selectedTool.category] ?? selectedTool.category}
                  </span>
                </div>
                <p className="text-sm text-slate-400 mt-1">{selectedTool.description}</p>
                <div className="flex items-center gap-2 mt-2">
                  <code className="text-xs bg-slate-800 border border-white/8 rounded px-2 py-0.5 text-slate-400">{selectedTool.name}</code>
                  <span className="text-xs text-slate-600">handler: <code className="text-slate-500">{selectedTool.handler_name}</code></span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1 mb-5 bg-slate-800/40 border border-white/6 rounded-xl p-1 w-fit">
              {(['schema', 'test'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${activeTab === tab ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-500 hover:text-white'}`}
                >
                  {tab === 'schema' ? <Code2 className="w-3.5 h-3.5" /> : <Zap className="w-3.5 h-3.5" />}
                  {tab === 'schema' ? 'Schema' : 'Test'}
                </button>
              ))}
            </div>

            {activeTab === 'schema' && (
              <div className="space-y-5">
                <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-4">Parameters</h3>
                  <SchemaViewer schema={selectedTool.input_schema} />
                </div>

                <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-3">Raw Schema</h3>
                  <pre className="text-xs text-slate-400 font-mono bg-slate-800/60 border border-white/6 rounded-xl p-4 overflow-x-auto whitespace-pre leading-relaxed">
                    {JSON.stringify(selectedTool.input_schema, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {activeTab === 'test' && (
              <div className="space-y-5">
                <div className="bg-slate-900/60 border border-white/8 rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-white">Execute Tool</h3>
                    <button
                      onClick={() => setShowContext((s) => !s)}
                      className="text-xs text-slate-600 hover:text-slate-400 transition-colors flex items-center gap-1"
                    >
                      <Hash className="w-3 h-3" />
                      {showContext ? 'Hide context' : 'Add context'}
                    </button>
                  </div>

                  {showContext && (
                    <div className="mb-4">
                      <label className="block text-xs text-slate-500 mb-1.5">Ticket ID (optional context)</label>
                      <input
                        type="text"
                        value={contextTicketId}
                        onChange={(e) => setContextTicketId(e.target.value)}
                        placeholder="Ticket UUID for context-aware tools"
                        className="w-full bg-slate-800 border border-white/8 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-colors"
                      />
                    </div>
                  )}

                  <ToolArgForm
                    tool={selectedTool}
                    onExecute={handleExecute}
                    executing={executing}
                  />
                </div>

                {execError && (
                  <div className="px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400">
                    {execError}
                  </div>
                )}

                {result && !executing && <ResultViewer result={result} />}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
