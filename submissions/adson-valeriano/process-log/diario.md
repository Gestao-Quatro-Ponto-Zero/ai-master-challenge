# Diário do processo

## 16/11 – 23h00 | Escolha do desafio e setup
- Li os 4 desafios e escolhi o 002 (Redesign de Suporte). Trabalho com suporte e automação no dia a dia
  (Skill-Hub: agentes de IA, WhatsApp, CRMs), então é onde o meu contexto real pode fazer diferença em
  relação a uma resposta genérica de IA.
- Fiz fork, clone e criei a branch `submission/adson-valeriano`, com a estrutura de pastas do CONTRIBUTING.
- Baixei os dois datasets do Kaggle para `datasets/` (fica fora do repositório pelo .gitignore).
- Percebi que o .gitignore também ignora `submissions/`. Com `git add` normal, o PR iria vazio.
  Resolvi com `git add -f` na minha pasta.
- Tive problema com um arquivo salvo fora do repositório e outro que subiu vazio. Aprendi a conferir com
  `git status`, `git ls-files` e `git show --stat` antes de considerar algo entregue.

## 17/11 – 00h11 | Entender o problema antes de analisar
- Antes de qualquer análise, pedi clareza sobre o que o diretor pediu e onde estava a especificação.
- Resumo: onde se perde tempo, o que automatizar (e o que não), e algo rodando.

## 17/11 – 00h20 | Primeira leitura dos dados
- Abri alguns tickets para ver o dado com meus próprios olhos.
- Pedi ao Claude uma checagem de qualidade antes de qualquer conclusão. No dataset 1 (suporte):
  - São 8.469 tickets, não ~30 mil como o README sugere.
  - "First Response Time" e "Time to Resolution" são data/hora, não duração.
  - Todas as primeiras respostas cabem em ~27 horas (31/05 a 02/06/2023).
  - Em 49% dos tickets fechados, a resolução acontece antes da primeira resposta. Impossível.
  - A satisfação tem quantidades quase iguais de 1 a 5 (~550 cada).
  - 100% das descrições têm o texto-modelo "{product_purchased}" sem preencher; resoluções sem sentido.
  - Só 33% dos tickets (os fechados) têm tempo e nota.

## 17/11 – 00h24 | Análise das 3 perguntas do diretor
- Dataset 1: canal, tipo e prioridade contra status e satisfação deram tudo igual. ANOVA sem diferença
  significativa (p entre 0,28 e 0,70); correlação tempo x satisfação = 0,02.
  → O dado não permite dizer onde se perde tempo. Isso vira achado: a empresa não mede o que importa.
- Único sinal aproveitável: 1/3 dos tickets parado em "Pending Customer Response".
- Dataset 2 (TI, 47.837 tickets em 8 categorias): classificador TF-IDF + regressão logística, testado em
  9.568 tickets nunca vistos. Acurácia de 86,6%. Com confiança mínima de 70%, a IA cuida sozinha de 72%
  dos tickets com 95,6% de acerto.
- Pior categoria: Administrative rights (precisão 77%). Por ser tema de segurança, decidi que fica sempre
  com humano.

## 17/11 – 00h30 | Segunda varredura: procurar pegadinhas de propósito
- Minha suspeita: o desafio foi montado para quem cola o brief na IA e acredita na primeira resposta.
  Pedi ao Claude para procurar armadilhas de propósito.
- Mais sinais de dado sintético no dataset 1: 69% dos textos começam com a mesma frase (16 aberturas no
  total), e-mails de domínios de teste, gênero dividido exatamente em 1/3.
- Pegadinha principal, no cruzamento: os datasets são de mundos diferentes (suporte ao cliente x service
  desk de TI). Aplicando o modelo do dataset 2 no dataset 1, 74% viram "Hardware", inclusive reembolso e
  cobrança, e a confiança média cai para 55%. O modelo não transfere.
- No dataset 2: texto pré-processado, palavras de assinatura dominando, cargo no fim do texto, tudo em
  inglês, categorias desiguais e uma categoria "lixeira" (Miscellaneous).

## 17/11 – 00h45 | Raciocínio e checagem de coerência
- Escrevi o `docs/00-raciocinio.md` com as 3 hipóteses que vêm da minha experiência na Skill-Hub. Elas já
  guiavam o que eu pedi para testar, mas só formalizei depois da primeira leitura dos dados.
- Pedi uma revisão cruzada entre raciocínio e diário para garantir que a linha lógica fechasse. Duas
  incoerências foram corrigidas: a ordem no tempo das hipóteses e a parte "cair com a pessoa errada" da
  hipótese 3, que liguei ao roteamento do protótipo.

## Por que essas escolhas técnicas
- **Checagem de qualidade antes de tudo:** se o dado está errado, qualquer conclusão está errada.
- **ANOVA na satisfação:** é o teste para saber se a diferença entre vários grupos é real ou acaso.
- **Classificador simples (TF-IDF + regressão logística):** rápido, barato e explicável. Se já resolve bem,
  não preciso começar com algo mais caro.
- **20% dos dados separados para teste:** medir em chamados que o modelo nunca viu.
- **Limiar de confiança de 70%:** decisão de negócio. Equilibra o quanto a IA assume (72%) com o quanto
  ela erra (4,4%).

## 17/11 – 08h50 | Protótipo
- Pedi ao Claude o código do protótipo com as regras que eu defini: classificação com confiança, passagem
  para humano (crítico, dinheiro, segurança, permissões, confiança baixa) e busca de tickets parecidos.
- Rodei e testei na minha máquina. No teste em lote, vi a IA errar em tickets de confiança baixa e esses
  tickets irem para humano: o limiar segurando o erro antes do cliente.
- Vi também um caso de confiança alta discutível: "acesso à pasta do drive compartilhado" classificado
  como Storage com 100%. Confiança alta não é garantia de acerto, então o piloto em paralelo é necessário.

## 17/11 – 09h25 | Interface para o executivo
- Defini que a tela precisava ser clara para um executivo decidir em segundos: português com o termo
  original entre parênteses, sem emojis, decisão e motivo em destaque, fluxo em 3 passos no topo.
- Questionei o valor da lateral. Mantive o que responde "funciona?" e "é seguro?" e troquei o aviso técnico
  por "próximo passo".
- Cobrei de onde vinham os "tickets reais". Corrigimos para "chamados de TI de um dataset público (Kaggle)".

## 17/11 – 09h53 | Terceira revisão: subpegadinha
- Perguntei se o desafio não teria uma "subpegadinha" para quem achasse a primeira.
- Testamos vazamento entre treino e teste (não há: sem os 6% de "gêmeos", o acerto segue 86,0%) e atalho
  pela assinatura (não há: sem as últimas palavras, 86,1%).
- Achamos uma contradição na minha própria conta: o ROI assumia 72% de automação, mas as minhas regras
  mandam dinheiro para humano, e isso é 60% do volume de suporte. Reescrevi como faixa (36 a 90 h/mês) e
  separei "IA encaminhar" de "IA decidir".

## 17/11 – 11h20 a 13h00 | Revisão depois do PR
- Depois de abrir o PR, pedi uma avaliação honesta do que ficou fraco. Os pontos: o desperdício não estava
  em reais, as regras de passagem para humano nunca tinham sido testadas com números e o protótipo não usava
  IA generativa.
- **Custo em reais:** usei como premissa o custo empresa de um operador de suporte técnico (R$ 3.440/mês,
  Portal Salário 2026), ou seja, R$ 15,64/hora. A economia direta de triagem fica entre R$ 5.900 e
  R$ 14.700 por ano. É modesta, e escrevi isso: o valor principal é velocidade de encaminhamento.
- **Teste das regras:** no dataset de TI, as regras tiram 9 pontos de automação (de 71,7% para 62,8%) e
  mantêm o acerto em 95,8%. O "72%" que eu vinha usando era só o limiar, sem as regras. Corrigi README,
  protótipo, resumo e ROI.
- No dataset de suporte, a regra de dinheiro por palavra-chave pega só 7,4% dos chamados de dinheiro (a
  mesma taxa dos outros), porque o texto ali não tem relação com o tipo. Conclusão: em produção, a regra
  deve usar o campo estruturado do chamado.
- **Resumo executivo de 1 página** para o diretor ler em 5 minutos.
- **Comparação com LLM:** montei um script que classifica uma amostra com o Gemini (zero-shot) e compara
  acerto, tempo e custo com o modelo simples.

## 17/11 – 13h00 a 15h30 | Usar a ferramenta e pensar como o executivo
- Para entender a ferramenta por dentro, pedi ao Claude um roteiro de testes práticos no protótipo (casos
  fáceis, ambíguos, sensíveis e em português) e fui repetindo na minha máquina. Dois achados: a IA confunde compra de
  monitor com Hardware (43% de certeza, então foi para atendente) e não serve para português (um pedido
  de acesso em português virou "Permissões administrativas" com 24%). Os dois reforçam o piloto com
  dados reais da empresa.
- Me coloquei no lugar do diretor: "qual era o problema, quanto melhora, e aí?". A economia direta é
  modesta, então acrescentei ao resumo as metas do piloto: como vou provar o valor em 30 dias.
- Acrescentei ao protótipo o envio de planilha, para um gestor testar com os próprios chamados.

## 17/11 – 15h30 | Comparação com LLM (Gemini)
- Rodei o `comparar_llm.py` na minha máquina com a minha chave do Gemini.
- O primeiro modelo do script (`gemini-2.5-flash`) não estava mais disponível (erro 404). Listei os modelos
  da minha conta e testei outros: `gemini-3.8-flash` e `gemini-3.5-flash` estavam sobrecarregados (erro 503).
  Funcionou com `gemini-3.5-flash-lite`. Pedi ao Claude para corrigir o script, que escrevia "ok" mesmo
  quando um lote falhava.
- Resultado nos mesmos 200 tickets de teste: modelo simples 92,5% x LLM zero-shot 48,0%.
- Minha leitura: o LLM não conhece a convenção de categorias desta empresa; o modelo treinado aprendeu
  com 38 mil exemplos. Para classificar com a taxonomia da empresa, o modelo simples ganha em acerto,
  tempo e custo. O LLM fica para gerar resposta sugerida ou para um teste com exemplos (few-shot).

## Onde a IA errou e como corrigi
- **ROI aplicado ao lugar errado:** a primeira análise apresentou o ROI do dataset de TI como se valesse
  para o suporte da empresa. A segunda varredura mostrou que o modelo não transfere.
- **ROI contra as próprias regras:** a terceira revisão mostrou que a conta ignorava os 60% de chamados de
  dinheiro que as regras mandam para humano.
- **Números da conversa x números dos scripts:** com o pré-processamento do protótipo, alguns números
  mudaram (confiança média de 60% para 55%). Passei a usar só os números gerados pelos scripts.
- **"Tickets reais":** afirmação imprecisa, corrigida para "dataset público do Kaggle".
- **Cobertura sem as regras:** o "72% automatizado" ignorava as regras de passagem para humano. Com elas
  ligadas, são 62,8%.

## Decisões minhas
- Não tirar conclusão de ruído (ex.: "chat tem a melhor nota, 3,08").
- Diagnóstico honesto: o que dá para afirmar, o que não dá e o que a empresa precisa começar a medir.
- Peso técnico no dataset 2, com regras claras do que sempre vai para humano.
- Piloto com os dados da própria empresa antes de ligar a automação. ROI como estimativa, não promessa.
