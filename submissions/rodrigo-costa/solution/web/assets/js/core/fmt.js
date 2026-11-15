// Formatação de valores crus da API. Frases e números compostos já vêm prontos e não passam por aqui.

const integer = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const decimals = new Map();

function decimalFormat(digits) {
  if (!decimals.has(digits)) {
    decimals.set(
      digits,
      new Intl.NumberFormat('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits }),
    );
  }
  return decimals.get(digits);
}

const isNumber = (value) => typeof value === 'number' && Number.isFinite(value);

// 8800 -> "8.800"
export function number(value, digits = 0) {
  if (!isNumber(value)) return '—';
  return digits ? decimalFormat(digits).format(value) : integer.format(value);
}

// 5482.4 -> "US$ 5.482" (inteiro, ponto de milhar)
export function money(value) {
  if (!isNumber(value)) return '—';
  const text = `US$ ${integer.format(Math.abs(value))}`;
  return value < 0 ? `−${text}` : text;
}

// Fração de 0 a 1: 0.5 -> "50%"; percent(0.595, 1) -> "59,5%"
export function percent(fraction, digits = 0) {
  if (!isNumber(fraction)) return '—';
  return `${number(fraction * 100, digits)}%`;
}

// plural(1, 'deal', 'deals') -> "1 deal"; plural(2, 'deal', 'deals') -> "2 deals"
export function plural(count, singular, pluralForm = `${singular}s`) {
  return `${number(count)} ${pluralWord(count, singular, pluralForm)}`;
}

export function pluralWord(count, singular, pluralForm = `${singular}s`) {
  return count === 1 ? singular : pluralForm;
}

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

// Data crua "2017-12-31" -> "31 dez 2017" (as datas das telas já vêm com rótulo pronto da API).
export function dateLabel(iso) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso ?? ''));
  if (!match) return '—';
  return `${Number(match[3])} ${MONTHS[Number(match[2]) - 1]} ${match[1]}`;
}

// Para busca: sem diferença de caixa nem de acento ("São Paulo" -> "sao paulo").
export function normalize(text) {
  return String(text ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

// "seg, 4 dez 2017" -> "Seg, 4 dez 2017"
export function capitalize(text) {
  const value = String(text ?? '');
  return value.charAt(0).toLocaleUpperCase('pt-BR') + value.slice(1);
}

// "Daniell Hammack" -> "DH" (para quem não vem com initials da API)
export function initials(name) {
  return String(name ?? '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toLocaleUpperCase('pt-BR'))
    .join('');
}

export function firstName(name) {
  return String(name ?? '').trim().split(/\s+/)[0] || '';
}
