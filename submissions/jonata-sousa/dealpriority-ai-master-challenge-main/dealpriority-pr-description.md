# DealPriority — Submissão Challenge 003: Lead Scorer

**Inteligência de priorização para operações comerciais**

---

## 1. Resumo da entrega

Este PR representa a entrega completa do Challenge 003 — Lead Scorer, do processo seletivo de AI Master.

O objetivo era construir uma solução funcional para priorizar oportunidades de vendas, usando dados reais, com lógica de scoring explicável e entregue como produto utilizável — não apenas como análise ou notebook.

A solução entregue é o **DealPriority**: uma aplicação interativa de priorização comercial, com score numérico explicável, filtros operacionais, visualizações para leitura executiva e autenticação. O trabalho passou por inspeção e consolidação dos dados, construção da lógica de score, recalibração para uso operacional, geração de explicações por oportunidade e desenvolvimento da interface.

---

## 2. O que foi entregue

### Aplicação funcional
- Dashboard interativo com KPIs responsivos aos filtros ativos
- Filtros por vendedor, gestor, região, produto, estágio e prioridade
- Gráficos para leitura executiva
- Tabela interativa com paginação
- Painel de detalhe do deal com score destacado, badges de prioridade, razões positivas, razões de risco e ação recomendada
- Header com visão do total filtrado e total geral
- Autenticação com login e logout

### Lógica de priorização
- Score numérico no intervalo 0–100
- Classificação em três faixas operacionais: **Foco Agora**, **Nutrir** e **Baixa Prioridade**
- Score baseado em heurística de negócio, sem caixa-preta
- Recalibração por percentis para tornar a classificação operacionalmente útil

### Preparação e consolidação dos dados
- Inspeção do schema original
- Identificação de chaves e relações entre tabelas
- Join das bases do challenge
- Tratamento de inconsistências
- Criação de variáveis derivadas
- Construção e recalibração do score
- Geração das explicações por oportunidade
- Geração da base final utilizada na interface

### Segurança e acesso
- Rodada de validação de segurança
- Inclusão de autenticação com login e logout
- Preocupação com controle de acesso e exposição de dados

### PWA
- Camada leve de Progressive Web App
- Foco em responsividade, manifest e ícones
- Escopo básico de instalação — sem offline avançado, push notification ou sincronização complexa

---

## 3. Arquitetura da solução

### Dados de origem
Os arquivos do challenge foram usados como base do trabalho. A tabela central foi `sales_pipeline`, enriquecida via joins com `accounts`, `products` e `sales_teams`.

**Etapas do processo de dados:**
1. Inspeção do schema e identificação das chaves de relacionamento
2. Join das tabelas, com `sales_pipeline` como âncora
3. Tratamento da inconsistência entre os valores `GTXPro` e `GTX Pro` no campo de produto
4. Validação do merge com confirmação de que `opportunity_id` não duplicou
5. Identificação de 1.425 registros com `account` ausente na origem — problema existente nos dados brutos, não gerado pelo processo; decisão de não bloquear a análise por isso
6. Criação das variáveis derivadas necessárias para o score
7. Construção do score, recalibração e geração das explicações
8. Exportação da base final para a interface

### Arquivos gerados ao longo do processo

| Arquivo | Descrição |
|---|---|
| `merged_sales_pipeline.csv` | Pipeline após join das tabelas |
| `enriched_sales_pipeline.csv` | Pipeline com variáveis derivadas |
| `lead_scoring_output.csv` | Score inicial |
| `lead_scoring_output_recalibrated.csv` | Score após recalibração |
| `explainable_lead_scoring_output.csv` | Score com explicações (v1) |
| `explainable_lead_scoring_output_v2.csv` | Score com explicações refinadas (v2) |
| `ranked_open_deals_final.csv` | **Base final utilizada na interface** |

A base que alimenta o dashboard é `ranked_open_deals_final.csv`, contendo apenas oportunidades abertas, com score, classificação, explicações e ação recomendada.

---

## 4. Lógica de scoring

### Variáveis utilizadas

| Variável | Descrição |
|---|---|
| `stage_weight` | Peso do estágio atual da oportunidade no funil |
| `seller_win_rate` | Taxa de conversão histórica do vendedor |
| `product_win_rate` | Taxa de conversão histórica do produto |
| `regional_win_rate` | Taxa de conversão histórica da região |
| `manager_win_rate` | Taxa de conversão histórica do gestor |
| `aging_risk_flag` | Flag de risco por tempo excessivo sem avanço |

### Fórmula

```
priority_score = 100 × (
    0.45 × stage_weight +
    0.20 × seller_win_rate +
    0.15 × product_win_rate +
    0.10 × regional_win_rate +
    0.10 × manager_win_rate
) − penalidade de aging
```

**Penalidade:** −10 pontos quando `aging_risk_flag = true`

O score foi limitado ao intervalo **0–100**.

O peso maior foi atribuído ao estágio do funil, que é o sinal mais direto de proximidade ao fechamento. Os demais pesos refletem a influência histórica de cada dimensão no resultado final.

### Recalibração

A primeira distribuição de classificações não resultou em divisões operacionalmente úteis. A solução foi recalibrar com base nos percentis das próprias oportunidades abertas:

| Referência | Valor |
|---|---|
| p50 | 36,4294 |
| p85 | 39,1613 |

**Distribuição após recalibração:**

| Classificação | Quantidade | Percentual |
|---|---|---|
| Foco Agora | 316 | 15,1% |
| Nutrir | 734 | 35,1% |
| Baixa Prioridade | 1.039 | 49,7% |

Essa distribuição entrega uma lista de foco com tamanho realista para uso operacional — nem grande demais para ser ignorada, nem pequena demais para ser insuficiente.

---

## 5. Explicabilidade

Cada oportunidade aberta recebeu os seguintes campos de explicação:

- `top_positive_reason_1` — principal razão positiva para o score
- `top_positive_reason_2` — segunda razão positiva
- `top_risk_reason_1` — principal fator de risco identificado
- `top_risk_reason_2` — segundo fator de risco
- `recommended_action` — ação recomendada com base no score e no perfil da oportunidade

Houve um ciclo de refinamento específico para eliminar contradições lógicas nas explicações geradas — casos em que a mesma variável aparecia simultaneamente como razão positiva e fator de risco.

---

## 6. Interface e experiência

A interface foi construída como uma ferramenta operacional, não como um relatório estático.

**O que o usuário encontra ao entrar:**
- KPIs gerais (total de oportunidades, score médio, distribuição por prioridade) que se atualizam conforme os filtros aplicados
- Filtros por vendedor, gestor, região, produto, estágio e classificação de prioridade
- Gráficos para leitura executiva da distribuição do pipeline
- Tabela de oportunidades com paginação, ordenável por score
- Ao selecionar uma oportunidade: painel de detalhe com score destacado, badge de prioridade, razões positivas, fatores de risco e ação recomendada

**Acesso:**
- Tela de login ao abrir a aplicação
- Logout disponível durante o uso
- Sem acesso público à base de dados

---

## 7. Segurança e autenticação

A entrega incluiu uma rodada de validação de segurança antes da versão final. A autenticação foi adicionada para tornar a solução mais realista do ponto de vista de uso em ambiente comercial, onde o acesso a dados de pipeline precisa ser controlado.

O que foi implementado:
- Tela de login obrigatória para acesso à aplicação
- Funcionalidade de logout
- Preocupação com exposição de dados e controle de acesso

Não foram incluídos detalhes de infraestrutura ou gerenciamento avançado de permissões, pois o escopo é de um challenge — mas a decisão de incluir autenticação foi consciente e alinhada à utilidade real do produto.

---

## 8. PWA

Foi adicionada uma camada leve de Progressive Web App com foco em:
- Responsividade para diferentes telas
- Arquivo de manifest configurado
- Ícones para instalação

O escopo não inclui modo offline avançado, push notifications ou sincronização em background. O objetivo foi permitir que a aplicação possa ser instalada como um app leve, sem complexidade desnecessária para o contexto de um challenge.

---

## 9. Como avaliar a entrega

Esta seção foi escrita para o avaliador técnico e de negócio navegar pela entrega de forma objetiva.

### Por onde começar
1. Acesse a aplicação e realize o login
2. Observe o dashboard com os KPIs gerais: total de oportunidades abertas, distribuição por prioridade e score médio
3. Verifique que os números do header mostram o total filtrado e o total geral lado a lado

### O que checar no score
- Navegue até a tabela e ordene por `priority_score`
- Verifique que os maiores scores correspondem às oportunidades em estágio mais avançado no funil combinadas com vendedores e regiões de alta taxa de conversão
- Identifique oportunidades com `aging_risk_flag` ativo e verifique o desconto de 10 pontos no score

### O que checar nas explicações
- Abra o detalhe de uma oportunidade classificada como **Foco Agora** e leia as razões positivas e a ação recomendada
- Abra o detalhe de uma oportunidade classificada como **Baixa Prioridade** e verifique os fatores de risco
- Confirme que não há contradições lógicas: a mesma variável não deve aparecer como razão positiva e fator de risco simultaneamente

### O que checar nos filtros
- Aplique um filtro por vendedor específico e verifique que os KPIs se atualizam
- Aplique filtros combinados (ex: vendedor + região + estágio) e confirme que a tabela responde corretamente
- Limpe os filtros e verifique que o estado geral é restaurado

### O que checar no detalhe do deal
- Verifique o score numérico e o badge de prioridade
- Leia as duas razões positivas e as duas razões de risco
- Leia a ação recomendada e avalie se é coerente com o perfil da oportunidade
- Compare dois deals com scores próximos mas classificações diferentes para entender os pontos de corte da recalibração

### O que checar na autenticação
- Acesse a aplicação sem estar logado e confirme que o login é exigido
- Realize o logout e confirme que o acesso é bloqueado até nova autenticação

---

## 10. Como rodar

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd dealpriority

# 2. Instale as dependências
npm install
# ou yarn install, conforme o gerenciador configurado no projeto

# 3. Configure as variáveis de ambiente necessárias
# Consulte o arquivo .env.example no repositório

# 4. Inicie o ambiente local
npm run dev
# ou yarn dev

# 5. Acesse a aplicação no navegador
# http://localhost:8080 (ou porta configurada)

# 6. Realize o login com as credenciais configuradas
```

A base de dados utilizada é `ranked_open_deals_final.csv`, incluída no repositório. Não é necessária conexão com banco de dados externo para rodar localmente.

---

## 11. Limitações

Esta seção documenta as limitações conhecidas da entrega — com transparência e sem minimizar.

| Limitação | Contexto |
|---|---|
| **Snapshot estático** | A base é um arquivo CSV gerado a partir dos dados do challenge. Não há integração em tempo real com CRM ou fonte de dados dinâmica. |
| **Registros sem account** | 1.425 oportunidades no pipeline original não possuem `account` associado. Isso é uma inconsistência dos dados brutos, não introduzida pelo processo. Essas oportunidades foram mantidas na análise. |
| **Score heurístico** | A lógica de score é baseada em regras de negócio e pesos definidos por julgamento — não por modelo preditivo treinado. Isso favorece transparência, mas não otimiza estatisticamente a predição de conversão. |
| **Sem deploy público** | A aplicação não possui URL pública ativa. Veja seção 13. |
| **PWA em escopo leve** | A camada de PWA cobre apenas instalação básica. Funcionalidades como offline avançado e push notifications estão fora do escopo. |

---

## 12. Uso de IA no processo

A construção desta solução foi assistida por ferramentas de IA em diferentes etapas, com validação e decisão humana ao longo de todo o processo.

| Ferramenta | Uso |
|---|---|
| **ChatGPT** | Estratégia da solução, definição dos pesos do score, estruturação dos prompts, documentação e refinamento das explicações |
| **Julius AI** | Inspeção do schema, execução dos joins, validação do merge, construção do score, recalibração por percentis e geração das explicações por oportunidade |
| **Lovable** | Construção da interface — componentes, layout, filtros, tabela, painel de detalhe e autenticação |

O processo foi iterativo: cada etapa gerou artefatos que foram revisados, questionados e refinados antes de avançar. O julgamento humano esteve presente nas decisões de peso, no tratamento das inconsistências, na recalibração da classificação e no refinamento das explicações.

---

## 13. Observação sobre deploy

Nenhuma URL pública foi disponibilizada para esta entrega.

A decisão foi intencional: criar e manter infraestrutura de deploy em um contexto de challenge/teste geraria custo sem retorno proporcional. O foco foi garantir que o produto fosse funcional, bem estruturado, documentado e executável localmente.

A solução está pronta para evoluir para um deploy produtivo — a estrutura da aplicação, a base de dados e a lógica de score estão organizadas para isso.

---

## 14. Fechamento

O DealPriority foi construído com foco em utilidade operacional real. A decisão de não seguir por um caminho de machine learning mais pesado foi consciente: um score explicável, com classificação calibrada e explicações legíveis, entrega mais valor para um vendedor ou gestor do que um modelo de alta acurácia sem transparência.

O trabalho cobriu todas as dimensões solicitadas no challenge — dados reais, lógica de priorização, produto funcional e explicabilidade — e adicionou autenticação e uma camada de PWA como decisões de qualidade de entrega.
