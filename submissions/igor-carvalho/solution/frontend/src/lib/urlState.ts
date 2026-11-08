import type { ListTab, PriorityLevel, SortKey } from '../api/types';
import { CAP_OPTIONS, PAGE_SIZE_OPTIONS, SORT_OPTIONS } from './constants';

/** Tamanho máximo de texto aceito vindo da URL (não é regra de negócio). */
const MAX_PARAM_LENGTH = 100;

export type View = 'today' | 'all';

/** Estado da tela que vai para a URL (critério F1: restaura ao recarregar). */
export interface UrlState {
  view: View;
  tab: ListTab;
  product: string;
  search: string;
  /** null = padrão da aba (definido pela API). */
  sort: SortKey | null;
  level: PriorityLevel;
  page: number;
  pageSize: number;
  cap: number;
}

export const DEFAULT_URL_STATE: UrlState = {
  view: 'today',
  tab: 'focus',
  product: 'all',
  search: '',
  sort: null,
  level: 'all',
  page: 1,
  pageSize: 10,
  cap: 5,
};

const LEVELS: PriorityLevel[] = ['all', 'high', 'medium', 'low'];
const TABS: ListTab[] = ['focus', 'decide', 'follow', 'prospecting', 'review', 'all', 'ev'];

export function parseUrlState(search: string): UrlState {
  const p = new URLSearchParams(search);
  const d = DEFAULT_URL_STATE;
  const view = p.get('view') === 'all' ? 'all' : d.view;
  const tabRaw = p.get('tab') as ListTab | null;
  const tab = tabRaw && TABS.includes(tabRaw) ? tabRaw : d.tab;
  const productRaw = p.get('product');
  const product = productRaw ? productRaw.slice(0, MAX_PARAM_LENGTH) : d.product;
  const sortRaw = p.get('sort') as SortKey | null;
  const sort = sortRaw && SORT_OPTIONS.some((o) => o.value === sortRaw) ? sortRaw : d.sort;
  const levelRaw = p.get('level') as PriorityLevel | null;
  const level = levelRaw && LEVELS.includes(levelRaw) ? levelRaw : d.level;
  const pageRaw = parseInt(p.get('page') ?? '', 10);
  const page = Number.isInteger(pageRaw) && pageRaw >= 1 ? pageRaw : d.page;
  const sizeRaw = parseInt(p.get('size') ?? '', 10);
  const pageSize = PAGE_SIZE_OPTIONS.includes(sizeRaw) ? sizeRaw : d.pageSize;
  const capRaw = parseInt(p.get('cap') ?? '', 10);
  const cap = CAP_OPTIONS.includes(capRaw) ? capRaw : d.cap;
  return { view, tab, product, search: (p.get('q') ?? '').slice(0, MAX_PARAM_LENGTH), sort, level, page, pageSize, cap };
}

/** Só grava o que difere do padrão, para a URL ficar curta. Retorna sem o "?". */
export function serializeUrlState(s: UrlState): string {
  const d = DEFAULT_URL_STATE;
  const p = new URLSearchParams();
  if (s.view !== d.view) p.set('view', s.view);
  if (s.tab !== d.tab) p.set('tab', s.tab);
  if (s.product !== d.product) p.set('product', s.product);
  if (s.search.trim()) p.set('q', s.search);
  if (s.sort !== null) p.set('sort', s.sort);
  if (s.level !== d.level) p.set('level', s.level);
  if (s.page !== d.page) p.set('page', String(s.page));
  if (s.pageSize !== d.pageSize) p.set('size', String(s.pageSize));
  if (s.cap !== d.cap) p.set('cap', String(s.cap));
  return p.toString();
}
