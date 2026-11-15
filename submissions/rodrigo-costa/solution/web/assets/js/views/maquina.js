// Máquina do tempo (prancha 04): volta a uma segunda-feira, compara as duas listas de 10 deals e revela
// o desfecho. Embaixo, a prova agregada de /api/proof, que não muda com a data.

const OUTCOME_KEY = 'maquina:desfecho';
// O link "?desfecho=revelado" vale até o primeiro clique no botão, mesmo que a tela seja redesenhada depois.
let outcomeLinkUsed = false;
const PHASE_BY_MONTH = { 0: 'abre o trimestre', 2: 'fecha o trimestre' };
const OUTCOME_TONE = { venda: 'win', perda: 'loss' };
const RULES = [
  { key: 'score', label: 'Pelo score', main: true },
  { key: 'value_no_stale', label: 'Por valor, sem os sem desfecho' },
  { key: 'value_only', label: 'Só por valor' },
];

// Quem tinha o foco antes de trocar a data (ponto da linha do tempo ou botão de semana); a tela redesenha
// inteira com a nova data e devolve o foco ao equivalente.
let focusAfterDate = null;

function monthGroups(dates) {
  const groups = [];
  dates.forEach((d) => {
    let group = groups[groups.length - 1];
    if (!group || group.month !== d.month_label) {
      group = { month: d.month_label, phase: PHASE_BY_MONTH[d.month_in_quarter] || '', closes: d.month_in_quarter === 2, dates: [] };
      groups.push(group);
    }
    group.dates.push(d);
  });
  return groups;
}

function closingMonths(dates) {
  return new Set(dates.filter((d) => d.month_in_quarter === 2).map((d) => d.month_label));
}

/* Linha do tempo */

function timelineHtml(ctx) {
  const { dom, ui, icon, meta } = ctx;
  const { html } = dom;
  const dates = meta.dates;
  const index = dates.findIndex((d) => d.iso === ctx.date);
  const prev = dates[index - 1];
  const next = dates[index + 1];
  const months = monthGroups(dates).map((group) => {
    const dots = group.dates.map((d) => {
      const position = dates.indexOf(d);
      const state = position === index ? 'is-current' : position < index ? 'is-past' : 'is-future';
      const current = position === index;
      return html`<button type="button" class="tm-dot ${state}" data-tm-date="${d.iso}"${ui.attrs({
        'aria-current': current ? 'date' : null,
        'aria-label': current ? `${d.label}, data simulada atual` : `Ir para ${d.label}`,
        title: d.label,
      })}><span class="tm-dot__mark"></span></button>`;
    });
    const label = group.phase
      ? html`<span>${group.month} ·</span> <span>${group.phase}</span>`
      : group.month;
    return html`<li class="tm-month${group.closes ? ' tm-month--closes' : ''}" style="flex-grow: ${group.dates.length}">
      <div class="tm-month__track">${dots}</div>
      <p class="tm-month__label">${label}</p>
    </li>`;
  });
  return html`<section class="tm-timeline" aria-label="Linha do tempo">
    <div class="tm-timeline__head">
      <p class="tm-timeline__now"><span class="eyebrow">Você está em</span> <strong class="tm-timeline__date">${ctx.dateInfo?.label_long || ctx.date}</strong></p>
      <div class="tm-timeline__nav">
        <button type="button" class="btn btn--secondary btn--sm" data-tm-step="prev"${ui.attrs({ disabled: !prev, 'aria-label': prev ? `Semana anterior: ${prev.label}` : null })}>${icon('arrowLeft', { size: 14, stroke: 2 })}<span>Semana anterior</span></button>
        <button type="button" class="btn btn--secondary btn--sm" data-tm-step="next"${ui.attrs({ disabled: !next, 'aria-label': next ? `Próxima semana: ${next.label}` : null })}><span>Próxima semana</span>${icon('arrowRight', { size: 14, stroke: 2 })}</button>
      </div>
    </div>
    <div class="tm-timeline__scroll">
      <ol class="tm-months">${months}</ol>
    </div>
  </section>`;
}

/* As duas listas */

function outcomeHtml(ctx, outcome) {
  const { dom, ui } = ctx;
  const { html } = dom;
  const when = outcome.date_label ? html`<span class="sr-only">, em ${outcome.date_label}</span>` : '';
  return html`<span class="tm-reveal"${ui.attrs({ title: outcome.date_label ? `Fechou em ${outcome.date_label}` : null })}>${ui.badge(outcome.label, {
    tone: OUTCOME_TONE[outcome.kind] || 'neutral',
  })}${when}</span><span class="tm-mask"><span aria-hidden="true">—</span><span class="sr-only">desfecho escondido</span></span>`;
}

function listHtml(ctx, list, { id, main }) {
  const { dom, fmt } = ctx;
  const { html } = dom;
  const rows = list.rows.length
    ? html`<ol class="tm-list__rows" aria-labelledby="${id}">${list.rows.map(
        (row) => html`<li class="tm-row">
          <span class="tm-row__rank">${row.rank}</span>
          <span class="tm-row__deal"><b>${row.product}</b> · #${row.id}</span>
          <span class="tm-row__age">${fmt.plural(row.age_days, 'dia')}</span>
          <span class="tm-row__outcome">${outcomeHtml(ctx, row.outcome)}</span>
        </li>`,
      )}</ol>`
    : html`<p class="tm-list__empty">Nenhum deal aberto nesta data.</p>`;
  return html`<div class="tm-list${main ? ' tm-list--main' : ''}">
    <div class="tm-list__head">
      <h3 class="tm-list__title" id="${id}">${list.title}</h3>
      <p class="tm-total${list.wins > 0 ? ' tm-total--win' : ''}"><span class="tm-reveal">${list.total_label}</span><span class="tm-mask"><span aria-hidden="true">—</span><span class="sr-only">total escondido</span></span></p>
    </div>
    ${rows}
  </div>`;
}

function compareHtml(ctx, data, revealed) {
  const { dom, ui, fmt } = ctx;
  const { html } = dom;
  const isManager = ctx.user.role === 'manager';
  const firstName = ctx.subjectInfo?.first_name || fmt.firstName(ctx.subject);
  const title = `Os 10 deals que cada lista teria indicado a ${isManager ? firstName : 'você'}`;
  const short = data.enough
    ? ''
    : ui.banner(isManager
      ? `${firstName} tem menos de 10 deals abertos nesta data; a lista é curta.`
      : 'Você tem menos de 10 deals abertos nesta data; a lista é curta.', { iconName: 'alert' });
  return html`<section class="tm-compare" data-outcome="${revealed ? 'revealed' : 'hidden'}" aria-labelledby="tm-compare-title">
    <div class="tm-compare__head">
      <div class="tm-compare__titles">
        <h2 class="section-title" id="tm-compare-title">${title}</h2>
        <p class="section-sub">${data.window?.sentence || ''}</p>
      </div>
      <div class="tm-compare__action">
        ${ui.button(revealed ? 'Esconder o desfecho' : 'Revelar o desfecho', { variant: 'primary', attrs: { 'data-tm-toggle': true } })}
        <p class="tm-compare__saved">Sua escolha fica salva só neste navegador.</p>
      </div>
    </div>
    ${short}
    <div class="tm-lists">
      ${listHtml(ctx, data.lists.score, { id: 'tm-list-score', main: true })}
      ${listHtml(ctx, data.lists.value_only, { id: 'tm-list-value' })}
    </div>
    <div class="tm-notes">
      ${data.fair ? html`<div class="tm-note tm-reveal"><h3 class="tm-note__title">${data.fair.title}</h3><p class="tm-note__body">${data.fair.sentence}</p></div>` : ''}
      ${data.hidden_account_note ? html`<div class="tm-note"><h3 class="tm-note__title">${data.hidden_account_note.title}</h3><p class="tm-note__body">${data.hidden_account_note.body}</p></div>` : ''}
    </div>
  </section>`;
}

/* Prova agregada */

// O número em destaque ("+42%") dentro da frase da API fica em negrito, como no estudo; o texto não muda.
function emphasizePercents(ctx, sentence) {
  const { html } = ctx.dom;
  return String(sentence || '')
    .split(/([+−-]\d+(?:,\d+)?%)/)
    .map((part, i) => (i % 2 ? html`<strong>${part}</strong>` : part));
}

// As vendas por data são médias (deals empatados dividem a vaga), por isso a casa decimal.
function pairText(ctx, item) {
  const { fmt } = ctx;
  return `${item.label}: ${fmt.number(item.score.wins, 1)} ${fmt.pluralWord(item.score.wins, 'venda')} pelo score e ${fmt.number(item.value_only.wins, 1)} só por valor, em ${fmt.plural(item.lists, 'lista')}.`;
}

function defaultReadout(ctx, proof) {
  const current = proof.per_date.find((item) => item.date === ctx.date);
  if (current) return `Data atual, ${pairText(ctx, current)}`;
  if (ctx.dateInfo && !ctx.dateInfo.in_proof) return `A prova cobre ${proof.period_label}; ${ctx.dateInfo.label} fica fora dela.`;
  return 'Passe o mouse ou o foco numa data para ver os números.';
}

function chartHtml(ctx, proof) {
  const { dom, fmt, meta } = ctx;
  const { html } = dom;
  const peak = proof.peak?.wins || Math.max(1, ...proof.per_date.map((item) => Math.max(item.score.wins, item.value_only.wins)));
  const height = (wins) => `${Math.max(0, Math.min(100, (wins / peak) * 100)).toFixed(1)}%`;
  const currentIndex = proof.per_date.findIndex((item) => item.date === ctx.date);
  const tabbable = currentIndex >= 0 ? currentIndex : 0;
  const closes = closingMonths(meta.dates);
  const axis = [];
  proof.per_date.forEach((item) => {
    const last = axis[axis.length - 1];
    if (last && last.month === item.month_label) last.count += 1;
    else axis.push({ month: item.month_label, count: 1 });
  });
  const caption = proof.peak
    ? `Vendas nos 10 primeiros, por data · barra mais alta: ${fmt.number(proof.peak.wins, 1)} em ${fmt.plural(proof.peak.lists, 'lista')}`
    : 'Vendas nos 10 primeiros, por data';
  return html`<div class="tm-chart">
    <div class="tm-chart__legend">
      <span class="tm-key tm-key--score">Pelo score</span>
      <span class="tm-key tm-key--value">Só por valor</span>
      <span class="tm-chart__caption">${caption}</span>
    </div>
    <p class="tm-chart__readout" data-tm-readout>${defaultReadout(ctx, proof)}</p>
    <div class="tm-chart__scroll">
      <div class="tm-bars" role="group" aria-label="Vendas nos 10 primeiros, por data. Setas mudam de data; Enter vai para a data.">
        ${proof.per_date.map(
          (item, i) => html`<button type="button" class="tm-pair${i === currentIndex ? ' is-current' : ''}" data-tm-pair="${i}" data-tm-date="${item.date}" tabindex="${i === tabbable ? 0 : -1}"${ctx.ui.attrs({
            'aria-label': `${pairText(ctx, item)} Ir para esta data.`,
            'aria-current': i === currentIndex ? 'date' : null,
          })}>
            <span class="tm-bar tm-bar--score" style="height: ${height(item.score.wins)}"></span>
            <span class="tm-bar tm-bar--value" style="height: ${height(item.value_only.wins)}"></span>
          </button>`,
        )}
      </div>
      <div class="tm-axis" aria-hidden="true">${axis.map(
        (month) => html`<span class="tm-axis__month${closes.has(month.month) ? ' tm-axis__month--closes' : ''}" style="flex-grow: ${month.count}">${month.month}</span>`,
      )}</div>
    </div>
  </div>`;
}

function proofHtml(ctx, proof) {
  const { dom, fmt } = ctx;
  const { html } = dom;
  const sentences = proof.sentences || {};
  const top = Math.max(...RULES.map((rule) => proof.rules[rule.key]?.revenue || 0), 1);
  const rules = RULES.filter((rule) => proof.rules[rule.key]).map((rule) => {
    const revenue = proof.rules[rule.key].revenue;
    return html`<li class="tm-rule${rule.main ? ' tm-rule--main' : ''}">
      <span class="tm-rule__label">${rule.label}</span>
      <span class="tm-rule__value">${fmt.money(revenue)}</span>
      <span class="tm-rule__bar" aria-hidden="true" style="width: ${((revenue / top) * 100).toFixed(1)}%"></span>
    </li>`;
  });
  const limits = sentences.limits || [];
  return html`<section class="tm-proof" aria-labelledby="tm-proof-title">
      <div class="tm-proof__summary">
        <h2 class="tm-proof__lead" id="tm-proof-title">Uma lista não prova nada. No conjunto:</h2>
        <p class="tm-proof__headline">${sentences.headline}</p>
        <p class="tm-proof__detail">${emphasizePercents(ctx, sentences.headline_detail)}</p>
        <ul class="tm-rules" aria-label="Receita em 30 dias, somando as listas">${rules}</ul>
        <p class="tm-proof__method">${sentences.method}</p>
      </div>
      ${proof.per_date?.length ? chartHtml(ctx, proof) : ''}
    </section>
    ${limits.length
      ? html`<section class="tm-limits" aria-labelledby="tm-limits-title">
          <h2 class="eyebrow" id="tm-limits-title">Os limites desta prova</h2>
          <ul class="tm-limits__list">${limits.map(
            (item) => html`<li class="tm-limit"><h3 class="tm-limit__title">${item.title}</h3><p class="tm-limit__body">${item.body}</p></li>`,
          )}</ul>
        </section>`
      : ''}`;
}

function bindChart(ctx, container, proof) {
  const chart = container.querySelector('.tm-chart');
  if (!chart) return;
  const readout = chart.querySelector('[data-tm-readout]');
  const pairs = ctx.dom.qsa('[data-tm-pair]', chart);
  const show = (pair) => {
    readout.textContent = pair ? pairText(ctx, proof.per_date[Number(pair.dataset.tmPair)]) : defaultReadout(ctx, proof);
  };
  chart.addEventListener('mouseover', (event) => show(event.target.closest('[data-tm-pair]')));
  chart.addEventListener('mouseleave', () => show(chart.contains(document.activeElement) ? document.activeElement.closest('[data-tm-pair]') : null));
  chart.addEventListener('focusin', (event) => show(event.target.closest('[data-tm-pair]')));
  chart.addEventListener('focusout', (event) => {
    if (!chart.contains(event.relatedTarget)) show(null);
  });
  chart.addEventListener('keydown', (event) => {
    const pair = event.target.closest('[data-tm-pair]');
    if (!pair) return;
    const index = pairs.indexOf(pair);
    const moves = { ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: pairs.length - 1 };
    if (!(event.key in moves)) return;
    event.preventDefault();
    const target = pairs[Math.max(0, Math.min(pairs.length - 1, moves[event.key]))];
    pairs.forEach((other) => {
      other.tabIndex = other === target ? 0 : -1;
    });
    target.focus();
  });
}

/* Tela */

// Em tela estreita a linha do tempo rola de lado: deixa a data atual à vista.
function centerCurrentDot(wrap) {
  const scroller = wrap.querySelector('.tm-timeline__scroll');
  const dot = wrap.querySelector('.tm-dot.is-current');
  if (!scroller || !dot || scroller.scrollWidth <= scroller.clientWidth) return;
  const offset = dot.getBoundingClientRect().left - scroller.getBoundingClientRect().left;
  scroller.scrollLeft += offset - scroller.clientWidth / 2;
}

function restoreDateFocus(wrap) {
  const target = focusAfterDate;
  if (!target) return;
  let el = null;
  if (target.step) {
    el = wrap.querySelector(`[data-tm-step="${target.step}"]`);
    if (!el || el.disabled) el = wrap.querySelector('.tm-dot.is-current');
  } else if (target.pair) {
    // O gráfico chega depois (outra requisição): espera por ele.
    el = wrap.querySelector(`[data-tm-pair][data-tm-date="${target.iso}"]`);
    if (!el) return;
  } else {
    el = wrap.querySelector(`.tm-dot[data-tm-date="${target.iso}"]`);
  }
  focusAfterDate = null;
  el?.focus({ preventScroll: true });
}

export default {
  id: 'maquina',
  title: 'Máquina do tempo',
  roles: ['seller', 'manager'],
  area: 'vendas',

  render(root, ctx) {
    const { dom, ui } = ctx;
    const { html, setHtml, on } = dom;
    let wrap = root.querySelector('.tm');

    const viewing = ui.viewingBar(ctx, { what: 'a máquina do tempo' });
    if (ctx.reason === 'params' && wrap) {
      // Só o vendedor mudou: a linha do tempo e a prova ficam; a faixa do gestor e as listas são refeitas.
      wrap.querySelector('[data-viewing-bar]')?.replaceWith(dom.toFragment(viewing));
    } else {
      setHtml(root, html`<div class="tm">
        ${ui.screenHeader({
          eyebrow: 'Prova',
          title: 'Máquina do tempo',
          subtitle: 'Volte a qualquer segunda-feira do segundo semestre de 2017. O score só enxerga o que se sabia naquele dia. Depois, revele o que aconteceu.',
        })}
        ${viewing}
        ${timelineHtml(ctx)}
        <div class="tm-block" data-tm-lists></div>
        <div class="tm-block tm-block--proof" data-tm-proof></div>
      </div>`);
      wrap = root.querySelector('.tm');
      centerCurrentDot(wrap);
      restoreDateFocus(wrap);
    }

    const listsRoot = wrap.querySelector('[data-tm-lists]');
    const proofRoot = wrap.querySelector('[data-tm-proof]');
    // Abre escondido: quem chega vê primeiro as duas listas e só depois revela o que aconteceu.
    // "?desfecho=revelado" no endereço abre já revelado (link da documentação), até o primeiro clique no botão.
    let revealedByLink = !outcomeLinkUsed && ctx.params.desfecho === 'revelado';
    const isRevealed = () => revealedByLink || ctx.store.get(OUTCOME_KEY, 'escondido') === 'revelado';

    ui.load(
      listsRoot,
      () => ctx.api.get('time-machine', { name: ctx.subject, date: ctx.date }),
      (data) => setHtml(listsRoot, compareHtml(ctx, data, isRevealed())),
      { skeleton: { title: true, lines: 1, blocks: 4 }, errorTitle: 'Não foi possível montar as listas desta data.' },
    );

    if (!proofRoot.querySelector('.tm-proof')) {
      // Se a prova não chegar (erro ou saída da tela), o pedido de foco numa barra não pode sobrar para depois.
      const pending = focusAfterDate;
      ui.load(
        proofRoot,
        () => ctx.api.get('proof'),
        (proof) => {
          setHtml(proofRoot, proofHtml(ctx, proof));
          bindChart(ctx, proofRoot, proof);
          restoreDateFocus(wrap);
        },
        { skeleton: { title: false, lines: 2, blocks: 2 }, errorTitle: 'Não foi possível carregar a prova no conjunto.' },
      ).then((proof) => {
        if (!proof && pending && focusAfterDate === pending) focusAfterDate = null;
      });
    }

    const goTo = (iso, focus) => {
      if (!iso || iso === ctx.date) return;
      focusAfterDate = focus;
      ctx.setDate(iso);
    };

    const offs = [
      on(wrap, 'click', '.tm-dot[data-tm-date]', (event, dot) => goTo(dot.dataset.tmDate, { iso: dot.dataset.tmDate })),
      on(wrap, 'click', '[data-tm-pair]', (event, pair) => goTo(pair.dataset.tmDate, { iso: pair.dataset.tmDate, pair: true })),
      on(wrap, 'click', '[data-tm-step]', (event, button) => {
        const index = ctx.meta.dates.findIndex((d) => d.iso === ctx.date);
        const step = button.dataset.tmStep;
        const target = ctx.meta.dates[index + (step === 'next' ? 1 : -1)];
        goTo(target?.iso, { step });
      }),
      on(wrap, 'click', '[data-tm-toggle]', (event, button) => {
        const section = button.closest('.tm-compare');
        const reveal = section.dataset.outcome !== 'revealed';
        revealedByLink = false;
        outcomeLinkUsed = true;
        section.dataset.outcome = reveal ? 'revealed' : 'hidden';
        button.querySelector('span').textContent = reveal ? 'Esconder o desfecho' : 'Revelar o desfecho';
        ctx.store.set(OUTCOME_KEY, reveal ? 'revelado' : 'escondido');
        ui.toast(reveal ? 'Desfecho revelado.' : 'Desfecho escondido.');
      }),
    ];
    return () => offs.forEach((off) => off());
  },
};
