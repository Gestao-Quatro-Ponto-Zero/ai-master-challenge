import React from 'react';
import type { DealsApi } from '../api/DealsApi';
import { errorMessage } from '../api/errors';
import type {
  CurrentUser,
  Deal,
  DealActionKind,
  DealsPage,
  DisagreeReason,
  FeedbackEntry,
  FeedbackKind,
  ListDealsQuery,
  ListFilters,
  ListTab,
  Meta,
  PriorityLevel,
  SortKey,
  DealExplanation,
  Summary,
} from '../api/types';
import AppHeader from '../components/AppHeader';
import BandTabs from '../components/BandTabs';
import BulkBar from '../components/BulkBar';
import DealDetail from '../components/DealDetail';
import DealsTable from '../components/DealsTable';
import DetailPanel from '../components/DetailPanel';
import ErrorBanner from '../components/ErrorBanner';
import FiltersBar from '../components/FiltersBar';
import HowItWorks from '../components/HowItWorks';
import type { KpiItem } from '../components/KpiCard';
import KpiCards from '../components/KpiCards';
import ListFooter from '../components/ListFooter';
import Modal from '../components/Modal';
import PageTitle from '../components/PageTitle';
import Pagination from '../components/Pagination';
import Toast from '../components/Toast';
import TodayView from '../components/TodayView';
import UsageNotice from '../components/UsageNotice';
import ViewTabs from '../components/ViewTabs';
import { TAB_DEFS } from '../lib/constants';
import { buildFooterText, daysText, money } from '../lib/format';
import { browserStore, readJson, writeJson } from '../lib/storage';
import { DEFAULT_ACCENT } from '../lib/theme';
import { parseUrlState, serializeUrlState, type UrlState, type View } from '../lib/urlState';

export const DONE_STORAGE_KEY = 'g4.done.v1';
const WIDE_QUERY = '(min-width: 1100px)';

interface Props {
  api: DealsApi;
  accent?: string;
  /** Sobrescreve a flag que vem de GET /meta (critério F7). */
  showProbability?: boolean;
}

interface State extends UrlState {
  selId: string | null;
  modalId: string | null;
  howOpen: boolean;
  checked: Record<string, boolean>;
  confirmingLost: boolean;
  toast: string;
  undoIds: string[];
  done: Record<string, boolean>;
  lastFeedback: Record<string, FeedbackKind>;
  history: Record<string, FeedbackEntry[]>;
  explanations: Record<string, DealExplanation>;
  user: CurrentUser | null;
  meta: Meta | null;
  filters: ListFilters | null;
  summary: Summary | null;
  list: DealsPage | null;
  today: Deal[] | null;
  loading: boolean;
  error: string | null;
  wide: boolean;
}

const dealsText = (n: number) => `${n} ${n === 1 ? 'deal' : 'deals'}`;

/** Tela do vendedor: "Meu dia" e "Todo o pipeline". Guarda o estado e fala com a API. */
export default class SellerPage extends React.Component<Props, State> {
  private alive = false;
  private listSeq = 0;
  private todaySeq = 0;
  private mq: MediaQueryList | null = null;
  private store = browserStore();
  private listRef = React.createRef<HTMLElement>();

  constructor(props: Props) {
    super(props);
    const url = parseUrlState(typeof window !== 'undefined' ? window.location.search : '');
    this.state = {
      ...url,
      selId: null,
      modalId: null,
      howOpen: false,
      checked: {},
      confirmingLost: false,
      toast: '',
      undoIds: [],
      done: readJson<Record<string, boolean>>(this.store, DONE_STORAGE_KEY, {}),
      lastFeedback: {},
      history: {},
      explanations: {},
      user: null,
      meta: null,
      filters: null,
      summary: null,
      list: null,
      today: null,
      loading: true,
      error: null,
      wide: true,
    };
  }

  // ---- ciclo de vida ----

  componentDidMount() {
    this.alive = true;
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      this.mq = window.matchMedia(WIDE_QUERY);
      this.setState({ wide: this.mq.matches });
      this.mq.addEventListener('change', this.onMediaChange);
    }
    this.syncUrl();
    void this.loadStatic();
    void this.loadView();
  }

  componentDidUpdate(_prevProps: Props, prev: State) {
    if (this.viewKey(prev) !== this.viewKey(this.state)) void this.loadView();
    this.syncUrl();
    const id = this.activeDeal(this.state)?.id ?? null;
    if (id && id !== (this.activeDeal(prev)?.id ?? null)) {
      void this.loadHistory(id);
      void this.loadExplanation(id);
    }
  }

  componentWillUnmount() {
    this.alive = false;
    this.mq?.removeEventListener('change', this.onMediaChange);
  }

  private onMediaChange = (event: MediaQueryListEvent) => this.setState({ wide: event.matches });

  // ---- derivados do estado ----

  /** Opções do filtro de prioridade, montadas só com o que veio de GET /meta. */
  private levelOptions(meta: Meta): { value: PriorityLevel; label: string }[] {
    return [
      { value: 'all', label: 'Todas' },
      ...meta.priorityLevels.map((l) => ({ value: l.key, label: `${l.label} (${l.minScore} a ${l.maxScore})` })),
    ];
  }

  /** Ordenação em vigor: a escolhida ou o padrão da aba, que a API informa em /meta (views). */
  private effectiveSort(s: State, meta: Meta): SortKey {
    return s.sort ?? meta.views.find((v) => v.key === s.tab)?.defaultSort ?? 'score';
  }

  private buildQuery(s: State): ListDealsQuery {
    return {
      tab: s.tab,
      product: s.product,
      q: s.search.trim(),
      sort: s.sort,
      level: s.level,
      page: s.page,
      pageSize: s.pageSize,
    };
  }

  private viewKey(s: State): string {
    return s.view === 'today' ? `today|${s.cap}` : `all|${JSON.stringify(this.buildQuery(s))}`;
  }

  private urlStateOf(s: State): UrlState {
    const { view, tab, product, search, sort, level, page, pageSize, cap } = s;
    return { view, tab, product, search, sort, level, page, pageSize, cap };
  }

  private syncUrl() {
    if (typeof window === 'undefined') return;
    const qs = serializeUrlState(this.urlStateOf(this.state));
    const { pathname, search, hash } = window.location;
    const next = pathname + (qs ? `?${qs}` : '') + hash;
    if (next !== pathname + search + hash) window.history.replaceState(null, '', next);
  }

  private itemsOf(s: State): Deal[] {
    return s.view === 'all' ? (s.list?.items ?? []) : (s.today ?? []);
  }

  private modalDeal(s: State): Deal | null {
    if (!s.modalId) return null;
    return this.itemsOf(s).find((d) => d.id === s.modalId) ?? null;
  }

  private showModal(s: State): boolean {
    return !!this.modalDeal(s) && (s.view === 'today' || !s.wide);
  }

  private panelDeal(s: State): Deal | null {
    if (s.view !== 'all' || !s.wide) return null;
    const items = this.itemsOf(s);
    return items.find((d) => d.id === s.selId) ?? items[0] ?? null;
  }

  private activeDeal(s: State): Deal | null {
    return this.showModal(s) ? this.modalDeal(s) : this.panelDeal(s);
  }

  // ---- carregamento ----

  private fail(error: unknown) {
    if (this.alive) this.setState({ error: errorMessage(error), loading: false });
  }

  private async loadStatic() {
    const { api } = this.props;
    try {
      const [user, meta, filters, summary] = await Promise.all([
        api.getCurrentUser(),
        api.getMeta(),
        api.getFilters(),
        api.getSummary(),
      ]);
      if (this.alive) this.setState({ user, meta, filters, summary });
    } catch (error) {
      this.fail(error);
    }
  }

  private async loadSummary() {
    try {
      const summary = await this.props.api.getSummary();
      if (this.alive) this.setState({ summary });
    } catch (error) {
      this.fail(error);
    }
  }

  private async loadView() {
    const s = this.state;
    try {
      if (s.view === 'all') {
        const seq = ++this.listSeq;
        this.setState({ loading: true });
        const list = await this.props.api.listDeals(this.buildQuery(s));
        if (!this.alive || seq !== this.listSeq) return;
        this.setState({ list, loading: false, error: null, page: list.page });
      } else {
        const seq = ++this.todaySeq;
        this.setState({ loading: true });
        const today = await this.props.api.listTodayDeals({ cap: s.cap });
        if (!this.alive || seq !== this.todaySeq) return;
        this.setState({ today, loading: false, error: null });
      }
    } catch (error) {
      this.fail(error);
    }
  }

  private async refresh() {
    void this.loadSummary();
    await this.loadView();
  }

  private async loadExplanation(dealId: string) {
    if (this.state.explanations[dealId]) return;
    try {
      const explanation = await this.props.api.getDealExplanation(dealId);
      if (this.alive) this.setState((st) => ({ explanations: { ...st.explanations, [dealId]: explanation } }));
    } catch {
      /* a explicação detalhada é opcional: sem ela a tela mostra os motivos resumidos */
    }
  }

  private async loadHistory(dealId: string) {
    try {
      const items = await this.props.api.listFeedback(dealId);
      if (this.alive) this.setState((st) => ({ history: { ...st.history, [dealId]: items } }));
    } catch {
      /* o histórico é opcional: se falhar, a tela segue sem ele */
    }
  }

  private onRetry = () => {
    this.setState({ error: null });
    void this.loadStatic();
    void this.loadView();
  };

  // ---- filtros e navegação ----

  private onSwitchView = (view: View) =>
    this.setState({ view, selId: null, modalId: null, checked: {}, confirmingLost: false });
  private onSearch = (search: string) => this.setState({ search, selId: null, page: 1 });
  private onProduct = (product: string) => this.setState({ product, selId: null, page: 1 });
  private onLevel = (level: PriorityLevel) => this.setState({ level, selId: null, page: 1 });
  private onSort = (sort: SortKey) => this.setState({ sort, selId: null, page: 1 });
  private onClear = () => this.setState({ search: '', product: 'all', level: 'all', selId: null, page: 1 });
  private onPickTab = (tab: ListTab) =>
    this.setState({ tab, selId: null, page: 1, checked: {}, confirmingLost: false });
  private onPickKpi = (tab: ListTab) => {
    this.onPickTab(tab);
    this.listRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  };
  private onPage = (page: number) => this.setState({ page, selId: null });
  private onPageSize = (pageSize: number) => this.setState({ pageSize, page: 1, selId: null });
  private onCap = (cap: number) => this.setState({ cap });

  private onSelectRow = (id: string) => {
    if (this.state.wide) this.setState({ selId: id });
    else this.setState({ modalId: id });
  };
  private onOpenModal = (id: string) => this.setState({ modalId: id });
  private onCloseModal = () => this.setState({ modalId: null });
  private onOpenHow = () => this.setState({ howOpen: true });
  private onCloseHow = () => this.setState({ howOpen: false });

  private onToggleDone = (id: string) => {
    const done = { ...this.state.done };
    if (done[id]) delete done[id];
    else done[id] = true;
    writeJson(this.store, DONE_STORAGE_KEY, done);
    this.setState({ done });
  };

  private onToggleCheck = (id: string) =>
    this.setState((st) => ({ checked: { ...st.checked, [id]: !st.checked[id] }, confirmingLost: false }));

  private onTogglePage = (all: boolean) =>
    this.setState((st) => {
      const checked = { ...st.checked };
      (st.list?.items ?? []).forEach((d) => {
        if (all) checked[d.id] = true;
        else delete checked[d.id];
      });
      return { checked, confirmingLost: false };
    });

  // ---- ações sobre deals ----

  private async runAction(action: DealActionKind, ids: string[], days: number | undefined, message: string) {
    if (ids.length === 0) return;
    try {
      await this.props.api.applyAction({ action, dealIds: ids, snoozeDays: days });
      if (!this.alive) return;
      this.setState((st) => {
        const checked = { ...st.checked };
        ids.forEach((id) => delete checked[id]);
        return { toast: message, undoIds: ids, selId: null, modalId: null, confirmingLost: false, checked };
      });
      await this.refresh();
    } catch (error) {
      this.fail(error);
    }
  }

  private snoozeDeal = (deal: Deal, days: number) =>
    void this.runAction('snooze', [deal.id], days, `${deal.product} adiado por ${daysText(days)}.`);

  private loseDeal = (deal: Deal) =>
    void this.runAction('lost', [deal.id], undefined, `${deal.product} marcado como perdido.`);

  private selectedIds(): string[] {
    return Object.keys(this.state.checked).filter((id) => this.state.checked[id]);
  }

  private onBulkSnooze = () => {
    const ids = this.selectedIds();
    const n = ids.length;
    void this.runAction('snooze', ids, 30, `${dealsText(n)} ${n === 1 ? 'adiado' : 'adiados'} por 30 dias.`);
  };
  private onBulkAskLost = () => this.setState({ confirmingLost: true });
  private onBulkCancel = () => this.setState({ confirmingLost: false });
  private onBulkConfirmLost = () => {
    const ids = this.selectedIds();
    const n = ids.length;
    void this.runAction(
      'lost',
      ids,
      undefined,
      `${dealsText(n)} ${n === 1 ? 'encerrado como perdido' : 'encerrados como perdidos'}.`,
    );
  };

  private onUndo = async () => {
    try {
      await this.props.api.undoAction(this.state.undoIds);
      if (!this.alive) return;
      this.setState({ toast: '', undoIds: [] });
      await this.refresh();
    } catch (error) {
      this.fail(error);
    }
  };
  private onCloseToast = () => this.setState({ toast: '', undoIds: [] });

  private async sendFeedback(deal: Deal, kind: FeedbackKind, reason: DisagreeReason | null = null) {
    this.setState((st) => ({ lastFeedback: { ...st.lastFeedback, [deal.id]: kind } }));
    try {
      await this.props.api.sendFeedback(deal.id, kind, reason);
      await this.loadHistory(deal.id);
    } catch (error) {
      this.fail(error);
    }
  }

  private onReset = async () => {
    try {
      await this.props.api.reset?.();
      writeJson(this.store, DONE_STORAGE_KEY, {});
      if (!this.alive) return;
      this.setState({ done: {}, toast: '', undoIds: [], checked: {}, history: {}, lastFeedback: {}, selId: null });
      await this.refresh();
    } catch (error) {
      this.fail(error);
    }
  };

  // ---- partes da tela ----

  private renderDetail(deal: Deal, accent: string, showProbability: boolean) {
    const s = this.state;
    return (
      <DealDetail
        key={deal.id}
        deal={deal}
        accent={accent}
        showProbability={showProbability}
        lastFeedback={s.lastFeedback[deal.id]}
        history={s.history[deal.id] ?? []}
        thresholds={(this.state.meta as Meta).thresholds}
        horizonDays={(this.state.meta as Meta).horizonDays}
        calibrationUseful={(this.state.meta as Meta).calibrationUseful}
        explanation={s.explanations[deal.id]}
        onAct={() => void this.sendFeedback(deal, 'act')}
        onLost={() => this.loseDeal(deal)}
        onSnooze={(days) => this.snoozeDeal(deal, days)}
        onDisagree={(reason) => void this.sendFeedback(deal, 'disagree', reason)}
        onIgnore={() => void this.sendFeedback(deal, 'ignore')}
      />
    );
  }

  private buildKpis(accent: string): KpiItem[] {
    const { summary, tab } = this.state;
    const v = summary?.views;
    return [
      {
        key: 'focus',
        label: 'Em foco esta semana',
        value: v ? String(v.focus.count) : '–',
        note: v ? `Esperado ${money(v.focus.expectedValue)}` : '',
        valueColor: accent,
        selected: tab === 'focus',
      },
      {
        key: 'review',
        label: 'A revisar',
        value: v ? String(v.review.count) : '–',
        note: 'Encerrar ou reativar',
        valueColor: '#9B2C2C',
        selected: tab === 'review',
      },
      {
        key: 'all',
        label: 'Deals abertos',
        value: v ? String(v.all.count) : '–',
        note: v ? (v.prospecting.count > 0 ? `${v.prospecting.count} em prospecção` : 'Nenhum em prospecção') : '',
        valueColor: '#0F1B2D',
        selected: tab === 'all',
      },
      {
        key: 'ev',
        label: 'Valor esperado',
        value: v ? money(v.ev.expectedValue) : '–',
        note: 'Deals ativos, sem "A revisar"',
        valueColor: '#0F1B2D',
        selected: tab === 'ev',
      },
    ];
  }

  private renderPipeline(meta: Meta, accent: string, sampleData: boolean, detail: React.ReactNode | null) {
    const s = this.state;
    const list = s.list;
    const items = list?.items ?? [];
    const views = s.summary?.views ?? null;
    const levelOptions = this.levelOptions(meta);
    const canClear = s.search.trim() !== '' || s.product !== 'all' || s.level !== 'all';
    const levelLabel = levelOptions.find((o) => o.value === s.level && o.value !== 'all')?.label ?? null;
    const inReview = s.tab === 'review';
    const footer = list
      ? buildFooterText({
          total: list.total,
          pageStart: (list.page - 1) * list.pageSize,
          shown: items.length,
          tab: s.tab,
          levelLabel,
          sampleData,
        })
      : '';

    return (
      <>
        <UsageNotice onHowItWorks={this.onOpenHow} />
        <KpiCards items={this.buildKpis(accent)} onPick={this.onPickKpi} />

        <section className="workspace" ref={this.listRef}>
          <div className="listcard">
            <FiltersBar
              search={s.search}
              product={s.product}
              level={s.level}
              sort={this.effectiveSort(s, meta)}
              products={s.filters?.products ?? []}
              levelOptions={levelOptions}
              levelDisabled={inReview}
              canClear={canClear}
              onSearch={this.onSearch}
              onProduct={this.onProduct}
              onLevel={this.onLevel}
              onSort={this.onSort}
              onClear={this.onClear}
            />
            <BandTabs
              tabs={TAB_DEFS.map((t) => ({ key: t.key, label: t.label, count: views ? views[t.key].count : null }))}
              active={s.tab}
              onPick={this.onPickTab}
            />
            {inReview && list && list.total > 0 && (
              <BulkBar
                reviewDays={meta.thresholds.reviewDays}
                selectedCount={this.selectedIds().length}
                confirming={s.confirmingLost}
                onSnooze={this.onBulkSnooze}
                onAskLost={this.onBulkAskLost}
                onConfirmLost={this.onBulkConfirmLost}
                onCancel={this.onBulkCancel}
              />
            )}
            <DealsTable
              items={items}
              selectedId={s.wide ? (this.panelDeal(s)?.id ?? null) : null}
              accent={accent}
              reviewDays={meta.thresholds.reviewDays}
              sort={this.effectiveSort(s, meta)}
              onSort={this.onSort}
              onSelect={this.onSelectRow}
              checked={inReview ? s.checked : undefined}
              onToggle={this.onToggleCheck}
              onTogglePage={this.onTogglePage}
              loading={s.loading}
              hasLoaded={list !== null}
              canClear={canClear}
              onClear={this.onClear}
            />
            {list && list.total > 5 && (
              <Pagination
                page={list.page}
                pageCount={list.pageCount}
                pageSize={s.pageSize}
                onPage={this.onPage}
                onPageSize={this.onPageSize}
              />
            )}
            <ListFooter
              text={footer}
              sampleData={sampleData}
              onReset={this.props.api.reset ? this.onReset : undefined}
            />
          </div>
          {s.wide && <DetailPanel>{detail}</DetailPanel>}
        </section>
      </>
    );
  }

  render() {
    const s = this.state;
    const accent = this.props.accent ?? DEFAULT_ACCENT;
    const meta = s.meta;
    if (!meta) {
      // As regras (prazos, níveis de prioridade, abas) vêm de GET /meta: sem elas não há o que mostrar.
      return (
        <>
          <AppHeader user={s.user} />
          <main id="main" className="main">
            {s.error ? (
              <ErrorBanner message={s.error} onRetry={this.onRetry} />
            ) : (
              <div role="status" className="state">
                Carregando…
              </div>
            )}
          </main>
        </>
      );
    }
    const sampleData = meta.sampleData;
    const showProbability = this.props.showProbability ?? meta.showProbability;
    const showModal = this.showModal(s);
    const detailDeal = this.activeDeal(s);
    const detail = detailDeal ? this.renderDetail(detailDeal, accent, showProbability) : null;
    const today = s.view === 'today';

    return (
      <>
        <AppHeader user={s.user} />
        <main id="main" className="main">
          <PageTitle
            title={today ? 'Seu dia' : 'Todo o pipeline'}
            subtitle={today ? 'Os melhores deals do foco da semana, para hoje. O resto fica para os outros dias.' : 'Filtros, faixas e detalhes de cada deal.'}
            hint={today ? 'Ordenados pelo índice de prioridade, que pesa valor do produto, tempo no funil e histórico.' : undefined}
            referenceDate={meta.referenceDate}
            sampleData={sampleData}
            onHowItWorks={this.onOpenHow}
          />
          <ViewTabs view={s.view} allCount={s.summary?.views.all.count ?? null} onChange={this.onSwitchView} />

          {s.error && <ErrorBanner message={s.error} onRetry={this.onRetry} />}

          {today ? (
            <TodayView
              deals={s.today}
              cap={s.cap}
              done={s.done}
              accent={accent}
              onCap={this.onCap}
              onOpen={this.onOpenModal}
              onToggleDone={this.onToggleDone}
              onSnooze={this.snoozeDeal}
            />
          ) : (
            this.renderPipeline(meta, accent, sampleData, showModal ? null : detail)
          )}

          {s.toast && <Toast message={s.toast} onUndo={this.onUndo} onClose={this.onCloseToast} />}

          {showModal && detail && <Modal label="Detalhes do deal" onClose={this.onCloseModal}>{detail}</Modal>}
          {s.howOpen && (
            <Modal label="Como a prioridade é calculada" onClose={this.onCloseHow}>
              <HowItWorks meta={meta} />
            </Modal>
          )}
        </main>
      </>
    );
  }
}
