// Clientes (pranchas 06 e 06b): tabela por regional de casa e painel lateral com Dados, Em aberto e Fechadas.
// A URL guarda a regional, o cliente aberto e a aba (?regional=leste&cliente=Mathtouch&aba=em-aberto).
import { normalize } from '../core/fmt.js';

const REGIONS = [
  { value: 'leste', key: 'East', label: 'Leste' },
  { value: 'central', key: 'Central', label: 'Central' },
  { value: 'oeste', key: 'West', label: 'Oeste' },
  { value: 'todas', key: '', label: 'Todas' },
];

const TABS = ['dados', 'em-aberto', 'fechadas'];
const RECENT_LIMIT = 8;
const CHART_HEIGHT = 52;

// Estado da tela que sobrevive às trocas de parâmetro (reason 'params'), quando o root não é refeito.
let view = null;

function regionFromParam(param, user) {
  const wanted = String(param || '').toLowerCase();
  return (
    REGIONS.find((r) => r.value === wanted) ||
    REGIONS.find((r) => r.key === user.region) ||
    REGIONS[0]
  );
}

function tabFromParam(param) {
  return TABS.includes(param) ? param : 'dados';
}


/* Tabela */

function tableHtml(ctx, data, region) {
  const { html, raw } = ctx.dom;
  const { fmt, ui } = ctx;
  const showRegion = region.key === '';
  const rows = data.accounts.map((account) => {
    const link = ctx.href('clientes', { regional: region.value, cliente: account.name });
    const sub = showRegion ? `${account.sector_label} · ${account.home_region_label}` : account.sector_label;
    return html`<tr class="is-clickable" data-cliente="${account.name}" data-busca="${normalize(account.name)}">
      <td><a class="clientes-link cell-title" href="${link}" data-cliente-link>${account.name}</a><div class="cell-sub">${sub}</div></td>
      <td class="is-num">${fmt.number(account.closed_count)}</td>
      <td class="is-num">${fmt.percent(account.win_rate, 1)}</td>
      <td class="is-num clientes-table__value">${fmt.money(account.won_value)}</td>
      <td class="is-num clientes-table__muted">${account.last_sale_label || '—'}</td>
    </tr>`;
  });
  const table = html`<table class="table clientes-table">
    <caption class="sr-only">${data.title}. Clique numa linha para abrir a ficha do cliente.</caption>
    <thead><tr>
      <th scope="col">Cliente</th>
      <th scope="col" class="is-num">Fechados</th>
      <th scope="col" class="is-num">Ganhos</th>
      <th scope="col" class="is-num">Valor ganho</th>
      <th scope="col" class="is-num">Última venda</th>
    </tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
  return html`${data.accounts.length
    ? ui.tableWrap(table, { label: data.title })
    : ui.empty('Nenhum cliente tem esta regional como casa até esta data.', { title: 'Sem clientes' })}
    <div class="clientes-filter-empty" data-filter-empty hidden>${ui.empty(raw(''), { title: 'Nenhum cliente com esse nome nesta lista.' })}</div>
    <div class="clientes-notes">
      ${data.note ? html`<p>${data.note}</p>` : ''}
      ${data.home_region_note ? html`<p>${data.home_region_note}</p>` : ''}
    </div>`;
}

function applyFilter(ctx) {
  if (!view?.wrap) return;
  const { qsa, qs } = ctx.dom;
  const term = normalize(view.search);
  const rows = qsa('tbody tr[data-busca]', view.wrap);
  let shown = 0;
  rows.forEach((row) => {
    const match = !term || row.dataset.busca.includes(term);
    row.hidden = !match;
    if (match) shown += 1;
  });
  const emptyBox = qs('[data-filter-empty]', view.wrap);
  if (emptyBox) {
    emptyBox.hidden = !(rows.length && shown === 0);
    const text = emptyBox.querySelector('.state p:last-child');
    if (text) text.textContent = `Nada encontrado para “${view.search.trim()}”. Tente outro nome ou outra regional.`;
  }
  const status = qs('[data-filter-status]', view.wrap);
  if (status) status.textContent = term ? `${ctx.fmt.plural(shown, 'cliente')} na busca.` : '';
}

function markSelected(ctx) {
  if (!view?.wrap) return;
  ctx.dom.qsa('tbody tr[data-cliente]', view.wrap).forEach((row) => {
    const selected = Boolean(view.panelName) && normalize(row.dataset.cliente) === normalize(view.panelName);
    row.classList.toggle('is-selected', selected);
    const link = row.querySelector('[data-cliente-link]');
    if (selected) link?.setAttribute('aria-current', 'true');
    else link?.removeAttribute('aria-current');
  });
}

function loadTable(ctx, region) {
  const key = `${region.value}|${ctx.date}`;
  view.tableKey = key;
  view.tableReady = false;
  const host = ctx.dom.qs('[data-table]', view.wrap);
  return ctx.ui.load(
    host,
    () => ctx.api.get('accounts', { region: region.key, date: ctx.date }),
    (data) => {
      if (view?.tableKey !== key) return;
      view.tableReady = true;
      updateHeader(ctx, data);
      ctx.dom.setHtml(host, tableHtml(ctx, data, region));
      applyFilter(ctx);
      markSelected(ctx);
    },
    { skeleton: { title: false, lines: 1, blocks: 6 }, errorTitle: 'Não foi possível carregar os clientes.' },
  );
}

function updateHeader(ctx, data) {
  const title = ctx.dom.qs('#screen-title', view.wrap);
  const sub = ctx.dom.qs('[data-subtitle]', view.wrap);
  if (title) title.textContent = data.title;
  if (sub) sub.textContent = data.subtitle || '';
}

/* Painel: aba Dados */

function sectionLabel(ctx, text, aside) {
  const { html } = ctx.dom;
  return html`<div class="clientes-group-head"><h3 class="eyebrow">${text}</h3>${aside ? html`<span class="eyebrow">${aside}</span>` : ''}</div>`;
}

function dataTab(ctx, data) {
  const { html } = ctx.dom;
  const { fmt, ui } = ctx;
  const { history, account } = data;
  const products = data.top_products || [];
  const facts = [
    ['Faturamento anual', account.revenue_label || '—'],
    ['Funcionários', fmt.number(account.employees)],
    ['Fundada em', account.year_established ?? '—'],
    ['Sede', account.office_label || '—'],
    ['Controladora', account.parent || 'Nenhuma'],
  ];
  return html`<section class="clientes-block" aria-labelledby="clientes-historico">
      <h3 class="eyebrow" id="clientes-historico">Histórico fechado · antes de ${data.date?.label || ''}</h3>
      <div class="clientes-hero">
        <p class="clientes-hero__value">${fmt.money(history.won_value)}</p>
        ${history.headline_detail ? html`<p class="clientes-hero__sub">${history.headline_detail}</p>` : ''}
      </div>
      <div class="clientes-stats">
        <div><p class="clientes-stats__value">${fmt.money(history.avg_ticket)}</p><p class="clientes-stats__label">ticket médio</p></div>
        <div><p class="clientes-stats__value">${history.last_sale_label || '—'}</p><p class="clientes-stats__label">última venda</p></div>
        <div><p class="clientes-stats__value">${fmt.number(history.seller_count)}</p><p class="clientes-stats__label">${history.sellers_label || ''}</p></div>
      </div>
    </section>
    <section class="clientes-block clientes-block--ruled" aria-labelledby="clientes-produtos">
      <h3 class="eyebrow" id="clientes-produtos">O que mais compra</h3>
      ${products.length
        ? html`<ul class="clientes-products">${products.map(
          (item) => html`<li class="clientes-product">
            <div class="clientes-product__line"><span class="clientes-product__name">${item.product}</span><span class="clientes-product__meta">${fmt.plural(item.won_count, 'venda')} · ${fmt.money(item.won_value)}</span></div>
            <span class="clientes-bar" aria-hidden="true"><span class="clientes-bar__fill" style="width: ${(Math.max(0, Math.min(1, Number(item.share) || 0)) * 100).toFixed(1)}%"></span></span>
          </li>`,
        )}</ul>`
        : html`<p class="clientes-muted">Nenhuma venda ganha até esta data.</p>`}
    </section>
    <section class="clientes-block clientes-block--ruled" aria-labelledby="clientes-cadastro">
      <h3 class="eyebrow" id="clientes-cadastro">Cadastro</h3>
      <dl class="clientes-facts">${facts.map(([label, value]) => html`<div class="clientes-facts__row"><dt>${label}</dt><dd>${value}</dd></div>`)}</dl>
    </section>
    ${data.note ? ui.note(data.note) : ''}`;
}

/* Painel: aba Em aberto */

function sellerPart(ctx, deal) {
  const { html } = ctx.dom;
  if (!deal.is_viewer) return deal.seller;
  if (ctx.user.role === 'seller') return html`<b class="clientes-strong">Seu deal</b>`;
  return html`<b class="clientes-strong">Seu time</b> · ${deal.seller}`;
}

function regionPart(ctx, deal) {
  const { html } = ctx.dom;
  return deal.other_region ? html`<b class="clientes-other-region">${deal.region_label}</b>` : deal.region_label;
}

function openRow(ctx, deal) {
  const { html } = ctx.dom;
  const { fmt } = ctx;
  const days = fmt.plural(deal.age_days, 'dia');
  const main = html`<div class="clientes-row__main">
      <p class="clientes-row__title"><b>${deal.product}</b> · ${fmt.money(deal.price)}</p>
      <p class="clientes-row__meta">#${deal.id} · ${sellerPart(ctx, deal)} · ${regionPart(ctx, deal)}</p>
    </div>`;
  if (deal.stale) {
    return html`<li class="clientes-row clientes-row--stale">
      <span class="clientes-row__score clientes-row__score--none"><span aria-hidden="true">–</span><span class="sr-only">Sem score</span></span>
      ${main}
      <span class="clientes-row__side"><span class="clientes-row__days">${days}</span></span>
    </li>`;
  }
  return html`<li class="clientes-row">
    <span class="clientes-row__score"><span class="sr-only">Score </span>${deal.score ?? '—'}</span>
    ${main}
    <span class="clientes-row__side"><span class="clientes-row__chance"><span class="sr-only">Chance em 30 dias: </span>${fmt.percent(deal.chance)}</span><span class="clientes-row__days">${days}</span></span>
  </li>`;
}

function openTab(ctx, data) {
  const { html } = ctx.dom;
  const { fmt, ui } = ctx;
  const open = data.open || {};
  const live = open.live || [];
  const stale = open.stale || [];
  if (!live.length && !stale.length) {
    return ui.empty('Nenhum deal aberto com este cliente no cadastro.');
  }
  const warning = open.warning
    ? ui.alert(html`<p class="clientes-alert__title">${open.warning.title}</p>${open.warning.body ? html`<p class="clientes-alert__body">${open.warning.body}</p>` : ''}`)
    : '';
  const liveGroup = html`<section class="clientes-group" aria-label="Em negociação">
      ${sectionLabel(ctx, `Em negociação · ${fmt.number(live.length)}`, 'Chance em 30 dias')}
      ${live.length
        ? html`<ul class="clientes-rows">${live.map((deal) => openRow(ctx, deal))}</ul>`
        : html`<p class="clientes-muted clientes-group__empty">Nenhum deal em negociação agora.</p>`}
    </section>`;
  const staleGroup = stale.length
    ? html`<section class="clientes-group" aria-label="Sem desfecho">
        ${sectionLabel(ctx, `Sem desfecho · ${fmt.number(stale.length)} · ${fmt.money(open.stale_value)}`, fmt.capitalize(data.staleRule))}
        <ul class="clientes-rows clientes-rows--stale">${stale.map((deal) => openRow(ctx, deal))}</ul>
      </section>`
    : '';
  return html`${warning}${liveGroup}${staleGroup}`;
}

/* Painel: aba Fechadas */

function monthChart(ctx, months) {
  const { html } = ctx.dom;
  const { fmt } = ctx;
  const max = Math.max(1, ...months.map((m) => Number(m.won_count) || 0));
  const label = `Vendas por mês: ${months.map((m) => `${m.label} ${fmt.plural(m.won_count, 'venda')}`).join(', ')}.`;
  return html`<div class="clientes-chart" role="img" aria-label="${label}">
      <div class="clientes-chart__bars">${months.map((m) => {
        const height = m.won_count > 0 ? Math.max(2, Math.round((m.won_count / max) * CHART_HEIGHT)) : 0;
        return html`<span class="clientes-chart__bar${m.quarter_end ? ' is-quarter-end' : ''}" style="height: ${height}px" title="${m.label}: ${fmt.plural(m.won_count, 'venda')}"></span>`;
      })}</div>
      <div class="clientes-chart__labels" aria-hidden="true">${months.map(
        (m) => html`<span class="${m.quarter_end ? 'is-quarter-end' : ''}">${m.label}</span>`,
      )}</div>
    </div>`;
}

function closedRow(ctx, deal) {
  const { html } = ctx.dom;
  const { fmt } = ctx;
  const result = deal.won
    ? html`<span class="clientes-row__result is-win">${fmt.money(deal.close_value)}</span>`
    : html`<span class="clientes-row__result is-loss">Perdida</span>`;
  return html`<li class="clientes-row clientes-row--closed">
    <span class="clientes-row__date">${deal.close_label}</span>
    <div class="clientes-row__main">
      <p class="clientes-row__title"><b>${deal.product}</b> · #${deal.id}</p>
      <p class="clientes-row__meta">${sellerPart(ctx, deal)} · ciclo de ${fmt.plural(deal.cycle_days, 'dia')}</p>
    </div>
    ${result}
  </li>`;
}

function closedTab(ctx, data) {
  const { html } = ctx.dom;
  const { fmt, ui } = ctx;
  const closed = data.closed || {};
  const deals = closed.deals || [];
  if (!deals.length) {
    return ui.empty('Nenhum deal fechado com este cliente até esta data.');
  }
  const showAll = view.showAllClosed;
  const visible = showAll ? deals : deals.slice(0, RECENT_LIMIT);
  const months = closed.by_month || [];
  return html`<div class="clientes-stats clientes-stats--closed">
      <div><p class="clientes-stats__big is-win">${fmt.number(closed.won_count)}</p><p class="clientes-stats__label">ganhas</p></div>
      <div><p class="clientes-stats__big is-loss">${fmt.number(closed.lost_count)}</p><p class="clientes-stats__label">perdidas</p></div>
      <div class="clientes-stats__wide"><p class="clientes-stats__big">${fmt.money(closed.won_value)}</p><p class="clientes-stats__label">${closed.value_label || ''}</p></div>
    </div>
    ${months.length
      ? html`<section class="clientes-block clientes-block--ruled" aria-labelledby="clientes-meses">
          <h3 class="eyebrow" id="clientes-meses">Vendas por mês em 2017</h3>
          ${monthChart(ctx, months)}
          ${closed.month_sentence ? html`<p class="clientes-muted">${closed.month_sentence}</p>` : ''}
        </section>`
      : ''}
    <section class="clientes-group clientes-block--ruled" aria-label="Fechadas mais recentes">
      ${sectionLabel(ctx, 'Mais recentes', 'Resultado')}
      <ul class="clientes-rows" data-closed-list tabindex="-1">${visible.map((deal) => closedRow(ctx, deal))}</ul>
    </section>
    ${!showAll && deals.length > RECENT_LIMIT
      ? html`<button type="button" class="btn btn--secondary btn--block clientes-more" data-show-all>${`Ver as ${fmt.number(deals.length)} fechadas`}</button>`
      : ''}`;
}

/* Painel lateral */

function tabsHtml(ctx, data, active) {
  const { ui } = ctx;
  const open = data?.open;
  const closed = data?.closed;
  return ui.tabs({
    id: 'cliente',
    label: 'Partes da ficha do cliente',
    active,
    items: [
      { id: 'dados', label: 'Dados' },
      { id: 'em-aberto', label: 'Em aberto', count: open ? ctx.fmt.number(open.count ?? 0) : undefined },
      { id: 'fechadas', label: 'Fechadas', count: closed ? ctx.fmt.number(closed.count ?? 0) : undefined },
    ],
  });
}

function tabContent(ctx, data, tab) {
  if (tab === 'em-aberto') return openTab(ctx, data);
  if (tab === 'fechadas') return closedTab(ctx, data);
  return dataTab(ctx, data);
}

function drawTab(ctx) {
  const panel = view.panel;
  if (!panel || !view.panelData) return;
  const host = panel.el.querySelector('#cliente-panel');
  if (!host) return;
  host.setAttribute('aria-labelledby', `cliente-tab-${view.panelTab}`);
  ctx.dom.setHtml(host, tabContent(ctx, view.panelData, view.panelTab));
  ctx.dom.qsa('[role="tab"]', panel.el).forEach((tab) => {
    const on = tab.dataset.value === view.panelTab;
    tab.setAttribute('aria-selected', String(on));
    tab.tabIndex = on ? 0 : -1;
  });
}

function drawPanel(ctx, data) {
  const { html } = ctx.dom;
  const panel = view.panel;
  view.panelData = data;
  panel.setHeader({ eyebrow: 'Cliente', title: data.account.name, subtitle: data.account.subtitle });
  panel.setContent(html`${tabsHtml(ctx, data, view.panelTab)}${ctx.ui.tabPanel('cliente', view.panelTab, '')}`);
  drawTab(ctx);
}

function loadPanel(ctx) {
  const key = `${normalize(view.panelName)}|${ctx.date}`;
  view.panelKey = key;
  view.panelData = null;
  view.showAllClosed = false;
  const panel = view.panel;
  return ctx.ui.load(
    panel.body,
    // A regra de Sem desfecho ("mais de 138 dias") vem do modelo, como no Foco e no Pipeline.
    async () => {
      const [account, model] = await Promise.all([
        ctx.api.get('account', { name: view.panelName, viewer: ctx.user.name, date: ctx.date }),
        ctx.api.get('score-model', { date: ctx.date }),
      ]);
      return { ...account, staleRule: model.bands?.stale?.rule || '' };
    },
    (data) => {
      if (view?.panel !== panel || view.panelKey !== key) return;
      drawPanel(ctx, data);
    },
    { skeleton: { title: false, lines: 3, blocks: 3 }, errorTitle: 'Não foi possível abrir a ficha do cliente.' },
  );
}

function rowLink(name) {
  if (!view?.wrap) return null;
  const wanted = normalize(name);
  return (
    Array.from(view.wrap.querySelectorAll('[data-cliente-link]')).find(
      (link) => normalize(link.closest('tr')?.dataset.cliente) === wanted,
    ) || null
  );
}

function openClientPanel(ctx) {
  const name = view.panelName;
  // Solta o painel anterior antes: o onClose dele ('replaced') não deve limpar o estado do novo.
  view.panel = null;
  const panel = ctx.ui.openPanel({
    className: 'clientes-painel',
    eyebrow: 'Cliente',
    title: name,
    content: '',
    returnFocus: () => rowLink(name),
    onClose: (reason) => {
      if (view?.panel !== panel) return;
      view.panel = null;
      view.panelName = '';
      view.panelData = null;
      view.panelKey = '';
      markSelected(ctx);
      if (reason === 'user') {
        view.ctx.navigate('clientes', { regional: view.region.value }, { replace: true });
      }
    },
  });
  view.panel = panel;

  // Ouvintes no próprio painel: somem com ele.
  ctx.ui.bindTabs(panel.el, (tab) => {
    view.panelTab = tab;
    drawTab(view.ctx);
    view.ctx.navigate('clientes', { ...view.ctx.params, aba: tab }, { replace: true });
  });
  ctx.dom.on(panel.el, 'click', '[data-show-all]', () => {
    view.showAllClosed = true;
    drawTab(view.ctx);
    panel.el.querySelector('[data-closed-list]')?.focus({ preventScroll: true });
  });
  return panel;
}

function syncPanel(ctx) {
  const wanted = String(ctx.params.cliente || '').trim();
  const tab = tabFromParam(ctx.params.aba);
  if (!wanted) {
    if (view.panel) ctx.ui.closePanel('route');
    return;
  }
  const sameClient = view.panel && normalize(view.panelName) === normalize(wanted);
  if (sameClient && view.panelKey === `${normalize(wanted)}|${ctx.date}` && view.panelData) {
    if (view.panelTab !== tab) {
      view.panelTab = tab;
      drawTab(ctx);
    }
    return;
  }
  view.panelTab = tab;
  view.panelName = wanted;
  if (!sameClient) openClientPanel(ctx);
  markSelected(ctx);
  loadPanel(ctx);
}

/* Tela */

function pageHtml(ctx, region) {
  const { html } = ctx.dom;
  const { ui, icon } = ctx;
  return html`<div class="clientes">
    ${ui.screenHeader({ eyebrow: 'Clientes', title: 'Clientes', subtitle: html`<span data-subtitle></span>` })}
    <div class="clientes-toolbar">
      ${ui.chips(REGIONS.map((r) => ({ value: r.value, label: r.label })), { value: region.value, label: 'Regional de casa do cliente' })}
      <div class="clientes-search">
        <label class="sr-only" for="clientes-busca">Buscar cliente pelo nome</label>
        ${icon('search', { size: 16 })}
        <input id="clientes-busca" class="clientes-search__input" type="search" placeholder="Buscar cliente" autocomplete="off" spellcheck="false" data-search value="${view.search}">
      </div>
    </div>
    <p class="sr-only" role="status" data-filter-status></p>
    <div class="clientes-body" data-table></div>
  </div>`;
}

function bindPage(ctx) {
  const { on } = ctx.dom;
  const wrap = view.wrap;
  on(wrap, 'click', '[data-chip]', (event, chip) => {
    const value = chip.dataset.chip;
    if (value === view.region.value) return;
    view.ctx.navigate('clientes', { ...view.ctx.params, regional: value }, { replace: true });
  });
  on(wrap, 'input', '[data-search]', (event, input) => {
    view.search = input.value;
    applyFilter(view.ctx);
  });
  // A linha inteira abre o painel; o link do nome é o alvo de teclado.
  on(wrap, 'click', 'tbody tr[data-cliente]', (event, row) => {
    if (event.target.closest('a')) return;
    row.querySelector('[data-cliente-link]')?.click();
  });
}

function setChips(ctx, region) {
  ctx.dom.qsa('[data-chip]', view.wrap).forEach((chip) => {
    chip.setAttribute('aria-pressed', String(chip.dataset.chip === region.value));
  });
}

export default {
  id: 'clientes',
  title: 'Clientes',
  roles: ['seller', 'manager'],
  area: 'vendas',

  async render(root, ctx) {
    const region = regionFromParam(ctx.params.regional, ctx.user);
    const reuse = ctx.reason === 'params' && view?.wrap?.isConnected && root.contains(view.wrap);

    if (!reuse) {
      view = {
        ctx,
        wrap: null,
        region,
        // A busca só sobrevive à troca de parâmetro; outra pessoa ou outra data começa sem filtro.
        search: ctx.reason === 'params' ? view?.search ?? '' : '',
        tableKey: '',
        tableReady: false,
        panel: null,
        panelName: '',
        panelTab: 'dados',
        panelKey: '',
        panelData: null,
        showAllClosed: false,
      };
      ctx.dom.setHtml(root, pageHtml(ctx, region));
      view.wrap = root.querySelector('.clientes');
      bindPage(ctx);
    }
    view.ctx = ctx;
    view.region = region;
    setChips(ctx, region);

    // O cabeçalho já está desenhado; a moldura põe o foco nele antes de o painel abrir.
    await null;
    if (view?.ctx !== ctx) return undefined;

    if (!view.tableReady || view.tableKey !== `${region.value}|${ctx.date}`) loadTable(ctx, region);
    syncPanel(ctx);
    return undefined;
  },
};
