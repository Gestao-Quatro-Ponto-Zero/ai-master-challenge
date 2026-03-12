# Prompt para Lovable CRM

**User:** Daniel Schkolnick (schkolnick18@gmail.com)  
**Created:** 3/11/2026 22:10:08  
**Updated:** 3/11/2026 22:11:28  
**Exported:** 3/11/2026 23:16:23  
**Link:** [https://chatgpt.com/g/g-680aa6a76bf4819187fb7c001e02ca83-lovable-dev-specialist-por-rafael-milagre/c/69b21270-3c4c-8330-8862-d61d48ba74f3](https://chatgpt.com/g/g-680aa6a76bf4819187fb7c001e02ca83-lovable-dev-specialist-por-rafael-milagre/c/69b21270-3c4c-8330-8862-d61d48ba74f3)  

## Response:
Pensou por 6s

Aqui vai um **PROMPT COMPLETO (copiar e colar no Lovable)** já estruturado para ele construir exatamente o que você descreveu, **usando a planilha anexada como “database” (não Supabase)**.

* * *

PROMPT COMPLETO PARA O LOVABLE (CRM + Score Size + Painel Gerencial) — DB via Planilha
--------------------------------------------------------------------------------------

**Contexto (obrigatório ler antes de executar):**  
Você vai desenvolver um app web full-stack (MVP funcional, não mockup) que simula um CRM operacional para vendedores + um painel gerencial por manager.  
**A fonte de dados (database) NÃO é Supabase/Lovable Cloud**: a base vem de uma **planilha Excel anexada** (aba `sales_pipeline`). O app deve **carregar a planilha ao iniciar**, tratar dados inválidos e calcular métricas e scores de forma **determinística** (sem machine learning).  
Stack sugerida: **Next.js + React + Tailwind**. Pode usar bibliotecas utilitárias (ex.: leitura de XLSX) desde que seja estável.

* * *

1) Fonte de Dados (Planilha como DB)
====================================

1.1 Origem e esquema
--------------------

Use a planilha anexada como base principal. Ler a aba: `sales_pipeline`.

**Colunas disponíveis:**

*   `opportunity_id`
*   `sales_agent`
*   `manager`
*   `account`
*   `employees`
*   `sector`
*   `product`
*   `deal_stage`
*   `engage_date`
*   `close_date`
*   `close_value`

1.2 Estratégia de ingestão (sem Supabase)
-----------------------------------------

Implemente **uma camada de “Data Source”** que:

1.  Carrega a planilha no start (seed local) **e** permite o usuário **substituir a planilha** via upload (para atualizar o “database”).
2.  Converte as linhas em objetos normalizados.
3.  Mantém os dados em memória (state) e recalcula scores ao mudar o arquivo.

**Requisito:** o app tem que funcionar mesmo sem backend real — a planilha é o “DB”.  
**Sugestão técnica:** usar `xlsx` (SheetJS) para parse no client (ou route handler no Next para parse).  
**Persistência opcional do arquivo do usuário:** localStorage/IndexedDB (bom ter, mas não obrigatório para o MVP).

* * *

2) Regras de Tratamento de Dados
================================

2.1 Valores inválidos/incompletos
---------------------------------

Considere como “dado incompleto” qualquer campo que esteja:

*   vazio, `null`, `undefined`
*   `#REF!`
*   string vazia
*   valor não utilizável (ex.: employees não numérico)

Crie helpers:

*   `isInvalid(value): boolean`
*   `parseEmployees(value): number | null`
*   `parseDate(value): Date | null` (aceitar formatos comuns; se falhar, null)

2.2 Campos obrigatórios para Score Size
---------------------------------------

O Score Size depende **obrigatoriamente** de:

*   `sector`
*   `employees`

Se qualquer um estiver incompleto:

*   **não atribuir** Score Size A/B/C/D
*   **atribuir badge** “Dados incompletos”
*   lead **continua no Kanban**
*   lead **entra nas contagens do dashboard** como incompleto
*   lead **não entra no cálculo de quartis** A/B/C/D

2.3 Pipeline oficial (Kanban)
-----------------------------

As colunas do Kanban devem ser **exatamente**:

*   `Prospecting`
*   `Engaging`
*   `Lost`
*   `Won`

Mapeie `deal_stage` para essas colunas (se vier diferente, normalizar; se inválido, colocar em Prospecting e marcar aviso em console).

* * *

3) Métricas Históricas (base para Score)
========================================

3.1 Base histórica para cálculo
-------------------------------

Calcular win rate e tempo médio **somente** com deals fechados:

*   `deal_stage = Won` ou `deal_stage = Lost`

Ignorar `Prospecting` e `Engaging` nesses cálculos.

3.2 Win rate por grupo
----------------------

Para cada grupo analisado:

*   `win_rate = won / (won + lost)`

3.3 Tempo médio por grupo
-------------------------

Para cada grupo analisado:

*   `tempo_fechamento_dias = close_date - engage_date` (em dias)

Regras:

*   Se `engage_date` ou `close_date` estiver inválida em deals fechados: **ignorar essa linha no cálculo de tempo** (para não quebrar).
*   Se um grupo não tiver amostras válidas para tempo: tratar como null e depois lidar na normalização com fallback.

3.4 Buckets de employees (porte)
--------------------------------

Classificar `employees` em 4 faixas:

*   `0 a 250`
*   `251 a 1000`
*   `1001 a 5000`
*   `acima de 5000`

Crie função `getEmployeeBucket(employees): "0-250" | "251-1000" | "1001-5000" | "5001+"`.

* * *

4) Normalização e Score Size Numérico
=====================================

4.1 Variáveis estruturais do score (4 componentes)
--------------------------------------------------

O Score Size é a média de **4 notas (0-100)**:

1.  **nota\_segmento\_winrate**
2.  **nota\_segmento\_tempo**
3.  **nota\_porte\_winrate**
4.  **nota\_porte\_tempo**

Tudo vem da própria base histórica.

4.2 Normalização obrigatória (0 a 100)
--------------------------------------

*   Para **win rate**: quanto maior, melhor → nota maior
*   Para **tempo**: quanto menor, melhor → nota maior (inverter)

Sugestão concreta (implementar assim):

*   Para uma métrica X (ex.: win\_rate) por grupos, pegar min e max entre grupos válidos.
    *   Se `max == min`, todos recebem 50 (ou 100) para evitar divisão por zero.
    *   `score = ((x - min) / (max - min)) * 100`
*   Para tempo (onde menor é melhor):
    *   `score = ((max - x) / (max - min)) * 100`

Fallbacks:

*   Se um grupo não tem métrica (null) por falta de dados históricos, usar nota 50 (neutro) **mas documentar essa regra** no código e tooltip.

4.3 Fórmula final do score estrutural
-------------------------------------

Para cada lead com `sector` e `employees` válidos:

*   `score_size_numerico = (v1 + v2 + v3 + v4) / 4`

* * *

5) Classificação em Quartis (A/B/C/D) — Dinâmico
================================================

Após calcular `score_size_numerico` para **todos os leads completos**:

*   Top 25% = **Score A**
*   Próximo 25% = **Score B**
*   Próximo 25% = **Score C**
*   Último 25% = **Score D**

Regras:

*   Quartis devem ser recalculados toda vez que a base mudar (upload de planilha).
*   Leads com “Dados incompletos” **não entram** nos quartis.
*   Se a amostra for pequena, ainda assim dividir proporcionalmente (ordenar e atribuir por percentil/índice).

* * *

6) CRM Operacional (Kanban)
===========================

6.1 Cards obrigatórios (conteúdo)
---------------------------------

Cada card deve exibir:

*   **Nome do deal**: `${account} - ${product}`
*   Produto (`product`)
*   Empresa (`account`)
*   Vendedor (`sales_agent`)
*   Etapa atual (`deal_stage`)
*   ID do lead (`opportunity_id`)
*   Setor (`sector`)

E badges:

*   Badge **Score Size** (A/B/C/D) quando aplicável
*   Badge **Dados incompletos** quando aplicável (prioridade visual alta)

Sugestão visual (implementar):

*   A: destaque máximo
*   B: médio alto
*   C: médio
*   D: baixo
*   Dados incompletos: alerta forte

6.2 UX obrigatória (filtros + busca + ordenação)
------------------------------------------------

O CRM precisa permitir:

*   filtro por `manager`
*   filtro por `sales_agent`
*   filtro por `score size` (A/B/C/D)
*   filtro “apenas leads com dados incompletos”
*   busca por `account` (nome empresa)
*   busca por `opportunity_id`

Ordenação padrão recomendada:

1.  Dados incompletos
2.  Score A
3.  Score B
4.  Score C
5.  Score D

(ou oferecer seletor de ordenação: score/empresa/vendedor/estágio)

6.3 Explicabilidade
-------------------

Adicionar um tooltip/legenda fixa:

> “Score Size representa o potencial estrutural do lead com base em histórico de conversão e velocidade por segmento e porte. Não é predição absoluta.”

E um destaque para qualidade cadastral:

*   Mostrar contagem de “Dados incompletos” no topo e/ou um alerta quando alto.

* * *

7) Painel Gerencial por Manager
===============================

7.1 Filtro por manager
----------------------

A tela de gestão deve permitir selecionar um `manager` e ver apenas o time dele.

7.2 Métricas obrigatórias
-------------------------

Calcular e exibir:

1.  **Qtd de leads por vendedor**
    *   total por `sales_agent`
*   (opcional) distribuição por estágio em coluna adicional
    2.  **Qtd de leads por vendedor e por Score Size**
    *   Score A, B, C, D por vendedor
    3.  **Leads com dados incompletos por vendedor**
    *   total absoluto
*   percentual sobre a carteira do vendedor
    4.  **Tempo médio de fechamento**
    *   geral do manager
*   por vendedor  
    **Somente** com `Won + Lost` e apenas linhas com datas válidas
    5.  **Win rate**
    *   geral do manager
*   por vendedor  
    **Somente** com `Won + Lost`

7.3 Estrutura visual recomendada (implementar)
----------------------------------------------

**Bloco 1 — Cards resumo do time**

*   total leads
*   total completos
*   total incompletos
*   tempo médio do time
*   win rate do time

**Bloco 2 — Tabela por vendedor**  
Colunas:

*   vendedor
*   total leads
*   A / B / C / D
*   incompletos (total e %)
*   tempo médio de fechamento
*   win rate

**Bloco 3 — Gráficos simples**

*   barras empilhadas: Score A/B/C/D por vendedor
*   barras: incompletos por vendedor
*   barras: tempo médio por vendedor
*   barras: win rate por vendedor

(Use uma lib de gráficos simples e confiável; manter visual limpo.)

* * *

8) Regras de Negócio (restrições duras)
=======================================

1.  **Score Size é estrutural, não comportamental**  
    Não usar para cálculo:
    *   `manager`
*   `sales_agent`
*   `deal_stage`
*   `close_value`
*   tempo individual do deal atual (fora da base histórica agregada)
    2.  **Sem machine learning**  
    Tudo determinístico, baseado em métricas históricas agregadas.
3.  **Robustez**  
    Não quebrar interface por valores inválidos. Sempre fallback seguro.

* * *

9) Requisitos de Entrega (MVP utilizável)
=========================================

Ao abrir a aplicação:

*   Vendedor consegue ver Kanban, filtrar, buscar, entender score e incompletos.
*   Manager consegue ver dashboard por manager, com tabela e gráficos.

* * *

10) Backlog de Desenvolvimento (épicos → features → tarefas)
============================================================

Épico 1 — Ingestão e tratamento da base
---------------------------------------

*   Feature: Leitura da planilha (seed + upload)
    *   Tarefa: parser XLSX aba `sales_pipeline`
    *   Tarefa: normalização de colunas e tipos
    *   Tarefa: validação `isInvalid`, `parseEmployees`, `parseDate`
*   Feature: Camada DataSource
    *   Tarefa: estado global dos dados
    *   Tarefa: recomputar tudo ao trocar arquivo
    *   Tarefa: estados de loading/erro/empty

Épico 2 — Cálculo das métricas históricas
-----------------------------------------

*   Feature: base fechados (Won+Lost)
    *   Tarefa: filtrar deals fechados
*   Feature: métricas por sector
    *   Tarefa: win\_rate por sector
    *   Tarefa: tempo médio por sector
*   Feature: buckets employees
    *   Tarefa: bucketização employees
    *   Tarefa: win\_rate por bucket
    *   Tarefa: tempo médio por bucket
*   Feature: normalização 0-100
    *   Tarefa: normalizador com fallback e proteção min=max

Épico 3 — Score Size (numérico + quartis + incompletos)
-------------------------------------------------------

*   Feature: score\_size\_numerico por lead completo
*   Feature: quartis dinâmicos e atribuição A/B/C/D
*   Feature: regra “Dados incompletos” e exclusão do quartil
*   Feature: testes de sanidade (ex.: percentuais ~25/25/25/25 quando N grande)

Épico 4 — CRM fake (Kanban)
---------------------------

*   Feature: layout Kanban com 4 colunas fixas
*   Feature: card de lead com campos obrigatórios
*   Feature: badges Score e Dados incompletos
*   Feature: filtros + busca + ordenação
*   Feature: legenda/tooltip explicativo

Épico 5 — Painel gerencial
--------------------------

*   Feature: seletor de manager
*   Feature: cards resumo
*   Feature: tabela por vendedor
*   Feature: gráficos
*   Feature: consistência de cálculo (somente Won/Lost em win rate e tempo)

Épico 6 — UX, consistência e explicabilidade
--------------------------------------------

*   Feature: estados vazios e mensagens úteis
*   Feature: loading e erro de upload/parse
*   Feature: destaque de qualidade cadastral (incompletos)
*   Feature: layout moderno, limpo, “ferramenta interna de RevOps”

* * *

11) Critérios de Aceite (checagem final)
========================================

*   ✅ App lê planilha, processa e renderiza sem Supabase
*   ✅ Score Size calculado conforme regras (4 variáveis, normalização 0-100, média)
*   ✅ Quartis dinâmicos A/B/C/D
*   ✅ Leads incompletos marcados, filtráveis e fora do quartil
*   ✅ Kanban com 4 colunas exatas e cards completos
*   ✅ Dashboard por manager com métricas e gráficos obrigatórios
*   ✅ Tooltip explicando score + destaque para “Dados incompletos”

* * *

Observação importante (para você, Lovable)
------------------------------------------

**Não criar tabelas no Lovable Cloud e não integrar Supabase.**  
Toda a lógica deve funcionar a partir do arquivo Excel e do estado local da aplicação.

* * *

Se você quiser, eu também posso te devolver uma **versão “ultra curta”** desse prompt (para gastar menos créditos no Lovable) mantendo as mesmas regras — mas o texto acima já está no formato ideal para o Agent Mode executar de ponta a ponta.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)