# Walkthrough — Como Construí o Lead Scorer com IA

**Candidata:** Mariana Peixoto Coelho
**Challenge:** 003 — Lead Scorer
**Ferramentas de IA:** Claude Code + Stitch (Google) + Antigravity Kit

---

## Etapa 1 — Setup e organização com Claude Code

Comecei definindo a estrutura do projeto com Claude Code. A IA recomendou a Opção B — pasta dedicada com seções separadas para evidências, análise e assets.

![Estrutura de pastas criada pelo Claude Code](screenshots/06_chat_estrutura_pastas.png)

---

## Etapa 2 — Design visual com Stitch

Antes de codar, pedi ao Claude Code para criar um prompt detalhado para o Stitch (Google AI) com especificações de UX/UI: tema dark neon, 4 telas, badges de score, filtros por região/manager/vendedor.

![Claude Code escrevendo o prompt para o Stitch](screenshots/07_chat_prompt_stitch_criado.png)

O Stitch gerou múltiplas variações. Escolhi o estilo neon/cyberpunk — decisão curatorial minha.

![Variações geradas pelo Stitch](screenshots/05_stitch_variations_geradas.png)

### Designs finais escolhidos

![Dashboard Principal — design Stitch](screenshots/01_stitch_main_dashboard.png)

![Empty State — design Stitch](screenshots/02_stitch_empty_state.png)

![Manager View — design Stitch](screenshots/03_stitch_manager_view.png)

![Deal Breakdown — design Stitch](screenshots/04_stitch_deal_breakdown.png)

---

## Etapa 3 — Antigravity Kit e ferramentas

Utilizei o [Antigravity Kit](https://github.com/vudovn/antigravity-kit.git) como base de agentes para potencializar o Claude Code. Também documentei todas as ferramentas usadas no processo.

![Inclusão do Antigravity Kit na submissão](screenshots/08_chat_antigravity_kit.png)

![Tabela de ferramentas usadas](screenshots/09_chat_ferramentas_usadas.png)

---

## Etapa 4 — Workflow documentado

Registrei as 9 etapas do processo de construção, do briefing ao build final.

![Workflow em 9 etapas](screenshots/10_chat_workflow.png)

---

## Etapa 5 — Decisões humanas vs. IA

A parte mais importante: o que eu adicionei que a IA sozinha não faria — data de referência, escolha de explicabilidade sobre ML complexo, threshold de priorização, curadoria do design.

![O que eu adicionei que a IA sozinha não faria](screenshots/11_chat_decisoes_humanas.png)

---

## Resultado — Sistema funcionando

### Dashboard principal (2.089 deals ativos)

![Dashboard todos os deals ativos](screenshots/12_dashboard_todos_ativos.png)

### Filtro por Engajamento

![Filtro Engajando — 1.589 deals](screenshots/13_dashboard_filtro_engajando.png)

### Filtro por Prospecção

![Filtro Prospecção — 500 deals](screenshots/14_dashboard_filtro_prospeccao.png)

### Filtros e dropdowns

![Dropdown de Regiões — Central, Leste, Oeste](screenshots/15_dashboard_dropdown_regioes.png)

![Dropdown de Managers](screenshots/16_dashboard_dropdown_managers.png)

![Dropdown de Vendedores com scroll](screenshots/17_dashboard_dropdown_vendedores.png)

![Dropdown de Ordenação](screenshots/18_dashboard_dropdown_ordenacao.png)

### Painel de detalhes do deal

![Detalhes do deal — score 69/100 com fatores explicados](screenshots/19_dashboard_deal_detalhes_score.png)

![Agente de IA estratégico com recomendação personalizada](screenshots/20_dashboard_deal_agente_ia.png)

---

## Como rodar

```bash
cd submissions/mariana-peixoto/solution/web
npm install
npm run dev
# Acesse: http://localhost:3000/lead-scorer
```

---

*Walkthrough escrito em: 2026-03-24*
