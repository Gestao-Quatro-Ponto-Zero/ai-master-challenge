# Feature Specification: G4 Suporte Inteligente (MVP)

**Feature Branch**: `submission/pedro-henrique-silva`

**Created**: 2026-05-28

**Status**: Draft

**Input**: User description: "Construir um MVP funcional para o challenge AI Master com jornada de cliente (ticket via texto/áudio com tentativa de resolução por IA) e jornada de admin (dashboard com diagnóstico e gestão de tickets), seguindo SPEC-MVP." 

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolver no primeiro contato (Priority: P1)

Como cliente final, quero descrever meu problema por texto ou áudio e receber uma sugestão imediata com base em casos similares, para tentar resolver sem abrir ticket.

**Why this priority**: Esta é a proposta de valor principal do produto (deflexão de chamados), com impacto direto em custo operacional e experiência do cliente.

**Independent Test**: Pode ser testada isoladamente com um usuário cliente autenticado, envio de texto/áudio, retorno de sugestão e decisão "Resolveu" ou "Ainda preciso de ajuda".

**Acceptance Scenarios**:

1. **Given** cliente autenticado na tela de novo chamado, **When** envia texto de problema, **Then** o sistema retorna sugestão com nível de confiança e referências similares.
2. **Given** cliente autenticado na tela de novo chamado, **When** grava áudio e confirma envio, **Then** o sistema exibe a transcrição para revisão antes da busca de solução.
3. **Given** que a sugestão foi útil, **When** o cliente clica em "Resolveu meu problema", **Then** o sistema registra evento de deflexão e não cria ticket.
4. **Given** que a sugestão não foi suficiente, **When** o cliente clica em "Ainda preciso de ajuda", **Then** o sistema cria ticket aberto com classificação inicial.

---

### User Story 2 - Diagnóstico executivo em minutos (Priority: P2)

Como admin (Diretor de Operações), quero um dashboard que mostre gargalos, drivers de satisfação, desperdício e oportunidades de automação, para tomar decisão acionável em poucos minutos.

**Why this priority**: É o principal valor para liderança operacional e prova de maturidade analítica da solução.

**Independent Test**: Pode ser testada isoladamente com um usuário admin autenticado acessando `/admin` e visualizando os quatro blocos alimentados por dataset previamente processado.

**Acceptance Scenarios**:

1. **Given** admin autenticado, **When** acessa dashboard, **Then** visualiza blocos de gargalo por combinação operacional e ranking de piores segmentos.
2. **Given** admin autenticado, **When** acessa dashboard, **Then** visualiza variáveis mais associadas à satisfação e tendências de impacto.
3. **Given** admin autenticado, **When** acessa dashboard, **Then** visualiza estimativa de horas e custo recuperáveis.
4. **Given** admin autenticado, **When** acessa dashboard, **Then** visualiza padrões repetitivos com potencial de automação prioritária.

---

### User Story 3 - Operação assistida por IA (Priority: P3)

Como admin e cliente, quero acompanhar e gerenciar tickets com contexto de IA, para garantir continuidade do atendimento quando não houver deflexão.

**Why this priority**: Complementa a jornada ponta a ponta e sustenta operação humana quando automação não resolve totalmente.

**Independent Test**: Pode ser testada isoladamente com tickets já criados, validando listagem, filtros, histórico e ações básicas de operação.

**Acceptance Scenarios**:

1. **Given** cliente autenticado, **When** acessa seus tickets, **Then** vê apenas seus chamados e seus status atualizados.
2. **Given** admin autenticado, **When** acessa gestão de tickets, **Then** consegue filtrar por status, prioridade e categoria.
3. **Given** admin autenticado em um ticket, **When** atualiza prioridade ou status, **Then** a mudança é persistida e refletida na listagem.

---

### Edge Cases

- O que acontece quando o áudio enviado está vazio, corrompido ou acima do limite permitido?
- Como o sistema se comporta quando a busca por casos similares retorna baixa confiança?
- Como impedir criação duplicada de ticket em múltiplos cliques rápidos do usuário?
- Como tratar indisponibilidade temporária de serviço externo durante transcrição ou sugestão?
- Como garantir que cliente não acesse tickets de outro usuário e que admin tenha visão ampliada sem violar segurança?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir autenticação por credenciais para usuários com perfis `admin` e `customer`.
- **FR-002**: O sistema MUST restringir rotas administrativas apenas para usuários com papel `admin`.
- **FR-003**: O sistema MUST permitir abertura de solicitação por texto digitado.
- **FR-004**: O sistema MUST permitir abertura de solicitação por áudio gravado no navegador.
- **FR-005**: O sistema MUST converter áudio em texto para revisão do cliente antes de prosseguir.
- **FR-006**: O sistema MUST buscar casos similares em base histórica para gerar sugestão inicial.
- **FR-007**: O sistema MUST apresentar sugestão com confiança e fontes utilizadas.
- **FR-008**: O sistema MUST permitir que o cliente finalize a jornada sem criar ticket quando a sugestão resolver o problema.
- **FR-009**: O sistema MUST registrar evento de deflexão quando o cliente indicar resolução sem ticket.
- **FR-010**: O sistema MUST criar ticket quando o cliente indicar necessidade de ajuda adicional.
- **FR-011**: O sistema MUST classificar automaticamente categoria e prioridade inicial do ticket criado.
- **FR-012**: O sistema MUST persistir histórico e metadados de cada ticket criado.
- **FR-013**: O sistema MUST permitir ao cliente listar e filtrar seus próprios tickets.
- **FR-014**: O sistema MUST permitir ao admin listar e filtrar todos os tickets.
- **FR-015**: O sistema MUST permitir ao admin atualizar status e prioridade dos tickets.
- **FR-016**: O sistema MUST exibir dashboard com quatro blocos analíticos baseados em dados pré-processados.
- **FR-017**: O sistema MUST exibir métricas de deflexão, confiança média e principais perguntas resolvidas sem ticket.
- **FR-018**: O sistema MUST manter trilha de eventos operacionais relevantes para análise de ROI e operação.
- **FR-019**: O sistema MUST tratar falhas de serviços externos com resposta de erro amigável e alternativa de continuidade.
- **FR-020**: O sistema MUST garantir segregação de dados por perfil de acesso.

### Key Entities *(include if feature involves data)*

- **Profile**: Representa o usuário autenticado, com papel de acesso, identidade e metadados básicos.
- **Knowledge Base Entry**: Representa item histórico com descrição, resolução e vetores para busca semântica.
- **Ticket**: Representa solicitação ativa ou encerrada do cliente, com origem, texto final, classificação e status.
- **Deflection Event**: Representa evento em que o problema foi resolvido antes da criação de ticket.
- **Insight Snapshot**: Representa conjunto de métricas agregadas e blocos analíticos disponibilizados no dashboard.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuário cliente consegue concluir o fluxo completo de novo chamado (texto ou áudio) sem suporte manual em até 2 minutos em cenário padrão.
- **SC-002**: Transcrição de áudio de até 30 segundos é concluída em até 8 segundos em pelo menos 90% das tentativas em ambiente de demonstração.
- **SC-003**: Sugestão inicial baseada em casos similares é retornada em até 4 segundos em pelo menos 90% das tentativas em ambiente de demonstração.
- **SC-004**: Pelo menos 1 evento de deflexão é registrado e exibido no dashboard durante validação do MVP.
- **SC-005**: Dashboard administrativo exibe os 4 blocos analíticos com dados reais processados previamente.
- **SC-006**: Tickets criados por clientes ficam visíveis para admin e rastreáveis por status, categoria e prioridade.
- **SC-007**: 100% dos acessos indevidos entre usuários customer são bloqueados nas consultas de tickets.

## Assumptions

- O MVP será executado com foco em demonstração funcional e não em escala de produção corporativa.
- Os datasets históricos estarão disponíveis e serão processados antes da validação do dashboard.
- O sistema operará em português (PT-BR) no escopo inicial.
- Os custos e premissas de desperdício usarão valor-hora padrão configurável (ponto de partida: R$ 35/h).
- O fluxo de autenticação e autorização terá usuários de teste previamente provisionados.
- O sucesso da deflexão será medido pela confirmação explícita do cliente no fluxo de atendimento.
