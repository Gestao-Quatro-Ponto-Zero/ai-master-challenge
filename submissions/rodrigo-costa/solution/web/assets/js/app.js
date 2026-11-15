/*
 * Vendas · Lead Scorer: inicialização, roteador por hash e moldura.
 *
 * CONTRATO DAS TELAS (cada arquivo em assets/js/views/<nome>.js)
 *
 *   export default {
 *     id: 'foco',                      // igual ao nome do arquivo
 *     title: 'Foco da semana',         // vai para o <title> da aba
 *     roles: ['seller', 'manager'],    // quem pode ver; papel fora da lista volta para o início
 *     area: 'vendas',                  // 'vendas' ou 'config' (define o menu lateral); a tela de acesso usa 'login'
 *     render(root, ctx) { ...; return () => limpeza() },
 *   };
 *
 * render desenha dentro de `root` (o painel branco) e pode devolver uma função de limpeza (ou uma Promise
 * dela, se for async). A limpeza roda antes de qualquer novo render e ao sair da tela. Na entrada (e na troca
 * de data ou de usuário) `root` é um elemento novo, então ouvintes postos nele somem sozinhos. Com reason
 * 'params' o mesmo `root` é reaproveitado: ouvintes postos direto nele precisam sair na limpeza (ouvintes em
 * filhos que a tela redesenha somem com eles). Ouvintes em window/document sempre precisam de limpeza.
 *
 * ctx:
 *   user       { role: 'seller' | 'manager', roleLabel: 'Vendedor' | 'Gestor', name, first_name, initials,
 *                region, region_label, ... } mais os dados da pessoa em /api/meta (vendedor: manager;
 *                gestor: team, a lista de nomes do time)
 *   date       data simulada em ISO ("2017-12-04")
 *   dateInfo   o item de /api/meta.dates dessa data (label, label_short, label_long, quarter_phase...)
 *   meta       a resposta inteira de /api/meta
 *   params     a query da rota como objeto ({ vendedor: 'Boris Faz' })
 *   subject    nome do vendedor em foco: o próprio vendedor; para gestor, ?vendedor= (se for do time) ou o
 *              primeiro do time. subjectInfo é o item dele em meta.sellers.
 *   reason     por que esta chamada: 'enter' (chegou na tela), 'params' (só a query mudou; o root NÃO é
 *              esvaziado, a tela pode atualizar só o que mudou), 'date' ou 'user'
 *   api.get(path, params, { channel })  Promise com o JSON. path 'seller' vira /api/seller. Respostas ficam em
 *              cache por URL; a chamada anterior do mesmo canal (padrão: o path) é cancelada; tudo o que
 *              está pendente é cancelado ao sair da tela. Erro: ApiError com a mensagem da API.
 *   navigate(route, params, { replace })  troca a rota ('clientes', { cliente: 'Mathtouch' }). replace não
 *              empilha histórico.
 *   href(route, params)  monta o "#/rota?query" para links <a>.
 *   setDate(iso)  troca a data simulada (re-renderiza a tela atual).
 *   setUser({ role, name } | null)  entra como alguém ou sai (usado pela tela de acesso).
 *   store      decisões locais desta pessoa: get(chave, padrão), set(chave, valor), remove(chave), keys(prefixo).
 *              Fica em localStorage ("leadscorer:...") e só neste navegador; a tela deve dizer isso.
 *   ui, fmt, dom, icon  os módulos core/ui.js, core/fmt.js, core/dom.js e o construtor de ícones.
 *
 * Mudança de data ou de usuário re-renderiza a tela atual. Mudança só de parâmetro da rota chama render de
 * novo (reason 'params'). O painel lateral (ui.openPanel) fica aberto quando só a query muda e fecha nos
 * outros casos.
 *
 * ROTAS (hash): #/entrar, #/foco, #/pipeline, #/clientes (?cliente=Nome&aba=dados|em-aberto|fechadas),
 * #/time (só gestor), #/maquina-do-tempo, #/como-funciona, #/como-chegamos, #/qualidade-dos-dados,
 * #/fontes-de-dados. Gestor usa ?vendedor=Nome em foco, pipeline e maquina-do-tempo.
 */
import { ApiError, buildUrl, createScope, request } from './core/api.js';
import * as dom from './core/dom.js';
import * as fmt from './core/fmt.js';
import { icon } from './core/icons.js';
import * as state from './core/state.js';
import * as ui from './core/ui.js';

const { html, setHtml, on } = dom;

const ROUTES = {
  entrar: { module: 'login', area: 'login' },
  foco: { module: 'foco', area: 'vendas' },
  pipeline: { module: 'pipeline', area: 'vendas' },
  clientes: { module: 'clientes', area: 'vendas' },
  time: { module: 'time', area: 'vendas' },
  'maquina-do-tempo': { module: 'maquina', area: 'vendas' },
  'como-funciona': { module: 'score', area: 'vendas' },
  'como-chegamos': { module: 'chegamos', area: 'vendas' },
  'qualidade-dos-dados': { module: 'qualidade', area: 'vendas' },
  'fontes-de-dados': { module: 'fontes', area: 'config' },
};

const SALES_MENU = [
  {
    items: [
      { route: 'foco', label: 'Foco da semana', icon: 'target', roles: ['seller'] },
      { route: 'time', label: 'Meu time', icon: 'target', roles: ['manager'] },
      { route: 'pipeline', label: 'Pipeline', icon: 'kanban' },
      { route: 'clientes', label: 'Clientes', icon: 'building' },
    ],
  },
  { title: 'Prova', items: [{ route: 'maquina-do-tempo', label: 'Máquina do tempo', icon: 'history' }] },
  {
    title: 'Transparência',
    items: [
      { route: 'como-funciona', label: 'Como o score funciona', icon: 'book' },
      { route: 'como-chegamos', label: 'Como chegamos aqui', icon: 'route' },
      { route: 'qualidade-dos-dados', label: 'Qualidade dos dados', icon: 'database' },
    ],
  },
];

const CONFIG_MENU = [{ items: [{ route: 'fontes-de-dados', label: 'Fontes de dados', icon: 'plug' }] }];

const PHASES = { abre: 'abre o trimestre', meio: 'meio do trimestre', fecha: 'fecha o trimestre' };
const INERT_AREAS = ['inbox', 'grid', 'folder'];

const app = {
  meta: null,
  path: null,
  token: 0,
  cleanup: null,
  scope: null,
  shellKey: '',
  ctx: null,
  booted: false,
  views: new Map(),
};

const els = {
  boot: document.getElementById('boot'),
  shell: document.getElementById('shell'),
  login: document.getElementById('login-root'),
};

/* Rotas */

function parseHash() {
  const value = window.location.hash.replace(/^#\/?/, '');
  const [path = '', query = ''] = value.split('?');
  let clean = path;
  try {
    clean = decodeURIComponent(path);
  } catch {
    clean = path;
  }
  return { path: clean.replace(/\/+$/, ''), params: Object.fromEntries(new URLSearchParams(query)) };
}

function href(route, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
  });
  const text = query.toString();
  return `#/${String(route).replace(/^[#/]+/, '')}${text ? `?${text}` : ''}`;
}

function navigate(route, params = {}, { replace = false } = {}) {
  const target = href(route, params);
  if (replace) {
    window.history.replaceState(null, '', target);
    handleRoute();
  } else if (window.location.hash === target) {
    handleRoute();
  } else {
    window.location.hash = target;
  }
}

function homeRoute(user) {
  return user?.role === 'manager' ? 'time' : 'foco';
}

/* Usuário e data */

function currentUser() {
  const saved = state.getUser();
  if (!saved || !app.meta) return null;
  const sameName = (item) => item.name.toLowerCase() === saved.name.toLowerCase();
  if (saved.role === 'seller') {
    const seller = app.meta.sellers.find(sameName);
    return seller ? { ...seller, role: 'seller', roleLabel: 'Vendedor' } : null;
  }
  const manager = app.meta.managers.find(sameName);
  if (!manager) return null;
  return {
    ...manager,
    role: 'manager',
    roleLabel: 'Gestor',
    first_name: fmt.firstName(manager.name),
    initials: fmt.initials(manager.name),
  };
}

function currentDate() {
  const saved = state.getDate();
  return app.meta.dates.some((d) => d.iso === saved) ? saved : app.meta.default_date;
}

function dateInfo(iso) {
  return app.meta.dates.find((d) => d.iso === iso) || null;
}

function resolveSubject(user, params) {
  if (!user) return null;
  if (user.role === 'seller') return user.name;
  const wanted = String(params.vendedor || '').toLowerCase();
  return user.team.find((name) => name.toLowerCase() === wanted) || user.team[0];
}

/* Moldura */

function navGroupsHtml(groups, user, active) {
  return groups.map((group, index) => {
    const items = group.items.filter((item) => !item.roles || item.roles.includes(user.role));
    const labelId = `menu-grupo-${index}`;
    const list = html`<ul class="sidemenu__list"${group.title ? ui.attrs({ 'aria-labelledby': labelId }) : ''}>${items.map(
      (item) => html`<li><a class="navitem" href="${href(item.route)}"${ui.attrs({ 'aria-current': item.route === active ? 'page' : null })}><span class="navitem__pill">${icon(item.icon, { size: 17, stroke: 1.7 })}<span>${item.label}</span></span></a></li>`,
    )}</ul>`;
    if (!group.title) return list;
    return html`<div class="sidemenu__group"><p class="eyebrow sidemenu__group-label" id="${labelId}">${group.title}</p>${list}</div>`;
  });
}

function railHtml(area, user) {
  const config = area === 'config';
  return html`<div class="rail__top">
      <span class="mark" title="Vendas">${icon('trend', { size: 18, stroke: 2 })}</span>
      <ul class="rail__areas">
        <li><a class="rail__item rail__item--area${config ? '' : ' is-active'}" href="${href(homeRoute(user))}" title="Vendas"${ui.attrs({ 'aria-current': config ? null : 'true' })}><span class="rail__btn">${icon('target', { size: 19 })}</span><span class="sr-only">Vendas</span></a></li>
        ${INERT_AREAS.map(
          (name) => html`<li><span class="rail__item is-inert" title="Fora deste conceito"><span class="rail__btn">${icon(name, { size: 19, stroke: 1.6 })}</span><span class="sr-only">Outra área, fora deste conceito</span></span></li>`,
        )}
      </ul>
    </div>
    <div class="rail__bottom">
      <a class="rail__item${config ? ' is-active' : ''}" href="${href('fontes-de-dados')}" title="Configurações"${ui.attrs({ 'aria-current': config ? 'true' : null })}><span class="rail__btn">${icon('settings', { size: 19, stroke: 1.8 })}</span><span class="sr-only">Configurações</span></a>
      <a class="rail__item" href="${href('como-funciona')}" title="Ajuda: como o score funciona"><span class="rail__btn">${icon('help', { size: 19, stroke: 1.8 })}</span><span class="sr-only">Ajuda: como o score funciona</span></a>
    </div>`;
}

function sidemenuHtml(area, user, active, iso) {
  const config = area === 'config';
  const nav = config
    ? html`${navGroupsHtml(CONFIG_MENU, user, active)}<ul class="sidemenu__list"><li><a class="navitem navitem--back" href="${href(homeRoute(user))}"><span class="navitem__pill">${icon('arrowLeft', { size: 16, stroke: 1.8 })}<span>Voltar para Vendas</span></span></a></li></ul>`
    : navGroupsHtml(SALES_MENU, user, active);
  return html`<div class="sidemenu__top">
      <div class="sidemenu__title"><span>${config ? 'Configurações' : 'Vendas'}</span>${ui.conceptBadge()}</div>
      <nav class="sidemenu__links" aria-label="${config ? 'Configurações' : 'Menu de Vendas'}">${nav}</nav>
    </div>
    <div class="sidemenu__foot">
      <div class="datepick">
        <button type="button" class="datepick__btn" data-date-picker aria-haspopup="listbox" aria-expanded="false">
          ${icon('calendar', { size: 15, stroke: 1.7 })}<span class="grow"><span class="sr-only">Data simulada: </span><span data-date-label>${dateButtonLabel(iso)}</span></span>${icon('chevronDown', { size: 14 })}
        </button>
        <p class="datepick__note">Data simulada. A base vai até ${fmt.dateLabel(app.meta.dataset.last_close)}.</p>
      </div>
      <div class="userbox">
        <button type="button" class="userbox__btn" data-user-menu aria-haspopup="menu" aria-expanded="false">
          ${ui.avatar(user.initials)}
          <span class="grow userbox__text"><span class="userbox__name">${user.name}</span><span class="userbox__role">${user.roleLabel} · ${user.region_label}</span></span>
          ${icon('chevronUpDown', { size: 16 })}
        </button>
      </div>
    </div>`;
}

function topbarHtml(area, iso) {
  return html`<button type="button" class="topbar__menu" data-menu-toggle aria-expanded="false" aria-controls="nav-drawer">${icon('menu', { size: 18 })}<span class="sr-only">Abrir menu</span></button>
    <span class="topbar__brand"><span class="mark">${icon('trend', { size: 18, stroke: 2 })}</span><span class="topbar__brand-text">${area === 'config' ? 'Configurações' : 'Vendas'}</span></span>
    ${ui.conceptBadge()}
    <span class="topbar__date" data-topbar-date>${dateButtonLabel(iso)}</span>`;
}

function dateButtonLabel(iso) {
  return fmt.capitalize(dateInfo(iso)?.label_short || iso);
}

function renderShell(area, user, path) {
  const active = user.role === 'manager' && path === 'foco' ? 'time' : path;
  const key = `${area}|${user.role}|${user.name}`;
  const iso = currentDate();
  if (key !== app.shellKey) {
    app.shellKey = key;
    setHtml(els.shell.querySelector('[data-topbar]'), topbarHtml(area, iso));
    setHtml(els.shell.querySelector('[data-rail]'), railHtml(area, user));
    setHtml(els.shell.querySelector('[data-sidemenu]'), sidemenuHtml(area, user, active, iso));
  } else {
    dom.qsa('.navitem', els.shell).forEach((link) => {
      if (link.classList.contains('navitem--back')) return;
      const route = link.getAttribute('href').replace(/^#\//, '');
      if (route === active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    updateDateLabels(iso);
  }
  els.login.hidden = true;
  els.shell.hidden = false;
}

function updateDateLabels(iso) {
  const label = dateButtonLabel(iso);
  dom.qsa('[data-date-label], [data-topbar-date]', els.shell).forEach((el) => {
    el.textContent = label;
  });
}

// Abaixo de 900 px o menu é uma gaveta modal: enquanto aberta, o conteúdo atrás do fundo escuro fica inerte.
const drawerQuery = window.matchMedia('(max-width: 899px)');

function setDrawer(open, { focus = false } = {}) {
  const drawer = document.getElementById('nav-drawer');
  const toggle = els.shell.querySelector('[data-menu-toggle]');
  const backdrop = els.shell.querySelector('[data-drawer-backdrop]');
  drawer.classList.toggle('is-open', open);
  backdrop.hidden = !open;
  document.getElementById('conteudo').inert = open;
  toggle?.setAttribute('aria-expanded', String(open));
  toggle?.querySelector('.sr-only')?.replaceChildren(open ? 'Fechar menu' : 'Abrir menu');
  if (open && focus) dom.focusables(drawer)[0]?.focus();
  if (!open && focus) toggle?.focus();
}

function openDatePicker(button) {
  const iso = currentDate();
  ui.openPicker(button, {
    title: 'Data simulada',
    label: 'Escolha a segunda-feira simulada',
    value: iso,
    minWidth: 280,
    options: app.meta.dates.map((d) => ({
      value: d.iso,
      label: fmt.capitalize(d.label_short),
      hint: d.iso === app.meta.default_date ? 'data inicial' : '',
      group: `${fmt.capitalize(d.month_name)} de ${d.iso.slice(0, 4)}`,
      groupHint: PHASES[d.quarter_phase] || '',
    })),
    onSelect: (value) => state.setDate(value),
  });
}

function openUserMenu(button) {
  ui.openPicker(button, {
    role: 'menu',
    label: 'Opções da pessoa simulada',
    options: [{ value: 'trocar', label: 'Trocar de pessoa', iconName: 'logout' }],
    onSelect: () => state.setUser(null),
  });
}

function openSellerPicker(button) {
  const ctx = app.ctx;
  if (!ctx || ctx.user.role !== 'manager') return;
  ui.openPicker(button, {
    label: 'Vendedor do time',
    title: `Time de ${ctx.user.first_name}`,
    value: ctx.subject,
    options: ctx.user.team.map((name) => ({ value: name, label: name })),
    // O deal aberto por link (?deal=) e a aba (?aba=) são do vendedor anterior: não valem para o próximo.
    onSelect: (name) => navigate(app.path, { ...ctx.params, vendedor: name, deal: undefined, aba: undefined }, { replace: true }),
  });
}

function bindShell() {
  on(els.shell, 'click', '[data-date-picker]', (event, button) => openDatePicker(button));
  on(els.shell, 'click', '[data-user-menu]', (event, button) => openUserMenu(button));
  on(els.shell, 'click', '[data-seller-select]', (event, button) => openSellerPicker(button));
  on(els.shell, 'click', '[data-menu-toggle]', () => {
    setDrawer(!document.getElementById('nav-drawer').classList.contains('is-open'), { focus: true });
  });
  on(els.shell, 'click', '[data-drawer-backdrop]', () => setDrawer(false));
  on(els.shell, 'click', '#nav-drawer a[href]', () => setDrawer(false));
  drawerQuery.addEventListener('change', (event) => {
    if (!event.matches) setDrawer(false);
  });
  els.shell.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && document.getElementById('nav-drawer').classList.contains('is-open')) {
      setDrawer(false, { focus: true });
    }
  });
  // O link "pular para o conteúdo" não pode mexer no hash, que é do roteador.
  on(document.body, 'click', '[data-skip]', (event) => {
    event.preventDefault();
    (els.shell.hidden ? els.login : document.getElementById('conteudo')).focus();
  });
}

/* Telas */

async function loadView(name, retry = false) {
  if (!retry && app.views.has(name)) return app.views.get(name);
  const module = await import(`./views/${name}.js${retry ? `?tentativa=${Date.now()}` : ''}`);
  app.views.set(name, module.default);
  return module.default;
}

function teardown(reason) {
  ui.closePicker();
  if (reason !== 'params') ui.closePanel('route');
  if (app.cleanup) {
    const cleanup = app.cleanup;
    app.cleanup = null;
    cleanup();
  }
  app.scope?.dispose();
  app.scope = null;
  app.ctx = null;
}

function pageMessage(root, { title, text, action }) {
  document.title = `${title} · Vendas`;
  setHtml(root, html`<div class="page-message">
    ${ui.screenHeader({ eyebrow: 'Vendas', title, subtitle: text })}
    ${action ? html`<div>${action}</div>` : ''}
  </div>`);
}

// Devolve o root da tela. fresh troca o elemento por uma cópia vazia: ouvintes da tela anterior somem com ele.
function screenRoot(isLogin, { fresh }) {
  const current = isLogin ? els.login : document.getElementById('panel');
  if (!fresh) return current;
  const next = current.cloneNode(false);
  next.removeAttribute('aria-busy');
  current.replaceWith(next);
  if (isLogin) els.login = next;
  return next;
}

function renderNotFound(user) {
  app.token += 1;
  teardown('enter');
  app.path = null;
  renderShell('vendas', user, '');
  pageMessage(screenRoot(false, { fresh: true }), {
    title: 'Página não encontrada',
    text: 'Este endereço não existe neste conceito. O menu ao lado leva a todas as telas.',
    action: ui.linkArrow('Ir para o início', href(homeRoute(user))),
  });
}

function renderLoadFailure(root, retry) {
  pageMessage(root, {
    title: 'Não foi possível abrir esta tela.',
    text: 'O arquivo da tela não carregou. Pode ser a conexão; o resto do app continua funcionando.',
    action: ui.button('Tentar de novo', { attrs: { 'data-retry-view': true } }),
  });
  root.querySelector('[data-retry-view]')?.addEventListener('click', retry, { once: true });
}

function buildCtx(user, params, reason, scope) {
  const date = currentDate();
  const subject = resolveSubject(user, params);
  return {
    user,
    date,
    dateInfo: dateInfo(date),
    meta: app.meta,
    params,
    subject,
    subjectInfo: subject ? app.meta.sellers.find((s) => s.name === subject) || null : null,
    reason,
    api: { get: (path, query, options) => scope.get(path, { ...query }, options) },
    signal: scope.signal,
    navigate,
    href,
    setDate: (iso) => state.setDate(iso),
    setUser: (next) => state.setUser(next),
    store: state.createStore(user),
    ui,
    fmt,
    dom,
    icon,
  };
}

async function mount(def, path, params, reason, { retry = false } = {}) {
  const token = (app.token += 1);
  // O seletor de vendedor redesenha com a tela; o foco volta para o novo.
  const keepSellerFocus = reason === 'params' && Boolean(document.activeElement?.matches('[data-seller-select]'));
  teardown(reason);
  const user = currentUser();
  const isLogin = def.area === 'login';
  if (isLogin) {
    els.shell.hidden = true;
    els.login.hidden = false;
    app.shellKey = '';
  } else {
    renderShell(def.area, user, path);
  }
  app.path = path;

  let view;
  try {
    view = await loadView(def.module, retry);
  } catch {
    if (token === app.token) {
      renderLoadFailure(screenRoot(isLogin, { fresh: true }), () => mount(def, path, params, 'enter', { retry: true }));
    }
    return;
  }
  if (token !== app.token) return;
  if (!isLogin && Array.isArray(view.roles) && !view.roles.includes(user.role)) {
    navigate(homeRoute(user), {}, { replace: true });
    return;
  }

  document.title = `${view.title} · Vendas`;
  const root = screenRoot(isLogin, { fresh: reason !== 'params' });
  const scope = createScope();
  app.scope = scope;
  app.ctx = buildCtx(user, params, reason, scope);

  const keepCleanup = (cleanup) => {
    if (typeof cleanup !== 'function') return;
    if (token === app.token) app.cleanup = cleanup;
    else cleanup();
  };
  const onRenderError = (error) => {
    if (token === app.token) ui.showError(root, error, () => mount(def, path, params, 'enter'));
  };
  try {
    const result = view.render(root, app.ctx);
    if (result && typeof result.then === 'function') result.then(keepCleanup, onRenderError);
    else keepCleanup(result);
  } catch (error) {
    onRenderError(error);
  }

  if (keepSellerFocus && !document.activeElement?.matches('[data-seller-select]')) {
    root.querySelector('[data-seller-select]')?.focus({ preventScroll: true });
  }
  if (reason === 'enter' && app.booted) {
    window.scrollTo(0, 0);
    const focusTarget = document.getElementById('screen-title') || (isLogin ? null : document.getElementById('conteudo'));
    focusTarget?.focus({ preventScroll: true });
  }
  app.booted = true;
}

function handleRoute(reason) {
  if (applyEntryLink()) {
    if (app.booted) updateDateLabels(currentDate());
    reason = 'enter';
  }
  const { path, params } = parseHash();
  const user = currentUser();
  if (!path) {
    navigate(user ? homeRoute(user) : 'entrar', {}, { replace: true });
    return;
  }
  const def = ROUTES[path];
  if (!def) {
    if (user) renderNotFound(user);
    else navigate('entrar', {}, { replace: true });
    return;
  }
  if (def.area !== 'login' && !user) {
    navigate('entrar', {}, { replace: true });
    return;
  }
  if (path === 'time' && user.role !== 'manager') {
    navigate('foco', {}, { replace: true });
    return;
  }
  return mount(def, path, params, reason || (path === app.path ? 'params' : 'enter'));
}

/* Inicialização */

function showBootError(error) {
  setHtml(els.boot, html`<div class="boot__box">
    ${ui.errorState(error?.message || 'Não foi possível falar com o servidor.', { title: 'O app não conseguiu abrir.' })}
  </div>`);
  els.boot.querySelector('[data-retry]')?.addEventListener('click', boot, { once: true });
}

// Formato mínimo de /api/meta para a moldura abrir; sem ele, erro de boot em vez de tela em branco.
function validMeta(meta) {
  return Boolean(
    meta &&
      Array.isArray(meta.dates) && meta.dates.length > 0 &&
      Array.isArray(meta.sellers) &&
      Array.isArray(meta.managers) &&
      meta.dataset && typeof meta.dataset === 'object',
  );
}

let shellBound = false;

// Link direto de entrada, para quem avalia ir a uma tela sem passar pela escolha de pessoa:
// "#/foco?como=Daniell%20Hammack&data=2017-12-04" (perfil=vendedor|gestor é opcional).
// Só aceita nome e data que o servidor conhece, e os três parâmetros saem do endereço depois de lidos.
let applyingLink = false;

function applyEntryLink() {
  const { path, params } = parseHash();
  const { como, perfil, data, ...rest } = params;
  if (como === undefined && perfil === undefined && data === undefined) return false;
  applyingLink = true;
  try {
    if (como) {
      const same = (item) => item.name.toLowerCase() === como.trim().toLowerCase();
      const seller = perfil === 'gestor' ? null : app.meta.sellers.find(same);
      const manager = perfil === 'vendedor' ? null : app.meta.managers.find(same);
      if (seller) state.setUser({ role: 'seller', name: seller.name });
      else if (manager) state.setUser({ role: 'manager', name: manager.name });
    }
    if (data && app.meta.dates.some((d) => d.iso === data)) state.setDate(data);
  } finally {
    applyingLink = false;
  }
  window.history.replaceState(null, '', path ? href(path, rest) : window.location.pathname + window.location.search);
  return true;
}

async function boot() {
  setHtml(els.boot, html`<div class="boot__box">${ui.skeleton({ lines: 2, blocks: 3 })}</div>`);
  els.boot.hidden = false;
  try {
    const meta = await request(buildUrl('meta'));
    if (!validMeta(meta)) throw new ApiError('O servidor respondeu num formato que este app não reconhece.', 0);
    app.meta = meta;
  } catch (error) {
    showBootError(error);
    return;
  }
  els.boot.hidden = true;
  try {
    await handleFirstRoute();
  } catch (error) {
    els.shell.hidden = true;
    els.login.hidden = true;
    els.boot.hidden = false;
    showBootError(error);
  }
}

// A primeira tela é montada aqui (e não só pelo hashchange) para que uma falha dela vire erro de boot.
async function handleFirstRoute() {
  if (shellBound) {
    await handleRoute();
    return;
  }
  shellBound = true;
  bindShell();
  window.addEventListener('hashchange', () => handleRoute());
  state.onChange(({ what }) => {
    if (applyingLink) return;
    if (what === 'user') {
      const user = currentUser();
      navigate(user ? homeRoute(user) : 'entrar', {}, { replace: !user });
    } else if (what === 'date') {
      updateDateLabels(currentDate());
      if (app.path && ROUTES[app.path]) handleRoute('date');
    }
  });
  await handleRoute();
}

boot();
