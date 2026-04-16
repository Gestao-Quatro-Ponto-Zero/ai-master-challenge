AI Master Challenge — Lead Scorer | Log de Decisões e Processo

Tempo Médio de Criação: ~5 horas (Desenvolvimento, Debug de Ambiente e Refatoração).

Este documento detalha o processo de desenvolvimento do RavenStack CRM, registrando a interação estratégica entre o AI Master (Bruno Duarte) e a IA Generativa para a construção de uma solução robusta e auditável.
🛠 1. Ferramentas e Papéis

    AI Master (Bruno Duarte): Definição de requisitos de negócio, arquitetura de software, supervisão técnica, gestão de ambiente virtual (venv), governança de dados e controle de consistência de interface.

    IA (Gemini 3 Flash): Co-piloto de codificação, geração de protótipos e suporte em lógica matemática.

🏗 2. Decomposição do Problema

O desenvolvimento foi estruturado em quatro sprints principais:

    Engenharia de Dados: Integração de 4 tabelas CSV, tratamento de nulos e normalização de strings.

    Motor de Scoring: Evolução da lógica de priorização de leads.

    Interface SaaS: Desenvolvimento de dashboard multicamadas com filtros waterfall e paginação para performance.

    Laudo de Saúde: Criação de uma página de auditoria com mapeamento de impacto estratégico.

🔄 3. Histórico de Iterações e Decisões Críticas
🔴 Iteração 1: O Bug de Tipagem (Float vs String)

    Contexto: Erro de tipagem ao categorizar o porte dos clientes.

    Decisão do AI Master: Rejeição da solução simplista da IA. Implementação de conversão forçada e tratamento de NaNs via pd.cut com labels específicos para garantir a integridade dos filtros.

🔴 Iteração 2: Blindagem de Deploy (Path Dinâmico)

    Contexto: O app falhava no Streamlit Cloud por não localizar a pasta /data.

    Decisão do AI Master: Implementação da biblioteca os para criar caminhos absolutos dinâmicos (os.path.abspath(__file__)). Isso tornou o app portátil entre ambiente local e nuvem.

🔴 Iteração 3: Otimização de Performance (Paginação)

    Contexto: Dataset com ~8.800 registros causava lentidão no navegador.

    Decisão: Implementação de lógica de slicing e paginação dinâmica (math.ceil) para garantir fluidez na UX.

📊 4. Evolução do Scoring (Feedback G4)

Atendendo ao critério de fundamentação em dados históricos, o motor de inteligência passou por uma migração crítica:

    Como era antes (Heurístico): Baseado em pesos manuais e percepções de negócio (Ex: Fase Reunião = +X pontos). Uma lógica de "regra de bolso".

    Como ficou agora (Data-Driven): O scoring agora é fundamentado no dataset:

        Win-Rate Histórico: O algoritmo calcula a probabilidade real de fechamento por produto (WinRate=TotalWon​). Produtos com maior histórico de conversão elevam o score do lead automaticamente.

        Lógica de Aging: Implementação de penalidade por estagnação. Leads sem interação há mais de 45 dias sofrem decaimento de score, refletindo a perda de tração observada nos dados históricos.

⚠️ 5. Desafios de Governança e Consistência

A maior dificuldade deste projeto foi manter a consistência do código e da interface. Por ser uma IA aberta, o modelo apresentou falhas frequentes de reconhecimento de contexto:

    Limitação de RAG/Memória: Em diversas iterações, a IA não reconheceu corretamente as diretrizes de design e skills previamente validadas, tentando alterar layouts de páginas consolidadas (como a Auditoria de Dados).

    Rigor no Design: Houve uma necessidade constante de intervenção humana ("Human-in-the-loop") para impedir que a IA inserisse textos genéricos ou ruídos visuais (pontos, termos como "dado técnico em falta") em seções que já possuíam um mapeamento estratégico definido.

    Manutenção da Integridade: A consistência final foi garantida pela supervisão do AI Master, que bloqueou alterações desnecessárias em páginas já aprovadas enquanto focava exclusivamente na evolução da lógica do motor de score.

🔍 6. Auditoria e Solo Sagrado

    Página de Auditoria: Preservada com o Mapa de Impacto Real, traduzindo falhas de dados em riscos de negócio (ex: falta de revenue impede o tiering de contas).

    Painel de Ações: Mantido com a estrutura de 4 colunas de filtros e botões de reset via session_state.

Bruno Duarte
AI Master | Data Analyst | Software Engineering Student