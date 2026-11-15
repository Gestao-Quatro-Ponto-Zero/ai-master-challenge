// Meu time: a visão do gestor (prancha 03). Escopo na URL: ?regional=&gestor=&vendedor=.
// Sem ?gestor= vale o próprio usuário; ?gestor=todos tira o filtro de gestor.
import { prefs } from '../core/state.js';

const ALL_MANAGERS = 'todos';
const MODE_PREF = 'time:leitura';
const MODES = [
  { value: 'lado', label: 'Lado a lado' },
  { value: 'declarado', label: 'Declarado' },
  { value: 'real', label: 'Real' },
];
const MAX_CHIPS = 6;

// Palavra do escopo nas frases fixas da tela ("do time", "a regional declara").
const NOUNS = {
  time: { of: 'do time', subject: 'o time', each: 'Há uma para cada vendedor do time.' },
  regional: { of: 'da regional', subject: 'a regional', each: 'Há uma para cada vendedor da regional.' },
  empresa: { of: 'da empresa', subject: 'a empresa', each: 'Há uma para cada vendedor da empresa.' },
  carteira: { of: 'da carteira', subject: 'a carteira', each: '' },
};

const sameName = (a, b) => String(a ?? '').toLowerCase() === String(b ?? '').toLowerCase();

// Sem armazenamento (janela privada), o modo escolhido vale enquanto a página estiver aberta.
let readingMode = null;

function savedMode() {
  if (!readingMode) {
    const value = prefs.get(MODE_PREF, null);
    readingMode = MODES.some((mode) => mode.value === value) ? value : 'lado';
  }
  return readingMode;
}

function rememberMode(value) {
  readingMode = value;
  prefs.set(MODE_PREF, value);
}

/* Escopo: URL <-> filtros */

function readScope(ctx) {
  const { meta, params, user } = ctx;
  const region = meta.regions.find((r) => sameName(r.key, params.regional) || sameName(r.label, params.regional));
  let manager = null;
  if (!params.gestor) manager = meta.managers.find((m) => sameName(m.name, user.name)) || null;
  else if (!sameName(params.gestor, ALL_MANAGERS)) manager = meta.managers.find((m) => sameName(m.name, params.gestor)) || null;
  let seller = params.vendedor ? meta.sellers.find((s) => sameName(s.name, params.vendedor)) || null : null;

  // Combinações impossíveis vindas da URL caem para a parte mais ampla, em vez de virar erro.
  let regionKey = region ? region.key : null;
  if (manager && regionKey && manager.region !== regionKey) manager = null;
  if (seller && manager && !sameName(seller.manager, manager.name)) seller = null;
  if (seller && regionKey && seller.region !== regionKey) seller = null;
  if (manager) regionKey = null;
  return { region: regionKey, manager: manager ? manager.name : null, seller: seller ? seller.name : null };
}

function scopeParams(ctx, scope) {
  const own = scope.manager && sameName(scope.manager, ctx.user.name);
  return {
    regional: scope.region || undefined,
    gestor: own ? undefined : scope.manager || ALL_MANAGERS,
    vendedor: scope.seller || undefined,
  };
}

function regionOf(ctx, scope) {
  if (scope.region) return scope.region;
  const manager = ctx.meta.managers.find((m) => sameName(m.name, scope.manager));
  if (manager) return manager.region;
  const seller = ctx.meta.sellers.find((s) => sameName(s.name, scope.seller));
  return seller ? seller.region : null;
}

function nextScope(ctx, scope, which, value) {
  const sellerInfo = ctx.meta.sellers.find((s) => sameName(s.name, scope.seller));
  if (which === 'regional') {
    if (!value) return { region: null, manager: null, seller: null };
    const managerInfo = ctx.meta.managers.find((m) => sameName(m.name, scope.manager));
    const manager = managerInfo && managerInfo.region === value ? managerInfo.name : null;
    const sellerFits = sellerInfo && sellerInfo.region === value && (!manager || sameName(sellerInfo.manager, manager));
    return { region: manager ? null : value, manager, seller: sellerFits ? sellerInfo.name : null };
  }
  if (which === 'gestor') {
    if (!value) {
      const region = regionOf(ctx, scope);
      return { region, manager: null, seller: sellerInfo && sellerInfo.region === region ? sellerInfo.name : null };
    }
    return { region: null, manager: value, seller: sellerInfo && sameName(sellerInfo.manager, value) ? sellerInfo.name : null };
  }
  return { ...scope, seller: value || null };
}

function nounFor(data) {
  if (data.scope.seller) return 'carteira';
  if (data.scope.manager) return 'time';
  if (data.scope.region) return 'regional';
  return 'empresa';
}

/* Marcação */

function headerHtml(ctx) {
  const { ui } = ctx;
  return ui.screenHeader({
    eyebrow: ctx.dateInfo ? ctx.dateInfo.label_long : '',
    title: `Bom dia, ${ctx.user.first_name}.`,
    subtitle: ctx.dom.html`<span data-time-headline></span>`,
    aside: ctx.dom.html`<div class="time-filters" data-time-filters aria-busy="true"></div>`,
  });
}

function filtersHtml(ctx, data, scope) {
  const { ui, dom } = ctx;
  const regionKey = regionOf(ctx, scope);
  const region = data.options.regions.find((r) => r.key === regionKey);
  const sellerCount = data.options.sellers.length;
  return dom.html`<div class="time-filters__row" role="group" aria-label="Escopo da visão">
      ${ui.selectButton({ label: 'Regional', value: region ? region.label : 'Todas', attrs: { 'data-time-filter': 'regional' } })}
      ${ui.selectButton({ label: 'Gestor', value: scope.manager || 'Todos', attrs: { 'data-time-filter': 'gestor' } })}
      ${ui.selectButton({
        label: 'Vendedor',
        value: scope.seller || (sellerCount === 1 ? 'Todos' : `Todos os ${sellerCount}`),
        attrs: { 'data-time-filter': 'vendedor' },
      })}
    </div>
    <p class="time-filters__note">Valores a preço de tabela</p>`;
}

function numbersHtml(ctx, data, noun, maxCycle) {
  const { ui, fmt, dom } = ctx;
  const s = data.summary;
  const words = NOUNS[noun];
  const liveSub = Number.isFinite(maxCycle)
    ? `${fmt.plural(s.live_count, 'deal')} com até ${fmt.number(maxCycle)} dias em negociação`
    : `${fmt.plural(s.live_count, 'deal')} em negociação dentro do prazo`;
  const livePct = fmt.percent(s.live_share);
  const stalePct = fmt.percent(s.stale_share);
  return dom.html`<section class="time-numbers" aria-labelledby="time-numbers-title">
    <h2 class="sr-only" id="time-numbers-title">Os números ${words.of}</h2>
    <div class="time-numbers__row">
      <div class="time-numbers__main">${ui.kpi({ label: `Pipeline vivo ${words.of}`, value: fmt.money(s.live_value), sub: liveSub, size: 'xl' })}</div>
      <div class="time-numbers__side">
        ${ui.kpi({ label: 'Declarado no CRM', value: fmt.money(s.declared_value), sub: `${fmt.plural(s.open_count, 'deal')} em negociação`, muted: true })}
        ${ui.kpi({ label: 'Sem desfecho', value: fmt.money(s.stale_value), sub: `${fmt.plural(s.stale_count, 'deal')} ${fmt.pluralWord(s.stale_count, 'parado', 'parados')}`, muted: true })}
        ${ui.kpi({ label: 'Esperado em 30 dias', value: fmt.money(s.expected_30d), sub: 'chance × valor dos vivos', divided: true })}
      </div>
    </div>
    <div class="time-numbers__bar">
      ${ui.dualBar({
        share: s.live_share,
        variant: 'thick',
        label: `${livePct} do que ${words.subject} declara ainda pode fechar; ${stalePct} passou do prazo sem ganho nem perda.`,
      })}
      <div class="dualbar__legend time-numbers__legend">
        <span class="time-numbers__live">${livePct} do que ${words.subject} declara ainda pode fechar</span>
        <span>${stalePct} passou do prazo sem ganho nem perda</span>
      </div>
    </div>
  </section>`;
}

function rateHtml(ctx, row) {
  const { fmt, dom } = ctx;
  const official = fmt.percent(row.rate_official, 1);
  const delta = Number(row.rate_delta_points) || 0;
  if (delta === 0) {
    return dom.html`<span class="time-rate">${official}</span><span class="time-rate__sub">não muda</span>`;
  }
  // A diferença sai das duas taxas já arredondadas, para a conta de cabeça bater com o que está na tela.
  const shown = Math.abs(Math.round(row.rate_official * 1000) - Math.round(row.rate_with_stale * 1000)) / 10;
  const points = fmt.number(shown, 1);
  const word = shown < 2 ? 'ponto' : 'pontos';
  return dom.html`<span class="time-rate">${official}<span aria-hidden="true"> → </span><span class="sr-only"> passa a </span>${fmt.percent(row.rate_with_stale, 1)}</span><span class="time-rate__sub">${points} ${word} a ${delta > 0 ? 'menos' : 'mais'}</span>`;
}

function rowsHtml(ctx, data, teamSet) {
  const { ui, fmt, dom } = ctx;
  const maxDeclared = Math.max(0, ...data.rows.map((r) => Number(r.declared_value) || 0));
  const width = (value) => (maxDeclared > 0 ? ((Number(value) || 0) / maxDeclared) * 100 : 0).toFixed(2);
  const body = data.rows.map((row) => {
    const inTeam = teamSet.has(row.name.toLowerCase());
    const href = ctx.href('foco', { vendedor: row.name });
    const name = inTeam
      ? dom.html`<a class="time-row__link" href="${href}">${row.name}</a>`
      : dom.html`<span>${row.name}</span>`;
    const label = `Vivo ${fmt.money(row.live_value)} de ${fmt.money(row.declared_value)} declarados`;
    return dom.html`<tr class="${inTeam ? 'is-clickable' : ''}"${ui.attrs({ 'data-href': inTeam ? href : null })}>
      <td class="time-col-seller">
        <div class="time-row__who">${ui.avatar(row.initials, { soft: true })}<div class="time-row__names"><div class="cell-title">${name}</div><div class="time-row__sub">${row.stale_label}</div></div></div>
      </td>
      <td class="time-col-bar">
        <div class="time-bar" role="img" aria-label="${label}">
          <span class="time-bar__declared" style="width: ${width(row.declared_value)}%"></span>
          <span class="time-bar__live" style="width: ${width(row.live_value)}%"></span>
        </div>
        <p class="time-bar__text">
          <span data-mode-text="lado"><b>${fmt.money(row.live_value)}</b> de ${fmt.money(row.declared_value)}</span>
          <span data-mode-text="declarado"><b>${fmt.money(row.declared_value)}</b> no CRM</span>
          <span data-mode-text="real"><b>${fmt.money(row.live_value)}</b> ainda podem fechar</span>
        </p>
      </td>
      <td class="is-num time-col-expected">${fmt.money(row.expected_30d)}</td>
      <td class="is-num time-col-rate"><div class="time-rate__cell">${rateHtml(ctx, row)}</div></td>
    </tr>`;
  });
  return ui.tableWrap(
    dom.html`<table class="table time-table">
      <caption class="sr-only">As duas leituras, por vendedor: vivo dentro do declarado, esperado em 30 dias e taxa de ganho</caption>
      <thead><tr>
        <th scope="col">Vendedor</th>
        <th scope="col">
          <span data-mode-text="lado">Vivo dentro do declarado</span>
          <span data-mode-text="declarado">Declarado no CRM</span>
          <span data-mode-text="real">Vivo, sem os sem desfecho</span>
        </th>
        <th scope="col" class="is-num">Esperado</th>
        <th scope="col" class="is-num">Taxa de ganho</th>
      </tr></thead>
      <tbody>${body}</tbody>
    </table>`,
    { label: 'Tabela de vendedores' },
  );
}

function tableSectionHtml(ctx, data, maxCycle, teamSet) {
  const { ui, dom, fmt } = ctx;
  const mode = savedMode();
  const outsideTeam = data.rows.some((row) => !teamSet.has(row.name.toLowerCase()));
  const staleLegend = Number.isFinite(maxCycle)
    ? `Declarado, mas sem desfecho há mais de ${fmt.number(maxCycle)} dias`
    : 'Declarado, mas sem desfecho';
  return dom.html`<section class="time-section" aria-labelledby="time-table-title">
    <div class="time-section__head">
      <h2 class="time-section__title" id="time-table-title">As duas leituras, por vendedor</h2>
      ${ui.segmented({ label: 'Leitura do pipeline de cada vendedor', items: MODES, value: mode })}
    </div>
    ${data.rows.length
      ? dom.html`<div class="time-table-wrap" data-time-mode="${mode}">${rowsHtml(ctx, data, teamSet)}</div>
        <div class="time-legend">
          <div class="time-legend__keys">
            <span class="time-legend__key"><span class="time-legend__live" aria-hidden="true"></span>Vivo</span>
            <span class="time-legend__key"><span class="time-legend__rest" aria-hidden="true"></span>${staleLegend}</span>
          </div>
          <p>Taxa de ganho: a oficial e, depois da seta, a que conta os deals sem desfecho como não ganhos.</p>
          ${outsideTeam ? dom.html`<p>O nome leva ao foco da semana só para os vendedores do seu time.</p>` : ''}
        </div>`
      : ui.empty('Nenhum vendedor com deals neste escopo na data escolhida.', { title: 'Nada para mostrar' })}
  </section>`;
}

function messageLabel(messages, item) {
  const repeated = messages.filter((m) => sameName(m.first_name, item.first_name)).length > 1;
  return repeated ? item.seller : item.first_name;
}

function messageChooserHtml(ctx, messages, current) {
  const { ui, dom } = ctx;
  if (messages.length < 2) return '';
  if (messages.length <= MAX_CHIPS) {
    return ui.chips(
      messages.map((m) => ({ value: m.seller, label: messageLabel(messages, m) })),
      { value: current.seller, label: 'Mensagem de qual vendedor' },
    );
  }
  return dom.html`<div>${ui.selectButton({ label: 'Mensagem de', value: current.seller, attrs: { 'data-time-message-pick': true } })}</div>`;
}

function messageCardHtml(ctx, current, noun) {
  const { ui, dom, icon } = ctx;
  return dom.html`<div class="time-message__card">
    ${ui.avatar(current.initials, { soft: true })}
    <div class="time-message__body">
      <p class="time-message__text" id="time-message-text">${current.text}</p>
      <div class="time-message__actions">
        <button type="button" class="btn btn--primary btn--sm" data-time-copy aria-describedby="time-message-text">${icon('copy', { size: 14 })}<span>Copiar mensagem</span></button>
        ${NOUNS[noun].each ? dom.html`<span class="time-message__hint">${NOUNS[noun].each}</span>` : ''}
      </div>
    </div>
  </div>`;
}

function messagesSectionHtml(ctx, data, current, noun) {
  const { ui, dom } = ctx;
  return dom.html`<section class="time-section time-message" aria-labelledby="time-message-title">
    <div class="time-section__intro">
      <h2 class="time-section__title" id="time-message-title">Para quem não abre o sistema</h2>
      <p class="section-sub">O foco da semana de cada vendedor vira uma mensagem pronta. Você copia e envia.</p>
    </div>
    ${data.messages.length
      ? dom.html`<div data-time-message-chooser>${messageChooserHtml(ctx, data.messages, current)}</div>
        <div data-time-message>${messageCardHtml(ctx, current, noun)}</div>`
      : ui.empty('Nenhuma mensagem para este escopo na data escolhida.')}
  </section>`;
}

// Quem do escopo tem mais deals no campo pedido. O foco da semana só abre vendedor do time do usuário,
// então, se o primeiro for de outro time, o cartão fica sem link em vez de levar para outra pessoa.
function topTeamSeller(data, teamSet, field) {
  const candidates = data.rows.filter((row) => Number(row[field]) > 0);
  if (!candidates.length) return null;
  const top = candidates.reduce((best, row) => (row[field] > best[field] ? row : best));
  return teamSet.has(top.name.toLowerCase()) ? top : null;
}

const FOCUS_LINKS = {
  sem_desfecho: { field: 'stale_count', tab: 'sem_desfecho' },
  quentes: { field: 'hot_count', tab: 'quente' },
};

// O link_label da API fala do escopo inteiro ("Ver os 153 deals"), mas o foco da semana abre um vendedor
// só. Para o número do link bater com o que abre, o texto passa a nomear esse vendedor e a contagem dele.
// A frase do cartão continua a da API.
function agendaCard(ctx, card, data, teamSet) {
  const link = FOCUS_LINKS[card.link_target];
  const top = link ? topTeamSeller(data, teamSet, link.field) : null;
  if (!top) return ctx.ui.gabiCard(card, { href: null });
  return ctx.ui.gabiCard(
    { ...card, link_label: `Ver os ${ctx.fmt.number(top[link.field])} de ${top.name}` },
    { href: ctx.href('foco', { vendedor: top.name, aba: link.tab }) },
  );
}

function agendaHtml(ctx, data, teamSet) {
  const { ui, dom } = ctx;
  return dom.html`${ui.gabiHead({ title: 'Pauta da Gabi', subtitle: 'O que levar para a reunião do time' })}
    ${data.agenda.length
      ? data.agenda.map((card) => agendaCard(ctx, card, data, teamSet))
      : ui.empty('A Gabi não tem pauta para este escopo na data escolhida.')}`;
}

function scopeBannerHtml(ctx, data, own) {
  const { ui, dom } = ctx;
  if (own) return '';
  return ui.banner(
    dom.html`Você está vendo: <strong>${data.scope.title}</strong>. ${ui.linkArrow('Voltar para o meu time', ctx.href('time'))}`,
    { iconName: 'users' },
  );
}

/* Tela */

export default {
  id: 'time',
  title: 'Meu time',
  roles: ['manager'],
  area: 'vendas',

  render(root, ctx) {
    const { dom, ui } = ctx;
    const scope = readScope(ctx);
    const keepFocus = ctx.reason === 'params' ? document.activeElement?.getAttribute('data-time-filter') : null;

    dom.setHtml(root, dom.html`${headerHtml(ctx)}<div class="time-body" data-time-body></div>`);

    const filters = root.querySelector('[data-time-filters]');
    const headline = root.querySelector('[data-time-headline]');
    const body = root.querySelector('[data-time-body]');
    const teamSet = new Set((ctx.user.team || []).map((name) => name.toLowerCase()));
    const state = { data: null, current: null, noun: 'time' };

    const apiParams = {
      date: ctx.date,
      region: scope.manager ? undefined : scope.region || undefined,
      manager: scope.manager || undefined,
      seller: scope.seller || undefined,
    };

    const draw = ([data, model]) => {
      const maxCycle = Number(model?.max_cycle);
      const own = !data.scope.seller && !data.scope.region && sameName(data.scope.manager, ctx.user.name);
      state.data = data;
      state.noun = nounFor(data);
      state.current = data.messages[0] || null;
      headline.textContent = data.summary.headline;
      filters.removeAttribute('aria-busy');
      dom.setHtml(filters, filtersHtml(ctx, data, scope));
      dom.setHtml(body, dom.html`${scopeBannerHtml(ctx, data, own)}
        ${data.summary.open_count
          ? numbersHtml(ctx, data, state.noun, maxCycle)
          : ui.empty('Ninguém neste escopo tem deal em negociação na data escolhida.', { title: 'Nada em negociação' })}
        <div class="with-aside time-columns">
          <div class="with-aside__main time-main">
            ${tableSectionHtml(ctx, data, maxCycle, teamSet)}
            ${messagesSectionHtml(ctx, data, state.current, state.noun)}
          </div>
          <aside class="with-aside__aside time-agenda" aria-label="Pauta da Gabi">${agendaHtml(ctx, data, teamSet)}</aside>
        </div>`);
      if (keepFocus) filters.querySelector(`[data-time-filter="${keepFocus}"]`)?.focus({ preventScroll: true });
    };

    const run = async () => {
      ui.showLoading(body, { title: false, lines: 2, blocks: 5 });
      try {
        const [data, model] = await Promise.all([
          ctx.api.get('team', apiParams),
          // Só o limite de dias sem desfecho; se falhar, a tela segue sem o número.
          ctx.api.get('score-model', { date: ctx.date }).catch((error) => {
            if (error?.name === 'AbortError') throw error;
            return null;
          }),
        ]);
        body.removeAttribute('aria-busy');
        draw([data, model]);
      } catch (error) {
        if (error?.name === 'AbortError') return;
        filters.removeAttribute('aria-busy');
        ui.showError(body, error, run, { title: 'Não foi possível carregar o time.' });
        const own = !ctx.params.regional && !ctx.params.gestor && !ctx.params.vendedor;
        if (!own) body.querySelector('.state__actions')?.append(dom.toFragment(ui.linkArrow('Voltar para o meu time', ctx.href('time'))));
      }
    };

    const go = (next) => ctx.navigate('time', scopeParams(ctx, next), { replace: true });

    // Em reason 'params' o root é reaproveitado: os ouvintes saem na limpeza para não se acumularem.
    const offs = [];
    offs.push(dom.on(root, 'click', '[data-time-filter]', (event, button) => {
      const data = state.data;
      if (!data) return;
      const which = button.dataset.timeFilter;
      const all = { value: '', label: which === 'regional' ? 'Todas' : 'Todos' };
      let options;
      let value;
      if (which === 'regional') {
        options = [all, ...data.options.regions.map((r) => ({ value: r.key, label: r.label }))];
        value = regionOf(ctx, scope) || '';
      } else if (which === 'gestor') {
        options = [all, ...data.options.managers.map((m) => ({ value: m.name, label: m.name, hint: m.region_label }))];
        value = scope.manager || '';
      } else {
        options = [{ ...all, hint: String(data.options.sellers.length) }, ...data.options.sellers.map((name) => ({ value: name, label: name }))];
        value = scope.seller || '';
      }
      ui.openPicker(button, {
        label: which === 'regional' ? 'Regional' : which === 'gestor' ? 'Gestor' : 'Vendedor',
        options,
        value,
        minWidth: 240,
        onSelect: (picked) => go(nextScope(ctx, scope, which, picked)),
      });
    }));

    offs.push(dom.on(root, 'click', 'tr[data-href]', (event, row) => {
      if (event.target.closest('a, button')) return;
      window.location.hash = row.dataset.href;
    }));

    offs.push(ui.bindSegmented(root, (value) => {
      rememberMode(value);
      root.querySelector('[data-time-mode]')?.setAttribute('data-time-mode', value);
    }));

    const showMessage = (seller) => {
      const item = state.data?.messages.find((m) => m.seller === seller);
      if (!item) return;
      state.current = item;
      dom.setHtml(root.querySelector('[data-time-message]'), messageCardHtml(ctx, item, state.noun));
    };

    offs.push(dom.on(root, 'click', '[data-time-message-chooser] [data-chip]', (event, chip) => {
      dom.qsa('[data-chip]', chip.parentElement).forEach((other) => other.setAttribute('aria-pressed', String(other === chip)));
      showMessage(chip.dataset.chip);
    }));

    offs.push(dom.on(root, 'click', '[data-time-message-pick]', (event, button) => {
      ui.openPicker(button, {
        label: 'Mensagem de qual vendedor',
        options: state.data.messages.map((m) => ({ value: m.seller, label: m.seller })),
        value: state.current?.seller,
        minWidth: 240,
        onSelect: (seller) => {
          showMessage(seller);
          const value = button.querySelector('.select-btn__value');
          if (value) value.textContent = seller;
        },
      });
    }));

    offs.push(dom.on(root, 'click', '[data-time-copy]', () => {
      if (state.current) ui.copyText(state.current.text, { success: 'Mensagem copiada' });
    }));

    run();
    return () => offs.forEach((off) => off());
  },
};
