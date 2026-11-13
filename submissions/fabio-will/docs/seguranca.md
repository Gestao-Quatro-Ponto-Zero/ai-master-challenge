# Segurança: modelo de ameaça e pentest

Pentest feito em 13/11/2026, antes de qualquer publicação. Dois alvos: a **política de roteamento**, que alguém pode tentar enganar, e o **console**, que roda no navegador de quem usa. Tudo aqui é reproduzível pelos scripts citados.

## O que existe para atacar

| Superfície | O que é | Quem controla a entrada |
|---|---|---|
| Teste ao vivo | Campo de texto que o modelo lê no navegador | Quem usa o console |
| Arquivo do modelo | `public/model/router.<hash>.json`, baixado pelo navegador | O build; em trânsito, a rede ou um CDN |
| Páginas | HTML estático, sem login, sem API, sem banco | O build |
| Política de roteamento | Modelo e travas que decidem automático, assistido ou humano | Quem escreve o ticket |
| Cadeia de build | Dependências npm e Python fixadas | Os registros de pacote |

## Modelo de ameaça

| Ameaça | Exemplo concreto | Controle | Evidência |
|---|---|---|---|
| Evasão do modelo (OWASP ML01) | Colar palavras de Hardware num ticket de RH para ele seguir sozinho para outra fila | Travas de trecho e de sequência | `05_adversarial.py`, tabela S1 abaixo |
| Script injetado (XSS) | Ticket com `<img onerror>` ou `<script>` | React escapa o texto; CSP com hash de cada script legítimo | Pentest `xss-input` e `csp-injection` |
| Clickjacking | Console dentro de um iframe de outro site | `X-Frame-Options: DENY` e `frame-ancestors 'none'` | Pentest `clickjacking` |
| Vazamento de dado | Texto do ticket sair do navegador ou ir para terceiro | Modelo roda no navegador; `connect-src 'self'`; nenhuma chamada depois de digitar | Pentest `egress` |
| Modelo adulterado | Trocar o arquivo no caminho para automatizar tudo | Hash SHA-256 no nome e conferido antes do uso; validação de estrutura | `tests/model-loader.test.ts` e pentest `model-tampering` |
| Negação de serviço no navegador | Colar meio megabyte de texto | Corte em 4.000 caracteres antes do modelo | Pentest `oversized-input` |
| Arquivo sensível exposto | `.env`, `.git`, configuração, mapa de código | Build estático só com `out/`; sem mapa de código em produção | Pentest `exposed-files` |
| Rastreamento | Cookie ou storage com dado do usuário | Nenhum cookie, nenhum storage | Pentest `no-tracking` |
| Dependência vulnerável | Pacote com falha conhecida | Versões fixas e auditadas | `npm audit` e `pip-audit`: 0 |
| Envenenamento no retreino (OWASP ML02) | Agente que corrige errado de propósito para ensinar o modelo | Retreino só com rótulo confirmado; auditoria cega de 2% | Operacional: não testável no protótipo |
| Injeção de prompt | Ticket que dá ordem para um LLM | Não se aplica: o console não usa LLM. Na fase de rascunho, o texto do cliente entra como dado, e o LLM não tem ferramenta | Desenho na página Como funciona |

## S1: ataque ao modelo

Tickets do conjunto de teste, com palavras de outra fila coladas. Conta como escape a política inteira mandar o ticket sozinho para uma fila que não é a dele. "Antes" é a política sem as duas travas que o pentest criou.

| Fila | Ataque | Antes do pentest | Com as travas novas |
|---|---|---|---|
| Direitos de administrador (264 tickets) | 5 palavras comuns no fim | 42% | 15% |
| Direitos de administrador | 12 palavras escolhidas por quem conhece o modelo (pior fila-alvo) | 86% | 16% |
| Direitos de administrador | Uma palavra intercalada entre cada palavra | 96% | 2% |
| RH (1.638 tickets) | 5 palavras comuns no fim | 42% | 10% |
| RH | 12 palavras escolhidas por quem conhece o modelo (pior fila-alvo) | 91% | 10% |
| RH | Uma palavra intercalada entre cada palavra | 100% | 7% |

**Como as travas funcionam.** A de trecho lê o ticket também em janelas de 8 palavras: se uma janela tem probabilidade de 0,70 ou mais numa fila sensível e a fila prevista não é sensível, uma pessoa confirma. Palavras coladas diluem o ticket inteiro, não a janela. A de sequência mede quantos pares de palavras vizinhas o modelo conhece: palavra intercalada destrói esses pares, e abaixo do percentil 2 da validação (0,094) o ticket vai para humano.

**Custo.** 6,5 pontos de automação (de 64% para 57%) e rejeição indevida de 2,2% para 4,1%. A precisão do automático subiu de 96,0% para 96,2%. Os parâmetros foram escolhidos na validação; o teste só mediu.

**O que fica exposto.** Com 5 palavras coladas, ainda escapam cerca de 15% dos pedidos de administrador e 10% dos de RH. O dano é de rota, não de acesso: nenhuma permissão é concedida pela fila, e a auditoria cega e a taxa de override pegam o padrão. No Dataset 2, "Direitos de administrador" é sobre instalar software e atualizar Outlook e Windows; as palavras "admin" e "rights" aparecem pelo menos 10 vezes mais em outras filas, então uma trava por palavra-chave custaria automação e não pegaria o ataque.

## S2: ataque ao console

Rodado num Chrome real, primeiro contra o servidor local que aplica os mesmos cabeçalhos do `vercel.json` (`npm run serve`) e depois contra a URL publicada. Resultado: **10 de 10 contidos nos dois**. Relatórios brutos em [`../process-log/security/pentest-local.json`](../process-log/security/pentest-local.json) e [`../process-log/security/pentest-vercel.json`](../process-log/security/pentest-vercel.json).

| Severidade | Ataque | Esperado | Resultado |
|---|---|---|---|
| Extremamente crítico | 6 cargas de XSS coladas como ticket | Nada executa; tudo aparece como texto | Contido: 6 cargas, 0 execução, 0 diálogo |
| Extremamente crítico | Script inline, handler inline, script de terceiro e eval injetados no DOM | Os quatro bloqueados pela CSP | Contido: 4 de 4 bloqueados; eval: bloqueado |
| Extremamente crítico | Trocar o modelo no caminho para automatizar tudo | O console recusa o arquivo e não decide nada | Contido: arquivo recusado; nenhuma decisão |
| Crítico | Cabeçalhos de segurança em todas as páginas | Todos presentes, sem x-powered-by | Contido: 5 páginas × 8 cabeçalhos |
| Crítico | Embutir o console num iframe de outro site | O navegador recusa o quadro | Contido: quadro recusado pelo navegador |
| Crítico | Digitar um ticket com dado pessoal no teste ao vivo | 0 requisição depois de digitar, 0 terceiro, marcador em lugar nenhum | Contido: 0 requisição depois de digitar; 0 de terceiros |
| Médio | Navegar por todas as telas e usar o teste ao vivo | 0 violação de CSP e 0 erro de console | Contido: 0 violação, 0 erro |
| Médio | Colar 0,5 MB de texto no ticket | Texto cortado em 4.000 caracteres e decisão em menos de 1 s | Contido: 4.000 de 468.912 caracteres; decisão em 16 ms |
| Médio | 8 arquivos sensíveis e 7 mapas de código | Nenhum servido | Contido: 15 caminhos, 0 servido |
| Leve | Usar todas as telas e procurar cookie, storage e indexação | Sem cookie, sem storage, fora de buscador | Contido: sem cookie, sem storage, noindex |

## Como a CSP fecha script injetado

O export estático precisa de alguns scripts inline para iniciar a página, então a CSP do cabeçalho permite inline. Depois do build, [`scripts/csp-hashes.mjs`](../solution/app/scripts/csp-hashes.mjs) calcula o SHA-256 de cada script inline de cada página e grava uma segunda CSP num `<meta>`. O navegador aplica as duas: só roda o script inline cujo hash está na lista. O cabeçalho continua cuidando do que o `<meta>` não carrega, como `frame-ancestors`. `eval` fica bloqueado nas duas.

## Cadeia de dependências

- npm: versões exatas (`save-exact`), `npm audit` com 0 vulnerabilidade. A ferramenta de pentest entrou primeiro como `puppeteer-core` 24.40.0, que puxava pacotes com falha alta; ficou a 25.16.0, sem alerta.
- Python: versões fixas em `requirements.txt`, `pip-audit` com 0 vulnerabilidade depois de trocar o pytest 8.3.4 (PYSEC-2026-1845) pelo 9.0.3.

## Segredo e dado pessoal

- Varredura dos 78 arquivos que seriam publicados: nenhuma chave, senha, token, IP, e-mail, nome de cliente ou atribuição de ferramenta. Um arquivo de controle com itens plantados prova que os padrões detectam o que procuram.
- Modelo publicado: 10 mil termos, nenhum com sequência de 5 ou mais dígitos. Fila de exemplo: nenhum e-mail, URL ou número longo.

## O que falta para produção

- Login (SSO) na fila do agente e trilha de auditoria por decisão.
- A trava de histórico parecido atrás de uma API própria, com o índice de tickets fora do navegador.
- Rodar `npm run pentest -- <url>` contra a URL publicada a cada deploy (feito no primeiro deploy: 10 de 10).
- `style-src 'unsafe-inline'` continua: as barras de probabilidade usam estilo inline. Estilo injetado não executa código; o risco residual é visual.

## Como reproduzir

```bash
cd solution/analysis && ../.venv/bin/python 05_adversarial.py   # S1
cd ../app && npm run build && npm run serve                      # terminal 1
npm run pentest -- http://localhost:4180                          # terminal 2, S2
npm audit && uvx --python 3.12 --from pip-audit pip-audit -r ../analysis/requirements.txt
```

## Referências

- OWASP Machine Learning Security Top 10 (2023): ML01, manipulação de entrada; ML02, envenenamento de dado.
- Lowd, D. e Meek, C. (2005). Good Word Attacks on Statistical Spam Filters. CEAS. É o mesmo ataque, em filtro de spam: colar palavras "boas" para escapar do classificador.
- Biggio, B. e Roli, F. (2018). Wild Patterns: Ten Years After the Rise of Adversarial Machine Learning. Pattern Recognition.
