# Registro de decisões — JourneyGraph

## D001 — Challenge escolhido

- **ID:** D001
- **Título:** Challenge escolhido
- **Contexto:** o repositório oferece múltiplos desafios e a submissão precisa ter escopo inequívoco.
- **Decisão:** desenvolver exclusivamente o **Challenge 001 — Diagnóstico de Churn**, sob o nome de produto **JourneyGraph**.
- **Justificativa:** concentrar tempo, evidências e implementação em um único problema de alto valor para retenção.
- **Consequências:** documentação, código e process log deverão tratar somente do Challenge 001.
- **Status:** APROVADA

## D002 — Tese do produto

- **ID:** D002
- **Título:** Tese do JourneyGraph
- **Contexto:** um diagnóstico isolado tem valor limitado se não conectar evidência a decisão e aprendizagem operacional.
- **Decisão:** JourneyGraph é uma plataforma de inteligência de retenção que reconstrói trajetórias temporais de contas, identifica padrões antes de churn, retenção e reativação, prioriza receita em risco e converte evidências em intervenções e experimentos.
- **Justificativa:** ligar análise temporal, impacto econômico e ação mensurável aumenta utilidade para negócio.
- **Consequências:** fases futuras deverão preservar rastreabilidade entre fontes, sinais, prioridades, intervenções e resultados.
- **Status:** APROVADA

## D003 — Challenge 002

- **ID:** D003
- **Título:** Exclusão do conteúdo anterior do Challenge 002
- **Contexto:** existiu trabalho anterior denominado SupportOps Intelligence Graph fora deste clone.
- **Decisão:** preservar esse conteúdo somente como backup externo; nenhum arquivo do Challenge 002 integra ou integrará `submissions/carlos-henrique/`.
- **Justificativa:** impedir mistura de escopos, evidências e propriedade intelectual entre duas propostas.
- **Consequências:** qualquer conteúdo desse trabalho encontrado no clone é condição de bloqueio; a menção neste registro serve apenas para documentar sua exclusão.
- **Status:** APROVADA

## D004 — Escopo permitido

- **ID:** D004
- **Título:** Caminho único autorizado
- **Contexto:** as regras oficiais rejeitam mudanças fora da pasta individual da submissão.
- **Decisão:** criar, alterar, remover ou versionar somente arquivos abaixo de `submissions/carlos-henrique/`.
- **Justificativa:** preservar a integridade do repositório oficial e a separação entre candidatos.
- **Consequências:** qualquer necessidade de mudança externa interrompe a execução; arquivos da raiz permanecem intocados.
- **Status:** APROVADA

## D005 — Event log antes do grafo

- **ID:** D005
- **Título:** Event-log-first
- **Contexto:** projetar um grafo antes de validar identidade, granularidade e tempo pode cristalizar erros de integração.
- **Decisão:** nenhum grafo será construído antes da criação e validação do event log temporal.
- **Justificativa:** o event log torna ordem, origem e reconciliação verificáveis antes da projeção em rede.
- **Consequências:** auditoria e integração temporal são gates obrigatórios para a fase de grafo.
- **Status:** APROVADA

## D006 — NetworkX antes de Neo4j

- **ID:** D006
- **Título:** Tecnologia mínima para o grafo MVP
- **Contexto:** um banco de grafos adiciona custo operacional antes de existir evidência de escala ou uso que o justifique.
- **Decisão:** usar NetworkX no MVP; avaliar Neo4j somente após validar o modelo relacional e o valor operacional do grafo.
- **Justificativa:** reduzir complexidade e custo enquanto se testa a hipótese de valor.
- **Consequências:** Neo4j não integra a stack da fundação e dependerá de critérios explícitos de adoção.
- **Status:** APROVADA

## D007 — Não causalidade

- **ID:** D007
- **Título:** Associação temporal não implica causa
- **Contexto:** sequências e correlações observacionais podem refletir confundimento, seleção ou informação posterior ao desfecho.
- **Decisão:** não apresentar associações temporais como causas de churn.
- **Justificativa:** manter rigor estatístico e evitar intervenções baseadas em alegações não sustentadas.
- **Consequências:** linguagem, visualizações e recomendações deverão distinguir evidência observacional, hipótese e efeito causal validado.
- **Status:** APROVADA

## D008 — Ausência dos dados

- **ID:** D008
- **Título:** Fontes oficiais ainda indisponíveis
- **Contexto:** os cinco datasets oficiais não estão presentes localmente.
- **Decisão:** não criar dados sintéticos para substituí-los e não iniciar análise sem as cinco fontes.
- **Justificativa:** resultados fabricados ou parciais comprometeriam contrato, reconciliação e credibilidade.
- **Consequências:** schemas permanecem pendentes e a Fase 1 depende da disponibilização oficial de todos os arquivos.
- **Status:** APROVADA

## D009 — Git remoto

- **ID:** D009
- **Título:** Publicação condicionada a autorização
- **Contexto:** a Fase 0 autoriza versionamento local, mas não publicação externa.
- **Decisão:** permitir o commit local definido; condicionar push e Pull Request a autorização explícita posterior.
- **Justificativa:** separar validação local de ações remotas visíveis e potencialmente irreversíveis.
- **Consequências:** não configurar tracking, não criar branch remota, não fazer push e não abrir PR nesta fase.
- **Status:** APROVADA

## D010 — Diretório ignorado

- **ID:** D010
- **Título:** Staging seletivo sob regra de ignore
- **Contexto:** o `.gitignore` da raiz ignora `submissions/` e não pode ser alterado.
- **Decisão:** adicionar somente arquivos revisados, um por vez, com `git add -f`; nunca adicionar a pasta inteira ou usar staging amplo.
- **Justificativa:** incluir intencionalmente a submissão sem modificar arquivo oficial nem capturar conteúdo acidental.
- **Consequências:** cada caminho deverá ser conferido antes e depois do staging, seguido de revisão do diff completo.
- **Status:** APROVADA

## Registro de erros e riscos da fase

Nenhum erro de implementação foi observado, pois a fase foi exclusivamente estrutural. O principal risco identificado foi o bloqueio da pasta submissions/ pelo .gitignore da raiz.

---

## D011 — Estratégia de carga dos CSVs

- **ID:** D011
- **Título:** Carga read-only, explícita e rastreável
- **Contexto:** os cinco arquivos precisam ser lidos sem alteração, aliases ou coerção silenciosa.
- **Decisão:** resolver caminhos a partir da solução, exigir os cinco nomes oficiais, testar UTF-8 primeiro, detectar delimiter e registrar encoding, colunas e dtypes inferidos.
- **Justificativa:** torna a carga reproduzível e mantém o raw imutável.
- **Consequências:** arquivo ausente ou encoding indeterminado causa falha crítica; dtypes inferidos não são schema canônico.
- **Status:** APROVADA

## D012 — Chaves primárias candidatas

- **ID:** D012
- **Título:** Identidade por snapshot e exceção de uso
- **Contexto:** quatro IDs são completos e únicos, mas `usage_id` não é; o composto de uso também duplica.
- **Decisão:** tratar `account_id`, `subscription_id`, `ticket_id` e `churn_event_id` como `CANDIDATE` no snapshot. Manter a identidade de `feature_usage` como `INCONCLUSIVE`.
- **Justificativa:** há zero nulos/duplicatas excedentes nas quatro candidatas, contra 21 no `usage_id` e 3 no composto testado.
- **Consequências:** a Fase 2 precisa de identidade substituta determinística para uso e não pode descartar duplicatas sem regra.
- **Status:** APROVADA COM RESSALVA; identidade de uso ABERTA

## D013 — Relacionamentos utilizáveis

- **ID:** D013
- **Título:** Cobertura referencial completa com cardinalidade um-para-muitos
- **Contexto:** todas as fontes dependem das chaves de conta ou assinatura.
- **Decisão:** autorizar as quatro relações mínimas para vínculo relacional, classificadas `UNSAFE_WITHOUT_AGGREGATION` para joins tabulares.
- **Justificativa:** taxa de match de 100%, zero órfãos e zero FKs nulas, mas todas expandem o pai.
- **Consequências:** vínculos são utilizáveis no event log; joins para tabelas analíticas exigem grão e agregação explícitos.
- **Status:** APROVADA COM RESSALVAS

## D014 — Política contra mega-join

- **ID:** D014
- **Título:** Proibição de mega-tabela ingênua
- **Contexto:** o encadeamento key-only expandiu 500 contas para 147.896 linhas.
- **Decisão:** proibir materialização e uso analítico de mega-join entre as cinco fontes.
- **Justificativa:** multiplicador de 295,792× produziria contagens e somas financeiras incorretas.
- **Consequências:** normalizar eventos por fonte; agregar ou selecionar child records as-of antes de qualquer join ao grão de conta.
- **Status:** APROVADA

## D015 — Campos temporais confiáveis

- **ID:** D015
- **Título:** Parsing validado, cronologia condicionada
- **Contexto:** sete campos temporais parseiam sem inválidos, mas eventos contradizem o ciclo de vida.
- **Decisão:** autorizar `signup_date`, `start_date`, `end_date`, `usage_date`, `submitted_at`, `closed_at` e `churn_date` como timestamps de origem; não autorizar automaticamente sua coerência relacional.
- **Justificativa:** ranges e parsing são válidos; 19.142 usos, 1.077 tickets e 53 churns violam predecessores esperados.
- **Consequências:** a Fase 2 deve manter flags de qualidade, timezone declarado, regra de quarentena e métricas de cobertura antes/depois.
- **Status:** APROVADA COM RESSALVAS

## D016 — Tratamento de churn recorrente

- **ID:** D016
- **Título:** Preservar recorrência como eventos distintos
- **Contexto:** 175 contas possuem mais de um churn e o máximo observado é cinco.
- **Decisão:** não colapsar churn por conta; preservar `churn_event_id`, ordem e data de cada evento.
- **Justificativa:** reduzir a um flag destruiria informação de ciclo e confundiria reativação.
- **Consequências:** coortes e cutoffs futuros deverão selecionar explicitamente primeiro, último ou n-ésimo churn conforme o uso.
- **Status:** APROVADA

## D017 — Definição provisória de reativação

- **ID:** D017
- **Título:** Evidência explícita sem regra final fechada
- **Contexto:** existem 61 eventos com `is_reactivation=true` e 2.117 assinaturas iniciadas após o primeiro churn da conta.
- **Decisão:** classificar disponibilidade como `EXPLICIT`, mas manter a regra operacional final `DECISION_PENDING_PHASE_2`.
- **Justificativa:** o flag é direto, porém múltiplas assinaturas e cronologias conflitantes impedem inferência automática única.
- **Consequências:** a Fase 2 deve combinar flag, ordem de churn e nova `subscription_id`, documentando precedência e exceções.
- **Status:** PARCIALMENTE APROVADA; regra final ABERTA

## D018 — Campos proibidos por leakage

- **ID:** D018
- **Título:** Separação entre outcome, pós-evento e features as-of
- **Contexto:** flags, datas, motivos, refunds e feedback codificam o desfecho; métricas de suporte têm disponibilidade posterior.
- **Decisão:** proibir como features pré-churn `accounts.churn_flag`, `subscriptions.churn_flag`, `subscriptions.end_date` sem regra as-of e todos os campos de `churn_events` exceto o vínculo usado em auditoria. Submeter uso, tickets e métricas de suporte a cutoff temporal.
- **Justificativa:** evita leakage explícito, proxy e temporal.
- **Consequências:** cada feature futura deverá declarar `available_at` e provar que antecede a data de corte.
- **Status:** APROVADA

## D019 — Política de texto e privacidade

- **ID:** D019
- **Título:** Texto bruto restrito à zona raw
- **Contexto:** `account_name` e `feedback_text` são campos textuais; regex não encontrou email, telefone ou URL, mas ausência de match não elimina risco.
- **Decisão:** permitir somente missingness, comprimentos e contagens regex agregadas nos artefatos; mascarar IDs e nunca reproduzir texto livre.
- **Justificativa:** minimização e LGPD by design reduzem exposição sem impedir auditoria estrutural.
- **Consequências:** análise semântica, exemplos e uso por LLM continuam proibidos até fase explicitamente autorizada e governada.
- **Status:** APROVADA

## D020 — Gate de viabilidade do event log

- **ID:** D020
- **Título:** Event log viável com controles obrigatórios
- **Contexto:** chaves relacionais, cobertura e datas existem, mas identidade de uso, cronologia e target têm conflitos materiais.
- **Decisão:** classificar a Fase 2 como `PASS_WITH_WARNINGS`.
- **Justificativa:** é possível construir eventos por fonte sem mega-join; os riscos são controláveis por regras explícitas, quarentena e reconciliação.
- **Consequências:** antes de produzir qualquer event log, a Fase 2 deve implementar identidade substituta de uso, precedência do target, cutoffs as-of, flags de cronologia, separação de grãos e preservação de recorrência/reativação.
- **Status:** APROVADA COM RESSALVAS

---

## D021 — Schema canônico do event log

- **ID:** D021
- **Título:** Evento normalizado com provenance por linha
- **Contexto:** fases posteriores precisam reconstruir jornadas sem perder grão ou origem.
- **Decisão:** adotar schema de 28 campos, `event_id` determinístico e obrigatório, `account_id` obrigatório no ativo, assinatura opcional, tempo canônico, origem, linha física, regra, qualidade e metadados de recorrência.
- **Justificativa:** separa fontes e entidades, permite auditoria e evita mega-join.
- **Consequências:** todo novo tipo deverá preencher o mesmo contrato e registrar sua disponibilidade temporal.
- **Status:** APROVADA

## D022 — Política de deduplicação

- **ID:** D022
- **Título:** Preservar registros distintos e remover somente cópia integral secundária
- **Contexto:** `usage_id` e a chave candidata duplicam, mas não há duplicata integral no snapshot.
- **Decisão:** incluir `source_row_number` na identidade; sinalizar todas as linhas de IDs/chaves repetidos; remover apenas duplicata exata secundária e reconciliá-la separadamente.
- **Justificativa:** evita perda e soma silenciosa de eventos legítimos ou conflitantes.
- **Consequências:** 42 linhas recebem `DUPLICATE_SOURCE_ID`, 6 recebem `DUPLICATE_CANDIDATE_KEY` e nenhuma é removida neste build.
- **Status:** APROVADA COM RESSALVAS

## D023 — Política de quarentena

- **ID:** D023
- **Título:** Erro temporal fatal permanece auditável fora do log ativo
- **Contexto:** uso, suporte, churn e reativação contêm cronologias incompatíveis.
- **Decisão:** classificar como `QUARANTINED` evento pré-conta, uso pré/pós-assinatura, timestamp/ID inválido, fim antes do início, fechamento antes da abertura, churn pré-assinatura e reativação sem churn anterior utilizável.
- **Justificativa:** 21.659 eventos não podem sustentar sequência válida, mas também não podem desaparecer.
- **Consequências:** análises usam somente o log ativo; quarentena permanece rastreável e recuperável mediante evidência upstream.
- **Status:** APROVADA

## D024 — Ordenação de eventos no mesmo dia

- **ID:** D024
- **Título:** Desempate técnico estável e não causal
- **Contexto:** fontes diárias perdem sequência intradiária e 5.011 eventos compartilham conta/data com outra ocorrência.
- **Decisão:** aplicar a ordem documentada em `event_order_on_same_day` e marcar `SAME_DAY_ORDER_ASSIGNED`.
- **Justificativa:** garante idempotência sem inventar causalidade ou horário.
- **Consequências:** a ordem serve somente para sort; análises não podem tratá-la como precedência factual.
- **Status:** APROVADA COM RESSALVAS

## D025 — Modelo de churn recorrente

- **ID:** D025
- **Título:** Churn como sequência de eventos de conta
- **Contexto:** após separar reativações, 149 contas têm múltiplos churns e o máximo é cinco.
- **Decisão:** preservar cada CHURN_RECORDED com sequência, anterior, próximo e dias desde o anterior.
- **Justificativa:** um flag binário destruiria ciclos observados.
- **Consequências:** fases posteriores devem declarar primeiro, último ou n-ésimo churn e nunca inferir retained por ausência.
- **Status:** APROVADA

## D026 — Modelo de reativação

- **ID:** D026
- **Título:** Reativação explícita, separada e dependente de churn utilizável anterior
- **Contexto:** há 61 flags explícitas; 31 não possuem churn anterior utilizável após a quarentena.
- **Decisão:** gerar REACTIVATION_RECORDED somente do flag real, preservar sequência e quarentenar ausência de churn anterior utilizável; não inferir retorno por assinatura nova.
- **Justificativa:** evita apagar churn, inventar assinatura ou misturar outcome com retorno.
- **Consequências:** 30 reativações permanecem temporalmente utilizáveis e 31 ficam auditáveis na quarentena.
- **Status:** APROVADA COM RESSALVAS

## D027 — Atribuição churn–assinatura

- **ID:** D027
- **Título:** Candidato somente para assinatura ativa exata
- **Contexto:** churn é de conta e múltiplas assinaturas frequentemente se sobrepõem.
- **Decisão:** preencher `candidate_subscription_id` somente em `EXACT_ACTIVE_MATCH`; manter nulo em múltiplas ativas, anterior única, ausência e ambiguidade.
- **Justificativa:** apenas 67 de 600 ocorrências têm uma assinatura ativa exata; 478 têm múltiplas candidatas.
- **Consequências:** o campo é evidência de atribuição, não alteração do grão do churn.
- **Status:** APROVADA COM RESSALVAS

## D028 — Modelo de episódio

- **ID:** D028
- **Título:** Uma assinatura, um episódio inicial
- **Contexto:** contas possuem múltiplas assinaturas, muitas abertas e sobrepostas.
- **Decisão:** criar 5.000 episódios independentes, preservar datas de origem e inferir previous/next somente pela ordem na conta.
- **Justificativa:** fusão ou encerramento por churn inventaria fatos ausentes.
- **Consequências:** 4.514 episódios permanecem abertos; 4.992 recebem warning de sobreposição.
- **Status:** APROVADA COM RESSALVAS

## D029 — Campos excluídos por leakage e privacidade

- **ID:** D029
- **Título:** Minimização temporal e textual no event log
- **Contexto:** flags snapshot, end_date, motivo, refund, feedback e métricas pós-interação podem antecipar desfecho ou expor texto.
- **Decisão:** não copiar nome, feedback, motivo, refund ou churn flags; usar `end_date` somente como evento no próprio tempo e atributos de fechamento somente em SUPPORT_TICKET_CLOSED.
- **Justificativa:** aplica LGPD by design e evita leakage explícito, proxy e temporal.
- **Consequências:** outputs mantêm categorias controladas, números autorizados e provenance sem texto livre.
- **Status:** APROVADA

## D030 — Gate do event log

- **ID:** D030
- **Título:** Camada temporal utilizável com filtros obrigatórios
- **Contexto:** 35.586 oportunidades reconciliam integralmente, porém 21.659 eventos são temporalmente inválidos e a atribuição de churn é majoritariamente ambígua.
- **Decisão:** classificar a Fase 2 como `PASS_WITH_WARNINGS`.
- **Justificativa:** 13.927 eventos ativos, provenance completo, IDs determinísticos, reconciliação zero e idempotência permitem diagnóstico controlado.
- **Consequências:** Fase 3 deve excluir quarentena, respeitar flags, declarar cutoffs, manter churn no grão de conta e não interpretar desempate como causalidade.
- **Status:** APROVADA COM RESSALVAS

---

## D031 — População analítica principal

- **Decisão:** usar `VALID + VALID_WITH_WARNING`, com quarentena excluída; `VALID` forma a população estrita.
- **Justificativa:** warnings são utilizáveis com ressalva e preservam cobertura, enquanto quarentena contém cronologias não autorizadas.
- **Consequência:** métricas principais exigem análise de sensibilidade.
- **Status:** APROVADA COM RESSALVAS

## D032 — Definição de observation_end

- **Decisão:** maior `event_time` utilizável da população principal, `2024-12-31T19:00:00`.
- **Justificativa:** é o último ponto temporal autorizado no event log.
- **Consequência:** episódios abertos são observados, não artificialmente encerrados.
- **Status:** APROVADA

## D033 — Classificação principal de desfecho

- **Decisão:** prioridade `REACTIVATED_THEN_CHURNED_AGAIN`, `REACTIVATED`, `RECURRING_CHURN`, `SINGLE_CHURN`, `NO_CHURN_OBSERVED`.
- **Justificativa:** garante exatamente um estado executivo sem apagar estados auxiliares.
- **Consequência:** 500 contas permanecem únicas no grão.
- **Status:** APROVADA

## D034 — Cutoff do primeiro churn

- **Decisão:** primeiro churn utilizável para contas com churn; `observation_end` para as demais.
- **Justificativa:** impede uso de eventos posteriores ao desfecho em features comparativas.
- **Consequência:** pós-reativação aparece somente em diagnóstico descritivo separado.
- **Status:** APROVADA

## D035 — Janelas temporais

- **Decisão:** 7, 30, 60 e 90 dias, mais lifetime até o cutoff, com inclusão do dia do cutoff.
- **Justificativa:** acomoda granularidade diária sem inventar ordem intradiária.
- **Consequência:** toda feature de janela é reproduzível por `feature_cutoff_time`.
- **Status:** APROVADA

## D036 — Política de censura

- **Decisão:** manter `NO_CHURN_OBSERVED` e `is_censored_episode`; calcular duração observada de abertos até `observation_end`.
- **Justificativa:** ausência de evento futuro não prova retenção ou encerramento.
- **Consequência:** Fase 4 deverá preservar a censura administrativa.
- **Status:** APROVADA

## D037 — Definição de receita associada

- **Decisão:** MRR de conta é a soma ativa no cutoff; MRR de episódio permanece no grão original.
- **Justificativa:** evita antecipação temporal e alegação financeira não comprovada.
- **Consequência:** relatórios usam “MRR associado”, nunca perda ou recuperação automática.
- **Status:** APROVADA COM RESSALVAS

## D038 — Política de grupos pequenos

- **Decisão:** `MIN_GROUP_SIZE=20`; grupos menores recebem `SMALL_SAMPLE` e não podem sustentar finding principal.
- **Justificativa:** reduz destaque de diferenças frágeis sem ocultar o grupo técnico.
- **Consequência:** todos os grupos permanecem nos JSONs com status explícito.
- **Status:** APROVADA

## D039 — Confidence level dos findings

- **Decisão:** `HIGH`, `MEDIUM` ou `LOW` conforme tamanho, cobertura, warnings, evidência e estabilidade; evidência vazia é erro.
- **Justificativa:** separa força da evidência de relevância operacional.
- **Consequência:** cada finding inclui n, efeito, comparação, limitação e investigação recomendada.
- **Status:** APROVADA

## D040 — Sensitivity analysis

- **Decisão:** recalcular métricas em `VALID` e `VALID + VALID_WITH_WARNING`; classificar diferença relativa até 10% como `ROBUST`, até 30% como `SENSITIVE` e acima como `UNSTABLE`.
- **Justificativa:** warnings alteram tanto eventos quanto cutoffs disponíveis.
- **Consequência:** churn observado, recorrência, reativação e mediana de uso 90d ficaram `UNSTABLE` e não são findings principais.
- **Status:** APROVADA COM RESSALVAS

## D041 — Gate do diagnóstico executivo

- **Decisão:** `PASS_WITH_WARNINGS`.
- **Justificativa:** 500 contas, 5.000 episódios, reconciliação zero, cutoffs auditáveis, outputs determinísticos e findings governados permitem avançar; cobertura analítica de 39,1362%, sobreposição de 99,84% e sensibilidade dos outcomes impedem `PASS` pleno.
- **Consequência:** Fase 4 pode usar apenas as populações, cutoffs e censura documentados; nenhuma métrica instável pode ser tratada como evidência principal sem estratificação.
- **Status:** APROVADA COM RESSALVAS

## Revisão operacional complementar

- **Resolução de suporte:** lookup read-only por `ticket_id`, autorizado somente no fechamento utilizável e antes do cutoff.
- **Suporte por episódio:** contexto de conta no intervalo, sem atribuição à assinatura.
- **Sobreposição:** recalculada até o boundary pertinente; não usa episódio futuro para feature de conta.
- **Segmentos:** cinco agregados sem `account_id`, não constituem score.
- **Jornadas:** ordenação estável, duplicatas consecutivas colapsadas, limite 12 e suporte explícito; nenhuma mineração formal.

---

## D042 ? Unidade principal conta

- **Decis?o:** usar uma linha por conta; IDs permanecem somente em Parquets operacionais.
- **Justificativa:** churn ? evento de conta e epis?dios repetidos violam independ?ncia simples.
- **Status:** APROVADA

## D043 ? Primeiro churn como endpoint

- **Decis?o:** usar o primeiro churn utiliz?vel em ou ap?s a exposi??o; recorr?ncias n?o substituem o endpoint e churns anteriores s?o apenas contabilizados.
- **Justificativa:** define um ?nico evento temporal reproduz?vel sem antecipar jornadas futuras.
- **Status:** APROVADA

## D044 ? Origem temporal principal

- **Decis?o:** primeira assinatura utiliz?vel; signup entra somente em sensibilidade.
- **Justificativa:** assinatura inicia exposi??o comercial observ?vel, enquanto signup testa depend?ncia da origem.
- **Status:** APROVADA COM RESSALVAS

## D045 ? Censura administrativa

- **Decis?o:** censura ? direita em `2024-12-31T19:00:00` para contas sem primeiro churn observado.
- **Justificativa:** aus?ncia de evento at? o fim da janela n?o prova reten??o definitiva.
- **Status:** APROVADA COM RESSALVAS

## D046 ? Popula??es estrita e principal

- **Decis?o:** principal usa `VALID + VALID_WITH_WARNING`; estrita usa somente `VALID`; quarentena ? proibida.
- **Justificativa:** preserva cobertura e mede influ?ncia dos warnings.
- **Status:** APROVADA COM RESSALVAS

## D047 ? Landmarks

- **Decis?o:** marcos em 30, 60 e 90 dias; excluir churn at? o marco e falta de observabilidade; calcular features somente at? o marco.
- **Justificativa:** evita tempo imortal e exposi??o desigual em vari?veis comportamentais.
- **Status:** APROVADA

## D048 ? Pol?tica de grupos pequenos

- **Decis?o:** exigir n m?nimo 20, pelo menos cinco eventos por grupo e at-risk m?nimo 20; registrar grupos omitidos.
- **Justificativa:** impede destaque de curvas e p-values sem suporte observacional razo?vel.
- **Status:** APROVADA

## D049 ? Uso de RMST

- **Decis?o:** estimar RMST em 90, 180 e 365 dias e comunicar somente diferen?a observada de tempo m?dio sem primeiro churn.
- **Justificativa:** resume curvas quando mediana ou proporcionalidade s?o fr?geis sem criar interpreta??o causal.
- **Status:** APROVADA COM RESSALVAS

## D050 ? Crit?rios para Cox

- **Decis?o:** n?o executar Cox nesta fase.
- **Justificativa:** endpoints s?o sens?veis a warnings, a popula??o estrita tem somente 46 eventos eleg?veis e riscos proporcionais n?o foram testados de forma est?vel.
- **Consequ?ncia:** nenhum coeficiente, hazard ratio, concord?ncia, score ou res?duo foi produzido.
- **Status:** N?O EXECUTADA POR GATE

## D051 ? Gate de sobreviv?ncia

- **Decis?o:** `PASS_WITH_WARNINGS`.
- **Justificativa:** 500 contas principais, 497 estritas, quatro Parquets, oito JSONs, quatro relat?rios, seis figuras, testes e 22 hashes id?nticos sustentam uso descritivo; 325 versus 46 eventos e censura de 35,0% versus 90,74% demonstram sensibilidade material.
- **Consequ?ncia:** Fase 5 pode usar curvas e landmarks somente com popula??es, censura, at-risk e sensibilidade preservados; score, causalidade e interven??o permanecem proibidos.
- **Status:** APROVADA COM RESSALVAS

## Revis?o humana complementar da Fase 4

- exposi??o, endpoint, censura, dura??o e exclus?es revisados;
- churn recorrente e pr?-exposi??o revisados;
- landmark features e aus?ncia de futuro revisados;
- curvas, at-risk, intervalos, log-rank, BH e RMST revisados;
- Cox e assinatura explicitamente n?o executados;
- pressupostos, sensibilidade e linguagem causal revisados;
- figuras, PII, hashes, escopo e diff revisados.

---

## D052 ? Conta como unidade sequencial

- **Decis?o:** suporte e jornada usam conta, nunca ocorr?ncia isolada, como unidade.
- **Justificativa:** limita domin?ncia de contas com grande volume.
- **Status:** APROVADA

## D053 ? Escopos de jornada

- **Decis?o:** oito escopos temporais expl?citos; nenhum evento posterior ao boundary entra na linha.
- **Justificativa:** impede mistura de jornadas e leakage temporal.
- **Status:** APROVADA

## D054 ? Representa??es raw, collapsed e bucketed

- **Decis?o:** preservar tipo completo em raw, vocabul?rio reduzido em collapsed e JSON estruturado di?rio em bucketed.
- **Justificativa:** concilia auditoria, minera??o e parsing determin?stico.
- **Status:** APROVADA

## D055 ? Pol?tica de ordena??o no mesmo dia

- **Decis?o:** desempate t?cnico por ordem can?nica e event_id; depend?ncia classificada NONE/PARTIAL/HIGH.
- **Justificativa:** ordem t?cnica n?o deve ser comunicada como causal.
- **Status:** APROVADA COM RESSALVAS

## D056 ? Suporte por conta

- **Decis?o:** account_support ? o n?mero de contas distintas que cont?m o padr?o.
- **Justificativa:** ocorr?ncias permanecem medida secund?ria.
- **Status:** APROVADA

## D057 ? Par?metros de n-gram

- **Decis?o:** collapsed 2?5, raw bigram de sensibilidade; suporte m?nimo 10, relativo 2%, grupo 20.
- **Justificativa:** oferece baseline transparente antes da minera??o flex?vel.
- **Status:** APROVADA

## D058 ? Par?metros de sequence mining

- **Decis?o:** implementa??o pr?pria testada; suporte 15 contas, comprimento 5, gap 5 eventos/90 dias.
- **Justificativa:** evita depend?ncia adicional e mant?m sem?ntica audit?vel.
- **Status:** APROVADA

## D059 ? Pol?tica de padr?es fechados

- **Decis?o:** remover padr?o menor quando superpadr?o tem conjunto id?ntico de contas; contabilizar antes/depois.
- **Justificativa:** reduz redund?ncia sem ocultar exclus?es.
- **Status:** APROVADA

## D060 ? Taxonomia de jornadas

- **Decis?o:** dez classes determin?sticas, uma principal e secund?rias opcionais; nenhuma classe ? score ou previs?o.
- **Justificativa:** transforma sequ?ncias em vocabul?rio de neg?cio audit?vel.
- **Status:** APROVADA COM RESSALVAS

## D061 ? Estabilidade principal versus estrita

- **Decis?o:** ROBUST, SENSITIVE e UNSTABLE dependem de presen?a, dire??o, magnitude, amostra e ordem.
- **Justificativa:** warnings n?o podem ser apagados da interpreta??o.
- **Status:** APROVADA COM RESSALVAS

## D062 ? Controle de exposi??o

- **Decis?o:** janelas 7/30/60/90d, landmarks, suporte por conta e bandas Q33/Q67.
- **Justificativa:** jornadas longas geram mais combina??es por constru??o.
- **Status:** APROVADA

## D063 ? Gate de journey mining

- **Decis?o:** `PASS_WITH_WARNINGS`.
- **Justificativa:** outputs reconciliados e padr?es est?veis permitem proje??o governada futura; warnings, exposi??o residual e ordem t?cnica impedem PASS pleno.
- **Consequ?ncia:** apenas padr?es ROBUST/SENSITIVE com suporte, denominador, escopo e depend?ncia de ordem preservados podem alimentar a Fase 6.
- **Status:** APROVADA COM RESSALVAS

## Revis?o humana complementar da Fase 5

- sequ?ncias, escopos, ordena??o, exposi??o, transi??es, n-grams e padr?es revisados;
- pruning, churn, recorr?ncia, reativa??o, estabilidade e taxonomia revisados;
- findings, figuras, causalidade, PII, hashes, escopo e diff revisados;
- grafo, centralidade, comunidades, interven??o e app confirmados como n?o implementados.

## D064 ? NetworkX como implementa??o de refer?ncia

- **Decis?o:** construir e validar localmente em NetworkX 3.6.1.
- **Justificativa:** reprodu??o determin?stica sem servidor, credencial ou custo externo.
- **Status:** APROVADA

## D065 ? Separa??o instance graph e analytical graph

- **Decis?o:** rastreabilidade fica no `INSTANCE_GRAPH`; evid?ncia agregada promov?vel fica no `ANALYTICAL_GRAPH`.
- **Justificativa:** impede mistura silenciosa de m?tricas de inst?ncia e agregadas.
- **Status:** APROVADA

## D066 ? Identificadores an?nimos determin?sticos

- **Decis?o:** SHA-256 truncado com prefixo e salt p?blico apenas de namespacing.
- **Justificativa:** estabilidade e auditoria sem expor IDs operacionais ou mapa revers?vel.
- **Status:** APROVADA

## D067 ? Rela??es n?o causais

- **Decis?o:** validar tipos e propriedades textuais contra vocabul?rio causal proibido.
- **Justificativa:** sequ?ncia, associa??o e centralidade n?o demonstram causa.
- **Status:** APROVADA

## D068 ? Pattern como n? anal?tico

- **Decis?o:** identidade combina padr?o normalizado, tipo, escopo, outcome e popula??o; `pattern_family_key` agrupa equivalentes.
- **Justificativa:** preserva contexto sem fundir padr?es hom?nimos.
- **Status:** APROVADA

## D069 ? Quality Profile como entidade expl?cita

- **Decis?o:** popula??o, estabilidade, ordem, amostra, warning, cobertura e confian?a formam perfis reutiliz?veis.
- **Justificativa:** qualidade passa a integrar a topologia e n?o apenas metadados externos.
- **Status:** APROVADA

## D070 ? Centralidade somente em EventType e Pattern

- **Decis?o:** PageRank, grau e betweenness s?o calculados na proje??o de EventType; Pattern ? ordenado apenas por suporte/MRR agregado; Account n?o recebe centralidade.
- **Justificativa:** evita ranking individual e interpreta??o causal indevida.
- **Status:** APROVADA COM RESSALVAS

## D071 ? Subgrafos promov?veis

- **Decis?o:** produzir `ROBUST`, `PROMOTABLE`, `CHURN`, `REACTIVATION`, `QUALITY_REVIEW` e `HIGH_MRR`.
- **Justificativa:** limita consumidores futuros a recortes governados e expl?citos.
- **Status:** APROVADA COM RESSALVAS

## D072 ? Exporta??o Neo4j sem depend?ncia de servidor

- **Decis?o:** gerar CSV/Cypher port?teis e amostrar EventInstance por 250 jornadas determin?sticas.
- **Justificativa:** demonstra portabilidade sem ampliar infraestrutura; GraphML mant?m o grafo completo.
- **Status:** APROVADA COM RESSALVAS

## D073 ? Reconcilia??o grafo versus tabelas

- **Decis?o:** exigir `difference_unexplained = 0` para contas, jornadas, taxonomia, padr?es, transi??es, findings e MRR.
- **Justificativa:** o grafo ? uma camada governada, n?o uma fonte paralela sem controle.
- **Status:** APROVADA

## D074 ? Gate do JourneyGraph

- **Decis?o:** `PASS_WITH_WARNINGS`.
- **Justificativa:** grafos reconciliados, an?nimos, temporalmente consistentes e n?o causais est?o utiliz?veis; warnings herdados, cobertura de reativa??o, amostra Neo4j e aus?ncia de execu??o externa impedem PASS pleno.
- **Consequ?ncia:** somente `PROMOTABLE_GRAPH` e subgrafos governados podem alimentar a Fase 7, preservando qualidade, suporte, estabilidade e revis?o humana.
- **Status:** APROVADA COM RESSALVAS

## Revis?o humana complementar da Fase 6

- modelo conceitual, dez labels, rela??es e propriedades revisados;
- anonimiza??o, salt, aus?ncia de mapa revers?vel, PII e texto livre revisados;
- `NEXT_EVENT`, limites, ordem intradi?ria e endpoints revisados;
- promo??o de padr?es/transi??es, denominadores, suporte e estabilidade revisados;
- outcomes, taxonomia, QualityProfile, centralidade e caminhos revisados;
- MRR confirmado exclusivamente como agregado associado;
- dez consultas NetworkX e equivalentes Cypher revisadas;
- GraphML completo, export Neo4j amostrado e manifest revisados;
- seis figuras revisadas quanto a t?tulos, legibilidade, agrega??o e aus?ncia de IDs;
- reconcilia??o, hashes, escopo e diff staged inclu?dos no gate final.

## Erros e corre??es da Fase 6

- **E048 ? NetworkX ausente:** verifica??o local falhou; NetworkX 3.6.1 foi instalado somente em `solution/.venv`, sem alterar o ambiente global.
- **E049 ? chave duplicada de padr?o pr?-churn:** janelas diferentes compartilhavam identidade l?gica; `pattern_type` passou a incorporar janela e comprimento, preservando o contexto exigido.
- **E050 ? falso positivo do gate financeiro:** o schema documentava `revenue_lost` como propriedade proibida e o scanner interpretava a lista preventiva como exposi??o; a valida??o passou a procurar chaves publicadas, mantendo a proibi??o.
- **E051 ? consulta de MRR sem filtro terminal:** GQ05 usava o ranking global de MRR; a consulta passou a restringir explicitamente caminhos terminando em CHURN e com pelo menos dez contas.
- **E052 ? cobertura sem?ntica em n?s:** o primeiro validador inspecionava texto apenas de arestas; o gate foi ampliado para propriedades textuais de n?s.

## D075 ? Watchlist como fila de investiga??o humana

- **Decis?o:** cada item exige revis?o humana e n?o autoriza a??o operacional.
- **Status:** APROVADA

## D076 ? Regras determin?sticas versionadas

- **Decis?o:** configurar 16 regras audit?veis em JSON, sem texto livre ou l?gica secreta.
- **Status:** APROVADA

## D077 ? Separa??o dos componentes

- **Decis?o:** preservar evid?ncia, urg?ncia, materialidade e confian?a como dimens?es discretas independentes.
- **Status:** APROVADA

## D078 ? Prioridade discreta sem score preditivo

- **Decis?o:** usar matriz expl?cita P1?P4; proibir m?dia ponderada e probabilidade.
- **Status:** APROVADA

## D079 ? Data quality gate antes de sinal comportamental

- **Decis?o:** quarentena ? quality-only e confian?a LOW bloqueia P1 comportamental.
- **Status:** APROVADA

## D080 ? Evid?ncia estruturada e provenance

- **Decis?o:** cada item registra fontes controladas, m?tricas, popula??o, denominadores, cutoff, janela e estabilidade.
- **Status:** APROVADA

## D081 ? Explica??es por template

- **Decis?o:** gerar linguagem determin?stica, descritiva e n?o causal, sem LLM.
- **Status:** APROVADA

## D082 ? MRR associado e deduplicado

- **Decis?o:** usar MRR somente como materialidade contextual e deduplicar por conta nos agregados.
- **Status:** APROVADA

## D083 ? Integra??o somente com grafo promov?vel

- **Decis?o:** usar somente ROBUST/SENSITIVE, n?o-HIGH, n?o-small e `is_promotable=true`.
- **Status:** APROVADA

## D084 ? Proibi??o de interven??o autom?tica

- **Decis?o:** n?o produzir contato, desconto, mudan?a de plano, cancelamento ou a??o outbound.
- **Status:** APROVADA

## D085 ? Gate da watchlist

- **Decis?o:** `PASS_WITH_WARNINGS`.
- **Justificativa:** outputs reconciliados e explic?veis; W011 ? ampla por overlap sist?mico, W015 exige revis?o por cobrir mais de 40%, warnings e amostra reduzida de reativa??o limitam confian?a.
- **Status:** APROVADA COM RESSALVAS

## Erros e corre??es da Fase 7

- **E053 ? janela nula em regra de qualidade:** template tentou converter aus?ncia de janela em inteiro; passou a registrar zero como janela n?o temporal.
- **E054 ? schema consolidado inicial:** nomes internos foram alinhados ao contrato (`active_queue_count`, `rule_ids`, extremos de componentes e revis?o humana).
- **E055 ? volume amplo:** W011 foi preservada exclusivamente como exce??o DATA_QUALITY_REVIEW; W015 recebeu `BROAD_RULE_REVIEW_REQUIRED`, sem promo??o silenciosa.
- **E056 ? tmp_path bloqueado pelo sandbox:** quatro setups da su?te hist?rica n?o acessaram o tempor?rio padr?o do Windows; a mesma su?te foi repetida fora do sandbox com `--basetemp` isolado em `C:\tmp` e encerrou com 111 testes aprovados.
- **E057 ? inspe??o visual no Windows:** o visualizador local n?o atravessou o wrapper de sandbox; um montage derivado fora do reposit?rio permitiu revisar t?tulos, legibilidade, agrega??o, paleta e aus?ncia de IDs nas seis figuras.

## Decis?es da Fase 8

## D086 ? Laborat?rio de desenho, n?o execu??o

- **Decis?o:** limitar a fase a especifica??es e valida??o de viabilidade.
- **Status:** APROVADA

## D087 ? Separa??o entre observa??o, hip?tese e efeito

- **Decis?o:** hist?ricos sustentam hip?teses, nunca resultados ou causalidade.
- **Status:** APROVADA

## D088 ? Cat?logo governado de interven??es

- **Decis?o:** versionar dez op??es com riscos, aprova??es e usos proibidos.
- **Status:** APROVADA

## D089 ? Unidade de randomiza??o expl?cita

- **Decis?o:** bloquear desenhos quando a unidade operacional necess?ria n?o existe.
- **Status:** APROVADA

## D090 ? Uma m?trica prim?ria

- **Decis?o:** cada hip?tese possui exatamente uma m?trica prim?ria e m?tricas secund?rias separadas.
- **Status:** APROVADA

## D091 ? Power e MDE antes de promo??o

- **Decis?o:** classificar viabilidade antes de qualquer execu??o futura.
- **Status:** APROVADA

## D092 ? Assignment somente simulado

- **Decis?o:** usar seed fixa e bra?os explicitamente simulados, sem exposi??o real.
- **Status:** APROVADA

## D093 ? ITT como estimando principal

- **Decis?o:** especificar intention-to-treat como an?lise prim?ria futura.
- **Status:** APROVADA

## D094 ? Guardrails e stopping rules

- **Decis?o:** especificar crit?rios de prote??o antes de observar resultados.
- **Status:** APROVADA

## D095 ? Gate ?tico obrigat?rio

- **Decis?o:** exigir revis?o humana, consentimento aplic?vel, fairness e MRR neutro.
- **Status:** APROVADA

## D096 ? Subdimensionamento n?o ? promo??o

- **Decis?o:** classificar amostra insuficiente como `UNDERPOWERED` ou `PILOT_ONLY`.
- **Status:** APROVADA

## D097 ? Gate do Experiment Lab

- **Decis?o:** `PASS_WITH_WARNINGS`.
- **Justificativa:** artefatos s?o reproduz?veis e governados, mas h? desenhos n?o vi?veis, piloto e subdimensionados; nenhum experimento foi executado.
- **Status:** APROVADA COM RESSALVAS

## Erros e corre??es da Fase 8

- **E058 ? statsmodels ausente:** adotadas f?rmulas audit?veis com SciPy, sem instala??o.
- **E059 ? lista em especifica??o:** normalizador passou a preservar se??es em lista.
- **E060 ? amostra sem baseline:** popula??o eleg?vel zero agora produz amostra requerida zero e `NOT_FEASIBLE`.
- **E061 ? tmp_path bloqueado pelo sandbox:** quatro fixtures hist?ricas falharam por permiss?o; a su?te foi repetida fora do sandbox com diret?rio tempor?rio isolado e passou integralmente.
- **E062 ? visualizador local bloqueado no Windows:** as seis figuras foram reunidas em montage tempor?rio fora do reposit?rio e revisadas sem alterar os artefatos finais.
## Decisoes da Fase 9

## D098 - Dashboard como narrativa de produto

- **Decisao:** organizar a experiencia como fluxo auditado de dados fragmentados ate desenho experimental, com resposta executiva antes do detalhe tecnico.
- **Status:** APROVADA

## D099 - Dados locais derivados para demo

- **Decisao:** gerar 15 snapshots JSON deterministicos a partir de inputs congelados e verificados por SHA-256.
- **Status:** APROVADA

## D100 - Separacao visual entre qualidade e comportamento

- **Decisao:** manter quarentena e regras de qualidade fora da interpretacao comportamental e das filas de acao.
- **Status:** APROVADA

## D101 - Grafo reduzido e promovivel

- **Decisao:** limitar modos a 35 nos/80 arestas, excluir UNSTABLE, HIGH dependency e small sample, e mostrar apenas 16 relacoes no event-flow inicial.
- **Status:** APROVADA

## D102 - Explicacao deterministica na interface

- **Decisao:** derivar `Explain this` somente de evidencia local estruturada, sem LLM ou geracao livre.
- **Status:** APROVADA

## D103 - Guided Demo como fluxo principal

- **Decisao:** disponibilizar oito etapas in-product e roteiro de 3:10 como caminho padrao de avaliacao.
- **Status:** APROVADA

## D104 - Experiment Lab sem resultados

- **Decisao:** apresentar elegibilidade, power, metricas, SAP e governanca mantendo os oito experimentos como `UNTESTED`.
- **Status:** APROVADA

## D105 - Interface em ingles

- **Decisao:** usar ingles na aplicacao e no material operacional da demo para ampliar compreensao de avaliadores e compradores enterprise.
- **Status:** APROVADA

## D106 - Modo demo sem servicos externos

- **Decisao:** prerenderizar rotas com JSONs locais, sem backend, banco, API, credenciais ou rede em runtime.
- **Status:** APROVADA

## D107 - Protecao contra linguagem causal

- **Decisao:** validar termos proibidos no builder/testes e repetir limitacoes descritivas nas telas de grafo, watchlist e experimentos.
- **Status:** APROVADA

## D108 - Gate do dashboard

- **Decisao:** `PASS`.
- **Justificativa:** build estatico, lint, typecheck, 18 testes UI, 36 smokes responsivos, 130 testes Python, 15 JSONs idempotentes e sete screenshots reais revisadas passaram; privacidade, causalidade e escopo reconciliaram em zero violacoes.
- **Status:** APROVADA
