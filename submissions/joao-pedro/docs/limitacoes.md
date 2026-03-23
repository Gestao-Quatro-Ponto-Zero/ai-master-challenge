## ⚠️ Limitações e Escalabilidade

### Limitações de Dados

#### 1. **Ausência de Timestamps Granulares**

**O que não temos:**

- Datas de entrada/saída por estágio (só `engage_date` e `close_date`)
- Histórico de movimentações (`Prospecting → Engaging → Won`)
- Quem/quando mudou o deal de estágio

**Impacto:**

- Não conseguimos calcular **tempo real** em Prospecting
- Urgência usa proxy: `snapshot_end_date - engage_date` para Engaging aberto
- Não detectamos "deals que pularam Prospecting" (entrada direta em Engaging)

**Para escalar:**

```sql
-- Schema ideal:
stage_history (
  deal_id,
  stage,
  entered_at TIMESTAMP,
  exited_at TIMESTAMP,
  changed_by VARCHAR  -- audit trail
)
```

**Benefício:** Calcular **tempo em cada estágio** + detectar gargalos específicos.

---

#### 2. **Sem Dados de Interação/Atividade**

**O que não temos:**

- Última atividade no deal (email, call, meeting)
- Frequência de touchpoints
- Engajamento do prospect (replies, meetings aceitos)

**Impacto:**

- "165 dias em Engaging" pode ser:
  - Deal ativo com 50 interações (difícil, mas trabalhado) ✓
  - Deal morto com 0 interações há 120 dias (abandonado) ✗
- Não diferenciamos "travado sendo trabalhado" de "travado esquecido"

**Para escalar:**

```python
# Feature adicional:
days_since_last_activity = today - last_interaction_date

IF days_since_last_activity > 30:
    urgency × 1.5  # Multiplicador de "abandono"
```

**Benefício:** Urgência considera **abandono**, não só tempo total.

---

#### 3. **Histórico de Reativações Inexistente**

**O que não temos:**

- Deals que foram Lost e depois voltaram
- Taxa de recuperação por motivo de Lost
- Tempo médio até reativação bem-sucedida

**Impacto:**

- Não validamos eficácia de "Lost Inteligente" (proposto como evolução)
- Não sabemos se "budget negado" realmente volta em Q1
- Ação "Discard" é binária (Lost = morte), sem nuance

**Para escalar:**

```python
# Lost Inteligente (proposta futura)
lost_categories = {
    'TIMING': {
        'recovery_rate': 0.35,  # 35% voltam
        'avg_days_to_reactivate': 90,
        'reactivation_trigger': 'Q1 budget cycle'
    },
    'DECISOR_CHANGE': {
        'recovery_rate': 0.22,
        'reactivation_trigger': 'New VP hired'
    },
    # ...
}
```

**Benefício:** Vendedor aceita mover para Lost (não é "morte"), sistema recicla automaticamente.

---

#### 4. **Dados de Concorrência Ausentes**

**O que não temos:**

- Concorrentes ativos no deal
- Preços oferecidos por concorrentes
- Recursos que concorrente tem e nós não

**Impacto:**

- Probabilidade não considera "pressão competitiva"
- Deal com 3 concorrentes tem mesma prob que deal exclusivo
- Não sugerimos ações específicas ("baixar preço 10%" vs "destacar feature X")

**Para escalar:**

```python
IF competitor_count >= 3:
    probability × 0.85  # -15% em leilão
    
IF competitor == 'incumbent':
    probability × 0.75  # -25% vs quem já está lá
```

---

### Limitações de Escopo (Escolhas do MVP)

#### 1. **Modelo Baseado em Regras (não ML)**

**Heurísticas bem definidas:**

- Usamos heurísticas + regras (50/30/20, thresholds fixos)
- NÃO usamos Machine Learning no MVP (Random Forest, XGBoost, Neural Nets)

> "Um scoring baseado em regras + heurísticas, bem apresentado,   
> vale mais que um XGBoost sem interface." 

**Vantagens:**

- ✅ **Explicabilidade total:** "Score 94 porque frozen 215d + conta estratégica"
- ✅ **Auditável:** Manager vê exatamente por que deal está no topo
- ✅ **Ajustável:** Mudar peso de 50% para 55% não exige retreinar modelo

**Desvantagens:**

- ❌ Não detecta **padrões não-óbvios** (ex: "deals do setor X + produto Y + Q4 sempre travam")
- ❌ Thresholds são **fixos** (165d, 85d) — não se adaptam automaticamente

**Para escalar:**

```python
# Híbrido: Regras + ML
base_score = rules_engine(deal)  # 50/30/20

ml_adjustment = xgboost_model.predict(deal)  # -10 a +10
final_score = base_score + ml_adjustment

# Mantém explicabilidade (regras) + captura padrões (ML)
```

---

#### 2. **Viabilidade Calculada por Vendedor (não por Deal)**

**Escolha:**

- Viabilidade é **atributo do vendedor** (prospecting, carga, especialização)
- Mesmo vendedor tem mesma viabilidade em TODOS os seus deals

**Limitação:**

- Vendedor pode ter viabilidade 20% geral
- Mas viabilidade 80% em **um deal específico** (ex: conta onde tem relação pessoal)

**Para escalar:**

```python
# Viabilidade contextual
viability = (
    0.4 × seller_viability +  # Capacidade geral
    0.3 × relationship_strength +  # Relação com decisor neste deal
    0.3 × deal_complexity_match  # Deal match com skillset
)
```

**Benefício:** Captura nuances (vendedor pode estar sobrecarregado mas ter deal "fácil").

---

#### 3. **Ações Sugeridas Não São Executadas Automaticamente**

**Escolha:**

- Sistema **sugere** ação ("Transfer para Wilburn")
- Vendedor/Manager **decide** se executa
- Não há automação (bot que transfere deals sozinho)

**Limitação:**

- Depende de adoção humana
- Vendedor pode ignorar recomendação
- Sem tracking de "taxa de execução de sugestões"

**Para escalar:**

```python
# Auto-execution com aprovação
IF score >= 90 AND viability < 30:
    action = 'TRANSFER'
    
    # Auto-suggest com 1-click approval
    notification = {
        'to': 'manager@company.com',
        'message': 'Deal #4521 auto-flagged for transfer',
        'approve_button': True,  # 1 click = transfere
        'reject_button': True
    }
    
# Tracking
executed_suggestions = 45%  # KPI de adoção
```

---

#### 4. **Não Integra com CRM Real**

**MVP:**

- Lê CSVs estáticos
- Outputs são arquivos/interface
- Não **escreve de volta** no CRM (Salesforce, HubSpot, Pipedrive)

**Limitação:**

- Vendedor vê recomendação no sistema → tem que **manualmente** ir no CRM executar
- Dados podem ficar desatualizados (CSV é snapshot de 2017-12-31)
- Sem sincronização bidirecional

**Para escalar:**

```python
# Integração CRM
salesforce_client.update_deal(
    deal_id='4521',
    fields={
        'Priority_Score__c': 94,
        'Suggested_Action__c': 'Transfer to Wilburn',
        'Urgency_Flag__c': 'CRITICAL'
    }
)

# Webhook inverso: CRM → Sistema
@app.post('/webhook/deal-updated')
def deal_updated(payload):
    # Re-calcula score quando deal muda no CRM
    recalculate_score(payload['deal_id'])
```

---

### Limitações de Escala (Produção)

#### 1. **Performance com Volume Alto**

**MVP:**

- Processa 8.800 deals em memória (pandas DataFrame)
- Calcula score sob demanda (on-the-fly)
- Adequado para dataset pequeno/médio

**Limitações de escala:**

- 100k deals: Pandas fica lento (5-10s para carregar)
- 1M deals: Não cabe em memória de servidor único
- Score calculado a cada request (sem cache)

**Para escalar:**

```python
# 1. Database real (não CSV)
PostgreSQL com indexes:
  - deal_stage (B-tree)
  - sales_agent (B-tree)  
  - days_in_pipeline (computed column)
  
# 2. Cache de scores
Redis:
  deal:4521:score → {score: 94, calculated_at: 2024-01-15T10:00:00}
  TTL: 1 hour  # Re-calcula apenas se deal mudar

# 3. Processamento batch
Celery task (daily):
  - Calcula score de TODOS os deals
  - Atualiza cache
  - Request time: <50ms (lê cache, não calcula)

# 4. Sharding por região
West region → Server A
East region → Server B
Central → Server C
```

---

#### 2. **Ausência de Testes Automatizados**

**MVP:**

- Testes manuais ("roda e olha se faz sentido")
- Sem test suite (pytest, unittest)
- Sem CI/CD pipeline

**Limitação:**

- Regressão: Mudar threshold pode quebrar lógica sem perceber
- Confiança baixa para deploy automático

**Para escalar:**

```python
# tests/test_scoring_engine.py

def test_urgency_frozen_deal():
    """Deal > 200 dias deve ter urgência 100"""
    deal = create_test_deal(days_in_pipeline=215)
    score = engine.calculate_urgency(deal)
    assert score == 100

def test_viability_no_prospecting():
    """Vendedor sem prospecting deve ter viability < 50"""
    seller = create_test_seller(prospecting_count=0)
    viab = engine.calculate_viability(seller)
    assert viab < 50

def test_action_transfer_low_viability():
    """Score alto + viab baixa → ação Transfer"""
    deal = create_test_deal(score=90, viability=20)
    action = engine.suggest_action(deal)
    assert action['type'] == 'TRANSFER'

# CI/CD
GitHub Actions:
  - Roda testes em cada commit
  - Deploy só se 100% dos testes passarem
```

---

#### 3. **Monitoramento e Observabilidade Ausentes**

**MVP:**

- Sem logs estruturados
- Sem métricas de uso (quantos deals scored/dia)
- Sem alertas (ex: "Score médio caiu 20 pts, algo errado?")

**Para escalar:**

```python
# Logging estruturado
import structlog

logger.info(
    'score_calculated',
    deal_id='4521',
    score=94,
    urgency=100,
    viability=20,
    action='TRANSFER',
    execution_time_ms=45
)

# Métricas (Prometheus)
score_calculation_duration.observe(0.045)  # 45ms
score_distribution.observe(94)
viability_distribution.observe(20)

# Alertas (PagerDuty)
IF avg_score_last_hour < 50:  # Normalmente é ~65
    alert('Score médio caiu drasticamente — verificar dados')
```

---

#### 4. **Segurança e Compliance**

**MVP:**

- Sem autenticação (qualquer um acessa)
- Sem RBAC (vendedor vê deals de outros vendedores)
- Sem audit trail (quem mudou o quê, quando)
- Sem GDPR compliance (dados de clientes em texto plano)

**Para produção:**

```python
# Auth + RBAC
@app.get('/deals')
@require_auth
def get_deals(current_user):
    IF current_user.role == 'SELLER':
        # Só vê seus deals
        deals = db.query(Deal).filter(
            Deal.sales_agent == current_user.id
        )
    ELIF current_user.role == 'MANAGER':
        # Vê da equipe
        deals = db.query(Deal).filter(
            Deal.sales_agent.in_(current_user.team)
        )
    # ...

# Audit log
audit_log.create({
    'user_id': user.id,
    'action': 'TRANSFER_DEAL',
    'deal_id': '4521',
    'from_seller': 'Anna',
    'to_seller': 'Wilburn',
    'timestamp': now(),
    'ip_address': request.ip
})

# GDPR
- Criptografia em repouso (AES-256)
- PII anonimizada em logs
- Right to be forgotten (delete cascade)
```

---

## Possíveis evoluções

- 🔧 Integração CRM (Salesforce API)
- 🔧 Database real (PostgreSQL)
- 🔧 Cache (Redis)
- 🔧 Testes automatizados + CI/CD
- 🔧 Autenticação + RBAC

- 🧠 Lost Inteligente (categorização + reciclagem)
- 🧠 ML Híbrido (regras + XGBoost para ajuste fino)
- 🧠 Detecção de padrões não-óbvios
- 🧠 Previsão de churn de deals

- 📈 Sharding por região
- 📈 Processing distribuído (Spark)
- 📈 Real-time scoring (stream processing)
- 📈 Multi-tenant (SaaS para outras empresas)



---

## 💡 Aprendizados e Trade-offs

### O que funcionou bem (validado com dados)

✅ **Urgência baseada em medianas reais**

- 165d (Engaging), 57d (Won), 14d (Lost) são thresholds **objetivos**
- Não arbitrários (30d, 60d, 90d)

✅ **Viabilidade separada do score**

- Mantém score auditável
- Permite ações diferentes sem confundir importância

✅ **Features baseadas em heurísticas bem definidas**

- Especialização produto×vendedor: diferença de 20 pts de WR
- Sobrecarga: Darcel com 194 deals vs média de 75



### O que precisaria de validação adicional

⚠️ **Thresholds de viabilidade (prospecting, carga)**

- 150 deals = sobrecarga? Pode ser 120 ou 180 dependendo da empresa
- 0 prospecting = -50% viabilidade? Pode ser -30% ou -70%
- **Ideal:** Calibrar com A/B test ou feedback de vendedores

⚠️ **Pesos do score (50/30/20)**

- Funcionam com a tese atual (destravar pipeline)
- Podem precisar ajuste se objetivo mudar (ex: maximizar receita)
- **Ideal:** Testar 60/25/15 vs 50/30/20 e medir impacto

⚠️ **Ações sugeridas (PUSH vs TRANSFER vs DISCARD)**

- Baseadas em lógica, não em dados de execução
- **Ideal:** Tracking de "taxa de execução por tipo de ação"


---

