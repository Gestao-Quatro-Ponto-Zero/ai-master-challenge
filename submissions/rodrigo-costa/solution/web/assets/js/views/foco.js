// Foco da semana (prancha 02): os deals do vendedor em ordem de prioridade, cada um com o porquê da nota.
import { STALE_DECISIONS, getDecision, getTreated, setDecision, setTreated } from '../core/marks.js';
import { listHead, liveRow, staleRow } from './foco/rows.js';

const STALE = 'sem_desfecho';
const PAGE_SIZE = 10;
const ACCOUNT_FILTERS = [
  { value: 'todos', label: 'Todos' },
  { value: 'com', label: 'Com cliente' },
  { value: 'sem', label: 'Sem cliente' },
];

export default {
  id: 'foco',
  title: 'Foco da semana',
  roles: ['seller', 'manager'],
  area: 'vendas',

  render(root, ctx) {
    const { dom, ui } = ctx;
    const manager = ctx.user.role === 'manager';
    dom.setHtml(root, dom.html`<div class="foco" data-foco>
      ${ui.screenHeader({
        eyebrow: ctx.dateInfo?.label_long,
        title: manager ? `Lista de ${ctx.subject}` : `Bom dia, ${ctx.user.first_name}.`,
        subtitle: dom.html`<span data-foco-context></span>`,
        aside: dom.html`<div class="foco-summary" data-foco-summary></div>`,
      })}
      ${ui.viewingBar(ctx)}
      <div class="foco-body" data-foco-body></div>
    </div>`);
    const screen = dom.qs('[data-foco]', root);
    const body = dom.qs('[data-foco-body]', screen);
    return ui
      .load(body, () => ctx.api.get('seller', { name: ctx.subject, date: ctx.date }), (data) => drawScreen(screen, body, ctx, data), {
        skeleton: { title: false, lines: 1, blocks: 6 },
      })
      .then(() => undefined);
  },
};

function drawScreen(screen, body, ctx, data) {
  const { dom, ui } = ctx;
  dom.qs('[data-foco-context]', screen).textContent = data.date?.context_sentence || '';
  dom.setHtml(dom.qs('[data-foco-summary]', screen), summaryHtml(ctx, data.summary));

  const insights = Array.isArray(data.insights) ? data.insights : [];
  const deals = Array.isArray(data.deals) ? data.deals : [];
  const bands = Array.isArray(data.bands) ? data.bands : [];
  const gabi = dom.html`<aside class="with-aside__aside" aria-label="Insights da Gabi">${ui.gabiHead()}${insights.map((insight) =>
    ui.gabiCard(insight, insightLink(ctx, insight)),
  )}</aside>`;

  if (deals.length === 0) {
    dom.setHtml(body, dom.html`<div class="with-aside"><div class="with-aside__main">${ui.empty(
      `Não há deal aberto de ${ctx.subject} em ${data.date?.label || ctx.date}. Troque a data simulada no menu para ver outra semana.`,
      { title: 'Nada para priorizar nesta data' },
    )}</div>${gabi}</div>`);
    return;
  }

  const list = createList(ctx, data, deals, bands);
  dom.setHtml(body, dom.html`<div class="with-aside">
    <div class="with-aside__main"><section class="foco-list" aria-label="Deals abertos" data-foco-list>${list.shell()}</section></div>
    ${gabi}
  </div>`);
  list.mount(dom.qs('[data-foco-list]', body), screen);
}

function summaryHtml({ dom, fmt, ui }, summary) {
  if (!summary) return '';
  return dom.html`<p class="foco-summary__kpis">
      <span><span class="foco-summary__big">${fmt.money(summary.live_value)}</span> ainda podem fechar</span>
      <span><span class="foco-summary__strong">${fmt.money(summary.expected_30d)}</span> esperados em 30 dias</span>
    </p>
    ${ui.dualBar({ share: summary.live_share, label: `${fmt.percent(summary.live_share)} do valor declarado ainda pode fechar` })}
    ${summary.sentence ? dom.html`<p class="foco-summary__sentence">${summary.sentence}</p>` : ''}`;
}

function insightLink(ctx, insight) {
  if (!insight.link_label) return {};
  if (insight.link_target === 'janela' || insight.link_target === STALE) {
    return { linkAttrs: { 'data-foco-insight': insight.link_target } };
  }
  return {};
}

// Lista com abas, filtros, linhas abertas e marcações locais. Guarda o estado da tela enquanto ela vive.
function createList(ctx, data, deals, bands) {
  const { dom, ui, fmt, store } = ctx;
  const win = data.window || null;
  const bandKeys = bands.map((band) => band.key);
  const janelaDeals = deals.filter((deal) => !deal.stale && deal.position === 'janela');

  // A decisão é por deal e vale também no Pipeline; o tratado é por vendedor e data.
  const readDecisions = () =>
    Object.fromEntries(deals.filter((deal) => deal.stale).map((deal) => [deal.id, getDecision(store, deal.id)]).filter(([, value]) => value));

  const st = {
    tab: initialTab(),
    account: 'todos',
    janela: false,
    showAll: false,
    openId: null,
    treated: getTreated(store, ctx.subject, ctx.date),
    decisions: readDecisions(),
  };
  let section = null;
  let panel = null;
  let scrollToOpen = false;

  function initialTab() {
    const wanted = String(ctx.params.aba || '').toLowerCase();
    if (bandKeys.includes(wanted)) return wanted;
    return (bands.find((band) => band.count > 0) || bands[0])?.key || STALE;
  }

  const bandOf = (key) => bands.find((band) => band.key === key) || null;
  const tabDeals = () => (st.janela ? janelaDeals : deals.filter((deal) => deal.band === st.tab));
  const isStaleView = () => !st.janela && st.tab === STALE;
  const matchesAccount = (deal) =>
    st.account === 'todos' || (st.account === 'com' ? Boolean(deal.account) : !deal.account);
  const visibleDeals = () => tabDeals().filter(matchesAccount);

  function applyDeepLink() {
    const wanted = String(ctx.params.deal || '').replace(/^#/, '').toLowerCase();
    const deal = wanted ? deals.find((item) => String(item.id).toLowerCase() === wanted) : null;
    if (deal && bandKeys.includes(deal.band)) {
      st.tab = deal.band;
      st.openId = deal.id;
      st.showAll = tabDeals().indexOf(deal) >= PAGE_SIZE;
      scrollToOpen = true;
      return;
    }
    st.openId = visibleDeals()[0]?.id ?? null;
  }

  function tabItems() {
    return bands.map((band) => ({
      id: band.key,
      label: band.label,
      count: fmt.number(band.count),
      hint: tabHint(band),
      separatorBefore: band.key === STALE,
    }));
  }

  // O rótulo da faixa aparece na aba ativa e sempre em Sem desfecho, como no estudo.
  function tabHint(band) {
    const showHint = band.key === STALE || (!st.janela && band.key === st.tab);
    return showHint ? band.hint : null;
  }

  function shell() {
    return dom.html`${ui.tabs({ id: 'foco', label: 'Faixas de score', items: tabItems(), active: st.janela ? null : st.tab })}
      <div class="tabpanel foco-panel" role="tabpanel" id="foco-panel" tabindex="-1" data-foco-panel></div>`;
  }

  function syncTabs() {
    dom.qsa('[role="tab"]', section).forEach((tab) => {
      const selected = !st.janela && tab.dataset.value === st.tab;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected || (st.janela && tab === dom.qs('[role="tab"]', section)) ? 0 : -1;
      const band = bandOf(tab.dataset.value);
      const count = dom.qs('.tab__count', tab);
      if (band && count) count.replaceWith(dom.toFragment(ui.tabCount(fmt.number(band.count), tabHint(band))));
    });
    if (st.janela) {
      panel.removeAttribute('aria-labelledby');
      panel.setAttribute('aria-label', 'Deals na faixa de idade que mais fecha');
    } else {
      panel.removeAttribute('aria-label');
      panel.setAttribute('aria-labelledby', `foco-tab-${st.tab}`);
    }
  }

  function accountCounts() {
    const band = st.janela ? null : bandOf(st.tab);
    if (band) return { todos: band.count, com: band.with_account, sem: band.without_account };
    const all = tabDeals();
    const withAccount = all.filter((deal) => deal.account).length;
    return { todos: all.length, com: withAccount, sem: all.length - withAccount };
  }

  function filtersHtml() {
    const counts = accountCounts();
    const all = tabDeals();
    const stale = isStaleView();
    const done = stale
      ? all.filter((deal) => st.decisions[deal.id]).length
      : all.filter((deal) => st.treated.has(deal.id)).length;
    const janelaChip = st.janela
      ? dom.html`<button type="button" class="chip foco-chip-janela" data-clear-janela aria-pressed="true">Na janela · ${fmt.number(janelaDeals.length)}${ctx.icon('close', { size: 12, stroke: 2.2 })}<span class="sr-only">, remover filtro</span></button><span class="foco-filters__sep" aria-hidden="true"></span>`
      : '';
    const counter = dom.html`<span class="foco-filters__count" aria-live="polite">${
      stale ? `${fmt.number(done)} de ${fmt.plural(all.length, 'decidido')}` : `${fmt.number(done)} de ${fmt.plural(all.length, 'tratado')}`
    }</span>`;
    return dom.html`<div class="foco-filters">
      <div class="foco-filters__left">
        ${janelaChip}
        ${ui.chips(ACCOUNT_FILTERS.map((item) => ({ ...item, count: fmt.number(counts[item.value]) })), { value: st.account, label: 'Filtrar por cliente' })}
        ${stale ? counter : ''}
      </div>
      <div class="foco-filters__right">${stale
        ? ui.button('Copiar decisões', { size: 'sm', iconName: 'copy', disabled: done === 0, attrs: { 'data-copy-decisions': true, 'data-key': 'copy-decisions' } })
        : dom.html`<p class="foco-filters__sort">Ordem: receita esperada (chance × preço). No empate, o mais antigo primeiro.</p>${counter}`}</div>
    </div>`;
  }

  function staleIntro() {
    const max = win && Number.isFinite(win.max_days) ? win.max_days : null;
    const first = max === null ? 'Nesta base nenhum deal fechou depois desse prazo.' : `Nesta base nenhum deal fechou depois de ${max} dias.`;
    return dom.html`<p class="foco-stale-intro">${first} Marque o que segue de pé e o que você vai encerrar. Fica salvo só neste navegador.</p>`;
  }

  function legendHtml() {
    const hasMax = win && Number.isFinite(win.max_days);
    if (!hasMax) return '';
    const hasWindow = Number.isFinite(win.from_days) && Number.isFinite(win.to_days);
    const scale = `A régua vai de 0 a ${win.max_days} dias.`;
    return dom.html`<p class="foco-legend">${hasWindow ? dom.html`<span class="foco-legend__swatch" aria-hidden="true"></span>` : ''}<span>${
      hasWindow ? `Faixa de idade em que os deals mais fecham nesta altura do trimestre (${win.from_days} a ${win.to_days} dias). ${scale}` : scale
    }</span></p>`;
  }

  function footerHtml(visible) {
    const stale = isStaleView();
    const more = !st.showAll && visible.length > PAGE_SIZE
      ? dom.html`<button type="button" class="link-arrow foco-more" data-show-all>Ver os ${fmt.plural(visible.length, 'deal')}</button>`
      : '';
    if (stale && !more) return '';
    return dom.html`<div class="foco-foot">
      ${stale
        ? dom.html`<span></span>`
        : dom.html`<div class="foco-foot__notes">
            ${legendHtml()}
            <p class="foco-note">O cliente não entra na conta: nesta base ele só é confiável depois que o deal fecha. O filtro Com cliente serve para navegar. <a class="link" href="${ctx.href('qualidade-dos-dados')}">Ver qualidade dos dados</a></p>
            <p class="foco-note">Os deals marcados como tratados ficam salvos só neste navegador.</p>
          </div>`}
      ${more}
    </div>`;
  }

  function rowsHtml(visible) {
    const stale = isStaleView();
    const shown = st.showAll ? visible : visible.slice(0, PAGE_SIZE);
    return shown.map((deal) =>
      stale || deal.stale
        ? staleRow(deal, { open: deal.id === st.openId, decision: st.decisions[deal.id] })
        : liveRow(deal, { open: deal.id === st.openId, treated: st.treated.has(deal.id), win }),
    );
  }

  function panelHtml() {
    const all = tabDeals();
    if (all.length === 0) {
      return ui.empty(st.janela ? 'Nenhum deal na faixa que mais fecha nesta data.' : 'Nenhum deal nesta faixa nesta data.');
    }
    const visible = visibleDeals();
    const stale = isStaleView();
    return dom.html`${stale ? staleIntro() : ''}
      ${filtersHtml()}
      ${visible.length === 0
        ? ui.empty(`Nenhum deal ${st.account === 'com' ? 'com' : 'sem'} cliente ${st.janela ? 'na faixa que mais fecha' : 'nesta faixa'}.`)
        : dom.html`${listHead({ stale })}<div class="foco-rows">${rowsHtml(visible)}</div>${footerHtml(visible)}`}`;
  }

  // Redesenha o painel e devolve o foco ao mesmo controle (as linhas são refeitas a cada mudança).
  function refresh({ focus } = {}) {
    const active = document.activeElement;
    const selector = focus || (panel.contains(active) ? focusSelector(active) : null);
    dom.setHtml(panel, panelHtml());
    syncTabs();
    if (selector) dom.qs(selector, panel)?.focus({ preventScroll: true });
  }

  function focusSelector(el) {
    if (el.dataset.key) return `[data-key="${CSS.escape(el.dataset.key)}"]`;
    if (el.dataset.chip) return `[data-chip="${CSS.escape(el.dataset.chip)}"]`;
    return null;
  }

  function selectTab(key) {
    st.tab = key;
    st.janela = false;
    st.account = 'todos';
    st.showAll = false;
    st.openId = visibleDeals()[0]?.id ?? null;
    refresh();
  }

  function toggleOpen(id) {
    st.openId = st.openId === id ? null : id;
    refresh({ focus: `[data-key="${CSS.escape(`toggle:${id}`)}"]` });
  }

  function toggleTreated(id) {
    if (st.treated.has(id)) st.treated.delete(id);
    else st.treated.add(id);
    setTreated(store, ctx.subject, ctx.date, st.treated);
    refresh();
  }

  function decide(id, value) {
    if (!STALE_DECISIONS[value]) return;
    if (st.decisions[id] === value) delete st.decisions[id];
    else st.decisions[id] = value;
    setDecision(store, id, st.decisions[id] || null);
    refresh();
  }

  function decisionsText() {
    const lines = [`Deals sem desfecho de ${ctx.subject} · ${data.date?.label || ctx.date}`];
    Object.entries(STALE_DECISIONS).forEach(([value, { label }]) => {
      const chosen = deals.filter((deal) => deal.stale && st.decisions[deal.id] === value);
      if (!chosen.length) return;
      lines.push('', `${label} (${chosen.length}):`);
      chosen.forEach((deal) => {
        const client = deal.account ? ` · ${deal.account}` : '';
        lines.push(`- #${deal.id} · ${deal.product} · ${fmt.money(deal.price)}${client} · aberto há ${fmt.plural(deal.age_days, 'dia')}`);
      });
    });
    return lines.join('\n');
  }

  function showJanela() {
    st.janela = true;
    st.account = 'todos';
    st.showAll = false;
    st.openId = janelaDeals[0]?.id ?? null;
    refresh();
    section.scrollIntoView({ block: 'start', behavior: smoothScroll() });
    dom.qs('[data-clear-janela]', panel)?.focus({ preventScroll: true });
  }

  function showTab(key) {
    selectTab(key);
    section.scrollIntoView({ block: 'start', behavior: smoothScroll() });
    dom.qs(`#foco-tab-${CSS.escape(key)}`, section)?.focus({ preventScroll: true });
  }

  function bind(screen) {
    ui.bindTabs(section, (key) => selectTab(key));
    dom.on(panel, 'click', '[data-chip]', (event, chip) => {
      st.account = chip.dataset.chip;
      st.showAll = false;
      st.openId = visibleDeals()[0]?.id ?? null;
      refresh();
    });
    dom.on(panel, 'click', '[data-clear-janela]', () => {
      st.janela = false;
      st.showAll = false;
      st.openId = visibleDeals()[0]?.id ?? null;
      refresh();
      dom.qs(`#foco-tab-${CSS.escape(st.tab)}`, section)?.focus();
    });
    dom.on(panel, 'click', '[data-toggle]', (event, button) => toggleOpen(button.dataset.toggle));
    dom.on(panel, 'click', '.foco-row__line', (event, line) => {
      if (event.target.closest('button')) return;
      const id = line.closest('[data-deal]')?.dataset.deal;
      if (id) toggleOpen(id);
    });
    dom.on(panel, 'click', '[data-treat]', (event, button) => toggleTreated(button.dataset.treat));
    dom.on(panel, 'click', '[data-decide]', (event, button) => decide(button.dataset.dealId, button.dataset.decide));
    dom.on(panel, 'click', '[data-copy]', (event, button) => {
      const deal = deals.find((item) => item.id === button.dataset.copy);
      if (deal?.summary_text) ui.copyText(deal.summary_text, { success: 'Resumo copiado' });
    });
    dom.on(panel, 'click', '[data-copy-decisions]', () => ui.copyText(decisionsText(), { success: 'Decisões copiadas' }));
    dom.on(panel, 'click', '[data-show-all]', () => {
      const next = visibleDeals()[PAGE_SIZE];
      st.showAll = true;
      refresh({ focus: next ? `[data-key="${CSS.escape(`toggle:${next.id}`)}"]` : null });
    });
    dom.on(screen, 'click', '[data-foco-insight]', (event, link) => {
      if (link.dataset.focoInsight === 'janela') showJanela();
      else if (bandKeys.includes(link.dataset.focoInsight)) showTab(link.dataset.focoInsight);
    });
  }

  function mount(sectionEl, screen) {
    section = sectionEl;
    panel = dom.qs('[data-foco-panel]', section);
    applyDeepLink();
    refresh();
    bind(screen);
    if (scrollToOpen) {
      const row = dom.qs(`[data-deal="${CSS.escape(st.openId)}"]`, panel);
      row?.scrollIntoView({ block: 'center', behavior: smoothScroll() });
      dom.qs('[data-toggle]', row || panel)?.focus({ preventScroll: true });
    }
  }

  return { shell, mount };
}

function smoothScroll() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
}
