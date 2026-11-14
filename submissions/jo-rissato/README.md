# Submissão: Jó Rissato, Challenge 002 (Redesign de Suporte)

## Sobre mim

- **Nome:** Jó Rissato
- **LinkedIn:** https://www.linkedin.com/in/jorissato
- **Challenge escolhido:** 002, Redesign de Suporte (Operações / CX)

**Protótipo no ar:** https://g4.creagle.com.br

---

## Executive Summary

O suporte não tem um gargalo por canal, prioridade ou tipo de pedido: tem um problema de processo. Nos 8.469
tickets do Dataset 1, um terço (2.819) nunca recebeu resposta, a prioridade não muda nada (692 críticos sem resposta,
p = 0,227), nenhuma variável registrada explica a satisfação e metade dos fechados (49,3%) tem tempo de resolução
impossível. Por isso a proposta não é automatizar um recorte, e sim reestruturar o atendimento inteiro: uma IA
recebe todo cliente, conduz o suporte até ele confirmar que resolveu e passa para uma pessoa só o que mexe com
dinheiro ou contrato (reembolso e cancelamento), com as métricas que hoje não existem registradas desde a primeira
mensagem. O protótipo está no ar com IA real, classificador treinado no Dataset 2 (87,0% de acerto contra 28,5% da
linha de base) e painel do time.

---

## Solução

### Abordagem

1. **Entender antes de abrir o dado.** Antes de qualquer análise, respondi às hipóteses do diretor e fiz 10
   perguntas sobre o problema (process log, rodada 1). A regra da etapa foi não olhar número até fechar a leitura.
2. **Auditar a base.** O Dataset 1 tem 8.469 tickets, não ~30 mil como diz o brief; todas as descrições trazem o
   marcador `{product_purchased}` e o texto de resolução não tem sentido. Cada achado saiu com a base (n) declarada.
3. **Testar os três diagnósticos do brief contra o acaso**: qui-quadrado com V de Cramér, teste de permutação com
   1.000 embaralhamentos, correção de Bonferroni e modelos contra linha de base.
4. **Responder às 6 perguntas de negócio** com as minhas palavras e conferir cada resposta contra o dado. Onde a
   minha frase não se sustentava ("o tempo de resolução subiu"), ela foi ajustada antes de ser salva.
5. **Medir o classificador no Dataset 2** com treino e teste separados antes de qualquer treino e comparar 4
   modelos por validação cruzada.
6. **Construir, usar e corrigir.** O protótipo foi para o ar no primeiro dia. Eu li as conversas, apontei os erros
   chamada por chamada e cada correção virou teste automatizado e rodada de bateria com a IA real.

### Resultados

**1. Onde o fluxo trava** ([diagnóstico](docs/relatorio-diagnostico-base-completa.md), [combinações](docs/relatorio-combinacoes.md))

| Status | Tickets | % |
|---|---|---|
| Sem nenhuma resposta | 2.819 | 33,3% |
| Respondido, aguardando o cliente | 2.881 | 34,0% |
| Fechado | 2.769 | 32,7% |

- Nenhuma das 8 variáveis explica o status (menor p = 0,073; V de Cramér até 0,067). Um modelo com todas juntas
  acerta 34,2% contra 34,0% da linha de base.
- Nenhuma combinação de canal, prioridade e tipo é pior que o acaso, nem em tempo (n = 1.404) nem em falta de
  resposta (n = 8.469), depois da correção para testes múltiplos.
- Responder não é resolver: dos 5.650 tickets que receberam a 1ª resposta, só 49,0% fecharam.

**2. O que impacta a satisfação** ([relatório](docs/relatorio-satisfacao.md))

- Nada do que está registrado. As 2.769 notas se distribuem como sorteio (cerca de 20% cada, p = 0,797); nenhum dos
  15 testes passa da correção; nenhum modelo supera a linha de base.
- 67,3% dos tickets não têm nota, porque a nota só existe no fechamento.

**3. Quanto estamos desperdiçando** ([relatório](docs/relatorio-desperdicio.md))

| Desperdício | Tamanho | Base |
|---|---|---|
| Demanda sem nenhuma resposta | 2.819 tickets (33,3%), 692 críticos | 8.469 |
| Registro de tempo inútil para gestão | 1.365 fechados (49,3%) | 2.769 |
| Cauda de tempo | 25% dos tickets somam 51,7% das 10.639 h | 1.404 |
| Satisfação não coletada | 5.700 tickets (67,3%) | 8.469 |

O custo em reais não foi estimado: o dado não tem custo da hora, número de atendentes nem tempo trabalhado
([12 lacunas de dado](docs/lacunas-de-dado.md)). A fórmula fica pronta para quando o dado existir.

**4. Classificador de assunto** ([relatório](docs/relatorio-classificador.md))

- Regressão logística com peso por categoria, escolhida entre 4 modelos: **87,0% de acerto** no teste de 9.568
  textos nunca vistos (linha de base 28,5%), F1 entre 79,7% e 92,0% nas 8 categorias.
- Com limite de confiança de 0,8 (minha decisão), a IA marca 68,4% dos tickets com 96,4% de acerto.

**5. Proposta de automação** ([fluxo](docs/fluxo-proposto.md))

| Automatiza | Não automatiza (pessoa decide e executa) |
|---|---|
| Recepção de todo cliente, em qualquer canal, com data e hora de abertura | Reembolso, cancelamento e alteração ou estorno de cobrança |
| Suporte completo: perguntas específicas, solução em passos e confirmação | Atendimento quando a IA está fora do ar |
| Defeito de aparelho: passos de verificação e indicação da assistência autorizada mais perto | |
| Coleta do detalhe do pedido e do contato para o time, validada no código | |
| Assunto de cada chamada e métricas para o dashboard | |

O critério de não automatizar reembolso e cancelamento é julgamento, não achado do dado: é ação irreversível sobre
dinheiro e contrato. Esses dois tipos somam 3.447 tickets (40,7%) do Dataset 1.

**6. Protótipo** ([como rodar](solution/prototipo/LEIAME.md))

- **Conversa:** a IA (DeepSeek) atende em português até o cliente confirmar que resolveu. Nome, CPF, telefone,
  e-mail e CEP nunca vão para a IA externa: o código troca por marcadores e coleta com mensagens fixas.
- **Painel do atendente:** toda conversa vira chamada com ID desde a primeira mensagem, com motivo da decisão,
  situação e dados mascarados.
- **Dashboard:** a operação de hoje (Dataset 1, com filtros), o classificador rodando sobre os 9.568 tickets reais
  do teste e as chamadas do próprio protótipo.
- **Validação:** 124 testes automatizados; bateria de 17 conversas com cliente simulado pela IA, refeita a cada
  mudança. Na última rodada (`docs/bateria-ia-rodada64.md`), 15 de 17 passaram: uma falha foi falso alarme da própria
  checagem e a outra, um diagnóstico de Excel que não fechou dentro do limite de 14 trocas. 6 h no ar sob medição contínua (73 de 73 checagens com sucesso,
  memória plana); teto de gasto de 40 mil tokens por conversa e 600 mil por dia.

### Recomendações

1. **Primeiro, medir.** Registrar data e hora de abertura, atendente, tempo trabalhado, custo da hora, reabertura e
   nota em todo ticket, não só no fechado. Sem isso não existe linha de base para nenhuma promessa.
2. **Ligar a recepção por IA em todo canal**, com a regra do protótipo: IA conduz até resolver; reembolso e
   cancelamento vão para uma pessoa com o pedido e o contato já coletados.
3. **Revisar por amostragem nos primeiros 30 dias** e comparar com a linha de base que o dado já dá: 33,3% sem
   resposta, 692 críticos sem resposta, 49,0% dos respondidos fechados, 32,7% com nota.
4. **Depois de 30 dias**, decidir com histórico e métricas se reembolso ou cancelamento podem ganhar automação,
   conforme as APIs dos sistemas da empresa.
5. **Levantar o processo com o time** (equipes, sistemas, base de conhecimento interna) e treinar o time para a nova
   divisão de trabalho.

### Limitações

- O Dataset 1 tem marcas de dado gerado; os achados valem para esta base e precisam ser repetidos com dado real.
- Não foi possível medir tempo até a 1ª resposta, tendência no tempo nem custo (lacunas 3, 4, 5 e 11).
- O classificador é de TI interna (Dataset 2). Não há chave entre os dois datasets, então o acerto nos tipos do
  Dataset 1 não foi medido.
- A conversa foi testada com cliente simulado pela IA, não com clientes reais.
- A IA só dá passos de ajuda oficial de sistemas e aparelhos conhecidos; procedimento interno da empresa depende de
  uma base de conhecimento que não existe nos dados. Ela não lê print (imagem pode trazer dado pessoal).
- A rede de assistências e o cadastro de clientes do protótipo são **de exemplo**, fictícios; "mais perto" é o maior
  começo de CEP igual, não distância em quilômetros.

---

## Process Log: como usei IA

O registro completo, em ordem cronológica e com horário, está em
[`process-log/01-entendimento-do-problema.md`](process-log/01-entendimento-do-problema.md): cada pedido meu está
literal, seguido do que a IA fez, do que foi conferido e do que eu decidi.

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code (Claude Opus) | Análise estatística, conferência das minhas respostas contra o dado, construção do protótipo, testes e documentação |
| DeepSeek (API) | A IA que conversa com o cliente dentro do protótipo e o cliente simulado da bateria de testes |
| scikit-learn | Classificador de assunto (TF-IDF + regressão logística) |
| Streamlit + Cloudflare Tunnel | Página do protótipo no ar em endereço fixo |

### Workflow

1. Li o brief e fiz minhas 10 perguntas antes de ver o dado (rodada 1).
2. Pedi ao Claude a auditoria das bases; ele levantou as divergências (8.469 contra ~30 mil, marcador
   `{product_purchased}`, tempo negativo).
3. Os diagnósticos do brief foram testados contra o acaso, e cada número saiu com a sua base.
4. Respondi às 6 perguntas de negócio com as minhas palavras. O Claude conferia cada resposta contra o dado e
   propunha ajuste; eu aprovava ou não. Seis respostas, seis ajustes aprovados (rodadas 30 a 41).
5. Classificador: escolhi o limite de confiança de 0,8 depois de ver a troca entre cobertura e acerto (rodada 45).
6. Aprovei o fluxo de 9 etapas e acrescentei a recepção conversacional (rodadas 47 e 48).
7. Protótipo no ar, eu testando como cliente. A cada rodada eu apontava os erros por chamada e o Claude corrigia,
   criava teste e rodava a bateria com a IA real (rodadas 51 a 61 e as seguintes, mais de 60 rodadas ao todo).

### Onde a IA errou e como corrigi

- **Falso achado de satisfação:** o texto da descrição parecia prever a nota (p = 0,002). Na conferência, o
  vocabulário tinha sido aprendido com a base inteira, inclusive com o teste. Sem o vazamento, p = 0,05, que não
  resiste à correção. Depois disso, todo modelo passou a ter o vetorizador dentro da validação.
- **Afirmação sem dado na minha própria resposta:** "o tempo de resolução subiu" saiu da resposta, porque o dado não
  tem série no tempo.
- **Robô que só encaminhava:** a primeira versão classificava e mandava para a fila. Ao ler as conversas, decidi que
  a IA atende até resolver e só reembolso e cancelamento passam para o time (rodada 59).
- **Atendimento que mandava o cliente ao fabricante:** o notebook com defeito ficava num laço de despedidas. Defini
  que defeito de aparelho vai para a assistência autorizada da empresa (rodada 60) e, depois, que deve ser a mais
  perto do endereço do cliente, confirmado com ele.
- **Suporte que começava pelo difícil:** no Outlook travado, a IA levou 14 respostas e 30 mil tokens. Com a regra de
  começar pelas verificações simples, caiu para 5 respostas. A mudança mandou a impressora com erro na fila para a
  assistência; o critério foi corrigido e conferido de novo.
- **Problemas de operação pegos na régua:** conversas perdidas com várias pessoas ao mesmo tempo (gravação
  corrigida com trava), máscara do CPF quebrada no painel, falsos alarmes na própria bateria de testes.

### O que eu adicionei que a IA sozinha não faria

- A leitura de que o problema é de processo, e que sobrecarga, tempo e satisfação são consequência.
- A fronteira da automação: ação irreversível sobre dinheiro ou contrato fica com pessoa, e o resto a IA resolve.
- O limite de confiança de 0,8 e a recepção conversacional, para o cliente explicar melhor antes de ser classificado.
- A regra de que dado pessoal nunca vai para IA estrangeira, aplicada no código.
- Os critérios de atendimento que só aparecem usando: perguntas específicas sem frase de cortesia vazia, pedir o
  pedido exato no reembolso e o valor na cobrança em dobro, assistência mais perto com confirmação do endereço.
- A métrica de 30 dias comparada com a linha de base que o próprio dado dá, sem meta inventada.

---

## Evidências

- [x] Narrativa escrita com cada pedido literal e horário: `process-log/01-entendimento-do-problema.md`
- [x] Git history: commits da branch `submission/jo-rissato`
- [x] Baterias de teste com a IA real: `docs/bateria-ia-*.md`
- [x] Régua de validação do protótipo: `docs/regua-validacao-prototipo.md`
- [x] Protótipo no ar: https://g4.creagle.com.br

## Estrutura

```
submissions/jo-rissato/
├── README.md
├── docs/                 relatórios, fluxo, lacunas, respostas, baterias e régua
├── process-log/          registro cronológico das rodadas
└── solution/
    ├── analise/          scripts do diagnóstico e do classificador
    └── prototipo/        conversa, roteador, painel e dashboard (LEIAME com o setup)
```

---

_Submissão enviada em: 14/11/2026_
