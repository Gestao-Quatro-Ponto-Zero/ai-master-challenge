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
