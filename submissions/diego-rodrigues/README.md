# Submissão — Diego Rodrigues — Challenge 003 · Lead Scorer

> **Para o CEO, em uma frase:** pelo histórico, três quartos do pipeline que o time reporta já não fecha mais; esta ferramenta mostra os 115 negócios que ainda podem decidir e em que ordem atacar na segunda-feira.

**Demo pública:** https://lead-scorer-diego.vercel.app · **Testar em 60 segundos:** [docs/como-usar-a-demo.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/como-usar-a-demo.md) · **Como usei IA:** [process-log/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log)

| Pipeline aberto | Já passou da janela de decisão | Vivo de verdade | Ganho no backtest vs. ordenar por preço |
|---|---|---|---|
| US$ 4,97 mi · 2.089 negócios | **73,6%** · US$ 3,66 mi · 1.474 negócios | **115 negócios** · US$ 236 mil | **1,30×** · IC 95% de 1,13 a 1,52 ([como foi medido](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/experimento.md)) |

**Janela de decisão** é o prazo dentro do qual, no histórico deste CRM, todo negócio fechou: até 138 dias de duração e até o fim do trimestre seguinte ao do primeiro contato. Dos 6.711 negócios fechados no export, nenhum foi ganho depois desse ponto.

Todo número desta página sai de script guardado no repositório e foi recalculado por um revisor independente, com código próprio, a partir dos CSVs ([process-log/verificacao/relatorio.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/verificacao/relatorio.md)).

---

## Sobre mim

- **Nome:** Diego Rodrigues
- **LinkedIn:** https://www.linkedin.com/in/diegoaorodrigues/
- **Challenge escolhido:** 003 · Lead Scorer

---

## Executive Summary

Construí uma fila de trabalho para a segunda-feira do vendedor, que roda sobre os quatro CSVs reais do CRM e explica cada posição em frases que ele consegue checar. A descoberta que mudou o produto é que nenhum atributo do negócio prevê quem ganha — conta, vendedor, gerente, região, setor, porte e produto foram testados contra o resultado real e nenhum mostrou sinal estatístico (p-valor de 0,05 ou mais em todos) —, mas a duração do negócio combinada com a altura do trimestre prevê **quando** ele decide. Por essa régua, 73,6% do valor aberto já passou do ponto em que, no histórico deste export, qualquer negócio foi ganho. A recomendação é priorizar por valor de tabela multiplicado pela chance aprendida de decidir na janela, o que no teste de volta ao passado capturou 1,30 vez o valor da melhor alternativa honesta, com intervalo de confiança que não cruza 1, e medir esse ganho num piloto com grupo de controle antes de expandir. O que a ferramenta não sabe está declarado em cada negócio: registro de atividade, desconto, motivo de perda e os 500 negócios em Prospecting sem data de engajamento, que somam US$ 1,07 mi e sobre os quais ela não opina.

Resumo completo, com a conta de horas tratada como premissa declarada: [docs/resumo-executivo.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/resumo-executivo.md).

---

## Solução

### O problema em uma imagem

![Pipeline aberto em 01/01/2018: a maior parte já passou da janela de decisão](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/01-pipeline-aberto.png?raw=true)

<sub>Código-fonte: [01-pipeline-aberto.mmd](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/01-pipeline-aberto.mmd)</sub>

**Por que dá para afirmar que esse valor já não fecha.** A afirmação se apoia em três provas, todas conferidas por um revisor independente com código próprio ([process-log/verificacao/relatorio.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/verificacao/relatorio.md)):

1. **O histórico inteiro.** Dos 6.711 negócios fechados no export, nenhum fechou com mais de 138 dias, e só um fechou depois do fim do trimestre seguinte. Esse um foi perdido.
2. **O teste de volta ao passado.** Em seis datas de 2017, a ferramenta classificou 734 negócios distintos como vencidos. Nenhum deles foi ganho depois, em momento algum do export.
3. **A tentativa de derrubar o número.** O revisor refez a conta só com o limite de 138 dias (733 negócios) e com a fronteira trocada de `<` para `<=` (717 negócios). Em nenhuma das variantes aparece um vencido ganho.

O que isso não prova também está escrito. Dos 734, 733 não foram perdidos: ficaram parados até o fim do export, e não se sabe por quê. A regra descreve este CRM com precisão, mas pode ser um padrão do gerador de dados sintéticos. Por isso o piloto mede o efeito em operação real, e `drift.py` avisa se o próximo export mudar a regra ([docs/logica.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/logica.md), seção "O que 'nenhum vencido foi ganho' prova").

### Como usar em 60 segundos

![Como usar a demo em 60 segundos](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/02-como-usar-60s.png?raw=true)

<sub>Código-fonte: [02-como-usar-60s.mmd](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/02-como-usar-60s.mmd)</sub>

Passo a passo com prints de cada tela: [docs/como-usar-a-demo.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/como-usar-a-demo.md).

![A tela de segunda-feira, em desktop](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/01-segunda-desktop.png?raw=true)

### Como o score decide

Cada negócio aberto cai em uma de quatro filas, e a ordem dentro da fila é o que vira prioridade. A ação aparece como verbo, não como nota.

| Fila | Quando o negócio cai aqui | O que o vendedor lê | Ordenada por | Negócios hoje |
|---|---|---|---|---|
| **Fechar** | vivo, com 5% ou mais de chance de decidir em 28 dias | Ligar e propor data de fechamento | valor × chance de ganhar em 28 dias | 7 |
| **Preparar** | vivo, com chance abaixo de 5% | Avançar uma etapa: próxima reunião ou proposta | valor × chance de ganhar até o fim do trimestre | 108 |
| **Iniciar** | em Prospecting, sem data de engajamento | Registrar data de engajamento e fazer o primeiro contato | valor de tabela | 500 |
| **Encerrar** | passou de 138 dias ou do fim do trimestre seguinte | Confirmar ou fechar como perdido no CRM | valor de tabela | 1.474 |

**Decidir e ganhar não são a mesma coisa.** *Decidir* é o negócio fechar, ganho ou perdido. *Ganhar* conta só o fechamento ganho. A chance de decidir separa as filas: um negócio que deve sair do lugar nas próximas quatro semanas vai para Fechar, onde vale ligar agora. Dentro de cada fila, a ordem usa o valor multiplicado pela chance de ganhar, porque, entre os negócios que vão andar, primeiro vêm os que mais valem.

**Por que isto não é ordenar por valor.** Ordenar só por preço de tabela e prazo é a melhor alternativa honesta medida no backtest, e é o que a operação faz hoje; o motor captura 1,30 vez o valor dela. Ordenar só pela chance de decidir, sem multiplicar pelo valor, é pior que o preço (razão de 0,66). O ganho vem de combinar os dois, não de trocar um pelo outro.

**Prioridade não é probabilidade.** O índice de 0 a 100 é a posição relativa do negócio entre os vivos da carteira, não a chance de ele ser ganho. A ferramenta não diz quem ganha, porque o dado não sustenta essa afirmação.

![A explicação de um negócio, com o que a ferramenta não sabe](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/screenshots/03-por-que.png?raw=true)

### Arquitetura

![Arquitetura: do CSV ao app estático](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/03-arquitetura.png?raw=true)

<sub>Código-fonte: [03-arquitetura.mmd](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/03-arquitetura.mmd)</sub>

`recortar` é a única porta de entrada do dado e apaga tudo o que é posterior à data de referência, e é a mesma função usada em produção e no backtest. O caminho crítico é determinístico: o mesmo dado gera o mesmo JSON, com o mesmo hash. A geração de briefings com IA está implementada e testada em `solution/ia/`, com validador que confere cada número contra os fatos, mas **não está ligada**: a conta da API não tem créditos e a primeira chamada real foi recusada, então todos os textos publicados vêm de template.

### Abordagem

Comecei pela procedência do dado, não pelo modelo. Um merge ingênuo do catálogo de produto derrubaria 1.480 linhas de pipeline por causa de um apelido ("GTXPro" contra "GTX Pro"), e descobrir isso na primeira tarefa evitou construir em cima de um recorte errado. Em seguida fixei a fronteira temporal numa única função, porque vazamento de futuro é o erro que mais barato se comete e mais caro se descobre.

Cada módulo do motor foi escrito com teste antes do código, e cada um foi conferido contra os valores de ouro de um protótipo rodado na fase de análise, não apenas contra os testes que eu mesmo havia escrito. Essa diferença importa: teste que passa prova consistência interna, e comparar com o protótipo prova que o resultado é o esperado. O plano tarefa a tarefa está em [process-log/planejamento/02-plano-implementacao.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/02-plano-implementacao.md), e a revisão que o reescreveu em [process-log/planejamento/03-revisao-tecnica.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/03-revisao-tecnica.md).

**O discovery foi ensaiado com quatro personas sintéticas, não conduzido com vendedores reais.** Como não tenho acesso à área comercial, construí informantes em vez de supor o que eles diriam. Parti de uma pesquisa em fontes abertas sobre a cultura comercial e o comportamento de vendedores, recortei quatro arquétipos e um líder, e montei um agente para ser entrevistado.

![Caminho do discovery, com personas sintéticas](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/04-discovery.png?raw=true)

<sub>Código-fonte: [04-discovery.mmd](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/04-discovery.mmd)</sub>

As três travas existem porque o agente foi construído sobre o mesmo dataset do desafio, e isso abre a porta para validação circular — a ferramenta confirmando a si mesma. Primeira: persona como vendedor e agente como consultor do dado rodam em conversas separadas, para a resposta de processo não vir contaminada pelo número. Segunda: o pré-registro das premissas foi commitado antes da primeira pergunta, de modo que uma confirmação posterior não pudesse ser reescrita como "eu já sabia". Terceira: nenhuma resposta virou fato, apenas premissa com teste definido.

Medi a confiabilidade do informante com perguntas cuja resposta eu já conhecia, e ele falhou em cinco delas, inventando situações vividas e acesso a dados que não tinha. Isso está registrado como categoria própria de erro. Protocolo, transcrições e calibração em [docs/discovery.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/discovery.md); a configuração do agente, com as travas, em [process-log/agente-personas-config.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/agente-personas-config.md).

**A metodologia FDE nas decisões, não no jargão**

| Princípio | O que isso virou aqui | Onde conferir |
|---|---|---|
| Número antes da tecnologia | medi quanto do pipeline está morto antes de desenhar qualquer tela | [docs/resumo-executivo.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/resumo-executivo.md) |
| Usuário e decisão operacional | a unidade é "o que eu faço na segunda-feira", não "score do lead" | [docs/operating-map.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/operating-map.md) |
| Baseline antes de confiança | três modelos sem dado na mão, mais backtest contra a regra de preço | [process-log/baseline/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/baseline), [docs/experimento.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/experimento.md) |
| Determinístico antes de agente | nenhum LLM no caminho crítico do score | `solution/motor/` |
| Verificação independente | números recalculados com código próprio, a partir dos CSVs | [process-log/verificacao/relatorio.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/verificacao/relatorio.md) |
| Explicação para adoção | cada negócio diz por que está ali e o que a ferramenta não sabe | [docs/logica.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/logica.md) |
| Piloto antes de escala | sorteio por negócio dentro do vendedor, com poder calculado | [docs/experimento.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/experimento.md) |
| Reutilizável contra específico | motor e contrato configuráveis; a regra do trimestre é deste CRM | [docs/contrato.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/contrato.md) |

### Resultados / Findings

| Medida | Definição | Baseline | Resultado | Limitação |
|---|---|---|---|---|
| Valor capturado | valor ganho pelos negócios priorizados, somando seis cortes | ordenar por preço de tabela e prazo | **1,30×**, IC 95% de 1,13 a 1,52 | vence em cinco dos seis cortes; o que sustenta a conclusão é o intervalo, não a repetição |
| Taxa de acerto | fração dos priorizados que foi ganha | 15,4% | **22,7%** | resultado offline, sobre dados históricos |
| Pipeline sem chance histórica | negócios além da janela de decisão | — | 734 distintos classificados como vencidos, **nenhum ganho** | descreve este export; 733 seguem sem decisão até o fim dele |
| Atributos como sinal | permutação de cada atributo contra o resultado real, mil vezes | p < 0,05 indicaria sinal | **nenhum atributo abaixo de 0,05** | o campo de conta só é preenchido após o desfecho, e isso vazava sinal falso para "vendedor" até ser corrigido |

A diferença entre as duas ordens equivale a US$ 1.416 por vendedor a cada quatro semanas. Esse é o valor que a ferramenta precisa não consumir em tempo de vendedor para se pagar, e a conversão em horas depende de um custo-hora que não temos, por isso o resumo executivo apresenta três cenários em vez de um número único.

### Como rodar

```bash
cd submissions/diego-rodrigues/solution
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-ia.txt
python -m pytest -q                        # 68 testes, cerca de 90 segundos
python build.py --hoje 2018-01-01          # gera app/data/ com hash determinístico
python run.py --hoje 2018-01-01 --sem-ia   # build e servidor local em http://localhost:8000
```

O segundo arquivo de requisitos instala o cliente da Anthropic, necessário apenas para os três testes do módulo de IA. Sem ele, rode o núcleo com `python -m pytest -q --ignore=tests/test_briefing.py --ignore=tests/test_gerar_ia.py --ignore=tests/test_validar.py`, que são 52 testes e não pede chave de API. Backtest, permutação, relatório de desvio e solução de problemas estão em [solution/README.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/solution/README.md).

### Recomendações

1. **Usar a fila de segunda-feira já, sem meta atrelada.** Os 115 negócios vivos estão em 17 dos 35 vendedores, e 11 deles têm mais de cinco. A lista cabe na rotina sem mudar processo nenhum, e a adoção se mede por quem volta espontaneamente na terceira ou quarta semana, não por quem abre a tela no primeiro dia.
2. **Medir antes de expandir.** O piloto sorteia negócios dentro de cada vendedor, o que faz cada um ser seu próprio controle e neutraliza a maior fonte de ruído. São cerca de 1.100 negócios por braço, aproximadamente 16 semanas, com taxa de decisão em 28 dias como métrica primária e valor ganho apenas como secundária. A regra de parada está escrita em [docs/experimento.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/experimento.md).
3. **Tratar os 500 negócios em Prospecting sem data como problema de processo, não de modelo.** São US$ 1,07 mi sobre os quais nenhuma ferramenta consegue opinar, porque não se sabe quando começaram. A correção é no registro, dentro do CRM.

### Limitações

- **O dataset é sintético e público** (CC0, Kaggle), com cerca de três trimestres de história. O ciclo de 138 dias e a regra do fim do trimestre podem ser artefato do gerador dos dados, e é por isso que `drift.py` existe: se o próximo export mudar esses números, o comando avisa em vez de a ferramenta seguir calada.
- **1.425 dos 2.089 negócios abertos não têm conta no CRM**, porque o campo só é preenchido após o desfecho. Isso descartou o atributo como sinal e também significa que boa parte do pipeline aberto não tem com que cruzar porte, setor ou histórico de relacionamento.
- **Não há registro de atividade, desconto, quantidade negociada nem motivo de perda.** O cartão "o que o score não sabe" existe para declarar essa lacuna em cada negócio.
- **O backtest é offline e não prova impacto causal.** Ele mostra concentração histórica no dataset analisado; aumento de conversão em operação real é o que o piloto mede.
- **O discovery é ensaiado com personas sintéticas.** As premissas de adoção seguem sem teste com pessoas reais, e cada premissa confirmada por uma persona continua sendo premissa.

Lista completa, incluindo ausência de login, ausência de escrita no CRM e o que falta para ligar a IA em produção: [docs/limitacoes.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/limitacoes.md).

---

## Process Log — Como usei IA

A IA foi parceira de decomposição, implementação, crítica e documentação ao longo de duas fases: um dia de planejamento, em que o plano foi escrito, revisado por três ângulos e reescrito antes de qualquer linha de código, e um dia de construção, com teste antes do código em cada módulo. As decisões comerciais, os critérios de validade, a verificação dos números e a aceitação ou recusa de cada sugestão ficaram sob julgamento humano. Dezesseis erros da IA estão registrados com o teste ou a verificação que pegou cada um. O registro completo, com a linha do tempo e o mapa das evidências, está em [process-log/README.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/README.md).

![Linha do tempo: do problema ao Pull Request](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/05-linha-do-tempo.png?raw=true)

<sub>Código-fonte: [05-linha-do-tempo.mmd](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diagramas/05-linha-do-tempo.mmd)</sub>

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| **Claude Code** — `claude-fable-5-1`, `claude-fable-5-2`, `claude-opus-5`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-sonnet-5`, `claude-sonnet-4-6`, `claude-haiku-5-5`, `claude-haiku-4-5-20251001` | Planejamento e revisão do plano (Fable, em esforço alto e extra-alto), implementação do motor com teste antes do código, telas, documentos de operação, deploy, verificação independente e este README. A troca de modelo foi feita por mim entre etapas, por custo e qualidade: Fable e Opus no que exige raciocínio ou prosa lida por humano, Haiku no que é mecânico. Inventário com versão exata e tarefa em [process-log/MODELOS.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/MODELOS.md). |
| **API da Anthropic**, `claude-haiku-5-5` — planejada e **não executada** | Geração dos textos de briefing, com limite de tokens e teto de chamadas. Implementada e testada com cliente falso; a primeira chamada real foi recusada por falta de créditos, então nenhum texto de IA foi publicado. |
| **Perplexity** | Pesquisa em fontes abertas sobre a cultura comercial e os arquétipos de vendedor, que virou insumo das personas. A síntese não entrou como fato: [process-log/fontes-cultura-g4.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/fontes-cultura-g4.md). |
| **Microsoft 365 Copilot (Premium)**, GPT Sol 6.1 | Agente com as quatro personas sintéticas do discovery, usado como informante, nunca como fonte de fato. Configuração e travas contra validação circular em [process-log/agente-personas-config.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/agente-personas-config.md). |
| **Nemotron-3.5-lightning** (via OpenRouter), **Gemini 3.1**, **ChatGPT 6.1 Sol** | Baseline sem ferramentas, antes de abrir o dado, para medir o que um modelo propõe sem nada na mão: [process-log/baseline/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/baseline). |
| **ChatGPT Sol 5.6**, em modo de raciocínio estendido | Revisão externa da entrega contra o pedido do desafio, que devolveu um plano de ajustes depois triado contra o repositório. |

### Workflow

**Fase de planejamento, antes de qualquer código.** Li o desafio e os Pull Requests já enviados, escrevi um plano com o Fable 5.1 e então pedi ao Fable 5.2, em esforço extra-alto, para atacá-lo por três ângulos: engenharia de dados, software e operação comercial. O plano v2 nasceu dessa revisão, e a análise exploratória que a acompanhou derrubou a tese inicial: eu procurava quem ganha, e o dado mostrou que isso não existe ali. A pesquisa de cultura comercial e as personas sintéticas vieram em seguida, com o pré-registro das premissas commitado antes da primeira pergunta, justamente para que uma confirmação depois não virasse "eu já sabia".

**Fase de construção, tarefa por tarefa.** Procedência e recorte temporal; janela de validade e tabela de destino aprendidas do histórico, com censura; filas, ordem e explicação por negócio; contrato JSON com hash e relatório de desvio; backtest com três medidas, intervalo de confiança por reamostragem de vendedor e permutação de atributos; briefing com validador determinístico; servidor local e três telas, corrigidas depois de eu olhar os próprios prints, não só os testes; documentos de operação citando as transcrições do discovery; deploy, verificação independente e documentação final.

Todas as iterações estão no histórico deste repositório, em 49 commits na branch `submission/diego-rodrigues`, e as conversas exportadas em [process-log/chat-exports/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/chat-exports).

### Onde a IA errou e como corrigi

Lista completa, cada item com o teste ou a verificação que o pegou: [process-log/onde-a-ia-errou.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/onde-a-ia-errou.md). Quatro que mudaram o resultado:

- A fórmula de chance de decidir contava apenas negócios já fechados e chegava a 100% aos 120 dias. Corrigida com uma tabela censurada, e fixada pelo teste `test_nao_ha_vies_de_sobrevivencia`.
- O teste de permutação dava sinal ao atributo "vendedor" por causa dos negócios sem conta: ao filtrar, o p-valor foi de 0,012 para 0,141. O campo de conta só é preenchido após o desfecho, então usá-lo era olhar o futuro.
- Uma frase do plano dizia que o que sobra vivo cabe numa lista de cinco por vendedor. Não se sustenta: 11 dos 17 vendedores com negócio vivo têm mais de cinco, e o resumo executivo foi corrigido com o número medido.
- A atribuição da regra do trimestre a um Pull Request público estava errada e não havia sido verificada. Conferi com script próprio e corrigi a atribuição.

Além desses, cinco erros são das personas sintéticas, que inventaram situações concretas e acessos a dados que não tinham. Estão registrados na mesma lista, separados dos meus, porque são de natureza diferente.

### O que eu adicionei que a IA sozinha não faria

Lista completa em [process-log/o-que-eu-acrescentei.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/o-que-eu-acrescentei.md). Em resumo: trocar a pergunta de "quem vai ganhar" para "quando este negócio decide", depois que o dado recusou a primeira; recusar o atalho de comparar com uma ordem aleatória, que mediria mistura de preço e não previsão; exigir intervalo de confiança em toda razão entre políticas, e corrigir a leitura de que o intervalo de uma razão não cruza zero, e sim um; desenhar o piloto por sorteio dentro do vendedor depois de descobrir que por região não haveria poder estatístico; manter a IA fora do caminho crítico do score, para preservar reprodutibilidade; e declarar em cada negócio o que a ferramenta não sabe, em vez de esconder a lacuna atrás de um número.

---

## Evidências

- [ ] Screenshots das conversas com IA — as conversas estão exportadas em texto, em [process-log/chat-exports/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/chat-exports); os arquivos em `process-log/screenshots/` são prints **do produto**, não de conversas
- [x] Chat exports: [process-log/chat-exports/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/chat-exports), com índice por sessão, data, modelo e etapa
- [x] Git history: 49 commits na branch `submission/diego-rodrigues`
- [x] Narrativa escrita: [process-log/diario.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diario.md), gravado por sessão, na hora
- [x] Verificação independente dos números: [process-log/verificacao/relatorio.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/verificacao/relatorio.md)
- [x] Outro: baselines de três modelos sem dado na mão, documentos de planejamento e o inventário de modelos em [process-log/MODELOS.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/MODELOS.md)
- [ ] Screen recording do workflow

---

_Submissão enviada em: 11/11/2026_
