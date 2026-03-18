import { useState } from 'react';
import { Plus, Pencil, Trash2, Check, X, Database, Globe, FileText, BookOpen, Loader2 } from 'lucide-react';
import {
  listSources, createSource, updateSource, deleteSource,
  type KnowledgeSource, type SourceType,
} from '../../services/knowledgeService';

const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  manual_upload: 'Manual Upload',
  web_import:    'Web Import',
  api_import:    'API Import',
  notion:        'Notion',
  google_docs:   'Google Docs',
  faq:           'FAQ',
};

const SOURCE_TYPE_ICONS: Record<SourceType, React.ComponentType<{ className?: string }>> = {
  manual_upload: FileText,
  web_import:    Globe,
  api_import:    Database,
  notion:        BookOpen,
  google_docs:   FileText,
  faq:           BookOpen,
};

interface Props {
  sources: KnowledgeSource[];
  onRefresh: () => void;
}

interface FormState {
  name: string;
  description: string;
  source_type: SourceType;
}

const EMPTY_FORM: FormState = { name: '', description: '', source_type: 'manual_upload' };

export default function SourceManager({ sources, onRefresh }: Props) {
  const [showCreate, setShowCreate] = useState(false);
  const [editId,     setEditId]     = useState<string | null>(null);
  const [form,       setForm]       = useState<FormState>(EMPTY_FORM);
  const [saving,     setSaving]     = useState(false);
  const [deleting,   setDeleting]   = useState<string | null>(null);
  const [error,      setError]      = useState('');

  function startCreate() { setForm(EMPTY_FORM); setError(''); setShowCreate(true); setEditId(null); }
  function startEdit(s: KnowledgeSource) {
    setForm({ name: s.name, description: s.description, source_type: s.source_type });
    setError('');
    setEditId(s.id);
    setShowCreate(false);
  }
  function cancel() { setShowCreate(false); setEditId(null); setForm(EMPTY_FORM); setError(''); }

  async function save() {
    if (!form.name.trim()) { setError('Name is required'); return; }
    setSaving(true); setError('');
    try {
      if (editId) {
        await updateSource(editId, { name: form.name, description: form.description, source_type: form.source_type });
      } else {
        await createSource({ name: form.name, description: form.description, source_type: form.source_type });
      }
      onRefresh();
      cancel();
    } catch (e) { setError((e as Error).message); } finally { setSaving(false); }
  }

  async function remove(id: string) {
    setDeleting(id);
    try { await deleteSource(id); onRefresh(); }
    catch (e) { alert((e as Error).message); }
    finally { setDeleting(null); }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{sources.length} source{sources.length !== 1 ? 's' : ''} configured</p>
        <button onClick={startCreate}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm text-white font-medium transition-colors">
          <Plus className="w-3.5 h-3.5" />New Source
        </button>
      </div>

      {(showCreate || editId) && (
        <div className="bg-slate-800/60 border border-white/10 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">{editId ? 'Edit Source' : 'New Source'}</h3>
          {error && <p className="text-xs text-rose-400">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1.5">Name *</label>
              <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Help Center Articles"
                className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1.5">Type</label>
              <select value={form.source_type} onChange={(e) => setForm((f) => ({ ...f, source_type: e.target.value as SourceType }))}
                className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40">
                {(Object.keys(SOURCE_TYPE_LABELS) as SourceType[]).map((t) => (
                  <option key={t} value={t}>{SOURCE_TYPE_LABELS[t]}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">Description</label>
            <input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Optional description"
              className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={cancel} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">Cancel</button>
            <button onClick={save} disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl text-sm text-white font-medium transition-colors">
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
              {editId ? 'Save Changes' : 'Create Source'}
            </button>
          </div>
        </div>
      )}

      {sources.length === 0 && !showCreate ? (
        <div className="flex flex-col items-center justify-center py-14 bg-slate-800/20 border border-white/6 rounded-2xl text-center">
          <Database className="w-10 h-10 text-slate-700 mb-3" />
          <p className="text-sm text-slate-500 mb-1">No sources yet</p>
          <p className="text-xs text-slate-600">Create a source to organise where your knowledge comes from</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {sources.map((s) => {
            const Icon = SOURCE_TYPE_ICONS[s.source_type];
            return (
              <div key={s.id} className={`bg-slate-800/40 border rounded-2xl p-4 transition-colors ${editId === s.id ? 'border-blue-500/30' : 'border-white/6'}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-slate-700/60 border border-white/8 flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4 text-slate-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{s.name}</p>
                      <p className="text-xs text-slate-500">{SOURCE_TYPE_LABELS[s.source_type]}</p>
                    </div>
                  </div>
                  <div className="flex gap-1 ml-2">
                    <button onClick={() => startEdit(s)} className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => remove(s.id)} disabled={deleting === s.id}
                      className="p-1.5 rounded-lg text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 transition-colors">
                      {deleting === s.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                {s.description && <p className="text-xs text-slate-600 mt-2 ml-12">{s.description}</p>}
                <div className="flex items-center gap-2 mt-3 ml-12">
                  <span className={`w-1.5 h-1.5 rounded-full ${s.is_active ? 'bg-emerald-500' : 'bg-slate-600'}`} />
                  <span className="text-xs text-slate-600">{s.is_active ? 'Active' : 'Inactive'}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
