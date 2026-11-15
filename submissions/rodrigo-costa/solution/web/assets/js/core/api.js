// Cliente da API: cache por URL, erro com a mensagem da API e cancelamento da requisição antiga.

const CACHE_LIMIT = 200;
const TIMEOUT_MS = 15000;
const cache = new Map(); // url -> dados (só respostas 200)
const inflight = new Map(); // url -> { promise, controller, waiters }

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export function isAbort(error) {
  return error?.name === 'AbortError';
}

function abortError() {
  return new DOMException('Requisição cancelada.', 'AbortError');
}

// buildUrl('seller', { name: 'A B', date: '2017-12-04' }) -> "/api/seller?date=2017-12-04&name=A+B"
export function buildUrl(path, params = {}) {
  const base = path.startsWith('/') ? path : `/api/${path}`;
  const query = new URLSearchParams();
  Object.keys(params)
    .sort()
    .forEach((key) => {
      const value = params[key];
      if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
    });
  const text = query.toString();
  return text ? `${base}?${text}` : base;
}

async function parse(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    const message = typeof body?.error === 'string' && body.error
      ? body.error
      : `O servidor não respondeu como esperado (código ${response.status}).`;
    throw new ApiError(message, response.status);
  }
  if (body === null) throw new ApiError('A resposta do servidor veio vazia ou inválida.', response.status);
  return body;
}

function remember(url, data) {
  cache.delete(url);
  cache.set(url, data);
  if (cache.size > CACHE_LIMIT) cache.delete(cache.keys().next().value);
}

// O tempo limite cancela com um TimeoutError, separado do AbortError do cancelamento silencioso: um servidor
// que aceita a conexão e não responde vira mensagem com "Tentar de novo", e não esqueleto eterno.
function startFetch(url) {
  const controller = new AbortController();
  const entry = { controller, waiters: 0, promise: null };
  const timer = window.setTimeout(() => controller.abort(new DOMException('Tempo esgotado.', 'TimeoutError')), TIMEOUT_MS);
  const timedOut = () => controller.signal.aborted && controller.signal.reason?.name === 'TimeoutError';
  entry.promise = fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } })
    .catch((error) => {
      if (isAbort(error)) throw error;
      throw new ApiError('Sem conexão com o servidor. Confira se ele está no ar e tente de novo.', 0);
    })
    .then(parse)
    .catch((error) => {
      // Vale também para o corpo que parou no meio (parse veria uma resposta vazia).
      if (timedOut()) throw new ApiError('O servidor demorou para responder. Tente de novo.', 0);
      throw error;
    })
    .then((data) => {
      remember(url, data);
      return data;
    })
    .finally(() => {
      window.clearTimeout(timer);
      if (inflight.get(url) === entry) inflight.delete(url);
    });
  inflight.set(url, entry);
  return entry;
}

// Busca uma URL já montada. Requisições iguais em andamento são compartilhadas; a de rede só é
// cancelada quando todos que esperam por ela desistem.
export function request(url, signal) {
  if (cache.has(url)) return Promise.resolve(cache.get(url));
  if (signal?.aborted) return Promise.reject(abortError());
  const entry = inflight.get(url) || startFetch(url);
  entry.waiters += 1;
  return new Promise((resolve, reject) => {
    const onAbort = () => {
      entry.waiters -= 1;
      if (entry.waiters === 0) {
        entry.controller.abort();
        if (inflight.get(url) === entry) inflight.delete(url);
      }
      reject(abortError());
    };
    signal?.addEventListener('abort', onAbort, { once: true });
    entry.promise.then(
      (data) => {
        signal?.removeEventListener('abort', onAbort);
        resolve(data);
      },
      (error) => {
        signal?.removeEventListener('abort', onAbort);
        reject(error);
      },
    );
  });
}

// Escopo de uma tela. dispose() cancela tudo o que ainda está pendente.
// get(path, params, { channel }) cancela a chamada anterior do mesmo canal (padrão: o próprio path).
// Uma resposta que chega depois do cancelamento (inclusive a que vem do cache) vira AbortError: a resposta
// antiga nunca sobrescreve a nova.
export function createScope() {
  const scope = new AbortController();
  const latest = new Map();

  return {
    signal: scope.signal,
    get(path, params = {}, { channel = path } = {}) {
      latest.get(channel)?.abort();
      const controller = new AbortController();
      latest.set(channel, controller);
      const stop = () => controller.abort();
      if (scope.signal.aborted) stop();
      scope.signal.addEventListener('abort', stop, { once: true });
      return request(buildUrl(path, params), controller.signal)
        .then((data) => {
          if (controller.signal.aborted) throw abortError();
          return data;
        })
        .finally(() => {
          scope.signal.removeEventListener('abort', stop);
          if (latest.get(channel) === controller) latest.delete(channel);
        });
    },
    dispose() {
      scope.abort();
    },
  };
}
