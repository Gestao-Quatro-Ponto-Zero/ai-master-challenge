# CONTEXT5.md — Score Final por Valor Esperado + Correções de Interface

## Mudança 1 — Score Final baseado em Valor Esperado (CRÍTICA)

### O problema
O objetivo da ferramenta é maximizar receita. Com a fórmula anterior (média ponderada prob×0.70 + valor×0.30), um deal de $55 com alta probabilidade ficava em #3 no ranking — acima de deals de $3.000+. Isso não faz sentido para o vendedor que precisa gerar faturamento.

### A solução: Valor Esperado

O Score Final agora é baseado no **Valor Esperado** — a receita provável de cada deal:

```
Valor Esperado ($) = (Score Probabilidade / 100) × sales_price
```

Isso alinha a ferramenta com o objetivo real: um deal de $5.482 com 75% de probabilidade vale $4.147 esperados. Um deal de $55 com 85% de probabilidade vale $47 esperados. Não há como o de $55 ficar acima.

### Normalização com escala logarítmica

O Valor Esperado bruto varia de $24 a $17.648. Com normalização linear, o GTK 500 ($26.768) dominaria completamente e tudo abaixo ficaria esmagado. A escala logarítmica suaviza:

```python
import math

# Para cada deal:
valor_esperado_bruto = (score_probabilidade / 100) * sales_price
valor_esperado_log = math.log(max(valor_esperado_bruto, 1))

# Normalizar para 0-100:
score_final = ((valor_esperado_log - min_log) / (max_log - min_log)) * 100
```

Onde min_log e max_log são calculados sobre TODOS os deals abertos.

### Resultado validado

O ranking com a nova fórmula:
- Top: GTK 500 (scores 95-100) — correto, maior valor esperado
- Tier 2: GTX Plus Pro e GTXPro (scores 72-79) — segundo tier de valor
- Meio: GTX Basic e GTX Plus Basic (scores 55-70) 
- MG Advanced: scores 60-75 (valor médio-alto)
- Bottom: MG Special (scores 0-10) — deals de $55, como deveria ser

### O que o vendedor vê

Para cada deal, agora são exibidas 3 informações:
- **Score Final** (0-100): baseado no valor esperado normalizado (LOG)
- **Probabilidade** (0-100): exibida separadamente como informação complementar
- **Valor Esperado ($)**: o número real em dólares que ele pode esperar

---

## Mudança 2 — Explicação completa visível na tabela

### O problema
A coluna "Por que esse score?" na tabela Pipeline Completo está cortada — o vendedor não consegue ler a justificativa.

### A solução
Duas abordagens combinadas:

**Na tabela:** Manter explicação resumida de 1 linha, mas garantir que a coluna tenha largura suficiente. Usar st.dataframe() com column_config para definir largura mínima da coluna de explicação:

```python
st.dataframe(
    df_display,
    column_config={
        "Por que esse score?": st.column_config.TextColumn(
            width="large"
        )
    },
    use_container_width=True,
    hide_index=True
)
```

**Abaixo da tabela:** Adicionar um st.expander() "📋 Ver explicação detalhada de todos os deals" que mostra uma versão expandida com explicação completa por deal — mesma formatação dos Top 5 (tabela de pontos por fator).

---

## Mudança 3 — Atualizar a caixa "Como funciona o Score?"

A explicação precisa refletir a nova fórmula. Atualizar o conteúdo do expander:

```
## Como calculamos o Score de cada deal?

O score vai de 0 a 100 e representa o **valor esperado** de cada deal — ou seja, quanto dinheiro aquele deal provavelmente vai gerar.

### Como funciona:

Primeiro calculamos a **probabilidade de fechar** (0 a 100) baseada em 4 fatores:

🏷️ **Produto + Setor do cliente (35%)** — Algumas combinações historicamente fecham mais. Por exemplo, GTX Pro para empresas de serviços fecha 72% das vezes.

🏢 **Histórico da conta (30%)** — Contas que já compraram antes e têm bom histórico recebem pontuação maior.

📅 **Momento do trimestre (20%)** — Deals fecham muito mais nos meses de final de trimestre (março, junho, setembro, dezembro).

⏱️ **Tempo no pipeline (15%)** — Há quanto tempo o deal está em andamento.

Depois multiplicamos a probabilidade pelo **valor do produto**, gerando o **Valor Esperado em $**:

💰 **Valor Esperado = Probabilidade × Valor do Produto**

Um deal de $5.000 com 70% de chance vale $3.500 esperados.
Um deal de $55 com 85% de chance vale $47 esperados.

O Score Final (0-100) é baseado nesse valor esperado. Deals com maior retorno provável ficam no topo.

### O que significa cada cor:

🟢 **Verde (acima de 70)** — Alto valor esperado. Foque aqui primeiro.
🟡 **Amarelo (40 a 70)** — Valor esperado moderado. Mantenha acompanhamento.
🔴 **Vermelho (abaixo de 40)** — Baixo valor esperado. Reavalie a abordagem.

### Sobre o estágio (Prospecting vs Engaging):

O estágio do deal **NÃO** afeta o score. Um deal em Prospecting com alto potencial aparece no topo — porque precisa do seu primeiro contato. O badge 🆕 Novo indica que ninguém falou com o cliente ainda.
```

---

## Mudança 4 — Pontuação detalhada nos Top 5 (atualizada)

Os cards Top 5 agora mostram a nova estrutura com Valor Esperado:

```
#1 — RUNDOFASE                                    🔄 Em andamento
Score 100.0 | GTK 500 · $26,768 · Engaging · 150 dias

📊 Pontuação detalhada:
| Fator              | Pontos     | Detalhe                                           |
|---------------------|-----------|---------------------------------------------------|
| 🏷️ Produto + Setor | XX.X / 35 | technolgy+GTK 500 converte XX% (forte/média/fraca) |
| 🏢 Histórico conta | XX.X / 30 | Rundofase converte XX% (acima/na/abaixo média)    |
| 📅 Sazonalidade    | XX.X / 20 | mês de fechamento trimestral                       |
| ⏱️ Tempo pipeline  | XX.X / 15 | 150 dias no pipeline                               |
| **📈 Probabilidade** | **XX.X / 100** |                                              |
| 💰 Valor do produto | $26,768   |                                                    |
| 💵 Valor Esperado   | $17,648   | = Probabilidade × Valor                           |
| **🎯 Score Final**  | **100.0** | Baseado no valor esperado (escala logarítmica)     |
```

---

## Fórmula completa (v4 — FINAL)

```python
# 1. Score de Probabilidade (0-100)
score_probabilidade = (
    fator_setor_produto * 0.35 +
    fator_historico_conta * 0.30 +
    fator_sazonalidade * 0.20 +
    fator_tempo * 0.15
)

# 2. Valor Esperado
valor_esperado = (score_probabilidade / 100) * sales_price

# 3. Score Final (0-100) — valor esperado normalizado com log
valor_esperado_log = math.log(max(valor_esperado, 1))
# min_log e max_log calculados sobre todos os deals abertos
score_final = ((valor_esperado_log - min_log) / (max_log - min_log)) * 100
```

### Colunas a guardar no dataframe:
- `fator_setor_produto` (0-100)
- `fator_historico_conta` (0-100)
- `fator_sazonalidade` (0-100)
- `fator_tempo` (0-100)
- `taxa_combo` (0-1)
- `taxa_conta` (0-1)
- `score_probabilidade` (0-100)
- `valor_esperado` (em $)
- `score_final` (0-100)

---

## Checklist para o Claude Code

1. [ ] Implementar Score Final baseado em Valor Esperado (prob × valor, normalizado com log)
2. [ ] Exibir Probabilidade e Valor Esperado ($) como informações separadas na interface
3. [ ] Atualizar pontuação detalhada nos Top 5 com Valor Esperado
4. [ ] Corrigir coluna de explicação na tabela (largura suficiente ou column_config)
5. [ ] Atualizar caixa "Como funciona o Score?" com nova explicação
6. [ ] Manter TUDO que já funciona: filtros, KPIs, Top 5 dinâmico, checklist, badges de stage
7. [ ] Não mudar a lógica dos 4 fatores de probabilidade — só o Score Final muda
