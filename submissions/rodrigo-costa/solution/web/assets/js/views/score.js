// Como o score funciona (prancha 08): a conta em três passos, um exemplo real, a tabela de chance
// por idade, as faixas, os sinais que ficaram de fora e a chamada para a prova.

const BAR_MAX_PX = 120;

// example.steps vem da API sempre com quatro frases: faixa, chance, receita esperada e score. Os passos 1 e 3
// usam a frase pronta do exemplo depois do texto fixo.
function steps({ html }, example) {
  const apiSteps = Array.isArray(example?.steps) ? example.steps : [];
  const withExample = (text, sentence) => (sentence ? `${text} ${sentence}` : text);
  // A frase da API já cita a faixa de idade e a semana do trimestre; o texto fixo não repete.
  const step1 = apiSteps[1]
    ? `Olhamos o que aconteceu com deals parecidos no passado. ${apiSteps[1]}`
    : 'Olhamos o que aconteceu com deals da mesma idade, na mesma semana do trimestre.';
  const step3 = withExample('O score de 0 a 100 é a posição do deal na fila da empresa.', apiSteps[3]);
  const items = [
    ['Passo 1', 'Chance de virar venda em 30 dias', step1],
    ['Passo 2', 'Vezes o preço de tabela', 'Chance vezes valor dá a receita esperada do deal. Um deal caro com pouca chance pode valer menos que um médio prestes a fechar.'],
    ['Passo 3', 'Posição entre os deals vivos', step3],
  ];
  return html`<ol class="score-steps">${items.map(
    ([label, title, body]) => html`<li class="score-step">
      <p class="eyebrow">${label}</p>
      <h2 class="score-step__title">${title}</h2>
      <p class="score-step__body">${body}</p>
    </li>`,
  )}</ol>`;
}

function exampleStrip({ html }, fmt, icon, ctx, data) {
  const example = data.example;
  if (!example) {
    return html`<section class="score-example score-example--empty" aria-label="Exemplo real">
      <p class="score-example__muted">Nesta data não há deal vivo para servir de exemplo.</p>
    </section>`;
  }
  const showOwner = !example.is_viewer || example.seller !== ctx.user.name;
  const opened = `aberto há ${fmt.plural(example.age_days, 'dia')}`;
  const terms = [
    [fmt.percent(example.chance), `${fmt.number(example.y)} de ${fmt.number(example.n)} parecidos`],
    [fmt.money(example.price), 'preço de tabela'],
    [fmt.money(example.expected_value), 'receita esperada'],
  ];
  const term = ([value, sub]) => html`<div class="score-term"><p class="score-term__value">${value}</p><p class="score-term__sub">${sub}</p></div>`;
  const op = (symbol) => html`<span class="score-op" aria-hidden="true">${symbol}</span>`;
  const hasSteps = Array.isArray(example.steps) && example.steps.length > 0;

  return html`<section class="score-example" aria-labelledby="score-example-title">
    <div class="score-example__row">
      <div class="score-example__deal">
        <p class="eyebrow" id="score-example-title">Exemplo real · ${data.date?.label || ''}</p>
        <p class="score-example__name">${example.product} · #${example.id}</p>
        <p class="score-example__muted">${opened}${showOwner ? html` · de ${example.seller}` : ''}</p>
      </div>
      <div class="score-example__math">
        ${term(terms[0])}${op('×')}${term(terms[1])}${op('=')}${term(terms[2])}
        <span class="score-op score-op--arrow" aria-hidden="true">${icon('arrowRight', { size: 22, stroke: 1.8 })}</span>
        <div class="score-seal">
          <p class="score-seal__value">${example.score}</p>
          <p class="score-seal__sub">score · ${String(example.band_label || '').toLocaleLowerCase('pt-BR')}</p>
        </div>
      </div>
    </div>
    ${example.note ? html`<p class="score-example__muted">${example.note}</p>` : ''}
    ${hasSteps ? html`<div class="score-example__more">
      <button type="button" class="link-arrow score-example__toggle" data-score-steps aria-expanded="false" aria-controls="score-steps-list">Ver a conta passo a passo${icon('chevronDown', { size: 14, stroke: 2 })}</button>
      <ol class="score-example__steps" id="score-steps-list" hidden>${example.steps.map((text) => html`<li>${text}</li>`)}</ol>
    </div>` : ''}
  </section>`;
}

function chart({ html }, fmt, data) {
  const table = Array.isArray(data.table) ? data.table : [];
  if (table.length === 0) {
    return html`<p class="score-chart__empty">A tabela de chance não está disponível para esta data.</p>`;
  }
  const max = Math.max(...table.map((row) => Number(row.chance) || 0));
  const height = (row) => {
    const chance = Number(row.chance) || 0;
    if (max <= 0 || chance <= 0) return 2;
    return Math.max(2, Math.round((chance / max) * BAR_MAX_PX));
  };
  const barClass = (row) => {
    if (row.stale) return 'score-bar score-bar--stale';
    return row.in_window ? 'score-bar score-bar--window' : 'score-bar';
  };

  return html`<div class="score-chart__scroll" role="region" tabindex="0" aria-label="Gráfico de chance por idade do deal">
    <div class="score-chart" aria-hidden="true">
      <div class="score-chart__bars">${table.map(
        (row) => html`<div class="${barClass(row)}">
          <span class="score-bar__value">${row.chance_label}</span>
          <span class="score-bar__fill" style="height: ${row.stale ? 0 : height(row)}px"></span>
        </div>`,
      )}</div>
      <div class="score-chart__axis">${table.map(
        (row) => html`<div class="score-chart__tick"><span class="score-chart__label">${row.label}</span><span class="score-chart__n">${fmt.number(row.n)}</span></div>`,
      )}</div>
    </div>
    <table class="sr-only">
      <caption>Chance de virar venda em 30 dias, por idade do deal</caption>
      <thead><tr><th scope="col">Idade, em dias</th><th scope="col">Chance</th><th scope="col">Casos</th><th scope="col">Situação</th></tr></thead>
      <tbody>${table.map(
        (row) => html`<tr><th scope="row">${row.label}</th><td>${row.chance_label}</td><td>${fmt.number(row.y)} de ${fmt.number(row.n)}</td><td>${
          row.stale ? 'sem desfecho' : row.in_window ? 'janela boa' : ''
        }</td></tr>`,
      )}</tbody>
    </table>
  </div>`;
}

function bands({ html }, data) {
  const score = data.bands?.score || [];
  const stale = data.bands?.stale;
  return html`<div class="score-bands">
    <p class="eyebrow" id="score-bands-title">As faixas</p>
    <dl class="score-bands__list" aria-labelledby="score-bands-title">
      ${score.map((band) => html`<div class="score-band"><dt>${band.label}</dt><dd>${band.rule}</dd></div>`)}
      ${stale ? html`<div class="score-band score-band--stale">
        <div class="score-band__line"><dt>${stale.label}</dt><dd>${stale.rule}</dd></div>
        ${stale.text ? html`<dd class="score-band__text">${stale.text}</dd>` : ''}
      </div>` : ''}
    </dl>
    <div class="score-unknown">
      <p class="score-unknown__title">O que o score não sabe</p>
      <p class="score-unknown__body">Dois deals da mesma idade têm a mesma chance: o score não conhece o cliente nem a conversa. Ele ordena a semana; não prevê um deal.</p>
    </div>
  </div>`;
}

function signals({ html }, data) {
  const rows = Array.isArray(data.signals) ? data.signals : [];
  return html`<section class="score-signals" aria-labelledby="score-signals-title">
    <div class="score-section-head">
      <h2 class="eyebrow" id="score-signals-title">O que foi testado e ficou de fora</h2>
      <p class="score-section-head__sub">Um sinal só entra no score se mudar a chance de fechar e se existir de forma confiável nos deals abertos.</p>
    </div>
    ${rows.length === 0
      ? html`<p class="score-chart__empty">Nenhum sinal testado para mostrar.</p>`
      : html`<table class="score-signals__table">
        <thead class="sr-only"><tr><th scope="col">Sinal</th><th scope="col">O que os dados mostraram</th><th scope="col">Decisão</th></tr></thead>
        <tbody>${rows.map(
          (row) => html`<tr>
            <th scope="row" class="score-signals__name">${row.signal}</th>
            <td class="score-signals__finding"><p>${row.finding}</p>${row.evidence ? html`<p class="score-signals__evidence">${row.evidence}</p>` : ''}</td>
            <td class="score-signals__decision">${row.decision}</td>
          </tr>`,
        )}</tbody>
      </table>`}
  </section>`;
}

function proof({ html }, icon, ctx, data) {
  return html`<section class="score-proof" aria-labelledby="score-proof-title">
    <div class="score-proof__text">
      <h2 class="score-proof__title" id="score-proof-title">E funciona? A prova está na Máquina do tempo.</h2>
      ${data.proof?.sentence ? html`<p class="score-proof__body">${data.proof.sentence}</p>` : ''}
    </div>
    <a class="score-proof__link" href="${ctx.href('maquina-do-tempo')}">Abrir a Máquina do tempo${icon('arrowRight', { size: 16, stroke: 2 })}</a>
  </section>`;
}

function page(ctx, data) {
  const { dom, fmt, icon } = ctx;
  const { html } = dom;
  return html`${steps(dom, data.example)}
    ${exampleStrip(dom, fmt, icon, ctx, data)}
    <div class="score-split">
      <section class="score-chance" aria-labelledby="score-chance-title">
        <div class="score-section-head">
          <h2 class="eyebrow" id="score-chance-title">Chance de virar venda em 30 dias, por idade do deal</h2>
          ${data.table_sentence ? html`<p class="score-section-head__sub">${data.table_sentence}</p>` : ''}
        </div>
        ${chart(dom, fmt, data)}
        ${data.training?.sentence ? html`<p class="score-chance__note">${data.training.sentence}</p>` : ''}
      </section>
      ${bands(dom, data)}
    </div>
    ${signals(dom, data)}
    ${proof(dom, icon, ctx, data)}`;
}

export default {
  id: 'score',
  title: 'Como o score funciona',
  roles: ['seller', 'manager'],
  area: 'vendas',

  render(root, ctx) {
    const { dom, ui } = ctx;
    dom.setHtml(root, dom.html`${ui.screenHeader({
      eyebrow: 'Transparência',
      title: 'Como o score funciona',
      subtitle: 'Uma conta curta, que dá para refazer na mão: chance de virar venda em 30 dias, vezes o valor do deal.',
    })}<div class="score-body"></div>`);
    const body = root.querySelector('.score-body');

    const offToggle = dom.on(root, 'click', '[data-score-steps]', (event, button) => {
      const list = document.getElementById(button.getAttribute('aria-controls'));
      if (!list) return;
      const open = button.getAttribute('aria-expanded') !== 'true';
      button.setAttribute('aria-expanded', String(open));
      list.hidden = !open;
    });

    ui.load(
      body,
      () => ctx.api.get('score-model', { date: ctx.date, viewer: ctx.user.name }),
      (data) => dom.setHtml(body, page(ctx, data)),
      { skeleton: { title: false, lines: 3, blocks: 4 }, errorTitle: 'Não foi possível carregar a explicação do score.' },
    );

    return offToggle;
  },
};
