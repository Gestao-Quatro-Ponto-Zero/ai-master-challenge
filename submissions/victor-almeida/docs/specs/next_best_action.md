# Especificacao Tecnica — Next Best Action (NBA)

**Modulo:** `scoring/nba.py`
**Autor:** Victor Almeida
**Data:** 21 de marco de 2026
**Versao:** 1.0
**Dependencias:** scoring engine (score composto + componentes), dados enriquecidos do pipeline

---

## 1. Objetivo

O modulo de Next Best Action transforma o score numerico de cada deal em uma **instrucao ativa e especifica** para o vendedor. Em vez de exibir apenas "Score 72", o sistema diz:

> "Score 72 -- Deal parado ha 18 dias (media: 12). Acao: agendar call de requalificacao."

O vendedor nao precisa interpretar o score — ele sabe o que fazer.

---

## 2. Catalogo de Regras

O sistema define 6 regras NBA, cada uma com condicao de disparo, prioridade, e template de mensagem. Um deal pode satisfazer multiplas condicoes; a regra de **maior prioridade** prevalece como acao principal, mas regras secundarias aparecem como contexto adicional.

### 2.1 Tabela Completa de Regras

| ID | Nome | Prioridade | Condicao | Template |
|----|------|-----------|----------|----------|
| `NBA-01` | Deal Parado | 3 (media) | `dias_no_stage > referencia_stage` E `dias_no_stage <= 1.5 * referencia_stage` | "Deal parado ha {dias} dias (media do stage: {ref} dias). Agendar follow-up ou requalificar." |
| `NBA-02` | Deal em Risco | 2 (alta) | `dias_no_stage > 1.5 * referencia_stage` E `dias_no_stage <= 2.0 * referencia_stage` | "Deal em risco — parado ha {dias} dias. Enviar case de sucesso do setor {setor}." |
| ~~`NBA-03`~~ | ~~Alto Valor Estagnado~~ | — | **REMOVIDA** — dependia de `dias_no_stage` para Prospecting, que nao existe no dataset. Substituida por NBA-06B. | — |
| `NBA-04` | Seller Fit Baixo | 4 (baixa) | `seller_sector_winrate < team_sector_winrate * 0.8` E `deals_vendedor_no_setor >= 5` | "Seu historico em {setor} esta abaixo da media ({wr_vendedor}% vs {wr_time}%). Consultar {vendedor_top} para estrategia." |
| `NBA-05` | Conta Problematica | 2 (alta) | `losses_conta >= 2` | "Esta conta ja teve {n_losses} deals perdidos. Revisar approach antes de investir mais tempo." |
| `NBA-06` | Prioridade Maxima | 1 (critica) | `deal_stage == 'Engaging'` E `valor_deal >= percentil_75_valor` E `dias_no_stage <= referencia_engaging` | "Deal saudavel e de alto valor ({valor_formatado}). Prioridade maxima para fechar esta semana." |
| `NBA-06B` | Prospecting Alto Valor | 2 (alta) | `deal_stage == 'Prospecting'` E `valor_deal >= percentil_75_valor` | "Oportunidade de alto valor ({produto}, {valor_formatado}) em Prospecting. Priorizar qualificacao para mover para Engaging." |

---

## 3. Detalhamento de Cada Regra

### 3.1 NBA-01: Deal Parado (Prioridade 3)

**Logica:** o deal ultrapassou o tempo de referencia do stage, mas ainda nao entrou na zona critica. E um alerta leve para reativacao.

**Condicao exata:**
```python
dias_no_stage > referencia_stage AND dias_no_stage <= 1.5 * referencia_stage
```

**Thresholds por stage:**
- **Prospecting:** `referencia_prospecting` = mediana de dias em Prospecting dos deals que avancaram para Engaging (calcular dos dados; estimativa: ~30 dias)
- **Engaging:** `referencia_engaging` = P75 dos dias Won em Engaging = **88 dias**

**Template:**
```
"Deal parado ha {dias_no_stage} dias (media do stage: {referencia_stage} dias). Agendar follow-up ou requalificar."
```

**Variaveis dinamicas:**
| Variavel | Fonte | Tipo |
|----------|-------|------|
| `dias_no_stage` | `DATA_REFERENCIA - engage_date` (apenas Engaging). Para Prospecting: `None` — nao ha datas disponiveis no dataset. | int ou None |
| `referencia_stage` | Constante calculada por stage | int |

**Exemplo de saida:**
> "Deal parado ha 95 dias (media do stage: 88 dias). Agendar follow-up ou requalificar."

---

### 3.2 NBA-02: Deal em Risco (Prioridade 2)

**Logica:** o deal ultrapassou 1.5x o tempo de referencia. Esta esfriando e precisa de uma acao mais agressiva — enviar material relevante do setor para reengajar o contato.

**Condicao exata:**
```python
dias_no_stage > 1.5 * referencia_stage AND dias_no_stage <= 2.0 * referencia_stage
```

**Thresholds:**
- **Engaging:** dispara a partir de `1.5 * 88 = 132 dias`, ate `2.0 * 88 = 176 dias`
- **Prospecting:** dispara a partir de `1.5 * referencia_prospecting`

> **Nota:** acima de `2.0 * referencia_stage` o deal e classificado como **Zumbi** pelo scoring engine. A NBA-02 nao se aplica a zumbis — zumbis recebem a flag visual propria e a NBA muda para "Considerar descarte ou requalificacao total".

**Template:**
```
"Deal em risco — parado ha {dias_no_stage} dias. Enviar case de sucesso do setor {setor_conta}."
```

**Variaveis dinamicas:**
| Variavel | Fonte | Tipo |
|----------|-------|------|
| `dias_no_stage` | Calculado | int |
| `setor_conta` | `accounts.sector` via join com `sales_pipeline.account` | str |

**Exemplo de saida:**
> "Deal em risco — parado ha 145 dias. Enviar case de sucesso do setor technology."

---

### 3.3 ~~NBA-03: Alto Valor Estagnado em Prospecting~~ **REMOVIDA — substituida por NBA-06B**

**Motivo da remocao:** NBA-03 dependia de `dias_no_stage` para Prospecting, mas o dataset NAO possui datas para deals em Prospecting (sem `engage_date`, sem `created_date`). Impossivel determinar se um deal de Prospecting esta "estagnado".

**Substituicao:** A regra NBA-06B (Prospecting de Alto Valor, secao 3.7) cobre o caso de deals de alto valor em Prospecting, sem depender de dados temporais. Em vez de "esta parado ha X dias", recomenda "priorizar qualificacao para mover para Engaging".

---

### 3.4 NBA-04: Seller Fit Baixo (Prioridade 4)

**Logica:** o vendedor historicamente performa abaixo da media do time neste setor especifico. A recomendacao e buscar mentoria com o vendedor que tem melhor performance neste setor.

**Condicao exata:**
```python
seller_sector_winrate < team_sector_winrate * 0.8
AND deals_vendedor_no_setor >= 5
```

O threshold de `0.8` (20% abaixo da media) evita que pequenas variacoes disparem a regra. Somente se aplica quando o vendedor tem **5 ou mais deals fechados** naquele setor (threshold minimo de significancia estatistica).

**Como identificar o "vendedor top":**
```python
def get_top_seller_for_sector(sector, pipeline_df, current_seller):
    """
    Retorna o vendedor com maior win rate no setor dado,
    excluindo o vendedor atual, com minimo de 5 deals.
    """
    sector_deals = pipeline_df[
        (pipeline_df['sector'] == sector)
        & (pipeline_df['deal_stage'].isin(['Won', 'Lost']))
        & (pipeline_df['sales_agent'] != current_seller)
    ]

    seller_stats = sector_deals.groupby('sales_agent').agg(
        wins=('deal_stage', lambda x: (x == 'Won').sum()),
        total=('deal_stage', 'count')
    )

    # Filtrar vendedores com minimo de 5 deals no setor
    seller_stats = seller_stats[seller_stats['total'] >= 5]
    seller_stats['win_rate'] = seller_stats['wins'] / seller_stats['total']

    if seller_stats.empty:
        return None  # Sem candidato qualificado

    return seller_stats['win_rate'].idxmax()
```

**Criterios de selecao do vendedor top:**
1. Deve ter >= 5 deals fechados no mesmo setor
2. Nao pode ser o proprio vendedor
3. Seleciona-se o de **maior win rate** no setor
4. Em caso de empate: desempata por volume (mais deals)

**Template:**
```
"Seu historico em {setor} esta abaixo da media ({wr_vendedor_pct}% vs {wr_time_pct}% do time). Consultar {vendedor_top} para estrategia."
```

**Variaveis dinamicas:**
| Variavel | Fonte | Tipo |
|----------|-------|------|
| `setor` | `accounts.sector` | str |
| `wr_vendedor_pct` | `seller_sector_winrate * 100`, arredondado 1 decimal | str |
| `wr_time_pct` | `team_sector_winrate * 100`, arredondado 1 decimal | str |
| `vendedor_top` | Resultado de `get_top_seller_for_sector()` | str |

**Exemplo de saida:**
> "Seu historico em technology esta abaixo da media (35.7% vs 63.4% do time). Consultar Cecily Lampkin para estrategia."

---

### 3.5 NBA-05: Conta Problematica (Prioridade 2)

**Logica:** a conta ja acumulou multiplos deals perdidos. Antes de investir mais tempo, o vendedor precisa reavaliar a abordagem ou reconsiderar se vale perseguir esta conta.

**Condicao exata:**
```python
losses_conta >= 2
```

**Como calcular `losses_conta`:**
```python
losses_por_conta = pipeline_df[pipeline_df['deal_stage'] == 'Lost'] \
    .groupby('account')['opportunity_id'].count()
```

> **Nota:** o threshold e **2 losses** (nao 3), porque com 2 ja ha um padrao. O PRD menciona 3 para o health score, mas a NBA deve alertar antes — e uma acao preventiva, nao reativa.

**Template:**
```
"Esta conta ja teve {n_losses} deals perdidos. Revisar approach antes de investir mais tempo."
```

**Variaveis dinamicas:**
| Variavel | Fonte | Tipo |
|----------|-------|------|
| `n_losses` | Contagem de deals Lost da conta | int |

**Exemplo de saida:**
> "Esta conta ja teve 72 deals perdidos. Revisar approach antes de investir mais tempo."

---

### 3.6 NBA-06: Prioridade Maxima (Prioridade 1)

**Logica:** tudo esta a favor — deal de alto valor, em Engaging (mais avancado no funil), e dentro do tempo saudavel. Esse deal merece foco maximo do vendedor.

**Condicao exata:**
```python
deal_stage == 'Engaging'
AND valor_deal >= percentil_75_valor
AND dias_no_stage <= referencia_engaging  # <= 88 dias
```

**Como calcular `valor_deal` para Engaging:**
Deals em Engaging tambem nao tem `close_value` (null). Usar `products.price` como proxy, identico a Prospecting.

**Template:**
```
"Deal saudavel e de alto valor ({valor_formatado}). Prioridade maxima para fechar esta semana."
```

**Variaveis dinamicas:**
| Variavel | Fonte | Tipo |
|----------|-------|------|
| `valor_formatado` | `products.price` formatado como moeda USD | str |

**Exemplo de saida:**
> "Deal saudavel e de alto valor ($26.768). Prioridade maxima para fechar esta semana."

### 3.7 NBA-06B: Prospecting de Alto Valor (Prioridade 2)

**Logica:** deal de alto valor ainda em Prospecting. Nao temos dados temporais para Prospecting, mas o valor alto justifica priorizacao da qualificacao.

**Condicao exata:**
```python
deal_stage == 'Prospecting'
AND valor_deal >= percentil_75_valor
```

**Template:**
```
"Oportunidade de alto valor ({produto}, {valor_formatado}) em Prospecting. Priorizar qualificacao para mover para Engaging."
```

**Variaveis dinamicas:**
| Variavel | Fonte | Tipo |
|----------|-------|------|
| `produto` | `sales_pipeline.product` | str |
| `valor_formatado` | `products.sales_price` formatado como moeda USD | str |

**Exemplo de saida:**
> "Oportunidade de alto valor (GTK 500, $26.768) em Prospecting. Priorizar qualificacao para mover para Engaging."

**Nota:** Esta regra existe porque Prospecting nao recebe NBA-01/02/03/06 (todas dependem de `dias_no_stage`). NBA-06B garante que deals de alto valor em Prospecting nao fiquem sem recomendacao.

---

## 4. Sistema de Prioridades

Quando um deal satisfaz multiplas condicoes, o sistema precisa decidir qual acao exibir. A logica e:

### 4.1 Niveis de Prioridade

| Nivel | Valor | Significado | Regras |
|-------|-------|-------------|--------|
| Critica | 1 | Acao imediata necessaria | NBA-03 (Alto Valor Estagnado), NBA-06 (Prioridade Maxima) |
| Alta | 2 | Acao necessaria esta semana | NBA-02 (Deal em Risco), NBA-05 (Conta Problematica) |
| Media | 3 | Acao recomendada | NBA-01 (Deal Parado) |
| Baixa | 4 | Informativo/orientacao | NBA-04 (Seller Fit Baixo) |

### 4.2 Resolucao de Conflitos

```python
def resolver_nba(regras_aplicaveis: list[RegraAplicavel]) -> NBAResult:
    """
    Recebe lista de regras que se aplicam ao deal.
    Retorna acao principal + acoes secundarias.
    """
    # 1. Ordenar por prioridade (menor valor = maior prioridade)
    regras_aplicaveis.sort(key=lambda r: r.prioridade)

    # 2. Acao principal = regra de maior prioridade
    acao_principal = regras_aplicaveis[0]

    # 3. Excecao: NBA-06 (positiva) nao prevalece sobre NBA-05 (conta problematica)
    #    Se ambas se aplicam, NBA-05 vira principal e NBA-06 vira secundaria.
    #    Razao: alerta de risco deve prevalecer sobre otimismo.
    if acao_principal.id == 'NBA-06' and any(r.id == 'NBA-05' for r in regras_aplicaveis):
        acao_principal = next(r for r in regras_aplicaveis if r.id == 'NBA-05')
        regras_aplicaveis = [r for r in regras_aplicaveis if r.id != 'NBA-05']

    # 4. Excecao: NBA-02/NBA-01 (tempo) sao mutuamente exclusivas
    #    Um deal nao pode estar "parado" e "em risco" ao mesmo tempo.
    #    A faixa de tempo determina qual se aplica (ver secao 3.1/3.2).

    # 5. Acoes secundarias = demais regras (max 2 para nao poluir a UI)
    acoes_secundarias = [r for r in regras_aplicaveis[1:] if r.id != acao_principal.id][:2]

    return NBAResult(
        acao_principal=acao_principal,
        acoes_secundarias=acoes_secundarias
    )
```

### 4.3 Combinacoes Comuns e Resolucao

| Combinacao | Acao Principal | Secundaria |
|------------|---------------|------------|
| NBA-02 + NBA-05 | NBA-02 (Deal em Risco) | NBA-05 (Conta Problematica) |
| NBA-06 + NBA-05 | NBA-05 (Conta Problematica) | NBA-06 (Deal saudavel...) |
| NBA-01 + NBA-04 | NBA-01 (Deal Parado) | NBA-04 (Seller Fit Baixo) |
| NBA-03 + NBA-04 | NBA-03 (Alto Valor Estagnado) | NBA-04 (Seller Fit Baixo) |
| NBA-02 + NBA-04 + NBA-05 | NBA-02 (Deal em Risco) | NBA-05, NBA-04 |
| Nenhuma regra se aplica | Fallback (ver secao 8.1) | -- |

---

## 5. Integracao com o Scoring Engine

### 5.1 Dados Necessarios do Scoring Engine

O modulo NBA nao recalcula scores — ele **consome** os dados ja calculados pelo engine. Para cada deal ativo, o scoring engine deve expor:

```python
@dataclass
class DealScoreData:
    # Identificacao
    opportunity_id: str
    sales_agent: str
    product: str
    account: str
    deal_stage: str  # 'Prospecting' ou 'Engaging'

    # Score composto
    score_total: float  # 0-100

    # Componentes individuais (necessarios para avaliar condicoes NBA)
    dias_no_stage: int
    referencia_stage: int  # 88 para Engaging, calculado para Prospecting

    valor_deal: float  # close_value ou products.price como proxy
    percentil_75_valor: float  # P75 de valor (calculado uma vez)

    seller_sector_winrate: float  # 0.0-1.0
    team_sector_winrate: float  # 0.0-1.0
    deals_vendedor_no_setor: int  # numero de deals fechados do vendedor neste setor

    losses_conta: int  # deals Lost desta conta

    setor_conta: str  # accounts.sector

    # Flags do engine
    is_zombie: bool  # dias_no_stage > 2.0 * referencia_stage
```

### 5.2 Dados Adicionais (calculados pelo modulo NBA)

O modulo NBA precisa calcular por conta propria:

1. **Vendedor top por setor** — nao faz parte do scoring engine, e especifico da NBA-04. Calculado uma unica vez no carregamento e cacheado em dicionario `{setor: vendedor_top}`.

### 5.3 Fluxo de Dados

```
[CSVs] -> [data_loader] -> [scoring/engine.py] -> [DealScoreData por deal]
                                                          |
                                                          v
                                                  [scoring/nba.py]
                                                          |
                                                          v
                                                  [NBAResult por deal]
                                                          |
                                                          v
                                               [components/deal_detail.py]
                                               [components/pipeline_view.py]
```

---

## 6. Interface do Modulo

### 6.1 Funcao Principal

```python
def calcular_nba(deal: DealScoreData, contexto: NBAContext) -> NBAResult:
    """
    Calcula a Next Best Action para um deal individual.

    Args:
        deal: Dados do deal com score ja calculado pelo engine.
        contexto: Dados pre-calculados compartilhados entre deals
                  (top sellers por setor, thresholds globais).

    Returns:
        NBAResult com acao principal, acoes secundarias, e metadata.
    """
```

### 6.2 Funcao Batch

```python
def calcular_nba_batch(deals: list[DealScoreData], pipeline_df: pd.DataFrame) -> dict[str, NBAResult]:
    """
    Calcula NBA para todos os deals ativos de uma vez.
    Pre-calcula contexto compartilhado (top sellers, thresholds)
    e itera sobre os deals.

    Args:
        deals: Lista de deals com scores calculados.
        pipeline_df: DataFrame completo do pipeline (para calcular top sellers).

    Returns:
        Dicionario {opportunity_id: NBAResult}.
    """
```

### 6.3 Estruturas de Dados

```python
@dataclass
class NBAContext:
    """Contexto pre-calculado, compartilhado entre todos os deals."""
    top_sellers_por_setor: dict[str, str]  # {setor: nome_vendedor}
    percentil_75_valor: float
    referencia_prospecting: int  # mediana dias em Prospecting dos que avancaram
    referencia_engaging: int  # 88 (P75 dos Won)

@dataclass
class RegraAplicavel:
    """Uma regra NBA que se aplica a um deal especifico."""
    id: str          # 'NBA-01' a 'NBA-06'
    nome: str        # Nome legivel
    prioridade: int  # 1 (critica) a 4 (baixa)
    mensagem: str    # Template ja preenchido com valores do deal
    tipo: str        # 'alerta' | 'risco' | 'oportunidade' | 'orientacao'

@dataclass
class NBAResult:
    """Resultado final da NBA para um deal."""
    acao_principal: RegraAplicavel
    acoes_secundarias: list[RegraAplicavel]  # max 2

    @property
    def tem_acao(self) -> bool:
        return self.acao_principal is not None

    @property
    def cor_indicador(self) -> str:
        """Cor para UI baseada no tipo da acao principal."""
        cores = {
            'alerta': 'amarelo',    # NBA-01
            'risco': 'vermelho',    # NBA-02, NBA-05
            'oportunidade': 'verde', # NBA-03, NBA-06
            'orientacao': 'azul',   # NBA-04
        }
        return cores.get(self.acao_principal.tipo, 'cinza')
```

### 6.4 Classificacao por Tipo

| Regra | Tipo | Cor na UI |
|-------|------|-----------|
| NBA-01 (Deal Parado) | `alerta` | Amarelo |
| NBA-02 (Deal em Risco) | `risco` | Vermelho |
| NBA-03 (Alto Valor Estagnado) | `oportunidade` | Verde (escalonamento positivo) |
| NBA-04 (Seller Fit Baixo) | `orientacao` | Azul |
| NBA-05 (Conta Problematica) | `risco` | Vermelho |
| NBA-06 (Prioridade Maxima) | `oportunidade` | Verde |

---

## 7. Apresentacao na UI

### 7.1 Pipeline View (tabela principal)

Na tabela de pipeline, a NBA aparece como uma **coluna resumida**:

```
| Score | Deal    | Conta     | Produto  | Dias | NBA                                    |
|-------|---------|-----------|----------|------|----------------------------------------|
| 85    | A3F2... | Betasoloin| GTK 500  | 45   | Prioridade maxima para fechar.         |
| 72    | B7C1... | Hottechi  | GTXPro   | 95   | Deal parado ha 95 dias. Follow-up.     |
| 58    | D4E9... | Kan-code  | MG Adv.  | 155  | Deal em risco. Case de sucesso.        |
```

- Texto truncado na coluna (max ~50 caracteres)
- Icone/emoji indicando tipo: circunferencia verde, triangulo amarelo, X vermelho, (i) azul
- Hover ou clique expande a mensagem completa

### 7.2 Deal Detail (card expandido)

Quando o vendedor clica/expande um deal, a NBA aparece como um **card destacado** abaixo do score:

```
+-------------------------------------------------------------------+
| Score: 72                                                          |
|                                                                    |
| Componentes:                                                       |
|   Stage (Engaging): 70/100 | Valor: 65/100 | Velocidade: 42/100  |
|   Seller-Fit: 80/100       | Saude Conta: 35/100                 |
|                                                                    |
| +---------------------------------------------------------------+ |
| | ACAO RECOMENDADA                                               | |
| |                                                                | |
| | Deal em risco — parado ha 155 dias. Enviar case de sucesso    | |
| | do setor technology.                                           | |
| |                                                                | |
| | Tambem considere:                                              | |
| | - Esta conta ja teve 63 deals perdidos. Revisar approach.     | |
| | - Seu historico em technology esta abaixo da media (35.7%     | |
| |   vs 63.4% do time). Consultar Cecily Lampkin.               | |
| +---------------------------------------------------------------+ |
+-------------------------------------------------------------------+
```

**Regras de layout:**
- Card da acao principal: fundo colorido conforme `cor_indicador`
- Acoes secundarias: texto menor, abaixo, com prefixo "Tambem considere:"
- Se nao ha acao secundaria, a secao nao aparece (nao mostrar area vazia)

### 7.3 Formatacao de Valores

| Dado | Formato | Exemplo |
|------|---------|---------|
| Valor monetario | USD com separador de milhares, sem centavos | `$26.768` |
| Win rate | Percentual com 1 casa decimal | `35.7%` |
| Dias no stage | Numero inteiro seguido de "dias" | `155 dias` |
| Nome do vendedor | Nome completo como no dataset | `Cecily Lampkin` |
| Setor | Lowercase, como no dataset | `technology` |

---

## 8. Edge Cases

### 8.1 Deal sem Nenhuma Regra Aplicavel

**Quando ocorre:** deal em Engaging, dentro do tempo saudavel, valor abaixo do P75, vendedor sem fit especialmente bom ou ruim, conta sem historico problematico.

**Acao:** retornar uma **mensagem fallback neutra**:
```
"Deal dentro dos parametros normais. Manter acompanhamento regular."
```

**Tipo:** `orientacao` | **Cor:** cinza | **Prioridade:** 5 (minima)

### 8.2 Vendedor Novo (sem historico)

**Quando ocorre:** vendedor tem < 5 deals fechados em qualquer setor.

**Tratamento na NBA-04:** regra **nao dispara**. O threshold de 5 deals e respeitado tanto para o fit do scoring quanto para a NBA. O vendedor novo nao recebe a recomendacao de "consultar alguem" — seria frustrante receber isso em todos os deals.

**Na pratica:** o `seller_sector_winrate` e o `team_sector_winrate` recebem o mesmo valor (media do time), entao a condicao `< 0.8 * team` nunca e satisfeita.

### 8.3 Setor sem Vendedor Top Qualificado

**Quando ocorre:** nenhum outro vendedor tem >= 5 deals no setor, ou so o proprio vendedor tem historico.

**Tratamento:** a NBA-04 ajusta o template:
```
"Seu historico em {setor} esta abaixo da media ({wr_vendedor_pct}% vs {wr_time_pct}% do time). Buscar cases de sucesso internos para aprimorar abordagem."
```

Substitui a mencionamento do vendedor top por uma acao generica.

### 8.4 Deal Zumbi (acima de 2x referencia)

**Quando ocorre:** `dias_no_stage > 2.0 * referencia_stage`.

**Tratamento:** deals zumbis **nao recebem NBA-01 ou NBA-02** (que cobrem ate 2.0x). Em vez disso, recebem uma mensagem especifica de zumbi:
```
"Deal classificado como zumbi — parado ha {dias_no_stage} dias ({ratio}x a referencia). Considerar descarte ou requalificacao total com novo approach."
```

**ID:** `NBA-ZB` | **Prioridade:** 1 (critica) | **Tipo:** `risco`

### 8.5 Conta sem Deals Fechados (nova)

**Quando ocorre:** conta aparece apenas com deals em Prospecting/Engaging, sem Won ou Lost historico.

**Tratamento na NBA-05:** regra nao dispara (`losses_conta = 0`).
**Tratamento no health_score:** recebe 0.5 (neutro), conforme PRD.

### 8.6 Deal em Prospecting sem Data de Referencia

**Quando ocorre:** deals em Prospecting nao tem `engage_date` nem qualquer outra data. O campo `created_date` NAO existe no dataset.

**Tratamento:** Prospecting NAO recebe regras baseadas em tempo (NBA-01, NBA-02, NBA-03, NBA-ZB). `dias_no_stage` = None. Aplicar apenas: NBA-04 (Seller Fit), NBA-05 (Conta Problematica), e NBA-06B (Prospecting de Alto Valor). Se nenhuma regra se aplicar, usar fallback: "Deal em fase inicial de qualificacao. Proximo passo: validar fit e agendar primeiro contato."

---

## 9. Constantes e Configuracao

Todas as constantes ficam centralizadas para facilitar ajuste futuro:

```python
# scoring/constants.py (ou topo do nba.py)

# Data de referencia do dataset ("hoje")
DATA_REFERENCIA = pd.Timestamp('2017-12-31')

# Referencias de tempo por stage (em dias)
REFERENCIA_ENGAGING = 88       # P75 dos deals Won
REFERENCIA_PROSPECTING = 30    # Mediana dos que avancaram (calcular dos dados)

# Thresholds de tempo
RATIO_PARADO = 1.0             # NBA-01 dispara acima deste ratio
RATIO_RISCO = 1.5              # NBA-02 dispara acima deste ratio
RATIO_ZUMBI = 2.0              # Classificacao de zumbi (flag, nao NBA)

# Threshold de valor
PERCENTIL_VALOR = 0.75         # P75 para "alto valor"

# Seller fit
THRESHOLD_DEALS_SETOR = 5      # Minimo de deals para calcular fit
RATIO_FIT_BAIXO = 0.8          # WR vendedor < 80% do WR time = fit baixo

# Conta problematica
THRESHOLD_LOSSES_CONTA = 2     # Minimo de losses para alertar
```

---

## 10. Testes e Validacao

### 10.1 Casos de Teste Unitarios

| Caso | Input | NBA Esperada |
|------|-------|-------------|
| Deal Engaging, 95 dias, valor medio | `dias=95, ref=88, valor < P75` | NBA-01 (Deal Parado) |
| Deal Engaging, 140 dias, setor technology | `dias=140, ref=88` | NBA-02 (Deal em Risco) |
| Deal Prospecting, 35 dias, GTK 500 | `dias=35, ref=30, valor=26768` | NBA-03 (Alto Valor Estagnado) |
| Deal com vendedor WR 35% no setor, time 63% | `wr_seller=0.357, wr_team=0.634, deals=28` | NBA-04 (Seller Fit Baixo) |
| Deal na Hottechi (82 losses) | `losses_conta=82` | NBA-05 (Conta Problematica) |
| Deal Engaging, 50 dias, GTK 500 | `dias=50, ref=88, valor=26768` | NBA-06 (Prioridade Maxima) |
| Deal Engaging, 200 dias | `dias=200, ref=88` | NBA-ZB (Zumbi) |
| Deal saudavel, valor medio, sem issues | Todos os indicadores normais | Fallback neutro |

### 10.2 Validacao com Dados Reais

Verificar com os dados do dataset:

1. **Markita Hansen + technology:** deve receber NBA-04 (WR 35.7% vs ~63.4% do time)
2. **Deals da Hottechi:** devem receber NBA-05 (82 losses)
3. **Deals GTK 500 em Prospecting ha 30+ dias:** devem receber NBA-03
4. **Deals Engaging ha 50 dias com GTK 500:** devem receber NBA-06
5. **Maioria dos deals Engaging ativos:** devem receber NBA-02 ou NBA-ZB (mediana de 165 dias)

### 10.3 Teste de Cobertura

Dado o estado atual do pipeline (96.7% dos deals Engaging acima da mediana Won), a distribuicao esperada de NBAs e:

| NBA | % Estimado dos Deals Ativos | Razao |
|-----|----------------------------|-------|
| NBA-ZB (Zumbi) | ~60-70% | Maioria esta acima de 2x referencia |
| NBA-02 (Risco) | ~15-20% | Faixa 1.5x-2.0x |
| NBA-01 (Parado) | ~5-10% | Faixa 1.0x-1.5x |
| NBA-06 (Prioridade) | ~3-5% | Poucos deals saudaveis + alto valor |
| NBA-05 (Conta) | Sobrepoe-se | Se aplica como secundaria a muitos |
| NBA-04 (Fit) | Sobrepoe-se | Se aplica como secundaria onde fit < 0.8 |

---

## 11. Resumo de Implementacao

### Ordem de Implementacao Sugerida

1. **Estruturas de dados** — `NBAContext`, `RegraAplicavel`, `NBAResult`
2. **Calculo de contexto** — `top_sellers_por_setor`, constantes
3. **Regras individuais** — cada regra como funcao isolada que retorna `Optional[RegraAplicavel]`
4. **Resolvedor de prioridades** — `resolver_nba()` com tratamento de conflitos
5. **Funcao batch** — `calcular_nba_batch()` que orquestra tudo
6. **Integracao com UI** — renderizacao do card NBA nos componentes Streamlit
7. **Fallback e edge cases** — zumbi, fallback neutro, vendedor novo
8. **Testes** — validacao com dados reais do dataset

### Arquivos Envolvidos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `scoring/nba.py` | Modulo principal — regras, resolvedor, funcao batch |
| `scoring/engine.py` | Expor `DealScoreData` com todos os campos necessarios |
| `scoring/constants.py` | Constantes centralizadas (ou inline no `engine.py`) |
| `components/deal_detail.py` | Renderizar card de NBA expandido |
| `components/pipeline_view.py` | Coluna NBA resumida na tabela |
| `utils/formatters.py` | Formatacao de moeda, percentual, dias |

---

## 12. Testes TDD (test_nba.py)

Antes de implementar `nba.py`, escrever os seguintes testes em `tests/test_nba.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 12.1 Testes de regras individuais

```python
def test_nba01_deal_parado_fires_when_ratio_above_1():
    """NBA-01 dispara quando 1.0 < ratio <= 1.5 (ex: 95 dias Engaging)."""

def test_nba01_does_not_fire_below_reference():
    """NBA-01 NAO dispara quando ratio <= 1.0."""

def test_nba02_deal_em_risco_fires_when_ratio_above_1_5():
    """NBA-02 dispara quando 1.5 < ratio <= 2.0 (ex: 140 dias Engaging)."""

def test_nba04_seller_fit_fires_when_wr_below_80pct_team():
    """NBA-04 dispara quando seller_wr < team_wr * 0.8 e deals >= 5."""

def test_nba04_does_not_fire_with_few_deals():
    """NBA-04 NAO dispara quando vendedor tem < 5 deals no setor."""

def test_nba05_conta_problematica_fires_with_2_losses():
    """NBA-05 dispara quando conta tem >= 2 losses."""

def test_nba05_does_not_fire_with_1_loss():
    """NBA-05 NAO dispara com apenas 1 loss."""

def test_nba06_prioridade_maxima_fires_for_healthy_high_value():
    """NBA-06 dispara: Engaging + valor >= P75 + dias <= 88."""

def test_nba06b_prospecting_alto_valor():
    """NBA-06B dispara: Prospecting + valor >= P75."""
```

### 12.2 Testes de resolucao de prioridades

```python
def test_highest_priority_rule_wins():
    """Quando multiplas regras se aplicam, a de menor prioridade numerica e a principal."""

def test_nba05_overrides_nba06():
    """NBA-05 (Conta Problematica) prevalece sobre NBA-06 (Prioridade Maxima)."""

def test_secondary_actions_limited_to_2():
    """Acoes secundarias sao limitadas a no maximo 2."""
```

### 12.3 Testes de deals zumbi

```python
def test_zombie_deal_receives_nba_zb():
    """Deal com ratio > 2.0 recebe NBA-ZB (nao NBA-01 ou NBA-02)."""

def test_zombie_nba_includes_days_and_ratio():
    """Mensagem do zumbi inclui dias no stage e ratio."""
```

### 12.4 Testes de edge cases

```python
def test_deal_without_any_rule_gets_fallback():
    """Deal sem nenhuma regra aplicavel recebe mensagem fallback neutra."""

def test_prospecting_without_temporal_data_skips_time_rules():
    """Deals Prospecting nao recebem NBA-01, NBA-02, NBA-ZB."""

def test_deal_with_null_account_skips_nba05():
    """Deal sem conta nao dispara NBA-05."""

def test_nba_result_has_acao_principal():
    """NBAResult sempre tem acao_principal (nunca None)."""
```

### 12.5 Testes com dados reais

```python
def test_hottechi_deals_receive_nba05():
    """Deals na conta Hottechi (82 losses) recebem NBA-05."""

def test_gtk500_engaging_healthy_receives_nba06():
    """Deal GTK 500 em Engaging ha 50 dias recebe NBA-06 (Prioridade Maxima)."""
```
