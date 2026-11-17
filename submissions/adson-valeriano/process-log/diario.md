# Diário do processo

## 16/11 – 23h00 | Escolha do desafio e setup
- Li os 4 desafios e escolhi o 002 (Redesign de Suporte). Trabalho com suporte e
  automação no dia a dia (Skill-Hub: agentes de IA, WhatsApp, CRMs), então é onde
  meu contexto real pode fazer diferença em relação a uma resposta genérica de IA.
- Fiz fork, clone e criei a branch submission/adson-valeriano. Montei a estrutura
  de pastas que o CONTRIBUTING pede.
- Baixei os dois datasets do Kaggle para datasets/ (fica fora do repositório pelo .gitignore).
- Percebi que o .gitignore também ignora submissions/. Se eu desse git add normal, o PR
  ia vazio. Resolvi com git add -f na minha pasta.

## 17/11 – 00h20 | Primeira leitura dos dados
- Antes de pedir qualquer análise, abri alguns tickets para ver o dado com meus olhos.
- Pedi ao Claude uma checagem de qualidade antes de qualquer conclusão.
- No dataset 1 (suporte), apareceram vários sinais de problema:
  - São 8.469 tickets, não ~30 mil como o README sugere.
  - "First Response Time" e "Time to Resolution" são data/hora, não duração.
  - Todas as primeiras respostas aconteceram em ~27 horas (31/05 a 02/06/2023).
  - Em 49% dos tickets fechados, a resolução acontece ANTES da primeira resposta. Impossível.
  - A satisfação tem quantidades quase iguais de 1 a 5 (~550 cada). Na vida real a nota
    não se distribui assim.
  - 100% das descrições têm o texto modelo "{product_purchased}" sem preencher, e as
    resoluções são frases sem sentido.
  - Só 33% dos tickets (os fechados) têm tempo e nota.

## 17/11 – 00h30 | Análise das 3 perguntas do diretor
- Pedi ao Claude para responder as 3 perguntas com base nos dois CSVs.
- Dataset 1: testei canal, tipo e prioridade contra status e satisfação. Tudo igual
  (~25% por canal, ~20% por tipo, satisfação ~3 em tudo). ANOVA sem diferença
  significativa (p entre 0,28 e 0,70). Correlação tempo x satisfação = 0,02.
  → Conclusão: o dado não permite dizer onde se perde tempo. Isso vira achado: a empresa
  não mede direito o que importa.
- Único sinal operacional aproveitável: 1/3 dos tickets está parado em "Pending Customer
  Response". É exatamente o tipo de situação que eu resolvo no trabalho com follow-up
  automático.
- Dataset 2 (TI, 47.837 tickets reais em 8 categorias): treinamos um classificador
  (TF-IDF + regressão logística), separando 20% para teste (9.568 tickets que o modelo
  nunca viu).
  - Acurácia de 86,6% (chutar sempre "Hardware" acertaria 28,5%).
  - Usando a confiança do modelo como regra: com confiança mínima de 70%, a IA cuida
    sozinha de 72% dos tickets com 95,6% de acerto. O resto vai para triagem humana.
  - Pior categoria: Direitos administrativos (precisão 77%). Por ser tema de segurança,
    decidi que fica sempre com humano.

## 17/11 – 00h35 | Desconfiei e pedi uma segunda varredura atrás de pegadinhas
- Minha suspeita: o desafio foi montado para quem cola o brief na IA, recebe uma análise
  superficial e acredita. Pedi ao Claude para procurar armadilhas de propósito.
- Confirmou mais sinais de dado sintético no dataset 1: 69% dos textos começam com a
  mesma frase (só 16 aberturas diferentes), e-mails de domínios de teste (example.com),
  gênero dividido exatamente em 1/3, compras de 2020–21 e tickets todos de 2023.
- A pegadinha mais importante foi no cruzamento. O README diz que "o poder está no
  cruzamento", mas os dois datasets são de mundos diferentes: o 1 é suporte ao cliente
  (cobrança, reembolso, produto) e o 2 é service desk interno de TI (hardware, RH, acesso).
  Testamos aplicar o classificador do dataset 2 nos tickets do dataset 1:
  - 73% viraram "Hardware", inclusive reembolso e cobrança;
  - confiança média caiu para 60%, só 28,5% acima do limite de 70%;
  - a distribuição foi igual para qualquer tipo de ticket → o modelo não entende aquele suporte.
- Outros pontos que achamos no dataset 2: o texto já vem pré-processado (sem números
  nem pontuação); as palavras mais comuns são de assinatura de e-mail ("please",
  "regards", "pm", "tuesday"); os textos terminam com o cargo de quem escreveu, então o
  modelo pode estar aprendendo pelo cargo e não pelo problema; está tudo em inglês;
  as categorias são desiguais (Hardware 13.617 x Direitos administrativos 1.760) e
  existe uma categoria "lixeira" (Miscellaneous).

  ## 17/11 – 00h45 | Formalizei o entendimento
- Escrevi o 00-raciocínio.md com as 3 hipóteses que vêm da minha experiência na Skill-Hub.
  Elas já guiavam o que eu pedi para testar, mas só formalizei agora, depois da primeira
  leitura dos dados. Registro isso para ficar transparente.

## Onde a IA errou e como corrigi
- Na primeira análise, o Claude apresentou "72% automatizados com 95,6% de acerto, ~90 h/mês
  economizadas" como se valesse para o suporte da empresa. Quando pedi a segunda
  varredura, ficou claro que esse número vale para o tipo de ticket do dataset 2. Aplicado
  ao dataset 1, o modelo não funciona.
- Corrigi a forma de apresentar: a técnica está provada no dataset 2; para o suporte da
  empresa, é preciso treinar com os tickets dela, rotulados com as categorias dela. O
  ROI vira estimativa a confirmar em piloto, não promessa.

  ## Por que essas escolhas técnicas
- Checagem de qualidade antes de tudo: se o dado está errado, qualquer conclusão está errada.
- ANOVA na satisfação: é o teste para saber se a diferença entre vários grupos (ex.: 4 canais)
  é real ou se é acaso. Deu que é acaso.
- Classificador simples (TF-IDF + regressão logística) em vez de algo mais sofisticado:**
  é rápido, barato e explicável, e serve de base. Se já resolve bem (86,6%), não preciso
  começar com algo mais caro.
- 20% dos dados separados para teste: testar o modelo em chamados que ele nunca viu,
  para o número de acerto ser honesto.
- Limite de confiança de 70%: é decisão de negócio. Equilibra o quanto a IA assume
  sozinha (72%) com o quanto ela erra (4,4%).

## Decisões minhas até aqui
- Não vou tirar conclusões de ruído (ex.: "chat tem a melhor nota, 3,08"). Vou mostrar
  por que o dado não sustenta isso.
- O diagnóstico vai ser honesto: o que dá para afirmar, o que não dá, e o que a empresa
  precisa começar a medir.
- O peso técnico da entrega vai para o dataset 2: classificador com limite de confiança
  e regras do que sempre vai para humano (crítico, dinheiro, acesso/permissões,
  confiança baixa).
- O cruzamento certo: dataset 1 mostra o que está quebrado na operação e as categorias
  de negócio; dataset 2 prova a técnica e os limites dela.
- [Escreva aqui com as suas palavras por que você concorda ou discorda de alguma decisão]

## Próximos passos
- Montar o protótipo: ticket entra → classificação com confiança → regras de passagem
  para humano → tickets parecidos (RAG) → sugestão de encaminhamento.
- Escrever a entrega no template e preparar a defesa.