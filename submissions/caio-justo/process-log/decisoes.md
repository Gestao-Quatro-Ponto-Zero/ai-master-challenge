# Registro de decisões

Este registro separa o que eu decidi do que a IA propôs.

## Decisões minhas

| # | Decisão | O que mudou |
|---|---|---|
| 1 | Escolher o desafio 003, com a tese de reduzir custo e ganhar velocidade, usando inicialmente o Jev | Definiu o problema e a primeira hipótese |
| 2 | Mapear as submissões públicas antes de construir, em busca de algo pouco comum | Levou à análise dos 228 PRs e mudou o rumo do projeto |
| 3 | Abandonar o Jev, em vez de forçar o uso | O Jev saiu da solução |
| 4 | Pedir uma proposta inovadora sem ferramenta definida | A IA propôs o Lead Scorer que se prova |
| 5 | Exigir uma explicação em linguagem simples antes de aprovar | Aprovei a proposta depois de entendê-la |
| 6 | Exigir base científica para a proposta | Levou às fontes em `docs/EVIDENCIAS.md` |
| 7 | Propor um simulador de cenários com IA | Ficou fora desta entrega por recomendação da IA, porque ainda não foi testado no histórico |
| 8 | Colocar uma LLM no produto, pelo OpenRouter, com modelos pequenos para controlar o custo | A IA reduziu os candidatos a modelos pequenos e integrou a sugestão na checagem |
| 9 | Escolher o modelo depois de ver os números: testar também o DeepSeek V4.1 Flash e ficar com o Claude Haiku 5.5 | O Haiku virou o padrão, com 59 acertos nas duas rodadas |
| 10 | Manter a execução local e adicionar um vídeo de apresentação com os dados | A IA gravou a ferramenta real e montou o vídeo com narração sintética |

## Decisões propostas pela IA, com a minha aprovação geral

Estas decisões técnicas partiram da IA, e eu as acompanhei pelos resultados que ela relatou: a ideia do Lead Scorer que se prova, a regra da lista, os sorteios, o porteiro, a interface e a organização do relatório.

## Erros da IA encontrados no caminho

Quase todos foram encontrados pela própria IA, ao verificar o trabalho com dados ou com o navegador. Os scripts de cada etapa estão em `scripts-exploratorios/`.

| # | O erro | Como apareceu | O que mudou |
|---|---|---|---|
| 1 | Propôs um score de vitória com regressão logística | O teste temporal deu AUC de 0,49 | O score de vitória saiu do produto |
| 2 | Recomendou o Jev na triagem do desafio 002 | Três PRs já tinham testado e o Jev acertou de 38,6% a 45% | A ideia caiu |
| 3 | Disse que os deals acima de 138 dias eram um achado diferencial | Busca nos PRs mostrou o número 138 em 47 deles | O diferencial passou a ser o teste, não o achado |
| 4 | Calculou o porteiro misturando meses e chegou a AUC de 0,36 a 0,44 | O número estava bom de menos para ser real | Passou a calcular dentro de cada mês, com resultado de 0,47 a 0,52 |
| 5 | Simulou alternar a ferramenta por semana | O ciclo mediano é de 45 dias, então o efeito passaria de uma semana para outra | Sorteio por negócio |
| 6 | Disse que detectar +10 pontos levaria cerca de 5 semanas | Recalculado sobre todos os sorteados, com 90 dias de acompanhamento | O prazo real é de cerca de 17 semanas |
| 7 | Propôs ordenar por preço x tempo restante | O replay mostrou $1,11M contra $1,32M de preço sem parados | A regra mudou |
| 8 | Contou só negócios encerrados no placar | Isso enviesaria o teste, porque o destaque pode mudar o que encerra | Todo sorteado entra no denominador |
| 9 | Sorteou os parados por quantidade | Simulação mostrou margem acertando de 89% a 92%, abaixo dos 95% | Sorteio proporcional ao valor, com 92% a 98% |
| 10 | Mostrou tela quase vazia para 6 vendedores | Uso da ferramenta no navegador | Negócios não trabalhados sobem para o topo |
| 11 | Mostrava estimativa de 100% com uma única resposta | Uso da ferramenta no navegador | A estimativa só aparece a partir de 30 respostas |
| 12 | Limitou a resposta da LLM a 120 tokens | O teste real mostrou respostas cortadas em modelos que raciocinam antes | O limite subiu para 400, e o raciocínio foi desligado nos modelos em que isso é possível |
| 13 | Enviou o parâmetro de temperatura | O teste real mostrou que o Haiku era recusado por causa dele | O parâmetro saiu. Repeti para medir a estabilidade |
| 14 | Rodou as frases uma a uma, estourou o tempo e imprimiu um arquivo antigo | As duas rodadas foram interrompidas, e os números impressos eram velhos | Descartei esses números e passei a rodar em paralelo |
| 15 | Fixou um critério impossível: menos erros graves que a regra de palavras | A regra teve zero erros desse tipo, então nenhum modelo podia ficar abaixo | Registrei a falha e decidi com os dois tipos de erro à vista |

## O que a IA leu

A IA baixou o corpo dos 228 PRs, a lista de arquivos, até 3 documentos de cada um e as 176 reviews públicas do avaliador. Leu resumos por desafio, quase sempre com trechos e não o código inteiro. Quando este trabalho diz que não viu algo em outros PRs, isso significa apenas que não apareceu nessa leitura. Os relatórios brutos dessa leitura não estão neste repositório. Nenhum código de outros candidatos foi copiado.
