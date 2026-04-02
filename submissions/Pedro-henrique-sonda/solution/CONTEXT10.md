# CONTEXT10.md — Pipeline como Planilha + Explicação Completa + Cicle Time Recalibrado

## Mudança 1 — Pipeline Completo como planilha com lupa clicável

### O problema
O Pipeline está como lista de expanders. O vendedor quer a visão de planilha (linhas e colunas) com a possibilidade de clicar para ver a explicação.

### A solução
Usar st.dataframe() para a planilha visual. Adicionar uma coluna "🔍" que, quando o vendedor seleciona uma linha, abre a explicação detalhada ABAIXO da linha selecionada.

**Implementação prática no Streamlit:** st.dataframe() não suporta clique em linha nativamente. A melhor alternativa:

```python
st.subheader(f"📋 Pipeline Completo — {len(df_display)} registros")

# Ordenação
ordenar_pipeline = st.radio(
    "📊 Ordenar por:",
    options=["Probabilidade", "Valor"],
    horizontal=True,
    key="ord_pipeline"
)

if ordenar_pipeline == "Valor":
    df_display = df_display.sort_values('sales_price', ascending=False)
else:
    df_display = df_display.sort_values('score', ascending=False)

# Preparar tabela para exibição
df_tabela = df_display[['score', 'estagio_badge', 'account', 'sector', 'product', 
                         'sales_price', 'sales_agent', 'dias_pipeline', 'recompras']].copy()
df_tabela.columns = ['Score', 'Estágio', 'Conta', 'Setor', 'Produto', 'Valor ($)', 
                      'Vendedor', 'Dias', 'Rec.']

# Exibir tabela com st.dataframe
st.dataframe(
    df_tabela.style.applymap(colorir_score, subset=['Score']),
    use_container_width=True,
    hide_index=True
)

# Seletor de deal para ver detalhes (logo abaixo da tabela)
st.markdown("🔍 **Pontuação detalhada:**")
deal_labels = df_display.apply(
    lambda r: f"{r['account']} — {r['product']} — Score {r['score']:.1f} — ${r['sales_price']:,.0f}",
    axis=1
).tolist()

selected = st.selectbox(
    "Selecione um deal para ver a explicação completa",
    options=range(len(deal_labels)),
    format_func=lambda i: deal_labels[i],
    key="pipeline_detail",
    label_visibility="collapsed"
)

if selected is not None:
    row = df_display.iloc[selected]
    with st.container(border=True):
        st.markdown(gerar_explicacao_detalhada(row))
```

A planilha mostra os dados de forma compacta. O seletor logo abaixo permite ver a explicação de qualquer deal. É acoplado à planilha — não numa seção separada.

---

## Mudança 2 — Explicação completa na caixa "Como funciona o Score?"

### O problema
A caixa só mostra os pesos (35%, 30%, etc.) mas não explica POR QUE cada peso foi definido assim. O vendedor não entende a lógica por trás.

### Novo conteúdo completo

```python
with st.expander("ℹ️ Como funciona o Score? (clique para entender)"):
    st.markdown("""
## Como calculamos o Score de cada deal?

O score vai de **0 a 100** e mede a **probabilidade de fechar** o deal, com bônus para clientes que já compraram antes.

---

### Os 4 fatores da probabilidade

Analisamos todo o histórico de vendas (mais de 8.800 negociações passadas) para identificar quais fatores realmente influenciam se um deal fecha ou não. Testamos 13 hipóteses diferentes e apenas 4 fatores se mostraram estatisticamente relevantes. Os pesos refletem o impacto real de cada fator nos dados:

**🏷️ Produto + Setor do cliente (peso: 35%)**
Analisamos a taxa de conversão de cada combinação de produto e setor. A variação é de 52% a 73% — são 20 pontos de diferença, o segundo maior preditor nos dados. Por exemplo, MG Special para telecom fecha 73% das vezes, enquanto MG Advanced para serviços fecha só 52%. O peso de 35% reflete esse alto impacto.

**🏢 Histórico da conta (peso: 30%)**
Cada conta tem sua própria taxa de conversão histórica. Varia de 53% (Statholdings) a 75% (Rangreen) — são 22 pontos de diferença. Contas que historicamente fecham mais deals continuam fechando. O peso de 30% reflete que a conta é um preditor forte.

**📅 Momento do trimestre (peso: 20%)**
Descobrimos um padrão trimestral nos dados: meses de final de trimestre (março, junho, setembro, dezembro) convertem em torno de 80%, enquanto meses de início de trimestre caem para ~49%. São 34 pontos de diferença — o maior preditor em teoria. Porém, como esse fator é igual para todos os deals no mesmo momento, ele diferencia menos na prática, por isso o peso é 20% e não maior.

**⏱️ Tempo no pipeline (peso: 15%)**
Analisamos quanto tempo os deals levam para fechar. Descobrimos que:
- O ciclo médio de fechamento (Won) é de **52 dias**
- 75% dos deals que fecham, fecham em até **88 dias**
- **Nenhum deal na história fechou após 138 dias**

Isso significa que deals abertos há mais de 140 dias provavelmente estão mortos. O peso é 15% porque a relação entre tempo e conversão não é linear — deals muito novos (0-30 dias) também têm conversão mais baixa (57%) porque muitos ainda vão cair.

---

### Bônus de recorrência 🔄

Se a conta já comprou **esse mesmo produto** antes, o deal recebe pontos extras. Isso reflete a realidade: clientes recorrentes tendem a comprar de novo.

- Nunca comprou esse produto: **+0 pontos** (neutro, sem penalidade)
- 1 a 3 compras anteriores: **+5 pontos**
- 4 a 10 compras anteriores: **+10 pontos**
- 11 ou mais compras: **+15 pontos**

O bônus nunca reduz o score — apenas aumenta. Quem não tem recorrência fica exatamente com a probabilidade base.

Quando há bônus, o score é normalizado para manter a escala de 0 a 100 (dividido por 115 e multiplicado por 100, onde 115 é o máximo teórico: 100 da probabilidade + 15 do bônus).

---

### E o valor do deal?

O valor do deal **NÃO** está dentro do score — porque mede coisas diferentes. O score diz "qual a chance de fechar". O valor diz "quanto vale se fechar".

Use o filtro **💰 Faixa de Valor** na barra lateral para focar nos deals do tamanho que você quer trabalhar, e use o score para priorizar dentro dessa faixa.

---

### O que significam as cores:

🟢 **Verde (acima de 70)** — Alta probabilidade de fechar. Priorize.
🟡 **Amarelo (40 a 70)** — Probabilidade moderada. Acompanhe.
🔴 **Vermelho (abaixo de 40)** — Baixa probabilidade. Reavalie a abordagem.

---

### Sobre o estágio (🆕 Novo / 🔄 Em andamento):

O estágio **NÃO** afeta o score. O score mede **potencial**, não progresso. Um deal novo (Prospecting) com alto potencial aparece no topo — porque precisa urgentemente do seu primeiro contato antes de esfriar.
""")
```

---

## Mudança 3 — Remover filtro "Faixa de Score" da sidebar

O slider de faixa de score (0-100) não é relevante para o vendedor. Remover completamente.

### Sidebar final (ordem):
1. 💰 Faixa de Valor
2. Escritório Regional
3. Manager
4. Vendedor
5. Stage

Sem slider de score.

---

## Mudança 4 — Recalibrar faixas de tempo no pipeline

### O problema
As faixas atuais (0-60, 60-120, 120-240, 240-365, 365+) estão desalinhadas com a realidade dos dados:
- Cicle time médio Won: 52 dias
- 75% dos Won fecham em até 88 dias
- NENHUM deal Won fechou após 138 dias
- 44% dos deals abertos estão há 180+ dias — provavelmente mortos

### Novas faixas calibradas com dados reais

```python
if pd.isna(engage_date):  # Prospecting
    fator_tempo = 50  # Neutro
else:
    dias = (data_referencia - engage_date).days
    if dias <= 30:
        fator_tempo = 45   # Deal cru, 57.4% conversão histórica
    elif dias <= 60:
        fator_tempo = 60   # Amadurecendo, 65.6% conversão
    elif dias <= 90:
        fator_tempo = 65   # Zona forte, 66.4% conversão
    elif dias <= 120:
        fator_tempo = 60   # Viável mas se aproximando do limite, 70.6% conversão
    elif dias <= 140:
        fator_tempo = 45   # Limite histórico (último Won = 138 dias), urgência
    else:  # 140+ dias
        fator_tempo = 20   # NENHUM deal fechou após 138 dias, provavelmente morto
```

### Justificativa por faixa

| Faixa | Conv. histórica | Pontos | Justificativa |
|-------|----------------|--------|---------------|
| 0-30 dias | 57.4% | 45 | Deal novo, pode ir pra qualquer lado |
| 30-60 dias | 65.6% | 60 | Converão subindo, deal amadurecendo |
| 60-90 dias | 66.4% | 65 | Zona forte — 25% dos Won fecham aqui |
| 90-120 dias | 70.6% | 60 | Ainda viável mas se aproximando do limite |
| 120-140 dias | 75.1% | 45 | Limite — último Won histórico foi em 138 dias |
| 140+ dias | 0% (nenhum Won) | 20 | Provavelmente morto — nenhum deal fechou após 138 dias na história |
| Prospecting | N/A | 50 | Neutro — sem data para calcular |

**Impacto:** ~700 deals abertos que estão há 180+ dias vão cair significativamente no score. Isso é correto — se nenhum deal fechou nesse prazo na história, esses deals estão provavelmente abandonados.

---

## Checklist para o Claude Code

1. [ ] Pipeline Completo como st.dataframe() (planilha) com seletor de deal logo abaixo para explicação
2. [ ] Reescrever caixa "Como funciona o Score?" com explicação completa incluindo justificativa dos pesos e dados reais
3. [ ] Remover filtro "Faixa de Score" (slider) da sidebar
4. [ ] Recalibrar faixas de tempo: 0-30=45, 30-60=60, 60-90=65, 90-120=60, 120-140=45, 140+=20, Prospecting=50
5. [ ] Manter TUDO: filtros (valor, escritório, manager, vendedor, stage), KPIs, Top 5 dinâmico, checklist, badges, boost recorrência, deals em acompanhamento
6. [ ] Testar: deal com 200 dias no pipeline deve ter fator_tempo = 20 (não 55)
