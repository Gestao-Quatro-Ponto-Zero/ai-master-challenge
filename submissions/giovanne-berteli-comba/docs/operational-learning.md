# Aprendizado central: acurácia não é economia

**A pergunta do candidato mudou o desenho da entrega:** mesmo com gráficos e um
classificador validado, onde estava a redução do trabalho de quem atende tickets?

O candidato observou que alimentar gráficos poderia agilizar a análise, mas não
conseguia ver redução significativa de tempo/custo na operação sem evoluções.
A revisão dessa objeção mostrou uma lacuna concreta: copiar um ticket, pedir uma
sugestão e preencher outra revisão poderia levar mais trabalho do que escolher
uma categoria no sistema original. Essa hipótese não tinha sido medida.

## O que foi aprendido e alterado

| Antes | Aprendizado | Mudança entregue |
| --- | --- | --- |
| Modelo com macro F1 superior ao baseline | Melhor classificação retrospectiva não mede esforço humano | Separar qualidade do modelo da experiência de uso |
| Um ticket por formulário | Cópia, troca de tela e revisão podem consumir o ganho | CSV → sugestões em lote → tabela de conferência/correção → arquivo final |
| Simulador partindo de quatro minutos manuais | É uma premissa, sem medição que a sustente para esta tarefa | Instrumentar tempo decorrido do percurso e preservar resultado negativo |
| Integrações planejadas | Transportar dados não garante reduzir trabalho | Demonstrar a tarefa localmente; manter integrações como continuidade |
| Afirmação genérica de valor | O benefício depende de tempo e qualidade juntos | Preparar um ensaio manual versus assistido com plano prévio e participação humana |

**O que já está entregue:** lote, medição e comparação, testes de software e um
[ensaio concluído por operador declarado](workflow-rehearsal.md). Nele, o assistido
teve maior concordância (7/8 contra 1/8), mas levou mais tempo (52,72 s contra
41,58 s). **O que continua pendente:** um piloto representativo da operação.
A extração pelo agente não constitui observação independente do participante.

## Como testar a triagem em lote

1. Na aplicação completa, abra **Triagem em lote** em Empresa ou Instrutor.
2. Informe identificação/tipo declarado, confirme IT em inglês e clique em
   **Iniciar lote e cronômetro**, antes de selecionar o arquivo.
3. Importe CSV UTF-8 com `ticket_id,text`. Há um cabeçalho para baixar; preencha
   1–50 linhas e até 10 mil caracteres por texto. IDs devem ser únicos no lote.
   `reference_category` é opcional, aceita só as oito classes e não entra no modelo.
4. Clique em **Gerar sugestões do lote**. Rerender não gera inferências nem aprovações.
5. Confira textos/sugestões numa tabela, corrija categorias e marque as linhas
   efetivamente revisadas. Confirme a conferência e registre-as. Textos completos
   também ficam disponíveis para leitura. Todas as linhas precisam de decisão.
6. **Preparar arquivo e concluir lote** fixa as decisões e o término. Baixe CSV e
   trilha JSON. O arquivo contém IDs, modelo, categoria final, estado confirmado
   e tipo de participante; não inclui textos originais, nomes ou referências.

O tempo vai do início do lote à preparação do arquivo final, incluindo seleção/
importação, espera pelo modelo, revisão, correções e pausas. Exclui criar o CSV
fora da aplicação, baixar o arquivo e entregá-lo a outro sistema. **É tempo
decorrido; não esforço ativo ou economia de caixa.** Falhas ficam registradas e
podem receber classificação manual. Interrupções e revisões anteriores não são
apagadas. O histórico fica no SQLite local ignorado pelo Git.

O CSV alimenta a triagem, **não recalcula o painel de diagnóstico de clientes**.
O modelo atende IT em inglês por declaração do operador; não valida sozinho o
domínio de um texto novo nem transfere sua qualidade para o dataset de clientes.

## Como você realiza o experimento

Na aplicação completa, selecione **Instrutor → Experimento**:

1. Leia o protocolo, informe sua identificação, escolha **Operador (declarado)**
   para uma execução pessoal e prepare o plano. Testes de automação usam seu tipo próprio.
2. A aplicação fixa 16 casos de **treino**, oito por etapa, um de cada classe em
   cada grupo. São textos/grupos distintos; pares aproximam comprimento sem usar
   predições para escolher exemplos. A ordem das etapas e dos casos é registrada
   por hash antes do início, evitando ordenar as linhas pela categoria verdadeira.
3. Inicie a etapa indicada. No modo manual, nenhuma sugestão é calculada/exibida.
   No assistido, a espera das sugestões entra no tempo. Confira, decida e prepare
   o arquivo em ambos. Não consulte referências ou outras telas para descobrir os rótulos.
4. Após as duas conclusões, veja tempo total e por caso, concordância com rótulos
   fornecidos, correções da sugestão e falhas. Valores negativos ficam visíveis;
   menor tempo com pior concordância não é apresentado como produtividade melhor.
5. Exporte resultado, protocolo, IDs/grupos, versões e trilhas. Todas as tentativas
   preparadas/interrompidas e os testes automatizados permanecem no inventário.

O protocolo versionado é [workflow-protocol.json](../data/workflow-protocol.json).
Os rótulos ficam ocultos nas duas etapas; a concordância só aparece ao final.
A montagem do plano e do CSV externo ficam fora do cronômetro do ensaio. Seus
lotes já são atribuídos; o tempo inclui abertura/importação interna até arquivo
pronto. Essa fronteira é diferente de operar uma integração de helpdesk.

## Como interpretar sem exagerar

Este é um **ensaio local de usabilidade**, com participante declarado e amostra
pequena/balanceada de textos já processados e usados no treino do modelo. Dificuldade,
experiência, ordem e aprendizado podem afetar os tempos. Os rótulos fornecidos
não foram adjudicados. Não é outro teste independente de generalização da IA.

Uma execução pode sustentar “neste ensaio e nestas tarefas, a etapa assistida teve
este tempo e esta concordância”. Não sustenta sozinha redução mensal de custos,
causas do backlog ou melhoria na outra base de atendimento. O teste final da V01
continua consumido e não é usado para ajustar modelo/limiar/referências.

Se o assistido não ajudar, o resultado orienta rever a tarefa e os atritos antes
de expandir. Se ajudar, o próximo passo é validar com a equipe e dados novos,
medindo o fluxo real completo. As [integrações futuras](future-roadmap.md)
podem facilitar adoção; não substituem essa demonstração de benefício.
