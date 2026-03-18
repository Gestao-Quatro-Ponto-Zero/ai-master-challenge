import { useState } from 'react';
import { Plus, Pencil, Trash2, Check, ChevronRight, Loader2, FolderOpen, Folder } from 'lucide-react';
import {
  createCategory, updateCategory, deleteCategory,
  type KnowledgeCategory,
} from '../../services/knowledgeService';

interface Props {
  categories: KnowledgeCategory[];
  onRefresh: () => void;
}

interface FormState { name: string; description: string; parent_id: string | null }
const EMPTY_FORM: FormState = { name: '', description: '', parent_id: null };

function buildTree(flat: KnowledgeCategory[]): KnowledgeCategory[] {
  const map = new Map<string, KnowledgeCategory>();
  flat.forEach((c) => map.set(c.id, { ...c, children: [] }));
  const roots: KnowledgeCategory[] = [];
  flat.forEach((c) => {
    const node = map.get(c.id)!;
    if (c.parent_id && map.has(c.parent_id)) {
      map.get(c.parent_id)!.children!.push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

function CategoryRow({
  cat, depth, onEdit, onDelete, deleting,
}: {
  cat: KnowledgeCategory; depth: number;
  onEdit: (c: KnowledgeCategory) => void;
  onDelete: (id: string) => void;
  deleting: string | null;
}) {
  const hasChildren = (cat.children?.length ?? 0) > 0;
  const Icon = hasChildren ? FolderOpen : Folder;
  return (
    <>
      <div className="flex items-center justify-between py-2.5 px-4 hover:bg-white/2 rounded-xl group transition-colors"
        style={{ paddingLeft: `${16 + depth * 20}px` }}>
        <div className="flex items-center gap-2.5">
          {depth > 0 && <ChevronRight className="w-3 h-3 text-slate-700 shrink-0" />}
          <Icon className={`w-4 h-4 shrink-0 ${depth === 0 ? 'text-blue-400' : 'text-slate-500'}`} />
          <div>
            <p className="text-sm text-white">{cat.name}</p>
            {cat.description && <p className="text-xs text-slate-600">{cat.description}</p>}
          </div>
        </div>
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={() => onEdit(cat)} className="p-1.5 rounded-lg text-slate-600 hover:text-white hover:bg-white/8 transition-colors">
            <Pencil className="w-3 h-3" />
          </button>
          <button onClick={() => onDelete(cat.id)} disabled={deleting === cat.id}
            className="p-1.5 rounded-lg text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 transition-colors">
            {deleting === cat.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
          </button>
        </div>
      </div>
      {cat.children?.map((child) => (
        <CategoryRow key={child.id} cat={child} depth={depth + 1} onEdit={onEdit} onDelete={onDelete} deleting={deleting} />
      ))}
    </>
  );
}

export default function CategoryManager({ categories, onRefresh }: Props) {
  const [showForm,  setShowForm]  = useState(false);
  const [editId,    setEditId]    = useState<string | null>(null);
  const [form,      setForm]      = useState<FormState>(EMPTY_FORM);
  const [saving,    setSaving]    = useState(false);
  const [deleting,  setDeleting]  = useState<string | null>(null);
  const [error,     setError]     = useState('');

  const tree = buildTree(categories);

  function startCreate() { setForm(EMPTY_FORM); setError(''); setShowForm(true); setEditId(null); }
  function startEdit(c: KnowledgeCategory) {
    setForm({ name: c.name, description: c.description, parent_id: c.parent_id });
    setError(''); setEditId(c.id); setShowForm(true);
  }
  function cancel() { setShowForm(false); setEditId(null); setForm(EMPTY_FORM); setError(''); }

  async function save() {
    if (!form.name.trim()) { setError('Name is required'); return; }
    setSaving(true); setError('');
    try {
      if (editId) {
        await updateCategory(editId, { name: form.name, description: form.description, parent_id: form.parent_id });
      } else {
        await createCategory({ name: form.name, description: form.description, parent_id: form.parent_id });
      }
      onRefresh(); cancel();
    } catch (e) { setError((e as Error).message); } finally { setSaving(false); }
  }

  async function remove(id: string) {
    if (!confirm('Delete this category? Documents in it will become uncategorised.')) return;
    setDeleting(id);
    try { await deleteCategory(id); onRefresh(); }
    catch (e) { alert((e as Error).message); }
    finally { setDeleting(null); }
  }

  const topLevelCats = categories.filter((c) => !c.parent_id);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{categories.length} categor{categories.length !== 1 ? 'ies' : 'y'}</p>
        <button onClick={startCreate}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm text-white font-medium transition-colors">
          <Plus className="w-3.5 h-3.5" />New Category
        </button>
      </div>

      {showForm && (
        <div className="bg-slate-800/60 border border-white/10 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">{editId ? 'Edit Category' : 'New Category'}</h3>
          {error && <p className="text-xs text-rose-400">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1.5">Name *</label>
              <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Billing"
                className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40" />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1.5">Parent Category</label>
              <select value={form.parent_id ?? ''} onChange={(e) => setForm((f) => ({ ...f, parent_id: e.target.value || null }))}
                className="w-full bg-slate-900/60 border border-white/8 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40">
                <option value="">— Top Level —</option>
                {topLevelCats.filter((c) => c.id !== editId).map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
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
              {editId ? 'Save Changes' : 'Create Category'}
            </button>
          </div>
        </div>
      )}

      {tree.length === 0 && !showForm ? (
        <div className="flex flex-col items-center justify-center py-14 bg-slate-800/20 border border-white/6 rounded-2xl text-center">
          <FolderOpen className="w-10 h-10 text-slate-700 mb-3" />
          <p className="text-sm text-slate-500 mb-1">No categories yet</p>
          <p className="text-xs text-slate-600">Categories help organise knowledge by topic or domain</p>
        </div>
      ) : (
        <div className="bg-slate-900/40 border border-white/6 rounded-2xl py-2">
          {tree.map((cat) => (
            <CategoryRow key={cat.id} cat={cat} depth={0} onEdit={startEdit} onDelete={remove} deleting={deleting} />
          ))}
        </div>
      )}
    </div>
  );
}
