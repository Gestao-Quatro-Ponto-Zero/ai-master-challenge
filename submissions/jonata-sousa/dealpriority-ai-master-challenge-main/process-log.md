# process-log.md
### Challenge 003 — Lead Scorer | AI Master Selection Process

---

## 1. Objetivo do Documento

Este arquivo registra o processo de construção da solução entregue no Challenge 003 — Lead Scorer. O objetivo é documentar como o projeto foi pensado, quais decisões foram tomadas, como as ferramentas de IA foram usadas, onde houve ajustes e quais limitações foram aceitas conscientemente.

O documento não é uma narrativa de marketing. É um registro honesto do processo.

---

## 2. Contexto do Desafio

**Challenge:** 003 — Lead Scorer
**Área:** Vendas / RevOps
**Processo:** Seleção AI Master

O desafio exigia a construção de uma **solução funcional** — não apenas uma análise — para ajudar times de vendas a priorizar oportunidades. Os requisitos centrais eram:

- Uso dos dados reais fornecidos
- Lógica de scoring ou priorização
- Explicabilidade: o vendedor precisa entender por que um deal tem score alto ou baixo
- Software funcionando, não notebook analítico

---

## 3. Estratégia Escolhida

### Por que este challenge

Após avaliar os desafios disponíveis, o Challenge 003 foi escolhido porque:

- Tinha melhor aderência à proposta de entregar algo funcional e interativo dentro do prazo
- Permitia mostrar visão de negócio, produto e execução de forma integrada
- Favorecia uma solução utilizável por vendedores e gestores, sem exigir ML complexo
- Era possível construir uma interface prática com ferramentas acessíveis e de resultado rápido

### Direção estratégica

A solução foi posicionada deliberadamente como uma **ferramenta de priorização comercial explicável**, e não como um modelo preditivo sofisticado. Os motivos foram:

- O requisito de explicabilidade é central no challenge — um modelo opaco não atende isso
- Heurísticas bem construídas entregam valor operacional real sem sacrificar compreensão
- O foco em utilidade prática é mais relevante para o contexto de vendas do que performance preditiva
- O escopo era viável dentro do tempo disponível

A aposta foi: score explicável + contexto por deal + ação recomendada + interface interativa.

---

## 4. Ferramentas Utilizadas

O processo envolveu três ferramentas com papéis distintos. Nenhuma foi usada de forma passiva — cada uma exigiu iteração, validação e ajuste humano.

### ChatGPT

- Apoio na avaliação dos challenges e escolha do foco
- Definição da estratégia de solução e do MVP
- Estruturação da lógica de scoring (variáveis, pesos, penalidades)
- Criação e refinamento de prompts usados no Julius AI e no Lovable
- Apoio na documentação final (README e process-log)
- Revisão de narrativa e decisões de produto

### Julius AI

- Inspeção do schema dos arquivos CSV
- Identificação das chaves de join entre tabelas
- Execução dos merges entre `sales_pipeline`, `accounts`, `sales_teams` e `products`
- Validação da base resultante (contagem de linhas, ausência de duplicação, checagem de nulos)
- Criação das variáveis derivadas
- Cálculo do `priority_score`
- Recalibração da classificação com base em percentis
- Geração dos campos de explicação por deal
- Geração do ranking final de oportunidades abertas

### Lovable

- Construção da interface interativa do produto
- Implementação dos filtros, KPIs, gráficos e tabela
- Painel de detalhe do deal
- Refinamentos de UX/UI e coerência de navegação
- Ajuste de paginação e responsividade
- Adição de autenticação (login/logout)
- Configuração de PWA básico

> Em nenhuma das ferramentas o resultado foi aceito sem revisão. Cada etapa envolveu leitura dos outputs, identificação de problemas e decisão sobre o que ajustar.

---

## 5. Linha do Tempo do Projeto

### Etapa 1 — Entendimento do desafio e definição do caminho

Leitura do material do challenge e avaliação das opções disponíveis. A análise levou à escolha do Challenge 003, com foco em construir um produto funcional voltado a priorização comercial.

A decisão central desta etapa foi privilegiar **utilidade operacional sobre sofisticação algorítmica**.

---

### Etapa 2 — Decisão de stack e abordagem

Definição das ferramentas com base em critérios práticos: velocidade de entrega, capacidade de resultado demonstrável e complementaridade entre elas.

A preocupação foi evitar complexidade desnecessária. O critério foi: o que entrega mais valor no menor tempo, com qualidade suficiente para o contexto do challenge?

Escolhas:
- **Julius AI** para a parte analítica e tratamento de dados
- **Lovable** para a interface do produto
- **ChatGPT** para coordenação, lógica de score e documentação

---

### Etapa 3 — Organização do plano de execução

Antes de iniciar o trabalho nos dados, foi estruturado um plano sequencial para manter o foco:

```
schema → join → validação → variáveis derivadas → score → ranking → export → app → documentação
```

Esse plano serviu como guia ao longo do processo e evitou dispersão.

---

### Etapa 4 — Exploração inicial dos dados no Julius AI

Os quatro arquivos CSV do challenge foram carregados e inspecionados:

- `sales_pipeline.csv`
- `accounts.csv`
- `products.csv`
- `sales_teams.csv`

Resultados da exploração:

- `sales_pipeline` identificado como tabela central
- Chaves de ligação mapeadas: `account`, `product`, `sales_agent`
- Unicidade de `opportunity_id` confirmada
- Identificada inconsistência: `GTXPro` no pipeline vs. `GTX Pro` na tabela de produtos
- Detectados 1.425 registros com `account` ausente em `sales_pipeline`
- Confirmado que `close_date` e `close_value` nulos eram compatíveis com deals em aberto — não eram erros, mas ausências esperadas

---

### Etapa 5 — Join e validação da base

O merge foi executado com `sales_pipeline` como base, fazendo joins com as demais tabelas pelas chaves identificadas.

**Problema encontrado:** A inconsistência `GTXPro` vs. `GTX Pro` causaria falha silenciosa no join com `products`. Foi criada uma regra de padronização antes do merge para normalizar os valores.

**Validações realizadas:**
- Confirmação de que `opportunity_id` não duplicou após os joins
- Manutenção do total de 8.800 linhas da base original
- Checagem de linhas sem correspondência em cada join

**Problema remanescente:** Os 1.425 registros com `account` nulo já existiam antes do merge — não era erro de join, era dado faltante na origem. A decisão foi **não bloquear a análise por isso**, pois excluir esses registros reduziria o pipeline analisado sem necessidade, já que `account` não é variável central no scoring.

**Arquivo gerado:** `merged_sales_pipeline.csv`

---

### Etapa 6 — Criação das variáveis derivadas

A base foi enriquecida com variáveis voltadas a tornar o score explicável e operacionalmente útil:

| Variável | Propósito |
|---|---|
| `deal_status_group` | Separar abertos, ganhos e perdidos |
| `deal_age_days` | Medir tempo desde abertura do deal |
| `days_to_close` | Calcular tempo histórico médio até fechamento |
| `seller_win_rate` | Taxa histórica de fechamento do vendedor |
| `product_win_rate` | Taxa histórica de fechamento por produto |
| `regional_win_rate` | Desempenho histórico da região |
| `manager_win_rate` | Desempenho histórico do gestor |
| `close_value_band` | Faixa de valor estimado do deal |
| `aging_risk_flag` | Flag para deals envelhecendo acima do padrão |
| `stage_weight` | Peso baseado no avanço no funil |
| `priority_label_suggestion` | Classificação preliminar antes da recalibração |

Essas variáveis foram pensadas para refletir quatro dimensões: avanço no funil, desempenho histórico, risco de envelhecimento e contexto operacional.

**Arquivo gerado:** `enriched_sales_pipeline.csv`

---

### Etapa 7 — Construção do score

O score foi construído como **heurística explicável**, com pesos definidos a partir do raciocínio de negócio:

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

O maior peso foi dado ao `stage_weight` porque o avanço no funil é o sinal mais objetivo de maturidade de um deal. Os demais fatores refletem contexto histórico, do mais granular (vendedor) ao mais agregado (região e gestor).

O score foi limitado ao intervalo **0 a 100**.

**Arquivo gerado:** `lead_scoring_output.csv`

---

### Etapa 8 — Recalibração da classificação

Após calcular o score, a primeira tentativa de classificação produziu um resultado operacionalmente inútil: **nenhum deal caía em "Foco Agora"**. A distribuição estava comprimida em faixas intermediárias, o que impedia qualquer priorização real.

**Decisão:** manter a fórmula do score, mas recalibrar a **classificação final** com base nos percentis das oportunidades abertas.

Percentis calculados sobre `priority_score`:

| Percentil | Valor |
|---|---|
| p50 | 36,4294 |
| p85 | 39,1613 |

**Regra de classificação:**

| Condição | Label |
|---|---|
| `priority_score >= p85` | Foco Agora |
| `p50 <= priority_score < p85` | Nutrir |
| `priority_score < p50` | Baixa Prioridade |

**Distribuição resultante:**

| Label | Quantidade | % |
|---|---|---|
| Foco Agora | 316 | 15,1% |
| Nutrir | 734 | 35,1% |
| Baixa Prioridade | 1.039 | 49,7% |

Essa mudança foi essencial. Sem ela, o dashboard teria um score calculado, mas nenhuma utilidade operacional para o vendedor.

**Arquivo gerado:** `lead_scoring_output_recalibrated.csv`

---

### Etapa 9 — Criação de explicações e ação recomendada

O projeto não poderia ficar apenas no número. Para cada oportunidade aberta, foram gerados campos em linguagem de negócio:

- `top_positive_reason_1` e `top_positive_reason_2`: fatores que elevam o score
- `top_risk_reason_1` e `top_risk_reason_2`: fatores de alerta ou risco
- `recommended_action`: sugestão prática de próximo passo

Após a geração inicial, foi feita uma **segunda rodada de revisão** para eliminar contradições lógicas — como deals classificados como "Foco Agora" com razões predominantemente negativas, ou o inverso. Essa revisão resultou em uma segunda versão dos campos de explicação.

**Arquivos gerados:** `explainable_lead_scoring_output.csv` → `explainable_lead_scoring_output_v2.csv`

---

### Etapa 10 — Geração da base final

A base final para o app foi gerada contendo apenas as oportunidades com status aberto, com todas as variáveis necessárias para a interface:

- Ordenação por `priority_score` decrescente
- Classificação final (`priority_label`)
- Campos de explicação positiva e de risco
- Ação recomendada
- Colunas de contexto do deal

**Total de oportunidades abertas:** 2.089
**Arquivo gerado:** `ranked_open_deals_final.csv`

---

### Etapa 11 — Construção da interface no Lovable

Com a base final pronta, a construção da interface foi iniciada no Lovable. O foco foi em simplicidade, uso real e boa demonstração.

Elementos implementados na primeira versão:

- Header com nome do produto
- Filtros por vendedor, gestor, região, produto, estágio e prioridade
- KPIs: total de deals, distribuição por prioridade, score médio
- Gráficos: distribuição por prioridade, por estágio, por vendedor, por gestor
- Tabela interativa com paginação
- Painel de detalhe ao selecionar um deal
- Score numérico em destaque
- Badge de prioridade
- Razões positivas e de risco
- Ação recomendada

---

### Etapa 12 — Ajustes de coerência da interface

Durante a revisão da interface, foram identificados problemas de coerência que exigiram correção:

- KPIs não respondiam corretamente aos filtros aplicados
- A ordem dos componentes na tela não favorecia a leitura
- Paginação ausente na tabela (necessária dado o volume de deals)
- Inconsistências entre os valores exibidos na tabela, nos gráficos e nos cards
- Gráficos precisavam de ajuste para refletir a carteira filtrada

Cada um desses pontos foi corrigido iterativamente. A interface só foi considerada adequada após os componentes estarem coerentes entre si.

---

### Etapa 13 — Segurança e autenticação

Antes de fechar a solução, foi realizada uma revisão de segurança da aplicação com foco nos riscos mais relevantes para um produto de dados comerciais:

- Avaliação de possível exposição não intencional de dados sensíveis do pipeline
- Revisão de permissões e fluxo de acesso
- Identificação de eventuais segredos expostos no frontend

Como resultado, foram adicionados:

- Página de login/autenticação antes do acesso ao dashboard
- Botão de logout no header, acessível em todas as telas pós-login

> **Nota de honestidade:** A revisão realizada foi adequada ao escopo do challenge. Não foi implementada segurança de produção — sem gestão de sessões avançada, criptografia de base ou trilha de auditoria. Esses pontos são evolução natural para uma versão produtiva.

O objetivo foi tornar a solução mais realista em termos de acesso controlado, e não apenas entregar uma interface aberta.

---

### Etapa 14 — PWA leve

Foi adicionada uma camada básica de Progressive Web App com foco em:

- Arquivo de manifest configurado
- Ícones para instalação no dispositivo
- Experiência de instalação habilitada
- Responsividade básica

**Fora do escopo:** offline avançado, push notifications e sincronização em background. A decisão foi manter o escopo propositalmente leve para não adicionar complexidade sem retorno claro dentro do prazo do challenge.

---

### Etapa 15 — Decisão de não publicar URL

Ao final do processo, foi tomada a decisão deliberada de **não criar uma URL pública** para a aplicação.

Motivação: manter uma aplicação publicada em produção gera custo recorrente sem retorno direto para o contexto de avaliação. O foco foi concentrar energia na qualidade do produto, da lógica e da documentação.

A arquitetura da solução permite deploy futuro sem mudanças estruturais.

---

## 6. Decisões Importantes

| Decisão | Justificativa |
|---|---|
| Heurística explicável em vez de ML complexo | ML opaco não atende o requisito de explicabilidade do challenge |
| Software funcional em vez de notebook analítico | O challenge pede solução utilizável, não análise estática |
| Base final consolidada para o app | Simplifica a integração e garante consistência dos dados exibidos |
| Não bloquear análise por account ausente | 1.425 registros sem account não justificavam reduzir o pipeline analisado |
| Recalibração da classificação por percentis | A primeira versão produzia zero deals em "Foco Agora" — sem isso, o app era inoperante |
| Segunda rodada de revisão das explicações | Contradições lógicas nas explicações comprometem a credibilidade do produto |
| Inclusão de autenticação | Torna a solução mais realista e demonstra preocupação com acesso controlado |
| PWA leve | Melhoria de usabilidade sem aumento relevante de complexidade |
| Sem deploy público | Decisão de escopo para evitar custo desnecessário em contexto de challenge |

---

## 7. Ajustes e Aprendizados

### Recalibração da classificação

O problema com a primeira versão da classificação só ficou visível depois que o score foi calculado e a distribuição analisada. A solução foi simples — percentis — mas exigiu reconhecer que a fórmula estava correta, mas o corte de classificação estava errado para uso operacional.

### Revisão das explicações contraditórias

A primeira versão das explicações gerava, em alguns casos, resultados logicamente inconsistentes: deals com score baixo recebendo razões predominantemente positivas, ou o inverso. Isso comprometia a credibilidade do produto para o vendedor. A segunda rodada de revisão corrigiu os casos identificados.

### Foco no valor operacional, não na sofisticação técnica

A percepção ao longo do processo foi que o valor do projeto estava mais na **utilidade operacional** do que na complexidade algorítmica. Um score de 47 pontos que o vendedor entende vale mais do que um modelo com AUC 0.82 que ele não consegue interpretar.

### Controle de escopo

A principal disciplina ao longo do processo foi **não dispersar**. Há muitas melhorias possíveis — modelo preditivo, integração com CRM, automações — mas nenhuma delas cabia no escopo do challenge. A escolha foi entregar algo completo e coerente dentro do que era viável.

---

## 8. Evidências de Uso de IA

O processo não foi um único prompt. Foi uma sequência de iterações com validação humana em cada etapa.

**Exemplos concretos:**

- **ChatGPT foi usado para estruturar o plano do projeto antes de tocar nos dados.** O resultado foi um plano sequencial que guiou o trabalho de ponta a ponta e evitou retrabalho.

- **ChatGPT definiu a lógica de scoring com pesos e justificativas de negócio.** O output foi revisado, ajustado e então usado como instrução para o Julius AI.

- **Julius AI confirmou as chaves de join, executou os merges e devolveu a base validada.** O resultado foi inspecionado manualmente antes de seguir para a próxima etapa.

- **A inconsistência GTXPro vs. GTX Pro foi identificada no Julius AI e corrigida com regra explícita.** Sem isso, o join com a tabela de produtos teria falhado silenciosamente.

- **A recalibração surgiu da análise do output do score.** O Julius AI calculou o score; a decisão de recalibrar foi humana, com base na distribuição resultante.

- **As explicações contraditórias foram identificadas por revisão humana dos campos gerados.** A segunda rodada de refinamento foi uma instrução específica de correção, não uma regeneração automática.

- **O Lovable foi usado iterativamente.** A interface não foi gerada de uma vez — houve múltiplas rodadas de ajuste de coerência, filtros, gráficos e comportamento dos KPIs.

- **A revisão de segurança foi uma etapa separada e consciente.** Não foi adicionada como afterthought — foi uma decisão de produto para dar mais realismo à solução.

Em todas as etapas, a IA funcionou como **acelerador de execução**, não como substituta do julgamento. As decisões de escopo, os critérios de qualidade e os ajustes de direção foram humanos.

---

## 9. Limitações Aceitas

As seguintes limitações foram identificadas e aceitas conscientemente durante o processo:

- **Base estática:** os dados são um snapshot. Não há atualização automática nem integração com sistema de origem.
- **Ausência de integração com CRM:** alimentação da ferramenta exige exportação manual dos dados de pipeline.
- **Registros sem account na origem:** 1.425 oportunidades não foram enriquecidas com dados de conta por ausência na fonte.
- **Score heurístico:** os pesos foram definidos por raciocínio de negócio, não por treinamento estatístico. Não há validação preditiva formal.
- **Sem deploy público:** a aplicação não está acessível em URL pública nesta versão.
- **Segurança em nível de challenge:** a revisão realizada foi adequada ao escopo, mas não substitui as camadas necessárias para produção.
- **PWA propositalmente limitado:** sem funcionalidade offline avançada, push notifications ou sincronização em background.

---

## 10. Conclusão

O processo foi orientado por quatro princípios centrais:

**Clareza de escopo.** O challenge pedia uma solução funcional com scoring explicável. Todas as decisões foram avaliadas à luz desse critério.

**Foco em valor real.** A pergunta que guiou o projeto foi: isso ajuda um vendedor a tomar uma decisão melhor amanhã cedo? Se a resposta fosse não, a feature não entrava.

**Uso estratégico de IA.** As ferramentas foram usadas para acelerar execução, não para substituir raciocínio. Cada output foi revisado, questionado e, quando necessário, corrigido.

**Iteração com validação.** Nenhuma etapa foi tratada como definitiva sem revisão do resultado. A recalibração do score, a correção das explicações e os ajustes de coerência da interface são evidências disso.

O resultado é um produto funcional, demonstrável e coerente com o que o challenge propõe — construído com critério de produto, honestidade sobre limitações e uso estratégico das ferramentas disponíveis.

---

*Challenge 003 — Lead Scorer | AI Master Selection Process*
