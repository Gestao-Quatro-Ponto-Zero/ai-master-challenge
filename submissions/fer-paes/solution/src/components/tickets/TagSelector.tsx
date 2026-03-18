import { useState, useEffect, useRef } from 'react';
import { Tag as TagIcon, Plus, X, Check, Loader2 } from 'lucide-react';
import { getTags, createTag, assignTag, removeTag, getTicketTags } from '../../services/tagService';
import type { Tag } from '../../types';

interface TagChipProps {
  tag: Tag;
  onRemove?: () => void;
  size?: 'sm' | 'xs';
}

export function TagChip({ tag, onRemove, size = 'sm' }: TagChipProps) {
  const isXs = size === 'xs';
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-lg font-medium border ${isXs ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs'}`}
      style={{
        backgroundColor: `${tag.color}18`,
        borderColor: `${tag.color}40`,
        color: tag.color,
      }}
    >
      {tag.name}
      {onRemove && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="hover:opacity-70 transition-opacity"
          title={`Remove ${tag.name}`}
        >
          <X className={isXs ? 'w-2 h-2' : 'w-2.5 h-2.5'} />
        </button>
      )}
    </span>
  );
}

const PRESET_COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B',
  '#8B5CF6', '#EC4899', '#06B6D4', '#F97316',
  '#6B7280', '#84CC16',
];

interface TagSelectorProps {
  ticketId: string;
  readonly?: boolean;
}

export default function TagSelector({ ticketId, readonly = false }: TagSelectorProps) {
  const [appliedTags, setAppliedTags] = useState<Tag[]>([]);
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [newName, setNewName] = useState('');
  const [newColor, setNewColor] = useState(PRESET_COLORS[0]);
  const [creatingMode, setCreatingMode] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadData();
  }, [ticketId]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
        setCreatingMode(false);
        setNewName('');
      }
    }
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  async function loadData() {
    setLoading(true);
    try {
      const [applied, all] = await Promise.all([getTicketTags(ticketId), getTags()]);
      setAppliedTags(applied);
      setAllTags(all);
    } finally {
      setLoading(false);
    }
  }

  const appliedIds = new Set(appliedTags.map((t) => t.id));

  async function handleToggle(tag: Tag) {
    if (saving) return;
    setSaving(tag.id);
    try {
      if (appliedIds.has(tag.id)) {
        await removeTag(ticketId, tag.id);
        setAppliedTags((prev) => prev.filter((t) => t.id !== tag.id));
      } else {
        await assignTag(ticketId, tag.id);
        setAppliedTags((prev) => [...prev, tag]);
      }
    } finally {
      setSaving(null);
    }
  }

  async function handleRemove(tag: Tag) {
    if (saving) return;
    setSaving(tag.id);
    try {
      await removeTag(ticketId, tag.id);
      setAppliedTags((prev) => prev.filter((t) => t.id !== tag.id));
    } finally {
      setSaving(null);
    }
  }

  async function handleCreate() {
    const name = newName.trim().toLowerCase();
    if (!name) return;
    setCreateLoading(true);
    try {
      const tag = await createTag(name, newColor);
      setAllTags((prev) => [...prev, tag].sort((a, b) => a.name.localeCompare(b.name)));
      await assignTag(ticketId, tag.id);
      setAppliedTags((prev) => [...prev, tag]);
      setNewName('');
      setNewColor(PRESET_COLORS[0]);
      setCreatingMode(false);
    } finally {
      setCreateLoading(false);
    }
  }

  return (
    <section>
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
        <TagIcon className="w-3 h-3" />
        Tags
      </p>

      {loading ? (
        <div className="flex gap-1.5">
          {[1, 2].map((i) => (
            <div key={i} className="h-5 w-14 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {appliedTags.map((tag) => (
            <TagChip
              key={tag.id}
              tag={tag}
              onRemove={readonly ? undefined : () => handleRemove(tag)}
            />
          ))}

          {!readonly && (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setOpen((v) => !v)}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-medium text-gray-400 border border-dashed border-gray-300 hover:border-gray-400 hover:text-gray-600 transition-colors"
              >
                <Plus className="w-2.5 h-2.5" />
                Add tag
              </button>

              {open && (
                <div className="absolute left-0 top-full mt-1.5 z-30 bg-white border border-gray-100 rounded-xl shadow-xl w-52 overflow-hidden">
                  {!creatingMode ? (
                    <>
                      <div className="max-h-48 overflow-y-auto py-1">
                        {allTags.length === 0 && (
                          <p className="text-xs text-gray-400 px-3 py-2 italic">No tags yet</p>
                        )}
                        {allTags.map((tag) => {
                          const active = appliedIds.has(tag.id);
                          return (
                            <button
                              key={tag.id}
                              disabled={saving === tag.id}
                              onClick={() => handleToggle(tag)}
                              className="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-gray-50 transition-colors"
                            >
                              {saving === tag.id ? (
                                <Loader2 className="w-3 h-3 animate-spin text-gray-400 shrink-0" />
                              ) : active ? (
                                <Check className="w-3 h-3 text-emerald-500 shrink-0" />
                              ) : (
                                <span className="w-3 h-3 shrink-0" />
                              )}
                              <span
                                className="text-xs font-medium"
                                style={{ color: tag.color }}
                              >
                                {tag.name}
                              </span>
                              <span
                                className="ml-auto w-2.5 h-2.5 rounded-full shrink-0"
                                style={{ backgroundColor: tag.color }}
                              />
                            </button>
                          );
                        })}
                      </div>
                      <div className="border-t border-gray-100">
                        <button
                          onClick={() => setCreatingMode(true)}
                          className="w-full flex items-center gap-2 px-3 py-2.5 text-xs text-gray-500 hover:bg-gray-50 transition-colors font-medium"
                        >
                          <Plus className="w-3 h-3" />
                          Create new tag
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="p-3 space-y-3">
                      <p className="text-xs font-semibold text-gray-700">New tag</p>
                      <input
                        autoFocus
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleCreate(); if (e.key === 'Escape') setCreatingMode(false); }}
                        placeholder="tag name…"
                        className="w-full px-2.5 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200"
                      />
                      <div>
                        <p className="text-[10px] text-gray-400 mb-1.5">Color</p>
                        <div className="flex flex-wrap gap-1.5">
                          {PRESET_COLORS.map((c) => (
                            <button
                              key={c}
                              onClick={() => setNewColor(c)}
                              className={`w-5 h-5 rounded-full transition-transform ${newColor === c ? 'ring-2 ring-offset-1 ring-gray-400 scale-110' : 'hover:scale-110'}`}
                              style={{ backgroundColor: c }}
                            />
                          ))}
                        </div>
                      </div>
                      <div className="flex gap-2 pt-1">
                        <button
                          onClick={() => { setCreatingMode(false); setNewName(''); }}
                          className="flex-1 px-2 py-1.5 text-xs rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          disabled={!newName.trim() || createLoading}
                          onClick={handleCreate}
                          className="flex-1 px-2 py-1.5 text-xs rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-1"
                        >
                          {createLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Create'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
