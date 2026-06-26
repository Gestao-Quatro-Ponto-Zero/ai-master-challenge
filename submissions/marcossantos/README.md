# Submissão — Marcos Santos — Challenge 003 — Lead Scorer

## Sobre mim

- **Nome:** Marcos Santos
- **LinkedIn:** https://www.linkedin.com/in/marcos-santosss/
- **Challenge escolhido:** 003 — Lead Scorer · Vendas / RevOps

---

## Executive Summary

Construí o Lead Scorer, uma plataforma web completa de priorização de deals para o time de vendas. A solução vai além do pedido: além do dashboard com scoring explicável, implementei autenticação JWT com roles, alertas automáticos com notificação por email, histórico de contatos que alimenta o score em tempo real, e analytics para managers — tudo com código limpo e separação de responsabilidades clara. O resultado é uma ferramenta que um vendedor abre na segunda-feira de manhã e sabe exatamente onde focar, com explicação do porquê de cada score.

---

## Solução

### Abordagem

Antes de escrever qualquer código, discuti a arquitetura com IA e revisei os critérios de qualidade do challenge para identificar gaps. A primeira proposta tinha só features óbvias (stage, valor, tamanho da conta) — revisamos antes de codar e adicionamos 3 features não-óbvias que fazem a diferença real no scoring.

Stack escolhida: **Python + FastAPI** no backend (fit natural com pandas para os CSVs), **React** no frontend. Decisão pragmática para demo local: menos boilerplate, setup rápido, pandas é a ferramenta certa para o trabalho.

### Resultados / Findings

**Scoring engine com 6 fatores (0–100 pts):**

| Fator | Peso | Por que importa |
|---|---|---|
| Stage Score | 25 pts | Engaging > Prospecting — mais perto do fechamento |
| Velocity ⭐ | 25 pts | Compara vs. média histórica de Won deals *do produto específico* |
| Account Fit | 20 pts | Porte + setor vs. perfil de contas que fecham |
| Product Win Rate ⭐ | 15 pts | GTX Pro fecha 65% vs MG Special 30% nos dados reais |
| Agent Performance ⭐ | 15 pts | Win rate histórico do vendedor responsável |
| Notes Activity ⭐ | 10 pts | Contato recente documentado prediz engajamento |

Os fatores marcados com ⭐ vão além do óbvio. O Velocity Score é o mais impactante: em vez de uma média global, compara o deal contra a média histórica de Won deals **daquele produto específico** — isso captura esfriamento contextualizado.

**O que foi construído além do mínimo:**

- **JWT + Roles** — agent vê só os próprios deals, manager vê o time, admin vê tudo. Filtro automático na API baseado no token.
- **Senhas bcrypt** — work factor 12, migração automática no startup.
- **Sistema de alertas** — scheduler assíncrono a cada 15min detecta 4 tipos de alerta (deal parado, deal crítico, alto valor em risco, vendedor sem Engaging). Deduplicação automática.
- **Notificação por email** — alerta crítico dispara email imediato via Gmail SMTP. Resumo diário enviado no horário configurado com top 5 deals e KPIs.
- **Deal Notes** — vendedor registra contatos no deal e o score atualiza automaticamente. Histórico completo no painel lateral.
- **Analytics para manager** — 3 visões: ranking de vendedores com status de coaching, funil de conversão por stage/produto, deals em risco por região.
- **Interface CRM** — paleta azul-marinho profissional, score bars inline na tabela, painel deslizante com breakdown fator a fator.

**Rotas de API:** 22 endpoints organizados em 7 módulos (data, scoring, auth, alerts, notes, analytics, notifications).

### Recomendações

Para o time de RevOps usar essa ferramenta em produção, as prioridades seriam:

1. Conectar ao CRM real (Salesforce/HubSpot) via webhook — elimina o CSV estático
2. Migrar para PostgreSQL — notas e alertas precisam de persistência real
3. Treinar um modelo XGBoost nos dados históricos usando as mesmas features como baseline — manter SHAP values para preservar a explainability que já existe
4. Adicionar script de sincronização de usuários a partir do CRM — hoje o `users.json` precisa ser editado manualmente

### Limitações

- Pipeline reflete snapshot dos CSVs no startup — sem atualização em tempo real
- Notas e alertas persistem em JSON — reiniciar o servidor não perde dados, mas não é banco de dados
- JWT sem refresh token — sessão expira em 8h
- `users.json` precisa ter os nomes dos agentes exatamente iguais aos do CSV para os filtros por role funcionarem

---

## Process Log — Como usei IA

> **Ferramenta principal:** Claude (Anthropic) via claude.ai — utilizado como pair programmer do início ao fim.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (claude.ai) | Arquitetura, geração de código, debugging, documentação |

### Workflow

1. **Apresentei o problema e pedi arquitetura** — não "gere o código", mas "como devemos estruturar isso". Discutimos stack, separação de módulos e trade-offs antes de qualquer código.
2. **Revisei os critérios de qualidade com a IA antes de codar** — identificamos que a primeira proposta tinha só features óbvias. Revisamos a arquitetura para incluir features não-óbvias e explainability real.
3. **Geração módulo por módulo** — loader → factors → engine → main → auth → alerts → notes → analytics → notifications → frontend. Cada módulo discutido antes de implementado.
4. **Debugging de erros reais no Windows** — colei as mensagens de erro do terminal e recebi causa + solução diretamente (pandas não compilava, uvicorn não encontrado, PYTHONPATH, DATA_DIR errado).
5. **Iteração contínua** — a cada módulo novo, revisamos o que já existia para manter consistência arquitetural.

### Onde a IA errou e como corrigi

- **DATA_DIR apontava para o lugar errado** — a IA calculou o path relativo com base em uma estrutura de pastas que eu não tinha. Corrigi para `Path(__file__).parent` ao identificar o erro no terminal.
- **`users.json` com nomes fictícios** — os agentes precisam bater exatamente com os nomes nos CSVs do Kaggle. A IA gerou nomes plausíveis mas que não existiam no dataset. Corrigi manualmente consultando o `sales_teams.csv`.
- **Import circular no fator de notas** — `factor_notes_activity()` importava `notes/store.py` no topo do módulo, causando circular import. Corrigi movendo o import para dentro da função.

### O que eu adicionei que a IA sozinha não faria

- **Decisão de stack** — a IA aceitou minha sugestão de Java/Spring Boot mas argumentou tecnicamente por Python + FastAPI. Eu avaliei o argumento e concordei — esse julgamento foi meu.
- **Priorização das features** — a IA sugeriu ML (XGBoost) como opção. Decidi manter scoring por regras porque entendi que explainability vale mais que acurácia para esse público específico.
- **Sequência de desenvolvimento** — decidir a ordem dos módulos (auth antes de analytics, notes antes de email) foi julgamento meu sobre o que desbloqueava o quê.
- **Escopo além do mínimo** — bcrypt, email com digest diário, analytics para manager — foram decisões minhas de ir além do que o challenge pedia.

---

## Evidências

- [x] **Narrativa escrita** — PROCESS.md com linha do tempo completa, decisões e debugging documentados
- [x] **Git history** — commits mostrando evolução da solução na branch `submission/marcossantos`
- [x] **Código funcional** — backend + frontend completos na pasta `submissions/marcossantos/`

---

*Submissão enviada em: junho de 2026*