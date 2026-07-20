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
