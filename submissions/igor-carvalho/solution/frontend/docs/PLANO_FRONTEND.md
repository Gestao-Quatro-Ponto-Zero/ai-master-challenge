# Plano do frontend — G4 - Sales Priority (vendedor, MainV2)

Escopo: apenas a tela do vendedor da versão 2. v1, v3 e a visão do gestor ficam só no protótipo.

## 1. Princípios
- React 18 + TypeScript estrito; **somente classes** (`Component`/`PureComponent`), sem hooks (verificado por teste de arquitetura).
- Componentes de apresentação recebem dados e callbacks por props. Só `SellerPage` guarda estado e fala com a API.
- API atrás da interface `DealsApi`; dois adaptadores (`MockDealsApi`, `HttpDealsApi`). O formato do fio (snake_case) fica isolado em `HttpDealsApi`; o domínio é camelCase.
- Estado de filtros na URL (`history.replaceState`).
- Estados de carregamento, erro (com "Tentar de novo"), vazio e dados de exemplo em todas as telas.

## 2. Elementos da tela → componentes

| Elemento da tela | Componente |
|---|---|
| Cabeçalho, navegação, usuário | `AppHeader` |
| Título, subtítulo, data de referência, "dados de exemplo" | `PageTitle` |
| Abas "Meu dia" / "Todo o pipeline (N)" | `ViewTabs` |
| Aviso de uso + "Como a prioridade é calculada" | `UsageNotice`, `HowItWorks`, `Modal` |
| KPIs (Em foco, A revisar, Deals abertos, Valor esperado) | `KpiCards`, `KpiCard` |
| Filtros (busca, produto, prioridade, ordenar, "Só os seus deals", limpar) | `FiltersBar` |
| Faixas (Foco da semana, Decidir, Baixa prioridade, Prospecção, A revisar) | `BandTabs` |
| Ações em massa (encerrar/adiar, confirmação) | `BulkBar` |
| Tabela e linhas | `DealsTable`, `DealRow`, `ReasonChip` |
| Paginação e rodapé | `Pagination`, `ListFooter` |
| Painel de detalhe (lateral ou modal) | `DetailPanel`, `DealDetail`, `FunnelTimeline`, `QuickActions`, `SnoozeMenu`, `FeedbackSection` |
| Meu dia | `TodayView`, `DayProgress`, `TodayDealCard` |
| Erro / aviso com "Desfazer" | `ErrorBanner`, `Toast` |

## 3. Fluxo de dados
`SellerPage` lê a URL no construtor; `componentDidUpdate` regrava a URL e recarrega quando a chave da visão muda. Respostas antigas são descartadas (contadores de sequência) e há guarda de desmontagem. Ações (adiar/encerrar) → `applyAction` → toast com "Desfazer" (`undoAction`) → recarrega resumo e lista. Contadores dos KPIs e abas vêm de `GET /summary`, nunca de números fixos.

Telas largas (≥1100px): detalhe em painel lateral. Estreitas e "Meu dia": detalhe em modal (Esc fecha, foco preso e devolvido).

## 4. Integração com a API real (`backend/`, `/api/v1`)

**O front não contém regra de negócio; ver `/meta` e `/deals`.** Tudo que é regra (faixas de score, abas, limiares de dias, confiança, textos de ação, filtros, ordenação, totais) vem da API. Literais de regra só podem existir em `src/api/mock` (teste de arquitetura).

Adaptador: `src/api/HttpDealsApi.ts`. Rotas: `POST /auth/login`, `GET /me`, `GET /meta`, `GET /filters`, `GET /summary`, `GET /deals`, `POST|GET /deals/{id}/feedback`.

| Frontend | API |
|---|---|
| Login | `POST /auth/login {user_key}` → JWT; renova sozinho em 401 |
| Usuário | `/me`: `full_name`, `regional_office` |
| Limiares, níveis de prioridade, abas e ordem padrão | `/meta`: `thresholds`, `priority_levels`, `views`, `low_confidence_below_closed_deals`. Sem `/meta` a tela fica em "Carregando…" |
| Opções de produto | `/filters.products` |
| KPIs e contadores das abas | `/summary.views.<aba>.{count, expected_value}` |
| Lista | `GET /deals?view&priority&product&q&sort&order&page&page_size`; cada troca de aba/filtro/busca/ordem/página faz uma nova chamada. Ordem: score→`score`, valor esperado→`expected_value`, tempo→`age_days`; sem `sort` vale o padrão da aba |
| Aba do deal | `view` |
| Texto de prioridade | `priority_level` (só mapeado para cor) |
| Ação sugerida | `suggested_action` |
| Confiança | `confidence` + `confidence_reason` |
| Motivos | `reasons[].label`; `positive`→+, `negative`→−, tempo no funil negativo→alerta |
| Feedback | `worked`, `disagree` (+ comentário `reason:<motivo>`), `ignore` |

**TODO(api), sem endpoint hoje (estado local, não é regra de produto):**
1. Adiar e encerrar como perdido (escondem o deal neste navegador; totais ajustados localmente).
2. "Seu dia" no servidor (hoje `GET /deals?view=focus&sort=score&order=desc`: o dia é o topo do foco da semana).
3. Feedback com motivo estruturado (hoje em `comment`).
4. "Marcar feito" em Meu dia.
5. Último contato por deal (removido da tela).

## 5. Sugestões de usabilidade implementadas
Contadores e KPIs vindos da API; remoção de números inventados e rótulo "dados de exemplo"; motivo do "Discordo" e histórico; confirmação e desfazer nas ações destrutivas; adiar com prazos; seleção em massa só em "A revisar"; busca por ID/produto/conta; filtro de prioridade; limpar filtros; tamanho de página; ordenação clicável nos cabeçalhos; motivo da confiança baixa; aviso de conta faltando; estado vazio com saída; foco e Esc nos modais; URL compartilhável. Itens que dependem do backend estão na seção 4.

## 6. Plano de testes

| Camada | Arquivo | Cobre |
|---|---|---|
| Mock | `api/MockDealsApi.test.ts` | contagens, abas, busca, paginação, adiar/desfazer, hoje, feedback |
| HTTP | `api/HttpDealsApi.test.ts` | mapeamento de respostas reais (fixture), login e renovação, abas, feedback, adiar com validade, erros |
| API real | `api/live.integration.test.ts` | usuário, meta, deals x resumo, Seu dia, feedback ida e volta (pulado sem `G4_API_URL`) |
| Lib | `lib/*.test.ts` | URL (ida e volta, valores inválidos), formatação, tema |
| Tela | `pages/SellerPage.test.tsx` | Meu dia, pipeline, URL, erro e retry, probabilidade oculta (F7), modal/Esc, busca/limpar, ações em massa + desfazer, feedback |
| Arquitetura | `architecture.test.ts` | sem hooks, só classes (F1) |

Rodar: `npm test`. Contra a API real: `npm run test:integration` (`api/live.integration.test.ts`).

## 7. Critérios de aceite
F1 sem hooks · F2 filtros na URL · F3 carregando/erro/vazio · F4 acessibilidade (papéis, rótulos, foco, Esc) · F5 probabilidade oculta quando `show_probability=false` · F6 contadores vindos da API · F7 troca mock↔API só por variável de ambiente.

## 8. Riscos
Contrato ainda não implementado no backend (seção 4); fonte IBM Plex vem do Google Fonts (cair para fonte do sistema se offline); "feito" em Meu dia é local ao navegador.
