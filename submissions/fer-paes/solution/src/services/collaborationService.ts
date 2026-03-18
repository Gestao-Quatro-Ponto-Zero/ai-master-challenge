import { supabase } from '../lib/supabaseClient';

export interface NoteAuthor {
  id:        string;
  user_id:   string;
  full_name: string;
  email:     string;
}

export interface MentionedOperator {
  id:        string;
  user_id:   string;
  full_name: string;
  email:     string;
}

export interface NoteMention {
  id:                    string;
  note_id:               string;
  mentioned_operator_id: string;
  operator:              MentionedOperator | null;
  created_at:            string;
}

export interface InternalNote {
  id:          string;
  ticket_id:   string;
  operator_id: string;
  note:        string;
  created_at:  string;
  updated_at:  string;
  author:      NoteAuthor | null;
  mentions:    NoteMention[];
}

export interface MentionCandidate {
  id:        string;
  user_id:   string;
  full_name: string;
  email:     string;
  handle:    string;
}

export async function getOperatorsForMentions(): Promise<MentionCandidate[]> {
  const { data, error } = await supabase
    .from('operators')
    .select(`
      id, user_id,
      profile:profiles!operators_user_id_fkey(full_name, email)
    `)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);

  return ((data ?? []) as unknown[]).map((raw) => {
    const r       = raw as Record<string, unknown>;
    const profArr = r.profile as { full_name?: string; email?: string }[] | null;
    const prof    = Array.isArray(profArr) ? profArr[0] : profArr;
    const name    = prof?.full_name ?? '';
    const email   = prof?.email     ?? '';
    const handle  = name
      ? name.toLowerCase().replace(/\s+/g, '')
      : email.split('@')[0].toLowerCase();
    return {
      id:        r.id        as string,
      user_id:   r.user_id   as string,
      full_name: name,
      email,
      handle,
    };
  });
}

export function parseMentionHandles(note: string): string[] {
  const matches = note.match(/@(\w+)/g) ?? [];
  return [...new Set(matches.map((m) => m.slice(1).toLowerCase()))];
}

async function resolveMentions(
  note:       string,
  candidates: MentionCandidate[],
): Promise<string[]> {
  const handles = parseMentionHandles(note);
  if (handles.length === 0) return [];

  const operatorIds: string[] = [];
  for (const handle of handles) {
    const op = candidates.find((c) => c.handle.startsWith(handle) || handle.startsWith(c.handle));
    if (op) operatorIds.push(op.id);
  }
  return [...new Set(operatorIds)];
}

export async function createInternalNote(
  ticketId:   string,
  operatorId: string,
  note:       string,
): Promise<InternalNote> {
  const { data, error } = await supabase
    .from('internal_notes')
    .insert({ ticket_id: ticketId, operator_id: operatorId, note })
    .select()
    .single();

  if (error) throw new Error(error.message);

  const candidates = await getOperatorsForMentions();
  const mentionIds = await resolveMentions(note, candidates);

  if (mentionIds.length > 0) {
    await supabase.from('internal_note_mentions').insert(
      mentionIds.map((id) => ({ note_id: data.id, mentioned_operator_id: id })),
    );
  }

  return enrichNote(data, candidates);
}

export async function getTicketNotes(ticketId: string): Promise<InternalNote[]> {
  const { data: notes, error } = await supabase
    .from('internal_notes')
    .select('*')
    .eq('ticket_id', ticketId)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);
  if (!notes || notes.length === 0) return [];

  const candidates = await getOperatorsForMentions();

  const noteIds = notes.map((n) => n.id);
  const { data: mentions } = await supabase
    .from('internal_note_mentions')
    .select('*')
    .in('note_id', noteIds);

  const mentionsByNote: Record<string, string[]> = {};
  (mentions ?? []).forEach((m) => {
    if (!mentionsByNote[m.note_id]) mentionsByNote[m.note_id] = [];
    mentionsByNote[m.note_id].push(m.mentioned_operator_id);
  });

  return notes.map((n) => {
    const noteM = (mentionsByNote[n.id] ?? []).map((opId) => {
      const op = candidates.find((c) => c.id === opId) ?? null;
      return {
        id:                    `${n.id}_${opId}`,
        note_id:               n.id,
        mentioned_operator_id: opId,
        operator:              op ? { id: op.id, user_id: op.user_id, full_name: op.full_name, email: op.email } : null,
        created_at:            n.created_at,
      } as NoteMention;
    });

    const author = candidates.find((c) => c.id === n.operator_id) ?? null;

    return {
      ...n,
      author: author ? { id: author.id, user_id: author.user_id, full_name: author.full_name, email: author.email } : null,
      mentions: noteM,
    } as InternalNote;
  });
}

export async function updateNote(
  noteId:     string,
  note:       string,
): Promise<void> {
  const now = new Date().toISOString();

  const { error } = await supabase
    .from('internal_notes')
    .update({ note, updated_at: now })
    .eq('id', noteId);

  if (error) throw new Error(error.message);

  await supabase.from('internal_note_mentions').delete().eq('note_id', noteId);

  const candidates = await getOperatorsForMentions();
  const mentionIds = await resolveMentions(note, candidates);

  if (mentionIds.length > 0) {
    await supabase.from('internal_note_mentions').insert(
      mentionIds.map((id) => ({ note_id: noteId, mentioned_operator_id: id })),
    );
  }
}

export async function deleteNote(noteId: string): Promise<void> {
  const { error } = await supabase
    .from('internal_notes')
    .delete()
    .eq('id', noteId);

  if (error) throw new Error(error.message);
}

function enrichNote(raw: Record<string, unknown>, candidates: MentionCandidate[]): InternalNote {
  const author = candidates.find((c) => c.id === raw.operator_id) ?? null;
  return {
    ...(raw as unknown as InternalNote),
    author: author
      ? { id: author.id, user_id: author.user_id, full_name: author.full_name, email: author.email }
      : null,
    mentions: [],
  };
}
