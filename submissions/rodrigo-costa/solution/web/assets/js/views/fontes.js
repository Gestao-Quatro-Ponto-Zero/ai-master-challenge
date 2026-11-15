// Configurações · Fontes de dados (prancha 07). Tudo vem de /api/sources; a tela só organiza.
const CONNECT_HINT = 'Somente referência: nenhuma integração existe neste conceito.';
const CONNECT_HINT_ID = 'fontes-conectar-dica';

function fileRow(file, { html }) {
  return html`<li class="fontes-file">
    <span class="fontes-file__name">${file.name}</span>
    <span class="fontes-file__desc">${file.description}</span>
    <span class="fontes-file__count num">${file.count_label}</span>
  </li>`;
}

function activeSource(active, { html, ui, icon }) {
  const files = active.files || [];
  return html`<section class="fontes-section" aria-labelledby="fontes-active-label">
    ${ui.eyebrow('Fonte em uso', { id: 'fontes-active-label' })}
    <div class="fontes-box">
      <div class="fontes-active">
        <span class="fontes-active__icon">${icon('database', { size: 20 })}</span>
        <div class="fontes-active__text">
          <h2 class="fontes-active__title">${active.title}</h2>
          ${active.detail ? html`<p class="fontes-active__detail">${active.detail}</p>` : ''}
        </div>
        ${active.status ? ui.badge(active.status, { tone: 'win', dot: true }) : ''}
      </div>
      ${files.length
        ? html`<ul class="fontes-files" aria-label="Arquivos lidos">${files.map((file) => fileRow(file, { html }))}</ul>`
        : html`<p class="fontes-box__empty">Nenhum arquivo lido nesta base.</p>`}
    </div>
  </section>`;
}

function crmRow(crm, { html, ui }) {
  return html`<li class="fontes-crm">
    <span class="fontes-crm__mark" aria-hidden="true">${crm.initials}</span>
    <div class="fontes-crm__text">
      <p class="fontes-crm__name">${crm.name}</p>
      ${crm.brings ? html`<p class="fontes-crm__brings">${crm.brings}</p>` : ''}
    </div>
    <button type="button" class="btn btn--secondary fontes-crm__connect"${ui.attrs({
      'aria-disabled': 'true',
      'aria-label': `Conectar ${crm.name}`,
      'aria-describedby': CONNECT_HINT_ID,
      title: CONNECT_HINT,
      'data-connect': true,
    })}>Conectar</button>
  </li>`;
}

function crmList(crms, { html, ui }) {
  const items = crms.items || [];
  return html`<section class="fontes-section" aria-labelledby="fontes-crm-label">
    <div class="fontes-section__head">
      ${ui.eyebrow(crms.title, { id: 'fontes-crm-label' })}
      ${crms.status ? html`<p class="fontes-section__status">${crms.status}</p>` : ''}
    </div>
    ${items.length
      ? html`<ul class="fontes-box fontes-crms">${items.map((crm) => crmRow(crm, { html, ui }))}</ul>
        <p class="sr-only" id="${CONNECT_HINT_ID}">${CONNECT_HINT}</p>`
      : html`<div class="fontes-box"><p class="fontes-box__empty">Nenhuma integração listada.</p></div>`}
  </section>`;
}

function requirements(req, { html, ui }) {
  const items = req.items || [];
  return html`<section class="fontes-req" aria-labelledby="fontes-req-title">
    <div class="fontes-req__head">
      ${req.label ? ui.eyebrow(req.label) : ''}
      <h2 class="fontes-req__title" id="fontes-req-title">${req.title}</h2>
    </div>
    <ol class="fontes-req__list">
      ${items.map((item, index) => html`<li class="fontes-req__item">
        <span class="fontes-req__num num" aria-hidden="true">${index + 1}</span>
        <div class="fontes-req__text">
          <p class="fontes-req__item-title">${item.title}</p>
          <p class="fontes-req__item-body">${item.text}</p>
        </div>
      </li>`)}
    </ol>
    ${req.note ? ui.note(req.note) : ''}
  </section>`;
}

function draw(body, data, ctx) {
  const { dom, ui } = ctx;
  const parts = { html: dom.html, ui, icon: ctx.icon };
  dom.setHtml(body, dom.html`
    ${data.alert ? ui.alert(data.alert) : ''}
    <div class="with-aside fontes-layout">
      <div class="with-aside__main fontes-main">
        ${data.active ? activeSource(data.active, parts) : ''}
        ${data.crms ? crmList(data.crms, parts) : ''}
      </div>
      ${data.requirements ? dom.html`<aside class="with-aside__aside fontes-aside">${requirements(data.requirements, parts)}</aside>` : ''}
    </div>`);
}

export default {
  id: 'fontes',
  title: 'Fontes de dados',
  roles: ['seller', 'manager'],
  area: 'config',

  render(root, ctx) {
    const { dom, ui } = ctx;
    dom.setHtml(root, dom.html`${ui.screenHeader({
      eyebrow: 'Configurações',
      title: 'Fontes de dados',
      subtitle: 'De onde vêm os dados que fazem o módulo de Vendas funcionar.',
    })}<div class="fontes-body"></div>`);

    const body = dom.qs('.fontes-body', root);
    // O botão não faz nada; no toque e no teclado, o motivo aparece num aviso.
    const off = dom.on(root, 'click', '[data-connect]', () => ui.toast(CONNECT_HINT));
    ui.load(body, () => ctx.api.get('sources'), (data) => draw(body, data, ctx), {
      skeleton: { title: false, lines: 1, blocks: 3 },
      errorTitle: 'Não foi possível carregar as fontes de dados.',
    });
    return off;
  },
};
