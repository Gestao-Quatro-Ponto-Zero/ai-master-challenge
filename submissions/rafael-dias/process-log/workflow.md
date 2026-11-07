# Process log — Challenge 003

## Preparação da submissão — 06/11/2026

- Após avaliação crítica de 8,4/10, o usuário decidiu encerrar a expansão funcional e autorizou organizar a entrega. Conferidos novamente template oficial, guia de submissão e regras do Pull Request.
- Escolhido formato principal de evidência: narrativa escrita já existente, complementada por capturas de evolução e QA. Não foram inventados export de conversa, horas, métricas ou histórico Git anterior.
- Preparado pacote independente em submissions/rafael-dias, com código/dados públicos em solution, README do candidato, roteiro do avaliador e instruções de envio. Rafael forneceu o LinkedIn para identificação.
- Gerador usa lista explícita, exclui segredos, dependências, builds, backups e registros privados do navegador. Manifesto SHA-256 permite conferir integridade do código copiado. Arquivos originais de trabalho permanecem no lugar.
- A instalação e verificações do pacote serão registradas em docs/validacao-da-entrega.md dentro da submissão, distinguindo execução atual de evidências anteriores. Nenhum fork, PR ou deploy é criado nesta etapa local.
- A instalação independente exigiu download das dependências: o cache offline estava incompleto. O primeiro build detectou o lockfile da pasta-pai; adicionada configuração explícita de raiz e rastreamento do Next.js para manter a solução independente do workspace de desenvolvimento, conforme documentação oficial.

## 06/11/2026 — Contexto e decisões com o usuário

- Ferramenta de IA: Codex, para recuperar o briefing da conversa anterior, inspecionar fontes, analisar CSVs, escrever código e verificar comportamento.
- O usuário pediu análise antes da construção e proibiu mudanças em repositórios sem alinhamento. A análise inicial foi somente leitura, com download temporário.
- O README oficial e o guia foram consultados. A entrega exige software funcional, explicações, setup, limitações e evidências de processo.
- Na análise, identificamos 2.089 oportunidades abertas, 1.425 sem conta e divergência `GTXPro`/`GTX Pro`. Não assumimos que as 8.800 oportunidades eram semanais ou mensais.
- Calculamos tempo entre início de negociação e encerramento: média geral 47,99 dias, ganhos 51,78 e perdidos 41,48. Esclarecemos que isso não inclui prospecção nem negócios ainda abertos.
- O usuário propôs Supabase, Vercel, Codex e Obsidian. Discutimos a relação com os critérios. Ele decidiu retirar Obsidian e manter documentação no projeto.
- O usuário autorizou criar tudo do zero e depois explicitamente iniciar a construção nesta pasta.

## Construção da primeira versão

- Decidimos implementar regras explicáveis, evitando apresentar heurística como probabilidade.
- Não atribuímos pontos por porte, setor ou vendedor sem evidência de utilidade. A conta ausente gera tarefa sem penalização de perfil.
- O tempo não é chamado de inatividade: faltam dados de contato. Negociações longas entram em revisão, sem afirmar perda.
- Foram criados Next.js, filas com filtros, busca, exportação CSV, explicação por componente, modo local reproduzível e integração Supabase no servidor com RLS.
- O banco usa snapshot enriquecido para manter a primeira entrega pequena; isso é uma decisão de escopo, não uma integração CRM completa.
- A consulta de pacotes e o download público exigiram acesso de rede fora do ambiente restrito. Não houve provisionamento de conta externa.

## Evidências e honestidade

- Testes e build serão registrados conforme executados. Não são inventados prompts, correções, medições comerciais ou resultados de uso.
- Contribuição humana: escolha da arquitetura, retirada de ferramenta desnecessária, perguntas sobre período e ciclo de vendas e autorização gradual do escopo.
- Pendente: avaliar utilidade com usuários comerciais, criar contas/projetos Supabase e Vercel e publicar com o proprietário.
- Esta narrativa pode acompanhar a exportação da conversa como evidência adicional; não substitui evidências de testes ou de funcionamento publicados.

## Iteração 2 — de relatório para rotina comercial

- Feedback humano: a primeira versão parecia um relatório em um app. O usuário pediu uma ferramenta que conduzisse ações, com energia visual, contexto, explicação, próximos passos e resultado de funil individual/empresa. Esse feedback mudou a estrutura do produto, não apenas as cores.
- Pesquisa no Behance encontrou Track x CRM e Smart CRM. As páginas completas bloquearam acesso (403); usamos descrições públicas sem afirmar inspeção visual completa. Fontes e limites em `docs/design-research.md`.
- A paleta foi verificada no HTML do site oficial atual do G4: azul escuro, dourado e off-white.
- Corrigimos a interpretação da média: 251 inclui histórico; aproximadamente 60 oportunidades abertas por vendedor. A distribuição individual é mostrada por carteira.
- Criamos Meu dia com top 5, carteira selecionada, agenda, tarefas vencidas, perfil, registro de ações, evidências de SQL, proposta e encerramento, além de pipeline e resultados.
- Não inventamos contatos ou SQLs históricos. Informações ausentes precisam ser cadastradas, e a confirmação de SQL exige evidências.
- Atividades usam persistência local explícita; sincronização multiusuário ainda depende de integração e autenticação. O modo Supabase existente continua como leitura do snapshot.
- Um erro de aplicação de patch (substituição de arquivo com operações incompatíveis no mesmo patch) foi corrigido separando a remoção e a adição; nenhum resultado comercial foi afetado.
- Revisão de código detectou risco de comparar datas em fusos diferentes; corrigimos para comparação numérica e normalização em UTC. Teste cobre essa fronteira.
- 12 testes automatizados passaram: cinco originais e sete para fluxo, isolamento, agenda, validação e reconciliação histórica. A compilação inicial do redesenho passou. Verificação final será registrada após o fechamento das alterações.
- Verificação final de código: os 12 testes passaram novamente e o build de produção foi concluído após as alterações. Encontramos 27 vendedores com oportunidades abertas; o seletor inclui os 35 cadastrados, inclusive carteiras vazias.
- A porta 3000 já estava ocupada. Iniciamos uma instância da nova versão na porta 3002 para verificar sem interromper a sessão existente.
- A instância isolada de 3002 não ficou acessível pelo navegador do host. Iniciamos a versão na porta 3003 com acesso local adequado: HTTP 200, HTML contém a nova tela e o botão “Trabalhar oportunidade”.
- Verificação no navegador: cadastro com nome explicitamente fictício e `qa@example.com`, contato com retorno, recarga da página preservando histórico/agenda, confirmação de SQL com três evidências de teste e fechamento simulado de USD 100. Resultados pessoais e da empresa atualizaram corretamente, mantendo os totais de 2017 separados. Esses registros são exclusivos do navegador usado para QA, rotulados como teste, não vendas reais.
- A inspeção encontrou dois ajustes de leitura: oportunidades distintas da mesma conta precisavam de ID visível, e no celular o foco comercial precisava vir antes dos indicadores. Ambos foram corrigidos.
- Layout inspecionado em desktop de 1440 px e celular de 390 px; sem transbordamento horizontal na página inicial. Código formatado com Prettier e auditoria de instalação sem vulnerabilidades reportadas.
- A inspeção de carteira vazia identificou uma frase inadequada (“próximas cinco” quando não havia oportunidades); substituída por orientação contextual. Compilação final passou após essa correção de texto.

## Iteração 3 — orientação comercial, marca e plano do dia

- Feedback do usuário: manter a abertura, aprofundar a ação e a sequência de próximos passos, usar logo original, rever nome, simplificar ajuda, retirar referências da interface e substituir a frase lateral genérica por progresso de tarefas.
- Pesquisa pública nos produtos do G4: [G4 Skills](https://g4business.com/g4-skills) descreve trilhas personalizadas, acompanhamento individual e painéis de progresso; [G4 OS](https://g4business.com/blog/g4-os-plataforma-ia-negocios) descreve assistência proativa. Não acessamos telas internas, contas privadas ou funcionalidades autenticadas. O plano diário é nossa interpretação para esta solução, não cópia certificada do app.
- Identificado e baixado o [SVG original branco do G4](https://g4business.com/wp-content/uploads/2026/01/logo-g4-completa-branca.svg), encontrado no HTML oficial, sem redesenhar ou alterar seus paths.
- O usuário rejeitou Impulso, Radar e Foco como nomes isolados e pediu combinação de G4, inglês, tecnologia e radar/prioridade comercial. Proposta implementada: **G4 Deal Radar**, com o logo separado do nome do produto.
- Criada ajuda em linguagem simples, com exemplos e detalhes opcionais. Pesquisa/referências retiradas da interface, mantidas aqui e em `design-research.md`.
- O roteiro muda por ação: cadastro, contato, qualificação, proposta, retorno, venda, perda ou nota. Caminhos pela resposta do cliente preparam o registro; não inventam resposta nem executam contato. Após salvar, próximo passo e compromisso aparecem explicitamente.
- Mais contexto concreto: fundação, porte, setor, localização e histórico de negócios ganhos por conta até 31/12/2017, com última venda histórica. Esses agregados não alteram o score e não confirmam intenção atual. Lacunas de qualificação continuam explícitas.
- Criado plano diário por vendedor, persistido no mesmo armazenamento e compatível com os registros existentes. Até cinco tarefas, sem reposição que aumente a meta durante o dia; progresso por ação pertinente, sem contar nota/reagendamento como contato.
- 17 testes passaram, incluindo plano fixo, progresso, prioridade dos retornos, caminhos de ação e corte do histórico de conta. Build de produção aprovado.
- O usuário reviu a proposta de nome e pediu retornar a **Sales Priority**. Interface, título do navegador, exportação e README foram atualizados para **G4 Sales Priority**, preservando o logo original e os demais ajustes.
- Verificação no navegador: histórico concreto da conta exibido, cadastro fictício preservado, próximo passo após salvar e caminho de ausência de resposta preparando o formulário de retorno. Nenhuma mensagem foi enviada.

## Iteração 4 — leitura visual e conversa guiada

- O usuário pediu cor por função, prioridade alta verde, card mais curto, SPIN contextualizado, arraste no Kanban, funil visual, lateral mais larga/recolhível, modo escuro e seletor de vendedor pesquisável.
- Consultada a [fonte primária da metodologia SPIN](https://www.huthwaiteinternational.com/spin-methodology): situação, problema, implicação e valor da solução. Não verificamos se é a principal estratégia interna do G4; implementamos por solicitação do usuário.
- Perguntas usam fatos conhecidos e pedem confirmação. Implicação é condicionada a problema relatado; não inferimos urgência, perdas financeiras ou intenção a partir do cadastro.
- Card resumido: uma pergunta por vez; dados completos, passos adicionais, caminhos posteriores e formulário sob demanda. Requisitos de SQL e venda preservados.
- Faixas visuais documentadas: 80–100 verde, 60–79 âmbar, abaixo de 60 vermelho, com texto. Estágios e saúde têm indicação semântica distinta da identidade dourada do G4.
- Arraste nativo prepara registro para avanço/perda, sem promover estágio antes de salvar evidências. Retrocessos e reabertura não suportados; interface manual permanece como alternativa ao arraste.
- Criados menu com recolhimento, modo escuro persistente e escolha de vendedor com busca por nome/gestor/região. Lateral ampliada para acomodar plano diário.
- Funil ilustrativo colorido mantém contagens reais e informa que há caminhos que pulam etapas; não apresentamos largura como taxa de conversão.
- 20 testes passaram e build aprovado antes da verificação visual.
- Teste de navegador: busca por “Darcel” encontrou a carteira correta; modo escuro e recolhimento responderam; card exibiu uma pergunta SPIN por vez e formulário inicialmente fechado. Arraste real por mouse de “A trabalhar” para “Contato realizado” abriu o registro correspondente. Cancelar preservou contagens 194/0; salvar contato simulado atualizou para 193/1 e criou o compromisso. Dados de QA explicitamente rotulados, sem contato real.
- Revisão final de contraste ajustou textos secundários no modo escuro. Uma compilação encontrou bloqueio temporário de arquivo no Windows enquanto a instância estava aberta; após encerrar a instância de verificação, a compilação repetida passou sem alterar a lógica.
- Verificação final: modo escuro e menu recolhido persistiram após recarregar (menu com 87 px no desktop); menu expandido mostrou plano com largura ampliada. Score 85 exibiu classe verde e cor verde calculada. Busca de vendedor e funil funcionaram. Sem transbordamento horizontal na abertura a 1440 e 390 px. Capturas finais em `docs/screenshots/`.

## Iteração 5 — conteúdo visível e registro direto

- O usuário observou que esconder campos reduzia a exploração. Dados, passos, perguntas SPIN, caminhos posteriores e formulário passaram a ficar visíveis no card. O histórico mantém sua aba própria. Atalho destacado leva ao registro sem exigir percorrer tudo.
- Pesquisa aprofundada em materiais públicos do G4, documentada em `g4-commercial-research.md`: artigo sobre SPIN, características de vendedores, Academia de Vendedores e valores públicos. Não acessamos playbook interno nem afirmamos reproduzir scripts proprietários.
- Perguntas reescritas com linguagem de conversa e escuta; estatísticas históricas ficam como contexto do vendedor, não fala para o cliente. Implicações continuam condicionadas ao que o cliente confirmou. Mantidos os produtos do dataset, sem substituir por cursos G4.
- Soltar um card no Kanban abre apenas o formulário correspondente; foco no registro, mesmas validações e fechamento da janela depois de salvar. Cancelar não altera etapa.
- Botão de tema substituído por switch de sol/lua com nome acessível e estado anunciado. Revisadas cores de textos secundários, formulário, roteiro e próximos passos no tema escuro.
- 20 testes passaram após atualizar as perguntas e a distinção entre contexto histórico e fala sugerida. Compilação e verificação de navegador serão registradas conforme executadas.
- Compilação aprovada. Navegador confirmou campos e quatro perguntas visíveis, atalho para registro e contexto histórico separado da fala sugerida. Checagem dos estilos computados de textos do card no modo escuro não encontrou contraste abaixo de 4,5:1 nos elementos inspecionados; isso não equivale a uma auditoria integral de acessibilidade.
- Arraste real abriu apenas a janela de registro e focou o resultado. Cancelamento manteve 57/0 nas etapas; salvar teste explícito atualizou para 56/1, criou próximo compromisso e fechou a janela automaticamente. Sem comunicação externa.

## Iteração 6 — acabamento sem mudar a estrutura

- Usuário identificou contraste fraco no aviso de contas ausentes, números dos passos, contador do histórico e campo de busca; pediu retorno do SPIN por abas, explicação da distribuição original, FAQ em cartões e recolhimento simétrico/suave.
- Diagnóstico: números dos passos são pseudo-elementos que mantinham fundo claro com texto claro no tema escuro; badge do histórico tinha o mesmo conflito. Correção explícita de fundo e texto, além dos elementos já verificados anteriormente.
- Busca do pipeline passa a usar fundo transparente dentro do contêiner, com foco no contêiner. Aviso de contas ausentes recebe contraste próprio para texto, complemento e ação.
- SPIN voltou a uma pergunta por aba, preservando perguntas humanizadas e contexto; navegação por setas, Home e End também suportada. Outros campos e passos continuam visíveis.
- Conferida a base: 35 cadastrados, 27 com abertas, oito sem abertas, intervalo 31–194. Entre os oito, três têm somente encerradas e cinco não possuem oportunidades associadas. Explicação deixa claro que preservamos `sales_agent` original e que o dataset não explica as causas da distribuição.
- Botão de recolher com ícone vetorial e grupo centralizado, mesma largura do menu, transição de 210 ms e respeito a movimento reduzido. FAQ ganha cartões com bordas e estado aberto definido.
- Pesquisa adicional registrada em `design-research.md`; páginas completas do Behance bloquearam acesso, sem alegação de cópia ou validação visual dessas referências.
- 21 testes passaram, incluindo verificação da distribuição e preservação dos responsáveis. Verificação visual pendente nesta etapa.
- Build aprovado e conferência no navegador concluída. Contraste medido dos pseudo-elementos dos passos: 7,8:1; badge do histórico: 9,58:1. Botão de recolher com diferença zero de deslocamento/largura em relação à área do menu, transição de 210 ms e largura recolhida de 87 px. Busca focada com fundo interno transparente. SPIN respondeu à seta direita; FAQ em cartões abriu corretamente. Página de ajuda sem transbordamento horizontal a 390 px. Capturas em `docs/screenshots/`.


## Ajuste solicitado — rodadas secundárias e seleção de resultado

- Removido painel de lotes acima do dashboard e lista duplicada de clientes. Rodadas do dia aparece como quatro checkpoints após as oportunidades. Sem alterar dados ou apagar progresso anterior.
- Substituídos botões de resposta que mudavam roteiro e rolavam a tela por um seletor único de resultado, com linguagem de ação executada. Formulário permanece visível; escolha não altera o pipeline antes de salvar.
- Pesquisa temática Behance registrada em design-research.md com limitação 403 explícita; validação de usabilidade com vendedores continua pendente.

- Validação: 24 testes passaram e build de produção aprovado. No navegador, seleção de SQL revelou os campos corretos com o mesmo roteiro e sem alterar a rolagem (scrollTop 480,8 antes/depois). Progresso anterior 1/20 preservado. A 390 px a página não apresenta transbordamento horizontal. Capturas rodadas-compactas.png e registro-simplificado.png.


## Refatoração para continuidade — 06/11/2026

- Autorização explícita do usuário para organizar o código mantendo o comportamento aprovado. Cópia recuperável criada em `.backups/refactor-20261106-195217/`, com manifesto SHA-256; credenciais, dependências e cache de build excluídos. Armazenamento do navegador preservado pelas mesmas chaves/envelope, não copiado para arquivos.
- Dashboard passou de cerca de 2.100 linhas não vazias para cerca de 190, compondo telas. Meu dia, Kanban, Resultados, ajuda, menu/cabeçalho e componentes compartilhados foram separados. Card foi dividido em contexto do cliente, modal, formulário e SPIN.
- Separados hook de sessão comercial, controller de navegação e filtros, projeções puras e adaptador de armazenamento. JSDoc documenta contratos; não houve migração integral para TypeScript.
- CSS dividido em módulos ordenados com tokens de marca centralizados. Removidas 31 declarações superadas em seletores idênticos, preservando a cascata. A comparação de seis elementos principais confirmou mesmas dimensões, fonte, cor e fundo em desktop.
- A extração inicial revelou referências ausentes e uma delimitação incorreta de JSX nos checkpoints; foram corrigidas antes da compilação final e da conferência. Verificação de referências foi usada na reorganização; scripts temporários ficam somente na cópia local ignorada.
- A compilação restrita encontrou bloqueio de pasta gerada no Windows; nova execução com acesso adequado concluiu o build. Nenhuma regra de negócio foi alterada para resolver esse bloqueio.
- 32 testes aprovados (24 anteriores + oito de compatibilidade/armazenamento/filtros). No navegador, fluxo completo fictício de cadastro → contato → SQL → proposta → venda USD 100, além de nota, reagendamento e perda com motivo. Histórico/resultados persistiram após recarga; filtros por gestor separaram atividades corretamente. Arraste abriu o registro resumido e cancelar preservou a etapa. Testes adicionais usaram origem localhost distinta de 127.0.0.1, mantendo os registros anteriores dessa outra origem.
- Guia de continuidade e roteiro de verificação adicionados. README atualizado para refletir o seletor atual e a nova organização. Score, regras de qualificação, snapshot e rodadas foram preservados. Correção da precedência de retornos urgentes continua como mudança funcional separada.

- Fechamento: npm run check aprovado integralmente; verificação móvel e de tema/menu concluída. Hashes das regras de score, workflow, guia/plano e snapshot idênticos ao backup. Versão reorganizada disponibilizada novamente na porta 3003.


## Estudo de saúde e prioridade — proposta v2

- Pedido do usuário: pesquisar portais e fóruns para fundamentar um health score comercial efetivo. Consulta a documentação HubSpot, Gong, Salesforce, AWS e discussões públicas; achados, limitações e links em health-score-research.md. Relatos de fórum foram tratados como anedóticos, sem usar alegações promocionais como prova.
- Auditoria do snapshot: 2.089 abertas, 1.425 sem conta; 21 notas distintas, Engaging entre 62–95 e Prospecting entre 32–45. Identificada prioridade estrutural do estágio sobre toda a prospecção. Relatório com hash em health-score-audit.json.
- Proposta separa potencial, saúde e urgência, prevê sinais de participação do comprador, aceite do próximo passo, confiança, atualização temporal e proteção contra vazamento. Pesos são hipóteses para piloto, sem promessa de lift. Nenhum valor orçado inexistente foi fabricado ou valor fechado futuro usado como entrada.
- Entrega desta etapa é o estudo; aplicativo, scoring e persistência permanecem inalterados. Validação comparativa e implementação ficam para a sequência.


## Comparativos e cenários antes da implementação

- Conferidos README, pasta oficial do Challenge 003 e guia. A pasta consultada lista somente o briefing, sem pesos oficiais ou bateria executável de benchmarks; não auditamos todos os PRs/forks. API de árvore não ficou disponível na ferramenta web, então a listagem foi conferida na página pública do GitHub.
- Pesquisadas referências oficiais de teste de registros/distribuição (HubSpot), cenários de alto valor com baixa avaliação (Salesforce), riscos de negociação (Gong) e avaliação preditiva (Microsoft), além de discussão de auditoria na comunidade HubSpot. Cenários adaptados são nossos, não casos reais de clientes.
- Script de análise isolado compare-priority.mjs compara seis regras estáticas em pool comum de 664 abertas identificadas e 27 carteiras. Executado com top 5 (133 selecionadas) e top 20 (487). Garante IDs únicos e isolamento por vendedor; não usa fechamento futuro nem modifica prepared.json. Resultados completos e hash em priority-comparison-top5.json e priority-comparison-top20.json.
- Documento priority-validation-plan.md reúne resultados, limitações, 20 cenários e seis pares de decisões para orientar a implementação. Espaço de descoberta é política experimental de capacidade; composição de fila não é acurácia ou lift. Nenhuma nova regra foi ativada no app.


## Implementação de saúde e prioridade v2 — 06/11/2026

- Autorização explícita para aplicar o conceito pesquisado. Cópia de código/documentação em .backups/health-v2-20261106-203448/. Preservadas chaves e envelope do armazenamento.
- Novos módulos puros health.mjs, priority.mjs e evidence.mjs. Saúde versionada por evidência/cobertura; filas por urgência e avanço, sem confundir potencial com saúde. Não alteramos o score histórico de 2017.
- Formulários acrescentam resposta confirmada/tentativa/desconhecido, ocorrência, aceite, proposta total USD, condições e pausa solicitada. Saúde detalha pontos e lacunas; valores orçados não são inventados. Novos registros recebem schemaVersion 3, origem manual e versão da política.
- Eventos legados não ganham respostas inferidas; efeitos duplicados e posteriores ao corte são ignorados na projeção, preservando os eventos salvos. Notas não contam como participação.
- Retornos vencidos e avanços atuais entram no foco fora das rodadas. Bloqueio financeiro também pode pedir revisão interna, sem antecipar contato. Pausas e agendamentos são respeitados; reserva experimental de descoberta não foi ativada.
- Cenários C01–C20 e pares P1–P6 viraram testes. Testes antigos que esperavam saúde 20/100 ou 100/100 sem resposta estruturada foram atualizados para desconhecido, mantendo validações comerciais.
- Conferência inicial no navegador: SQL fictício com resposta e aceite gerou 90/100, cobertura 90%, verde; proposta fictícia USD 1.000 com bloqueio gerou risco mesmo com 90 pontos. Identificado problema de rolagem após salvar (histórico ficava acima da posição atual); corrigido para abrir o histórico no topo.
- Política ativa, limites e continuidade em docs/health-v2-implementation.md. Testes verificam coerência; impacto comercial continua sem medição. Publicação não realizada nesta etapa.

- Fechamento da etapa: 58 testes, formatação e build de produção aprovados. Pausa fictícia conferida na interface e persistida após recarga. Corrigido crédito retroativo de checkpoint com ocorrência antiga. Documentação ativa alinhada às regras, sem alegação de lift ou conversão comprovados.

- Verificação visual final do modo escuro e formulário móvel concluída, sem transbordamento horizontal a 390 px. A origem de QA preservou pausa/agenda após recarga. Captura health-v2-risk.png documenta cenário fictício; nenhum contato foi feito.
