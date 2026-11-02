# Revisão adversarial da arquitetura inicial

## Lista oficial para validação

**Este arquivo é a fonte de verdade dos sete achados desta revisão e das decisões
sobre seus ajustes.** Os IDs F01–F07 permanecem estáveis. Resumos no chat, no status
ou no plano devem referenciar esses IDs; não criam outra lista de ajustes.

Há **dois problemas reproduzidos** e **cinco riscos preventivos**. Um risco preventivo
é um cuidado a incorporar na etapa indicada, não uma falha já observada na aplicação.
As explicações e os critérios de aceite de cada ID estão nas seções abaixo.

| ID | Ponto a validar | Evidência | Ajuste proposto | Sua decisão | Execução do ajuste |
| --- | --- | --- | --- | --- | --- |
| F01 | Documentos podem discordar e os checks não perceberem | Problema reproduzido em cópia temporária | Definir autoridade por informação, detectar conflitos e revalidar evidências afetadas | Aprovado | Implementado e validado na fundação: mutação rejeitada e dependências alteradas invalidam recibos; [escopo, limites e evidências](foundation-controls.md) |
| F02 | A avaliação pode ser contaminada durante o desenvolvimento | Risco preventivo | Separar dados de desenvolvimento, validação e teste antes de ajustar a solução | Aprovado | Protocolo antecipado no plano; execução em D02/V00 |
| F03 | A automação pode não saber quando encaminhar ao humano | Risco preventivo | Definir saídas e falhas; registrar e filtrar possíveis anomalias altas e baixas | Aprovado com complemento | Requisitos incorporados; implementação em S01/I01/V01 |
| F04 | Uma sessão iniciada na raiz pode não descobrir as instruções | Problema reproduzido com busca por arquivos | Documentar a entrada pela submissão e o caminho explícito para suas instruções | Aprovado | Entrada explícita validada nesta nova sessão Codex; CLI verificada em diretório independente; [limites e procedimento](foundation-controls.md#resumption-check-f04) |
| F05 | Outra pessoa pode não conseguir reproduzir os resultados | Risco preventivo | Registrar versões dos dados, hashes, dependências e comandos de reprodução | Aprovado | Planejado para D01 e resultados futuros |
| F06 | Manter contexto e tarefas extras pode consumir esforço excessivo | Risco preventivo | Usar o process log para recrutamento, fora do contexto operacional; manter retomada curta e extras limitados | Aprovado com complemento | Regra de leitura alterada; acompanhamento contínuo |
| F07 | Métricas e estimativas de economia podem induzir conclusões erradas | Risco preventivo | Explicitar população, cobertura, unidades e premissas; separar espera de trabalho ativo | Aprovado | Planejado para D01/A01 |

**Decisão humana em 02/11/2026:** o usuário concordou com F01–F07 e acrescentou os
requisitos de anomalias em F03 e de finalidade do process log em F06. `Aprovado`
registra essa decisão sobre a proposta; a coluna de execução informa o que foi
efetivamente feito e o que falta. Aprovação não é conclusão técnica nem revisão
humana de resultados ainda inexistentes. Alterações futuras usam os mesmos IDs.

**Sequência de trabalho:** F04/F01 antes da próxima etapa;
F05 na aquisição dos dados e F07 na auditoria/diagnóstico; F02/F03 antes do protótipo;
F06 durante toda a execução. Aprovação, implementação e validação serão registradas
separadamente nesta tabela e ligadas às evidências dos respectivos IDs.

O [plano de execução](../execution/plan.md) continua sendo a fonte do andamento
geral do desafio. O [process log](../process-log/README.md) guarda o histórico das
conversas e decisões. Para validar **esta revisão**, use a tabela acima.

## Escopo e parecer

Data: 02/11/2026. Escopo: base de contexto, execução, validação e evidências.
A aplicação e os datasets ainda não existem nesta entrega. As observações sobre
seu funcionamento são requisitos preventivos, não defeitos de código demonstrados.

**Parecer: manter a estrutura e reforçar seus controles antes de implementar.**
A divisão de responsabilidades é adequada. A fragilidade principal está em
depender de atualização manual e interpretação das IAs para manter a coerência.
Mais documentos ou infraestrutura não resolveriam isso por si só.

## Evidências e limites

O [snapshot da revisão](review-evidence/foundation-baseline.json) registra os
hashes dos 18 arquivos originais, comandos, saídas e uma mutação controlada.
O HEAD identifica a base do repositório; os hashes identificam a fundação que
estava no índice, ainda sem commit.

| Verificação executada | Resultado |
| --- | --- |
| Links locais dos documentos atuais, excluídos os chats históricos | 23 destinos existentes |
| Metadados mínimos dos dois conceitos e índice OKF | Válidos nos checks locais; sem certificação completa de conformidade |
| Escopo dos 18 arquivos previamente preparados no índice | Todos dentro da submissão |
| `git diff --cached --check` antes da revisão | Sem erros |
| Busca `rg --files -g AGENTS.md` na raiz | Código 1, nenhum resultado |
| Mesma busca com a submissão como diretório de trabalho | Código 0, encontra `AGENTS.md` |
| Alteração conflitante de desafio em cópia temporária | Checks estruturais continuam passando |

Não executei um benchmark de agentes, ataque contra um modelo, auditoria de dados
ou teste de aplicação. Os demais cenários abaixo foram examinados pela leitura
dos contratos existentes. A contagem de 23 links usa o extrator desta revisão;
o log histórico registrou 22 em sua execução anterior.

## Pontos positivos

- **Responsabilidades claras:** `AGENTS.md` define trabalho; `knowledge/` guarda
  conhecimento; `execution/` acompanha entregas; `process-log/` preserva evidências.
- **Decisões adiadas no momento certo:** stack e uso conjunto dos datasets
  dependem da auditoria. Isso evita construir em cima de uma conexão inexistente.
- **Boa disciplina analítica:** já há restrições sobre vazamento de resultados,
  transferência entre domínios e diferença entre tempo decorrido e esforço ativo.
- **Evidência honesta:** sugestões históricas, decisão humana, execução e
  validação são distinguidas; limites dos exports estão declarados.
- **Complexidade contida:** contexto em arquivos locais, sem runtime próprio,
  banco vetorial ou serviços obrigatórios; dashboard e galeria estão adiados.
- **Testes separados da qualidade da IA:** o plano reconhece que código correto
  não basta para provar classificação ou roteamento úteis.

O uso atual de OKF é compatível com sua função de representar conhecimento.
A especificação distingue metadados de confiança de controle de acesso e
explicita que o formato não executa cálculos por conta própria. A responsabilidade
pelos controles continua no consumidor e no workflow.
[Fonte primária: OKF v0.2, §§5.3 e 10](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

## Achados e ajustes necessários

P1 significa resolver antes da etapa que depende do controle; P2 significa
melhoria de confiabilidade ou de escopo. Não foi demonstrada falha crítica de
uma aplicação em execução.

### F01 — P1: coerência entre documentos não é verificada

**Como tentei quebrar:** em uma cópia temporária, alterei apenas o desafio em
`PROJECT_STATUS.md` para 004, mantendo 002 em `AGENTS.md` e no contexto. Os checks
de links, frontmatter, fontes locais e ausência de `verified` passaram antes e
depois. Isso comprova uma lacuna dos checks; não prova qual decisão uma IA tomaria.

**Por que importa:** os mesmos fatos aparecem no status, plano, README e
conhecimento. Uma edição parcial pode produzir uma retomada baseada no estado
errado. A [rotina de atualização](../knowledge/knowledge-workflow.md) pede atualizar
os arquivos, mas não define uma autoridade por campo nem como invalidar evidências.

**Ajuste mínimo:** definir um dono para cada informação: regras em `AGENTS.md`,
andamento no plano, decisões duráveis em um registro curto de decisões e status
como resumo com links. Registrar o que uma decisão substitui. Diante de conflito,
resolver pela decisão explícita mais recente do usuário e pelas regras aplicáveis;
sem evidência suficiente, explicitar a pendência. Não escolher silenciosamente.

**Aceite:** a mutação de desafio gera diagnóstico de inconsistência; uma mudança
em dado, regra ou modelo marca suas evidências dependentes para nova validação.
Um `verified` antigo precisa ser interpretado em relação à versão que foi revisada.

### F02 — P1: o protocolo de avaliação precisa preceder a implementação

**Cenário:** ajustar prompts, features e limiar de encaminhamento olhando o mesmo
conjunto reservado para avaliação. O resultado melhora sem demonstrar generalização.
O [plano](../execution/plan.md) lista V01 após I01. A
[estratégia](validation-strategy.md) já prevê holdout e duplicatas, mas não define
quando o conjunto é reservado nem onde escolher os limiares.

**Ajuste mínimo:** em D02/S01, registrar baseline, entradas disponíveis na chegada
do ticket, unidade de separação e conjuntos de desenvolvimento, validação e teste.
Agrupar duplicatas e variantes conforme a auditoria; ajustar limiares na validação;
usar o teste para a avaliação final da versão escolhida. Se o teste orientar uma
nova escolha, declarar esse reuso e a limitação. Medir transferência de domínio
separadamente. Definir metas após a auditoria e antes de escolher a solução vencedora.

**Aceite:** resultados identificam split, dados, modelo/prompt e configuração;
há baseline comparável, suporte por classe e análise dos erros relevantes. Sem
rótulos adequados, a alegação é uma demonstração ou avaliação exploratória,
com essa limitação explícita.

### F03 — P1: encaminhamento humano ainda é intenção, não contrato operacional

**Cenário:** ticket fora da taxonomia recebe score alto, dependência fica
indisponível ou resposta do modelo vem malformada. O que o sistema faz?
[S01](../execution/plan.md) prevê exceções humanas, mas deixa sua representação
e comportamento pendentes. Isso é aceitável nesta fase; deve ser resolvido antes
de I01. A regra de tratar texto como dado em `AGENTS.md` também precisa virar
comportamento verificável no protótipo, caso use um LLM.

**Ajuste mínimo:** definir uma saída pequena com categoria, ação sugerida, motivo,
versão e estado como sugestão, revisão necessária ou falha. Especificar o destino
humano em entrada vazia, desconhecida, falha de parsing e timeout. Se houver LLM,
validar a saída contra o contrato e testar instruções maliciosas dentro do ticket.
Se houver ações externas, separá-las da decisão do modelo e limitar as permitidas.

**Aceite:** casos normais e exceções percorrem o fluxo completo; baixa confiança,
erro técnico e caso fora do escopo têm comportamento definido. Medir erro nos
casos automatizados junto da cobertura e do volume enviado à fila humana.

**Complemento aprovado pelo usuário — anomalias registradas e filtráveis:**
um caso muito acima ou abaixo do padrão pode ser marcado como possível anomalia.
Comparar o mesmo indicador, escala, versão e grupo de tickets comparáveis; registrar
a regra e a referência utilizadas. Os valores 4 e 10 citados na conversa são
ilustrativos, não limites definidos. Um score alto pode ser perfeitamente válido;
a raridade do valor, sozinha, não comprova erro nem determina encaminhamento humano.

Guardar identificador do caso e da execução, indicador, valor observado, referência
comparável, direção alta/baixa, motivo, versão da regra, horário e estado de revisão.
Esse é um registro operacional da solução, separado do process log de conversas
destinado ao recrutamento.
Permitir filtrar por direção, motivo e estado, incluindo casos ainda não avaliados
por falta de referência. Distinguir anomalia numérica, baixa confiança e falha
técnica; um caso pode ter mais de uma dessas condições. Preservar o valor original.
Registrar a conclusão humana sem realimentar automaticamente o modelo ou seu teste.

Definir método, limites e ação operacional após a auditoria, ajustando-os no
conjunto de desenvolvimento/validação. Medir alertas falsos e volume de revisão.
No protótipo, testar casos altos, baixos, comuns e sem referência suficiente,
e verificar persistência e filtros. A visualização pode ser uma tabela simples;
esse requisito não obriga construir um dashboard separado.

### F04 — P2: entrada pela raiz dificulta descobrir a fundação

**Falha reproduzida:** a regra `submissions/` no `.gitignore` da raiz faz a busca
`rg --files -g AGENTS.md` retornar vazia neste ambiente. O chat atual começou na
raiz, e ali não há `AGENTS.md` nem `CLAUDE.md`. Os arquivos locais são legíveis;
passar a pasta explicitamente ao `rg` ou iniciar nela resolve a busca.

**Ajuste mínimo:** configurar a pasta da submissão como diretório inicial nas
ferramentas e colocar esse procedimento no README. Para sessões na raiz, instruir
explicitamente a leitura de `submissions/giovanne-berteli-comba/AGENTS.md`.
Preservar os arquivos da raiz conforme a regra de contribuição. Não pressupor que
uma ferramenta descerá até instruções aninhadas automaticamente.

**Aceite:** uma sessão nova encontra as regras, identifica desafio e próxima ação
sem consultar chats antigos. Verificar também arquivos novos ignorados ao preparar
o diff; `git status` sozinho não lista todos os arquivos não rastreados ignorados.
O uso de `git add -f` deve continuar limitado a arquivos explicitamente revisados.

### F05 — P2: rastreabilidade futura precisa de versões e comandos executáveis

**Cenário:** o dataset é atualizado, um resultado antigo continua vinculado e o
link existe. Ou o avaliador clona o projeto e os arquivos locais ignorados não
estão disponíveis. Links válidos não bastam para reproduzir uma conclusão.
A política de preservar dados e a exigência de setup já existem; falta concretizar
seu contrato na aquisição e no primeiro relatório.

**Ajuste mínimo:** em D01, manifesto com origem, versão, arquivo, hash e procedimento
de aquisição. Nos resultados, registrar comando, configuração, versão de código,
dependências e entradas. Ao criar código, fornecer um caminho documentado para
reproduzir auditoria, avaliação e demonstração, incluindo pré-requisitos de acesso.
Conservar a revisão de dados sensíveis antes de publicação já prevista.

**Aceite:** reproduzir o fluxo em diretório limpo com as instruções publicadas;
uma mudança de conteúdo no arquivo é identificada mesmo quando seu nome não muda.

### F06 — P2: o custo de manter contexto pode crescer sem melhorar a entrega

**Cenário:** a última entrada do process log cresce, e sua leitura obrigatória
vira um novo carregamento extenso de histórico. O plano também trata pesquisa de
PRs e CodeTour como tarefas a concluir, sem limite concreto de esforço.

**Evidência atual:** a leitura inicial indicada soma 12.063 bytes e 1.686 palavras
em cinco arquivos. Os três arquivos de chats somam 102.273 bytes e 42 mensagens.
Esses são tamanhos e contagens, não tokens ou economia medida. A base ainda é
pequena; o risco é sua expansão sem critério de parada.

**Ajuste mínimo:** manter um resumo curto de retomada com próxima ação, bloqueios
e links. Limitar previamente a amostra
e o esforço de R01. Reavaliar CodeTour e outros extras pelo benefício para o
avaliador quando a solução principal estiver pronta. Preservar os chats pedidos
pelo usuário sem torná-los leitura obrigatória de execução.

**Complemento aprovado pelo usuário — público do process log:** a narrativa e os
exports são evidências para a equipe de recrutamento, organizadas para facilitar
a avaliação do processo. Saem do contexto operacional padrão dos chats, inclusive
na retomada de sessões. Regras atuais, decisões duráveis e próxima ação ficam nos
documentos operacionais correspondentes, atualizados quando a decisão ocorre.
O log só deve ser lido ao preparar/auditar essas evidências ou por pedido explícito
de consulta histórica; seu conteúdo não se torna instrução de execução.

**Aceite:** outra ferramenta retoma o trabalho pelo resumo e documentos relevantes;
o arquivo de conversas não participa do contexto padrão. Economia de tokens só é
alegada quando medida em condições comparáveis.

### F07 — P1 antes do diagnóstico: cobertura dos dados limita as métricas

**Cenários a enfrentar na auditoria:** tickets ainda abertos somem da análise de
tempo; apenas uma parte dos clientes responde satisfação; médias de grupos com
composição diferente parecem indicar um efeito de canal; tempo de espera vira
suposta economia de pessoal. Nada disso foi observado nos arquivos, ainda não
adquiridos. São testes de resistência para as conclusões futuras.

**Ajuste mínimo:** D01/A01 devem registrar denominadores, população observada,
cobertura de satisfação, tickets abertos e validade dos campos temporais. Mostrar
distribuição e caudas quando viáveis, além de médias. Na estimativa de esforço,
explicitar tempo ativo por tarefa, elegibilidade, cobertura, revisão e retrabalho;
se esses dados faltarem, usar cenários identificados como hipóteses.

**Aceite:** cada número do diagnóstico permite recuperar população, unidade,
premissas e cálculo. Economia simulada e melhoria operacional medida aparecem
como categorias distintas. Os datasets podem cumprir papéis complementares sem
um join artificial ou transferência de taxonomia não validada.

## Acompanhamento

Decisões e estado dos ajustes ficam exclusivamente na lista oficial no início
deste arquivo. As seções F01–F07 detalham evidências, propostas e critérios de aceite.
A escolha de stack e a combinação dos datasets permanecem pendentes da auditoria.
