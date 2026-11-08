import type { Confidence, DisagreeReason, FeedbackKind, SortKey, TabKey } from '../api/types';

export const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'score', label: 'Prioridade' },
  { value: 'expected_value', label: 'Valor esperado' },
  { value: 'age_days', label: 'Tempo no funil' },
];

/** Rótulos de apresentação das confianças que a API devolve. */
export const CONFIDENCE_LABELS: Record<Confidence, string> = { low: 'Baixa', medium: 'Média', high: 'Alta' };

export const PAGE_SIZE_OPTIONS = [5, 10, 25];
export const CAP_OPTIONS = [3, 5, 8, 10];
export const SNOOZE_OPTIONS = [1, 7, 30];

export const TAB_DEFS: { key: TabKey; label: string }[] = [
  { key: 'focus', label: 'Foco da semana' },
  { key: 'decide', label: 'Decidir agora' },
  { key: 'follow', label: 'Baixa prioridade' },
  { key: 'prospecting', label: 'Prospecção' },
  { key: 'review', label: 'A revisar' },
];

export const ROLE_LABELS: Record<string, string> = {
  seller: 'Vendedor',
  manager: 'Manager',
  revops: 'RevOps',
};

export const FEEDBACK_MESSAGES: Record<FeedbackKind, string> = {
  act: 'Atividade registrada no deal (exemplo).',
  disagree: 'Registrado: você discorda do score. Isso ajuda a melhorar o modelo.',
  ignore: 'Registrado: deal ignorado nesta semana.',
};

export const FEEDBACK_LABELS: Record<FeedbackKind, string> = {
  act: 'Atividade registrada',
  disagree: 'Discordou da prioridade',
  ignore: 'Ignorou o deal',
};

export const DISAGREE_REASONS: { value: DisagreeReason; label: string }[] = [
  { value: 'value', label: 'O valor ou o produto está errado' },
  { value: 'stalled', label: 'O cliente parou de responder' },
  { value: 'closed', label: 'O deal já fechou ou foi perdido' },
  { value: 'other', label: 'Outro motivo' },
];
