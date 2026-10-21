# Submissão — Hoffman — Challenge 002

## Sobre mim

- **Nome:** Hoffman
- **LinkedIn:** https://www.linkedin.com/in/mateushoffman/
- **Challenge escolhido:** 002 — Redesign de Suporte (`challenges/process-002-support`)

---

## Executive Summary

No **Dataset 1** (8.469 registros; ~29,8 mil linhas físicas no CSV), a fila operacional é o achado mais confiável: **67%** Open/Pending e **2.819** abertos **sem** `First Response Time`. Quase metade dos fechados tem timestamps inconsistentes (**49,3%** invertidos; **49,4%** resolução ≤ 1ª resposta); CSAT quase não é explicado pelas variáveis testadas (**R² ≈ 0,003**). No **Dataset 2** (47.837 tickets IT), a automação provada é **classificação + roteamento**: no hold-out, **50,6%** vão para L1 sem humano com **95,9%** de acerto de categoria nesse subconjunto (**85,8%** acurácia global). Regras do Dataset 1 (refund/cancel) e categorias sensíveis ficam fora da IA plena. Entrega: `diagnostico.py`, `prototipo.py`, process log.

---

## Para o avaliador (2 minutos)

| O quê | Onde |
|-------|------|
| Auditoria + diagnóstico | `pip install -r solution/requirements.txt` → `python solution/diagnostico.py` |
| Prova da política de roteamento | `python solution/prototipo.py treinar` |
| Demo do fluxo | `python solution/prototipo.py rotear "VPN password reset cannot login"` |
| Process log | [process-log/narrativa.md](process-log/narrativa.md) |

---

## Solução

Datasets (CC0, Kaggle): [Dataset 1](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) → `solution/data/customer_support_tickets.csv` · [Dataset 2](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) → `solution/data/all_tickets_processed_improved_v3.csv`.

Métricas abaixo geradas por `python solution/diagnostico.py` e `python solution/prototipo.py treinar` (out/2026).

### Abordagem

Dois scripts em `solution/`: **`diagnostico.py`** (Dataset 1 + cruzamento DS2) e **`prototipo.py`** (treino/roteamento no Dataset 2 + regras Dataset 1). Dependências: `solution/requirements.txt`.

### Resultados / Findings

#### 1. Diagnóstico operacional (obrigatório)

Com base no **Dataset 1**. Tempos: diferença `Time to Resolution` − `First Response Time` em horas.

##### Camada A — Confiável para decisão (qualidade do dado + fila)

- **Volume:** 8.469 tickets (pandas); ~29.807 linhas no arquivo (texto multiline) — explica o “~30 mil” do brief.
- **Timestamps:** entre 2.769 fechados com ambos os campos, **49,3%** com pós-FRT &lt; 0 e **49,4%** com resolução ≤ 1ª resposta → **não** tratar tempos/CSAT como KPI operacional fechado sem instrumentação.
- **Fila parada:** **5.700** Open/Pending (**67%**); **2.819** abertos sem `First Response Time`.
- **Tipos sensíveis (comercial):** Refund request (CSAT médio **2,93**); Cancellation request (**3,03**).
- **Desperdício (upper bound ilustrativo):** mediana pós-FRT (recorte válido) × backlog ≈ **36.148 h**; @ R$ 120/h ≈ **R$ 4,34 mi** — premissas no script.

##### Camada B — Exploratório (recorte pós-FRT ≥ 0 h; n = 1.404)

Sujeito à qualidade de timestamp do Dataset 1; útil para hipóteses, não para SLA contratual.

**Onde o fluxo trava?** Mediana global **6,3 h**, p90 **16 h**. Piores combinações (n≥20): Chat + High + Refund (**11,4 h**); Social + High + Refund (**10,6 h**); Email + Low + Cancellation (**9,7 h**); Social + Low + Product inquiry (**9,1 h**).

**O que impacta satisfação?** CSAT médio **2,99/5**. Correlação CSAT × pós-FRT ≈ **0**. Regressão canal/tipo/prioridade: **R² = 0,003**; efeitos marginais pequenos em Phone (−0,13), Email (−0,12), Social (−0,11) vs referência.

**Quanto estamos desperdiçando?** Além do backlog (Camada A), o maior alívio recuperável combina **reduzir fila parada** com squads em refund/cancel e canais assíncronos (Social/Email) — tempos acima são exploratórios.

#### 2. Proposta de automação com IA (obrigatório)

Com base nos **dois datasets**. Domínio do classificador: **texto IT (DS2)**; metadados **DS1** (`--tipo`, `--prioridade`) entram só quando existirem na entrada real.

**O que automatizar** — Classificação + roteamento (DS2). No hold-out (política do protótipo, sem metadados DS1): **50,6%** auto (L1), **49,4%** humana (HR/Admin + confiança &lt; 70%), **95,9%** acerto de categoria no auto (**85,8%** global). Triagem de prioridade quando DS1 indica `High`. Respostas sugeridas (pares descrição/resolução no DS1) e duplicatas em social — **fora do protótipo** (fase 2).

**O que NÃO automatizar** — Refund request e Cancellation request (DS1: pior CSAT e maiores tempos no recorte exploratório). HR Support e Administrative rights (DS2: **26,5%** do volume). Confiança &lt; 70%.

Exemplos dos dados (trechos reais, truncados):

- **Refund request (DS1):** *"I've accidentally deleted important data from my {product_purchased}… remember there are no refunds or cre…"* → fila **AGENTE_SENIOR** (política comercial; CSAT **2,93**).
- **HR Support (DS2):** *"access request dear modules report report cost thank much regards"* → fila **HUMANA** (**22,8%** do volume DS2).

**Como funcionaria na prática** — Ticket entra → se tipo Refund/Cancel (DS1) → agente sênior → senão classificação (IA, DS2) → se HR/Admin ou confiança baixa → humano → se prioridade High → fila prioritária → senão L1 → humano valida antes de resposta ao cliente.

**Cruzamento Dataset 2 → operação:**

| Topic_group (DS2) | % volume | Destino |
|-------------------|----------|---------|
| Hardware | 28,5% | L1 |
| HR Support | 22,8% | HUMANA |
| Access | 14,9% | L1 |
| Miscellaneous | 14,8% | L1 |
| Storage | 5,8% | L1 |
| Purchase | 5,2% | L1 |
| Internal Project | 4,4% | L1 |
| Administrative rights | 3,7% | HUMANA |

**ROI triagem (ilustrativo):** ~23 tickets/dia (DS1/365), 4 min → 0,5 min por ticket elegível (70%) → **~21 h/mês** de triagem evitável (premissas em `diagnostico.py`).

#### 3. Protótipo funcional (diferencial)

Roteador CLI: classifica texto (DS2) e aplica regras do fluxo; metadados opcionais `--tipo` / `--prioridade` (DS1).

```bash
pip install -r solution/requirements.txt
python solution/diagnostico.py
python solution/prototipo.py treinar
python solution/prototipo.py rotear "VPN password reset cannot login"
python solution/prototipo.py rotear "I want a refund" --tipo "Refund request" --prioridade High
```

Saída: `categoria`, `confianca`, `fila` (`AGENTE_SENIOR` | `HUMANA` | `PRIORITARIA` | `L1`), `motivo`.

### Recomendações

1. **Esta semana (sem IA):** atacar fila Open/Pending e tickets sem FRT; squad refund/cancel + Social/Email.
2. **4 semanas:** piloto em **sombra** do roteador (DS2 + regras DS1) — medir acerto e fila antes de auto-resposta.
3. Implementar roteador na entrada; humano para HR/Admin, baixa confiança e exceções comerciais.

### Limitações

- DS1: métricas de tempo/CSAT limitadas por timestamps sintéticos/inconsistentes (ver Camada A).
- DS1 (cliente) ≠ DS2 (IT): classificador validado no DS2; generalização para texto DS1 exigiria retreino ou guarda de domínio.
- Protótipo: classificação + roteamento apenas; sem respostas sugeridas, duplicatas ou dashboard.
- Backlog, custo e ROI com premissas explícitas no terminal.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada. Detalhes em [process-log/narrativa.md](process-log/narrativa.md).

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|----------------|
| Cursor (IA) | Diagnóstico, proposta, `diagnostico.py` e `prototipo.py` |
| Kaggle | Download dos datasets CC0 |

### Workflow

1. Decomposição alinhada ao challenge (diagnóstico, proposta, protótipo roteador, process log).
2. Script reprodutível; auditoria de timestamps e subconjunto cronológico.
3. Iteração final: métrica de política de roteamento no `treinar` + narrativa Camada A/B no README.

### Onde a IA errou e como corrigi

Interpretação errada dos campos de tempo; filtro ≥0 h e bloco de qualidade DS1. Ajuste da fronteira humano/IA em refund/cancelamento e categorias sensíveis.

### O que eu adicionei que a IA sozinha não faria

Regras de exceção humanas ancoradas em dados; ordem de decisão no roteador; premissas de ROI explícitas; reprodutibilidade via scripts.

---

## Evidências

_Anexe ou linke as evidências do processo:_

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [x] Git history — [PR #209](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/209) (branch `submission/hoffman`)
- [x] Outro: narrativa escrita — [process-log/narrativa.md](process-log/narrativa.md)

---

_Submissão enviada em: outubro/2026_
