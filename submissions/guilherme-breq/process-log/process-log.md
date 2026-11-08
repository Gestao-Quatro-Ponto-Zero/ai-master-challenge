# Process log — como a solução foi construída

Ambiente: **Claude Code (Claude Opus) rodando dentro do Maestri**, um canvas onde vários agentes trabalham conectados. Um agente principal (orquestrador) fez a análise e a construção, e delegou a revisão de código e segurança e a QA de interface para dois agentes especializados do meu time.

As evidências estão em quatro lugares:

- **Git history** da branch `submission/guilherme-breq`.
- **Scripts de análise** em `solution/analysis/`, na ordem em que foram escritos.
- **Capturas** em `screenshots/`.
- **Export da conversa** em `chat-exports/`.

---

## Linha do tempo

### 1. Entender antes de abrir o dataset

- Li o README geral, o brief do challenge 003, o `CONTRIBUTING` e o guia de submissão.
- Decidi três coisas antes de qualquer código:
  - **Stack:** Next.js + TypeScript + Tailwind, que é o meu padrão, sem banco. Os CSVs são lidos no build e a página sai estática, então a ferramenta roda com `npm install && npm start`.
  - **Onde trabalhar:** clone em `E:\Projetos`. O fork fica para a hora do PR, porque é uma ação pública.
  - **Dados:** baixei o zip do Kaggle à mão (exige login) e extraí numa pasta isolada, fora do repo.

### 2. Exploração (`analysis/01-03`)

A primeira passada já mostrou o que o baseline não vê:

- **Os atributos "óbvios" não discriminam.** Produto, setor, região, manager, receita e funcionários ficam todos entre 60% e 65% de win rate.
- **81% do pipeline Engaging é mais velho que qualquer deal que já fechou.** Nenhum dos 6.711 fechados passou de 138 dias, e 1.291 dos 1.589 abertos já passaram.
- **Problemas de qualidade:** `GTXPro` ≠ `GTX Pro`, `technolgy`, 68% dos deals abertos sem conta e 5 vendedores sem nenhum deal.

Na sequência validei a estabilidade dos sinais entre semestres (`03`). A taxa por conta e por vendedor × produto tem correlação de −0,07 entre H1 e H2, ou seja, é ruído.

### 3. Primeira proposta, e o backtest que a derrubou (`analysis/04`)

**Proposta inicial (que eu aprovei):** score = chance de ganhar (curva de sobrevivência por idade, ajustada pelo vendedor com shrinkage) × valor × urgência, com os zumbis fora do ranking.

Antes de escrever o app, a IA montou um **backtest temporal sem vazamento**: congelou o CRM em 5 datas, treinou só com o que já tinha fechado e pontuou cada deal aberto com a idade que ele tinha naquele dia.

**Resultado:** AUC de 0,50 a 0,52 para todas as variantes de "chance", com Brier pior que a média global. A curva de idade, que parecia forte dentro da amostra (63% → 76%), não se sustentou fora dela.

**Decisão:** tirar a chance de ganhar do score. Ela aparece na tela de forma honesta ("~63%, a média do time; testamos e nada muda isso de forma confiável").

### 4. Achar o que funciona (`analysis/05`)

Com o mesmo rigor, testei os sinais candidatos:

| Hipótese | Resultado | Decisão |
|---|---|---|
| Momento: p(decisão em 30d \| idade) | AUC 0,66 / 0,70 / 0,87 (*inflado; ver seção 7*) | **Entra** (40 pts) |
| Regra do zumbi | "589 zumbis" em datas passadas, 0 fecharam (*eram 411 deals únicos*) | **Entra** como filtro |
| Valor | Top 20% concentra ~50% da receita ganha | **Entra** (60 pts) |
| Fim de trimestre (81% × 52%) | Efeito igual nos dias 1–10, 11–20 e 21–31 do mês | **Descartado**: artefato do dataset, e usaria uma data do futuro |

### 5. Construção com TDD

- **Motor de score** (`src/lib/scoring.ts`): puro, sem I/O. Os testes vieram primeiro (RED → GREEN).
- **Teste de integração** com os CSVs reais. Ele cruza o TypeScript com a análise em Python: 298 vivos, 1.291 zumbis, 500 em prospecção, 138 dias e 63,2%. As duas implementações bateram de primeira.
- **Filtros e KPIs** (`selection.ts`) também puros e testados. A UI só desenha.
- **Interface:** tela de segunda de manhã com a frase de abertura ("Bom dia, Darcel. N deals vivos de M abertos. X pedem decisão esta semana."), KPIs que pedem ação, abas por tipo de decisão (Foco, Janela fechando, Higiene, Prospecção, Time, Como funciona) e cada deal expansível com motivos em português simples e a composição do score.
- **Gates:** 24 testes nesta etapa (35 no final), lint, typecheck, build estático e `npm audit` (0 vulnerabilidades em produção).

### 6. Revisão visual e ajustes

Tirei uma captura da build de produção (Edge headless) e critiquei:

- **Empates em 85:** o desempate passou a ser explícito (menos dias restantes no ciclo primeiro), com teste.
- **KPIs em fonte mono:** "1.291" ficava espaçado demais, então troquei por sans tabular.
- **Ações longas** quebravam linha e foram encurtadas.

### 7. Revisão delegada (agentes do Maestri), e o backtest que estava errado

No meio da sessão, eu cobrei: *"por que não delegou nada pra ninguém?"*. Defini que o Maestri é o meu ambiente padrão e que o agente principal deve usar o time de agentes de lá. A partir daí, com o motor fechado, a revisão rodou em paralelo enquanto a documentação era escrita:

- **Esquadro** (revisor de código, estatística e segurança, só leitura, rodando em outro modelo): achou **dois vieses no backtest do momento**.
  - **Seleção pelo futuro:** só deals que acabaram fechando entravam no teste.
  - **Censura ignorada:** a curva era estimada sem os deals ainda abertos.

  Também achou zumbis contados em dobro e quatro bordas sem validação.
- **Retina** (QA de interface, só leitura): 3 rodadas no navegador com emulação de dispositivo. Foram 11 achados na 1ª, 6 na 2ª e 3 detalhes na 3ª, entre eles beco sem saída no estado vazio, abas sem teclado, mobile com o 1º deal a 1000px e ações contraditórias.
- **Torno** (engenheiro full stack): implementou em paralelo os ajustes de `DealRow` e `TeamTable`, com escopo de arquivos isolado do meu.

**O que mudou com a revisão:**

- O momento foi refeito com **Kaplan-Meier** (`analysis/06`, com o `05` mantido como registro do erro).
- A AUC honesta é **0,65 em média** (0,53–0,79), não 0,66–0,87. A calibração ficou boa (previsto 25%, real 26%).
- A curva corrigida revelou que **deals esfriam depois de ~100 dias**: a chance de decisão cai de 44% aos 75 dias para 2% aos 135. Isso virou o estado "esfriando" no app, com a ação "reengajar".
- Ao implementar as faixas da curva, achei mais um bug meu: um limiar simples juntava o pico inicial com o pico do ciclo. Foi corrigido com teste.

Os achados e o que foi feito com cada um estão em [`review-findings.md`](review-findings.md).

### 8. Redesign com identidade G4 (time de agentes no Maestri)

- **Meu pedido:** rever o que o desafio pede e dizer se tínhamos entregado algo genérico ou útil, com um design à altura e nas cores da G4 (extraídas do site: navy, off-white, dourado, tijolo; Manrope). **Crítica de partida (orquestrador e Design):** a análise era o diferencial, mas a interface ainda era um dashboard genérico. A ação ignorava o valor ("Ligar hoje" em um deal de US$ 55; 11 dos 16 vivos da Rosalina somavam US$ 605) e o app abria na visão do time, não no vendedor.
- **Crítica a mais:** o número do score era lido como chance de ganhar, que o backtest mostra ser igual para todos. Nas direções novas, o score aparece só como soma explicada.
- **3 direções com dados reais:** Pauta da segunda (editorial), Relógio do ciclo (mapa idade × produto com a curva por trás) e Fila de trabalho (fila + ficha).
- **Minha escolha:** a Fila como estrutura, o mapa do Relógio como visão do time e a entrada "Quem está abrindo?" da Pauta; ação variada pelo valor (ticket baixo vira lote por e-mail) e marcações Feito / Adiar / Não está vivo no navegador, com aviso de que ficam só ali.
- **Implementação pelo Frontend, em TDD:** `playbook.ts` (ação por status, valor, idade e dias restantes) com 18 testes, marcações versionadas em `marks.ts`/`persisted.ts`, vendedor lembrado e teclado J/K/E/A. `scoring.ts` intocado e a distribuição nova coberta por teste: Ligar 72 · Decidir 76 · Reengajar 53 · Preparar 35 · Lote 62 = 298.
- **Revisão em paralelo, na mesma base:** Design (fidelidade ao protótipo: achou 2 desvios altos, a caixa de foco no título e a ação repetida de volta na tabela do time), Olho do Usuário (1 P1: foco invisível nos três botões da ficha, e 8 P2) e Segurança (2 P2 de persistência: queda de quota descartava a marcação nova, e remoção por outra aba a ressuscitava).
- **3 rodadas do Frontend** com recapturas a cada rodada, e o Olho revalidando a 2ª com Tab real: foco com anel dourado 9,54:1 sobre o navy, estado vazio com saídas, grupos de ativos e sem vivos na entrada, lote por urgência com ID do deal, e store que prioriza memória só enquanto a gravação falha.
- **Rodada 3:** o mapa ganhou quatro variantes de viewBox, uma por faixa de largura, para o texto nunca cair de 13 px entre 900 e 1440 px (medido com barra de rolagem real; abaixo de 360 px continua < 13 px).
- **Gate do QA Líder:** lint, typecheck, build e 93/93 testes aprovados; escopo confinado à submissão; veredito aprovado com ressalvas — as pendências eram documentais (Q1/Q2) e um `git diff --check` por linha em branco.
- **Números reais: 35 → 93 testes** (35 do motor intocados + 58 de playbook, marcações e interface).

---

## Onde a IA errou e como foi corrigido

| Erro | Como apareceu | Correção |
|---|---|---|
| Propôs um score com "chance de ganhar" por vendedor e idade | O próprio backtest deu AUC ~0,50 | A chance saiu do score; o desenho foi refeito em torno de valor, momento e zumbi |
| Leu a curva de idade dentro da amostra como sinal | Não se sustentou fora da amostra | Passou a valer a regra: só entra o que passa no backtest |
| **Backtest do momento com viés de seleção** (usou o futuro para escolher a amostra) | Revisão independente (Esquadro) | Teste com todos os abertos; AUC reportada caiu de 0,66–0,87 para 0,53–0,79 |
| **Curva de decisão ignorando censura** | Revisão independente: previa 41% num mês com 10% | Kaplan-Meier em Python e TS, com teste cruzando os dois |
| Contou 589 zumbis onde havia 411 deals | Revisão independente | Deduplicado; corte descrito como heurístico |
| Bordas sem validação (preço, datas, histórico vazio) | Revisão independente | Validação explícita + 7 testes novos |
| Fase de decisão juntava o pico inicial com o pico do ciclo | Ao conferir os limites exatos da curva antes de documentar | Faixa contínua ao redor do pico (`decisionWindow`), com teste |
| Publicaria contagens calculadas antes de uma correção | Conferência antes de documentar | Recalculado (os números se mantiveram) |
| Escreveu na doc que deals decididos cedo eram "quase todos perdidos" | Conferindo contra a análise: o win rate deles é ~55% | Texto corrigido |
| Arredondou números na tela ("AUC 0,50", "win rate igual") | Revisão do texto contra a saída dos scripts | Trocado pelos valores reais (0,50–0,51; 61% a 66%) |
| Rodou Python com `-I`, que ignora o pandas instalado | `ModuleNotFoundError` | Rodar sem `-I`, com o script fora da pasta de dados |
| Scaffold veio com `@types/node@20`, e o vitest 5 pede 22+ | `ERESOLVE` no npm | Alinhar os tipos com o Node 24 instalado, em vez de forçar com `--legacy-peer-deps` |
| Montou o JSON da delegação com caminhos Windows mal escapados | O CLI do Maestri rejeitou | Gerar o JSON por script em vez de escapar no shell |
| Trabalhou sozinho por padrão | Eu perguntei por que não delegou | Revisão e QA delegadas a agentes do Maestri; virou regra do meu ambiente |

## O que eu adicionei que a IA sozinha não faria

> *Rascunho escrito pela IA a partir das decisões da sessão. Revisar e ajustar com a minha voz antes de enviar.*

- **Exigir verificação antes de construir.** O baseline de qualquer modelo para este brief é um score ponderado com setor, porte, produto e vendedor. Ele parece sofisticado, mas o backtest mostra que é ruído. A diferença desta entrega é ter testado e ter tido coragem de *tirar* do score o que não funciona, e de dizer isso na tela.
- **Reenquadrar o problema.** "Deals que não vão fechar" não se resolve com probabilidade, e sim com higiene: 81% do pipeline está morto. Isso muda a conversa com a Head de RevOps de "qual modelo usar" para "o CRM está mentindo".
- **Desconfiar do achado bonito.** O efeito fim de trimestre (81% contra 52%) entraria em qualquer slide. Olhei o dia do mês, vi que não é empurrão de vendas e descartei.
- **Decisões de produto:** a tela abre com uma frase, não com uma tabela. Cada deal traz uma ação, em progressão ao longo do ciclo ("Ligar hoje", "Reengajar antes que esfrie de vez", "Forçar o sim ou o não esta semana"). O zumbi não compete com deal vivo. A chance aparece com honestidade, não escondida.
- **Processo:** stack e escopo definidos antes do código, TDD no motor, números do app cruzados com a análise por teste automatizado e revisão independente por outros agentes.

## Iterações

- 3 rodadas de análise exploratória (01 → 03).
- 1 proposta de score derrubada pelo backtest (04) e redesenhada (05).
- 1 validação refeita depois da revisão independente (05 → 06, Kaplan-Meier).
- Motor em TDD: 14 → 19 → 23 → 24 → 32 → 35 testes.
- 1 revisão visual própria, 1 revisão de código e estatística, 3 rodadas de QA de interface e 1 rodada de implementação delegada.
- 1 redesign com identidade G4: 3 direções, 1 implementação em TDD, revisão de Design, Olho do Usuário e Segurança em paralelo, 3 rodadas de correção e gate do QA Líder (35 → 93 testes).
