# CONTEXT1.md — Resultado da Etapa 1

## O que foi feito

A Etapa 1 (Estrutura + Dados) foi executada com sucesso. O app.py carrega os 4 CSVs, faz os merges, filtra deals abertos e mostra uma tabela básica.

## Resultado confirmado

- Total de deals abertos: 2.089 (correto)
- Prospecting: 500 (correto)
- Engaging: 1.589 (correto)
- Tabela exibindo: ID, Conta, Setor, Produto, Preço, Stage, Vendedor, Manager, Escritório, Data Engaging, Dias no Pipeline
- A aplicação roda sem erros com `streamlit run app.py`

## Problemas identificados para corrigir na Etapa 2

### Problema 1 — Merge com accounts falha em alguns deals
Vários deals mostram Conta e Setor como "None". Isso significa que o nome da conta no sales_pipeline.csv não encontrou match no accounts.csv. 

**Solução:** Ao fazer o merge, usar left join (já deve estar). Nos deals onde setor é None, usar "unknown" como fallback para não quebrar o cálculo de setor+produto.

### Problema 2 — Nome do produto inconsistente
O produto "GTXPro" no sales_pipeline.csv aparece com Preço "None" porque no products.csv o nome é "GTX Pro" (com espaço). 

**Solução:** Antes do merge com products, criar um mapeamento de normalização:
```python
product_name_map = {
    "GTXPro": "GTX Pro",
    "GTX Plus Basic": "GTX Plus Basic",
    "GTX Plus Pro": "GTX Plus Pro",
    "GTX Basic": "GTX Basic", 
    "MG Special": "MG Special",
    "MG Advanced": "MG Advanced",
    "GTK 500": "GTK 500"
}
```
Ou simplesmente fazer strip() e comparação case-insensitive no merge.

Verifique todos os nomes de produto no pipeline vs products.csv e trate as inconsistências.

### Problema 3 — Dias no pipeline muito altos
Os deals mostram 3.400+ dias no pipeline. Isso é porque os dados são de 2016-2017 e o cálculo usa a data de hoje (2026). Isso é esperado dado o dataset — não é um bug. Porém, para a lógica de scoring, as faixas de tempo (0-30, 30-60, 60-90, 90+) vão classificar todos os deals em Engaging como 90+ dias.

**Solução:** Isso é uma limitação do dataset, não da lógica. No mundo real, os dados seriam atuais. Para o MVP, manter o cálculo como está — o fator tempo tem peso baixo (15%) e variação quase neutra justamente porque identificamos ambiguidade nos dados. Registrar como limitação na documentação final.

## O que a Etapa 2 deve fazer

Agora que os dados carregam corretamente, a Etapa 2 adiciona o scoring:

1. Corrigir os problemas 1 e 2 acima
2. Calcular taxas de conversão históricas (setor+produto)
3. Implementar os 4 fatores do Score de Probabilidade
4. Implementar o Score de Valor (logarítmico)
5. Calcular o Score Final
6. Adicionar colunas de score na tabela
7. Ordenar por Score Final decrescente

A lógica completa de cada fator está em INSTRUCTIONS.md seção 2.

## Decisão de design: como cada vendedor vê seus deals

### O problema
A ferramenta é para o vendedor usar no dia a dia. Cada vendedor precisa ver apenas os seus deals, não o pipeline inteiro.

### Opções consideradas

**Opção A — Login/senha por vendedor:** Cada vendedor teria um usuário e senha. Ao logar, veria apenas seus deals automaticamente.
- Descartada: consome tempo de implementação que deveria ir para o scoring e a interface. O avaliador do G4 precisaria de credenciais para testar, o que dificulta a avaliação. Estamos num MVP de 4-6 horas, não num sistema de produção.

**Opção B — Filtro por vendedor na sidebar:** O vendedor abre a ferramenta, seleciona seu nome num dropdown, e vê apenas seus deals.
- Escolhida: funcional, rápido de construir, permite que o avaliador teste com qualquer vendedor. Simula o comportamento real sem complexidade desnecessária.

### Implementação na Etapa 2

A sidebar deve ter filtros encadeados nesta ordem:
1. **Escritório Regional** (Todos / Central / East / West)
2. **Manager** (filtra baseado no escritório selecionado)
3. **Vendedor** (filtra baseado no manager selecionado)
4. **Stage** (Todos / Prospecting / Engaging)
5. **Faixa de Score** (slider 0-100)

Quando o vendedor seleciona seu nome, a tabela e os KPIs mostram APENAS os deals dele. O comportamento padrão (Todos) mostra o pipeline completo — útil para managers e para o avaliador testar.

### Evolução futura (registrar na documentação)
Em produção, cada vendedor teria login próprio com SSO integrado ao CRM, vendo automaticamente apenas seus deals ao abrir a ferramenta. No MVP, o filtro por nome simula esse comportamento.
