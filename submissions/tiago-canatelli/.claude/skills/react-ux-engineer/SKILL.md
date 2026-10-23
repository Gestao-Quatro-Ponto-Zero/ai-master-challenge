---
name: react-ux-engineer
description: Engenheiro front-end React e designer de UX do painel RavenStack (apps/dashboard). Use ao criar ou revisar telas, componentes shadcn/ui, layout, navegação, gráficos, estados de carregamento/erro/vazio, acessibilidade, a experiência do assistente de IA (prompts prontos editáveis, escolha de modelo, streaming, citações do "por quê"), a tela de conexão MCP e o acompanhamento de ingestão em tempo real.
---

# React + UX — Painel RavenStack

O painel existe para três pessoas tomarem decisão rápido: **CEO** (entender o porquê em 10 minutos), **CS** (saber quem ligar hoje) e **Dados** (confiar no que entrou no lake). Toda tela responde a uma pergunta dessas pessoas — se não responde, não entra.

Arquitetura, rotas e contratos: `docs/02-plano-tecnico.md` (seções 6 e 7). Padrões de código TypeScript, build e deploy: skill `python-software-engineer` (seção do painel). Gráficos: skill `dataviz`. Definições de KPI: skill `churn-business-analyst`.

## 1. Stack e estrutura

- Vite + React 18 + TypeScript strict · Tailwind · **shadcn/ui** (Radix por baixo) · lucide-react · TanStack Query · TanStack Table · Recharts · react-hook-form + zod · `@supabase/supabase-js`.
- Componentes shadcn instalados via CLI (`npx shadcn@latest add <componente>`), em `src/components/ui/` — não editar à mão sem motivo; customizar via tokens.
- Pastas: `src/pages/<rota>/`, `src/components/` (compartilhados: `KpiCard`, `DataTable`, `ChartCard`, `EmptyState`, `ErrorState`, `WhyPanel`, `SqlBlock`), `src/hooks/`, `src/lib/` (`supabase.ts`, `api.ts`, `format.ts`).
- Um hook por fonte de dados; nenhum componente chama Supabase direto.

## 2. Princípios de UX

1. **Resposta primeiro:** cada tela abre com a conclusão (número grande + frase), depois o gráfico, depois a tabela, depois o detalhe técnico.
2. **Todo número tem origem:** tooltip/ícone "de onde vem isso?" com a view do gold e a fórmula do dicionário de KPIs.
3. **Linguagem do usuário, não do banco:** "Contas que cancelaram", não `churn_events`. Termos técnicos só na área de Dados.
4. **Contas e dinheiro juntos:** onde houver contagem de contas, mostrar o MRR ao lado.
5. **Do insight à ação em 1 clique:** de um KPI para o segmento, do segmento para a fila de contas, da conta para a visão 360 e para "perguntar à IA sobre esta conta".
6. **Honestidade visual:** eixos começando em zero para barras, amostra pequena sinalizada ("n = 12"), correlação marcada como tal.
7. **Densidade adequada à persona:** CEO = poucas coisas grandes; CS = tabela densa com filtros; Dados = tudo, com busca.

## 3. Layout e navegação

- Shell: sidebar recolhível agrupada por persona (**Visão executiva** · **Customer Success** · **Produto** · **Dados** · **Assistente**), topbar com busca global (`Command` do shadcn, ⌘K: contas, tabelas, KPIs, prompts) e seletor de período.
- Filtros globais (período, plano, indústria, canal) na URL (`?periodo=2024-Q4&plano=Pro`) — links compartilháveis e botão voltar funcionando.
- Breadcrumb nas telas de detalhe.
- Responsivo: utilizável em tablet; no celular, pelo menos `/kpis`, `/risco` e `/assistente`.

## 4. Estados obrigatórios em toda tela

| Estado | Componente | Regra |
|---|---|---|
| Carregando | `Skeleton` no formato final | Nunca spinner de tela inteira |
| Vazio | `EmptyState` | Diz por quê e o que fazer ("Nenhuma ingestão ainda — rode `ravenlake ingest`") |
| Erro | `ErrorState` | Mensagem humana + botão tentar de novo + detalhe técnico recolhido |
| Dado desatualizado | badge | "Atualizado há 3 h · run #12" a partir de `ops.ingestion_runs` |

## 5. Telas-chave

**Ingestão (`/ingestao`)** — ao vivo via Realtime: card por run com status; por dataset uma linha com etapas raw → bronze → silver → gold (stepper), barra de progresso `rows_loaded / rows_read`, rejeitados em destaque, duração e bytes. Toast quando um run termina. Histórico em tabela.

**Catálogo (`/catalogo`)** — busca com destaque, filtro por camada, ficha da tabela (descrição, dono, linhas, atualização), colunas com tipo/descrição/nulos %/distintos/PII/chave, e linhagem visual raw → bronze → silver → gold.

**KPIs (`/kpis`)** — 4 `KpiCard` no topo (valor, variação, sparkline), depois os 3 gráficos do paradoxo (satisfação, uso por conta, logos × receita) cada um com uma frase-conclusão no título.

**Risco (`/risco`)** — `DataTable` ordenada por MRR em risco; colunas: conta, segmento, MRR, probabilidade (barra), top drivers (chips), ação sugerida; filtros, seleção em lote, exportar CSV, "perguntar à IA".

## 6. Experiência do assistente de IA (`/assistente`, `/prompts`)

- **Biblioteca de prompts** em cards agrupados por persona; busca; favoritos.
- Ao escolher um prompt: formulário gerado a partir de `variables` (zod), **editor do texto completo visível e editável antes de enviar**, com indicação "editado" e botão "restaurar padrão".
- Salvar edição como nova versão ou como prompt novo; histórico de versões com diff.
- **Seletor de modelo/provedor** (Claude por padrão; outros provedores aparecem só se configurados na API — ver plano técnico §7.3). Mostra custo/latência aproximados quando disponíveis.
- **Streaming** da resposta (SSE) com indicador de etapa: "consultando kpi_support_health…", "buscando nas análises…".
- Resposta renderizada nas 4 seções do contrato: **Resposta · Por quê · Confiança · Próxima ação**. O "Por quê" é um `WhyPanel`: cada evidência com número, view de origem e botão "ver query" (`SqlBlock`) ou "ver trecho" (fonte do RAG).
- Badge de confiança (alta / média / hipótese) com explicação no hover.
- Ações: copiar, exportar markdown, fixar no dashboard, avaliar 👍/👎 (grava em `app.ai_runs`).
- Atalhos contextuais: em qualquer conta/segmento/KPI, botão "Perguntar à IA" abre o assistente com o prompt certo e variáveis preenchidas.

## 6.1 Perfis, áreas e personas

- **Seletor de perfil** no assistente ("Analisar como: Financeiro ▾"); o perfil muda os prompts sugeridos e mostra um chip com a área na resposta.
- **Análise 360:** síntese no topo (concordâncias, **discordâncias destacadas**, ações por dono) e uma aba por área com a resposta daquela lente; progresso por perfil enquanto roda.
- **Editor de perfil (`/perfis`):** formulário (nome, pergunta central, KPIs em foco como multi-select do dicionário, fontes do RAG, prompts, tom) + editor das instruções; badge "personalizado" quando difere do padrão; histórico com diff e "restaurar padrão"; upload de documentos da área com status de indexação.
- **Navegação:** sidebar com **Geral**, **Áreas** (8 itens) e **Personas de cliente**; filtro de persona de cliente disponível em todo painel de área (matriz área × persona sem telas extras).
- **Ficha de persona de cliente:** cartão com quem é, tamanho (contas, MRR), por que sai, sinais de alerta e ação recomendada.

## 7. Tela de conexão MCP (`/conectar`)

- Mostra a URL do MCP e instruções copiáveis por cliente: Claude Code (`claude mcp add --transport http …`), Claude Desktop / claude.ai (conector personalizado), ChatGPT, Cursor, Gemini CLI e genérico (JSON de configuração).
- Botão "gerar token" (quando a API suportar tokens por usuário) e "testar conexão" que chama `/health` e lista as tools.
- Lista das tools e prompts disponíveis, lida do próprio MCP.

## 8. Visual

- Tema claro e escuro via tokens CSS do shadcn (`--background`, `--primary`…); nunca cores fixas em componentes.
- Paleta de dados da skill `dataviz`; vermelho só para risco/perda, verde só para ganho.
- Tipografia: números com `tabular-nums`; moeda `US$`, separadores pt-BR (`Intl.NumberFormat('pt-BR')`), datas `dd/MM/yyyy`.
- Espaçamento consistente (escala Tailwind 2/4/6/8); cards com o mesmo raio e sombra.

## 9. Acessibilidade e qualidade

- Contraste AA, foco visível, tudo navegável por teclado, `aria-label` em ícones-botão, gráficos com resumo textual e tabela alternativa.
- Interações < 100 ms de feedback; listas grandes paginadas ou virtualizadas.
- Antes de commit: `tsc --noEmit`, lint, `npm run build`; conferir a tela no navegador nos dois temas e numa largura de celular.
- Screenshot de cada tela nova em `process-log/screenshots/` (evidência).
