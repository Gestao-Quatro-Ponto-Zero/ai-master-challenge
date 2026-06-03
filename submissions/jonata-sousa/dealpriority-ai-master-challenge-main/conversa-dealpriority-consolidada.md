# Conversa Consolidada — Projeto DealPriority (Challenge 003 — Lead Scorer)

> Registro consolidado da conversa, decisões, prompts, estrutura do projeto e evolução da solução desde o início da construção do challenge.

## 1. Ponto de partida

O objetivo inicial foi escolher, entre os challenges disponíveis do processo seletivo de **AI Master**, qual entregaria a melhor combinação entre:

- viabilidade dentro do prazo do mesmo dia
- produto funcional
- interatividade
- utilidade prática
- facilidade de demonstração

Após análise do material do repositório do challenge, a decisão foi seguir com o **Challenge 003 — Lead Scorer**, por ser o que mais favorecia a construção de uma solução funcional, interativa e explicável. Essa direção também estava alinhada ao requisito explícito do challenge de entregar **software funcionando**, e não apenas análise.  
Referências do challenge e do repositório: fileciteturn0file5L1-L39 fileciteturn0file6L1-L16 fileciteturn0file7L1-L58

---

## 2. Escolha estratégica do challenge

### Decisão tomada
Foi recomendado seguir com o **Challenge 003 — Lead Scorer**.

### Justificativas discutidas
- Ele pedia uma **solução funcional** que rodasse de verdade.
- Favorecia uma entrega com **interface interativa**, filtros e explicabilidade.
- Permitia explorar mais visão de **negócio + produto + dados**, sem depender de ML complexo.
- Era o melhor encaixe para um fluxo de trabalho baseado em **vibe coding**, com foco em resultado rápido.

### Direção de solução escolhida
Em vez de tentar treinar um modelo sofisticado, a solução foi posicionada como um:

- **dashboard interativo**
- com **scoring heurístico explicável**
- voltado para **vendedores e gestores**
- com **priorização prática** e **recomendação por deal**

---

## 3. Definição da estratégia geral

A estratégia geral foi estruturada assim:

### Produto
Criar uma ferramenta chamada **DealPriority**, com o subtítulo:

**Inteligência de priorização para operações comerciais**

### Objetivo do produto
Ajudar vendedores e gestores a identificar quais oportunidades abertas merecem atenção primeiro, usando um **priority_score**, uma **classificação operacional** e explicações curtas em linguagem de negócio.

### Escopo definido
Foi decidido manter um **MVP funcional e convincente**, em vez de tentar um projeto superdimensionado. O MVP deveria incluir:

- filtros
- KPIs
- gráficos
- tabela interativa
- score
- classificações
- detalhe do deal
- explicações do score
- ação recomendada

---

## 4. Escolha de ferramentas

Como o objetivo era velocidade com qualidade e o perfil de execução era mais próximo de **vibe coding**, foi definida a seguinte divisão:

### ChatGPT
Usado para:
- definir a estratégia do projeto
- escolher o challenge
- desenhar a lógica do score
- escrever prompts
- estruturar README, process-log e PR

### Julius AI
Usado para:
- inspeção do schema
- joins entre tabelas
- validação de merge
- criação de variáveis derivadas
- cálculo do score
- recalibração da classificação
- geração de explicações
- geração do ranking final

### Lovable
Usado para:
- construir a interface do produto
- implementar filtros, KPIs, gráficos e tabela
- adicionar paginação
- criar painel de detalhe
- autenticação
- camada PWA básica

---

## 5. Organização visual do passo a passo

Foi sugerido o uso do **Whimsical** como ferramenta para organizar visualmente o fluxo do projeto.

### Estrutura proposta para o mapa/fluxo
**ChatGPT**
- estratégia
- MVP
- lógica de score
- prompts
- README
- process-log

**Julius AI**
- schema
- join
- validação
- variáveis derivadas
- score
- ranking
- export

**Lovable**
- estrutura do app
- dashboard
- filtros
- tabela
- gráficos
- paginação
- detalhe do deal

**Entrega final**
- app funcionando
- documentação
- evidências
- submissão

Também foi gerado um prompt para o Whimsical criar um fluxograma do projeto com a trilha:

**Planejamento → Dados → Scoring → Interface → Documentação → Entrega**

---

## 6. Definição sobre atualização dos dados

Foi discutido como os dados seriam atualizados “a cada dia”.

### Decisão tomada
Para o challenge, a escolha foi usar um **snapshot estático** dos CSVs do dataset.

### Justificativa
O challenge exige uso dos dados reais e solução funcional, mas não exige integração viva com CRM. Portanto, a abordagem mais madura e defensável foi:

- usar os CSVs como snapshot
- exibir “última atualização”
- documentar que, em produção, o próximo passo seria integração com CRM ou upload recorrente

---

## 7. Início da etapa no Julius AI

Foi estruturado um fluxo específico para o Julius AI:

1. schema
2. join
3. validação
4. variáveis derivadas
5. score
6. explicações
7. ranking
8. resumo executivo

### Prompts estruturados
Foram preparados prompts em português para cada uma dessas etapas, incluindo:

- inspeção dos 4 CSVs
- identificação das chaves de join
- merge usando `sales_pipeline` como tabela central
- validação de duplicidade e nulos
- criação de variáveis derivadas
- score explicável
- ranking final das oportunidades abertas

---

## 8. Resultado da exploração do schema no Julius AI

Os 4 arquivos do challenge foram carregados:

- `sales_pipeline.csv`
- `accounts.csv`
- `products.csv`
- `sales_teams.csv`

### O que foi identificado
- `sales_pipeline` como tabela central
- `opportunity_id` único
- `account` único em `accounts`
- `product` único em `products`
- `sales_agent` único em `sales_teams`

### Problema importante encontrado
Havia inconsistência em `product`:
- `GTXPro` em `sales_pipeline`
- `GTX Pro` em `products`

Isso exigiu padronização antes do join com `products`.

### Outro ponto relevante
Foram encontrados **1.425 registros com `account` ausente** já na origem do `sales_pipeline`.

---

## 9. Join e validação da base

### Join executado
Foi feito o merge com `sales_pipeline` como base, aplicando:

- left join com `accounts`
- left join com `sales_teams`
- left join com `products`
- padronização de `GTXPro` → `GTX Pro`

### Validações confirmadas
- `opportunity_id` não duplicou
- total de linhas permaneceu em **8.800**
- o join com `products` foi corrigido com sucesso
- `sales_agent`, `manager` e `regional_office` ficaram completos

### Descoberta importante
Os 1.425 registros sem `account` não eram erro de join. Eles já estavam nulos na origem.

### Decisão tomada
**Não bloquear a análise por ausência de `account`.**

---

## 10. Variáveis derivadas criadas

Depois da base consolidada, foram criadas variáveis derivadas para suportar um score explicável.

### Variáveis criadas
- `deal_status_group`
- `deal_age_days`
- `days_to_close`
- `seller_win_rate`
- `product_win_rate`
- `regional_win_rate`
- `manager_win_rate`
- `close_value_band`
- `aging_risk_flag`
- `stage_weight`
- `priority_label_suggestion`

### Lógica de negócio
Essas variáveis foram pensadas para representar:

- avanço no funil
- desempenho histórico do vendedor
- desempenho histórico do produto
- contexto de região e gestão
- risco de envelhecimento do deal
- valor e contexto operacional

---

## 11. Construção da lógica de scoring

O Julius AI gerou uma primeira versão do `priority_score`.

### Fórmula definida
```text
priority_score = 100 × (
  0.45 × stage_weight +
  0.20 × seller_win_rate +
  0.15 × product_win_rate +
  0.10 × regional_win_rate +
  0.10 × manager_win_rate
) − 10 se aging_risk_flag = true
```

### Características do score
- calculado apenas para oportunidades abertas
- limitado ao intervalo 0–100
- heurístico e explicável
- baseado em lógica de negócio, não em ML treinado

---

## 12. Problema na primeira classificação

Quando o score foi calculado, surgiu um problema importante:

### Distribuição inicial ruim
- **0** deals em `Foco Agora`
- **151** em `Nutrir`
- **1.938** em `Baixa Prioridade`

Isso tornava a solução fraca operacionalmente, porque o dashboard não ajudaria na priorização real.

---

## 13. Recalibração da classificação

### Decisão
Manter a fórmula do score, mas recalibrar **a classificação final** com base em percentis das oportunidades abertas.

### Percentis usados
- `p50 = 36,4294`
- `p85 = 39,1613`

### Regra final
- `Foco Agora` se `priority_score >= p85`
- `Nutrir` se `p50 <= priority_score < p85`
- `Baixa Prioridade` se `priority_score < p50`

### Resultado final
- **Foco Agora:** 316 (15,1%)
- **Nutrir:** 734 (35,1%)
- **Baixa Prioridade:** 1.039 (49,7%)

Essa recalibração foi considerada crucial para tornar o produto realmente utilizável.

---

## 14. Criação de explicações do score

Para cada oportunidade aberta, foram gerados os seguintes campos:

- `top_positive_reason_1`
- `top_positive_reason_2`
- `top_risk_reason_1`
- `top_risk_reason_2`
- `recommended_action`

### Exemplos de linguagem usada
- estágio avançado no funil
- bom histórico do vendedor
- produto com bom desempenho histórico
- deal envelhecendo acima do ideal
- região com baixa conversão histórica
- avanço para o próximo passo hoje
- manter cadência e buscar próximo compromisso
- decidir se vale a pena recuperar ou encerrar nesta semana

### Problema encontrado
A primeira versão gerava explicações contraditórias em alguns casos, por exemplo:
- positivo: “está avançado no funil”
- risco: “inicial no funil”

### Correção
Foi feita uma segunda rodada de refinamento para impedir contradições lógicas entre motivos positivos e riscos.

---

## 15. Geração da base final

A base final usada no aplicativo foi:

- `ranked_open_deals_final.csv`

### Características
- contém apenas oportunidades abertas
- ordenada por `priority_score` em ordem decrescente
- total de **2.089** oportunidades abertas
- inclui score, classificação, explicações e ação recomendada

Trecho da evidência dessa geração no Julius AI: fileciteturn0file2L1-L17 fileciteturn0file2L87-L90

---

## 16. Entrada no Lovable

Com a base final pronta, foi decidido subir apenas:

- `ranked_open_deals_final.csv`

### Motivo
Ela já era a **base de produto**, contendo tudo o que a interface precisava. Os outros arquivos (`lead_scoring_output_recalibrated.csv` e `explainable_lead_scoring_output_v2.csv`) foram mantidos apenas como apoio.

### Prompt mestre usado no Lovable
A aplicação deveria ter:

- dashboard executivo
- KPIs
- tabela interativa
- filtros por vendedor, gestor, região, produto, estágio e prioridade
- ordenação por score
- detalhe do deal em painel lateral/modal
- score com destaque visual
- badges de prioridade
- textos em português do Brasil

---

## 17. Evolução da interface no Lovable

### Estrutura da tela
A aplicação começou com:

- header
- KPIs
- tabela
- painel de detalhe

Depois evoluiu para:

- header
- filtros
- KPIs
- gráficos
- tabela com paginação
- detalhe do deal

### Ajustes realizados
Durante os testes, foram identificados alguns problemas:

#### 1. KPIs não respondiam aos filtros
No `Index.tsx`, os cards usavam `allDeals` em vez de `deals`/`filteredDeals`.

**Correção feita:**
`<KPICards deals={allDeals} />` → `<KPICards deals={filteredDeals} />`

#### 2. Header precisava mostrar total filtrado + total geral
Foi ajustado para exibir:
- quantidade visível
- quantidade total de oportunidades

#### 3. Gráficos
Foi adicionada uma seção de gráficos entre os filtros e a tabela.

#### 4. Paginação
Foi adicionada paginação na tabela principal.

#### 5. Ordem dos componentes
A estrutura foi refinada para favorecer a navegação:
- filtros primeiro
- KPIs e gráficos depois
- tabela por último

---

## 18. Código de referência do `Index.tsx`

Durante a evolução do app, foi compartilhado e ajustado o arquivo `Index.tsx` com:

- `useDeals()`
- `useAuth()`
- `KPICards`
- `ChartsSection`
- `FiltersBar`
- `DealsTable`
- `DealDetail`
- botão de logout no header
- total filtrado vs total geral

Esse trecho marcou a consolidação da tela principal da aplicação.

---

## 19. Página de login e autenticação

Foi registrada como evidência a inclusão de:

- página de login
- autenticação
- `signOut`
- botão “Sair” no header

### Objetivo
Dar mais realismo à solução, reforçando preocupação com:
- acesso controlado
- uso mais próximo do mundo real
- segurança mínima da aplicação

---

## 20. Validação de segurança

Antes da conclusão da solução, foi estruturado um prompt de auditoria de segurança para revisar:

- riscos de injeção
- segredos expostos no frontend
- dados sensíveis em páginas de configuração
- políticas de RLS
- alteração indevida de permissões
- outras vulnerabilidades como XSS, IDOR, logs, validação, etc.

### Resultado registrado
Foi deixado como evidência que:
- houve revisão de segurança
- foi adicionada autenticação
- houve preocupação com acesso e exposição de dados

---

## 21. Camada PWA

Depois do app funcional, foi adicionada uma camada leve de PWA.

### Escopo do PWA
- responsividade
- manifest
- ícones
- experiência de instalação
- compatibilidade com Android/iOS em nível básico

### Fora do escopo
- offline avançado
- push notification
- sincronização complexa

### Decisão de escopo
Fazer um **PWA leve e demonstrável**, sem deixar isso competir com o objetivo principal do challenge.

---

## 22. Decisão de não publicar URL pública

Foi decidido **não criar uma URL pública** para a aplicação.

### Justificativa
- evitar custo desnecessário
- o contexto era de challenge/teste
- o foco foi priorizar:
  - produto funcional
  - score
  - experiência
  - autenticação
  - segurança
  - documentação

Esse ponto foi registrado explicitamente para entrar como evidência no README e no process-log.

---

## 23. Documentação construída

Ao final do processo, foram produzidos:

- `README.md`
- `process-log.md`
- descrição do Pull Request
- evidências do Julius AI em PDF
- fluxo visual do projeto em PDF
- sugestão de estrutura da submissão no Git

### README
O README final cobre:
- visão geral
- problema de negócio
- solução proposta
- funcionalidades
- arquitetura
- base de dados
- lógica de scoring
- recalibração
- explicabilidade
- interface
- segurança e autenticação
- PWA
- como rodar
- decisões de produto
- limitações
- próximos passos
- uso de IA
- observação sobre deploy

Arquivo disponível na conversa: fileciteturn0file1L1-L18

### Process log
O process-log registra:
- contexto
- estratégia
- ferramentas
- linha do tempo
- decisões
- aprendizados
- evidências de uso de IA
- limitações

Arquivo disponível na conversa: fileciteturn0file0L1-L16

---

## 24. Pull Request e submissão

Foi construída também a descrição do Pull Request, cobrindo:

- resumo da entrega
- o que foi entregue
- arquitetura
- lógica de scoring
- explicabilidade
- interface
- segurança
- PWA
- como avaliar
- como rodar
- limitações
- uso de IA
- observação sobre deploy

Além disso, foi revisado o que o challenge exigia, reforçando que a submissão precisa conter:

- solução funcional
- documentação mínima
- process log
- evidência de uso de IA
- submissão via PR

Referência do repositório com essas exigências: fileciteturn0file5L15-L39 fileciteturn0file7L39-L58

---

## 25. Estrutura de pasta recomendada

Foi sugerida uma estrutura de submissão com:

```text
submissions/seu-nome/
├── README.md
├── process-log.md
├── pr-description.md
├── evidencias/
│   ├── fluxo-projeto-miro.pdf
│   └── evidencias-julius-ai.pdf
├── screenshots/
│   ├── login.png
│   ├── dashboard.png
│   ├── filtros.png
│   └── deal-detail.png
├── app/
│   └── código da aplicação
├── package.json
├── package-lock.json
└── .env.example
```

Também foi lembrado que o repositório ignora `submissions/` no `.gitignore` do challenge original, o que reforça a necessidade de subir a solução dentro do fork corretamente configurado. fileciteturn0file3L1-L11

---

## 26. Nome do repositório e descrição sugeridos

### Nome sugerido
- `dealpriority-ai-master-challenge`

### Descrição sugerida
- `Solução funcional para o Challenge 003 — Lead Scorer, com scoring explicável, dashboard interativo e foco em utilidade operacional.`

---

## 27. Evidências separadas para o Git

Foi discutido o melhor formato para exportar e subir as evidências do Julius AI.

### Decisão recomendada
- **PDF** como evidência principal
- **Jupyter Notebook** opcional como material complementar
- **DOCX** não recomendado como principal

### Itens separados pelo usuário
- fluxo do projeto em PDF
- descrição do PR
- process-log
- README
- evidências do Julius AI em PDF

---

## 28. Arquivos-chave consolidados

### Challenge e contexto
- README do repositório principal: fileciteturn0file5L1-L39
- índice de desafios: fileciteturn0file6L1-L16
- Challenge 003 — Lead Scorer: fileciteturn0file7L1-L58

### Documentos produzidos
- process-log: fileciteturn0file0L1-L16
- README do projeto: fileciteturn0file1L1-L18

### Evidência da base final
- ranking final de oportunidades abertas: fileciteturn0file2L1-L17

---

## 29. Síntese final da conversa

Ao longo da conversa, o projeto evoluiu por estas camadas:

1. **Escolha estratégica do challenge**
2. **Definição do produto**
3. **Estruturação do passo a passo**
4. **Tratamento e enriquecimento dos dados no Julius AI**
5. **Construção do scoring**
6. **Recalibração da classificação**
7. **Criação de explicações e ação recomendada**
8. **Geração da base final**
9. **Construção da interface no Lovable**
10. **Correções de coerência do app**
11. **Autenticação e segurança**
12. **PWA leve**
13. **Documentação completa**
14. **Preparação da submissão via Pull Request**

O resultado consolidado foi o **DealPriority**, uma solução funcional para o Challenge 003, com scoring explicável, dashboard interativo e foco em utilidade operacional.

---

## 30. Observação

Este arquivo consolida o conteúdo principal da conversa em formato de registro estruturado. Ele não inclui mensagens de sistema, conteúdos internos de ferramentas ou raciocínio privado, mas preserva as decisões, prompts, resultados, correções e entregáveis relevantes para documentação do projeto.
