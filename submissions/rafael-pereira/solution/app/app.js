/* Lead Scorer — interface. JavaScript puro, script clássico (funciona em file:// e no GitHub Pages).
   Tudo o que aparece com número vem de window.LEAD_DATA (contrato em data-contract.md).
   A interface filtra, mas nunca reordena os deals: a ordem é a do data.js.

   Três perfis, escolhidos na tela de entrada e guardados no hash (#perfil=vendedor&nome=...):
   - vendedor: "Minha semana", só os deals do próprio vendedor, ações salvas no navegador, simulador;
   - manager:  "Meu time", mapa por vendedor, carteira em modo leitura e pauta do 1:1;
   - revops:   a carteira completa com filtros (também é o destino dos links antigos #vendedor=...).
   ATENÇÃO: a separação é de experiência, não de segurança. O data.js contém todos os deals. */
(function () {
  'use strict';

  var D = window.LEAD_DATA;
  function $(id) { return document.getElementById(id); }

  if (!D || !D.meta || !D.people || !D.snapshots || !D.snapshots.length) {
    $('no-data').hidden = false;
    return;
  }
  $('app').hidden = false;

  /* ------------------------------------------------------------------ constantes de interface */
  var CATS = ['Foque', 'Reative', 'Limpe', 'Qualifique'];   // identificadores das listas (vêm do contrato)
  var MGR_LABEL = { Foque: 'Vivos', Reative: 'Esfriando', Limpe: 'Zumbis', Qualifique: 'Qualifique' };
  var PAGE_SIZE = 30;                                        // quantos cards por vez (parâmetro de layout)
  var PAUTA_N = 3;                                           // deals por bloco da pauta do 1:1 (parâmetro de formato)
  var COUNT_MS = 500;                                        // duração da contagem animada do valor da semana
  var TEST = 'teste';
  var TODAY = 'hoje';
  var K_ACOES = 'leadscorer:acoes:v1';
  var K_PERFIL = 'leadscorer:perfil:v1';
  var K_TEMA = 'leadscorer:tema';
  var ACTS = [
    { key: 'contatei', label: 'Contatei', done: 'contatado' },
    { key: 'agendei', label: 'Agendei', done: 'agendado' },
    { key: 'encerrar', label: 'Encerrar no CRM', done: 'para encerrar no CRM' }
  ];

  /* ------------------------------------------------------------------ armazenamento local (sempre com try/catch) */
  function lsGet(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { window.localStorage.setItem(k, v); return true; } catch (e) { return false; } }

  /* ------------------------------------------------------------------ formatação PT-BR */
  var nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  // Arredonda metade para cima, descartando ruído de ponto flutuante (igual ao fmt.py do motor).
  function rhu(x) { return Math.round(Number(Number(x).toFixed(10))); }
  function num(n) { return nf0.format(rhu(n)); }
  function usd(n) { return 'US$ ' + num(n); }
  function pct0(f) { return num(f * 100) + '%'; }
  function pct1(f) { return nf1.format(Number((f * 100).toFixed(10))) + '%'; }
  function dec2(f) { return nf2.format(Number(Number(f).toFixed(10))); }
  function dateBR(iso) {
    if (!iso) { return ''; }
    var p = String(iso).split('-');
    return p[2] + '/' + p[1] + '/' + p[0];
  }
  var ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return ESC[c]; }); }
  function plural(n, one, many) { return n === 1 ? one : many; }
  function days(n) { return num(n) + ' ' + plural(n, 'dia', 'dias'); }
  function joinPt(parts) {
    if (parts.length < 2) { return parts.join(''); }
    return parts.slice(0, -1).join(', ') + ' e ' + parts[parts.length - 1];
  }
  function byName(a, b) { return a.localeCompare(b, 'pt-BR', { sensitivity: 'base' }); }
  function icon(name, cls) {
    return '<svg class="ico ' + (cls || '') + '" aria-hidden="true" focusable="false"><use href="#i-' + name + '"/></svg>';
  }
  function announce(msg) {
    var el = $('live');
    el.textContent = '';
    window.setTimeout(function () { el.textContent = msg; }, 30);
  }

  /* ------------------------------------------------------------------ índices */
  var HORIZON = D.meta.horizon_days;
  var agentsByName = {};
  var managersByName = {};
  D.people.agents.forEach(function (a) { agentsByName[a.name] = a; });
  D.people.managers.forEach(function (m) { managersByName[m.name] = m; });
  var snapByDate = {};
  D.snapshots.forEach(function (s) { snapByDate[s.date] = s; });
  var todaySnap = D.snapshots.filter(function (s) { return s.mode === TODAY; })[0] || D.snapshots[0];

  // contagem de deals por vendedor em cada snapshot (para "sem deals abertos" nos seletores)
  var perAgentCache = {};
  function perAgent(snap) {
    if (!perAgentCache[snap.date]) {
      var m = {};
      snap.deals.forEach(function (d) { m[d.agent] = (m[d.agent] || 0) + 1; });
      perAgentCache[snap.date] = m;
    }
    return perAgentCache[snap.date];
  }

  /* ------------------------------------------------------------------ tema (claro, escuro, ou o do sistema) */
  var root = document.documentElement;
  var themeBtn = $('theme-btn');
  function effectiveTheme() {
    var t = root.getAttribute('data-theme');
    if (t === 'dark' || t === 'light') { return t; }
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function paintThemeBtn() {
    var dark = effectiveTheme() === 'dark';
    themeBtn.setAttribute('aria-label', dark ? 'Mudar para o tema claro' : 'Mudar para o tema escuro');
    themeBtn.setAttribute('data-theme-now', dark ? 'dark' : 'light');
    $('theme-use').setAttribute('href', dark ? '#i-sun' : '#i-moon');
  }
  themeBtn.addEventListener('click', function () {
    var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    lsSet(K_TEMA, next);
    paintThemeBtn();
    announce(next === 'dark' ? 'Tema escuro.' : 'Tema claro.');
  });
  if (window.matchMedia) {
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    var onScheme = function () { paintThemeBtn(); };
    if (mq.addEventListener) { mq.addEventListener('change', onScheme); } else if (mq.addListener) { mq.addListener(onScheme); }
  }
  paintThemeBtn();

  /* ------------------------------------------------------------------ marcações do vendedor (localStorage) */
  var store = {};                       // { vendedor: { idDoDeal: ['contatei', ...] } }
  var storeOk = true;
  (function loadStore() {
    var raw = lsGet(K_ACOES);
    if (raw) { try { var o = JSON.parse(raw); if (o && typeof o === 'object') { store = o; } } catch (e) { store = {}; } }
  })();
  function marksOf(agent, id) { return (store[agent] && store[agent][id]) || []; }
  function hasMark(agent, id, key) { return marksOf(agent, id).indexOf(key) >= 0; }
  function toggleMark(agent, id, key) {
    var cur = marksOf(agent, id).slice();
    var i = cur.indexOf(key);
    if (i >= 0) { cur.splice(i, 1); } else { cur.push(key); }
    if (!store[agent]) { store[agent] = {}; }
    if (cur.length) { store[agent][id] = cur; } else { delete store[agent][id]; }
    storeOk = lsSet(K_ACOES, JSON.stringify(store));
    return i < 0;
  }
  var sim = {};                         // simulador "e se eu fechar este?" (só nesta sessão da página)

  /* ------------------------------------------------------------------ estado (no location.hash) */
  var state = blankState();
  var activeCat = 'Foque';
  function blankState() {
    return { perfil: '', nome: '', ver: '', pauta: '', ordem: '', dir: '', vendedor: '', manager: '', regiao: '', modo: '', aba: '' };
  }
  var PERFIS = ['vendedor', 'manager', 'revops'];

  function normalize(s) {
    if (PERFIS.indexOf(s.perfil) < 0) { s.perfil = ''; }
    if (s.perfil === 'vendedor') {
      if (!agentsByName[s.nome]) { s.perfil = ''; }
      else { s.manager = ''; s.regiao = ''; s.vendedor = ''; s.ver = ''; s.pauta = ''; s.ordem = ''; s.dir = ''; }
    } else if (s.perfil === 'manager') {
      if (!managersByName[s.nome]) { s.perfil = ''; }
      else {
        s.vendedor = ''; s.manager = ''; s.regiao = '';
        var ag = s.ver ? agentsByName[s.ver] : null;
        if (!ag || ag.manager !== s.nome) { s.ver = ''; }
        if (!s.ver) { s.pauta = ''; }
      }
    } else if (s.perfil === 'revops') {
      s.nome = ''; s.ver = ''; s.pauta = ''; s.ordem = ''; s.dir = '';
      if (s.regiao && D.people.regions.indexOf(s.regiao) < 0) { s.regiao = ''; }
      var m = s.manager ? managersByName[s.manager] : null;
      if (s.manager && !m) { s.manager = ''; m = null; }
      if (m && s.regiao && m.region !== s.regiao) { s.manager = ''; }
      var a = s.vendedor ? agentsByName[s.vendedor] : null;
      if (s.vendedor && !a) { s.vendedor = ''; a = null; }
      if (a && s.manager && a.manager !== s.manager) { s.vendedor = ''; }
      if (a && s.regiao && a.region !== s.regiao) { s.vendedor = ''; }
    }
    if (!s.perfil) {
      s.nome = ''; s.ver = ''; s.pauta = ''; s.ordem = ''; s.dir = ''; s.vendedor = ''; s.manager = ''; s.regiao = ''; s.aba = '';
    }
    if (s.pauta !== '1') { s.pauta = ''; }
    if (s.ordem && s.ordem !== 'nome' && CATS.indexOf(s.ordem) < 0) { s.ordem = ''; }
    if (s.dir !== 'asc' && s.dir !== 'desc') { s.dir = ''; }
    if (!snapByDate[s.modo] || snapByDate[s.modo] === todaySnap) { s.modo = ''; }
    if (CATS.indexOf(s.aba) < 0) { s.aba = ''; }
    return s;
  }
  function parseHash() {
    var p = new URLSearchParams((location.hash || '').replace(/^#/, ''));
    var s = {
      perfil: p.get('perfil') || '', nome: p.get('nome') || '', ver: p.get('ver') || '', pauta: p.get('pauta') || '',
      ordem: p.get('ordem') || '', dir: p.get('dir') || '',
      vendedor: p.get('vendedor') || '', manager: p.get('manager') || '', regiao: p.get('regiao') || '',
      modo: p.get('modo') || '', aba: p.get('aba') || ''
    };
    if (!s.perfil && (s.vendedor || s.manager || s.regiao)) { s.perfil = 'revops'; }   // links antigos
    return normalize(s);
  }
  function serialize(s) {
    var p = new URLSearchParams();
    ['perfil', 'nome', 'ver', 'pauta', 'ordem', 'dir', 'vendedor', 'manager', 'regiao', 'modo', 'aba'].forEach(function (k) {
      if (s[k]) { p.set(k, s[k]); }
    });
    return p.toString();
  }
  var lastHash = '';
  function writeHash() {
    lastHash = serialize(state);
    var url = lastHash ? '#' + lastHash : location.pathname + location.search;
    try { history.replaceState(null, '', url); }
    catch (e) { location.hash = lastHash; }
  }

  function currentSnap() { return state.modo ? snapByDate[state.modo] : todaySnap; }
  function isTest(snap) { return snap.mode === TEST; }
  function isVend() { return state.perfil === 'vendedor'; }
  function isMgr() { return state.perfil === 'manager'; }

  /* ------------------------------------------------------------------ dados filtrados */
  // O escopo é decidido pelo perfil: vendedor vê só o próprio nome; manager vê o time (e, se abrir, um vendedor dele).
  function scopeOf(withVer) {
    if (isVend()) { return { agent: state.nome, manager: '', region: '' }; }
    if (isMgr()) { return { agent: withVer ? state.ver : '', manager: state.nome, region: '' }; }
    return { agent: state.vendedor, manager: state.manager, region: state.regiao };
  }
  function filterDeals(snap, sc) {
    return snap.deals.filter(function (d) {
      return (!sc.agent || d.agent === sc.agent) && (!sc.manager || d.manager === sc.manager) && (!sc.region || d.region === sc.region);
    });
  }
  function groupByCat(list) {
    var g = {};
    CATS.forEach(function (c) { g[c] = []; });
    list.forEach(function (d) { if (g[d.cat]) { g[d.cat].push(d); } });
    return g;
  }
  function statsOf(groups) {
    var st = {};
    CATS.forEach(function (c) {
      var n = 0, valor = 0, ev = 0;
      groups[c].forEach(function (d) { n += 1; valor += d.price; if (d.ev != null) { ev += d.ev; } });
      st[c] = { n: n, valor: valor, ev: ev };
    });
    return st;
  }

  /* ------------------------------------------------------------------ controles (barra e filtros) */
  var modeSel = $('mode-select');
  var agentSel = $('filter-agent');
  var managerSel = $('filter-manager');
  var regionSel = $('filter-region');
  var lastOptions = { agent: null, manager: null, region: null };

  modeSel.innerHTML = D.snapshots.map(function (s) {
    return '<option value="' + esc(s.date) + '">' + esc(s.label) + '</option>';
  }).join('');

  function setOptions(sel, key, html, value) {
    if (lastOptions[key] !== html) { sel.innerHTML = html; lastOptions[key] = html; }
    sel.value = value;
  }

  function sortedManagers(region) {
    return D.people.managers.filter(function (m) { return !region || m.region === region; })
      .sort(function (a, b) { return byName(a.name, b.name); });
  }
  function agentOptionsHtml(mans, onlyManager, counts, first) {
    var html = first;
    mans.forEach(function (m) {
      if (onlyManager && m.name !== onlyManager) { return; }
      var ags = D.people.agents.filter(function (a) { return a.manager === m.name; })
        .sort(function (a, b) { return byName(a.name, b.name); });
      if (!ags.length) { return; }
      html += '<optgroup label="' + esc('Time de ' + m.name + ' — ' + m.region) + '">' + ags.map(function (a) {
        var suffix = !a.has_deals ? ' (sem deals no CRM)' : (!counts[a.name] ? ' (sem deals abertos)' : '');
        return '<option value="' + esc(a.name) + '">' + esc(a.name + suffix) + '</option>';
      }).join('') + '</optgroup>';
    });
    return html;
  }

  function renderControls(snap) {
    modeSel.value = snap.date;
    if (state.perfil !== 'revops') { return; }
    setOptions(regionSel, 'region',
      '<option value="">Todas as regiões</option>' + D.people.regions.slice().sort(byName).map(function (r) {
        return '<option value="' + esc(r) + '">' + esc(r) + '</option>';
      }).join(''), state.regiao);
    var mans = sortedManagers(state.regiao);
    setOptions(managerSel, 'manager',
      '<option value="">Todos os managers</option>' + mans.map(function (m) {
        return '<option value="' + esc(m.name) + '">' + esc(m.name) + '</option>';
      }).join(''), state.manager);
    setOptions(agentSel, 'agent', agentOptionsHtml(mans, state.manager, perAgent(snap), '<option value="">Todos os vendedores</option>'), state.vendedor);
  }

  function renderBanner(snap) {
    var el = $('test-banner');
    if (!isTest(snap)) { el.hidden = true; el.innerHTML = ''; return; }
    el.hidden = false;
    el.innerHTML = '<div class="wrap banner-in"><p><strong>Modo teste</strong> — o que o score recomendaria em ' +
      dateBR(snap.date) + ' e o que aconteceu até ' + dateBR(D.meta.reference_date) +
      '. Só entra o que se sabia naquela data.</p>' +
      '<p class="banner-note" data-testid="test-banner-note">Os números de resultado seguem o perfil escolhido. Para um vendedor só mostramos ' +
      'contagens, não taxa de vitória: a diferença entre vendedores é compatível com ruído.</p>' +
      '<button type="button" class="btn" id="back-today" data-testid="back-to-today">Voltar para hoje</button></div>';
  }

  /* ------------------------------------------------------------------ tela de entrada */
  var entryAgent = $('entry-agent');
  var entryMgr = $('entry-mgr');
  var entryBuilt = false;
  function buildEntry() {
    if (entryBuilt) { return; }
    entryBuilt = true;
    entryAgent.innerHTML = agentOptionsHtml(sortedManagers(''), '', perAgent(todaySnap), '<option value="">Escolha o seu nome</option>');
    entryMgr.innerHTML = '<option value="">Escolha o seu nome</option>' + sortedManagers('').map(function (m) {
      return '<option value="' + esc(m.name) + '">' + esc(m.name + ' — ' + m.region) + '</option>';
    }).join('');
  }
  function lastProfile() {
    var raw = lsGet(K_PERFIL);
    if (!raw) { return null; }
    try {
      var o = JSON.parse(raw);
      if (o && o.perfil === 'vendedor' && agentsByName[o.nome]) { return o; }
      if (o && o.perfil === 'manager' && managersByName[o.nome]) { return o; }
    } catch (e) { return null; }
    return null;
  }
  function renderEntry() {
    buildEntry();
    var last = lastProfile(), box = $('entry-last'), btn = $('entry-continue');
    if (!last) { box.hidden = true; return; }
    box.hidden = false;
    btn.textContent = 'Continuar como ' + last.nome + ' (' + (last.perfil === 'vendedor' ? 'vendedor' : 'manager') + ')';
    btn.setAttribute('data-perfil', last.perfil);
    btn.setAttribute('data-nome', last.nome);
  }
  function fieldError(sel, msg) {
    var id = sel.id + '-err', old = $(id);
    if (old) { old.remove(); }
    sel.removeAttribute('aria-invalid');
    sel.removeAttribute('aria-describedby');
    if (!msg) { return; }
    var p = document.createElement('p');
    p.id = id; p.className = 'field-error'; p.setAttribute('role', 'alert'); p.textContent = msg;
    sel.insertAdjacentElement('afterend', p);
    sel.setAttribute('aria-invalid', 'true');
    sel.setAttribute('aria-describedby', id);
    sel.focus();
  }
  function enter(perfil, nome) {
    if (perfil !== 'revops') { lsSet(K_PERFIL, JSON.stringify({ perfil: perfil, nome: nome })); }
    var keepMode = state.modo;
    state = blankState();
    state.perfil = perfil; state.nome = nome; state.modo = keepMode;
    sim = {};
    pendingFocus = 'eyebrow';
    commit();
  }
  $('entry-vendedor').addEventListener('submit', function (e) {
    e.preventDefault();
    if (!entryAgent.value) { fieldError(entryAgent, 'Escolha o seu nome para continuar.'); return; }
    fieldError(entryAgent, '');
    enter('vendedor', entryAgent.value);
  });
  $('entry-manager').addEventListener('submit', function (e) {
    e.preventDefault();
    if (!entryMgr.value) { fieldError(entryMgr, 'Escolha o seu nome para continuar.'); return; }
    fieldError(entryMgr, '');
    enter('manager', entryMgr.value);
  });
  entryAgent.addEventListener('change', function () { fieldError(entryAgent, ''); });
  entryMgr.addEventListener('change', function () { fieldError(entryMgr, ''); });
  $('entry-continue').addEventListener('click', function () {
    enter(this.getAttribute('data-perfil'), this.getAttribute('data-nome'));
  });
  $('enter-revops').addEventListener('click', function () { enter('revops', ''); });
  $('switch-profile').addEventListener('click', function () {
    var keepMode = state.modo;
    state = blankState();
    state.modo = keepMode;
    sim = {};
    pendingFocus = 'entry-title';
    commit();
  });

  /* ------------------------------------------------------------------ identidade e frase de ação */
  function scopeText() {
    var sc = scopeOf(false);
    var a = sc.agent ? agentsByName[sc.agent] : null;
    if (a) { return a.name + ' · time de ' + a.manager + ' · ' + a.region; }
    if (sc.manager) { return 'Time de ' + sc.manager + ' · ' + managersByName[sc.manager].region; }
    if (sc.region) { return 'Região ' + sc.region + ' · todos os managers'; }
    return 'Todos os vendedores · todos os managers e regiões';
  }
  function nHtml(c, text) { return '<span class="n cat-' + c + '">' + text + '</span>'; }
  function accent(t) { return '<em class="accent">' + t + '</em>'; }

  // Sem Foque nem Reative e com Prospecting: a receita nova está no Qualifique (não existe no modo teste).
  function noLiveDeals(snap, st) {
    return !isTest(snap) && !st.Foque.n && !st.Reative.n && st.Qualifique.n > 0;
  }

  function renderIdentity() {
    var tag = $('role-tag'), who = $('who'), sub = $('who-sub');
    if (isVend()) {
      var a = agentsByName[state.nome];
      tag.textContent = 'Vendedor'; who.textContent = a.name; sub.textContent = 'time de ' + a.manager + ' · ' + a.region;
      $('eyebrow').textContent = 'Minha semana';
    } else if (isMgr()) {
      var m = managersByName[state.nome];
      var n = D.people.agents.filter(function (x) { return x.manager === m.name; }).length;
      tag.textContent = 'Manager'; who.textContent = m.name; sub.textContent = m.region + ' · ' + num(n) + ' ' + plural(n, 'vendedor', 'vendedores');
      $('eyebrow').textContent = 'Meu time';
    } else {
      tag.textContent = 'RevOps'; who.textContent = 'Visão completa'; sub.textContent = 'todos os vendedores, managers e regiões';
      $('eyebrow').textContent = 'Visão completa';
    }
    $('filters').hidden = state.perfil !== 'revops';
  }

  function renderAction(snap, st, total) {
    $('scope-label').textContent = scopeText();
    $('scope-label').hidden = state.perfil !== 'revops';          // vendedor e manager já têm a identidade na barra de perfil
    var hint = $('hero-hint');
    hint.hidden = !isMgr();
    hint.textContent = isMgr() ? 'Clique no nome de um vendedor para abrir a carteira dele em modo leitura e gerar a pauta do 1:1.' : '';
    var el = $('action-summary');
    var sc = scopeOf(false);
    if (!total) {
      var ag = sc.agent ? agentsByName[sc.agent] : null;
      if (ag && !ag.has_deals) {
        el.innerHTML = isVend() ? 'Você não tem deals no CRM (cadastro sem pipeline).'
          : '<strong>' + esc(ag.name) + '</strong> não tem deals no CRM (cadastro sem pipeline).';
      } else if (isVend()) { el.textContent = 'Você não tem deals abertos agora.'; }
      else { el.textContent = 'Nenhum deal para priorizar nesta seleção.'; }
      return;
    }
    var test = isTest(snap), parts = [], lead;
    if (isMgr()) {
      if (st.Foque.n) { parts.push(nHtml('Foque', num(st.Foque.n)) + ' ' + plural(st.Foque.n, 'deal vivo', 'deals vivos')); }
      if (st.Reative.n) { parts.push(nHtml('Reative', num(st.Reative.n)) + ' esfriando'); }
      if (st.Limpe.n) { parts.push(nHtml('Limpe', num(st.Limpe.n)) + ' ' + plural(st.Limpe.n, 'zumbi', 'zumbis') + ' (' + nHtml('Limpe', usd(st.Limpe.valor)) + ' parados)'); }
      if (!test && st.Qualifique.n) { parts.push(nHtml('Qualifique', num(st.Qualifique.n)) + ' em Prospecting para qualificar'); }
      lead = test ? 'Em ' + dateBR(snap.date) + ' ' + accent('o time tinha') + ': ' : accent('Seu time') + ' hoje: ';
      el.innerHTML = lead + joinPt(parts) + '.';
      return;
    }
    var newRevenue = noLiveDeals(snap, st);
    if (newRevenue) {
      parts.push('qualifique ' + nHtml('Qualifique', num(st.Qualifique.n)) + ' em Prospecting (a receita nova está no Qualifique)');
    }
    if (st.Foque.n) { parts.push('foque em ' + nHtml('Foque', num(st.Foque.n)) + ' ' + plural(st.Foque.n, 'deal', 'deals')); }
    if (st.Reative.n) { parts.push('reative ' + nHtml('Reative', num(st.Reative.n)) + ' antes que ' + plural(st.Reative.n, 'esfrie', 'esfriem')); }
    if (st.Limpe.n) {
      parts.push('limpe ' + nHtml('Limpe', num(st.Limpe.n)) + ' do CRM (' + nHtml('Limpe', usd(st.Limpe.valor)) + ' parados)');
    }
    if (!newRevenue && !test && st.Qualifique.n) { parts.push('qualifique ' + nHtml('Qualifique', num(st.Qualifique.n)) + ' em Prospecting'); }
    lead = test ? 'Em ' + dateBR(snap.date) + ' ' + accent('o score teria dito') + ': ' : accent('Esta semana') + ': ';
    el.innerHTML = lead + joinPt(parts) + '.';
  }

  /* ------------------------------------------------------------------ progresso e valor da semana (só vendedor, só "hoje") */
  var cur = { snap: null, groups: null, st: null, list: [] };

  function animateNumber(el, to, fmt) {
    var from = el._val == null ? to : el._val;
    el._val = to;
    el.setAttribute('data-value', String(Math.round(to)));
    if (el._raf) { window.cancelAnimationFrame(el._raf); el._raf = 0; }
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || from === to) { el.textContent = fmt(to); return; }
    var t0 = null;
    function step(ts) {
      if (t0 === null) { t0 = ts; }
      var k = Math.min(1, (ts - t0) / COUNT_MS);
      var e = 1 - Math.pow(1 - k, 3);
      el.textContent = fmt(from + (to - from) * e);
      if (k < 1) { el._raf = window.requestAnimationFrame(step); } else { el.textContent = fmt(to); el._raf = 0; }
    }
    el._raf = window.requestAnimationFrame(step);
  }

  function renderStats() {
    var snap = cur.snap, groups = cur.groups;
    var on = isVend() && !isTest(snap) && cur.list.length > 0;
    $('stats').hidden = !on;
    $('save-note').hidden = !on;
    if (!on) { return; }
    var agent = state.nome;
    var sales = groups.Foque.length + groups.Reative.length > 0;
    var cats = sales ? ['Foque', 'Reative'] : ['Limpe', 'Qualifique'];
    var total = 0, done = 0, lists = [];
    cats.forEach(function (c) {
      var d = groups[c].filter(function (x) { return marksOf(agent, x.id).length > 0; }).length;
      total += groups[c].length; done += d;
    });
    ['Foque', 'Reative', 'Limpe'].forEach(function (c) {
      if (!groups[c].length) { return; }
      var d = groups[c].filter(function (x) { return marksOf(agent, x.id).length > 0; }).length;
      lists.push(c + ' ' + num(d) + ' de ' + num(groups[c].length));
    });
    $('prog-done').textContent = num(done);
    $('prog-total').textContent = num(total);
    var frac = total ? done / total : 0;
    $('prog-fill').style.width = (frac * 100).toFixed(2) + '%';
    var bar = $('prog-bar');
    bar.setAttribute('aria-valuenow', String(Math.round(frac * 100)));
    bar.setAttribute('aria-valuetext', num(done) + ' de ' + num(total) + ' ' + plural(total, 'deal tratado', 'deals tratados'));
    bar.setAttribute('aria-label', 'Deals tratados em ' + joinPt(cats));
    $('prog-lists').textContent = (storeOk ? '' : 'Não foi possível salvar neste navegador. ') + lists.join(' · ') +
      (lists.length ? ' · tratados por lista' : '');

    // valor esperado da semana (Foque + Reative) e o efeito do simulador
    var weekBox = document.querySelector('[data-testid=stat-week]');
    weekBox.hidden = !sales;
    $('stats').classList.toggle('one', !sales);
    if (sales) {
      var base = 0, plus = 0, nsim = 0;
      groups.Foque.concat(groups.Reative).forEach(function (d) {
        base += d.ev || 0;
        if (sim[d.id]) { plus += d.price - (d.ev || 0); nsim += 1; }
      });
      animateNumber($('week-value'), base + plus, usd);
      $('week-sub').textContent = nsim
        ? 'Fechando ' + num(nsim) + ' ' + plural(nsim, 'deal', 'deals') + ' do simulador: ' + usd(plus) + ' a mais que o esperado.'
        : 'Foque e Reative: chance × preço de tabela. Use “E se eu fechar este?” nos cards.';
      $('sim-clear').hidden = !nsim;
      $('stat-week').classList.toggle('live', nsim > 0);
    }
    if (!storeOk) { $('save-note').textContent = 'Não foi possível salvar neste navegador: as marcações valem só até fechar a página.'; }
    else { $('save-note').textContent = 'Suas marcações ficam salvas só neste navegador.'; }
  }

  /* ------------------------------------------------------------------ abas = KPIs */
  var tabsEl = $('tabs');
  var tabRefs = {};
  CATS.forEach(function (c) {
    var b = document.createElement('button');
    b.type = 'button';
    b.id = 'tab-' + c;
    b.className = 'tab cat-' + c;
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-controls', 'panel');
    b.setAttribute('data-testid', 'tab-' + c);
    b.innerHTML = '<span class="tab-name">' + icon(c) + '<span class="tab-label">' + c + '</span></span>' +
      '<span class="tab-count" data-testid="count-' + c + '"></span>' +
      '<span class="tab-value"></span>';
    tabsEl.appendChild(b);
    tabRefs[c] = { btn: b, count: b.querySelector('.tab-count'), value: b.querySelector('.tab-value') };
  });

  function renderTabs(snap, st) {
    CATS.forEach(function (c) {
      var r = tabRefs[c];
      var off = isTest(snap) && c === 'Qualifique';
      r.count.setAttribute('data-count', off ? '0' : String(st[c].n));
      r.count.textContent = off ? '—' : num(st[c].n);
      r.value.textContent = off ? 'indisponível no teste' : usd(st[c].valor) + ' de tabela';
      var sel = activeCat === c;
      r.btn.setAttribute('aria-selected', sel ? 'true' : 'false');
      r.btn.tabIndex = sel ? 0 : -1;
    });
  }

  tabsEl.addEventListener('click', function (e) {
    var b = e.target.closest('.tab');
    if (!b) { return; }
    state.aba = b.id.replace('tab-', '');
    commit();
  });
  tabsEl.addEventListener('keydown', function (e) {
    var i = CATS.indexOf(activeCat), k = e.key;
    if (k === 'ArrowRight' || k === 'ArrowDown') { i = (i + 1) % CATS.length; }
    else if (k === 'ArrowLeft' || k === 'ArrowUp') { i = (i + CATS.length - 1) % CATS.length; }
    else if (k === 'Home') { i = 0; }
    else if (k === 'End') { i = CATS.length - 1; }
    else { return; }
    e.preventDefault();
    state.aba = CATS[i];
    commit();
    tabRefs[activeCat].btn.focus();
  });

  /* ------------------------------------------------------------------ resultado do modo teste */
  // Recalculado a partir dos deals do escopo (abas, frase de ação e resumos usam a mesma lista).
  // Para um vendedor só há contagens, sem porcentagem (a diferença entre vendedores é compatível com ruído).
  function outcomeStats(deals) {
    var won = 0, revenue = 0;
    deals.forEach(function (d) {
      if (d.outcome && d.outcome.status === 'Ganho') { won += 1; revenue += d.outcome.close_value || 0; }
    });
    return { n: deals.length, won: won, revenue: revenue };
  }
  function renderResults(snap, groups) {
    var el = $('results');
    if (!isTest(snap) || !snap.outcome_summary) { el.hidden = true; el.innerHTML = ''; return; }
    var counts = !!scopeOf(false).agent;
    var html = '<h2>O que aconteceu até ' + dateBR(D.meta.reference_date) +
      ' <span class="muted">(' + esc(scopeText()) + ')</span></h2><div class="results-grid">';
    CATS.forEach(function (c) {
      if (!snap.outcome_summary[c]) { return; }
      var o = outcomeStats(groups[c]);
      var big = counts ? num(o.won) : (o.n ? pct1(o.won / o.n) : '—');
      var sub = counts
        ? plural(o.won, 'deal ganho', 'deals ganhos') + ', de ' + num(o.n) + ' ' + plural(o.n, 'deal', 'deals')
        : 'foram ganhos, de ' + num(o.n) + ' ' + plural(o.n, 'deal', 'deals');
      html += '<div class="res cat-' + c + '" data-testid="backtest-summary-' + c + '" data-n="' + o.n +
        '" data-won="' + o.won + '" data-revenue="' + o.revenue + '"' +
        (counts || !o.n ? '' : ' data-pct="' + (o.won / o.n * 100).toFixed(1) + '"') + '>' +
        '<span class="res-name">' + icon(c) + c + '</span>' +
        '<span class="res-pct">' + big + '</span>' +
        '<span class="res-sub">' + sub + ' · ' + usd(o.revenue) + ' de receita</span></div>';
    });
    el.innerHTML = html + '</div>';
    el.hidden = false;
  }

  /* ------------------------------------------------------------------ visão completa: carteira do time (tabela simples) */
  var teamEl = $('team');
  var lastTeamKey = null;

  function renderTeam(snap, list) {
    if (state.perfil !== 'revops' || state.vendedor) { teamEl.innerHTML = ''; lastTeamKey = null; return; }
    var key = [snap.date, state.manager, state.regiao].join('|');
    if (key === lastTeamKey) { return; }
    var existing = teamEl.querySelector('details');
    var wasOpen = existing && lastTeamKey !== null && lastTeamKey.split('|').slice(1).join('|') === key.split('|').slice(1).join('|')
      ? existing.open : null;
    lastTeamKey = key;

    var ags = D.people.agents.filter(function (a) {
      return (!state.manager || a.manager === state.manager) && (!state.regiao || a.region === state.regiao);
    }).sort(function (a, b) { return byName(a.name, b.name); });
    var counts = {};
    list.forEach(function (d) {
      var c = counts[d.agent] || (counts[d.agent] = { Foque: 0, Reative: 0, Limpe: 0, Qualifique: 0 });
      c[d.cat] += 1;
    });
    var test = isTest(snap);
    var open = wasOpen !== null ? wasOpen : !!(state.manager || state.regiao);

    var rows = ags.map(function (a) {
      var c = counts[a.name] || { Foque: 0, Reative: 0, Limpe: 0, Qualifique: 0 };
      var total = c.Foque + c.Reative + c.Limpe + c.Qualifique;
      var alert = !a.has_deals ? 'Sem deals no CRM (cadastro sem pipeline)' : (!total ? 'Sem deals abertos' : '');
      var tds = CATS.map(function (cat) {
        if (test && cat === 'Qualifique') { return '<td class="zero">—</td>'; }
        return '<td' + (c[cat] ? '' : ' class="zero"') + '>' + num(c[cat]) + '</td>';
      }).join('');
      return '<tr data-agent="' + esc(a.name) + '"><th scope="row"><button type="button" class="link-btn" data-pick="' +
        esc(a.name) + '">' + esc(a.name) + '</button>' +
        (alert ? '<span class="row-alert">' + esc(alert) + '</span>' : '') + '</th>' + tds + '</tr>';
    }).join('');

    teamEl.innerHTML = '<details class="team"' + (open ? ' open' : '') + ' data-testid="team-details">' +
      '<summary>Carteira do time <span class="muted">· ' + num(ags.length) + ' ' + plural(ags.length, 'vendedor', 'vendedores') + '</span></summary>' +
      '<p class="team-note">Só contagens de deals por lista, em ordem alfabética. Sem taxa de vitória por vendedor: a diferença entre vendedores é compatível com ruído.</p>' +
      '<div class="table-wrap"><table data-testid="team-table"><thead><tr><th>Vendedor</th>' +
      CATS.map(function (c) { return '<th class="th-' + c + '">' + c + '</th>'; }).join('') +
      '</tr></thead><tbody>' + rows + '</tbody></table></div></details>';
  }

  teamEl.addEventListener('click', function (e) {
    var b = e.target.closest('[data-pick]');
    if (!b) { return; }
    state.vendedor = b.getAttribute('data-pick');
    normalize(state);
    commit();
    window.scrollTo(0, 0);
  });

  /* ------------------------------------------------------------------ manager: mapa do time */
  var mapEl = $('teammap-body');
  var SORTS = [
    { v: 'nome:asc', label: 'Nome (A a Z)' },
    { v: 'Foque:desc', label: 'Vivos (mais primeiro)' },
    { v: 'Reative:desc', label: 'Esfriando (mais primeiro)' },
    { v: 'Limpe:desc', label: 'Zumbis (mais primeiro)' }
  ];
  function sortKey() {
    var k = state.ordem || 'nome';
    var d = state.dir || (k === 'nome' ? 'asc' : 'desc');
    return { key: k, dir: d };
  }
  function teamRows(snap, teamList) {
    var by = {};
    teamList.forEach(function (d) {
      var r = by[d.agent] || (by[d.agent] = { Foque: { n: 0, v: 0 }, Reative: { n: 0, v: 0 }, Limpe: { n: 0, v: 0 }, Qualifique: { n: 0, v: 0 } });
      r[d.cat].n += 1; r[d.cat].v += d.price;
    });
    var ags = D.people.agents.filter(function (a) { return a.manager === state.nome; });
    var rows = ags.map(function (a) {
      var r = by[a.name] || { Foque: { n: 0, v: 0 }, Reative: { n: 0, v: 0 }, Limpe: { n: 0, v: 0 }, Qualifique: { n: 0, v: 0 } };
      return { a: a, c: r };
    });
    var sk = sortKey(), sign = sk.dir === 'asc' ? 1 : -1;
    rows.sort(function (x, y) {
      var r = sk.key === 'nome' ? byName(x.a.name, y.a.name) : x.c[sk.key].n - y.c[sk.key].n;
      return r ? r * sign : byName(x.a.name, y.a.name);
    });
    return rows;
  }
  function sortTh(key, label, cls) {
    var sk = sortKey(), on = sk.key === key;
    var ind = on ? (sk.dir === 'asc' ? 'up' : 'down') : 'sort';
    var inner = key === 'nome' ? '<span>' + label + '</span>' : '<span class="th-cat cat-' + key + '">' + icon(key) + label + '</span>';
    return '<th scope="col" class="' + cls + '" aria-sort="' + (on ? (sk.dir === 'asc' ? 'ascending' : 'descending') : 'none') + '">' +
      '<button type="button" class="sort" data-sort="' + key + '" data-testid="sort-' + key + '">' + inner + icon(ind, 'sort-ind') + '</button></th>';
  }
  function cellHtml(cat, cell, test) {
    var label = MGR_LABEL[cat];
    if (test && cat === 'Qualifique') { return '<td class="num" data-label="' + label + '"><span class="cell-n zero">—</span></td>'; }
    return '<td class="num" data-label="' + label + '" data-cat="' + cat + '"><span class="cell-n' + (cell.n ? '' : ' zero') + '" data-testid="cell-' + cat + '">' + num(cell.n) +
      '</span><span class="cell-v">' + (cell.n ? usd(cell.v) + ' de tabela' : '—') + '</span></td>';
  }
  function renderTeamMap(snap, teamList) {
    var box = $('teammap');
    box.hidden = !isMgr();
    if (!isMgr()) { mapEl.innerHTML = ''; return; }
    var test = isTest(snap), rows = teamRows(snap, teamList), sk = sortKey();
    var tot = { Foque: { n: 0, v: 0 }, Reative: { n: 0, v: 0 }, Limpe: { n: 0, v: 0 }, Qualifique: { n: 0, v: 0 } };
    var body = rows.map(function (r) {
      var c = r.c, a = r.a;
      CATS.forEach(function (k) { tot[k].n += c[k].n; tot[k].v += c[k].v; });
      var open = c.Foque.n + c.Reative.n + c.Limpe.n;
      var alert = !a.has_deals ? 'Sem deals no CRM (cadastro sem pipeline)' : (!open && !c.Qualifique.n ? 'Sem deals abertos' : '');
      var hyg;
      if (!open) { hyg = '<span class="hyg-text">' + (a.has_deals ? 'Sem deals em Engaging' : 'Sem deals no CRM') + '</span>'; }
      else {
        hyg = '<span class="hyg-text">' + num(c.Limpe.n) + ' ' + plural(c.Limpe.n, 'zumbi', 'zumbis') + ' em ' + num(open) + ' ' + plural(open, 'deal aberto', 'deals abertos') + '</span>' +
          '<span class="hyg-track" aria-hidden="true"><span class="hyg-fill" style="width:' + (c.Limpe.n / open * 100).toFixed(1) + '%"></span></span>';
      }
      return '<tr data-agent="' + esc(a.name) + '"' + (state.ver === a.name ? ' class="is-open"' : '') + '>' +
        '<th scope="row"><button type="button" class="open-btn" data-open="' + esc(a.name) + '" data-testid="open-agent"' +
        (state.ver === a.name ? ' aria-current="true"' : '') + '>' + esc(a.name) + '</button>' +
        (alert ? '<span class="row-alert">' + esc(alert) + '</span>' : '') + '</th>' +
        CATS.map(function (k) { return cellHtml(k, c[k], test); }).join('') +
        '<td class="hyg-cell" data-label="Higiene de carteira"><span class="hyg" data-testid="hyg">' + hyg + '</span></td>' +
        '<td class="act-cell" data-label="1:1"><button type="button" class="btn btn-small" data-pauta="' + esc(a.name) + '" data-testid="row-pauta">Pauta do 1:1</button></td></tr>';
    }).join('');
    var foot = '<tr><th scope="row">Time inteiro</th>' + CATS.map(function (k) { return cellHtml(k, tot[k], test); }).join('') +
      '<td class="hyg-cell" data-label="Higiene de carteira"><span class="hyg-text">' + num(tot.Limpe.n) + ' ' + plural(tot.Limpe.n, 'zumbi', 'zumbis') + '</span></td><td class="act-cell"></td></tr>';
    var sortVal = sk.key + ':' + sk.dir;
    var opts = SORTS.map(function (s) {
      return '<option value="' + s.v + '"' + (s.v === sortVal ? ' selected' : '') + '>' + s.label + '</option>';
    }).join('');
    mapEl.innerHTML =
      '<div class="map-tools"><label for="map-sort">Ordenar por</label><select id="map-sort" data-testid="map-sort">' + opts + '</select></div>' +
      '<div class="map-wrap"><table class="map" data-testid="team-map"><caption class="sr-only">Carteira de cada vendedor do time: deals e valor de tabela por grupo, com a higiene da carteira.</caption>' +
      '<thead><tr>' + sortTh('nome', 'Vendedor', '') +
      CATS.map(function (k) { return sortTh(k, MGR_LABEL[k], 'num'); }).join('') +
      '<th scope="col">Higiene de carteira</th><th scope="col"><span class="sr-only">Ações</span></th></tr></thead>' +
      '<tbody>' + body + '</tbody><tfoot>' + foot + '</tfoot></table></div>';
  }

  var pendingSortFocus = '';
  $('teammap').addEventListener('click', function (e) {
    var s = e.target.closest('[data-sort]');
    if (s) {
      var k = s.getAttribute('data-sort'), cur0 = sortKey();
      var dir = cur0.key === k ? (cur0.dir === 'asc' ? 'desc' : 'asc') : (k === 'nome' ? 'asc' : 'desc');
      state.ordem = (k === 'nome' && dir === 'asc') ? '' : k;
      state.dir = (k === 'nome' && dir === 'asc') || (k !== 'nome' && dir === 'desc') ? '' : dir;
      pendingSortFocus = k;
      announce('Ordenado por ' + (k === 'nome' ? 'nome' : MGR_LABEL[k].toLowerCase()) + ', ' + (dir === 'asc' ? 'crescente' : 'decrescente') + '.');
      commit();
      return;
    }
    var o = e.target.closest('[data-open]');
    if (o) { state.ver = o.getAttribute('data-open'); state.pauta = ''; state.aba = ''; pendingFocus = 'wallet-title'; commit(); return; }
    var p = e.target.closest('[data-pauta]');
    if (p) { state.ver = p.getAttribute('data-pauta'); state.pauta = '1'; state.aba = ''; pendingFocus = 'pauta-title'; commit(); }
  });
  $('teammap').addEventListener('change', function (e) {
    if (e.target.id !== 'map-sort') { return; }
    var parts = e.target.value.split(':');
    state.ordem = parts[0] === 'nome' ? '' : parts[0];
    state.dir = parts[0] === 'nome' ? '' : (parts[1] === 'desc' ? '' : parts[1]);
    commit();
    var again = $('map-sort');
    if (again) { again.focus(); }
  });

  /* ------------------------------------------------------------------ manager: cabeçalho da carteira e pauta do 1:1 */
  function renderWalletHead(snap) {
    var head = $('wallet-head');
    var on = isMgr() && !!state.ver;
    head.hidden = !on;
    if (!on) { $('pauta').hidden = true; $('pauta').innerHTML = ''; return; }
    var a = agentsByName[state.ver];
    $('wallet-title').textContent = 'Carteira de ' + a.name;
    $('wallet-sub').textContent = 'Time de ' + a.manager + ' · ' + a.region + ' · ' + snap.label + '. Só leitura: as marcações do vendedor ficam no navegador dele.';
    $('pauta-btn').textContent = state.pauta ? 'Esconder a pauta do 1:1' : 'Gerar pauta do 1:1';
    $('pauta-btn').setAttribute('aria-expanded', state.pauta ? 'true' : 'false');
  }
  function pautaItem(d) {
    var acct = d.account ? d.account : 'Conta não informada';
    var bits = [usd(d.price) + ' de tabela'];
    if (d.p != null) { bits.push('chance ' + (d.p > 0 && d.p < 0.005 ? '<' + pct0(0.01) : pct0(d.p))); }
    if (d.age != null) { bits.push('há ' + days(d.age)); }
    return { title: acct + ' · ' + d.product, sub: bits.join(' · '), why: d.why && d.why.length ? d.why[0] : '' };
  }
  function buildPauta(snap, agentName) {
    var a = agentsByName[agentName];
    var g = groupByCat(snap.deals.filter(function (d) { return d.agent === agentName; }));
    var st = statsOf(g);
    var push = g.Foque.slice(0, PAUTA_N).map(pautaItem);
    var rescue = g.Reative.slice(0, PAUTA_N).map(pautaItem);
    var lines = ['Pauta do 1:1 — ' + a.name, 'Time de ' + a.manager + ' · ' + snap.label, '', 'Empurrar (' + num(push.length) + ' de ' + num(g.Foque.length) + ' em Foque)'];
    if (!push.length) { lines.push('- Nenhum deal em Foque.'); }
    push.forEach(function (it, i) { lines.push(num(i + 1) + '. ' + it.title + ' — ' + it.sub + (it.why ? '. ' + it.why : '')); });
    lines.push('', 'Resgatar (' + num(rescue.length) + ' de ' + num(g.Reative.length) + ' em Reative)');
    if (!rescue.length) { lines.push('- Nenhum deal em Reative.'); }
    rescue.forEach(function (it, i) { lines.push(num(i + 1) + '. ' + it.title + ' — ' + it.sub + (it.why ? '. ' + it.why : '')); });
    lines.push('', 'Limpar: ' + num(st.Limpe.n) + ' ' + plural(st.Limpe.n, 'deal', 'deals') + (st.Limpe.n ? ' (' + usd(st.Limpe.valor) + ' de tabela): confirmar com o cliente e encerrar ou atualizar no CRM.' : '.'));
    if (!isTest(snap) && st.Qualifique.n) { lines.push('Qualificar: ' + num(st.Qualifique.n) + ' em Prospecting, sem data de engajamento.'); }
    lines.push('', 'Higiene de carteira, não desempenho: sem taxa de vitória por vendedor.');
    return { agent: a, push: push, rescue: rescue, clean: st.Limpe, qualify: st.Qualifique, text: lines.join('\n') };
  }
  function pautaListHtml(items, emptyMsg) {
    if (!items.length) { return '<p class="none">' + emptyMsg + '</p>'; }
    return '<ol>' + items.map(function (it) {
      return '<li><p class="pauta-item-title">' + esc(it.title) + '</p><p class="pauta-item-sub">' + esc(it.sub) + '</p>' +
        (it.why ? '<p>' + esc(it.why) + '</p>' : '') + '</li>';
    }).join('') + '</ol>';
  }
  var pautaCurrent = null;
  function renderPauta(snap) {
    var box = $('pauta');
    if (!(isMgr() && state.ver && state.pauta)) { box.hidden = true; box.innerHTML = ''; pautaCurrent = null; return; }
    var p = buildPauta(snap, state.ver);
    pautaCurrent = p;
    box.hidden = false;
    box.innerHTML =
      '<div class="pauta-head"><div><h3 id="pauta-title" tabindex="-1">Pauta do 1:1 · ' + esc(p.agent.name) + '</h3>' +
      '<p class="muted">' + esc(snap.label) + '. Os ' + num(PAUTA_N) + ' primeiros de cada lista, na ordem do score.</p></div>' +
      '<div class="pauta-copy"><span id="pauta-status" class="pauta-status" data-testid="pauta-status" role="status"></span>' +
      '<button type="button" class="btn btn-primary" id="pauta-copy" data-testid="pauta-copy">Copiar pauta</button></div></div>' +
      '<div class="pauta-grid">' +
      '<div class="pauta-block cat-Foque" data-testid="pauta-push"><h4>' + icon('Foque') + 'Empurrar</h4>' + pautaListHtml(p.push, 'Nenhum deal em Foque.') + '</div>' +
      '<div class="pauta-block cat-Reative" data-testid="pauta-rescue"><h4>' + icon('Reative') + 'Resgatar</h4>' + pautaListHtml(p.rescue, 'Nenhum deal em Reative.') + '</div>' +
      '<div class="pauta-block cat-Limpe" data-testid="pauta-clean"><h4>' + icon('Limpe') + 'Limpar</h4>' +
      '<p class="big" data-testid="pauta-clean-n" data-n="' + p.clean.n + '">' + num(p.clean.n) + '</p>' +
      '<p class="pauta-item-sub">' + (p.clean.n ? plural(p.clean.n, 'deal', 'deals') + ' (' + usd(p.clean.valor) + ' de tabela) para confirmar com o cliente e encerrar ou atualizar.' : 'Nada para limpar.') + '</p></div>' +
      '</div>';
  }
  function copyText(text, done) {
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      done(ok);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else { fallback(); }
  }
  $('pauta').addEventListener('click', function (e) {
    if (!e.target.closest('#pauta-copy') || !pautaCurrent) { return; }
    var status = $('pauta-status');
    copyText(pautaCurrent.text, function (ok) {
      if (ok) {
        status.textContent = 'Pauta copiada.';
        status.setAttribute('data-copied', 'true');
        announce('Pauta copiada.');
      } else {
        status.textContent = 'Não consegui copiar sozinho. Selecione o texto abaixo e copie.';
        status.setAttribute('data-copied', 'false');
        if (!$('pauta').querySelector('.pauta-text')) {
          var ta = document.createElement('textarea');
          ta.className = 'pauta-text'; ta.readOnly = true; ta.value = pautaCurrent.text; ta.setAttribute('aria-label', 'Texto da pauta');
          $('pauta').appendChild(ta);
        }
        $('pauta').querySelector('.pauta-text').select();
      }
      window.setTimeout(function () { if (status.getAttribute('data-copied') === 'true') { status.textContent = ''; status.removeAttribute('data-copied'); } }, 4000);
    });
  });
  $('pauta-btn').addEventListener('click', function () {
    state.pauta = state.pauta ? '' : '1';
    pendingFocus = state.pauta ? 'pauta-title' : '';
    commit();
  });
  $('wallet-close').addEventListener('click', function () {
    var prev = state.ver;
    state.ver = ''; state.pauta = ''; state.aba = '';
    pendingFocus = '';
    commit();
    var btns = document.querySelectorAll('[data-open]');
    for (var i = 0; i < btns.length; i += 1) {
      if (btns[i].getAttribute('data-open') === prev) { btns[i].focus(); break; }
    }
  });

  /* ------------------------------------------------------------------ painel da lista e cards */
  var panelEl = $('panel');
  var cardsEl = $('cards');
  var emptyEl = $('empty');
  var moreWrap = $('more');
  var moreBtn = $('more-btn');
  var shownEl = $('shown-count');
  var items = [];
  var shown = 0;
  var dealById = {};

  function instruction(cat, m) {
    switch (cat) {
      case 'Foque':
        return '<strong>Avance</strong> estes deals primeiro: até ' + days(m.knot_days) +
          ' abertos a chance de ganho ainda é pelo menos metade da de um deal novo (' + pct0(m.p_fresh) +
          '). Ordem: maior valor esperado (chance × preço de tabela).';
      case 'Reative':
        return '<strong>Fale com o cliente esta semana:</strong> a chance já está caindo, ' +
          (m.limpe_rule === 'chance'
            ? 'e depois de ' + days(m.limpe_after_days) + ' abertos ela fica abaixo de ' + pct0(m.limpe_min_chance)
            : 'e nenhum deal foi ganho depois de ' + days(m.limpe_after_days) + ' abertos') +
          '. Ordem: maior valor esperado.';
      case 'Limpe':
        return '<strong>Pergunte ao cliente se ainda quer comprar:</strong> se não, marque Lost no CRM; se sim, atualize o deal. ' +
          (m.limpe_rule === 'chance'
            ? 'Estes deals estão abertos há mais de ' + days(m.limpe_after_days) + ': a chance de ganho caiu abaixo de ' + pct0(m.limpe_min_chance) +
              ' (ou passa do maior ciclo já ganho, ' + days(m.max_won_cycle_days) + ').'
            : 'Estes deals estão abertos há mais tempo do que qualquer deal já ganho (' + days(m.limpe_after_days) + ').') +
          ' Ordem: maior valor de tabela.';
      default:
        return '<strong>Marque a primeira conversa ou descarte:</strong> estes deals ainda estão em Prospecting, sem data de engajamento, então não há score. Ordem: maior valor de tabela.';
    }
  }

  function emptyInfo(snap, cat, list, st) {
    var sc = scopeOf(true);
    var a = sc.agent ? agentsByName[sc.agent] : null;
    var self = isVend();
    if (cat === 'Qualifique' && isTest(snap)) {
      return { kind: 'qualifique-indisponivel',
        html: '<p><strong>Indisponível no modo teste:</strong> o CRM não registra quando o deal entrou em Prospecting.</p>' };
    }
    if (a && !a.has_deals) {
      return { kind: 'sem-deals',
        html: self
          ? '<p><strong>Você não tem deals no CRM.</strong></p><p>É um cadastro sem pipeline: não há nada para priorizar. Se isso estiver errado, confira com ' + esc(a.manager) + '.</p>'
          : '<p><strong>' + esc(a.name) + ' não tem deals no CRM.</strong></p>' +
            '<p>É um cadastro sem pipeline: não há nada para priorizar. Se isso estiver errado, confira com ' + esc(a.manager) + '.</p>' };
    }
    if (!list.length) {
      var when = isTest(snap) ? 'em ' + dateBR(snap.date) : 'agora';
      if (self) {
        return { kind: 'sem-deals-nesta-data',
          html: '<p><strong>Você não tem deals abertos ' + when + '.</strong></p>' +
            '<p>' + (isTest(snap) ? 'Nesta data você ainda não tinha deals abertos, ou todos já estavam fechados.'
                                  : 'Os seus deals já estão fechados. Quando um deal novo entrar no CRM, ele aparece aqui.') + '</p>' };
      }
      return { kind: 'sem-deals-nesta-data',
        html: '<p><strong>' + (a ? esc(a.name) + ' não tem' : 'Não há') + ' deals abertos ' + when + ' nesta seleção.</strong></p>' +
          '<p>' + (a ? (isTest(snap) ? 'Nesta data o vendedor ainda não tinha deals abertos, ou todos já estavam fechados.'
                                     : 'Os deals deste vendedor já estão fechados.')
                     : 'Mude os filtros ou clique em Limpar.') + '</p>' };
    }
    // a lista aberta está vazia, mas outra tem deals: leva a pessoa até ela
    var next = null;
    CATS.forEach(function (c) { if (!next && c !== cat && st[c].n && !(isTest(snap) && c === 'Qualifique')) { next = c; } });
    var html = '<p><strong>' + (self ? 'Você não tem' : 'Não há') + ' deals em ' + cat + ' nesta seleção.</strong></p>';
    if (next) {
      html += '<p>' + (self ? 'Comece pela lista ' : 'A lista com deals é ') + next + ': ' + num(st[next].n) + ' ' + plural(st[next].n, 'deal', 'deals') + '.</p>' +
        '<button type="button" class="btn" data-goto="' + next + '" data-testid="goto-next">Ir para ' + next + '</button>';
    } else { html += '<p>Veja as outras abas.</p>'; }
    return { kind: 'lista-vazia', html: html };
  }
  emptyEl.addEventListener('click', function (e) {
    var b = e.target.closest('[data-goto]');
    if (!b) { return; }
    state.aba = b.getAttribute('data-goto');
    commit();
    tabRefs[activeCat].btn.focus();
  });

  function dueText(d) {
    if (d.cat === 'Foque' && d.days_to_knot != null) {
      return d.days_to_knot === 0 ? 'último dia no Foque' : 'sai do Foque em ' + days(d.days_to_knot);
    }
    if (d.cat === 'Reative' && d.days_to_limpe != null) {
      return d.days_to_limpe === 0 ? 'último dia antes de virar Limpe' : 'vira Limpe em ' + days(d.days_to_limpe);
    }
    return '';
  }

  function outcomeHtml(o) {
    var t;
    if (o.status === 'Ganho') {
      t = '<strong>Ganho</strong> em ' + dateBR(o.close_date) + (o.close_value != null ? ' · ' + usd(o.close_value) : '');
    } else if (o.status === 'Perdido') {
      t = '<strong>Perdido</strong>' + (o.close_date ? ' em ' + dateBR(o.close_date) : '');
    } else {
      t = '<strong>Ainda aberto</strong> em ' + dateBR(D.meta.reference_date);
    }
    return '<p class="outcome" data-testid="outcome-badge" data-status="' + esc(o.status) + '">' + t + '</p>';
  }

  // Ações só para o próprio vendedor, na foto de hoje. O manager lê; o modo teste é história.
  function canAct(snap) { return isVend() && !isTest(snap); }

  function marksText(agent, d) {
    var m = marksOf(agent, d.id);
    if (!m.length) { return ''; }
    return 'Marcado: ' + joinPt(ACTS.filter(function (a) { return m.indexOf(a.key) >= 0; }).map(function (a) { return a.done; })) + '.';
  }
  function simText(d) {
    if (!sim[d.id]) { return ''; }
    return 'Simulação: se este deal fechar, entram ' + usd(d.price) + ' de tabela no lugar de ' + usd(d.ev || 0) + ' esperados (' + usd(d.price - (d.ev || 0)) + ' a mais).';
  }

  function cardHtml(d, snap) {
    var id = esc(d.id);
    var acct = d.account ? '<span class="acct">' + esc(d.account) + '</span>'
                         : '<span class="acct no-acct">Conta não informada</span>';
    var score = d.score == null ? '<span class="score none">Sem score</span>'
                                : '<span class="score">Score ' + d.score + '</span>';
    var l2 = score + '<span class="price">' + usd(d.price) + '</span>';
    if (d.p != null) {
      l2 += '<span class="chance" title="Chance de ganho nos próximos ' + days(HORIZON) + '">chance ' +
        (d.p > 0 && d.p < 0.005 ? '&lt;' + pct0(0.01) : pct0(d.p)) + '</span>';
    }
    var meta = [];                                   // 3ª linha: idade e prazo (quebra como texto corrido)
    if (d.age != null) { meta.push('há ' + days(d.age)); }
    var due = dueText(d);
    if (due) { meta.push('<span class="due">' + due + '</span>'); }
    var why = (d.why && d.why.length) ? d.why : [''];
    var whyHtml = why.map(function (s, i) {
      return '<p' + (i ? ' class="why-more" hidden' : '') + '>' + esc(s) + '</p>';
    }).join('');
    var rows = [
      ['Vendedor', d.agent], ['Manager', d.manager], ['Região', d.region],
      ['Engajado em', d.engage_date ? dateBR(d.engage_date) : 'sem data de engajamento'],
      ['Valor esperado', d.ev != null ? usd(d.ev) : 'sem estimativa (Prospecting)'],
      ['ID', d.id]
    ].map(function (r) { return '<dt>' + r[0] + '</dt><dd>' + esc(r[1]) + '</dd>'; }).join('');

    var act = '';
    if (canAct(snap)) {
      var agent = d.agent;
      act = '<p class="card-marks" data-testid="card-marks"' + (marksOf(agent, d.id).length ? '' : ' hidden') + '>' + esc(marksText(agent, d)) + '</p>';
      var canSim = d.cat === 'Foque' || d.cat === 'Reative';
      if (canSim) { act += '<p class="card-sim" data-testid="card-sim"' + (sim[d.id] ? '' : ' hidden') + '>' + esc(simText(d)) + '</p>'; }
      act += '<div class="card-actions" data-testid="card-actions">' + ACTS.map(function (a) {
        var on = hasMark(agent, d.id, a.key);
        return '<button type="button" class="act" data-act="' + a.key + '" data-testid="act-' + a.key + '" aria-pressed="' + (on ? 'true' : 'false') + '">' +
          icon('check', 'act-check') + '<span>' + a.label + '</span></button>';
      }).join('') + (canSim
        ? '<button type="button" class="act act-sim" data-sim="" data-testid="act-sim" aria-pressed="' + (sim[d.id] ? 'true' : 'false') + '">' +
          icon('check', 'act-check') + '<span>E se eu fechar este?</span></button>' : '') + '</div>';
    }
    var treated = canAct(snap) && marksOf(d.agent, d.id).length > 0;

    return '<article class="card cat-' + esc(d.cat) + (treated ? ' is-treated' : '') + '" data-testid="deal-card" data-id="' + id + '">' +
      '<button type="button" class="card-toggle" aria-expanded="false" aria-controls="det-' + id + '">' +
        '<span class="l1"><span class="chip-cat">' + icon(d.cat) + esc(d.cat) + '</span>' + acct + '<span class="prod">' + esc(d.product) + '</span></span>' +
        '<span class="l2">' + l2 + '</span>' +
        (meta.length ? '<span class="meta">' + meta.join(' · ') + '</span>' : '') +
      '</button>' +
      '<div class="card-why" data-testid="card-why" data-n="' + why.length + '">' + whyHtml + '</div>' +
      act +
      (d.outcome ? outcomeHtml(d.outcome) : '') +
      '<div class="card-detail" id="det-' + id + '" hidden><dl>' + rows + '</dl></div>' +
      '</article>';
  }

  function updateMore() {
    var all = shown >= items.length;
    moreWrap.hidden = items.length <= PAGE_SIZE;
    shownEl.textContent = 'Mostrando ' + num(shown) + ' de ' + num(items.length);
    moreBtn.hidden = all;
    moreBtn.textContent = 'Mostrar mais ' + num(Math.min(PAGE_SIZE, items.length - shown));
  }
  function appendCards() {
    var end = Math.min(items.length, shown + PAGE_SIZE), html = '', i;
    for (i = shown; i < end; i += 1) { html += cardHtml(items[i], cur.snap); }
    var first = shown;
    cardsEl.insertAdjacentHTML('beforeend', html);
    shown = end;
    updateMore();
    return cardsEl.children[first];
  }
  moreBtn.addEventListener('click', function () {
    var firstNew = appendCards();
    var b = firstNew && firstNew.querySelector('.card-toggle');
    if (b) { b.focus({ preventScroll: true }); }
  });

  function toggleCard(card) {
    var btn = card.querySelector('.card-toggle');
    var open = btn.getAttribute('aria-expanded') !== 'true';
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    card.querySelector('.card-detail').hidden = !open;
    var extra = card.querySelectorAll('.why-more');
    for (var i = 0; i < extra.length; i += 1) { extra[i].hidden = !open; }
  }
  // Atualiza só o card tocado (sem refazer a lista): mantém o card aberto, o foco e a rolagem.
  function refreshCard(card, d) {
    var agent = d.agent, any = marksOf(agent, d.id).length > 0;
    card.classList.toggle('is-treated', any);
    var marks = card.querySelector('.card-marks');
    if (marks) { marks.textContent = marksText(agent, d); marks.hidden = !any; }
    var note = card.querySelector('.card-sim');
    if (note) { note.textContent = simText(d); note.hidden = !sim[d.id]; }
    ACTS.forEach(function (a) {
      var b = card.querySelector('[data-act=' + a.key + ']');
      if (b) { b.setAttribute('aria-pressed', hasMark(agent, d.id, a.key) ? 'true' : 'false'); }
    });
    var sb = card.querySelector('[data-sim]');
    if (sb) { sb.setAttribute('aria-pressed', sim[d.id] ? 'true' : 'false'); }
  }
  cardsEl.addEventListener('click', function (e) {
    var card = e.target.closest('.card');
    if (!card) { return; }
    var d = dealById[card.getAttribute('data-id')];
    var actBtn = e.target.closest('[data-act]');
    if (actBtn && d) {
      var key = actBtn.getAttribute('data-act');
      var on = toggleMark(d.agent, d.id, key);
      var lab = ACTS.filter(function (a) { return a.key === key; })[0];
      refreshCard(card, d);
      renderStats();
      announce(on ? 'Deal de ' + (d.account || 'conta não informada') + ' marcado como ' + lab.done + '. Salvo só neste navegador.'
                  : 'Marcação “' + lab.label + '” removida.');
      return;
    }
    if (e.target.closest('[data-sim]') && d) {
      if (sim[d.id]) { delete sim[d.id]; } else { sim[d.id] = true; }
      refreshCard(card, d);
      renderStats();
      announce(sim[d.id] ? 'Simulação ligada para este deal.' : 'Simulação desligada para este deal.');
      return;
    }
    if (e.target.closest('.card-detail') || e.target.closest('.card-actions') || e.target.closest('.card-sim') || e.target.closest('.card-marks')) { return; }
    var sel = window.getSelection && String(window.getSelection());
    if (sel && !e.target.closest('.card-toggle')) { return; }   // selecionando texto das frases: não recolhe
    toggleCard(card);
  });
  $('sim-clear').addEventListener('click', function () {
    sim = {};
    var cs = cardsEl.querySelectorAll('.card');
    for (var i = 0; i < cs.length; i += 1) {
      var d = dealById[cs[i].getAttribute('data-id')];
      if (d) { refreshCard(cs[i], d); }
    }
    renderStats();
    announce('Simulação limpa.');
  });

  function renderPanel(snap, groups, list, st) {
    var cat = activeCat;
    panelEl.className = 'panel cat-' + cat;
    panelEl.setAttribute('aria-labelledby', 'tab-' + cat);
    $('instruction').innerHTML = instruction(cat, snap.model);
    // sem nenhum deal na seleção (ou lista indisponível), só o aviso explicativo: a instrução e as abas seriam ruído
    $('instruction').hidden = !list.length || (isTest(snap) && cat === 'Qualifique');
    tabsEl.hidden = !list.length;
    items = groups[cat] || [];
    dealById = {};
    list.forEach(function (d) { dealById[d.id] = d; });
    shown = 0;
    cardsEl.innerHTML = '';
    var unavailable = isTest(snap) && cat === 'Qualifique';
    var sc = scopeOf(true);
    var agent = sc.agent ? agentsByName[sc.agent] : null;
    var showEmpty = unavailable || !items.length || (agent && !agent.has_deals);
    if (showEmpty) {
      var info = emptyInfo(snap, cat, list, st);
      emptyEl.innerHTML = info.html;
      emptyEl.setAttribute('data-kind', info.kind);
      emptyEl.hidden = false;
      moreWrap.hidden = true;
      if (unavailable) { items = []; }
      return;
    }
    emptyEl.hidden = true;
    emptyEl.innerHTML = '';
    emptyEl.removeAttribute('data-kind');
    appendCards();
  }

  /* ------------------------------------------------------------------ como funciona / teste no passado */
  function renderHow(snap) {
    $('how-list').innerHTML = (snap.how_it_works || []).map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('');
  }

  function fmtMetric(kind, v) {
    if (v == null) { return '—'; }
    return kind === 'dec' ? dec2(v) : pct1(v);
  }
  function renderBacktest(snap) {
    var b = D.backtest, box = $('backtest');
    if (!b || !b.rows || !b.rows.length || !b.metrics || !b.metrics.length) { box.hidden = true; return; }
    box.hidden = false;
    var cuts = [], byCut = {}, methods = [], mlabel = {};
    b.rows.forEach(function (r) {
      if (!byCut[r.cut]) { byCut[r.cut] = { label: r.cut_label, vals: {} }; cuts.push(r.cut); }
      byCut[r.cut].vals[r.method] = r;
      if (methods.indexOf(r.method) < 0) { methods.push(r.method); mlabel[r.method] = r.method_label; }
    });
    var hasActive = cuts.indexOf(snap.date) >= 0;
    var html = '<div class="box-body">';
    if (b.headline) { html += '<p class="bt-line head" data-testid="backtest-headline">' + esc(b.headline) + '</p>'; }
    if (b.criterion_text) { html += '<p class="bt-line">' + esc(b.criterion_text) + '</p>'; }
    html += '<p class="bt-line muted">Como ler: em cada data de corte, ordenamos os deals que estavam abertos por cada método e vemos quanto do que foi ganho depois caiu no topo da lista. Maior é melhor; o número em negrito é o melhor de cada linha.' +
      (hasActive ? ' A linha destacada é a data da foto que você está vendo.' : '') + '</p>';
    b.metrics.forEach(function (mt) {
      html += '<div class="table-wrap"><table class="bt-table" data-metric="' + esc(mt.key) + '"><caption>' + esc(mt.label) +
        '</caption><thead><tr><th>Corte</th>' + methods.map(function (m) { return '<th>' + esc(mlabel[m]) + '</th>'; }).join('') +
        '</tr></thead><tbody>';
      cuts.forEach(function (c) {
        var vals = methods.map(function (m) { var r = byCut[c].vals[m]; return r ? r[mt.key] : null; });
        var best = Math.max.apply(null, vals.filter(function (v) { return v != null; }));
        html += '<tr' + (c === snap.date ? ' class="is-active"' : '') + ' data-cut="' + esc(c) + '"><th scope="row">' + esc(byCut[c].label) + '</th>' +
          vals.map(function (v) {
            return '<td' + (v != null && v === best ? ' class="best"' : '') + '>' + fmtMetric(mt.kind, v) + '</td>';
          }).join('') + '</tr>';
      });
      html += '</tbody></table></div>';
    });
    if (b.notes && b.notes.length) {
      html += '<ul class="bt-notes">' + b.notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>';
    }
    $('backtest-body').innerHTML = html + '</div>';
  }

  /* ------------------------------------------------------------------ rodapé */
  $('foot').innerHTML = 'Dados de ' + dateBR(D.meta.reference_date) + ' · gerado por <code>' + esc(D.meta.generated_by) + '</code>';

  /* ------------------------------------------------------------------ orquestração */
  var lastHowKey = null;
  var pendingFocus = '';
  // Aba escolhida pela pessoa; se ela ainda não escolheu, abre a 1ª lista que tem deals
  // (um vendedor sem nada em Foque não deve cair numa tela vazia).
  function pickCat(snap, st) {
    if (state.aba) { return state.aba; }
    if (noLiveDeals(snap, st)) { return 'Qualifique'; }
    for (var i = 0; i < CATS.length; i += 1) {
      if (isTest(snap) && CATS[i] === 'Qualifique') { continue; }
      if (st[CATS[i]].n) { return CATS[i]; }
    }
    return CATS[0];
  }
  function applyFocus() {
    var id = pendingFocus; pendingFocus = '';
    if (pendingSortFocus) {
      var s = document.querySelector('[data-sort=' + pendingSortFocus + ']');
      pendingSortFocus = '';
      if (s) { s.focus({ preventScroll: true }); }
      return;
    }
    var el = id ? $(id) : null;
    if (el && !el.hidden) { el.focus(); }
  }
  function render() {
    var snap = currentSnap();
    var entry = !state.perfil;
    $('entry').hidden = !entry;
    $('session').hidden = entry;
    $('bar-mode').hidden = entry;
    modeSel.value = snap.date;
    if (lastHowKey !== snap.date) { renderHow(snap); renderBacktest(snap); lastHowKey = snap.date; }
    if (entry) {
      $('test-banner').hidden = true;
      renderEntry();
      applyFocus();
      return;
    }
    var list = filterDeals(snap, scopeOf(true));
    var groups = groupByCat(list);
    var st = statsOf(groups);
    // o manager vê o time inteiro no resumo e no mapa; a carteira de um vendedor abre abaixo
    var teamList = isMgr() ? filterDeals(snap, scopeOf(false)) : list;
    var teamGroups = isMgr() ? groupByCat(teamList) : groups;
    var teamSt = isMgr() ? statsOf(teamGroups) : st;
    var walletOn = !isMgr() || !!state.ver;
    activeCat = pickCat(snap, st);
    cur = { snap: snap, groups: groups, st: st, list: list };

    renderIdentity();
    renderControls(snap);
    renderBanner(snap);
    renderAction(snap, teamSt, teamList.length);
    renderStats();
    renderResults(snap, teamGroups);
    renderTeamMap(snap, teamList);
    $('wallet').hidden = !walletOn;
    renderWalletHead(snap);
    renderPauta(snap);
    if (walletOn) {
      renderTabs(snap, st);
      renderTeam(snap, list);
      renderPanel(snap, groups, list, st);
    } else {
      teamEl.innerHTML = ''; lastTeamKey = null;
    }
    applyFocus();
  }
  function commit() { normalize(state); writeHash(); render(); }

  /* ------------------------------------------------------------------ eventos */
  modeSel.addEventListener('change', function () {
    state.modo = modeSel.value === todaySnap.date ? '' : modeSel.value;
    sim = {};
    commit();
  });
  agentSel.addEventListener('change', function () { state.vendedor = agentSel.value; commit(); });
  managerSel.addEventListener('change', function () { state.manager = managerSel.value; commit(); });
  regionSel.addEventListener('change', function () { state.regiao = regionSel.value; commit(); });
  $('filter-clear').addEventListener('click', function () {
    state.vendedor = ''; state.manager = ''; state.regiao = '';
    commit();
  });
  $('test-banner').addEventListener('click', function (e) {
    if (e.target.closest('#back-today')) { state.modo = ''; sim = {}; commit(); modeSel.focus(); }
  });
  $('how-btn').addEventListener('click', function () {
    var d = $('how');
    d.open = true;
    d.scrollIntoView();
    d.querySelector('summary').focus({ preventScroll: true });
  });
  window.addEventListener('hashchange', function () {
    var s = parseHash();
    if (serialize(s) === lastHash) { return; }
    state = s;
    lastHash = serialize(state);
    render();
  });

  state = parseHash();
  lastHash = serialize(state);
  try {
    render();
  } catch (err) {
    console.error(err);
    $('action-summary').textContent = 'Não foi possível montar a página. Rode python -m scorer.build de novo.';
    $('session').hidden = false;
    throw err;
  }
})();
