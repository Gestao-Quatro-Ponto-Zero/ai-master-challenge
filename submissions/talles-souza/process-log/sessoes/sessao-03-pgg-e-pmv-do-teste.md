# Sessão 03 — O próprio teste como projeto: PGG e PMV antes de construir

**Data:** 2026-10-22 · **Ferramentas:** Claude Code (Claude Opus 5.5) como coordenador, subagentes de uma esteira de diagnóstico, worker do Orca · **Etapa:** entre a E2 e a E3

## Problema

A E2 mostrou que o score óbvio seria ruído (sessão 02). Em vez de partir direto para o código, eu parei e pedi: *"precisamos fazer um PGG do desafio com um PMV"*. O teste em si virou um projeto: o objetivo escrito nos 4Cs (PGG, Projeto Ganha-Ganha) e o plano nos 8Rs (PMV, Plano Mínimo Viável), ambos do livro *Inteligência Pragmática* (Max Peters).

**Critério de aceite desta etapa:** o PGG do teste escrito no template do livro, revisado por um revisor adversarial até passar, com cada número com fonte e cada lacuna virando pergunta para mim.

## O que foi feito, em ordem

1. **Esteira de diagnóstico própria.** Uso uma esteira minha de diagnóstico de negócio (fases f0 a f4, cada uma com um executor e o portão de um revisor adversarial, com laço de até 3 voltas antes de escalar para mim; com ordem minha, a volta segue). Abri um caso novo para o teste, separado da preparação da vaga, em modo "problema", nível de análise 2 (tabela de alternativas), modo interativo e escopo f0–f4.
2. **f0, Qualificar.** O executor escreveu a qualificação, o briefing e o PGG inicial, e já conferiu fatos externos:
   - a vaga continua aberta, sem prazo publicado;
   - o repositório oficial tinha 209 PRs, ≥ 95 deles de Lead Scorer: é o desafio mais escolhido, o que aumenta a pressão para fugir do baseline;
   - um backtest da regra "fora da janela": no corte de 30/09/2017, nenhum dos 530 deals além de 138 dias ganhou.
3. **Portão, volta 1: FALHA.** O revisor achou 5 faltas. As duas que mudavam decisão:
   - a citação do README do desafio sobre tempo foi cortada justo no "Não há cronômetro", e daí saiu um "teto duro de 6 h" que a fonte não sustenta (a fonte diz que hora a mais não ganha ponto e que valorizam "inteligência no uso do tempo");
   - a frase do PGG punha a data da ação (abrir o PR) no lugar do prazo do resultado, prometendo aprovação no mesmo dia.
   Também: um "chute registrado antes de rodar" que, pela transcrição, foi escrito depois do resultado.
4. **Minhas respostas** entraram literais: o gatilho; a candidatura já feita; o crédito dos 8Rs ao livro; "Seremos honestos" sobre as horas; a esteira ao lado da construção; a tese da E2 aprovada; o aceite do PGG, com a razão principal *"ser a melhor entrega com o melhor processo e os melhores resultados"*.
5. **Portão, volta 2: RESSALVAS.** As 5 faltas foram corrigidas e conferidas na origem. Duas ressalvas: o caso descrevia o repositório como estava antes das minhas edições, e previsões que não tinham sido escritas antes da conferência. Recusei aceitar as ressalvas e mandei a volta 3.
6. **Correção de atribuição.** O revisor pegou que eu tinha escrito no README que os 8Rs eram "um framework proprietário meu". São do livro; a adaptação em hooks e a esteira são minhas. Corrigido antes de qualquer push.
7. **Formulários do diagnóstico.** Para a f1 (Autópsia), quero aplicar os formulários do meu framework de diagnóstico de negócio (4 encontros, 7 pilares, cemitério de tentativas, dor principal, ideação, pré-mortem, integrações, human-in-the-loop, equipe). Encontrei os originais no projeto onde foram criados e confirmei, arquivo por arquivo, que as cópias em uso são idênticas (0 linhas diferentes nos 9).
8. **Quem responde os formulários.** A f1 vai aplicar os formulários à empresa do enunciado (a Head de RevOps, 35 vendedores, ~8.800 oportunidades) por roleplay. A Head descreve a operação; a dor que importa é a do vendedor, que é quem vai usar a ferramenta. O roleplay usa só com o que o brief e o dataset sustentam. Onde não há dado, o campo fica "sem dado" e a fase segue: nada é inventado para a persona.
9. **Scoring a comparar na f2:** BANT × MEDDIC × SPICED, medidos contra os campos que o dataset tem. Conferência prévia dos cabeçalhos dos 4 CSVs: não há campo de autoridade, dor, critério de decisão nem champion. A expectativa é que a maior parte de cada framework caia em "sem dado", o que vira recomendação: registrar esses campos daqui em diante.
10. **Design system do G4.** Despachei um worker supervisionado pelo Orca, com spec escrita em arquivo (alvo, entregas, restrições, critério de aceite e definição de pronto), para extrair do g4business.com os tokens, os componentes e o catálogo de movimento (animações, transições e efeitos com duração, easing e gatilho). A aplicação vai se inspirar no sistema visual; logos e fotos ficam de fora, e o material bruto fica fora deste repositório.

## Onde desconfiei e conferi

- **O revisor reprovou um "teto de 6 h" que eu tinha aceitado sem conferir.** Parecia prudente, mas saía de uma citação cortada. Ficou como proposta, não como regra do desafio.
- **"Chute antes de rodar" só vale se estiver escrito antes de rodar.** O revisor comparou o horário do backtest com o horário em que a previsão apareceu no arquivo. A regra agora é gravar a previsão num arquivo antes de executar.
- **"Mortos" pode ser artefato do dataset.** O deal perdido mais longo também tem 138 dias, igual ao ganho mais longo, e nada fecha depois disso. A ferramenta vai dizer o que o dado mostra ("nenhum deal fechou depois de 138 dias, ganho ou perdido") e declarar a limitação, sem chamar 81% do pipeline de morto.
- **Atribuição.** Eu tinha atribuído a mim um framework do livro. Corrigido na fonte antes de publicar.
- **Volta 4 da f0, por ordem minha.** A volta 3 deu RESSALVAS; recusei, a esteira escalou para mim, e mandei mais uma volta. Ela deu FALHA por um erro de leitura da IA: o caso registrava que a idade não ordena os negócios vivos (AUC 0,505), mas esse número mede só ganho × perda entre os 935 que fecharam. Na pergunta certa, "ganhou até 31/12" entre os 1.879 abertos em 30/09/2017 com até 138 dias, a idade dá 0,766 ([`evidencias/idade-robustez.txt`](../evidencias/idade-robustez.txt)). Fechei a f0 com a falha registrada e levei a medição para a f2. É a base do produto.

## Horas

O tempo declarado é só o tempo ativo da sessão principal, medido no fim por `process-log/scripts/tempo_ativo.mjs` (ver o README). Até aqui, nada da E3 foi construído.

## Próximo passo

Fechar a f0 depois da volta 3 do portão. Abrir a f1 com os formulários da Autópsia na persona da empresa do enunciado. A E3 (construir) começa depois da f1, já com o design system extraído.
