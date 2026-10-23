/**
 * Cabeçalhos de segurança e CORS. Não há login: os cabeçalhos protegem o navegador de quem usa
 * (sniffing, clickjacking, vazamento de referer, script de terceiros), não identificam ninguém.
 */
import type { MiddlewareHandler } from 'hono';
import { cors } from 'hono/cors';
import { responderErro } from './erros';

/**
 * Recusa (421) o pedido cujo `Host` não é deste servidor. Protege contra DNS rebinding: uma
 * página de fora que faça o próprio domínio apontar para 127.0.0.1 não lê a API.
 */
export function hostPermitido(hosts: readonly string[]): MiddlewareHandler {
  const lista = new Set(hosts.map((h) => h.toLowerCase()));
  return async (c, next) => {
    if (!lista.has((c.req.header('host') ?? '').toLowerCase())) {
      return responderErro(c, 421, {
        codigo: 'host_invalido',
        mensagem: 'Este servidor só atende pelo próprio endereço.',
      });
    }
    await next();
  };
}

/** CSP das respostas da API: JSON não carrega nada nem pode ser emoldurado. */
export const CSP_API = "default-src 'none'; frame-ancestors 'none'";

/** CSP da web servida pela API: só recursos próprios, mais as fontes livres do Google Fonts. */
export const CSP_WEB = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  "img-src 'self' data:",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join('; ');

/** Caminhos que são da API (o resto, quando a web é servida, é página ou estático). */
export function ehCaminhoDaApi(caminho: string): boolean {
  return caminho === '/health' || caminho === '/api' || caminho.startsWith('/api/');
}

/**
 * Cabeçalhos em toda resposta, inclusive nas de erro: `nosniff`, `X-Frame-Options: DENY`,
 * `Referrer-Policy: no-referrer`, `Cross-Origin-Resource-Policy: same-origin`; CSP da API ou da
 * web conforme o caminho; `Cache-Control: no-store` em `/api` (a fila muda com as respostas).
 */
export function cabecalhosDeSeguranca(): MiddlewareHandler {
  return async (c, next) => {
    await next();
    const h = c.res.headers;
    h.set('X-Content-Type-Options', 'nosniff');
    h.set('X-Frame-Options', 'DENY');
    h.set('Referrer-Policy', 'no-referrer');
    h.set('Cross-Origin-Resource-Policy', 'same-origin');
    h.set('Content-Security-Policy', ehCaminhoDaApi(c.req.path) ? CSP_API : CSP_WEB);
    if (c.req.path === '/api' || c.req.path.startsWith('/api/')) h.set('Cache-Control', 'no-store');
  };
}

/** CORS restrito às origens da lista, só GET/POST, sem credenciais (não há cookie nem sessão). */
export function corsRestrito(origens: readonly string[]): MiddlewareHandler {
  const permitidas = new Set(origens);
  return cors({
    origin: (origem) => (permitidas.has(origem) ? origem : null),
    allowMethods: ['GET', 'POST'],
    allowHeaders: ['Content-Type'],
    credentials: false,
    maxAge: 600,
  });
}
