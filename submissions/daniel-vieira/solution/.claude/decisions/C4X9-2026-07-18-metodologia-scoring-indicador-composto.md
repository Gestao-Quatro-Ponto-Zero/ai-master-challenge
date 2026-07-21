---
id: C4X9
project: LeadScorer
subject: Metodologia de scoring: indicador composto com portão e média geométrica
author: dcvr@
status: accepted
created: 2026-07-18
updated: 2026-07-19
---


# Contexto (por que a decisão é necessária)

O modelo de scoring deve ser defensável e explicável. A análise exploratória (1J8R) estabeleceu
que a conversão Won/Lost é praticamente invariante nos atributos observáveis, de modo que um
classificador de probabilidade de ganho não tem sinal a aprender. A escolha do método de
composição, de normalização, de ponderação e de validação afeta materialmente o resultado e é
difícil de reverter, o que exige o seu registro. Consultaram-se, como fontes primárias, o Handbook
on Constructing Composite Indicators (OECD/JRC, 2008), Kaplan e Meier (1958), Schmittlein, Morrison
e Colombo (1987), Fader, Hardie e Lee (2005) e Saisana, Saltelli e Tarantola (2005). A formalização
e as cautelas residem em 'docs/metodologia-scoring.md'.


# Decisão (o que foi decidido)

Adota-se um indicador composto sobre a tripla produto-empresa-agente, com quatro dimensões ativas
(retorno, afinidade, momentum e especialização) normalizadas por percentil e ponderadas por
pesos arbitrados e documentados. A agregação é um portão de elegibilidade não compensatório
seguido de uma média geométrica ponderada das quatro dimensões, todas em 0-100, com o maior peso
no momentum; a média geométrica penaliza o desequilíbrio e um momentum 0 zera o índice, o
afundamento do par recém-fechado. O decaimento do momentum usa uma CCDF empírica como proxy
transparente. O sistema expõe duas listas e carrega duas dimensões inertes com peso zero, por
completude. A validação é por robustez, não por acurácia preditiva. Os valores concretos residem
no código e na configuração da implementação.

A forma de agregação foi revista na Fase 5: a forma inicial, uma base aditiva multiplicada por um
fator de momentum em [0,1], tornava o momentum dominante por artefato de escala e era apenas
moderadamente robusta à normalização. A validação por sensibilidade confirmou que a média
geométrica ponderada reequilibra as dimensões de valor e é substancialmente mais robusta;
a evidência reside em 'docs/validacao-scoring.md'.


# Alternativas consideradas (o que mais foi ponderado)

- Classificador de probabilidade de ganho treinado: rejeitado, pois a EDA mostra ausência de
  sinal discriminativo nos atributos observáveis;
- Composto puramente aditivo: rejeitado, pois a compensabilidade total permitiria que valor ou
  especialização compensassem um momentum ruim, e a exigência de que um par recém-fechado afunde
  requer não-compensabilidade;
- Base aditiva multiplicada por um fator de momentum em [0,1], a forma inicial: substituída pela
  média geométrica após a validação da Fase 5 revelar que ela tornava o momentum dominante por
  artefato de escala e era apenas moderadamente robusta à normalização;
- Normalização min-max como método primário: rejeitada pela sensibilidade a outliers dada a cauda
  do 'close_value'; mantida apenas como comparação de sensibilidade;
- Kaplan-Meier, Pareto/NBD ou BG/NBD: diferidos, pois, embora rigorosos, a janela de cerca de dez
  meses, a censura à direita e a matriz saturada com frequência de repetição próxima de um colocam
  os dados no regime degenerado desses modelos; os proxies empíricos transparentes bastam ao MVP,
  com a ressalva de censura documentada;
- Agregação multicritério não-compensatória (Condorcet ou Borda): rejeitada para o MVP pela
  inexistência de regra de agregação perfeita (Arrow e Raynaud, 1986) e pelo custo computacional;
  a média geométrica fornece a não-compensabilidade necessária de modo mais simples.


# Consequências (o que resulta da decisão)

- O indicador é transparente e explicável pela decomposição por dimensão, alinhado à valorização
  da transparência pelo desafio;
- Demonstra-se o método sob sinal fraco; os valores concretos residem no código e na configuração,
  não neste registro;
- Duas dimensões são inertes nesta base e carregadas por completude, com peso zero;
- A validação da Fase 5 confirmou a média geométrica como robusta à normalização e o momentum como
  eixo primário, com as dimensões de valor contribuindo; a dimensão de retorno contribui pouco para
  a ordenação fina por ter apenas sete níveis, uma limitação do dado, e a ordenação fina entre os
  pares maduros é sensível aos pesos arbitrados, o que se documenta;
- A validação estabelece robustez, não acurácia, o que é uma limitação documentada;
- A decisão complementa o ADR B7Q3 (realinhamento de escopo) e apoia-se na fonte normalizada do
  ADR F3N8 e na persistência faseada do ADR D2K9.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 3RJ8
