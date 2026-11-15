// Qualidade dos dados (prancha 10): cobertura da base, as cinco particularidades, campo a campo e regionais.
// Os números e as frases vêm prontos de /api/data-quality; aqui só se formatam as contagens cruas da tabela.

const SCOPE_WHOLE_BASE = 'base inteira';

export default {
  id: 'qualidade',
  title: 'Qualidade dos dados',
  roles: ['seller', 'manager'],
  area: 'vendas',

  render(root, ctx) {
    const { dom, ui } = ctx;
    const { html } = dom;

    dom.setHtml(root, html`${ui.screenHeader({
      eyebrow: 'Transparência',
      title: 'Qualidade dos dados',
      subtitle: 'O que a base tem, o que falta e as cinco particularidades que mudaram o desenho do score.',
    })}<div class="dq" data-dq-body></div>`);

    const body = root.querySelector('[data-dq-body]');
    ui.load(body, () => ctx.api.get('data-quality', { date: ctx.date }), (data) => draw(body, data, ctx), {
      skeleton: { title: false, lines: 2, blocks: 5 },
      errorTitle: 'Não foi possível carregar a qualidade dos dados.',
    });
  },
};

function draw(body, data, ctx) {
  const { dom, ui } = ctx;
  const { html } = dom;
  const coverage = data?.coverage ?? [];
  const items = data?.items ?? [];
  const fields = data?.fields ?? [];
  const regions = data?.regions;
  const dateLabel = data?.date?.label ?? regions?.date_label ?? '';

  if (!coverage.length && !items.length && !fields.length && !regions?.rows?.length) {
    ui.showEmpty(body, 'A base não trouxe informações de qualidade para esta data.', { title: 'Nada para mostrar' });
    return;
  }

  dom.setHtml(body, html`
    ${coverage.length ? coverageBlock(coverage, html) : ''}
    ${items.length ? itemsBlock(items, dateLabel, html) : ''}
    <div class="dq-details">
      ${fields.length ? fieldsBlock(fields, html) : ''}
      ${regionsBlock(regions, data?.fixes, ctx)}
    </div>`);
}

function coverageBlock(coverage, html) {
  return html`<section class="dq-coverage" aria-label="Cobertura da base">
    <ul class="dq-coverage__list">${coverage.map(
      (entry) => html`<li class="dq-coverage__item">
        <p class="dq-coverage__value">${entry.value}</p>
        ${entry.detail ? html`<p class="dq-coverage__detail">${entry.detail}</p>` : ''}
      </li>`,
    )}</ul>
  </section>`;
}

function scopeText(scope, dateLabel) {
  if (!scope) return '';
  if (scope === SCOPE_WHOLE_BASE || !dateLabel) return scope;
  return `${scope} de ${dateLabel}`;
}

function itemsBlock(items, dateLabel, html) {
  return html`<section class="dq-items" aria-labelledby="dq-items-title">
    <h2 class="sr-only" id="dq-items-title">As particularidades da base</h2>
    <div class="dq-items__head" aria-hidden="true">
      <p class="eyebrow dq-items__col-number">O número</p>
      <p class="eyebrow dq-items__col-text">O que acontece na base</p>
      <p class="eyebrow dq-items__col-action">O que o app faz</p>
    </div>
    <ol class="dq-items__list">${items.map((item) => {
      const scope = scopeText(item.scope, dateLabel);
      return html`<li class="dq-item">
        <div class="dq-item__number">
          <p class="dq-item__value">${item.number}</p>
          ${scope ? html`<p class="dq-item__scope">${scope}</p>` : ''}
        </div>
        <div class="dq-item__text">
          <h3 class="dq-item__title">${item.title}</h3>
          ${item.body ? html`<p class="dq-item__body">${item.body}</p>` : ''}
        </div>
        ${item.action ? html`<div class="dq-item__action">
          <p class="eyebrow dq-item__action-label">O que o app faz</p>
          <p class="dq-item__action-text">${item.action}</p>
        </div>` : ''}
      </li>`;
    })}</ol>
  </section>`;
}

function fieldsBlock(fields, html) {
  return html`<section class="dq-fields" aria-labelledby="dq-fields-title">
    <h2 class="eyebrow dq-fields__title" id="dq-fields-title">Campo a campo</h2>
    <dl class="dq-fields__list">${fields.map(
      (entry) => html`<div class="dq-field">
        <dt class="dq-field__name">${entry.field}</dt>
        <dd class="dq-field__text">${entry.text}</dd>
      </div>`,
    )}</dl>
  </section>`;
}

function regionsBlock(regions, fixes, ctx) {
  const { dom, fmt, ui } = ctx;
  const { html } = dom;
  const rows = regions?.rows ?? [];
  const heading = regions?.date_label ? `Regional · ${regions.date_label}` : 'Regional';

  const table = rows.length
    ? ui.tableWrap(
        html`<table class="dq-regions">
          <caption class="sr-only">Deals abertos e sem desfecho por regional${regions?.date_label ? `, em ${regions.date_label}` : ''}</caption>
          <thead><tr>
            <th scope="col" class="dq-regions__name">${heading}</th>
            <th scope="col" class="dq-regions__num">Abertos</th>
            <th scope="col" class="dq-regions__num dq-regions__num--wide">Sem desfecho</th>
          </tr></thead>
          <tbody>${rows.map(
            (row) => html`<tr>
              <th scope="row" class="dq-regions__name">${row.region_label || row.region}</th>
              <td class="dq-regions__num">${fmt.number(row.open_count)}</td>
              <td class="dq-regions__num dq-regions__num--wide dq-regions__stale">${fmt.number(row.stale_count)}</td>
            </tr>`,
          )}</tbody>
        </table>`,
        { label: heading },
      )
    : '';

  if (!table && !regions?.sentence && !fixes?.title) return '';

  return html`<section class="dq-side" aria-label="Regionais e consertos">
    ${table}
    ${regions?.sentence ? html`<p class="dq-side__sentence">${regions.sentence}</p>` : ''}
    ${fixes && (fixes.title || fixes.text) ? html`<div class="dq-fixes">
      ${fixes.title ? html`<h2 class="dq-fixes__title">${fixes.title}</h2>` : ''}
      ${fixes.text ? html`<p class="dq-fixes__text">${fixes.text}</p>` : ''}
    </div>` : ''}
  </section>`;
}
