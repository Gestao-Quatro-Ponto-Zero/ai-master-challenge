# PRD — Lead Scorer (Challenge 003)

**Produto:** Lead Scorer — Ferramenta de priorização de pipeline para vendedores
**Autor:** Victor Almeida
**Data:** 21 de março de 2026
**Contexto:** Submissão para processo seletivo de AI Master — G4 Educação

---

## 1. Visão Geral

Aplicação web que permite ao vendedor visualizar seu pipeline de oportunidades com **scoring inteligente**, entender **por que** cada deal tem determinada prioridade, e receber **recomendações de próxima ação**. O objetivo é substituir a priorização por "feeling" por dados acionáveis.

**Princípio central:** útil > sofisticado. Scoring baseado em regras e heurísticas calibradas com dados reais, bem apresentado, vale mais que ML sem interface.

---

## 2. Problema

### Situação atual
- 35 vendedores, ~8.800 oportunidades no pipeline
- Cada vendedor lida com ~250 deals em média
- Priorização feita por intuição — vendedor foca no que "sente" que vai fechar
- Resultado: tempo queimado em deals mortos + deals bons esfriando por falta de follow-up

### O que a Head de RevOps pediu
> "Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar."

### Diagnóstico do pipeline (dados reais)
- Pipeline massivamente inflado: deals em Engaging têm mediana de **165 dias** (referência Won: 57 dias)
- 96.7% dos deals ativos em Engaging já passaram da mediana de velocidade dos Won
- Contas com múltiplos losses (Hottechi: 82, Kan-code: 72, Konex: 63)
- Win Rate geral: **63.2%** (deals fechados)

---

## 3. Usuários e Personas

| Persona | Necessidade | Como usa a ferramenta |
|---------|-------------|----------------------|
| **Vendedor** | Saber onde focar na segunda-feira de manhã | Abre, vê seus deals rankeados por score, entende por que cada um está ali, sabe qual ação tomar |
| **Manager** | Visão do time, identificar deals zumbis, limpar forecast | Filtra por equipe, vê deals zumbis que inflam pipeline, identifica vendedores com deals parados |
| **Head RevOps** | Visão macro do pipeline por região/produto | Filtra por região/escritório, analisa saúde geral do pipeline |

---

## 4. Modelo de Dados

### Fonte
Dataset: **CRM Sales Predictive Analytics** (Kaggle, licença CC0)

### Tabelas

| Arquivo | Conteúdo | Registros | Campos-chave |
|---------|----------|-----------|--------------|
| `accounts.csv` | Contas clientes — setor, receita, funcionários, localização | ~85 | `account` |
| `products.csv` | Catálogo de produtos com série e preço | 7 | `product` |
| `sales_teams.csv` | Vendedores com manager e escritório regional | 35 | `sales_agent` |
| `sales_pipeline.csv` | Pipeline completo — oportunidades com stage, datas, vendedor, produto, conta e valor | ~8.800 | `opportunity_id` |

### Relações
```
accounts ←── sales_pipeline ──→ products
                   ↓
              sales_teams
```

`sales_pipeline` é a tabela central. Cada registro é uma oportunidade.

### Peculiaridades dos dados

- **Prospecting:** sem `engage_date`, sem `close_date`, sem `close_value` (tudo null)
- **Engaging:** tem `engage_date`, mas sem `close_date` e `close_value` (null)
- **Won:** `close_value` = valor real do fechamento
- **Lost:** `close_value` = 0
- **Data de referência** para cálculos: `2017-12-31` (data máxima do dataset)
- **Revenue** das contas em milhões de USD ($4.5M a $11.7B)
- Diferença de valor entre produtos: **486x** (GTK 500: $26.768 vs MG Special: $55)
- Win rates entre produtos são surpreendentemente similares (~60-65%)

### Produtos

| Produto | Preço | Win Rate |
|---------|-------|----------|
| GTK 500 | $26.768 | 60.0% |
| GTX Plus Pro | $5.482 | 64.3% |
| GTXPro | $4.821 | 63.6% |
| MG Advanced | $3.393 | 60.3% |
| GTX Plus Basic | $1.096 | 62.1% |
| GTX Basic | $550 | 63.7% |
| MG Special | $55 | 64.8% |

---

## 5. Algoritmo de Scoring

### Score Final (0-100)

```
SCORE = Base (Stage)        × 30%
      + Valor Esperado      × 25%    [log-scaled do close_value]
      + Velocidade          × 25%    [decay por tempo no stage]
      + Seller-Deal Fit     × 10%    [win rate vendedor × setor]
      + Saúde da Conta      × 10%    [histórico de wins/losses]
```

### 5.1 Base — Deal Stage (peso: 30%)

| Stage | Score base |
|-------|-----------|
| Prospecting | 30 |
| Engaging | 70 |

Deals Won/Lost não recebem score (já estão resolvidos).

### 5.2 Valor Esperado (peso: 25%)

Curva logarítmica para evitar que mega-deals dominem:

```
value_component = log(1 + close_value) / log(1 + max_value)
```

Para deals em Prospecting (sem `close_value`): usar preço de lista do produto como proxy.

### 5.3 Velocidade / Decay por Tempo (peso: 25%)

**Calibração com dados reais:**
- Mediana Won (Engaging → Close): **57 dias**
- P75: 88 dias | P90: 106 dias
- Deals ativos em Engaging: mediana de **165 dias**

**Achado contra-intuitivo:** deals que fecham entre 90-150 dias têm WR mais alta (70-75%) que deals de 0-15 dias (56%). O decay deve começar no **P75 (88 dias)**, com decaimento forte após **120 dias**.

```
ratio = dias_no_stage / referencia_stage

if ratio <= 1.0:  decay = 1.0       (saudável)
if ratio 1.0-1.2: decay = 0.85      (atenção)
if ratio 1.2-1.5: decay = 0.60      (alerta)
if ratio > 1.5:   decay = 0.30      (candidato a zumbi)
if ratio > 2.0:   decay = 0.10      (quase morto)
```

**Referências por stage:**
- Prospecting: usar mediana de dias em Prospecting dos deals que avançaram
- Engaging: **88 dias** (P75 dos Won)

### 5.4 Seller-Deal Fit (peso: 10%)

Multiplicador baseado no win rate do vendedor **naquele setor específico** vs média do time:

```
seller_sector_winrate = wins do vendedor no setor / total dele no setor
team_sector_winrate = wins do time no setor / total do time no setor

if vendedor tem >= 5 deals no setor:
    fit_multiplier = seller_sector_winrate / team_sector_winrate
else:
    fit_multiplier = 1.0  (dados insuficientes → usa média)
```

**Validação com dados:** Markita Hansen tem 90.5% WR em entertainment mas 35.7% em technology — a mesma vendedora performa radicalmente diferente por setor. O fit importa.

### 5.5 Saúde da Conta (peso: 10%)

Baseado no histórico de wins/losses da conta:

```
account_winrate = wins da conta / total de deals fechados da conta

if conta tem >= 3 deals fechados:
    health_score = account_winrate normalizado
else:
    health_score = 0.5  (neutro, dados insuficientes)
```

Penalização extra para contas com múltiplos losses recentes.

---

## 6. Funcionalidades

### 6.1 Pipeline View (obrigatório)
- Tabela de deals ativos rankeados por score
- Colunas: Score, Deal, Conta, Produto, Valor, Stage, Dias no Stage, Vendedor
- Código de cores por faixa de score (verde/amarelo/vermelho)

### 6.2 Score + Explicação (obrigatório)
- Score numérico (0-100) para cada deal ativo
- Explicação textual dos fatores que compõem o score
- Exemplo: *"Score 72 — Deal em Engaging há 45 dias (saudável). Valor alto (GTK 500). Seu WR neste setor está acima da média do time."*

### 6.3 Next Best Action (obrigatório)
Recomendações baseadas nos fatores do score:

| Condição | Ação sugerida |
|----------|---------------|
| Deal parado > média do stage | "Deal parado há X dias. Agendar follow-up ou requalificar." |
| Deal parado > 1.5× média | "Deal em risco. Enviar case de sucesso do setor [setor]." |
| Valor alto + Prospecting há muito tempo | "Conta de alto valor em Prospecting. Envolver manager para aceleração." |
| Vendedor com baixo WR no setor | "Seu histórico nesse setor é abaixo da média. Consultar [vendedor top] para estratégia." |
| Conta com múltiplos losses | "Conta com X deals perdidos. Revisar approach antes de investir." |
| Engaging + valor alto + tempo OK | "Deal saudável e de alto valor. Prioridade máxima para fechar." |

### 6.4 Deal Zumbi (obrigatório)
Flag visual para deals que atendem critérios:

```
ZUMBI: tempo_no_stage > 2× referência do stage E deal ativo
ZUMBI CRÍTICO: Zumbi + close_value > percentil 75
```

- Tag visual vermelha nos deals
- Filtro "Mostrar Deal Zumbis"
- Resumo: "X deals zumbis representando $Y em pipeline inflado"

### 6.5 Filtros (obrigatório)
- Por vendedor (visão individual)
- Por manager (visão do time)
- Por escritório/região
- Por produto
- Por faixa de score
- Mostrar/ocultar deals zumbis

### 6.6 Métricas de Resumo (desejável)
- Total de deals ativos e valor total do pipeline
- Distribuição por faixa de score
- Deals zumbis vs saudáveis
- Win rate do vendedor/time selecionado

---

## 7. Requisitos Técnicos

### Stack
- **Backend/Frontend:** Python + Streamlit
- **Processamento de dados:** Pandas
- **Visualização:** Plotly (integrado ao Streamlit)
- **Dados:** CSVs carregados localmente (não requer banco de dados)

### Setup
```bash
cd submissions/victor-almeida/solution
pip install -r requirements.txt
streamlit run app.py
```

### Estrutura do código
```
submissions/victor-almeida/solution/
├── app.py                 ← Entrada principal do Streamlit
├── requirements.txt       ← Dependências
├── data/                  ← CSVs do dataset
│   ├── accounts.csv
│   ├── products.csv
│   ├── sales_teams.csv
│   └── sales_pipeline.csv
├── scoring/               ← Lógica de scoring
│   ├── __init__.py
│   ├── engine.py          ← Cálculo do score composto
│   ├── velocity.py        ← Decay por tempo
│   ├── seller_fit.py      ← Win rate vendedor × setor
│   └── account_health.py  ← Saúde da conta
├── components/            ← Componentes de UI do Streamlit
│   ├── pipeline_view.py
│   ├── deal_detail.py
│   ├── filters.py
│   └── metrics.py
└── utils/                 ← Utilidades
    ├── data_loader.py
    └── formatters.py
```

---

## 8. Requisitos de UI/UX

- **Linguagem simples:** sem jargão técnico. "Deal parado há 45 dias" > "ratio temporal 1.5x acima do P75"
- **Acionável:** cada tela deve responder "o que eu faço agora?"
- **Visão de segunda-feira de manhã:** ao abrir, o vendedor vê imediatamente seus deals prioritários
- **Cores significativas:** verde (prioridade alta, saudável), amarelo (atenção), vermelho (risco/zumbi)
- **Mobile-friendly não é requisito** (vendedores usam desktop)
- **Performance:** carregar em < 3 segundos com os ~8.800 registros

---

## 9. Requisitos de Submissão

### Estrutura de arquivos
```
submissions/victor-almeida/
├── README.md              ← Baseado no template de submissão
├── solution/              ← Código da aplicação (seção 7)
├── process-log/           ← Evidências de uso de IA
│   ├── screenshots/
│   └── chat-exports/
└── docs/                  ← Documentação adicional
```

### Regras críticas
- **Só modificar arquivos dentro de `submissions/victor-almeida/`**
- Process log é **obrigatório** (sem evidência = desclassificado)
- Branch: `submission/victor-almeida`
- PR title: `[Submission] Victor Almeida — Challenge 003`

### Documentação mínima (no README.md)
1. **Setup:** Como rodar (dependências, comandos)
2. **Lógica:** Critérios de scoring usados e por quê
3. **Limitações:** O que não faz e o que precisaria para escalar

---

## 10. Critérios de Qualidade

| Critério | O que significa |
|----------|----------------|
| **Funciona** | Roda seguindo as instruções de setup |
| **Scoring inteligente** | Usa features certas, vai além de ordenar por valor |
| **Usável** | Vendedor não-técnico consegue usar e entender |
| **Acionável** | Interface ajuda a tomar decisão, não só mostra dados |
| **Manutenível** | Código limpo para outro dev dar manutenção |

### O que torna a submissão forte
- Entendeu o problema antes de construir
- IA usada estrategicamente (não como "Google glorificado")
- Output acionável — alguém poderia usar amanhã
- Process log mostra iteração e julgamento
- Comunicação clara para técnicos e não-técnicos

---

## 11. Fora de Escopo / Limitações

- **Não é ML:** scoring baseado em regras e heurísticas, não modelo treinado
- **Dados estáticos:** carrega CSVs uma vez, não tem integração com CRM real
- **Sem autenticação:** não tem login/permissão por vendedor
- **Sem histórico de score:** não rastreia evolução do score ao longo do tempo
- **Data de referência fixa:** usa 2017-12-31 como "hoje" (última data do dataset)
- **Sem deploy:** roda localmente via `streamlit run`

### Para escalar (futuro)
- Integração com CRM real (Salesforce, HubSpot, Pipedrive)
- Modelo de ML treinado com dados históricos para calibrar probabilidades
- Autenticação e permissões por papel
- Atualização em tempo real dos scores
- Tracking da evolução do score e alertas automáticos
- Deploy em cloud (AWS/GCP) com CI/CD
