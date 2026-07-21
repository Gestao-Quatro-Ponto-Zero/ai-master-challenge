# Retrospectiva do projeto MVP LeadScorer

Este MVP adota um modelo de ranqueamento do potencial de oportunidades de venda por meio da
mensuração de seis dimensões de oportunização, das quais apenas quatro estão ativas neste
MVP. Cada dimensão reflete um vetor do contexto de decisão do processo de venda e recebe um
peso conforme a avaliação arbitrada da sua importância.

Qualquer abordagem mais sofisticada para modelar o sinal de sucesso de uma oportunidade de
venda é desencorajada pela limitação do dataset, insuficiente tanto em largura (features)
quanto em profundidade (observações). Optou-se, assim, por um modelo de sinalização baseado
em dimensões de oportunização devidamente ponderadas.

Inicialmente, o projeto incluía a proposição de uma heurística de distribuição inteligente de
leads por agente de venda. Pelas mesmas limitações já apresentadas, decidiu-se derivar o
recurso como uma dimensão de oportunização, a Especialização do agente, que reflete a
habilidade histórica do agente em vender aquele produto ou para aquele cliente.

Isoladamente, a adoção de Python, com Django e SQLite, poderia ser uma escolha mais produtiva
para o protótipo. Contudo, optou-se pela stack composta por Common Lisp, HTMX e PostgreSQL, por
se dispor de um pipeline de planejamento e produção de software assistido por LLM maduro,
testado e pronto para uso, baseado nessas tecnologias.

O desenvolvimento seguiu boas práticas, entre elas a construção de uma concepção inicial
segundo o processo unificado, o desenvolvimento orientado a testes e o projeto seguro por
concepção (security by design). O pipeline de desenvolvimento assistido por LLM, projetado e
configurado pelo autor e por ele utilizado em seus projetos profissionais, registra
sistematicamente o trabalho diário realizado (worklogs), vinculando-o às respectivas sessões
físicas (sessions), e registra tempestivamente as decisões de arquitetura (ADR) em tempo de
desenvolvimento.

O projeto foi separado em três grandes fases: a análise exploratória; a construção do modelo
de ranqueamento; e o desenvolvimento da aplicação MVP para gestão de oportunidades. Em cada
fase, os objetivos principais foram desdobrados em objetivos atômicos, com as respectivas
tarefas, mantidas em um backlog unificado.

O desenvolvimento foi intercalado por sessões de análise e planejamento, com ampla
documentação. Cada sessão conta com a sua própria atividade de auditoria de qualidade e de
definição de pronto, realizada por agente independente e com contexto propositalmente
limitado. Cada uma das grandes fases foi sucedida por uma sessão complementar de code-review.

O overdelivery e o overengineering foram intencionais e controlados, com o objetivo de atender
à principal premissa do desafio: demonstrar como o autor interage com o LLM para o raciocínio
e a consequente solução de problemas que envolvem análise de dados e tomada de decisão.

Ao todo, foram consumidas cerca de 18 horas efetivas de trabalho humano-agente. O projeto foi
conduzido em um final de semana, com intervalos relevantes entre as sessões. O resultado é uma
proposta funcional e objetiva para o ranqueamento de oportunidades de venda, especialmente em
contexto de limitação de informações, sustentada por uma ferramenta, em estágio MVP,
autoportada, que gerencia o ciclo de vida de engajamento em cada oportunidade.
