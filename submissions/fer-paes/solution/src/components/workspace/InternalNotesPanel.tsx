import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Loader2, StickyNote, Send, Pencil, Trash2, Check, X, AtSign,
} from 'lucide-react';
import { supabase } from '../../lib/supabaseClient';
import {
  createInternalNote, getTicketNotes, updateNote, deleteNote,
  getOperatorsForMentions,
  type InternalNote, type MentionCandidate,
} from '../../services/collaborationService';

interface Props {
  ticketId: string;
  userId:   string;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs  < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function Avatar({ name }: { name: string }) {
  const initials = name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase() || '?';
  const colors = ['bg-blue-600', 'bg-emerald-600', 'bg-amber-600', 'bg-rose-600', 'bg-slate-600'];
  const color  = colors[(initials.charCodeAt(0) ?? 0) % colors.length];
  return (
    <div className={`w-6 h-6 rounded-full ${color} flex items-center justify-center shrink-0 text-xs font-semibold text-white`}>
      {initials}
    </div>
  );
}

function renderNoteText(note: string, mentions: InternalNote['mentions']): React.ReactNode[] {
  const mentionHandles = new Set(
    mentions
      .map((m) => m.operator?.full_name?.toLowerCase().replace(/\s+/g, '') ?? null)
      .filter(Boolean) as string[],
  );

  const parts = note.split(/(@\w+)/g);
  return parts.map((part, i) => {
    if (part.startsWith('@')) {
      const handle = part.slice(1).toLowerCase();
      const isReal = [...mentionHandles].some((h) => h.startsWith(handle) || handle.startsWith(h));
      if (isReal) {
        return (
          <span key={i} className="inline-flex items-center gap-0.5 text-blue-400 font-medium bg-blue-500/10 rounded px-0.5">
            {part}
          </span>
        );
      }
    }
    return <span key={i}>{part}</span>;
  });
}

interface NoteItemProps {
  note:        InternalNote;
  isAuthor:    boolean;
  onEdit:      (id: string, text: string) => void;
  onDelete:    (id: string) => void;
}

function NoteItem({ note, isAuthor, onEdit, onDelete }: NoteItemProps) {
  const [editing,  setEditing]  = useState(false);
  const [editText, setEditText] = useState(note.note);
  const [saving,   setSaving]   = useState(false);

  const authorName = note.author?.full_name || note.author?.email || 'Unknown';
  const isEdited   = note.updated_at !== note.created_at;

  async function handleSave() {
    if (!editText.trim()) return;
    setSaving(true);
    try {
      await onEdit(note.id, editText.trim());
      setEditing(false);
    } finally { setSaving(false); }
  }

  function handleCancel() {
    setEditText(note.note);
    setEditing(false);
  }

  return (
    <div className="group flex gap-2.5 px-4 py-3 hover:bg-white/2 transition-colors">
      <Avatar name={authorName} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300">{authorName}</span>
            {isEdited && <span className="text-xs text-slate-700 italic">edited</span>}
          </div>
          <div className="flex items-center gap-1">
            <span className="text-xs text-slate-700">{timeAgo(note.created_at)}</span>
            {isAuthor && !editing && (
              <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity ml-1">
                <button
                  onClick={() => setEditing(true)}
                  className="p-1 rounded-lg text-slate-600 hover:text-slate-300 hover:bg-white/8 transition-colors"
                >
                  <Pencil className="w-3 h-3" />
                </button>
                <button
                  onClick={() => onDelete(note.id)}
                  className="p-1 rounded-lg text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>
        </div>

        {editing ? (
          <div className="space-y-2">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              rows={3}
              autoFocus
              className="w-full bg-slate-800/80 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/40 resize-none transition-colors"
            />
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleSave}
                disabled={!editText.trim() || saving}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium hover:bg-blue-500 disabled:opacity-40 transition-colors"
              >
                {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                Save
              </button>
              <button
                onClick={handleCancel}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-slate-500 text-xs hover:text-white hover:bg-white/8 transition-colors"
              >
                <X className="w-3 h-3" />
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-wrap break-words">
            {renderNoteText(note.note, note.mentions)}
          </p>
        )}

        {note.mentions.length > 0 && !editing && (
          <div className="flex items-center flex-wrap gap-1 mt-1.5">
            {note.mentions.map((m) => (
              <span key={m.id} className="text-xs text-blue-500/70 bg-blue-500/8 border border-blue-500/15 rounded-full px-2 py-0.5">
                @{m.operator?.full_name?.split(' ')[0] ?? 'unknown'}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface MentionDropdownProps {
  candidates: MentionCandidate[];
  partial:    string;
  onSelect:   (candidate: MentionCandidate) => void;
  anchorRef:  React.RefObject<HTMLTextAreaElement>;
}

function MentionDropdown({ candidates, partial, onSelect }: MentionDropdownProps) {
  const filtered = candidates.filter((c) =>
    c.handle.startsWith(partial.toLowerCase()) ||
    c.full_name.toLowerCase().startsWith(partial.toLowerCase()),
  ).slice(0, 6);

  if (filtered.length === 0) return null;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-1 bg-slate-800 border border-white/10 rounded-xl overflow-hidden shadow-2xl z-10 max-h-48 overflow-y-auto">
      <div className="px-3 py-1.5 border-b border-white/5">
        <p className="text-xs text-slate-600 flex items-center gap-1">
          <AtSign className="w-3 h-3" />
          Mention a colleague
        </p>
      </div>
      {filtered.map((c) => (
        <button
          key={c.id}
          onMouseDown={(e) => { e.preventDefault(); onSelect(c); }}
          className="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-white/5 transition-colors text-left"
        >
          <div className="w-6 h-6 rounded-full bg-blue-600/20 flex items-center justify-center text-xs font-semibold text-blue-400 shrink-0">
            {(c.full_name[0] ?? '?').toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-300 truncate">{c.full_name || c.email}</p>
            <p className="text-xs text-slate-600 truncate">@{c.handle}</p>
          </div>
        </button>
      ))}
    </div>
  );
}

interface NoteComposerProps {
  candidates: MentionCandidate[];
  disabled:   boolean;
  onSubmit:   (text: string) => Promise<void>;
}

function NoteComposer({ candidates, disabled, onSubmit }: NoteComposerProps) {
  const [text,        setText]        = useState('');
  const [submitting,  setSubmitting]  = useState(false);
  const [mentionPartial, setMentionPartial] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const val    = e.target.value;
    const cursor = e.target.selectionStart ?? val.length;
    const before = val.slice(0, cursor);
    const match  = before.match(/@(\w*)$/);

    setText(val);
    setMentionPartial(match ? match[1] : null);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Escape') { setMentionPartial(null); return; }
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function insertMention(candidate: MentionCandidate) {
    const el     = textareaRef.current;
    if (!el) return;
    const cursor = el.selectionStart ?? text.length;
    const before = text.slice(0, cursor);
    const after  = text.slice(cursor);
    const replaced = before.replace(/@(\w*)$/, `@${candidate.handle} `);
    setText(replaced + after);
    setMentionPartial(null);
    setTimeout(() => {
      el.focus();
      const pos = replaced.length;
      el.setSelectionRange(pos, pos);
    }, 0);
  }

  async function handleSubmit() {
    if (!text.trim() || submitting || disabled) return;
    setSubmitting(true);
    try {
      await onSubmit(text.trim());
      setText('');
      setMentionPartial(null);
    } finally { setSubmitting(false); }
  }

  return (
    <div className="px-4 py-3 border-t border-white/5 shrink-0">
      <div className="relative">
        {mentionPartial !== null && (
          <MentionDropdown
            candidates={candidates}
            partial={mentionPartial}
            onSelect={insertMention}
            anchorRef={textareaRef}
          />
        )}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Write an internal note… Use @name to mention a colleague"
          rows={3}
          className="w-full bg-slate-800/60 border border-white/8 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/30 resize-none transition-colors disabled:opacity-40"
        />
      </div>
      <div className="flex items-center justify-between mt-2">
        <p className="text-xs text-slate-700">
          {text.length > 0 ? `Cmd+Enter to submit · @name to mention` : '@name to mention a colleague'}
        </p>
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || submitting || disabled}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/90 text-slate-950 text-xs font-semibold hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {submitting
            ? <Loader2 className="w-3 h-3 animate-spin" />
            : <Send className="w-3 h-3" />
          }
          {submitting ? 'Adding…' : 'Add Note'}
        </button>
      </div>
    </div>
  );
}

export default function InternalNotesPanel({ ticketId, userId }: Props) {
  const [notes,       setNotes]      = useState<InternalNote[]>([]);
  const [candidates,  setCandidates] = useState<MentionCandidate[]>([]);
  const [operatorId,  setOperatorId] = useState<string | null>(null);
  const [loading,     setLoading]    = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadNotes = useCallback(async () => {
    try {
      const data = await getTicketNotes(ticketId);
      setNotes(data);
    } catch { } finally { setLoading(false); }
  }, [ticketId]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [cands] = await Promise.all([
        getOperatorsForMentions(),
        loadNotes(),
      ]);
      setCandidates(cands);

      if (userId) {
        const { data: op } = await supabase
          .from('operators')
          .select('id')
          .eq('user_id', userId)
          .maybeSingle();
        setOperatorId(op?.id ?? null);
      }
    })();
  }, [ticketId, userId, loadNotes]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [notes]);

  async function handleSubmit(text: string) {
    if (!operatorId) return;
    const note = await createInternalNote(ticketId, operatorId, text);
    setNotes((prev) => [...prev, note]);
  }

  async function handleEdit(id: string, text: string) {
    await updateNote(id, text);
    await loadNotes();
  }

  async function handleDelete(id: string) {
    await deleteNote(id);
    setNotes((prev) => prev.filter((n) => n.id !== id));
  }

  return (
    <div className="flex flex-col h-full bg-slate-950 min-w-0">
      {/* Notes list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-4 h-4 animate-spin text-slate-700" />
          </div>
        ) : notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 py-16 px-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/15 flex items-center justify-center">
              <StickyNote className="w-5 h-5 text-amber-500/60" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">No internal notes yet</p>
              <p className="text-xs text-slate-700 mt-1">
                Add a note to share context with your team. Notes are never visible to customers.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="px-4 pt-3 pb-1">
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full bg-amber-500/60" />
                <p className="text-xs text-slate-700">
                  Internal notes — not visible to customers
                </p>
              </div>
            </div>
            {notes.map((note) => (
              <NoteItem
                key={note.id}
                note={note}
                isAuthor={note.author?.user_id === userId}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      <NoteComposer
        candidates={candidates}
        disabled={!operatorId}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
