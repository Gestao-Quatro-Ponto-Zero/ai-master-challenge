# DealPriority
### Inteligência de priorização para operações comerciais

## Acesso rápido

**Demo online:**  
https://opportunity-focus-hub.lovable.app/auth


> Para avaliação, acesse a demo online no link acima.

---

## 1. Visão Geral

**DealPriority** é uma ferramenta interativa de priorização comercial desenvolvida para o **Challenge 003 — Lead Scorer**, do processo seletivo de AI Master.

O produto foi construído com foco em utilidade real: um dashboard funcional que ajuda vendedores e gestores a identificar quais oportunidades abertas merecem atenção primeiro, usando um score explicável e recomendações práticas por deal.

A solução cobre o ciclo completo — do tratamento dos dados ao produto final com autenticação — e foi construída com uso estratégico de ferramentas de IA em todas as etapas.

---

## 2. Problema de Negócio

Em operações comerciais com pipeline ativo, o volume de oportunidades abertas torna inviável dar atenção uniforme a todos os deals. Vendedores precisam decidir, a cada dia, onde investir tempo e energia.

Sem critério claro de priorização, os riscos são:

- Tempo investido em deals com baixa probabilidade de fechamento
- Deals avançados no funil perdendo força por falta de cadência
- Gestores sem visão clara do estado real da carteira por vendedor, região ou produto

O objetivo do challenge era construir uma **solução funcional** — não apenas uma análise — que ajudasse times de vendas a tomar melhores decisões de alocação de atenção.

---

## 3. Solução Proposta

Em vez de desenvolver um modelo de machine learning complexo e de difícil explicação para o vendedor, a decisão foi construir uma **heurística de scoring explicável**, combinada com uma interface prática de uso diário.

Essa escolha foi intencional. O critério do challenge era software funcionando, com lógica de priorização e entendimento pelo vendedor do motivo do score — não performance preditiva sofisticada.

A solução entregue é um **dashboard/app interativo** que:

- Calcula um score de prioridade por oportunidade aberta
- Classifica os deals em três níveis: **Foco Agora**, **Nutrir** e **Baixa Prioridade**
- Explica, em linguagem de negócio, os fatores positivos e os riscos de cada deal
- Gera uma recomendação de ação por oportunidade
- Permite filtragem por vendedor, gestor, região, produto, estágio e prioridade
- Inclui autenticação de acesso

---

## 4. Principais Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| Score por deal | Calculado com base em múltiplos fatores históricos e operacionais |
| Classificação em 3 níveis | Foco Agora / Nutrir / Baixa Prioridade |
| Razões positivas | Até 2 fatores que elevam o score do deal |
| Razões de risco | Até 2 fatores que reduzem ou alertam sobre o deal |
| Ação recomendada | Sugestão prática e objetiva por oportunidade |
| Filtros interativos | Por vendedor, gestor, região, produto, estágio e prioridade |
| KPIs dinâmicos | Respondem aos filtros aplicados |
| Gráficos de carteira | Distribuição por prioridade, estágio, vendedor e gestor |
| Painel de detalhe | Visão completa de cada deal com score em destaque |
| Autenticação | Login e logout integrados à aplicação |
| PWA básico | Manifest, ícones e suporte a instalação |

---

## 5. Arquitetura da Solução

```
Dados brutos (CSV)
        │
        ▼
  Exploração e tratamento (Julius AI)
        │
        ├── Joins: sales_pipeline + accounts + sales_teams + products
        ├── Padronização de inconsistências (ex: GTXPro → GTX Pro)
        ├── Criação de variáveis derivadas
        ├── Cálculo do priority_score
        ├── Recalibração da classificação por percentis
        └── Geração de explicações e ranking final
                │
                ▼
        ranked_open_deals_final.csv
                │
                ▼
        Interface interativa (Lovable)
                │
                ├── Dashboard com filtros, KPIs, gráficos e tabela
                ├── Painel de detalhe por deal
                ├── Autenticação (login/logout)
                └── PWA básico
```

**Stack utilizada:**

- **Lovable** — construção da interface interativa do produto
- **Julius AI** — exploração, tratamento, joins, criação de variáveis, scoring, explicações e ranking
- **ChatGPT** — estratégia de solução, estruturação da lógica de scoring, prompts, documentação e refinamento

---

## 6. Base de Dados e Preparação

### Origem

A base foi construída a partir dos arquivos CSV fornecidos no challenge, tendo `sales_pipeline` como tabela central.

### Etapas de tratamento

1. Inspeção do schema e identificação de chaves de join
2. Join de `sales_pipeline` com `accounts` pela coluna `account`
3. Join com `sales_teams` pela coluna `sales_agent`
4. Join com `products` pela coluna `product`
5. Identificação de inconsistência: `GTXPro` no pipeline vs. `GTX Pro` na tabela de produtos
6. Criação de regra de padronização para resolver o mismatch
7. Validação do merge e confirmação de ausência de duplicação por `opportunity_id`
8. Identificação de 1.425 linhas com `account` ausente na origem
9. Decisão de seguir a análise sem bloquear por ausência de account (ver seção de Decisões de Produto)
10. Criação de variáveis derivadas e cálculo do score
11. Recalibração da classificação final
12. Geração de explicações textuais e ranking

### Arquivos gerados ao longo do processo

| Arquivo | Descrição |
|---|---|
| `merged_sales_pipeline.csv` | Base após joins |
| `enriched_sales_pipeline.csv` | Base com variáveis derivadas |
| `lead_scoring_output.csv` | Primeira versão do score |
| `lead_scoring_output_recalibrated.csv` | Score com classificação recalibrada |
| `explainable_lead_scoring_output.csv` | Com campos de explicação (v1) |
| `explainable_lead_scoring_output_v2.csv` | Com correção de contradições lógicas |
| `ranked_open_deals_final.csv` | Base final utilizada no app |

### Base final utilizada no app

O arquivo `ranked_open_deals_final.csv` contém exclusivamente as oportunidades com status **aberto**, ordenadas por `priority_score` decrescente. Cada linha inclui:

- Score e label de prioridade
- Razões positivas e de risco
- Ação recomendada
- Colunas de contexto do deal (vendedor, gestor, região, produto, estágio, valor estimado)

---

## 7. Lógica de Scoring

### Princípio

O score foi desenhado como uma **heurística explicável**, não como um modelo preditivo opaco. A premissa é que o vendedor precisa entender por que um deal tem score alto ou baixo — isso só é possível quando os fatores são legíveis e conectados à realidade operacional.

### Variáveis derivadas criadas

| Variável | Descrição de negócio |
|---|---|
| `deal_status_group` | Separa oportunidades abertas, ganhas e perdidas |
| `deal_age_days` | Mede há quantos dias o deal está aberto |
| `days_to_close` | Calcula o tempo histórico médio até fechamento |
| `seller_win_rate` | Taxa histórica de fechamento do vendedor |
| `product_win_rate` | Taxa histórica de fechamento por produto |
| `regional_win_rate` | Desempenho histórico da região comercial |
| `manager_win_rate` | Desempenho histórico do gestor responsável |
| `close_value_band` | Faixa de valor estimado do deal |
| `aging_risk_flag` | Sinaliza deals envelhecendo acima do padrão ideal |
| `stage_weight` | Traduz o avanço no funil em peso operacional |
| `priority_label_suggestion` | Label de prioridade sugerida antes da recalibração |

### Fórmula do score

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

O score final foi limitado ao intervalo **0 a 100**.

### Lógica de pesos

O maior peso foi atribuído ao `stage_weight` (45%) porque o avanço no funil é o sinal mais objetivo de maturidade de um deal. Os demais fatores refletem contexto histórico: quem vende, o quê, onde e sob qual gestão.

### Recalibração da classificação

A primeira versão do score gerou uma distribuição desequilibrada: nenhum deal era classificado como "Foco Agora", tornando o dashboard operacionalmente inútil.

A solução foi manter a fórmula do score intacta e **recalibrar a classificação com base nos percentis das oportunidades abertas**:

| Percentil | Valor |
|---|---|
| p50 | 36,4294 |
| p85 | 39,1613 |

**Regra de classificação final:**

| Condição | Label |
|---|---|
| `priority_score >= p85` | **Foco Agora** |
| `p50 <= priority_score < p85` | **Nutrir** |
| `priority_score < p50` | **Baixa Prioridade** |

**Distribuição resultante:**

| Label | Quantidade | % |
|---|---|---|
| Foco Agora | 316 | 15,1% |
| Nutrir | 734 | 35,1% |
| Baixa Prioridade | 1.039 | 49,7% |

Essa distribuição reflete uma lógica operacional coerente: a minoria dos deals merece atenção imediata, enquanto a maior parte aguarda desenvolvimento ou descarte.

---

## 8. Explicabilidade

Para cada oportunidade aberta, foram gerados campos de explicação em linguagem de negócio:

| Campo | Conteúdo |
|---|---|
| `top_positive_reason_1` | Principal fator que eleva o score |
| `top_positive_reason_2` | Segundo fator positivo |
| `top_risk_reason_1` | Principal fator de alerta ou risco |
| `top_risk_reason_2` | Segundo fator de risco |
| `recommended_action` | Sugestão de próximo passo para o vendedor |

**Exemplos de linguagem utilizada:**

- *Estágio avançado no funil*
- *Bom histórico de fechamento do vendedor*
- *Produto com bom desempenho histórico*
- *Deal envelhecendo acima do ideal*
- *Região com baixa conversão histórica*
- *Avançar para o próximo passo hoje*
- *Manter cadência e buscar próximo compromisso*
- *Decidir se vale recuperar ou encerrar esta semana*

Após a geração inicial das explicações, foi realizada uma **segunda rodada de refinamento** para identificar e corrigir contradições lógicas — como deals classificados como "Foco Agora" com razões predominantemente negativas, ou o inverso. O resultado foi a versão `explainable_lead_scoring_output_v2.csv`.

---

## 9. Interface do Produto

A interface foi construída no **Lovable** como um dashboard single-page com os seguintes elementos:

### Estrutura da tela principal

- **Header** com nome do produto e botão de logout
- **Filtros** por: vendedor, gestor, escritório regional, produto, estágio do deal e label de prioridade
- **KPIs dinâmicos** que respondem aos filtros:
  - Total de oportunidades abertas
  - Distribuição por prioridade (Foco Agora / Nutrir / Baixa Prioridade)
  - Score médio da carteira filtrada
- **Gráficos** de apoio à leitura executiva:
  - Distribuição por prioridade
  - Distribuição por estágio do funil
  - Visão por vendedor
  - Visão por gestor
- **Tabela interativa** com paginação, exibindo os deals ordenados por score
- **Painel de detalhe do deal** ao selecionar uma linha, contendo:
  - Score numérico em destaque
  - Badge de prioridade (Foco Agora / Nutrir / Baixa Prioridade)
  - Razões positivas e de risco
  - Ação recomendada

### Autenticação

- Página de login antes do acesso ao dashboard
- Botão de logout no header
- Controle de acesso básico integrado à aplicação

---

## 10. Segurança e Autenticação

A solução passou por uma etapa de **revisão de segurança** com foco nos pontos mais relevantes para um produto de dados comerciais:

- Adição de **página de login/autenticação** para acesso controlado ao dashboard
- Inclusão de **logout acessível no header** em todas as telas pós-login
- Revisão da possibilidade de **exposição não intencional de dados sensíveis** da base de vendas
- Avaliação de permissões e fluxo de acesso à aplicação

> **Nota:** A revisão de segurança realizada foi adequada ao escopo de um challenge. Não foram implementadas camadas de segurança de produção como gestão de sessões avançada, criptografia de base, auditoria de acesso ou controle de permissões por perfil. Esses pontos fazem parte dos próximos passos para uma versão produtiva.

O objetivo dessa etapa foi demonstrar que a solução não ficou restrita ao visual — houve preocupação com acesso controlado e uso mais realista do produto.

---

## 11. PWA

Foi adicionada uma camada leve de **Progressive Web App (PWA)** como melhoria de usabilidade:

- Arquivo de manifest configurado
- Ícones definidos para instalação
- Experiência de instalação no dispositivo habilitada
- Foco em responsividade e acessibilidade básica

**Fora do escopo desta versão:**

- Funcionalidade offline avançada
- Push notifications
- Sincronização em background
- Service worker complexo

O objetivo foi agregar usabilidade sem aumentar a complexidade da entrega.

---

## 12. Como Rodar

A aplicação foi construída no Lovable como um projeto web interativo. Para rodar localmente ou em outro ambiente:

**Pré-requisitos:**

- Node.js instalado (versão recomendada: LTS)
- Gerenciador de pacotes (`npm` ou `yarn`)

**Passos:**

```bash
# 1. Instalar dependências do projeto
npm install

# 2. Iniciar o ambiente de desenvolvimento
npm run dev

# 3. Acessar a aplicação no navegador
# Geralmente disponível em: http://localhost:5173 (ou porta configurada)
```

**Configuração de autenticação:**

- Verifique as configurações de autenticação no ambiente antes de acessar
- O acesso ao dashboard exige login válido

> Para implantação em ambiente produtivo, será necessário configurar variáveis de ambiente, serviço de autenticação e pipeline de deploy adequados ao destino escolhido.

---

## 13. Decisões de Produto e Escopo

As principais decisões tomadas ao longo do projeto, com justificativa:

| Decisão | Justificativa |
|---|---|
| Heurística explicável em vez de ML complexo | O critério do challenge é que o vendedor entenda o score. Um modelo opaco comprometeria esse requisito central. |
| Produto interativo em vez de notebook analítico | O challenge pede software funcionando, não análise estática. |
| Base final consolidada (`ranked_open_deals_final.csv`) | Simplifica a integração com o app e garante consistência dos dados exibidos. |
| Não bloqueio por `account` ausente | 1.425 registros sem account na origem não justificavam excluir essa parcela do pipeline. |
| Recalibração por percentis | A primeira distribuição produzia zero deals em "Foco Agora", tornando o produto inoperante. A recalibração resolveu isso sem alterar a fórmula. |
| Autenticação incluída | Dá mais realismo à solução e demonstra preocupação com acesso controlado. |
| Sem deploy público | Decisão intencional para evitar custo desnecessário em um contexto de challenge. |

---

## 14. Limitações

As limitações desta versão são explícitas e relevantes para avaliação:

- **Snapshot estático dos dados:** a base utilizada é um recorte fixo no tempo. Não há atualização automática.
- **Ausência de integração com CRM:** os dados precisam ser exportados manualmente para alimentar a ferramenta.
- **Registros sem account na origem:** 1.425 oportunidades não puderam ser enriquecidas com dados de conta.
- **Scoring heurístico:** o score é uma heurística baseada em taxas históricas e pesos fixos, não um modelo preditivo treinado e validado estatisticamente.
- **Sem deploy público:** a aplicação não está disponível em URL pública nesta versão.
- **Segurança em nível de challenge:** a revisão realizada não substitui as camadas de segurança necessárias para um ambiente produtivo.
- **Sem trilha de auditoria:** não há registro histórico de alterações no score ou nas recomendações.

---

## 15. Próximos Passos

Para evolução do produto em direção a um uso produtivo:

- **Integração com CRM** (Salesforce, HubSpot ou similar) para atualização automática dos dados de pipeline
- **Pipeline de dados automatizado** com atualização periódica do score e das classificações
- **Refinamento da lógica de score** com feedback do time comercial e análise de acurácia das recomendações
- **Trilha de auditoria** para registrar decisões tomadas com base no score
- **Deploy em ambiente web** com CI/CD, variáveis de ambiente e domínio configurado
- **Governança de acesso** com perfis de permissão (vendedor, gestor, admin)
- **Observabilidade** com logs, monitoramento de erros e rastreamento de uso
- **Evolução da camada PWA** com suporte a offline e notificações de deals prioritários
- **Modelo preditivo** como camada complementar após coleta de feedback e validação da heurística

---

## 16. Uso de IA no Processo

A IA foi usada de forma estruturada em todas as etapas do projeto, com papéis distintos para cada ferramenta:

### ChatGPT
- Estruturação da estratégia de solução
- Definição da lógica de scoring e dos pesos
- Criação e refinamento de prompts para Julius AI
- Documentação e README
- Decisões de produto e escopo

### Julius AI
- Inspeção do schema e identificação das chaves de join
- Execução dos joins entre as tabelas
- Identificação e resolução de inconsistências (ex: `GTXPro` vs. `GTX Pro`)
- Criação de variáveis derivadas
- Cálculo do `priority_score`
- Recalibração da classificação por percentis
- Geração dos campos de explicação (v1 e v2)
- Geração do ranking final de oportunidades abertas

### Lovable
- Construção da interface interativa do produto
- Implementação dos filtros, KPIs, gráficos e tabela
- Painel de detalhe do deal
- Autenticação e logout
- Configuração de PWA básico

O processo não foi linear. Envolveu iterações, validações intermediárias, recalibrações e refinamentos — com supervisão humana em cada etapa. O resultado é fruto de múltiplos ciclos de revisão, não de um único prompt.

---

## 17. Observação sobre Deploy

A aplicação possui uma URL pública para fins de avaliação:

**Demo online:**  
https://opportunity-focus-hub.lovable.app/auth

A publicação foi disponibilizada para facilitar o acesso ao produto durante a avaliação do challenge.

Caso necessário, o ambiente pode ser evoluído futuramente com domínio próprio, pipeline de deploy dedicado e configurações adicionais de produção.

---

## 18. Conclusão

O **DealPriority** entrega o que o challenge propõe: um software funcional que ajuda vendedores a priorizar oportunidades com base em um score explicável.

As escolhas feitas ao longo do projeto — heurística em vez de ML, produto interativo em vez de notebook, recalibração operacional, explicabilidade por deal, autenticação básica — refletem critério de produto, não simplificação. Cada decisão foi tomada com o objetivo de entregar algo utilizável, compreensível e demonstrável dentro do escopo do desafio.

As limitações estão documentadas com transparência. Os próximos passos mostram o caminho natural de evolução para um produto de produção.

## Como acessar

1. Abra a demo online
2. Faça login, se solicitado
3. Explore filtros, KPIs, gráficos e detalhes dos deals

---

*Challenge 003 — Lead Scorer | AI Master Selection Process*
