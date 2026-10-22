# 01 · O que já se sabe

> **Data:** 22/10/2026
> **Decisão que abriu esta etapa:** [D01 · Partir do que já foi descoberto, não refazer](decisoes.md#d01--partir-do-que-já-foi-descoberto-não-refazer)
> **Scripts:** [`catalogar_achados.py`](01-estado-da-arte/catalogar_achados.py) procura os achados nos 48 PRs. [`verificar_achados.py`](01-estado-da-arte/verificar_achados.py) refaz cada conta nos dados. Resultado bruto em [`verificacao.json`](01-estado-da-arte/verificacao.json).

Quando abri os dados, vi que tudo se dividia por igual. Antes de seguir, fui ver o que as outras entregas já tinham descoberto. Muita coisa. Então decidi não redescobrir nada. Juntei tudo aqui, dei o crédito pra quem achou e **conferi cada número nos dados com script meu**. Não aceitei nenhum número só porque alguém escreveu.

Como ler as tabelas:
- **Entregas que citam:** quantos dos 48 PRs do case 002 mencionam o achado. Conta por palavra-chave, então é ordem de grandeza.
- **Exemplos:** PRs que eu li e que mostram bem o achado.
- **Conferi:** o número que o meu script tirou dos dados.

---

## Dataset 1 · Tickets de clientes

### O dado é gerado por programa, não veio de uma operação

| Achado | Entregas que citam | Exemplos | Conferi |
|---|---|---|---|
| São 8.469 tickets, não ~30 mil como o brief diz | ~41 | #118, #134, #186 | ✅ 8.469 registros. O arquivo tem 29.808 linhas porque as descrições têm quebra de linha |
| O brief fala em 3 tipos de ticket, mas são 5 | ~15 | #27, #186 | ✅ Reembolso, Técnico, Cancelamento, Produto e Cobrança |
| Toda descrição tem `{product_purchased}` sem preencher | ~44 | #26, #27, #158 | ✅ 100% das descrições. Só existem 16 frases de abertura, e a mais comum aparece em 69% |
| A resolução é texto aleatório | ~23 | #27, #158 | ✅ Exemplos: *"Such option result friend able director."* e *"Deal step team east pressure."* |
| Todo e-mail é de domínio de exemplo | ~21 | #127 | ✅ example.com, example.org e example.net. São domínios reservados pra teste |
| Todas as colunas se dividem por igual | ~34 | #27, #127, #157 | ✅ Ver tabela abaixo |

**Como as colunas se dividem:**

| Coluna | Opções | Menor | Maior | Compatível com sorteio? |
|---|---|---|---|---|
| Canal | 4 | 24,5% | 25,3% | Sim (p = 0,72) |
| Prioridade | 4 | 24,4% | 25,9% | Sim (p = 0,21) |
| Tipo de ticket | 5 | 19,3% | 20,7% | Sim (p = 0,12) |
| Produto | 42 | 2,1% | 2,8% | Sim (p = 0,48) |
| Nota de satisfação | 5 | 19,6% | 20,9% | Sim (p = 0,80) |
| Assunto | 16 | 5,6% | 6,8% | Quase (p = 0,02) |
| Gênero | 3 | 31,7% | 34,2% | Quase (p = 0,01) |

Idade vai de 18 a 70 anos, com 137 a 186 clientes em cada idade.

*O teste de qui-quadrado compara com uma divisão perfeitamente igual. p alto quer dizer "não dá pra distinguir de sorteio". Assunto e gênero não são exatamente iguais, mas ficam longe de qualquer operação real. Nenhum canal domina, nenhum produto dá mais defeito, e "gênero: outro" tem um terço dos clientes.*

### Os tempos não medem nada

| Achado | Entregas que citam | Exemplos | Conferi |
|---|---|---|---|
| Não existe data de abertura do ticket | ~27 | #104, #121, #126 | ✅ Nenhuma coluna de abertura. Sem ela, não dá pra saber quanto tempo o cliente esperou |
| Metade dos tickets "resolve" antes da 1ª resposta | ~28 | #100, #101, #118 | ✅ 49,3% dos fechados (1.365 de 2.769) |
| Toda resposta e resolução cabe em 27 horas | ~21 | #101, #131, #158 | ✅ De 31/05/2023 21h53 a 02/06/2023 00h55. As compras são de 2020 e 2021 |
| A diferença entre os dois horários é ruído | ~10 | #158 | ✅ Média de -0,06 h e desvio de 9,6 h. Parece dois horários sorteados, não tempo de atendimento |

**O que isso quer dizer na prática:** a pergunta do brief "onde o fluxo trava?" não tem resposta com esses dados. Qualquer ranking de "canal mais lento" é ruído.

### A fila parada é o único sinal que se sustenta

| Achado | Entregas que citam | Exemplos | Conferi |
|---|---|---|---|
| 67% dos tickets não estão fechados | ~30 | #179, #205, #189 | ✅ 33,3% Open, 34,0% Pending, 32,7% Closed |
| Nenhum ticket Open recebeu resposta | ~28 | #179, #205 | ✅ 2.819 de 2.819 |
| Prioridade não muda nada | ~31 | #101, #150, #205 | ✅ Critical fecha 34,1%, Low fecha 31,2% (p = 0,23). Diferença de tempo entre prioridades menor que meia hora |

**Ressalva:** como o dado é sorteado, mesmo essa fila pode ser só o jeito que o gerador distribuiu os status. Quem leva isso a sério (#205, #189) usa como hipótese pra medir numa operação real, não como fato.

### A satisfação não depende de nada

| Achado | Entregas que citam | Exemplos | Conferi |
|---|---|---|---|
| As notas de 1 a 5 têm quase a mesma quantidade | ~24 | #27, #68 | ✅ 553, 549, 580, 543 e 544 |
| Tempo não explica a nota | ~24 | #5, #52 | ✅ r = 0,02 (p = 0,25) |
| Nenhuma coluna explica a nota | ~20 | #126, #193 | ✅ Canal, prioridade, tipo, gênero e assunto, todos com p acima de 0,14 |
| Um modelo com tudo junto não prevê a nota | ~10 | #158, #178 | ✅ Acerta 20,5%. Chutar a nota mais comum acerta 20,9% |
| O texto não prevê o tipo do ticket | ~18 | #157, #193 | ✅ Acerta 19,5%. O acaso com 5 tipos é 20% |

---

## Dataset 2 · Tickets de TI

| Achado | Entregas que citam | Exemplos | Conferi |
|---|---|---|---|
| 47.837 tickets reais em 8 equipes, desbalanceados | ~43 | quase todos | ✅ Hardware 28,5%, RH 22,8%, Acesso 14,9%, Diversos 14,8%, Armazenamento 5,8%, Compras 5,2%, Projeto interno 4,4%, Permissões 3,7% |
| Um classificador simples acerta ~86% | ~30 | #52, #81, #104 | ✅ 86,6% de acerto, F1 macro 86,5% |
| Com 2 sugestões, o atendente acerta ~96% | ~5 | #126, #158, #179 | ✅ 96,5% |
| Trava de confiança: parte vai sozinha com acerto alto | ~17 | #104, #126, #127 | ✅ Ver tabela abaixo |
| O modelo de TI lendo o Dataset 1 joga quase tudo em Hardware | ~20 | #5, #126 | ✅ 90% em Hardware. O texto de TI não serve pra suporte ao consumidor |
| O LLM classifica pior que o modelo simples | ~19 | #121, #131, #150, #158, #195 | ⚠️ Não conferi. Precisa de chave de API. Os números citados vão de 39% a 77% contra ~86% |
| Tem tickets na fila errada | ~18 | #179 | ⚠️ Não conferi |
| Tem tickets quase repetidos | ~30 | #126 | ⚠️ Repetição exata não existe (0 textos iguais). Quase repetidos não conferi |

**Trava de confiança.** O ticket só vai sozinho se o modelo tiver certeza acima do limite. O resto vai pra uma pessoa.

| Limite de certeza | Vai sozinho | Acerto nos que foram sozinhos |
|---|---|---|
| 50% | 90,6% | 90,4% |
| 60% | 83,2% | 92,9% |
| 70% | 75,4% | 95,1% |
| 80% | 66,8% | 96,8% |
| 90% | 54,4% | 98,4% |

É a troca básica: quanto mais exigente a trava, menos tickets vão sozinhos e mais eles acertam.

---

## O que as entregas propõem

| Proposta | Entregas que citam | Exemplos |
|---|---|---|
| Rascunho de resposta pro atendente aprovar | ~42 | #158, #205 |
| Reembolso e cancelamento sempre com uma pessoa | ~31 | #27, #126, #178 |
| Medir a operação antes de automatizar | ~30 | #104, #105, #126 |
| Piloto em modo sombra (a IA sugere, ninguém aplica) | ~26 | #133, #186, #195 |
| Resolver antes de abrir ticket (deflexão) | ~15 | #68, #99 |
| Lembrete automático pro cliente que sumiu (Pending) | ~7 | #189, #133 |

### O mesmo dado, economias de 1 a 100

Cada entrega estimou quanto a automação economiza. Como o dado não mede tempo, cada uma inventou as premissas:

| PR | Economia estimada |
|---|---|
| #20 | R$ 1,95 milhão por ano |
| #68 | R$ 921 mil |
| #15 | US$ 128 mil por mês |
| #150 | R$ 119 mil por ano |
| #131 | R$ 20 mil a R$ 114 mil por ano |
| #100 | R$ 84,5 mil líquidos no 1º ano |
| #127 | R$ 63 mil por ano |
| #27 | R$ 42 mil por ano |
| #118 | R$ 29,7 mil por ano |
| #126 | R$ 1,2 mil por mês (cerca de R$ 14 mil por ano) |
| #104 | Não converteu pra reais de propósito. 0,1 a 0,3 pessoa por ano |

*Números copiados dos resumos de cada PR. Não conferi as contas.*

A maior estimativa é mais de 100 vezes a menor. Em cima do mesmo arquivo. **Ninguém sabe quanto custa o suporte, porque o dado não mede.**

---

## O que ainda está aberto

O que quase ninguém fez, ou fez só pela metade:

1. **Medir a resposta, não só a triagem.** Quase todo mundo classifica e roteia. Rascunho de resposta aparece em ~42 entregas, mas quase ninguém mede se a resposta é boa ou segura: se inventa prazo, promete reembolso ou fala o que não pode.
2. **O cliente parado.** 34% da fila está esperando o cliente voltar. Só ~7 entregas propõem fazer algo com isso.
3. **Uma operação real.** Todas as entregas trabalham só com os dois datasets. Nenhuma contrasta com um suporte de verdade.
4. **O resultado do atendimento.** O Dataset 2 só diz pra qual equipe o ticket foi. Ninguém sabe se o problema foi resolvido.

Daqui eu escolho onde construir.

---

## Quem fez o quê nesta etapa

| Eu | Claude Code |
|---|---|
| Abri os dados e percebi que tudo se dividia por igual | Corrigiu minha leitura do "outros 59%", que era a tela do Kaggle juntando categorias |
| Decidi não redescobrir o que já foi achado ([D01](decisoes.md)) | Catalogou os achados nos 48 PRs |
| Pedi tudo com o porquê, em tabela, com os dados | Escreveu e rodou o script que confere cada achado |
| Pedi pra ver com os meus olhos que o dado é sorteado | Propôs conferir cada achado nos dados em vez de confiar no texto dos outros, e marcou o que não deu pra conferir |
