"""
Challenge - Enunciado do Challenge 003
"""

import streamlit as st

st.set_page_config(page_title="Challenge", page_icon="🏆", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

st.markdown("""
# 🏆 Challenge 003 — Lead Scorer

**Área:** Vendas / RevOps &nbsp;|&nbsp; **Tipo:** Build (construir solução funcional) &nbsp;|&nbsp; **Time budget:** 4–6 horas

---

## 📋 Contexto

Você é o novo AI Master da área de Vendas. O time comercial tem 35 vendedores distribuídos em escritórios regionais, gerenciados por managers, trabalhando um pipeline de ~8.800 oportunidades. Hoje, a priorização é feita "no feeling" — cada vendedor decide quais deals focar com base na própria experiência e intuição.

A Head de Revenue Operations te chamou e disse:

> *"Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."*

Este é o challenge mais "mão na massa". O deliverable principal é **software funcionando** — não um documento.

---

## 🗄️ Dados Disponíveis

Quatro tabelas de um CRM, todas interconectadas:

**Dataset:** CRM Sales Predictive Analytics (licença CC0)
""")

import pandas as pd

dados_tabelas = {
    "Arquivo": ["accounts.csv", "products.csv", "sales_teams.csv", "sales_pipeline.csv"],
    "O que contém": [
        "Contas clientes — setor, receita, número de funcionários, localização, empresa-mãe",
        "Catálogo de produtos com série e preço",
        "Vendedores com seu manager e escritório regional",
        "Pipeline completo — cada oportunidade com stage, datas, vendedor, produto, conta e valor de fechamento",
    ],
    "Registros": ["~85", "7", "35", "~8.800"],
    "Campo-chave": ["account", "product", "sales_agent", "opportunity_id → liga tudo"],
}

st.dataframe(pd.DataFrame(dados_tabelas), use_container_width=True, hide_index=True)

st.markdown("""
**Estrutura dos dados:**
```
accounts ←── sales_pipeline ──→ products
                    ↓
               sales_teams
```

O `sales_pipeline.csv` é a tabela central. Cada registro é uma oportunidade com:
- **deal_stage:** Prospecting, Engaging, Won, Lost
- **engage_date / close_date:** timeline do deal
- **close_value:** valor real de fechamento (0 se Lost)

---

## 📦 O Que Entregar

### 1. Solução Funcional *(obrigatório)*

Construa algo que um vendedor possa usar. Não importa a tecnologia — importa que funcione.

**Exemplos de soluções válidas:**
- Aplicação web (Streamlit, React, HTML+JS, qualquer coisa)
- Dashboard interativo (Plotly Dash, Retool, Metabase)
- CLI tool ou script que gera relatório priorizado
- API que recebe dados de um deal e retorna score + explicação
- Planilha inteligente com fórmulas de scoring
- Bot que envia prioridades por Slack/email

**Requisitos mínimos:**
- ✅ Precisa rodar (não é mockup, wireframe ou PowerPoint)
- ✅ Precisa usar os dados reais do dataset
- ✅ Precisa ter lógica de scoring/priorização (não é só ordenar por valor)
- ✅ O vendedor precisa entender **por que** um deal tem score alto ou baixo

### 2. Documentação Mínima *(obrigatório)*
- **Setup:** Como rodar a solução (dependências, comandos, URL)
- **Lógica:** Que critérios de scoring você usou e por quê
- **Limitações:** O que a solução não faz e o que precisaria pra escalar

### 3. Process Log *(obrigatório)*

Evidências de como você usou IA para construir. Leia o Guia de Submissão.

> Este challenge é especialmente interessante para quem usa "vibe coding" — Cursor, Claude Code, Replit Agent, v0, etc. Mostre o processo.

---

## 🏅 Critérios de Qualidade
""")

criterios = {
    "Critério": [
        "A solução funciona de verdade?",
        "O scoring faz sentido?",
        "O vendedor (não-técnico) consegue usar e entender?",
        "A interface ajuda a tomar decisão ou só mostra dados?",
        "O código é limpo o suficiente pra outro dev dar manutenção?",
    ],
    "O que avaliam": [
        "Dá pra rodar seguindo as instruções?",
        "Usa as features certas? Vai além do óbvio?",
        "UX e clareza das recomendações",
        "Decision-support vs data dump",
        "Qualidade e legibilidade do código",
    ],
}

st.dataframe(pd.DataFrame(criterios), use_container_width=True, hide_index=True)

st.markdown("""
---

## 💡 Dicas

- **A Head de RevOps não pediu ML perfeito.** Pediu algo útil. Comece simples, itere.
- Deal stage, tempo no pipeline, tamanho da conta, produto e vendedor são features óbvias. **O que mais importa? Olhe os dados.**
- Um scoring baseado em **regras + heurísticas**, bem apresentado, vale mais que um XGBoost sem interface.
- **Explainability ganha.** Se o vendedor entender POR QUE o deal tem score 85, a ferramenta é 10× mais útil que um número sem contexto.
- Pense no uso real: **o vendedor abre isso na segunda-feira de manhã.** O que ele precisa ver?
- **Bonus:** se a solução tiver filtro por vendedor/manager/região, fica imediatamente mais útil.
""")
