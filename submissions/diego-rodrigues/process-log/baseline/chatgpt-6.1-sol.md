Para este desafio, o MVP precisa resolver uma situação concreta: o vendedor abre sua carteira e identifica quais oportunidades revisar primeiro, com motivos que consegue entender. Dentro de 4–6 horas, eu priorizaria uma aplicação simples, com regras transparentes e testes, sem gastar o orçamento em infraestrutura ou em um modelo de ML difícil de validar.

1. Decisão de arquitetura

Recomendação: aplicação Streamlit, com processamento em pandas e scoring determinístico em Python.

O MVP terá uma única aplicação, executada localmente, que lê os quatro CSVs, consolida os dados e apresenta uma fila de oportunidades abertas.

Camada	Escolha	Responsabilidade
Interface	Streamlit	Filtros, fila priorizada e detalhes da oportunidade
Dados	pandas	Leitura, validação e junção dos quatro CSVs
Scoring	Funções Python	Cálculo dos componentes, score e explicações
Configuração	Arquivo de configuração	Pesos, limites e parâmetros de suavização
Testes	pytest	Validação das regras e prevenção de vazamento de dados
Persistência	CSVs locais	Dados de entrada, sem banco no MVP
Entrega	Repositório + README	Código, instruções, testes e process log

Não incluir no MVP: API separada, banco de dados, integração com CRM, autenticação, LLM em tempo de execução ou treinamento de modelo.

Essas peças aumentariam o esforço sem melhorar proporcionalmente a entrega principal.

Fluxo da aplicação
Carregar os quatro arquivos.
Validar esquema, chaves, datas e categorias.
Consolidar as oportunidades com conta, produto e equipe.
Separar histórico encerrado de oportunidades abertas.
Construir referências históricas.
Calcular score e explicações das oportunidades abertas.
Aplicar filtros e apresentar a fila.
Permitir exportar a seleção priorizada.

O score deve ser calculado antes dos filtros da interface. Assim, filtrar por vendedor ou região não muda artificialmente a nota de uma oportunidade.

2. Experiência do vendedor

A interface terá uma tela principal, com três áreas.

A. Seleção da carteira

Filtros por:

Vendedor.
Manager.
Escritório regional.
Produto.
Etapa.

Vendedor, manager e região serão usados para organizar a carteira, não para avaliar pessoas ou atribuir notas de desempenho.

B. Fila de prioridades

Separar em duas abas:

Engaging: oportunidades já em negociação.
Prospecting: oportunidades que ainda precisam ser qualificadas.

Isso evita tratar uma oportunidade em prospecção como equivalente a uma negociação ativa.

A tabela exibirá:

Campo	Utilidade
Posição	Ordem sugerida de revisão
Conta e produto	Identificação do deal
Score de prioridade	Síntese dos critérios
Principal motivo	Explicação imediata
Tempo desde o início de Engaging	Contexto temporal, quando disponível
Suporte histórico	Quantidade de casos usados como referência
Ação sugerida	Próximo passo de revisão

Ordenação padrão: score decrescente, com desempate por identificador. Não ordenar simplesmente pelo valor.

C. Detalhe da oportunidade

Ao selecionar um deal:

Mostrar os componentes do score.
Explicar o que elevou ou reduziu a prioridade.
Exibir os denominadores das taxas históricas.
Destacar dados ausentes e referências com pouca amostra.
Sugerir uma ação de revisão.

Exemplos de ações:

“Qualificar necessidade e prazo antes de avançar.”
“Revisar próximo passo da negociação.”
“Validar se a oportunidade continua ativa.”
“Completar identificação da conta.”

Essas ações são recomendações baseadas nas regras, não afirmações sobre contatos, interesse ou atividades que o dataset não registra.

3. Arquitetura dos dados
Tabela consolidada

A tabela central continua sendo sales_pipeline.csv.

As junções serão do tipo left join, preservando todas as oportunidades:

Junção	Chave	Informação adicionada
Pipeline → contas	account	Setor, receita, funcionários e localização
Pipeline → produtos	product	Série e preço de catálogo
Pipeline → equipes	sales_agent	Manager e escritório regional

Validações obrigatórias
opportunity_id único.
Chaves das dimensões sem duplicidade.
Junções sem multiplicação de linhas.
Etapas dentro dos valores esperados.
Datas convertidas corretamente.
Datas de fechamento anteriores ao engajamento sinalizadas.
Contas e produtos não encontrados sinalizados.
Campos ausentes tratados explicitamente.

Uma conta ausente não deve eliminar a oportunidade nem receber uma penalização automática. O componente correspondente usa uma referência neutra e a interface informa a limitação.

Separação dos conjuntos
Histórico: oportunidades Won e Lost.
Carteira a priorizar: oportunidades Prospecting e Engaging.

close_value e close_date não entram como atributos do deal aberto. A data de fechamento pode ser usada para delimitar o histórico e calcular duração dos casos encerrados.

Também não usaria receita ou número de funcionários como “quanto maior, melhor”. Sem evidência de aderência, tamanho da conta não demonstra intenção de compra.

4. Lógica de scoring
Princípio

O score representa prioridade de revisão comercial, não probabilidade de fechamento.

Um score 85 não significa “85% de chance de ganhar”. É uma combinação de aderência histórica, maturidade da oportunidade e contexto temporal.

Fórmula inicial

Todos os componentes variam de 0 a 1:

Score = 100 × (
    0,30 × histórico do produto
  + 0,20 × histórico do setor
  + 0,10 × histórico da conta
  + 0,25 × maturidade da etapa
  + 0,15 × contexto temporal
)

Os pesos são hipóteses iniciais de produto, documentadas e ajustáveis. Não devem ser apresentados como parâmetros estatisticamente otimizados.

A. Aderência histórica: 60 pontos

Usar a proporção de Won entre os casos encerrados de:

Mesmo produto.
Mesmo setor.
Mesma conta.

Para evitar que grupos pequenos dominem o ranking, aplicar suavização:

Taxa suavizada =
(vitórias do grupo + k × taxa global)
÷
(casos encerrados do grupo + k)

Parâmetro inicial: k = 20, configurável.

Com poucos casos, a taxa fica próxima da referência global. Com mais casos, o histórico do grupo ganha influência.

Regras:

Sem histórico: usar taxa global.
Mostrar sempre o tamanho da amostra.
Não somar oportunidades abertas ao denominador.
Não usar taxa individual do vendedor.

Limitação: produto, setor e conta podem trazer sinais correlacionados. No MVP, isso será documentado, sem tratar os três componentes como evidências independentes.

B. Maturidade da etapa: 25 pontos

Valores iniciais:

Etapa	Componente
Engaging	1,00
Prospecting	0,40

A lógica favorece negociações já iniciadas, mas as abas separadas mantêm uma fila útil para prospecção.

Won e Lost ficam fora do ranking.

C. Contexto temporal: 15 pontos

Para Engaging:

Calcular dias desde engage_date.
Comparar com o percentil 75 da duração histórica dos deals encerrados do mesmo produto.
Usar a duração global quando a amostra do produto for insuficiente.

Regra inicial:

Idade relativa à referência	Componente
Até a referência	1,00
Entre 1 e 2 vezes a referência	0,50
Acima de 2 vezes a referência	0,00
Data ausente ou referência indisponível	0,50

Para Prospecting, usar valor neutro e informar que não há data de início da prospecção no esquema fornecido.

Importante: tempo desde Engaging não é tempo sem contato. O MVP não pode afirmar que um deal está “sem follow-up”.

Fila adicional de atenção

Deals muito antigos também aparecem em uma seção “Revisar situação”, mesmo que tenham score baixo.

Isso distingue duas necessidades:

Onde concentrar esforço comercial.
Quais oportunidades precisam de atualização ou limpeza.

5. Data de referência e prevenção de vazamento

Como o dataset é um recorte histórico, usar a data atual automaticamente pode fazer todas as oportunidades parecerem antigas.

Decisão para o MVP: trabalhar em modo “snapshot do dataset”.

Sugerir como referência a maior data válida observada.
Mostrar essa data claramente na interface.
Explicar que ela é uma aproximação da data do recorte, não uma data de extração comprovada.
Usar apenas casos encerrados até a referência.

Não oferecer simulação de carteiras passadas no MVP. Sem histórico de mudanças de etapa, não é possível reconstruir com segurança como o pipeline estava em qualquer data anterior.

Também não apresentar métricas de acurácia ou ganho de conversão sem uma avaliação adequada. A entrega inicial valida funcionamento e coerência das regras, não eficácia comercial comprovada.

6. Estrutura do projeto

lead-scorer/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── accounts.csv
│   ├── products.csv
│   ├── sales_teams.csv
│   └── sales_pipeline.csv
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── validation.py
│   ├── features.py
│   ├── scoring.py
│   └── explanations.py
├── tests/
│   ├── test_validation.py
│   └── test_scoring.py
└── docs/
    ├── scoring.md
    ├── limitations.md
    └── process-log.md

Separação essencial: scoring.py não depende do Streamlit. Isso permite testar a lógica isoladamente e, no futuro, reutilizá-la em uma API ou integração.

As explicações serão geradas por templates a partir dos componentes reais do score, sem LLM. Assim, o texto permanece consistente com o cálculo.

7. Plano de execução: 6 horas

Tempo	Etapa	Entrega e critério de conclusão
0:00–0:30	Inspeção dos dados	Contagens reais, ausências, datas, categorias e problemas de chave identificados
0:30–1:15	Pipeline de dados	Junções validadas, sem perda ou multiplicação de oportunidades
1:15–2:15	Scoring	Componentes, suavização, fallbacks e explicações funcionando
2:15–3:30	Interface	Filtros, abas, ranking, detalhe e seção de atenção
3:30–4:15	Testes	Regras críticas e casos extremos cobertos
4:15–5:00	Entrega reproduzível	README, dependências, exportação e teste de instalação limpa
5:00–6:00	Revisão e demonstração	Ajustes de usabilidade, process log e roteiro de demo

Se houver apenas 4 horas

Cortar:

Gráficos decorativos.
Publicação em nuvem.
Refinamentos visuais.
Exportação, se necessário.

Não cortar: validação dos dados, explicações, testes essenciais ou instruções de execução.

8. Testes e critérios de aceite

O MVP estará pronto quando:

Rodar seguindo o README em um ambiente limpo.
Usar os quatro arquivos reais.
Preservar a quantidade de oportunidades após as junções.
Priorizar somente Prospecting e Engaging.
Produzir scores entre 0 e 100.
Mostrar explicações coerentes com os componentes.
Tratar dados ausentes sem quebrar.
Manter o score estável quando os filtros mudam.
Não alterar o score de um deal aberto quando seu close_value é modificado.
Não usar resultados encerrados depois da data de referência.
Permitir que um vendedor encontre sua carteira e entenda o primeiro deal sem ler a documentação técnica.

Teste manual final: selecionar uma carteira, abrir três oportunidades com scores diferentes e conferir cada contribuição contra os dados.

9. Uso de IA e process log

Usar IA por etapas pequenas, com critérios de aceite:

Inspecionar o esquema e propor validações.
Implementar carga e junções.
Implementar scoring e testes.
Construir a interface.
Revisar vazamento, casos extremos e documentação.

Registrar, conforme o trabalho acontecer:

Registro	Conteúdo	Objetivo
Prompt	Pedido efetivamente enviado	O que aquela interação precisava resolver
Resultado	Código ou proposta produzida	—
Verificação	Teste executado e resultado	—
Decisão humana	O que foi aceito, corrigido ou descartado	—
Evidência	Commit, captura ou saída de teste	—

Não reconstruir um processo fictício ao final. O guia de submissão citado no briefing ainda precisa ser consultado para conferir seu formato específico.

Recomendação final

Construa primeiro uma fila explicável e confiável, não um "motor de previsão". A melhor demonstração será mostrar um vendedor filtrando sua carteira, entendendo por que uma oportunidade aparece no topo e identificando outra que precisa ter sua situação revisada.

A arquitetura proposta separa dados, regras e interface para facilitar manutenção. O plano concentra o tempo em funcionamento, explicabilidade e reprodução da entrega, deixando infraestrutura e ML para uma evolução posterior.
