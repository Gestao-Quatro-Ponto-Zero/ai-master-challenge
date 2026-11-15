// Estado do navegador: usuário simulado, data simulada e decisões locais. Tudo fica em localStorage
// com o prefixo "leadscorer:" e só neste navegador; nada vai para o servidor.

const PREFIX = 'leadscorer:';
const events = new EventTarget();

// localStorage pode não existir ou recusar escrita (janela privada, cota): o app segue sem salvar.
function readKey(key, fallback = null) {
  try {
    const value = window.localStorage.getItem(PREFIX + key);
    return value === null ? fallback : JSON.parse(value);
  } catch {
    return fallback;
  }
}

function writeKey(key, value) {
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function removeKey(key) {
  try {
    window.localStorage.removeItem(PREFIX + key);
  } catch {
    // sem armazenamento: nada a remover
  }
}

function listKeys(prefix) {
  try {
    const full = PREFIX + prefix;
    const keys = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const key = window.localStorage.key(i);
      if (key && key.startsWith(full)) keys.push(key.slice(full.length));
    }
    return keys;
  } catch {
    return [];
  }
}

function emit(what, detail = {}) {
  events.dispatchEvent(new CustomEvent('change', { detail: { what, ...detail } }));
}

// Avisa mudanças: fn({ what: 'user' | 'date' | 'store', key? }). Devolve a função que para de ouvir.
export function onChange(fn) {
  const listener = (event) => fn(event.detail);
  events.addEventListener('change', listener);
  return () => events.removeEventListener('change', listener);
}

let user = readKey('usuario');
let date = readKey('data');

// { role: 'seller' | 'manager', name } ou null
export function getUser() {
  return user && typeof user.name === 'string' && (user.role === 'seller' || user.role === 'manager') ? user : null;
}

export function setUser(next) {
  user = next ? { role: next.role, name: next.name } : null;
  if (user) writeKey('usuario', user);
  else removeKey('usuario');
  emit('user');
}

// Data ISO salva (pode ser null antes da primeira escolha).
export function getDate() {
  return typeof date === 'string' ? date : null;
}

export function setDate(iso) {
  if (iso === date) return;
  date = iso;
  writeKey('data', iso);
  emit('date');
}

// Decisões locais de um usuário: chaves isoladas por pessoa ("leadscorer:decisoes:<papel>:<nome>:<chave>").
export function createStore(owner) {
  const base = owner ? `decisoes:${owner.role}:${owner.name}:` : 'decisoes:anonimo:';
  return {
    get(key, fallback = null) {
      return readKey(base + key, fallback);
    },
    set(key, value) {
      const ok = writeKey(base + key, value);
      emit('store', { key });
      return ok;
    },
    remove(key) {
      removeKey(base + key);
      emit('store', { key });
    },
    keys(prefix = '') {
      return listKeys(base + prefix).map((key) => prefix + key);
    },
  };
}

// Preferências do navegador que não pertencem a ninguém (por exemplo, a última aba aberta).
export const prefs = {
  get: (key, fallback = null) => readKey(`pref:${key}`, fallback),
  set: (key, value) => writeKey(`pref:${key}`, value),
};
