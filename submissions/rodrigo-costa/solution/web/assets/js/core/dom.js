// Escape, marcação segura, criação de elementos e delegação de eventos.

const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => ESCAPES[ch]);
}

// Marcação já escapada. Só `html` e `raw` criam instâncias.
class SafeHtml {
  constructor(value) {
    this.value = value;
  }

  toString() {
    return this.value;
  }
}

// Marca um texto como HTML confiável. Use só com marcação escrita no código, nunca com dado da API.
export function raw(markup) {
  return new SafeHtml(String(markup));
}

function toHtml(value) {
  if (value === null || value === undefined || value === false) return '';
  if (value instanceof SafeHtml) return value.value;
  if (Array.isArray(value)) return value.map(toHtml).join('');
  return escapeHtml(value);
}

// Template com escape automático: html`<p>${texto}</p>`. Valores html`` aninhados e listas entram sem escape duplo.
export function html(strings, ...values) {
  let out = strings[0];
  values.forEach((value, i) => {
    out += toHtml(value) + strings[i + 1];
  });
  return new SafeHtml(out);
}

// Substitui o conteúdo de `el` pela marcação (html`` ou texto, que é escapado).
export function setHtml(el, content) {
  el.innerHTML = toHtml(content);
  return el;
}

// Converte marcação em nós soltos (DocumentFragment).
export function toFragment(content) {
  const template = document.createElement('template');
  template.innerHTML = toHtml(content);
  return template.content;
}

// Cria um elemento: h('button', { class: 'btn', type: 'button', text: 'Ok', on: { click } }, ...filhos)
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'class') el.className = value;
    else if (key === 'text') el.textContent = value;
    else if (key === 'html') setHtml(el, value);
    else if (key === 'on') {
      for (const [type, handler] of Object.entries(value)) el.addEventListener(type, handler);
    } else if (key === 'dataset') Object.assign(el.dataset, value);
    else el.setAttribute(key, value === true ? '' : String(value));
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return el;
}

export function qs(selector, root = document) {
  return root.querySelector(selector);
}

export function qsa(selector, root = document) {
  return Array.from(root.querySelectorAll(selector));
}

// Delegação: on(root, 'click', '[data-acao]', (event, alvo) => ...). Devolve a função que remove o ouvinte.
export function on(root, type, selector, handler, options) {
  const listener = (event) => {
    const target = event.target instanceof Element ? event.target.closest(selector) : null;
    if (target && root.contains(target)) handler(event, target);
  };
  root.addEventListener(type, listener, options);
  return () => root.removeEventListener(type, listener, options);
}

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

export function focusables(root) {
  return qsa(FOCUSABLE, root).filter((el) => !el.closest('[hidden]') && el.getClientRects().length > 0);
}
