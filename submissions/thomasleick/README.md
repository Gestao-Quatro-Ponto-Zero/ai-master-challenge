# Submissão — thomasleick — Challenge 001

## Sobre mim

- **Nome:** Thomas Leick
- **LinkedIn:** não informado
- **Challenge escolhido:** G4 AI Master Challenge 001 — Diagnóstico de Churn

## Executive Summary

O diagnóstico encontra um quadro misto: eventos registrados e perdas de cobertura de plano aumentam, enquanto a intensidade de episódios de perda completa da conta cai. De 2023 para 2024, as linhas de evento passam de 73 para 527; normalizadas por exposição, de 8,64 para 13,48 por 100 contas-mês. No proxy conta × plano, perdas passam de 6 para 56 e de 0,427 para 0,595 por 100 relações-mês; episódios de perda completa passam de 2 para 6, mas caem de 0,237 para 0,153 por 100 contas-mês. Isso não comprova aumento do churn comercial de clientes nem causa raiz. As razões declaradas mais frequentes são funcionalidades (114/600), suporte (104/600) e orçamento (104/600); são hipóteses a validar, não causas demonstradas. Enterprise tem 5/120 relações da coorte inicial de 2024 com perda de cobertura (4,17%), contra 2/132 Basic (1,52%) e 0/122 Pro, com amostras pequenas e intervalos sobrepostos. A recomendação é reconciliar os 60 históricos de perda, começar pelos oito episódios de perda completa e retorno, instrumentar o ciclo de vida e testar outreach controlado antes de escalar. Um cenário ilustrativo de 60 contas elegíveis varia de -$1.056 a +$16.080 líquidos modelados; não é receita observada nem efeito causal.

No Capítulo 02, a visualização principal agora é a série mensal completa de janeiro de 2023 a dezembro de 2024: taxas de perda bruta e persistente para relações conta–plano e contas, movimentos absolutos e uma tabela com 24 meses. O seletor de outras granularidades é secundário; janeiro de 2023 mostra taxas `UNDEFINED` porque a base inicial é zero.

## Solução

**Paper executivo revisado (entrega principal):** [RavenStack — Beyond the Churn Headline](docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf). Fonte editável, método de reprodução, manifestos numéricos e QA: [docs/paper/](docs/paper/README.md). A versão anterior permanece preservada em `docs/paper/archive/2026-10-22-pre-rewrite/`. O paper é independente e não implica afiliação ou endosso do G4; a aplicação complementa a leitura com exploração mensal e cenários.

A solução é uma aplicação local, com API FastAPI e frontend React, apresentada em quatro capítulos executivos: **The Paradox**, **Follow the Evidence**, **The Cost of Inaction** e **The Decision Room**. O código agrega cada tabela no seu grão antes de comparar fontes. Métricas não reconstruíveis aparecem como UNKNOWN; o simulador só calcula cenários com hipóteses explícitas do usuário.

### Abordagem

1. Inspecionar o desafio, a procedência e a estrutura dos cinco CSVs.
2. Validar cardinalidades, duplicatas, datas e definições de churn antes de produzir uma taxa.
3. Separar contagens observadas, associações descritivas e cenários hipotéticos.
4. Expor evidência e limitações no mesmo fluxo da recomendação executiva.
5. Validar testes e a aplicação em containers; os resultados atuais estão registrados em process-log/checkpoints.

Detalhes de reprodução: solution/README.md. Entrega executiva atual: docs/findings/RAVENSTACK-FINAL-EXECUTIVE-DELIVERY.md. Prontidão da submissão: docs/findings/RAVENSTACK-SUBMISSION-READINESS.md. Matriz oficial do desafio: docs/findings/G4-CHALLENGE-REQUIREMENTS-MATRIX.md. A aplicação inclui o laboratório mensal com modos observado e cenário, e uma auditoria separada dos flags de upgrade/downgrade. Os relatórios G4 anteriores, a pesquisa pública e a metodologia permanecem disponíveis em `docs/findings/`, `docs/research/g4-business-framework.md` e `docs/methodology/analysis.md`.

**Consolidação final desta entrega:** [status de entrega](docs/findings/RAVENSTACK-FINAL-DELIVERY-STATUS.md), [auditoria de upgrade/downgrade](docs/findings/UPGRADE-DOWNGRADE-AUDIT.md) e [checkpoint final](process-log/checkpoints/51-final-delivery.md). A visualização mensal em 24 pontos está documentada em `docs/findings/G4-MONTHLY-CHURN-ANALYSIS.md`; a validação browser/viewport permanece UNKNOWN.

### Resultados / Findings

- Os cinco arquivos contêm 500 contas, 5.000 assinaturas, 25.000 linhas de uso, 2.000 tickets e 600 eventos de churn.
- Há 352 contas com ao menos um evento e 110 contas com a flag de churn ativa. A tabela cruzada tem 75 em ambas, 35 apenas na flag, 277 apenas em eventos e 113 em nenhuma; portanto 312/500 divergem.
- Os eventos registrados aumentam de 73 linhas em 2023 para 527 em 2024. São eventos, não uma taxa por população elegível.
- O ledger diário consolidado cobre 731 dias (2023-01-01 a 2024-12-31), com 1.476 intervalos conta × plano proxy após união de sobreposições/continuidade, 1.433 primeiras relações, 43 reativações de plano e 62 perdas. Os balanços diário de relações e de contas fecham sem resíduo; isso valida a aritmética do ledger, não a semântica comercial das datas.
- Em 2024, as 7/374 perdas de relações da coorte inicial incluem relações que retornaram; 3/374 continuavam sem cobertura ao fim do ano. Nenhuma conta da coorte inicial apresentou perda completa de cobertura sob essa reconstrução. A taxa clássica comercial de customer churn continua UNKNOWN.
- 19.142 linhas de uso antecedem o início da assinatura ligada; 290 estão depois de um fim de assinatura não nulo. Há 21 IDs de uso duplicados, 42 linhas nesses grupos e 21 linhas excedentes após manter uma ocorrência por ID.
- 825/2.000 tickets não têm escore de satisfação. Na divisão retrospectiva “qualquer evento” vs. “nenhum evento”, as médias são 3,980 (815 escores) e 3,983 (360 escores). Medianas de primeira resposta: 89 vs. 87 minutos; resolução: 35 h em ambos; escalamentos: 71/1.395 (5,09%) vs. 24/605 (3,97%). Isso não demonstra tendência ou causalidade.
- O campo de reembolso soma USD 8.652,25, mas não mede receita recorrente perdida. Logo churn, GRR, NRR e exposição recorrente permanecem UNKNOWN.

Todos são registros de um dataset público sintético; limites de qualidade e de inferência constam no relatório. Nenhuma causa ou efeito de intervenção foi afirmado.

### Uso, suporte e evolução mensal

A série completa de 24 meses distingue base de abertura, aquisições, reativações, perdas da coorte inicial, perdas no fechamento, eventos registrados e taxas condicionais. Janeiro de 2023 tem base inicial zero; suas taxas são indefinidas. A decomposição mostra que a maior exposição explica matematicamente parte substancial do aumento absoluto de eventos e perdas, mas as intensidades registradas/plan-proxy também mudam. Isso não identifica causa nem alteração de logging. Uso total foi 124.561→125.964 (+1,13%) e por account-month observado 24,462→24,747 (+1,17%); 19.142/25.000 linhas de uso ocorrem antes da assinatura ligada. Satisfação média por ticket do grupo com qualquer evento foi 3,9804 (815 pontuações) versus 3,9833 (360), com 41,25% de missing no dataset total; comparações são não temporais e não causais. A análise e tabela mensal completas estão em [G4-MONTHLY-CHURN-ANALYSIS.md](docs/findings/G4-MONTHLY-CHURN-ANALYSIS.md), com respostas concisas em [G4-CHALLENGE-FINAL-ANSWERS.md](docs/findings/G4-CHALLENGE-FINAL-ANSWERS.md).

### Recomendações

1. **Agora — Dados / RevOps:** reconciliar as 312 divergências de status, identificar qual contrato está ativo e definir datas de elegibilidade, cancelamento, reativação e receita recorrente.
2. **Em seguida — Customer Success com Analytics:** selecionar uma população confirmada de renovação e executar um piloto randomizado com holdout; medir retenção em 90 dias e reportar MRR confirmado separadamente.
3. **Em paralelo — Product Analytics:** persistir snapshots mensais por conta e assinatura, eventos com subscription_id, atividade temporal válida e denominadores estáveis de tickets/satisfação.

O impacto econômico e a efetividade permanecem condicionais até existirem dados contratuais e resultados experimentais. O Decision Room usa unidades monetárias genéricas e um incremento hipotético de retenção fornecido pelo usuário; não converte hipóteses em forecast nem em dólares observados.

### Limitações

Os dados são sintéticos e apresentam conflitos de entidade e tempo. Não existe mapeamento de evento para assinatura, histórico de elegibilidade ou snapshots de MRR reconciliados. A satisfação não é temporalmente alinhada ao churn e tem 41,25% de ausência. Assim, não há segmentação de risco confiável, previsão válida, causa raiz demonstrada, receita em risco verificável ou ROI causal. O painel lista exemplos de reconciliação, não contas priorizadas por probabilidade de churn.

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Codex (OpenAI) | Inspeção orientada por evidências, análise, implementação, revisão e registro de validações. |
| Python/pandas e pytest | Reproduzir perfis, agregações analíticas e contratos da API. |
| Docker Compose | Construir e exercitar os serviços locais com dados reais do desafio. |

### Workflow

1. O candidato autorizou o workspace independente, slug, limites Git e continuação local. As decisões estão registradas no histórico desta conversa e nos relatórios de checkpoint.
2. A IA recuperou os artefatos anteriores de staging, verificou hashes e reexecutou cópias dos scripts sem alterar os originais.
3. A IA cruzou os resultados para separar eventos, flags, assinaturas, uso e tickets; as métricas não sustentadas foram marcadas como desconhecidas.
4. Com base nessas limitações, a IA criou uma API com cenários assumidos e uma interface narrativa; testes e runtime são registrados sem antecipar resultados.

### Onde a IA errou e como corrigi

Uma tentativa anterior de gravação de arquivos expirou antes de produzir código; a ausência de arquivos foi conferida e o trabalho foi refeito no workspace autorizado. Na implementação do frontend, foram detectados tipos/variáveis não usados e uma configuração do Vitest que pressupunha jsdom não instalado; foram removidos antes do build. Relatórios de staging também continham um bloqueio antigo relacionado ao checkout remoto; esta execução os corrige: o trabalho local agora ocorre no pacote independente autorizado. Nenhuma intervenção humana ou falha adicional é alegada sem evidência.

### Evolução da investigação documentada

A sequência de prompts e checkpoints registra a mudança de escopo: (1) investigação inicial de churn; (2) identificação de divergências entre flags, eventos e datas; (3) aplicação da fórmula clássica e reconstrução por assinaturas; (4) separação entre perda de assinatura e perda do cliente; (5) pedido do candidato para explorar a relação cliente × produto; (6) confirmação de que não há `product_id`; (7) adoção explícita de cliente × plano como proxy; (8) migração do cálculo para ledger diário; (9) inclusão de possíveis upgrades/downgrades e contração como movimentos distintos; (10) consolidação executiva; e (11) orientação mais recente para frequência mensal, denominadores de exposição e separação entre contagem absoluta e retenção normalizada. A série mensal revelou resultados mistos: eventos/100 account-months e perdas de plano-proxy/100 relation-months aumentaram, enquanto episódios de perda completa/100 account-months diminuíram. Isso corrigiu a formulação anterior que deixava a comparação anual sem taxa de exposição.

### O que o candidato adicionou que a IA sozinha não faria

O candidato explicitou o workspace, identidade/slug e fronteiras de efeitos, autorizou o desenvolvimento local e determinou que a indisponibilidade do GitHub não interrompesse trabalho independente. A decisão central de não apresentar receita ou risco falsamente precisos decorre da inspeção dos dados, não de uma premissa comercial fornecida.

## Evidências

- Relatórios incrementais e narrativa de desenvolvimento em process-log/.
- Hashes de dados e perfis reproduzidos em process-log/evidence/.
- Fonte e instrução de atribuição do dataset em solution/data/raw/README.md.
- Saídas das verificações de build, testes e runtime ficam em process-log/checkpoints/08-submission-readiness.md quando verificadas.
- ## Entrega

A submissão segue o canal oficial de Pull Request para `main`, conforme `CONTRIBUTING.md` e `submission-guide.md`. Para executar a aplicação localmente, entre em `solution/` e use `docker compose up --build`; depois abra `http://localhost:8080`.



### Monthly executive reading

The default Chapter 02 view is the Jan 2023–Dec 2024 monthly series (24 points), with separate conditional customer-coverage and account × plan-tier proxy gross/persistent rates, movement counts, and a complete 24-month table. In the reconstructed plan proxy, the largest monthly absolute loss count is 11 in Dec 2024; the highest opening-cohort monthly plan loss rate is 9/1,073 = 0.84% in Oct 2024. These are different measures. Complete customer-coverage opening-cohort loss peaks at 1/149 = 0.67% in Nov 2023; the 2024 maximum is 2/385 = 0.52% in Sep 2024. The conditional series does not establish a statistically significant or commercially certified trend. The component is `solution/apps/web/src/features/monthly/MonthlyChurnView.tsx`; browser visual QA remains unverified because access to the local page was denied.

## Como explorar o laboratório mensal

1. Comece pelo [paper executivo](docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf); a [fonte Markdown e instruções de reprodução](docs/paper/README.md) acompanham o PDF.
2. Inicie a aplicação em `solution/` com `docker compose up --build` e abra http://localhost:8080.
3. No Capítulo 02, examine a série mensal completa de jan/2023 a dez/2024 e selecione um Key Moment. Outubro de 2024 destaca a maior taxa mensal da coorte inicial; dezembro destaca a maior contagem bruta. As duas medidas têm numeradores diferentes.
4. Use “Open [month] in the Monthly Business Lab” para levar o mês selecionado ao Capítulo 04. OBSERVED preserva a linha de base reconstruída; SCENARIO recalcula hipóteses submetidas à API sem alterar o histórico.
5. Consulte definições, limitações e evidências em `docs/findings/`, `process-log/checkpoints/` e `process-log/evidence/`.

A aplicação é um complemento interativo ao paper. Os Key Moments são seletores determinísticos descritivos, não testes de significância. `plan_tier` é um proxy de relação comercial; identidade real de produto, churn comercial certificado, receita recorrente observada e causalidade permanecem não identificáveis no dataset.

---

_Submissão enviada em: 2026-10-22_
