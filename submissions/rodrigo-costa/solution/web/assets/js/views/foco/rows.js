// Marcação das linhas da lista do Foco da semana: cabeçalho, linha viva, linha sem desfecho e o bloco aberto.
// Tudo usa os textos e números da API como vêm; aqui só se formatam valores crus (preço, chance).
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import * as fmt from '../../core/fmt.js';
import { STALE_DECISIONS } from '../../core/marks.js';
import * as ui from '../../core/ui.js';

const detailId = (deal) => `foco-deal-${deal.id}`;

function title(deal) {
  return html`<span class="foco-row__title"><b>${deal.product}</b> · ${fmt.money(deal.price)}</span>`;
}

function liveMeta(deal) {
  return deal.account ? `${deal.account} · #${deal.id}` : `#${deal.id} · aberto em ${deal.engage_label}`;
}

function staleMeta(deal) {
  const opened = `#${deal.id} · aberto em ${deal.engage_label}`;
  return deal.account ? `${deal.account} · ${opened}` : opened;
}

function toggleAttrs(deal, open) {
  return ui.attrs({
    'data-toggle': deal.id,
    'data-key': `toggle:${deal.id}`,
    'aria-expanded': String(open),
    'aria-controls': open ? detailId(deal) : null,
  });
}

function chevron() {
  return html`<span class="foco-row__chevron" aria-hidden="true">${icon('chevronDown', { size: 16, stroke: 2 })}</span>`;
}

function ruler(deal, win, treated) {
  if (!win || !Number.isFinite(win.max_days)) return '';
  const hasWindow = Number.isFinite(win.from_days) && Number.isFinite(win.to_days);
  const label = hasWindow
    ? `${deal.age_days} dias; a faixa que mais fecha vai de ${win.from_days} a ${win.to_days} dias`
    : `${deal.age_days} dias, numa régua de 0 a ${win.max_days} dias`;
  return ui.ageRuler({
    age: deal.age_days,
    max: win.max_days,
    from: hasWindow ? win.from_days : undefined,
    to: hasWindow ? win.to_days : undefined,
    stale: treated,
    label,
  });
}

// Cabeçalho das colunas (só visual: cada linha já diz o que é cada número).
export function listHead({ stale }) {
  return html`<div class="foco-head${stale ? ' foco-head--stale' : ''}" aria-hidden="true">
    <span class="foco-head__grid">
      <span class="eyebrow">Score</span><span class="eyebrow">Deal</span><span class="eyebrow foco-head__age">Idade</span>${
        stale ? '' : html`<span class="eyebrow foco-head__chance">Chance</span>`
      }
    </span>
    <span class="eyebrow foco-head__actions">${stale ? 'Decisão' : ''}</span>
  </div>`;
}

function detailBlock(deal, columns, buttons) {
  return html`<div class="foco-detail" id="${detailId(deal)}">
    <div class="foco-detail__cols">${columns.map(
      (col, index) => html`<div class="foco-detail__col">
        <p class="foco-detail__label${index === 0 ? ' foco-detail__label--strong' : ''}">${col.label}</p>
        <p class="foco-detail__text">${col.text}</p>
      </div>`,
    )}</div>
    <div class="foco-detail__foot">
      ${deal.why?.action ? html`<p class="foco-detail__action"><b>O que fazer:</b> ${deal.why.action}</p>` : html`<span></span>`}
      <div class="foco-detail__buttons">${buttons}</div>
    </div>
  </div>`;
}

function copyButton(deal) {
  return ui.button('Copiar resumo', { size: 'sm', attrs: { 'data-copy': deal.id, 'data-key': `copy:${deal.id}` } });
}

export function liveRow(deal, { open, treated, win }) {
  const score = Number.isFinite(deal.score) ? deal.score : '—';
  const treatLabel = `${treated ? 'Desfazer tratado' : 'Marcar como tratado'}: ${deal.product}, #${deal.id}`;
  const detail = open
    ? detailBlock(
        deal,
        [
          { label: `Por que ${score}`, text: deal.why?.reason },
          { label: 'De onde vem a chance', text: deal.why?.source },
          { label: 'O que não entra', text: deal.why?.excluded },
        ],
        html`${copyButton(deal)}${ui.button(treated ? 'Desfazer' : 'Marcar como tratado', {
          size: 'sm',
          variant: treated ? 'secondary' : 'primary',
          attrs: { 'data-treat': deal.id, 'data-key': `treat-detail:${deal.id}`, 'aria-pressed': String(treated) },
        })}`,
      )
    : '';
  return html`<div class="foco-row${open ? ' is-open' : ''}${treated ? ' is-treated' : ''}" data-deal="${deal.id}">
    <div class="foco-row__line">
      <button type="button" class="foco-row__toggle"${toggleAttrs(deal, open)}>
        <span class="foco-row__score"><span class="sr-only">Score </span>${score}</span>
        <span class="foco-row__main">${title(deal)}<span class="foco-row__meta">${liveMeta(deal)}</span>${
          treated ? html`<span class="sr-only">. Tratado.</span>` : ''
        }</span>
        <span class="foco-row__age">
          <span class="foco-row__age-top"><span class="foco-row__days">${fmt.plural(deal.age_days, 'dia')}</span>${
            deal.position_label ? html`<span class="foco-row__position">${deal.position_label}</span>` : ''
          }</span>
          ${ruler(deal, win, treated)}
        </span>
        <span class="foco-row__chance"><span class="foco-row__pct">${fmt.percent(deal.chance)}</span><span class="foco-row__sub">em 30 dias</span></span>
      </button>
      <div class="foco-row__actions">
        <button type="button" class="foco-check" data-treat="${deal.id}" data-key="treat:${deal.id}" aria-pressed="${String(treated)}" aria-label="${treatLabel}">
          <span class="foco-check__ring">${icon('check', { size: 12, stroke: 3 })}</span>
        </button>
        ${chevron()}
      </div>
    </div>
    ${detail}
  </div>`;
}

export function staleRow(deal, { open, decision }) {
  const detail = open
    ? detailBlock(
        deal,
        [
          { label: 'Por que sem score', text: deal.why?.reason },
          { label: 'De onde vem isso', text: deal.why?.source },
        ],
        copyButton(deal),
      )
    : '';
  return html`<div class="foco-row foco-row--stale${open ? ' is-open' : ''}${decision ? ' is-decided' : ''}" data-deal="${deal.id}">
    <div class="foco-row__line">
      <button type="button" class="foco-row__toggle"${toggleAttrs(deal, open)}>
        <span class="foco-row__score foco-row__score--none"><span aria-hidden="true">—</span><span class="sr-only">Sem score</span></span>
        <span class="foco-row__main">${title(deal)}<span class="foco-row__meta">${staleMeta(deal)}</span>${
          decision ? html`<span class="sr-only">. Decisão: ${STALE_DECISIONS[decision].label}.</span>` : ''
        }</span>
        <span class="foco-row__age"><span class="foco-row__days">${fmt.plural(deal.age_days, 'dia')}</span></span>
      </button>
      <div class="foco-row__actions foco-row__actions--stale">
        ${ui.decisionButtons(deal, decision)}
        ${chevron()}
      </div>
    </div>
    ${detail}
  </div>`;
}
