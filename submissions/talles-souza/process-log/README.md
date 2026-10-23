# Process log — Talles Souza — Challenge 003

Como a IA foi usada, sessão por sessão. Cada sessão de trabalho com o Claude Code gera um registro aqui **antes** de a sessão ser encerrada, porque o histórico da conversa é limpo de uma sessão para a outra (ver "Dinâmica").

## Registros por sessão

Antes da sessão 01: [instrumentacao.md](instrumentacao.md) (fase 0: o ambiente em que a IA trabalha, o ECC modificado com os 8Rs de PMV, as etapas E0–E5 e a higienização de contexto por etapa).

| # | Data | O que decidiu ou construiu | Registro |
|---|------|---------------------------|----------|
| 01 | 2026-10-22 | E0+E1: instrumentou o ambiente; mediu o sinal dos 5 datasets e escolheu o 003; levantou os 3 riscos do scoring | [sessoes/sessao-01-escolha-do-desafio.md](sessoes/sessao-01-escolha-do-desafio.md) |
| 02 | 2026-10-22 | E2: mediu o pipeline; nenhum atributo prediz ganho fora da amostra (AUC 0,50) e 81% dos negócios em negociação (Engaging) passaram da duração de qualquer deal fechado; a tese do score: idade × valor | [sessoes/sessao-02-entender-o-pipeline.md](sessoes/sessao-02-entender-o-pipeline.md) |
| 03 | 2026-10-22 | Entre E2 e E3: o teste virou projeto (PGG nos 4Cs, PMV nos 8Rs) numa esteira com revisor adversarial (portão da f0 em 4 voltas: FALHA, RESSALVAS, RESSALVAS e, na 4ª, por ordem minha, FALHA que corrigiu a leitura da idade: 0,505 → 0,766); formulários do diagnóstico conferidos na origem; design system do G4 delegado a um worker | [sessoes/sessao-03-pgg-e-pmv-do-teste.md](sessoes/sessao-03-pgg-e-pmv-do-teste.md) |
| 04 | 2026-10-22 | f1: Autópsia do negócio pela persona do enunciado, com o diagnóstico separado da solução; camada de dados com 9/9 testes; sistema visual do G4 extraído por um worker e conferido contra a spec | [sessoes/sessao-04-autopsia-dados-e-design.md](sessoes/sessao-04-autopsia-dados-e-design.md) |
| 05 | 2026-10-22 a 23 | E3–E5: desenho final (grupos pela idade, indicador "{chance} em 10", receita esperada, BANT ancorado no dado, painel só leitura); construção em fatias verticais por workers em paralelo; resiliência real com API e banco; E2E 11/11 com vídeo; verificação rodada pelo coordenador; números da Lógica reproduzidos a partir do repositório | [sessoes/sessao-05-construcao-e-verificacao.md](sessoes/sessao-05-construcao-e-verificacao.md) |
| 06 | 2026-10-23 | Motor de pontos (19 fatores, replay sem futuro, seleção fora da amostra: só a idade sobreviveu, AUC 0,830); score de qualidade (idade relativa à melhor faixa + respostas do BANT, pesos declarados), separado da ordem da tela e do valor em jogo; painel do manager com 4 números de dinheiro em jogo e a tabela por vendedor; correções vindas do backtest, da verificação em produção e do motor; E2E 12/12 | [sessoes/sessao-06-motor-score-e-verificacao.md](sessoes/sessao-06-motor-score-e-verificacao.md) |

## Evidências

A evidência do processo são os registros por sessão (`sessoes/`), os scripts, as saídas brutas e os vídeos. Não há export de chat, e o histórico de commits foi condensado num commit só para a entrega.

- `scripts/`: scripts usados para medir e verificar (reproduzíveis com `uv`)
- `evidencias/`: saídas brutas desses scripts, sem edição
- `../solution/e2e/videos/`: um vídeo por fluxo de ponta a ponta da ferramenta

## Dinâmica de trabalho

1. **Decompor antes de promptar.** Toda sessão começa com o problema e o critério de aceite escritos. O código vem depois.
2. **Medir antes de afirmar.** Nenhuma conclusão sobre os dados entra sem um script que a produza e a saída guardada em `evidencias/`.
3. **Registro fora da conversa.** O que foi decidido mora em arquivo (este log), nunca só no histórico do chat.
4. **Higienização de contexto a cada troca de etapa (`/clean`).** O **Jev (TypeSafe)** classifica cada retorno de ferramenta como relevante ou não para a próxima etapa, e as negativas de hook saem por regra fixa. Eu recebo o plano do que sai e aprovo. O corte só acontece com a sessão fechada e depois de um backup conferido, e a sessão retoma com um resumo que aponta para estes registros. Assim a atenção do modelo fica no problema atual, e o que foi descartado continua auditável aqui.
5. **Onde a IA erra, registro.** Cada sessão tem a seção "Onde desconfiei e conferi".
