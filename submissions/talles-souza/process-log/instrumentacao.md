# Fase 0 — Instrumentação do trabalho

Antes de resolver o desafio, montei o ambiente em que a IA trabalha, com a mesma lógica que eu usaria para instrumentar uma área de negócio: regras explícitas, registro fora da conversa e verificação antes de afirmar. O que está aqui não é o desafio. É **como** o desafio é feito, e por isso faz parte do process log.

## O que está instrumentado

| Peça | O que faz | Por que |
|---|---|---|
| **Claude Code** (Claude Opus 5.5) | Agente principal: lê, mede, constrói e registra | Trabalha no repositório e no terminal, com o histórico auditável |
| **ECC modificado, com os 8Rs de PMV** | ECC (Everything Claude Code) é um conjunto de hooks, skills e agentes para o Claude Code. A minha versão traz os **8Rs do PMV** (Plano Mínimo Viável), do livro *Inteligência Pragmática* (Max Peters), que adaptei em hooks, e um hook (GateGuard) que barra o primeiro comando e a primeira escrita de cada arquivo até a IA declarar um cartão de decisão: objetivo, alternativas (inclusive "não fazer agora"), impacto, custo, controle, reversibilidade e confiança | Força a IA a decidir antes de agir, em vez de sair executando. Em cada sessão, as negativas do hook ficam visíveis, e a IA tem de responder antes de seguir |
| **`/clean` com o Jev (TypeSafe)** | A cada troca de etapa, o Jev julga cada chamada de ferramenta da sessão contra a próxima etapa. Eu recebo o plano do que sai, aprovo, e o corte só acontece com a sessão fechada e depois de um backup conferido | O contexto do modelo é atenção. Os READMEs de desafios descartados e as negativas de hook já resolvidas competem com o problema atual. O que sai continua no backup e nos registros deste process log |
| **Hook de registro** | A cada mensagem, avisa a IA se há trabalho na submissão mais novo que o último registro de sessão. Ao escrever um registro de sessão, lembra de fechar a etapa (índice, Metodologia) e de oferecer o `/clean` | Faz o registro acontecer sem depender de alguém lembrar, eu ou a IA. Fica em silêncio quando está em dia, para não gastar contexto |
| **Medição reproduzível** | Scripts em `scripts/`, saídas brutas em `evidencias/`, ambiente isolado com `uv` e versões fixadas | Nenhuma afirmação sobre os dados sem um script que a produza |

Os 8Rs e os 4Cs (PGG, Projeto Ganha-Ganha) são do livro; a adaptação em hooks e a esteira de diagnóstico são minhas. O conteúdo dos meus frameworks próprios não está neste repositório. Aqui fica o registro de **quando** cada um entrou no trabalho e **o que mudou** por causa dele.

A evidência pública do processo são os registros por sessão (`sessoes/`), os scripts com as saídas brutas (`scripts/`, `evidencias/`), os vídeos do E2E (`solution/e2e/videos/`) Não há export de chat, e o histórico de commits foi condensado num commit só para a entrega.

## Etapas do desafio e onde o contexto é higienizado

| Etapa | O que fecha a etapa | Higienização |
|---|---|---|
| E0 Instrumentação | Este arquivo e a skill `/clean` funcionando | junto com a E1 |
| E1 Escolha do desafio | `sessoes/sessao-01-escolha-do-desafio.md` | `/clean` r1 |
| E2 Entender os dados e definir o score | `sessoes/sessao-02-*.md` com a lógica escrita e medida | `/clean` r2 |
| E3 Construir a ferramenta | app rodando com os dados reais | `/clean` r3 |
| E4 Verificar | critérios de aceite conferidos (contagens, casos, explicação do score) | `/clean` r4 |
| E5 Documentar e submeter | README final, process log completo, PR aberto | — |

Cada rodada de `/clean` registra aqui o tamanho antes e depois.

## Registro de frameworks e rodadas

| Data | O quê | Efeito observado |
|---|---|---|
| 2026-10-22 | ECC modificado com os 8Rs do PMV (livro *Inteligência Pragmática*), ativo desde o início | 14 negativas do GateGuard na sessão 01; cada uma exigiu declarar objetivo, alternativas e reversibilidade antes de criar o arquivo |
| 2026-10-22 | Skill `/clean` criada (motor de limpeza com o Jev, que eu já usava em outros trabalhos); o corte é feito num fork da sessão, e a original fica intacta | rodada r1 no fim da sessão 01: 129 de 131 chamadas cortadas; **contexto medido na retomada: 370.935 → 235.721 tokens (−36%)**, com o resumo da etapa respondido corretamente pelo fork |
| 2026-10-22 | Esteira de diagnóstico própria (squad de 9 agentes, fases f0–f4, cada uma com portão de um revisor adversarial e laço de até 3 voltas antes de escalar para mim; a f0 teve 4, a 4ª por ordem minha, e a f1, a f2 e a f3 tiveram 3 cada), aplicada ao próprio teste: o objetivo vira PGG (4Cs) e o plano vira PMV (8Rs); o diagnóstico (f1) vem antes da construção e as fases seguintes rodam ao lado dela | f0 (qualificar): revisor deu FALHA na volta 1 com 5 faltas, entre elas uma citação do README do desafio cortada no ponto que mudava o sentido ("Não há cronômetro") e um "chute registrado antes de rodar" que foi escrito depois do resultado |
| 2026-10-22 | `/clean` r2, no fim da f1 (troca de etapa): 211 retornos de ferramenta cortados pelo plano do Jev, com meu OK; corte num fork, original intacta | o plano não pegava uma skill carregada inteira na conversa (o texto de uma skill de configuração, 2 vezes, ~587 mil caracteres); cortei à mão e anotei na skill. **Contexto medido na retomada: 391.425 → 302.732 tokens** com o corte da skill; o fork respondeu certo o produto decidido e o próximo passo |
| 2026-10-22 | Worker supervisionado pelo Orca (orquestração com Run, Task e Dispatch rastreáveis) para extrair o design system do g4business.com, com spec em arquivo: alvo, entregas, restrições (só leitura, ≤ 5 páginas, sem logos e fotos no app), aceite observável e definição de pronto | aceito na sessão 04 só depois de conferido contra a spec (0 erros no console, 4 animações, sem rolagem em 390 px, nenhum logo ou foto); o worker ficou ~1 h parado e retomou por mensagem no canal da orquestração, sem ser morto e relançado |
| 2026-10-22 a 23 | Construção por workers do Orca em ondas (domínio, API e web em paralelo; depois receita esperada, painel, banco e deploy; depois os ajustes da verificação), cada um com spec em arquivo (entradas, passos, saídas, critério de aceite, definição de pronto) e registro de execução | o aceite foi conferido pelo coordenador rodando `npm test`, a integração com o banco real, o E2E e as telas (sessão 05). Os workers pegaram e registraram, eles mesmos, problemas que o "terminei" esconderia: arquivos novos fora dos commits (o `.gitignore` ignora `submissions/`) e 429 no E2E |
| 2026-10-22 a 23 | Revisão independente do código por subagentes só leitura (TypeScript e segurança), separada de quem escreveu | 4 achados altos, todos corrigidos com teste de regressão antes da verificação |
| 2026-10-23 | Motor de pontos, score de qualidade e painel do manager construídos por workers do Orca com spec em arquivo, e conferidos pelo coordenador ([sessão 06](sessoes/sessao-06-motor-score-e-verificacao.md)) | a verificação em produção pegou um negócio da Nutrição com score acima do Foque e o Foque vazio com negócios vivos no Siga; o backtest pegou a conversão por log-odds errando a receita em −13,9% (a razão: +0,2%); o vazamento pelo "sem dado" foi encontrado e corrigido no motor. Todos corrigidos com teste; `npm test` verde e E2E 12/12 |
| 2026-10-23 | Tempo ativo da sessão principal medido pelos timestamps das transcrições dela (`scripts/tempo_ativo.mjs`, limite de 5 min; pausas maiores não contam) | **7 h 28 min**, com `--ate 2026-10-23T20:58:49Z` (`evidencias/tempo-ativo-2026-10-23.txt`) |
