# Solução — Lead Scoring Inteligente

---

## Visão geral

Esta solução implementa um sistema de priorização de leads baseado em critérios reais de negócio.

O objetivo é ajudar vendedores e empresas a focarem nos leads com maior probabilidade de fechamento e maior impacto financeiro, evitando desperdício de tempo com oportunidades de baixo valor.

---

## Como funciona

O sistema avalia um lead com base em cinco fatores principais:

### 1. ICP Fit
Avalia o quanto o lead se encaixa no perfil ideal de cliente.

### 2. Dor / Impacto
Mede o tamanho do problema do cliente e o impacto financeiro dessa dor.

### 3. Timing
Identifica se o cliente quer resolver o problema agora ou apenas no futuro.

### 4. Estágio do Funil
Determina o nível de maturidade do lead dentro do processo de compra.

### 5. Autoridade de decisão
Verifica se o contato possui poder de decisão ou depende de terceiros.

---

## Lógica de scoring

Cada fator recebe um peso baseado na sua influência no fechamento da venda.

Exemplo:

- ICP alto → +20 pontos  
- Dor alta → +25 pontos  
- Timing imediato → +20 pontos  
- Estágio avançado → +15 pontos  
- Decisor direto → +20 pontos  

O score final é a soma desses fatores.

---

## Output do sistema

O sistema retorna:

- Score numérico total  
- Classificação do lead (Alta, Média, Baixa prioridade)  
- Explicação dos motivos do score  
- Sugestões de ação para o vendedor  

---

## Interface (app.py)

Foi criada uma interface simples usando Streamlit que permite:

- Inserir características do lead  
- Calcular automaticamente o score  
- Visualizar recomendações de ação  

---

## Como rodar (opcional)

Caso queira testar localmente:

```bash
pip install -r requirements.txt
streamlit run app.py
