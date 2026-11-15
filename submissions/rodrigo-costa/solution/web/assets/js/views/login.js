// Tela 01 · Acesso simulado: escolher perfil e pessoa, sem senha.
const ROLE_ITEMS = [
  { value: 'seller', label: 'Vendedor', iconName: 'user' },
  { value: 'manager', label: 'Gestor', iconName: 'users' },
];
const DEFAULT_MANAGER = 'Rocco Neubert';

function layout({ html, ui, icon }, meta) {
  const { dataset } = meta;
  return html`<div class="login">
    <section class="login__side">
      <div class="login__brand">
        <span class="mark">${icon('trend', { size: 18, stroke: 2 })}</span>
        <span class="login__brand-name">Vendas</span>
        <span class="badge badge--concept login__badge">Conceito</span>
      </div>
      <div class="login__form">
        <div class="login__intro">
          ${ui.eyebrow('Acesso simulado')}
          <h1 class="screen-title" id="screen-title" tabindex="-1">Entre como alguém do time.</h1>
          <p class="screen-sub">Não há senha. Escolha um perfil e uma pessoa para ver o módulo com os olhos dela.</p>
        </div>
        <div class="login__body" data-body></div>
      </div>
      <p class="login__foot">Conceito criado para o AI Master Challenge. Não é um produto oficial do G4. Dados: ${dataset.name} (${dataset.license}), ${dataset.period_label}.</p>
    </section>
    <div class="login__panel-wrap">
      <section class="login__panel" aria-label="Resumo da base" data-panel></section>
    </div>
  </div>`;
}

function formHtml({ html, ui, icon }) {
  return html`<div class="login__field">
      <p class="login__label" id="login-perfil">Perfil</p>
      <div data-roles></div>
    </div>
    <div class="login__field">
      <div class="login__field-head">
        <label class="login__label" for="login-busca">Pessoa</label>
        <p class="login__count" data-count></p>
      </div>
      <div class="search">
        ${icon('search', { size: 16, stroke: 1.7 })}
        <input class="search__input" id="login-busca" type="search" autocomplete="off" spellcheck="false"
          placeholder="Buscar por nome, gestor ou regional" aria-controls="login-lista" aria-describedby="login-dica">
      </div>
      <div class="person-list" role="listbox" id="login-lista" aria-label="Pessoas" data-list></div>
      <p class="login__hint" id="login-dica" aria-live="polite" data-hint></p>
    </div>
    ${ui.button('Entrar', { variant: 'primary', size: 'lg', block: true, iconAfter: 'arrowRight', attrs: { 'data-enter': true } })}`;
}

// Enquanto /api/login não responde (ou se falhar), o painel escuro mostra um estado neutro, não um vazio.
function panelPlaceholder({ html }, { failed = false } = {}) {
  return html`<p class="login__panel-label">Resumo da base</p>
    <div class="login__panel-main">
      ${failed
        ? html`<p class="login__sentence">O resumo da base aparece aqui quando os dados carregarem. Use “Tentar de novo” ao lado.</p>`
        : html`<div class="login__panel-wait" aria-hidden="true"><span></span><span></span><span></span></div>`}
    </div>`;
}

function panelHtml({ html, ui }, panel) {
  return html`<p class="login__panel-label" id="login-panel-title">${panel.label}</p>
    <div class="login__panel-main">
      <p class="login__headline"><span class="login__headline-1">${panel.headline_1}</span> <span class="login__headline-2">${panel.headline_2}</span></p>
      ${ui.dualBar({ share: panel.live_share, variant: 'on-ink', label: `${panel.headline_2} ${panel.headline_1}` })}
      <p class="login__sentence">${panel.sentence}</p>
    </div>
    <ul class="login__stats">${panel.stats.map(
      (stat) => html`<li class="login__stat"><span class="login__stat-value">${stat.value}</span> <span class="login__stat-label">${stat.label}</span></li>`,
    )}</ul>`;
}

export default {
  id: 'login',
  title: 'Entrar',
  roles: ['seller', 'manager'],
  area: 'login',

  render(root, ctx) {
    const { dom, ui, fmt, meta } = ctx;
    const { html, setHtml, on, qsa } = dom;
    const kit = { html, ui, icon: ctx.icon };
    setHtml(root, layout(kit, meta));
    const body = root.querySelector('[data-body]');
    const panelRoot = root.querySelector('[data-panel]');
    const offs = [];

    const start = (data) => {
      const sellerTag = new Map(data.suggestions.map((s) => [s.name, s.tag]));
      const view = {
        role: 'seller',
        query: '',
        current: null,
        selected: {
          seller: data.suggestions[0]?.name || data.sellers[0]?.name || null,
          manager: (data.managers.find((m) => m.name === DEFAULT_MANAGER) || data.managers[0])?.name || null,
        },
      };

      setHtml(panelRoot, panelHtml(kit, data.panel));
      panelRoot.removeAttribute('aria-label');
      panelRoot.setAttribute('aria-labelledby', 'login-panel-title');
      setHtml(body, formHtml(kit));
      const rolesEl = body.querySelector('[data-roles]');
      const list = body.querySelector('[data-list]');
      const hint = body.querySelector('[data-hint]');
      const count = body.querySelector('[data-count]');
      const input = body.querySelector('#login-busca');
      const enter = body.querySelector('[data-enter]');

      const people = () => {
        const q = fmt.normalize(view.query);
        if (view.role === 'manager') {
          const rows = data.managers.map((m) => ({ name: m.name, sub: m.descriptor, haystack: `${m.name} ${m.region_label}` }));
          return q ? rows.filter((r) => fmt.normalize(r.haystack).includes(q)) : rows;
        }
        if (!q) {
          return data.suggestions.map((s) => ({ name: s.name, sub: `${s.tag} · ${s.descriptor}` }));
        }
        return data.sellers
          .filter((s) => fmt.normalize(`${s.name} ${s.manager} ${s.region_label}`).includes(q))
          .map((s) => ({
            name: s.name,
            sub: [sellerTag.get(s.name), s.descriptor, `gestor ${s.manager}`].filter(Boolean).join(' · '),
          }));
      };

      const drawRoles = () => {
        setHtml(rolesEl, ui.segmented({ label: 'Perfil', items: ROLE_ITEMS, value: view.role, size: 'lg' }));
        rolesEl.firstElementChild.setAttribute('aria-labelledby', 'login-perfil');
      };

      const drawList = () => {
        const rows = people();
        // A escolha salva só vale enquanto aparece na lista filtrada; senão, vale a primeira linha.
        const saved = view.selected[view.role];
        const current = rows.some((r) => r.name === saved) ? saved : rows[0]?.name || null;
        view.current = current;

        count.textContent = view.role === 'manager'
          ? `${fmt.plural(data.managers.length, 'gestor', 'gestores')}, em ${fmt.plural(meta.dataset.regions, 'regional', 'regionais')}`
          : `${fmt.plural(data.sellers.length, 'vendedor com deals', 'vendedores com deals')}, em ${fmt.plural(meta.dataset.regions, 'regional', 'regionais')}`;

        setHtml(list, rows.length
          ? rows.map((row) => {
            const isOn = row.name === current;
            return html`<div class="person" role="option" data-name="${row.name}" aria-selected="${String(isOn)}" tabindex="${isOn ? 0 : -1}">
                <span class="person__mark" aria-hidden="true"></span>
                <span class="person__text"><span class="person__name">${row.name}</span><span class="person__sub">${row.sub}</span></span>
                <span class="person__check">${ctx.icon('check', { size: 16, stroke: 2.2 })}</span>
              </div>`;
          })
          : html`<p class="person-list__empty">Ninguém encontrado com “${view.query.trim()}”. Tente outro nome, gestor ou regional.</p>`);

        if (view.query.trim()) {
          hint.textContent = rows.length ? `${fmt.plural(rows.length, 'pessoa encontrada', 'pessoas encontradas')}.` : '';
        } else if (view.role === 'manager') {
          hint.textContent = 'O gestor vê o time inteiro e pode abrir a lista de foco de cada vendedor.';
        } else {
          const manager = data.managers.find((m) => m.name === DEFAULT_MANAGER) || data.managers[0];
          setHtml(hint, html`São ${fmt.number(data.suggestions.length)} sugestões entre os ${fmt.number(data.sellers.length)}. Para ver um time inteiro, troque o perfil para <strong>Gestor</strong>${
            manager ? html` e escolha ${manager.name}, da ${manager.region_label}` : ''
          }.`);
        }

        enter.disabled = !current;
        enter.querySelector('span').textContent = current ? `Entrar como ${current}` : 'Escolha uma pessoa';
      };

      const select = (option, focus) => {
        view.selected[view.role] = option.dataset.name;
        view.current = option.dataset.name;
        qsa('[role="option"]', list).forEach((el) => {
          const isOn = el === option;
          el.setAttribute('aria-selected', String(isOn));
          el.tabIndex = isOn ? 0 : -1;
        });
        if (focus) option.focus();
        enter.querySelector('span').textContent = `Entrar como ${option.dataset.name}`;
        enter.disabled = false;
      };

      const go = () => {
        const name = view.current;
        if (name && !enter.disabled) ctx.setUser({ role: view.role, name });
      };

      offs.push(ui.bindSegmented(rolesEl, (value) => {
        view.role = value;
        drawList();
      }));
      input.addEventListener('input', () => {
        view.query = input.value;
        drawList();
      });
      input.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowDown') {
          event.preventDefault();
          (list.querySelector('[aria-selected="true"]') || list.querySelector('[role="option"]'))?.focus();
        } else if (event.key === 'Enter') {
          event.preventDefault();
          go();
        }
      });
      on(list, 'click', '[role="option"]', (event, option) => select(option, false));
      on(list, 'dblclick', '[role="option"]', () => go());
      on(list, 'keydown', '[role="option"]', (event, option) => {
        const options = qsa('[role="option"]', list);
        const index = options.indexOf(option);
        const moves = { ArrowDown: index + 1, ArrowUp: index - 1, Home: 0, End: options.length - 1 };
        if (event.key in moves) {
          event.preventDefault();
          const next = options[Math.max(0, Math.min(options.length - 1, moves[event.key]))];
          select(next, true);
        } else if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          select(option, false);
          go();
        }
      });
      enter.addEventListener('click', go);

      drawRoles();
      drawList();
    };

    const fetchLogin = async () => {
      setHtml(panelRoot, panelPlaceholder(kit));
      try {
        return await ctx.api.get('login', { date: ctx.date });
      } catch (error) {
        if (error?.name !== 'AbortError') setHtml(panelRoot, panelPlaceholder(kit, { failed: true }));
        throw error;
      }
    };
    ui.load(body, fetchLogin, start, { skeleton: { title: false, lines: 2, blocks: 3 } });

    return () => offs.forEach((off) => off());
  },
};
