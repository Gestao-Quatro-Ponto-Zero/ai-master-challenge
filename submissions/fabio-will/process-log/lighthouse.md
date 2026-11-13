# Lighthouse 13.5.0 (13/11/2026, em produção)

Medido na URL publicada, [fabiowill-challenge-002.vercel.app](https://fabiowill-challenge-002.vercel.app), com os cabeçalhos do `vercel.json` (CSP com hash, HSTS, X-Frame-Options) e a CDN da Vercel. Mobile = perfil padrão do Lighthouse (4G lento simulado). SEO 60 é proposital: o protótipo usa a identidade da G4 e leva `noindex` para não aparecer em buscador.

| Página | Modo | Performance | Acessibilidade | Boas práticas | SEO | LCP | TBT | CLS |
|---|---|---|---|---|---|---|---|---|
| / | mobile | 99 | 100 | 100 | 60 | 2,1 s | 30 ms | 0 |
| / | desktop | 100 | 100 | 100 | 60 | 0,5 s | 0 ms | 0 |
| /testar/ | mobile | 100 | 100 | 100 | 60 | 1,9 s | 20 ms | 0 |
| /testar/ | desktop | 100 | 100 | 100 | 60 | 0,4 s | 0 ms | 0 |
| /diagnostico/ | mobile | 100 | 100 | 100 | 60 | 1,9 s | 30 ms | 0 |
| /diagnostico/ | desktop | 100 | 100 | 100 | 60 | 0,4 s | 0 ms | 0 |
| /estresse/ | mobile | 99 | 100 | 100 | 60 | 2,1 s | 20 ms | 0 |
| /estresse/ | desktop | 100 | 100 | 100 | 60 | 0,5 s | 0 ms | 0 |
| /como-funciona/ | mobile | 100 | 100 | 100 | 60 | 1,9 s | 20 ms | 0 |
| /como-funciona/ | desktop | 100 | 100 | 100 | 60 | 0,4 s | 0 ms | 0 |

Ordenação nas colunas, explicações com o ícone "i", skeleton, CSP mais rígida e as duas travas novas não custaram desempenho. A troca de página leva de 20 a 64 ms, inclusive com 4G lento e CPU 4 vezes mais lenta, porque as páginas são buscadas antes do clique.
