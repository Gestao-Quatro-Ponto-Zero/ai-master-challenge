# Etapa 0 — Preparação

**Quando:** 09/11/2026, antes de começar o desafio.
**Ferramenta:** Claude Code (assistente pessoal), numa conversa que também tratou de outros assuntos. Por isso o export dessa conversa não entra aqui. Esta narrativa registra o que aconteceu nela e o que foi decisão minha.

## O que aconteceu, em ordem

1. **Leitura do repositório com a IA.** Li com o Claude o README, os 4 challenges, o submission-guide, o CONTRIBUTING e o template, e pedi um resumo dos 4 desafios.

2. **Escolha do desafio.** A IA recomendou o 003 (Lead Scorer), por três motivos:
   - o entregável é software funcionando, que combina com o meu perfil;
   - tem ligação direta com a minha experiência em pipeline comercial (SDR e closer);
   - o escopo é fechado, cabe em 4–6 h e ainda deixa espaço para diferencial.

   O 002 ficou como alternativa.

3. **Um desafio ou os quatro.** Perguntei se dava para fazer os 4. A IA mostrou o FAQ oficial ("preferimos um bem feito do que dois superficiais") e os sinais de que o processo valoriza o uso inteligente do tempo. **Decidi fazer só o 003, bem feito.**

4. **Entendimento do 003 e abordagem inicial.** A IA explicou o desafio em detalhe:
   - as quatro tabelas;
   - Won e Lost são histórico, e Prospecting e Engaging são o alvo do score;
   - o dataset deve cobrir 2016–2017, então a data de referência tem que ser fixa.

   A IA também esboçou uma abordagem: score 0–100 em componentes visíveis (chance, valor, tempo, conta), validação no histórico e uma tela de "segunda-feira de manhã". **Aprovei como ponto de partida, a ser confirmado pelos dados.**

5. **Process log.** Revisei com a IA o que o process log exige. **Decidi fazer o desafio em sessões dedicadas, separadas da conversa principal, registrando as decisões na hora e com commits pequenos.**

6. **Repositório e branch.** Clone local do repositório oficial e branch de submissão. A pasta começou como `leandro-maia`. **Corrigi para `leandro-mallet`**, e a IA renomeou a branch e a pasta.

7. **Pegadinha do `.gitignore`.** A IA percebeu que o `.gitignore` oficial ignora `submissions/` (e `datasets/`). Sem `git add -f`, o PR sairia vazio. Registrado como cuidado obrigatório na entrega.

8. **Sessão no lugar errado.** A primeira sessão nova abriu numa cópia separada (worktree), fora da pasta certa e sem os arquivos de contexto. **Pedi a sessão na pasta certa e criei eu mesmo as sessões.**

9. **Organização em sessões.** A IA recomendou não paralelizar demais, pelo risco de conflito de arquivos e de um process log fragmentado. **Decidi usar 5 sessões com papéis separados, cada uma dona da própria pasta:**

   | Sessão | Papel |
   |---|---|
   | #1 | Orquestração, auditoria e process log (a única que faz commit) |
   | #2 | Dados |
   | #3 | Score |
   | #4 | App |
   | #5 | QA e baseline |

   Entre o score e o app existe um contrato de dados (`deals_scored.json`), para que um não quebre o outro.

10. **GitHub.** **Pedi que nada fosse feito no repositório oficial (fork, push, PR) até eu mandar.**

## O que foi julgamento meu nesta etapa

- Escolher 1 desafio em vez de 4.
- Separar a sessão do desafio do resto do trabalho.
- Corrigir o nome da pasta.
- Organizar as 5 sessões com donos de pasta e um contrato entre score e app.
- Exigir verificação de sinal nos dados antes de construir qualquer interface.
