// Pipeline por fase (prancha 05): cinco colunas do CRM. Deal aberto pode ser arrastado para outra fase;
// o movimento fica salvo só neste navegador e não muda o score nem as outras telas.
import { STALE_DECISIONS, getDecision, getMoves, setDecision, setMove } from '../core/marks.js';
import { prefs } from '../core/state.js';

const FIRST_BATCH = 3;
const NEXT_BATCH = 20;
const FILTERS = ['todos', 'com', 'sem'];
const FILTERED_COLUMNS = ['engaging', 'stale'];
// Só deal aberto sai do lugar. "Sem desfecho" é calculada pela idade, então não recebe cartão de fora.
const DRAGGABLE_FROM = ['prospecting', 'engaging', 'stale'];
const DROPPABLE = ['prospecting', 'engaging', 'won', 'lost'];

export default {
  id: 'pipeline',
  title: 'Pipeline',
  roles: ['seller', 'manager'],
  area: 'vendas',

  render(root, ctx) {
    const { dom, ui, fmt } = ctx;
    const { html } = dom;
    const isManager = ctx.user.role === 'manager';
    const savedFilter = prefs.get('pipeline:filtro');
    const view = { data: null, maxCycle: null, filter: FILTERS.includes(savedFilter) ? savedFilter : 'todos', shown: {}, dragging: null };

    const lead = 'As mesmas oportunidades do foco da semana, vistas pela fase do CRM.';
    dom.setHtml(root, html`<div class="pipe">
      <div class="pipe-head">
        ${ui.screenHeader({
          eyebrow: 'Pipeline',
          title: isManager ? `Pipeline de ${ctx.subject}` : 'Seu pipeline, fase por fase',
          subtitle: lead,
          aside: html`<div class="pipe-head__aside" data-pipe-filters></div>`,
        })}
      </div>
      ${ui.viewingBar(ctx, { what: 'o pipeline' })}
      <div class="pipe-body" data-pipe-body></div>
    </div>`);

    const body = dom.qs('[data-pipe-body]', root);
    const filtersSlot = dom.qs('[data-pipe-filters]', root);
    const subtitle = dom.qs('.screen-sub', root);

    /* Textos de apoio */

    // O limite de idade de Sem desfecho é o max_cycle do modelo (número cru), o mesmo do Foco.
    const staleDays = () => (Number.isFinite(view.maxCycle) ? fmt.number(view.maxCycle) : null);

    const visibleDeals = (column) => {
      if (!FILTERED_COLUMNS.includes(column.key) || view.filter === 'todos') return column.deals;
      return column.deals.filter((deal) => (view.filter === 'com' ? Boolean(deal.account) : !deal.account));
    };

    // Colunas como a pessoa deixou: as do CRM mais os cartões arrastados (que entram no topo do destino).
    const boardColumns = () => {
      const moves = getMoves(ctx.store);
      const origin = new Map();
      view.data.columns.forEach((column) => column.deals.forEach((deal) => origin.set(deal.id, column)));
      const target = (deal, column) => {
        const to = moves[deal.id];
        const valid = to && to !== column.key && DRAGGABLE_FROM.includes(column.key) && DROPPABLE.includes(to);
        return valid ? to : column.key;
      };
      return view.data.columns.map((column) => {
        const stayed = column.deals.filter((deal) => target(deal, column) === column.key);
        const arrived = [];
        view.data.columns.forEach((other) => {
          if (other.key === column.key) return;
          other.deals.forEach((deal) => {
            if (target(deal, other) === column.key) arrived.push({ ...deal, moved_from: other });
          });
        });
        const left = column.deals.length - stayed.length;
        return {
          ...column,
          deals: [...arrived, ...stayed.map((deal) => ({ ...deal, origin: column.key }))].map((deal) => ({
            ...deal,
            origin: deal.moved_from ? deal.moved_from.key : column.key,
          })),
          count: column.count - left + arrived.length,
          moved: left + arrived.length > 0,
        };
      });
    };

    const priceLine = (deal) => [deal.account, `#${deal.id}`, fmt.money(deal.price)].filter(Boolean).join(' · ');

    /* Cartões */

    const engagingCard = (deal) => html`<a class="pipe-card pipe-card--link" draggable="false" href="${ctx.href('foco', {
      deal: deal.id,
      vendedor: isManager ? ctx.subject : undefined,
    })}">
      <span class="pipe-card__top"><span class="pipe-card__title">${deal.product}</span>${
        Number.isFinite(deal.score) ? html`<span class="pipe-card__score"><span class="sr-only">Score </span>${deal.score}</span>` : ''
      }</span>
      <span class="pipe-card__meta">${priceLine(deal)}</span>
      <span class="pipe-card__fact">${fmt.plural(deal.age_days, 'dia')} · ${fmt.percent(deal.chance)} em 30 dias</span>
    </a>`;

    const staleCard = (deal) => html`<div class="pipe-card">
        <p class="pipe-card__title">${deal.product}</p>
        <p class="pipe-card__meta">${priceLine(deal)}</p>
        <p class="pipe-card__fact">${fmt.plural(deal.age_days, 'dia')} · desde ${deal.engage_label}</p>
        <div class="pipe-card__actions">${ui.decisionButtons(deal, getDecision(ctx.store, deal.id), { short: true })}</div>
      </div>`;

    const closedCard = (deal) => html`<div class="pipe-card">
      <p class="pipe-card__title">${deal.product}</p>
      <p class="pipe-card__meta">${[deal.account, `#${deal.id}`].filter(Boolean).join(' · ')}</p>
      <p class="pipe-card__fact">${
        deal.won
          ? `${fmt.money(deal.close_value)} · fechado em ${deal.close_label}`
          : `Perdido em ${deal.close_label} · ${fmt.plural(deal.cycle_days, 'dia')}`
      }</p>
    </div>`;

    const prospectCard = (deal) => html`<div class="pipe-card">
      <p class="pipe-card__title">${deal.product}</p>
      <p class="pipe-card__meta">${priceLine(deal)}</p>
    </div>`;

    const CARD = { prospecting: prospectCard, engaging: engagingCard, stale: staleCard, won: closedCard, lost: closedCard };

    // O cartão mantém o desenho da fase de origem; o que foi arrastado ganha a faixa "Veio de…" com Desfazer.
    const cardItem = (deal) => {
      const canDrag = DRAGGABLE_FROM.includes(deal.origin);
      return html`<li class="pipe-item${canDrag ? ' is-draggable' : ''}"${ui.attrs({
        draggable: canDrag ? 'true' : null,
        'data-deal-id': canDrag ? deal.id : null,
        'data-origin': canDrag ? deal.origin : null,
      })}>
        ${CARD[deal.origin](deal)}
        ${deal.moved_from ? html`<p class="pipe-moved"><span>Veio de ${deal.moved_from.title}</span><button type="button" class="pipe-moved__undo" data-unmove="${deal.id}">Desfazer<span class="sr-only"> o movimento do deal #${deal.id}</span></button></p>` : ''}
      </li>`;
    };

    /* Colunas */

    const emptyText = (column) => {
      if (column.note) return column.note;
      const filtered = FILTERED_COLUMNS.includes(column.key) && view.filter !== 'todos' && column.count > 0;
      if (filtered) return view.filter === 'com' ? 'Nenhum deal com cliente nesta fase.' : 'Nenhum deal sem cliente nesta fase.';
      const date = view.data.date.label;
      if (column.key === 'won') return `Nenhum deal ganho nos 30 dias anteriores a ${date}.`;
      if (column.key === 'lost') return `Nenhum deal perdido nos 30 dias anteriores a ${date}.`;
      if (column.key === 'stale') {
        const days = staleDays();
        return days ? `Nenhum deal aberto passou de ${days} dias.` : 'Nenhum deal aberto passou do limite de idade.';
      }
      return 'Nenhum deal aberto nesta fase.';
    };

    const columnHtml = (column) => {
      const deals = visibleDeals(column);
      const shown = Math.min(deals.length, view.shown[column.key] || FIRST_BATCH);
      const rest = deals.length - shown;
      const filtered = FILTERED_COLUMNS.includes(column.key) && view.filter !== 'todos';
      const headId = `pipe-col-${column.key}`;
      const note = column.note && deals.length > 0 ? html`<p class="pipe-col__note">${column.note}</p>` : '';
      return html`<section class="pipe-col${column.key === 'stale' ? ' pipe-col--stale' : ''}" data-col="${column.key}" aria-labelledby="${headId}">
        <header class="pipe-col__head">
          <div class="pipe-col__row">
            <h2 class="pipe-col__title" id="${headId}" tabindex="-1">${column.title}</h2>
            <span class="pipe-col__count">${
              filtered ? html`${deals.length}<span class="pipe-col__of"> de ${column.count}</span>` : column.count
            }<span class="sr-only"> ${fmt.pluralWord(column.count, 'deal')}</span></span>
          </div>
          ${column.hint ? html`<p class="pipe-col__hint">${column.hint}</p>` : ''}
        </header>
        ${note}
        ${
          deals.length === 0
            ? html`<div class="pipe-empty"><p class="pipe-empty__title">Nenhum deal nesta fase</p><p class="pipe-empty__text">${emptyText(column)}</p></div>`
            : html`<ul class="pipe-col__list" role="list">${deals.slice(0, shown).map(cardItem)}</ul>`
        }
        ${rest > 0 ? html`<button type="button" class="pipe-more" data-more="${column.key}">Mais ${fmt.plural(rest, 'deal')}</button>` : ''}
      </section>`;
    };

    const drawFilters = () => {
      const { counts } = view.data;
      dom.setHtml(filtersSlot, ui.chips(
        [
          { value: 'todos', label: 'Todos', count: counts.all },
          { value: 'com', label: 'Com cliente', count: counts.with_account },
          { value: 'sem', label: 'Sem cliente', count: counts.without_account },
        ],
        { value: view.filter, label: 'Filtrar deals abertos pelo cliente' },
      ));
    };

    const drawColumns = () => {
      const columns = boardColumns();
      dom.setHtml(body, html`<div class="pipe-board" role="region" tabindex="0" aria-label="Colunas do pipeline">
          ${columns.map(columnHtml)}
        </div>
        <p class="pipe-foot">As fases vêm do CRM. Você pode arrastar um deal aberto para outra fase: o movimento fica salvo só neste navegador e não muda o CRM, o score nem as outras telas. Dentro de “Em negociação” os cartões seguem a ordem do score. Ganhos e perdidos são dos 30 dias anteriores a ${view.data.date.label}. O filtro de cliente (Todos, Com cliente, Sem cliente) vale para Em negociação e Sem desfecho e serve para navegar: nesta base, o cliente de deal aberto não é confiável. Segue e Encerrar ficam salvos só neste navegador.</p>`);
    };

    const redrawColumn = (key) => {
      const column = boardColumns().find((item) => item.key === key);
      const current = dom.qs(`[data-col="${CSS.escape(key)}"]`, body);
      if (!column || !current) return null;
      const next = dom.toFragment(columnHtml(column)).firstElementChild;
      current.replaceWith(next);
      return next;
    };

    const draw = ({ pipeline, maxCycle }) => {
      view.data = pipeline;
      view.maxCycle = maxCycle;
      const days = staleDays();
      subtitle.textContent = days ? `${lead} A coluna tracejada separa o que passou de ${days} dias.` : lead;
      drawFilters();
      drawColumns();
    };

    /* Ações */

    const offs = [
      dom.on(root, 'click', '[data-chip]', (event, chip) => {
        if (!view.data || chip.dataset.chip === view.filter) return;
        view.filter = chip.dataset.chip;
        prefs.set('pipeline:filtro', view.filter);
        FILTERED_COLUMNS.forEach((key) => delete view.shown[key]);
        drawFilters();
        FILTERED_COLUMNS.forEach(redrawColumn);
        dom.qs(`[data-chip="${view.filter}"]`, filtersSlot)?.focus();
      }),
      dom.on(root, 'click', '[data-more]', (event, button) => {
        const key = button.dataset.more;
        const before = view.shown[key] || FIRST_BATCH;
        view.shown[key] = before + NEXT_BATCH;
        const col = redrawColumn(key);
        if (!col) return;
        // O foco vai para o primeiro cartão novo (ou fica no título da coluna se ele não for focável).
        const firstNew = dom.qsa('.pipe-col__list > li', col)[before];
        const target = firstNew && dom.focusables(firstNew)[0];
        (target || dom.qs('[data-more]', col) || dom.qs('.pipe-col__title', col))?.focus();
      }),
      dom.on(root, 'click', '[data-decide]', (event, button) => {
        const { decide: value, dealId } = button.dataset;
        const undo = button.getAttribute('aria-pressed') === 'true';
        setDecision(ctx.store, dealId, undo ? null : value);
        // Redesenha só os botões deste cartão e devolve o foco ao que foi clicado.
        const group = button.closest('.decide-group');
        group.replaceWith(dom.toFragment(ui.decisionButtons({ id: dealId }, getDecision(ctx.store, dealId), { short: true })));
        dom.qs(`[data-key="${CSS.escape(`decide:${dealId}:${value}`)}"]`, body)?.focus();
        ui.toast(undo
          ? `Marcação do deal #${dealId} desfeita.`
          : `Deal #${dealId} marcado: ${STALE_DECISIONS[value].label}. Fica salvo só neste navegador.`);
      }),
    ];

    /* Arrastar e soltar */

    const clearDrop = () => dom.qsa('.is-drop', body).forEach((el) => el.classList.remove('is-drop'));

    // Coluna em que o cartão arrastado pode cair (a de origem desfaz o movimento).
    const dropTarget = (col) => {
      const drag = view.dragging;
      if (!drag || !col) return null;
      const key = col.dataset.col;
      if (key === drag.current) return null;
      return key === drag.origin || DROPPABLE.includes(key) ? key : null;
    };

    const moveDeal = (dealId, origin, from, to) => {
      setMove(ctx.store, dealId, to === origin ? null : to);
      delete view.shown[to];
      [from, to].forEach(redrawColumn);
      const title = view.data.columns.find((item) => item.key === to)?.title || to;
      ui.toast(to === origin
        ? `Deal #${dealId} voltou para ${title}.`
        : `Deal #${dealId} movido para ${title}. Fica salvo só neste navegador; o CRM não muda.`);
    };

    offs.push(
      dom.on(root, 'dragstart', '[data-deal-id]', (event, item) => {
        view.dragging = { id: item.dataset.dealId, origin: item.dataset.origin, current: item.closest('[data-col]').dataset.col };
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', `#${item.dataset.dealId}`);
        item.classList.add('is-dragging');
        dom.qs('.pipe-board', body)?.classList.add('is-sorting');
      }),
      dom.on(root, 'dragend', '[data-deal-id]', (event, item) => {
        view.dragging = null;
        item.classList.remove('is-dragging');
        dom.qs('.pipe-board', body)?.classList.remove('is-sorting');
        clearDrop();
      }),
      dom.on(root, 'dragover', '[data-col]', (event, col) => {
        if (!dropTarget(col)) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
        if (!col.classList.contains('is-drop')) {
          clearDrop();
          col.classList.add('is-drop');
        }
      }),
      dom.on(root, 'dragleave', '[data-col]', (event, col) => {
        if (!col.contains(event.relatedTarget)) col.classList.remove('is-drop');
      }),
      dom.on(root, 'drop', '[data-col]', (event, col) => {
        const to = dropTarget(col);
        if (!to) return;
        event.preventDefault();
        const { id, origin, current } = view.dragging;
        view.dragging = null;
        dom.qs('.pipe-board', body)?.classList.remove('is-sorting');
        clearDrop();
        moveDeal(id, origin, current, to);
      }),
      dom.on(root, 'click', '[data-unmove]', (event, button) => {
        const item = button.closest('[data-deal-id]');
        const from = button.closest('[data-col]').dataset.col;
        moveDeal(button.dataset.unmove, item.dataset.origin, from, item.dataset.origin);
        dom.qs(`[data-col="${CSS.escape(item.dataset.origin)}"] .pipe-col__title`, body)?.focus();
      }),
    );

    const fetchAll = async () => {
      const [pipeline, model] = await Promise.all([
        ctx.api.get('pipeline', { name: ctx.subject, date: ctx.date }),
        ctx.api.get('score-model', { date: ctx.date }),
      ]);
      return { pipeline, maxCycle: model.max_cycle };
    };

    ui.load(body, fetchAll, draw, {
      skeleton: { title: false, lines: 1, blocks: 3 },
      errorTitle: 'Não foi possível carregar o pipeline.',
    });

    return () => offs.forEach((off) => off());
  },
};
