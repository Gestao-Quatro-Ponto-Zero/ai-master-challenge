# Limitações

## O dado

- **Dataset sintético e público** (CC0, Kaggle), não um CRM real. Os padrões que a ferramenta aprendeu — ciclo máximo de 138 dias, regra do fim do trimestre — podem ser artefato do gerador dos dados, não um fenômeno comercial real. É por isso que `drift.py` existe: se o próximo export mudar esses números, o comando avisa em vez de a ferramenta seguir calada.
- **Cerca de três trimestres de história** (01/03/2017 a 31/12/2017). A tabela de destino usa datas análogas de 3, 6 e 9 meses atrás; com só três trimestres, a primeira data análoga (há 3 meses) é a única bem sustentada, e o aviso de "sem data análoga" (Tarefa 3) cobre o caso em que nem essa existe.
- **1.425 dos 2.089 deals abertos não têm conta no CRM.** Isso não é um detalhe menor: o campo de conta só é preenchido depois do desfecho (0 dos 6.711 fechados está sem conta), o que descartamos como sinal de atributo em `docs/logica.md`, mas também significa que boa parte do pipeline aberto não tem com quem a ferramenta cruzar porte, setor ou histórico de relacionamento.
- **500 deals em Prospecting sem data de engajamento**, somando US$ 1,07 mi de tabela. A ferramenta não estima quando decidem, porque não sabe quando começaram. Fica na fila "iniciar", sem chance calculada.
- **Sem registro de atividade, desconto, quantidade negociada ou motivo de perda.** O cartão "o que o score não sabe" existe exatamente para declarar isso em cada deal, não para escondê-lo.

## A ferramenta

- **`hoje` é fixo no fim do export** (01/01/2018) na demo e no build de referência. Em produção, `run.py --hoje` recebe a data real; sem ela, o comando recusa, de propósito.
- **Sem escrita no CRM.** Marcar Feito, Adiar ou Não está vivo grava só no `acoes.jsonl` local (ou no navegador, na demo) — não volta para o sistema de origem. Um piloto real precisaria dessa integração.
- **Briefings são gerados em lote, não ao vivo.** O Haiku 5.5 escreve os textos no `run.py`, antes da publicação, e a demo mostra o resultado gravado. Quem abre a demo não dispara chamadas, e um dado que mude sem nova geração continua mostrando o texto antigo. O validador recusa números fora dos marcadores e promessas de decisão, mas não garante que o texto seja bom: a qualidade da prosa só foi conferida por leitura nossa, não por avaliação com vendedores reais.
- **Sem login.** Qualquer pessoa que acesse a URL vê os dados de todos os vendedores. Aceitável para uma demo pública com dados fictícios; não para uma operação real.
- **A conta de horas do resumo executivo é premissa, não medição.** Sabemos o ganho de valor por vendedor a cada quatro semanas; não sabemos o custo-hora real da operação, então convertemos em três cenários em vez de um número só.
- **O ajuste de cluster do cálculo de amostra do experimento não foi verificado por nós.** Usamos o número do guia de origem (1.100 deals por braço) por ser mais conservador que o nosso cálculo sem ajuste (996); não confirmamos a premissa de poder que o guia usou.

## O discovery foi ensaiado com personas sintéticas, não vivido com vendedores reais

As respostas da Tarefa 0B vêm de um agente de IA encarnando quatro arquétipos (Caçador de Meta, Consultor do Empresário, Operador de Processo, Embaixador da Cultura) e um líder, não de vendedores, gestores ou operadores reais da área comercial. Nunca escrevemos "entrevistei vendedores" neste repositório — o termo correto, em todo documento, é "discovery ensaiado" ou "personas sintéticas". Isso não é uma categoria de erro como "a IA errou uma conta": é uma categoria diferente, que pede tratamento diferente. Medimos a confiabilidade do informante com perguntas de calibração cuja resposta já conhecíamos (`discovery-transcricoes/calibracao-modo-b.md`), e separamos o que ele podia nos dizer do que não podia.

Consequências:

- Nenhuma resposta de persona é fato sobre a operação. É, no máximo, premissa com teste.
- As premissas P5, P7, P8 e P12 seguem **sem teste de adoção com pessoas reais**. Mudaram o produto porque a persona ou o dado as derrubaram nas transcrições — o estado vazio (P5), a marcação com motivo (P7), a visão agregada por padrão (P8), a fila de encerrar com patrocínio (P12) — e até serem testadas com gente de verdade, o produto deve ser tratado como hipótese de adoção, não como validada.
- A pergunta do discovery está validada como pergunta. A resposta não está.

**Cada premissa confirmada continua sendo premissa.** `docs/discovery.md` lista, para cada uma, o teste real que a resolveria com gente de verdade — observar vendedores numa segunda-feira, medir taxa de abandono, contar reversões no piloto (`docs/experimento.md`). Nenhuma virou fato só porque uma persona sintética concordou com ela.
