# Validação de localização e anonimização

## Resultado

**Gate: PASS.** A interface do JourneyGraph foi validada integralmente em português do Brasil, com mensagens controladas, formatação pt-BR, perfis anônimos e sem alteração da lógica analítica ou das métricas governadas.

## Contrato validado

- `lang="pt-BR"`, metadata, navegação, estados, tooltips, disclosures e rótulos de acessibilidade em português.
- Números, percentuais e datas formatados em pt-BR; valores analíticos preservados.
- Tradução por mensagens completas e mapas explícitos de enums/status; valores desconhecidos são preservados sem substituição parcial.
- `account_key`, IDs de contas e chaves de padrões usados somente internamente; a interface mostra perfis anônimos controlados.
- Evidência histórica e descritiva, revisão humana, MRR associado e hipóteses não testadas permanecem explícitos.

## Revisão por rota

| Rota | Idioma e acentuação | Layout e responsividade | Acessibilidade | Métricas e limites | Estado/console | Screenshot |
|---|---|---|---|---|---|---|
| `/` | PASS | PASS em desktop/tablet/mobile | landmarks, links e CTA nomeados | 500; 35.586; 13.927; 4.221; 435; 43; 7; 8 preservados | zero erro | `01-executive-overview.png` |
| `/quality` | PASS | PASS; eixos e rótulos legíveis | resumo textual dos gráficos | cobertura, quarentena e limitações preservadas | zero erro | `02-data-quality.png` |
| `/journeys` | PASS | PASS; filtros e timeline responsivos | selects rotulados e estado vazio testado | três perfis anônimos; sem chaves de conta ou padrões | zero erro | `03-journey-explorer.png` |
| `/graph` | PASS | PASS; grafo reduzido e painel lateral legíveis | visualização com nome alternativo e controles rotulados | 5 nós/16 arestas iniciais; limite descritivo visível | zero erro | `04-journeygraph.png` |
| `/watchlist` | PASS | tabela desktop e cards mobile aprovados | filtros, paginação e diálogo nomeados | 500 contas, 1.609 itens, 467 pendências; revisão humana obrigatória | estado vazio e zero erro | `05-watchlist.png` |
| `/experiments` | PASS | PASS; cards e detalhe responsivos | botões e diálogo nomeados | oito hipóteses não testadas; amostra e limite de execução visíveis | zero erro | `06-experiment-lab.png` |
| `/governance` | PASS | PASS; checklist e painéis legíveis | controles semânticos e listas | 97 decisões; proteções e proibições preservadas | zero erro | `07-governance.png` |
| `/demo` | PASS | PASS em três perfis de viewport | progresso e botões anterior/próxima nomeados | oito etapas e três perfis anônimos | zero erro | não aplicável |
| `/methodology` | PASS | PASS em três perfis de viewport | disclosures e hierarquia de títulos | hashes, commit-base e limites técnicos preservados | zero erro | não aplicável |

## Evidência de validação

| Gate | Resultado |
|---|---|
| ESLint | PASS, zero warnings/erros |
| TypeScript | PASS |
| Vitest | PASS, 18/18 |
| Next.js build | PASS, 10 rotas estáticas incluindo not-found |
| Playwright | PASS, 36/36 em desktop, tablet e mobile |
| Console do navegador | zero erros nas nove rotas |
| Requisições locais `/data/` | zero falhas |
| Overflow horizontal desktop | zero nas nove rotas |
| Chaves `acct_*` renderizadas | zero |
| Chaves `pattern_*` renderizadas | zero |
| Fragmentos da interface antiga em inglês | zero nas superfícies verificadas |
| Screenshots | sete regenerados e revisados visualmente |

## Revisão visual

Os sete screenshots aprovados foram regenerados a partir do build final. A revisão confirmou hierarquia, acentuação, contraste, rótulos, separadores numéricos, escalas, limites, anonimização e legibilidade do grafo. Dois problemas encontrados na revisão preliminar foram corrigidos antes da recaptura: truncamento arbitrário de rótulos de status e exposição visual de chaves internas de padrões.

## Limites preservados

A demonstração usa snapshot histórico fixo até 31 de dezembro de 2024. Não há previsão, probabilidade individual, receita em risco, recomendação automática, decisão por IA, contato com clientes, intervenção executada ou resultado causal. O modo local não implementa autenticação, dados ao vivo, observabilidade de produção ou integrações de saída.
