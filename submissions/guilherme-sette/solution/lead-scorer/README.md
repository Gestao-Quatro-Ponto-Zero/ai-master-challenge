# Challenge 003 — Lead Scorer

## Submissao - Solucao Implementada

Ferramenta funcional para priorizar oportunidades abertas de CRM e orientar a rotina de vendedores e gerentes. A solucao usa os dados reais do dataset, cria uma camada ETL padronizada, calcula um score operacional explicavel e entrega um front estatico com dois portais:

- **Vendedor:** fila de oportunidades priorizadas, score, acao recomendada, fit e motivos.
- **Gerente:** cenario de risco/roteamento atual e fila de aprovacoes para remanejamento ou revisao.

O score e uma prioridade operacional de 0 a 100, nao uma probabilidade calibrada de fechamento.

### Como Rodar

Na raiz do repositorio:

```bash
python3 -m pip install -r challenges/build-003-lead-scorer/requirements.txt

python3 challenges/build-003-lead-scorer/scripts/etl.py
python3 challenges/build-003-lead-scorer/scripts/seller_xray.py
python3 challenges/build-003-lead-scorer/scripts/seller_specialty_fit.py
python3 challenges/build-003-lead-scorer/scripts/score_pipeline.py
python3 challenges/build-003-lead-scorer/scripts/benchmark_score.py
python3 challenges/build-003-lead-scorer/scripts/validate_outputs.py
```

Servir o frontend:

```bash
cd challenges/build-003-lead-scorer/frontend
python3 -m http.server 4173
```

Abrir `http://127.0.0.1:4173/`.

### Arquivos da Solucao

- [SOLUTION.md](./SOLUTION.md): explicacao da solucao, score, roteamento e limitacoes.
- [PROCESS_LOG.md](./PROCESS_LOG.md): evidencias de uso de IA, iteracoes, erros e correcoes.
- [scripts/](./scripts): ETL, analises, score e validacao reproduzivel.
- [data/processed/](./data/processed): CSVs padronizados e outputs do score.
- [frontend/](./frontend): aplicacao estatica.
- [reports/project_critical_review.md](./reports/project_critical_review.md): auditoria critica do estado do projeto.
- [reports/score_benchmark.md](./reports/score_benchmark.md): benchmark historico simples contra baselines.
- [reports/frontend_visual_validation.md](./reports/frontend_visual_validation.md): screenshots e checks visuais do front.
- [reports/research_applicability.md](./reports/research_applicability.md): comparacao da pesquisa anexada com o escopo do desafio.
- [reports/research_sources/](./reports/research_sources): arquivos-fonte da pesquisa anexada pelo usuario.
- [reports/transcript_integrity_report.md](./reports/transcript_integrity_report.md): validacao do historico de conversa.

### Resumo da Logica

Componentes do score:

| Componente | Peso |
|---|---:|
| Valor economico | 20% |
| Fit vendedor-oportunidade | 25% |
| Timing / idade do deal | 20% |
| Stage operacional | 10% |
| Qualidade da conta / ICP | 10% |
| Contexto da carteira | 10% |
| Confianca dos dados | 5% |

Sinais principais: manter, consultar especialista, remanejar, revisao gerente, corrigir dados, ultima tentativa e nutricao.

### Benchmark Historico

O benchmark em `reports/score_benchmark.md` e um sanity check, nao uma validacao de forecast. Ele usa 70% das oportunidades fechadas mais antigas para construir taxas historicas e testa ranking nos 30% mais recentes.

Leitura honesta: o baseline por valor segue forte para captura de receita; o score V1 adiciona contexto operacional, fit vendedor-oportunidade, confianca dos dados e governanca. Portanto, a solucao deve ser apresentada como priorizacao RevOps explicavel, nao como maximizador estatistico puro de receita.

### Evidencia Visual

Screenshots atuais do front:

- [Portal do vendedor](./reports/frontend-current-seller.png)
- [Portal do gerente - Cenario](./reports/frontend-current-manager-scenario.png)
- [Portal do gerente - Aprovacoes](./reports/frontend-current-manager-approvals.png)

A validacao visual completa esta em [reports/frontend_visual_validation.md](./reports/frontend_visual_validation.md).

### Limitacoes Principais

- 68,2% das oportunidades abertas nao tem conta conhecida, reduzindo a confianca do score.
- Nao ha snapshots historicos reais; o score nao deve ser vendido como forecast calibrado.
- Fit vendedor-segmento e associativo, nao causal.
- Aprovacoes no frontend sao persistidas apenas em `localStorage`.
- Em producao seriam necessarios autenticacao, permissoes, integracao CRM e persistencia real.

---

**Área:** Vendas / RevOps
**Tipo:** Build (construir solução funcional)
**Time budget:** 4-6 horas

---

## Contexto

Você é o novo AI Master da área de **Vendas**. O time comercial tem 35 vendedores distribuídos em escritórios regionais, gerenciados por managers, trabalhando um pipeline de ~8.800 oportunidades. Hoje, a priorização é feita "no feeling" — cada vendedor decide quais deals focar com base na própria experiência e intuição.

A Head de Revenue Operations te chamou e disse:

> *"Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."*

Este é o challenge mais "mão na massa". O deliverable principal é **software funcionando** — não um documento.

---

## Dados disponíveis

Quatro tabelas de um CRM, todas interconectadas:

**Dataset:** [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) (licença CC0)

| Arquivo | O que contém | Registros | Campos-chave |
|---------|-------------|-----------|-------------|
| `accounts.csv` | Contas clientes — setor, receita, número de funcionários, localização, empresa-mãe | ~85 | `account` |
| `products.csv` | Catálogo de produtos com série e preço | 7 | `product` |
| `sales_teams.csv` | Vendedores com seu manager e escritório regional | 35 | `sales_agent` |
| `sales_pipeline.csv` | Pipeline completo — cada oportunidade com stage, datas, vendedor, produto, conta e valor de fechamento | ~8.800 | `opportunity_id` → liga tudo |

### Estrutura dos dados

```
accounts ←── sales_pipeline ──→ products
                   ↓
              sales_teams
```

O `sales_pipeline.csv` é a tabela central. Cada registro é uma oportunidade com:
- `deal_stage`: Prospecting, Engaging, Won, Lost
- `engage_date` / `close_date`: timeline do deal
- `close_value`: valor real de fechamento (0 se Lost)

---

## O que entregar

### 1. Solução funcional (obrigatório)

Construa algo que um vendedor possa usar. Não importa a tecnologia — importa que funcione.

**Exemplos de soluções válidas:**
- Aplicação web (Streamlit, React, HTML+JS, qualquer coisa)
- Dashboard interativo (Plotly Dash, Retool, Metabase)
- CLI tool ou script que gera relatório priorizados
- API que recebe dados de um deal e retorna score + explicação
- Planilha inteligente com fórmulas de scoring
- Bot que envia prioridades por Slack/email

**Requisitos mínimos:**
- Precisa **rodar** (não é mockup, wireframe ou PowerPoint)
- Precisa usar os **dados reais** do dataset
- Precisa ter **lógica de scoring/priorização** (não é só ordenar por valor)
- O vendedor precisa entender **por que** um deal tem score alto ou baixo

### 2. Documentação mínima (obrigatório)

- **Setup:** Como rodar a solução (dependências, comandos, URL)
- **Lógica:** Que critérios de scoring você usou e por quê
- **Limitações:** O que a solução não faz e o que precisaria pra escalar

### 3. Process log (obrigatório)

Evidências de como você usou IA para construir. Leia o [Guia de Submissão](../../submission-guide.md).

Este challenge é especialmente interessante para quem usa "vibe coding" — Cursor, Claude Code, Replit Agent, v0, etc. **Mostre o processo.**

---

## Critérios de qualidade

- A solução **funciona de verdade**? Dá pra rodar seguindo as instruções?
- O scoring faz sentido? Usa as features certas? Vai além do óbvio?
- O vendedor (não-técnico) consegue usar e entender?
- A interface ajuda a tomar decisão ou só mostra dados?
- O código é limpo o suficiente pra outro dev dar manutenção?

---

## Dicas

- A Head de RevOps não pediu ML perfeito. Pediu algo **útil**. Comece simples, itere.
- Deal stage, tempo no pipeline, tamanho da conta, produto e vendedor são features óbvias. O que mais importa? Olhe os dados.
- Um scoring baseado em regras + heurísticas, bem apresentado, vale mais que um XGBoost sem interface.
- **Explainability ganha.** Se o vendedor entender POR QUE o deal tem score 85, a ferramenta é 10x mais útil que um número sem contexto.
- Pense no uso real: o vendedor abre isso na segunda-feira de manhã. O que ele precisa ver?
- Bonus: se a solução tiver filtro por vendedor/manager/região, fica imediatamente mais útil.
