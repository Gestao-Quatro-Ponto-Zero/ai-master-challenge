// Construtores das peças comuns. Os que devolvem marcação devolvem html`` (já escapado) para usar dentro
// de outro html`` ou em setHtml(). Os que mexem na página (load, openPanel, openPicker, toast) dizem isso.
import { escapeHtml, focusables, h, html, on, qsa, raw, setHtml } from './dom.js';
import { icon } from './icons.js';
import { isAbort } from './api.js';
import { STALE_DECISIONS } from './marks.js';

let uid = 0;
const nextId = (prefix) => `${prefix}-${(uid += 1)}`;

// { 'data-x': 'a', disabled: true } -> ' data-x="a" disabled'. As chaves vêm do código; os valores são escapados.
export function attrs(map = {}) {
  return raw(
    Object.entries(map)
      .filter(([, value]) => value !== null && value !== undefined && value !== false)
      .map(([key, value]) => (value === true ? ` ${key}` : ` ${key}="${escapeHtml(value)}"`))
      .join(''),
  );
}

/* Textos e títulos */

export function eyebrow(text, { id } = {}) {
  return html`<p class="eyebrow"${attrs({ id })}>${text}</p>`;
}

// Cabeçalho de tela: rótulo, h1, subtítulo e um lado direito opcional (marcação).
export function screenHeader({ eyebrow: label, title, subtitle, aside } = {}) {
  return html`<header class="screen-head">
    <div class="screen-head__text">
      ${label ? eyebrow(label) : ''}
      <h1 class="screen-title" id="screen-title" tabindex="-1">${title}</h1>
      ${subtitle ? html`<p class="screen-sub">${subtitle}</p>` : ''}
    </div>
    ${aside ? html`<div class="screen-head__aside">${aside}</div>` : ''}
  </header>`;
}

/* Botões e links */

// variant: 'primary' | 'secondary' | 'ghost'; size: 'sm' | 'lg'
export function button(label, { variant = 'secondary', size, iconName, iconAfter, block, disabled, type = 'button', attrs: extra } = {}) {
  const classes = ['btn', `btn--${variant}`, size && `btn--${size}`, block && 'btn--block'].filter(Boolean).join(' ');
  return html`<button type="${type}" class="${classes}"${attrs({ disabled, ...extra })}>${iconName ? icon(iconName, { size: 16 }) : ''}<span>${label}</span>${iconAfter ? icon(iconAfter, { size: 16, stroke: 2 }) : ''}</button>`;
}

export function linkArrow(label, href, extra = {}) {
  return html`<a class="link-arrow" href="${href}"${attrs(extra)}>${label}${icon('arrowRight', { size: 14, stroke: 2 })}</a>`;
}

/* Selos, avatar */

// tone: 'neutral' | 'concept' | 'win' | 'loss'
export function badge(text, { tone = 'neutral', dot = false } = {}) {
  return html`<span class="badge${tone === 'neutral' ? '' : ` badge--${tone}`}${dot ? ' badge--dot' : ''}">${text}</span>`;
}

// O selo acompanha o nome do módulo em todas as telas; o aviso completo aparece ao passar o mouse.
export const CONCEPT_NOTE = 'Conceito criado para o AI Master Challenge. Não é um produto oficial do G4.';

export function conceptBadge() {
  return html`<span class="badge badge--concept" title="${CONCEPT_NOTE}">Conceito<span class="sr-only">. ${CONCEPT_NOTE}</span></span>`;
}

export function avatar(initials, { soft = false } = {}) {
  return html`<span class="avatar${soft ? ' avatar--soft' : ''}" aria-hidden="true">${initials}</span>`;
}

/* Filtros, abas, alternador */

// items: [{ value, label, count }]; o ativo recebe aria-pressed="true". Ouça cliques em [data-chip].
export function chips(items, { value, label } = {}) {
  return html`<div class="chips" role="group"${attrs({ 'aria-label': label })}>${items.map(
    (item) => html`<button type="button" class="chip" data-chip="${item.value}" aria-pressed="${String(item.value === value)}">${item.label}${
      item.count !== undefined && item.count !== null ? html` <span class="num">${item.count}</span>` : ''
    }</button>`,
  )}</div>`;
}

// Abas: tabs({ id: 'foco', label: 'Faixas de score', items: [{ id, label, count, hint, separatorBefore }], active }).
// active null deixa nenhuma aba selecionada (um filtro que atravessa as abas, por exemplo); a primeira
// continua alcançável pelo Tab. Use com tabPanel(id, active, conteúdo) e bindTabs(container, onSelect).
export function tabs({ id, label, items, active }) {
  const tabbable = items.some((item) => item.id === active) ? active : items[0]?.id;
  return html`<div class="tabs" role="tablist"${attrs({ 'aria-label': label })}>${items.map((item) => {
    const selected = item.id === active;
    return html`${item.separatorBefore ? html`<span class="tabs__sep" aria-hidden="true"></span>` : ''}<button type="button" role="tab" class="tab" id="${id}-tab-${item.id}" data-value="${item.id}" aria-controls="${id}-panel" aria-selected="${String(selected)}" tabindex="${item.id === tabbable ? 0 : -1}">${item.label}${tabCount(item.count, item.hint)}</button>`;
  })}</div>`;
}

// Contagem da aba ("47") e dica opcional ("· mais de 138 dias"). A dica fica num span próprio para que,
// em tela mais estreita, só a aba ativa a mostre (components.css).
export function tabCount(count, hint) {
  const hasCount = count !== undefined && count !== null && count !== '';
  const hasHint = hint !== undefined && hint !== null && hint !== '';
  if (!hasCount && !hasHint) return '';
  return html`<span class="tab__count">${hasCount ? count : ''}${hasHint ? html`<span class="tab__hint">${hasCount ? ' · ' : ''}${hint}</span>` : ''}</span>`;
}

export function tabPanel(id, active, content) {
  return html`<div class="tabpanel" role="tabpanel" id="${id}-panel" aria-labelledby="${id}-tab-${active}" tabindex="0">${content}</div>`;
}

// Alternador de opção única (role radiogroup): segmented({ label, items: [{ value, label, iconName }], value, size: 'lg' })
export function segmented({ label, items, value, size }) {
  return html`<div class="segmented${size ? ` segmented--${size}` : ''}" role="radiogroup"${attrs({ 'aria-label': label })}>${items.map((item) => {
    const checked = item.value === value;
    return html`<button type="button" role="radio" class="segmented__item" data-value="${item.value}" aria-checked="${String(checked)}" tabindex="${checked ? 0 : -1}">${
      item.iconName ? icon(item.iconName, { size: 16 }) : ''
    }<span>${item.label}</span></button>`;
  })}</div>`;
}

// Foco itinerante: clique e setas selecionam e chamam onSelect(valor, elemento).
function bindRoving(container, { group, item, attr, onSelect }) {
  const select = (el, focus) => {
    qsa(item, el.closest(group)).forEach((other) => {
      const isOn = other === el;
      other.setAttribute(attr, String(isOn));
      other.tabIndex = isOn ? 0 : -1;
    });
    if (attr === 'aria-selected') {
      document.getElementById(el.getAttribute('aria-controls'))?.setAttribute('aria-labelledby', el.id);
    }
    if (focus) el.focus();
    onSelect(el.dataset.value, el);
  };
  const offClick = on(container, 'click', item, (event, el) => {
    if (el.getAttribute(attr) !== 'true') select(el, false);
  });
  const offKey = on(container, 'keydown', item, (event, el) => {
    const items = qsa(item, el.closest(group)).filter((other) => !other.disabled);
    const index = items.indexOf(el);
    const moves = {
      ArrowRight: index + 1,
      ArrowDown: index + 1,
      ArrowLeft: index - 1,
      ArrowUp: index - 1,
      Home: 0,
      End: items.length - 1,
    };
    if (!(event.key in moves) || items.length === 0) return;
    event.preventDefault();
    select(items[(moves[event.key] + items.length) % items.length], true);
  });
  return () => {
    offClick();
    offKey();
  };
}

// Liga as abas de `container`: onSelect(idDaAba, botão). Devolve a função que desliga.
export function bindTabs(container, onSelect) {
  return bindRoving(container, { group: '[role="tablist"]', item: '[role="tab"]', attr: 'aria-selected', onSelect });
}

export function bindSegmented(container, onSelect) {
  return bindRoving(container, { group: '[role="radiogroup"]', item: '[role="radio"]', attr: 'aria-checked', onSelect });
}

// Decisão local sobre um deal sem desfecho (Segue de pé / Encerrar), igual no Foco e no Pipeline.
// Ouça cliques em [data-decide]; clicar de novo na escolhida desfaz. short: rótulos curtos (cartão estreito).
export function decisionButtons(deal, decision, { short = false } = {}) {
  return html`<div class="decide-group" role="group" aria-label="${`Decisão sobre o deal #${deal.id}`}">${Object.entries(STALE_DECISIONS).map(
    ([value, text]) => html`<button type="button" class="decide decide--${value}" data-decide="${value}" data-deal-id="${deal.id}" data-key="decide:${deal.id}:${value}" aria-pressed="${String(decision === value)}"${attrs({
      'aria-label': short ? text.label : null,
    })}>${decision === value ? icon('check', { size: 12, stroke: 2.6 }) : ''}<span>${short ? text.short : text.label}</span></button>`,
  )}</div>`;
}

/* Blocos */

export function note(content) {
  return html`<div class="note">${content}</div>`;
}

// Alerta dourado: no máximo um destaque dourado por tela.
export function alert(content, { iconName = 'alert' } = {}) {
  return html`<div class="alert" role="note">${icon(iconName, { size: 18, stroke: 2 })}<div class="grow">${content}</div></div>`;
}

// Faixa neutra de aviso (por exemplo, gestor vendo a lista de alguém).
export function banner(content, { iconName = 'users' } = {}) {
  return html`<div class="banner" role="note">${icon(iconName, { size: 16 })}<div class="grow">${content}</div></div>`;
}

// size: 'xl' (número grande da tela) | 'md'; muted: valor em cinza; divided: filete à esquerda.
export function kpi({ label, value, sub, size = 'md', muted = false, divided = false }) {
  const valueClass = ['kpi__value', size === 'xl' && 'kpi__value--xl', muted && 'kpi__value--muted'].filter(Boolean).join(' ');
  return html`<div class="kpi${divided ? ' kpi--divided' : ''}">
    ${label ? eyebrow(label) : ''}
    <p class="${valueClass}">${value}</p>
    ${sub ? html`<p class="kpi__sub">${sub}</p>` : ''}
  </div>`;
}

// Barra dupla: share (fração 0 a 1, vinda da API) cheio, o resto tracejado. variant: 'thin' | 'thick' | 'on-ink'.
export function dualBar({ share, label, variant } = {}) {
  const width = Math.max(0, Math.min(1, Number(share) || 0)) * 100;
  return html`<div class="dualbar${variant ? ` dualbar--${variant}` : ''}" role="img"${attrs({ 'aria-label': label })}>
    <span class="dualbar__live" style="width: ${width.toFixed(2)}%"></span>${width < 100 ? html`<span class="dualbar__rest"></span>` : ''}
  </div>`;
}

// Régua de idade de 0 a max dias; [from, to] é a janela escura; age é o ponto. Valores crus da API.
export function ageRuler({ age, max, from, to, stale = false, label } = {}) {
  const pos = (days) => `${(Math.max(0, Math.min(1, (Number(days) || 0) / (Number(max) || 1))) * 100).toFixed(2)}%`;
  const hasWindow = Number.isFinite(from) && Number.isFinite(to) && to > from;
  return html`<div class="age-ruler${stale ? ' age-ruler--stale' : ''}" role="img"${attrs({ 'aria-label': label })}>
    ${hasWindow ? html`<span class="age-ruler__window" style="left: ${pos(from)}; width: calc(${pos(to)} - ${pos(from)})"></span>` : ''}
    <span class="age-ruler__dot" style="left: ${pos(age)}"></span>
  </div>`;
}

/* Gabi */

export function gabiHead({ title = 'Insights da Gabi', subtitle = 'Calculados por regra, com a conta à mostra' } = {}) {
  return html`<div class="gabi-head">
    <span class="gabi-head__icon">${icon('sparkle', { size: 15 })}</span>
    <div><h2 class="gabi-head__title">${title}</h2><p class="gabi-head__sub">${subtitle}</p></div>
  </div>`;
}

// Cartão da Gabi a partir do cartão da API ({ label, title, body, link_label, highlight }).
// href (link) ou linkAttrs (por exemplo { 'data-acao': 'janela' }, vira botão) definem a ação; sem nenhum
// dos dois (href null, por exemplo) o cartão fica sem link, mesmo que a API mande link_label.
export function gabiCard(insight, { href, linkAttrs, highlight = insight.highlight } = {}) {
  let action = '';
  if (insight.link_label && href) action = linkArrow(insight.link_label, href);
  else if (insight.link_label && linkAttrs) {
    action = html`<button type="button" class="link-arrow"${attrs(linkAttrs)}>${insight.link_label}${icon('arrowRight', { size: 14, stroke: 2 })}</button>`;
  }
  return html`<article class="gabi-card${highlight ? ' gabi-card--highlight' : ''}">
    ${insight.label ? html`<p class="gabi-card__label">${insight.label}</p>` : ''}
    <h3 class="gabi-card__title">${insight.title}</h3>
    ${insight.body ? html`<p class="gabi-card__body">${insight.body}</p>` : ''}
    ${action ? html`<div class="gabi-card__foot">${action}</div>` : ''}
  </article>`;
}

/* Tabelas */

// Envolve uma <table class="table"> larga: ela rola dentro do bloco, não a página.
export function tableWrap(content, { label } = {}) {
  return html`<div class="table-wrap" role="region" tabindex="0"${attrs({ 'aria-label': label })}>${content}</div>`;
}

/* Estados: carregando, vazio, erro */

export function skeleton({ title = true, lines = 2, blocks = 4 } = {}) {
  return html`<div class="skeleton" aria-hidden="true">
    ${title ? html`<span class="skeleton__line skeleton__line--title"></span>` : ''}
    ${Array.from({ length: lines }, (_, i) => html`<span class="skeleton__line${i === lines - 1 ? ' skeleton__line--short' : ''}"></span>`)}
    ${Array.from({ length: blocks }, () => html`<span class="skeleton__block"></span>`)}
  </div><p class="sr-only" role="status">Carregando…</p>`;
}

export function empty(text, { title, action } = {}) {
  return html`<div class="state">
    ${title ? html`<p class="state__title">${title}</p>` : ''}
    <p>${text}</p>
    ${action ? html`<div class="state__actions">${action}</div>` : ''}
  </div>`;
}

export function errorState(message, { title = 'Não foi possível carregar.' } = {}) {
  return html`<div class="state state--error" role="alert">
    <p class="state__title">${title}</p>
    <p>${message}</p>
    <div class="state__actions">${button('Tentar de novo', { attrs: { 'data-retry': true } })}</div>
  </div>`;
}

function errorMessage(error) {
  return error?.name === 'ApiError' && error.message
    ? error.message
    : 'Algo deu errado ao montar esta parte da tela. Tente de novo em instantes.';
}

export function showLoading(root, options) {
  root.setAttribute('aria-busy', 'true');
  setHtml(root, skeleton(options));
}

// Mostra o erro em `root` com "Tentar de novo", que chama onRetry().
export function showError(root, error, onRetry, { title } = {}) {
  root.removeAttribute('aria-busy');
  setHtml(root, errorState(errorMessage(error), { title }));
  root.querySelector('[data-retry]')?.addEventListener('click', () => onRetry?.(), { once: true });
}

export function showEmpty(root, text, options) {
  root.removeAttribute('aria-busy');
  setHtml(root, empty(text, options));
}

// Ciclo completo: esqueleto -> task() -> draw(dados). Erro vira mensagem com "Tentar de novo";
// cancelamento (troca de tela, data ou vendedor) é ignorado em silêncio. Devolve os dados ou undefined.
export async function load(root, task, draw, { skeleton: skeletonOptions, errorTitle } = {}) {
  showLoading(root, skeletonOptions);
  try {
    const data = await task();
    root.removeAttribute('aria-busy');
    draw(data);
    return data;
  } catch (error) {
    if (isAbort(error)) return undefined;
    showError(root, error, () => load(root, task, draw, { skeleton: skeletonOptions, errorTitle }), { title: errorTitle });
    return undefined;
  }
}

/* Toast e cópia */

let toastRegion = null;
let activePanel = null;

// Com o painel aberto (aria-modal), o leitor de tela ignora o que está fora dele: o aviso também
// entra na região de status do próprio painel.
export function toast(message) {
  if (activePanel?.status) {
    activePanel.status.textContent = '';
    window.setTimeout(() => {
      if (activePanel?.status) activePanel.status.textContent = message;
    }, 50);
  }
  if (!toastRegion) {
    toastRegion = h('div', { class: 'toast-region', role: 'status', 'aria-live': 'polite' });
    document.body.append(toastRegion);
  }
  const item = h('div', { class: 'toast', text: message });
  toastRegion.append(item);
  window.setTimeout(() => item.remove(), 2800);
}

// Copia texto para a área de transferência e avisa com um toast. Devolve true se copiou.
export async function copyText(text, { success = 'Copiado.' } = {}) {
  let ok = false;
  try {
    await navigator.clipboard.writeText(text);
    ok = true;
  } catch {
    const area = h('textarea', { class: 'sr-only', readonly: true });
    area.value = text;
    document.body.append(area);
    area.select();
    try {
      ok = document.execCommand('copy');
    } catch {
      ok = false;
    }
    area.remove();
  }
  toast(ok ? success : 'Não deu para copiar. Selecione o texto e copie à mão.');
  return ok;
}

/* Painel lateral (dialog modal) */

// Abre o painel lateral à direita. onClose(motivo) recebe 'user' (Esc, X, clique fora), 'replaced'
// (outro painel abriu) ou 'route' (a moldura fechou ao trocar de tela, data ou usuário).
// returnFocus: elemento ou função que devolve o elemento que recebe o foco ao fechar (padrão: quem abriu).
// Enquanto ele está aberto, a moldura fica inerte: o foco não sai do painel.
// className: classe extra do painel, para a tela ajustar o próprio conteúdo (por exemplo 'clientes-painel').
export function openPanel({ eyebrow: label, title, subtitle, content, onClose, returnFocus, className } = {}) {
  activePanel?.close('replaced');
  const opener = returnFocus ?? document.activeElement;
  const background = document.getElementById('shell');
  const titleId = nextId('painel-titulo');
  const backdrop = h('div', { class: 'side-panel-backdrop' });
  const panel = h('section', { class: className ? `side-panel ${className}` : 'side-panel', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': titleId });
  setHtml(panel, html`<header class="side-panel__head">
      <div class="side-panel__titles" data-panel-titles></div>
      <button type="button" class="icon-btn" data-panel-close aria-label="Fechar painel">${icon('close', { size: 14, stroke: 1.8 })}</button>
    </header>
    <div class="side-panel__body" data-panel-body></div>
    <p class="sr-only" role="status" data-panel-status></p>`);
  const titles = panel.querySelector('[data-panel-titles]');
  const body = panel.querySelector('[data-panel-body]');

  // Troca rótulo, título e subtítulo; se o foco estava no título antigo, passa para o novo.
  const setHeader = (head) => {
    const hadFocus = titles.contains(document.activeElement);
    setHtml(titles, html`${head.eyebrow ? eyebrow(head.eyebrow) : ''}<h2 class="side-panel__title" id="${titleId}" tabindex="-1">${head.title}</h2>${
      head.subtitle ? html`<p class="side-panel__sub">${head.subtitle}</p>` : ''
    }`);
    if (hadFocus) document.getElementById(titleId)?.focus({ preventScroll: true });
  };

  // No documento, e não no painel, para que Esc e Tab funcionem mesmo com o foco solto no body.
  // As listas suspensas param o Esc antes dele chegar aqui.
  const onKey = (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      handle.close('user');
      return;
    }
    if (event.key !== 'Tab') return;
    const items = focusables(panel);
    if (items.length === 0) return;
    const first = items[0];
    const last = items[items.length - 1];
    const inside = panel.contains(document.activeElement);
    if (event.shiftKey && (document.activeElement === first || !inside)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !inside)) {
      event.preventDefault();
      first.focus();
    }
  };

  const handle = {
    el: panel,
    body,
    status: panel.querySelector('[data-panel-status]'),
    setHeader,
    setContent(next) {
      setHtml(body, next);
    },
    close(reason = 'user') {
      if (activePanel !== handle) return;
      activePanel = null;
      document.removeEventListener('keydown', onKey);
      if (background) background.inert = false;
      panel.remove();
      backdrop.remove();
      if (reason === 'user') {
        const target = typeof opener === 'function' ? opener() : opener;
        const fallback = document.getElementById('screen-title') || document.getElementById('conteudo');
        (target && target.isConnected ? target : fallback)?.focus({ preventScroll: true });
      }
      onClose?.(reason);
    },
  };

  setHeader({ eyebrow: label, title, subtitle });
  setHtml(body, content);
  document.addEventListener('keydown', onKey);
  panel.querySelector('[data-panel-close]').addEventListener('click', () => handle.close('user'));
  backdrop.addEventListener('click', () => handle.close('user'));
  document.body.append(backdrop, panel);
  if (background) background.inert = true;
  activePanel = handle;
  document.getElementById(titleId)?.focus({ preventScroll: true });
  return handle;
}

export function closePanel(reason = 'route') {
  activePanel?.close(reason);
}

/* Seletor e menu suspenso */

// Botão de seletor: "Rótulo  Valor  ⌄". Abra a lista com openPicker(botão, ...).
export function selectButton({ label, value, attrs: extra = {}, popup = 'listbox' } = {}) {
  return html`<button type="button" class="select-btn" aria-haspopup="${popup}" aria-expanded="false"${attrs(extra)}>
    ${label ? html`<span class="select-btn__label">${label}</span>` : ''}<span class="select-btn__value">${value}</span>${icon('chevronDown', { size: 14, stroke: 2 })}
  </button>`;
}

let activePicker = null;

// Lista suspensa presa a `anchor`. options: [{ value, label, hint, group, groupHint }]; value: o marcado.
// role 'listbox' (escolha, com marca) ou 'menu' (ações). onSelect(valor) roda depois de fechar.
export function openPicker(anchor, { label, title, options, value, role = 'listbox', onSelect, minWidth = 220 } = {}) {
  activePicker?.close(false);
  const itemRole = role === 'menu' ? 'menuitem' : 'option';
  const groups = [];
  options.forEach((option) => {
    const key = option.group ?? '';
    let group = groups.find((g) => g.key === key);
    if (!group) {
      group = { key, hint: option.groupHint, items: [] };
      groups.push(group);
    }
    group.items.push(option);
  });

  const optionHtml = (option) => {
    const selected = role === 'listbox' && option.value === value;
    return html`<button type="button" class="popover__option" role="${itemRole}" data-value="${option.value}" tabindex="-1"${attrs({
      'aria-selected': role === 'listbox' ? String(selected) : null,
    })}>${role === 'listbox' ? html`<span class="popover__option-check">${icon('check', { size: 16, stroke: 2.2 })}</span>` : ''}${
      option.iconName ? icon(option.iconName, { size: 16 }) : ''
    }<span>${option.label}</span>${option.hint ? html`<span class="popover__option-hint">${option.hint}</span>` : ''}</button>`;
  };

  const pop = h('div', { class: 'popover' });
  const listId = nextId('lista');
  setHtml(pop, html`${title ? html`<p class="popover__title eyebrow">${title}</p>` : ''}<div role="${role}" id="${listId}"${attrs({ 'aria-label': label || title })}>${groups.map((group) => {
    if (!group.key) return group.items.map(optionHtml);
    const groupId = nextId('grupo');
    return html`<div role="group" aria-labelledby="${groupId}"><p class="popover__group" id="${groupId}"><span>${group.key}</span>${
      group.hint ? html`<span class="popover__group-hint">${group.hint}</span>` : ''
    }</p>${group.items.map(optionHtml)}</div>`;
  })}</div>`);

  const items = () => qsa('.popover__option', pop);
  const place = () => {
    const box = anchor.getBoundingClientRect();
    pop.style.minWidth = `${Math.max(box.width, minWidth)}px`;
    const size = pop.getBoundingClientRect();
    let top = box.bottom + 6;
    if (top + size.height > window.innerHeight - 8 && box.top - 6 - size.height >= 8) top = box.top - 6 - size.height;
    top = Math.max(8, Math.min(top, window.innerHeight - 8 - size.height));
    const left = Math.max(8, Math.min(box.left, window.innerWidth - 8 - size.width));
    pop.style.top = `${top}px`;
    pop.style.left = `${left}px`;
  };

  const onOutside = (event) => {
    if (!pop.contains(event.target) && !anchor.contains(event.target)) handle.close(false);
  };
  const onScroll = (event) => {
    if (!pop.contains(event.target)) place();
  };
  const onResize = () => handle.close(false);

  const handle = {
    el: pop,
    close(restoreFocus = true) {
      if (activePicker !== handle) return;
      activePicker = null;
      document.removeEventListener('pointerdown', onOutside, true);
      window.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', onResize);
      anchor.setAttribute('aria-expanded', 'false');
      pop.remove();
      if (restoreFocus && anchor.isConnected) anchor.focus({ preventScroll: true });
    },
  };

  on(pop, 'click', '.popover__option', (event, option) => {
    handle.close(true);
    onSelect?.(option.dataset.value);
  });

  pop.addEventListener('keydown', (event) => {
    const list = items();
    const index = list.indexOf(document.activeElement);
    const moves = { ArrowDown: index + 1, ArrowUp: index - 1, Home: 0, End: list.length - 1 };
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      handle.close(true);
    } else if (event.key === 'Tab') {
      handle.close(true);
    } else if (event.key in moves && list.length) {
      event.preventDefault();
      list[(moves[event.key] + list.length) % list.length].focus();
    }
  });

  anchor.setAttribute('aria-expanded', 'true');
  anchor.setAttribute('aria-controls', listId);
  document.body.append(pop);
  place();
  document.addEventListener('pointerdown', onOutside, true);
  window.addEventListener('scroll', onScroll, true);
  window.addEventListener('resize', onResize);
  activePicker = handle;
  const start = items().find((item) => item.getAttribute('aria-selected') === 'true') || items()[0];
  start?.focus({ preventScroll: true });
  start?.scrollIntoView({ block: 'nearest' });
  return handle;
}

export function closePicker() {
  activePicker?.close(false);
}

/* Peças do gestor */

// Seletor do vendedor em foco (só para gestor). A moldura abre a lista do time e troca ?vendedor= na rota.
export function sellerSelect(ctx) {
  if (ctx.user.role !== 'manager') return '';
  return selectButton({ label: 'Vendedor', value: ctx.subject, attrs: { 'data-seller-select': true } });
}

// Faixa de aviso quando o gestor vê a tela de um vendedor. what: "a lista", "o pipeline"...
export function viewingBanner(ctx, { what = 'a lista' } = {}) {
  if (ctx.user.role !== 'manager') return '';
  return banner(html`Você está vendo ${what} de <strong>${ctx.subject}</strong>, do seu time. ${linkArrow('Voltar para Meu time', ctx.href('time'))}`);
}

// Faixa do gestor logo abaixo do cabeçalho: o aviso e o seletor do vendedor, iguais em todas as telas
// que mostram um vendedor (Foco, Pipeline, Máquina do tempo). Vazio para vendedor.
export function viewingBar(ctx, options) {
  if (ctx.user.role !== 'manager') return '';
  return html`<div class="viewing-bar" data-viewing-bar>${viewingBanner(ctx, options)}${sellerSelect(ctx)}</div>`;
}
