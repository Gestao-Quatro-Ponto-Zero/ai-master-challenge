# Investigação antes da submissão — cinco princípios

Revisão em **03/11/2026**, solicitada pelo candidato antes da P01. Foram lidos o
briefing, o plano, a entrada para o revisor, os contratos, o diagnóstico, a
avaliação, o setup e a implementação da interface. Esta investigação registrou
propostas. Os pontos 1–4 foram implementados posteriormente em M01–M05, por pedido
do candidato; veja o [resumo atual](start-here.md) e o [roteiro](demo-guide.md).
O ponto 5 permanece como [evoluções planejadas](future-roadmap.md). As formulações
de proposta abaixo preservam o corte da investigação original.

**Recomendação: fazer uma rodada curta de comunicação e utilidade para gestão
antes do PR.** O projeto já demonstra execução e verificação. Seu maior ganho
agora seria permitir que o entrevistador veja, no mesmo percurso, problema,
decisão de negócio, demonstração e contribuição humana. A aplicação atual abre
na triagem; o diagnóstico operacional e os resultados finais ficam nos documentos.

## 1. O entrevistador entende a entrega e a autoria?

O [README](../README.md) segue o template, distingue humano e agente e expõe os
limites. O [guia](review-guide.md), o [process log](../process-log/README.md) e o
[CodeTour](code-tour.md) fornecem evidências suficientes para investigar a execução.
Mas há muitos caminhos e termos internos — V00, I01, V01, gate, membership,
recibos — antes de uma pessoa entender por que deveria usar a solução.

O roteiro de entrada recomendado é:

1. **Problema:** a operação precisa entender fila, satisfação e desperdício.
2. **Descoberta:** os dados permitem investigar a fila e as notas, mas não medir
   duração ou esforço ativo com segurança.
3. **Decisão:** demonstrar assistência à classificação com confirmação e histórico;
   medir benefício em piloto antes de prometer economia.
4. **Resultado:** diagnóstico verificável e benchmark IT melhor que o baseline,
   com cobertura e erros explícitos.
5. **Demonstração:** texto → sugestão ou encaminhamento → revisão → histórico.

Isso cabe numa entrada de uma página e num roteiro de demonstração de cinco
minutos, tempo proposto de leitura/demo, ainda não medido com entrevistadores.
O tour técnico continua disponível para aprofundamento.

| Participação comprovada | Evidência e interpretação |
| --- | --- |
| Humano escolheu o desafio e direcionou a entrega | [Preparação](../process-log/01-preparation-and-foundation.md); escolha entre alternativas |
| Humano exigiu registro/filtro de anomalias altas e baixas | [Requisitos adicionais](../process-log/04-approved-review-scope.md); definição de uma necessidade de uso |
| Humano delimitou o papel das conversas | Mesmo registro; evidência para recrutamento e contexto operacional separado |
| Humano confrontou setup e descoberta do tour | [Setup](../process-log/13-setup-fix.md) e [CodeTour](../process-log/16-codetour-discovery.md); uso real revelou falhas que checks anteriores não cobriam |
| Humano definiu estes cinco critérios antes do envio | Pedido desta investigação; priorização de compreensão, reprodução e benefício para o negócio |
| IA analisou dados, definiu métodos e implementou | [Workflow e capturas](../process-log/README.md); geração técnica, cálculos, parâmetros, testes e documentação sob a direção registrada |

A apresentação pode explicar o papel humano como direção, requisitos e confronto
da experiência real. Não há evidência para atribuir ao candidato implementação
manual, adjudicação dos rótulos ou aprovação de cada decisão técnica. O uso de IA
generativa no desenvolvimento está documentado; a inferência do protótipo usa
TF-IDF e regressão logística, sem um LLM em produção.

## 2. O entrevistador consegue reproduzir?

Há dois inicializadores claros: `run.sh` para experimentar e `review.sh` para
abrir o tour. O lock, as versões/fontes dos dados e a reprodução isolada são
pontos fortes. Na verificação desta sessão:

- Contratos da fundação e apresentação passaram antes das alterações documentais.
- A reagregação dos **7.175 casos** conciliou resultados e hashes, sem carregar
  modelo, gerar novas previsões ou treinar.
- `bash run.sh --prepare-only` terminou com sucesso em **0,288 s** neste ambiente
  já preparado, preservando hashes e mtimes dos **23 arquivos** monitorados de
  dados/modelos. Esse tempo não estima uma instalação limpa.
- A reprodução limpa e o reuso com rede bloqueada já tinham sido executados na
  [evidência de setup](review-evidence/setup-reproduction.json); não foram repetidos
  nesta investigação. Não houve inspeção visual em navegador nesta sessão.

Os resultados e hashes inspecionados estão em
[evidência desta investigação](review-evidence/pre-submission-review-checks.json).

| Atrito encontrado | Ajuste recomendado | Critério de aceite |
| --- | --- | --- |
| Bootstrap validado apenas em Linux x86_64/glibc | Mostrar o pré-requisito junto do primeiro comando no README | Leitor conhece a compatibilidade antes de executar; não anunciar Windows/macOS como testados |
| Primeiro uso prepara ambiente, dados e quatro candidatos | Separar leitura dos resultados de reprodução completa; explicar etapas e dependência de rede | Resultados podem ser compreendidos sem treino; início/fim de cada etapa visíveis |
| Não há duração registrada do setup frio | Medir numa próxima reprodução quando necessária | Publicar tempo observado e host, sem estimativa apresentada como medição |
| Mensagem final do setup afirma que o teste permanece reservado | Corrigir o texto de status sem alterar os cálculos | Informar que o setup não executa o teste final; no checkout publicado a avaliação já foi consumida |
| Exemplo exige carregar, conferir contexto e enviar | Expor roteiro curto na própria tela com contexto IT em inglês | Um caso de treino percorre análise, revisão e recarga sem adivinhar passos |
| Trechos antigos dizem “próxima etapa” já concluída | Marcar relatórios como registros de suas etapas e ligar ao status atual | [Proposta](automation-proposal.md), [diagnóstico](operational-diagnosis.md) e [relatório final](final-evaluation.md) deixam claro seu corte histórico |

**Reprodução tem três objetivos diferentes:** ler os resultados agregados,
experimentar a triagem e refazer a análise/treino. A entrada deve indicar o comando
e a saída esperada de cada objetivo. As saídas locais detalhadas do teste final
não são versionadas; o check de reagregação exige esses arquivos. Uma pessoa que
acabou de clonar pode ler o agregado, mas precisará de uma reprodução identificada
para regenerar os detalhes. Isso não cria outro teste inédito.

## 3. Uma empresa consegue tomar decisões com os resultados?

Sim, principalmente sobre investigação da fila, qualidade de medição e desenho
de um piloto. A comunicação pode ligar cada achado a uma ação, responsável e
medida de acompanhamento. As propostas abaixo não são resultados de uma operação real.

| Achado observado | Decisão proposta e responsável sugerido | Como verificar benefício |
| --- | --- | --- |
| 5.700/8.469 não encerrados, incluindo 1.403 Critical | Liderança de suporte confere status/prioridade e verifica quais registros ainda representam trabalho ativo | Após validar e registrar datas: idade da fila, tempo em cada estado, reaberturas e cumprimento de SLA; o retrato atual não mede esses indicadores |
| 2.881 aguardam resposta do cliente; 2.819 estão Open, todos sem primeira resposta registrada | Operação distingue espera de cliente de trabalho do agente e confere instrumentação | Transições, retornos após contato e minutos ativos; testar um acompanhamento de pendências depois de validar os registros |
| 1.102/2.769 encerrados avaliados têm nota 1–2 (39,80%); não encerrados não têm nota | CX investiga motivos das notas e define quando convidar o cliente a avaliar | Distribuição e cobertura das notas por população, motivo e período; não interpretar silêncio como satisfação |
| Diferença entre proporções não encerradas dos canais é só 1,35 p.p.; associações marginais com notas não foram convincentes | Gestão evita priorizar contratação ou migração de canal com base apenas nesses recortes | Coletar capacidade, entradas, idade e esforço por tarefa antes de decidir alocação |
| Macro F1 0,844612 contra 0,646094 do baseline de texto no IT | Responsável pelo serviço IT pode testar apoio à classificação em piloto representativo | Concordância após revisão, tempo total por decisão, retrabalho e erros por classe; não transferir esse desempenho ao dataset de clientes |
| Só 1.951/7.175 vão à confirmação padrão (27,19%); 5.224 vão às demais filas | Operação planeja capacidade para triagem/especialistas e confirmação de todos os casos | Tempo por fila, pendências de revisão e proporção corrigida; cobertura não equivale a tickets resolvidos automaticamente |
| 50 dos 67 erros padrão pertencem a classes de especialista | Responsável técnico mantém confirmação e estuda esses erros num próximo ciclo | Categoria verdadeira adjudicada e gravidade do encaminhamento errado, usando novos dados para avaliar qualquer ajuste |
| Cenários variam de −26,67 a +74,75 h/mês | Gestão mede os componentes do esforço antes de expandir | Ganho líquido após assistência, revisão, retrabalho e esforço fixo; também registrar resultados negativos |

Fontes: [diagnóstico](operational-diagnosis.md), [premissas](../data/diagnosis-assumptions.json)
e [avaliação final](final-evaluation.md). Os 50 casos são **2,56% das 1.951 sugestões
padrão** e **74,63% dos 67 erros dessa fila**, dois denominadores diferentes.

No cenário de referência, 900 casos assistidos geram 45 horas brutas hipotéticas;
revisão, retrabalho e esforço fixo reduzem isso a **29,75 h/mês**. Mantendo as demais
premissas, o trabalho manual precisa superar **2,02 minutos por caso assistido**
para haver ganho. Esse ponto de equilíbrio ajuda a decidir o que medir no piloto.
Nem essa cobertura de 900 casos nem os tempos foram aprendidos do benchmark IT.

O próximo experimento de negócio deveria comparar o fluxo atual com o assistido,
com casos representativos, grupos comparáveis e confirmação humana em ambos os
fluxos. Medir tempo total, correções, retrabalho, satisfação e erros especializados;
acordar critérios de avanço/interrupção com a operação antes de olhar resultados.
O volume, a duração e o impacto esperado dependem dos dados reais do piloto.

## 4. O que acrescentar agora?

Prioridades e esforço abaixo são julgamento do agente. “Pequeno/médio” compara
escopos; não é tempo de execução medido nem autorização para ampliar a entrega.

| Ordem | Entrega proposta | Benefício imediato | Esforço e aceite |
| --- | --- | --- | --- |
| 1 | Entrada executiva e roteiro de cinco minutos | Candidato consegue explicar problema → decisão → evidência → demonstração; autoria humana explícita | Pequeno: uma página, fonte de cada número e percurso legível sem extensão |
| 2 | Visão **Diagnóstico e resultados** na aplicação | Diretor vê fila, satisfação, ações e benchmark sem procurar JSONs | Médio: ler agregados existentes, mostrar denominadores/fontes e separar diagnóstico de clientes, benchmark IT e atividade local; nenhum novo fit ou leitura dos casos finais na demo |
| 3 | Ajustes de reprodução e textos de status | Evitar surpresa de plataforma, contexto e teste já consumido | Pequeno: executar caminhos afetados, manter cálculos/modelos e não deixar informação histórica aparecer como status atual |
| 4 | Exportação operacional com esquema explícito | Operador leva a fila filtrada e as revisões para análise/planilha | Pequeno a médio: IDs/versões/estado/data, distinção caso versus métrica, texto do cliente omitido por padrão; total exportado reconcilia com filtros |
| 5 | Simulador de capacidade a partir da fórmula existente | Gestão entende revisão, retrabalho e ponto de equilíbrio | Médio: premissas editáveis, cenário negativo visível e rótulo “hipótese”; nunca preencher cobertura de clientes com métrica IT |

**Escopo recomendado antes da P01: itens 1–3, com uma única visão adicional de
gestão.** Exportação e simulador entram se o percurso principal estiver pronto e
fácil de demonstrar. Um CRUD de clientes, galeria de componentes, novos modelos
ou um bot completo aumentariam o escopo sem resolver a principal lacuna de leitura.

A visão proposta usa os resultados agregados salvos, com gráficos simples e tabela
achado → ação → indicador. Deve continuar útil para leitura mesmo quando não houver
modelo ou histórico local, evitando condicionar a compreensão a um treino completo.
O Streamlit oferece [botão de download](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)
para uma futura exportação explícita; nenhuma nova biblioteca é necessária para
propor esse caminho. A compatibilidade precisa ser conferida no lock ao implementar.

Não alterar os modelos, o núcleo congelado, o limiar ou as referências com base nos
erros conhecidos do teste. Mudanças de apresentação devem ter sua própria validação;
o benchmark permanece evidência da versão avaliada. Qualquer novo comportamento de
classificação exige identificação de versão e avaliação com novos dados.

## 5. O que implementar no futuro?

| Sequência | Evolução | Uso concreto | Dependência e critério de avanço |
| --- | --- | --- | --- |
| F1 | Piloto e captura de eventos/esforço | Identificar onde se gasta trabalho e se assistência compensa | Datas/eventos confiáveis, rótulos adjudicados e medição do fluxo atual; ganho líquido e qualidade aceitáveis acordados antes do teste |
| F2 | IA analista sobre métricas calculadas | Responder “o que mudou e quais casos investigar?” e redigir resumo com fontes | Cálculo determinístico separado do texto; cada afirmação aponta métrica, população, período e versão; recusar conclusão sem evidência |
| F3 | Google Sheets para fila/revisões | Permitir acompanhamento pelo time sem copiar telas | Exportação local estável, acesso configurado, event_id e reconciliação para evitar duplicações; SQLite/sistema de origem preserva histórico |
| F4 | Resumo por email e alerta em canal interno | Avisar mudança acionável, falha ou necessidade de revisão com link para o caso | Destinatários/canal configurados e fluxo autorizado; deduplicação, entrega observável e aplicação acessível com controle de acesso |
| F5 | Bot interativo no canal já usado pelo time | Consultar caso, atribuir responsável ou solicitar revisão | Autenticação/papéis, ações idempotentes e auditoria; confirmação no sistema antes de executar ação sensível |
| F6 | Integração de helpdesk e ciclo de melhoria | Receber tickets reais e registrar revisão/correções no trabalho habitual | Taxonomia e textos de entrada validados, contrato de eventos, dados novos e avaliação por versão; correção humana não altera modelo automaticamente |

**A IA analista não seria a fonte de verdade das métricas.** Código valida schema,
populações, ausência de duplicação, somas, limites e diferenças de versão. O modelo
consome esse resultado, explica achados e levanta hipóteses. Sua qualidade precisa
de avaliação própria: cálculos contraditos, números inventados, fontes ausentes e
confusão entre hipótese, associação e causa. Uma segunda IA concordando não comprova
que um rótulo ou uma decisão de negócio está correto.

Para comunicação, um resumo agendado e um alerta por mudança significativa podem
atender a necessidade inicial. O Discord permite publicar por
[webhook de entrada](https://docs.discord.com/developers/resources/webhook)
sem criar um bot completo. Um bot com comandos/revisões é uma etapa posterior,
se o time já trabalhar no Discord; a mesma necessidade pode ser atendida pelo canal
interno que a empresa utiliza.

Para planilhas, a API permite
[acrescentar linhas](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/append).
Isso fornece o transporte; a aplicação precisa resolver IDs, repetição de eventos,
permissões e conflitos de revisão. Para email, o Gmail permite
[criar/enviar mensagens ou enviar rascunhos](https://developers.google.com/workspace/gmail/api/guides/sending).
Uma primeira integração pode preparar um resumo para aprovação. Nenhuma conta,
credencial, envio ou conexão externa foi configurada nesta investigação.

O fluxo futuro proposto é:

`dados/eventos → cálculos e checks → métricas versionadas → IA explica com fontes
→ pessoa revisa → resumo/planilha/alerta → decisão registrada`

## Encaminhamento

Investigação R02 concluída; P01 continua pendente. O
[backlog](../execution/backlog.md) reúne os itens propostos e seus gatilhos.
Esta revisão registra diagnóstico e prioridade em seu corte histórico. Para o
painel, exportação e simulador entregues posteriormente, siga o [resumo atual](start-here.md).
A IA analista e as integrações permanecem no [roadmap](future-roadmap.md).
