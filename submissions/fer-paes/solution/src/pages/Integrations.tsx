import { useState, useEffect, useCallback } from 'react';
import {
  Key, Plus, RefreshCw, ToggleLeft, ToggleRight, Trash2, Copy, Check,
  Activity, Clock, AlertCircle, CheckCircle2, Eye, EyeOff, X, Shield,
  Zap, ChevronDown, ChevronUp,
} from 'lucide-react';
import {
  getApiKeys, createApiKey, toggleApiKey, deleteApiKey, getIntegrationLogs,
  AVAILABLE_SCOPES, CHANNEL_TYPES,
  type ApiKey, type ApiKeyCreated, type IntegrationLog, type CreateApiKeyPayload,
} from '../services/integrationService';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <button
      onClick={copy}
      className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
      title="Copiar"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

function CreateKeyModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (key: ApiKeyCreated) => void;
}) {
  const [name, setName] = useState('');
  const [scopes, setScopes] = useState<string[]>(['channel:ingest']);
  const [channelType, setChannelType] = useState('');
  const [rateLimit, setRateLimit] = useState(60);
  const [expiresAt, setExpiresAt] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function toggleScope(scope: string) {
    setScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope],
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError('Informe um nome para a chave.'); return; }
    if (scopes.length === 0) { setError('Selecione ao menos um escopo.'); return; }
    setSaving(true);
    setError('');
    try {
      const payload: CreateApiKeyPayload = {
        name: name.trim(),
        scopes,
        channel_type: channelType || null,
        rate_limit_per_minute: rateLimit,
        expires_at: expiresAt || null,
      };
      const created = await createApiKey(payload);
      onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar chave.');
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-slate-900 border border-white/10 rounded-2xl shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
              <Key className="w-4 h-4 text-emerald-400" />
            </div>
            <h2 className="text-white font-semibold">Nova Chave de API</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <div className="px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Nome da Integração</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Chat do Site, Bot WhatsApp..."
              className="w-full px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Canal (opcional)</label>
            <select
              value={channelType}
              onChange={(e) => setChannelType(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
            >
              <option value="">Qualquer canal</option>
              {CHANNEL_TYPES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">Escopos de Acesso</label>
            <div className="grid grid-cols-2 gap-2">
              {AVAILABLE_SCOPES.map((scope) => {
                const active = scopes.includes(scope.value);
                return (
                  <button
                    key={scope.value}
                    type="button"
                    onClick={() => toggleScope(scope.value)}
                    className={`flex items-start gap-2 p-2.5 rounded-lg border text-left transition-colors ${
                      active
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                        : 'bg-slate-800 border-white/5 text-slate-400 hover:border-white/15'
                    }`}
                  >
                    <div className={`w-3.5 h-3.5 mt-0.5 shrink-0 rounded flex items-center justify-center border ${
                      active ? 'bg-emerald-500 border-emerald-500' : 'border-white/20'
                    }`}>
                      {active && <Check className="w-2.5 h-2.5 text-white" />}
                    </div>
                    <div>
                      <p className="text-xs font-medium leading-none">{scope.label}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">{scope.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Limite (req/min)
              </label>
              <input
                type="number"
                min={1}
                max={1000}
                value={rateLimit}
                onChange={(e) => setRateLimit(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Expira em (opcional)
              </label>
              <input
                type="date"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
            >
              {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
              {saving ? 'Gerando...' : 'Gerar Chave'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function NewKeyRevealModal({
  apiKey,
  onClose,
}: {
  apiKey: ApiKeyCreated;
  onClose: () => void;
}) {
  const [revealed, setRevealed] = useState(true);
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(apiKey.full_key);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-md bg-slate-900 border border-emerald-500/30 rounded-2xl shadow-2xl">
        <div className="px-6 py-5 border-b border-white/5">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <h2 className="text-white font-semibold">Chave criada com sucesso</h2>
          </div>
          <p className="text-amber-400/90 text-xs mt-3 px-3 py-2 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            Copie esta chave agora. Por segurança, ela nao sera exibida novamente.
          </p>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <p className="text-xs text-slate-400 mb-1.5 font-medium">Chave de API</p>
            <div className="flex items-center gap-2 bg-slate-800 border border-white/10 rounded-lg px-3 py-2.5">
              <code className="flex-1 text-xs font-mono text-emerald-300 break-all select-all">
                {revealed ? apiKey.full_key : apiKey.full_key.slice(0, 16) + '•'.repeat(32)}
              </code>
              <button
                onClick={() => setRevealed((v) => !v)}
                className="text-slate-500 hover:text-white transition-colors shrink-0"
              >
                {revealed ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-800/50 rounded-lg px-3 py-2.5">
              <p className="text-slate-500 mb-1">Nome</p>
              <p className="text-white font-medium truncate">{apiKey.name}</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg px-3 py-2.5">
              <p className="text-slate-500 mb-1">Escopos</p>
              <p className="text-white font-medium">{apiKey.scopes.length} escopo(s)</p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={copy}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                copied
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-white'
              }`}
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copiado!' : 'Copiar Chave'}
            </button>
            <button
              onClick={onClose}
              className="flex-1 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
            >
              Entendido
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScopesBadge({ scopes }: { scopes: string[] }) {
  const [expanded, setExpanded] = useState(false);
  if (scopes.length === 0) return <span className="text-slate-600 text-xs">nenhum</span>;
  const display = expanded ? scopes : scopes.slice(0, 2);
  return (
    <div className="flex flex-wrap gap-1 items-center">
      {display.map((s) => (
        <span key={s} className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 text-[10px] font-mono">
          {s}
        </span>
      ))}
      {scopes.length > 2 && (
        <button
          onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v); }}
          className="text-slate-500 hover:text-slate-300 text-[10px] flex items-center gap-0.5"
        >
          {expanded ? (
            <><ChevronUp className="w-3 h-3" /> menos</>
          ) : (
            <><ChevronDown className="w-3 h-3" /> +{scopes.length - 2}</>
          )}
        </button>
      )}
    </div>
  );
}

function LogsPanel({ apiKeyId }: { apiKeyId?: string }) {
  const [logs, setLogs] = useState<IntegrationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getIntegrationLogs(apiKeyId, 50);
      setLogs(result.logs);
      setTotal(result.total);
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [apiKeyId]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-medium text-white">Logs de Integração</span>
          <span className="text-xs text-slate-500">({total} total)</span>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-5 h-5 text-slate-400 animate-spin" />
        </div>
      ) : logs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Activity className="w-8 h-8 text-slate-700 mb-2" />
          <p className="text-slate-500 text-sm">Nenhuma requisição registrada ainda</p>
          <p className="text-slate-600 text-xs mt-1">As chamadas feitas com suas chaves aparecerão aqui</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500 uppercase tracking-wider">Data/Hora</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500 uppercase tracking-wider">Endpoint</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500 uppercase tracking-wider">Chave</th>
                <th className="text-center px-4 py-2.5 text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                <th className="text-right px-4 py-2.5 text-xs font-medium text-slate-500 uppercase tracking-wider">Duração</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-slate-500 uppercase tracking-wider">Erro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs.map((log) => {
                const ok = log.status_code < 400;
                return (
                  <tr key={log.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString('pt-BR', {
                        day: '2-digit', month: '2-digit', year: '2-digit',
                        hour: '2-digit', minute: '2-digit', second: '2-digit',
                      })}
                    </td>
                    <td className="px-4 py-3">
                      <code className="text-xs font-mono text-slate-300">{log.endpoint}</code>
                    </td>
                    <td className="px-4 py-3">
                      <code className="text-xs font-mono text-slate-500">{log.key_prefix ?? '—'}</code>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${
                        ok
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-red-500/10 text-red-400 border-red-500/20'
                      }`}>
                        {ok
                          ? <CheckCircle2 className="w-3 h-3" />
                          : <AlertCircle className="w-3 h-3" />
                        }
                        {log.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-xs text-slate-400 tabular-nums">
                        {log.duration_ms != null ? `${log.duration_ms}ms` : '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-red-400/80 truncate max-w-[200px] block">
                        {log.error_message ?? ''}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function Integrations() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [revealKey, setRevealKey] = useState<ApiKeyCreated | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ApiKey | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState<'keys' | 'logs'>('keys');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setKeys(await getApiKeys());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar chaves.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleToggle(key: ApiKey) {
    setTogglingId(key.id);
    try {
      await toggleApiKey(key.id, !key.is_active);
      setKeys((prev) => prev.map((k) => k.id === key.id ? { ...k, is_active: !k.is_active } : k));
    } finally {
      setTogglingId(null);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteApiKey(deleteTarget.id);
      setKeys((prev) => prev.filter((k) => k.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao excluir chave.');
    } finally {
      setDeleting(false);
    }
  }

  function handleCreated(key: ApiKeyCreated) {
    setShowCreate(false);
    setRevealKey(key);
    setKeys((prev) => [key, ...prev]);
  }

  const channelLabel = (type: string | null) =>
    CHANNEL_TYPES.find((c) => c.value === type)?.label ?? 'Qualquer';

  const activeCount   = keys.filter((k) => k.is_active).length;
  const inactiveCount = keys.filter((k) => !k.is_active).length;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950">
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-600/20 flex items-center justify-center">
              <Zap className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg">Integrações</h1>
              <p className="text-slate-400 text-sm mt-0.5">
                Chaves de API para conectar sites, bots e sistemas externos
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nova Chave
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6">
          {[
            { label: 'Total de Chaves', value: keys.length, color: 'text-white' },
            { label: 'Ativas',          value: activeCount,   color: 'text-emerald-400' },
            { label: 'Inativas',        value: inactiveCount, color: 'text-slate-500' },
          ].map((s) => (
            <div key={s.label} className="bg-slate-900 border border-white/5 rounded-xl px-4 py-3">
              <p className="text-xs text-slate-400 font-medium">{s.label}</p>
              <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="px-8 pt-5 border-b border-white/5">
        <div className="flex gap-1">
          {(['keys', 'logs'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors border-b-2 ${
                activeTab === tab
                  ? 'text-white border-emerald-500'
                  : 'text-slate-500 border-transparent hover:text-slate-300'
              }`}
            >
              {tab === 'keys' ? 'Chaves de API' : 'Logs de Chamadas'}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto px-8 py-6">
        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {activeTab === 'keys' && (
          <>
            {loading ? (
              <div className="flex items-center justify-center py-24">
                <RefreshCw className="w-6 h-6 text-slate-400 animate-spin" />
              </div>
            ) : keys.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-white/5 flex items-center justify-center mb-4">
                  <Key className="w-7 h-7 text-slate-600" />
                </div>
                <p className="text-white font-medium">Nenhuma chave de API criada</p>
                <p className="text-slate-500 text-sm mt-1 max-w-sm">
                  Crie uma chave para conectar seu site, chatbot ou sistema externo a esta plataforma
                </p>
                <button
                  onClick={() => setShowCreate(true)}
                  className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Criar Primeira Chave
                </button>
              </div>
            ) : (
              <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/5">
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Nome</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Prefixo</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Canal</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Escopos</th>
                      <th className="text-center px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Req/min</th>
                      <th className="text-right px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Chamadas</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Último uso</th>
                      <th className="text-center px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {keys.map((key) => (
                      <tr key={key.id} className="hover:bg-white/[0.02] transition-colors group">
                        <td className="px-4 py-3.5">
                          <p className="text-white text-sm font-medium">{key.name}</p>
                          {key.expires_at && (
                            <p className="text-slate-500 text-xs mt-0.5 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              Expira {new Date(key.expires_at).toLocaleDateString('pt-BR')}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-1">
                            <code className="text-xs font-mono text-emerald-300 bg-emerald-500/10 px-2 py-1 rounded">
                              {key.key_prefix}…
                            </code>
                            <CopyButton text={key.key_prefix} />
                          </div>
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="text-slate-300 text-xs">{channelLabel(key.channel_type)}</span>
                        </td>
                        <td className="px-4 py-3.5 max-w-[200px]">
                          <ScopesBadge scopes={key.scopes} />
                        </td>
                        <td className="px-4 py-3.5 text-center">
                          <span className="text-slate-400 text-xs tabular-nums">{key.rate_limit_per_minute}</span>
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <span className="text-slate-400 text-xs tabular-nums">
                            {key.request_count.toLocaleString('pt-BR')}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="text-slate-500 text-xs">
                            {key.last_used_at
                              ? new Date(key.last_used_at).toLocaleDateString('pt-BR')
                              : 'Nunca'}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-center">
                          {key.is_active ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              <CheckCircle2 className="w-3 h-3" />
                              Ativa
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-400 border border-white/10">
                              Inativa
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleToggle(key)}
                              disabled={togglingId === key.id}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors disabled:opacity-50"
                              title={key.is_active ? 'Desativar' : 'Ativar'}
                            >
                              {key.is_active
                                ? <ToggleRight className="w-4 h-4 text-emerald-400" />
                                : <ToggleLeft className="w-4 h-4" />}
                            </button>
                            <button
                              onClick={() => setDeleteTarget(key)}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                              title="Revogar"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {activeTab === 'logs' && <LogsPanel />}
      </div>

      {showCreate && (
        <CreateKeyModal onClose={() => setShowCreate(false)} onCreated={handleCreated} />
      )}

      {revealKey && (
        <NewKeyRevealModal apiKey={revealKey} onClose={() => setRevealKey(null)} />
      )}

      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-slate-900 border border-white/10 rounded-2xl shadow-2xl p-6">
            <h3 className="text-white font-semibold mb-2">Revogar Chave</h3>
            <p className="text-slate-400 text-sm mb-1">
              Revogar <span className="text-white font-medium">{deleteTarget.name}</span>?
            </p>
            <p className="text-slate-500 text-xs mb-6">
              Todos os sistemas que utilizam esta chave perderao o acesso imediatamente.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 py-2.5 rounded-lg border border-white/10 text-slate-400 hover:text-white text-sm font-medium transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
              >
                {deleting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                {deleting ? 'Revogando...' : 'Revogar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
