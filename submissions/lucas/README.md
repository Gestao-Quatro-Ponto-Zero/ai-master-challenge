# Submissão — Lucas A. Maluf Stein — Challenge 003

## Sobre mim

- **Nome:** Lucas A. Maluf Stein
- **LinkedIn:** https://www.linkedin.com/in/lucasmalufstein/
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma ferramenta web (roda no navegador, sem backend) que organiza os
2.089 deals abertos do pipeline em uma matriz de ação — não um ranking cru nem
um score preditivo. A decisão mais importante veio de um achado: validei por
backtest com validação cruzada que a probabilidade de fechamento por
produto/setor **não discrimina** quem fecha (AUC 0,485, praticamente sorte) e
que priorizar por Valor Esperado quase empata com simplesmente ordenar pelos
deals mais caros. Em vez de esconder isso atrás de um dashboard bonito,
reposicionei a ferramenta em torno do que realmente muda a ação do vendedor:
**valor em jogo, deals sendo negligenciados, e explicabilidade transparente**.
Recomendação central: usar a matriz 2×2 (Valor × Abandono) como visão de
segunda-feira, tratando a probabilidade como contexto — não como previsão.

---

## Solução

Um app single-file (`app/index.html`) que o vendedor abre e vê, imediatamente,
onde focar. O deliverable roda de dois jeitos (double-click ou
`python -m http.server`) e usa os dados reais do CRM.

### Abordagem

Decompus o problema em cinco fases, cada uma validando a anterior antes de
avançar — o histórico de commits reflete essa sequência:

1. **Auditoria dos dados** — antes de qualquer modelo, mapear a realidade:
   integridade dos joins, win rate por segmento, ciclo de venda, disponibilidade
   de features.
2. **Disponibilidade de features** — descobrir com quais dados eu realmente
   posso contar num deal aberto (spoiler: firmografia só existe em 1/3 deles).
3. **Motor de scoring** — win rate empírico com shrinkage + Valor Esperado +
   flag de abandono, separando explicitamente o que é empírico do que é heurístico.
4. **Backtest** — provar (ou refutar) que o scorer funciona, com validação
   cruzada anti-vazamento.
5. **App** — a ferramenta que o vendedor usa, construída em torno do que o
   backtest mostrou ser real.

O princípio que guiou tudo: **deixar os dados decidirem o modelo**, em vez de
chutar pesos. Cada decisão de scoring está ancorada num número da auditoria.

### Resultados / Findings

**O que a análise revelou:**

- **A probabilidade de fechar é quase plana.** Win rate por produto varia só
  entre 60–65%; por setor, ±1,9pp. Nenhuma feature disponível separa bem
  ganhador de perdedor.
- **Backtest (5-fold, anti-vazamento):** AUC 0,485. As probabilidades são
  razoavelmente calibradas *na média agregada*, mas não discriminam deals
  individuais. Priorizar por Valor Esperado captura 46,8% do valor no top-20%
  — contra 47,9% de simplesmente ordenar por preço (rankings 98,5%
  correlacionados). O componente empírico não supera "perseguir o deal caro".
- **O valor real da ferramenta** não está em prever fechamento, e sim em dar
  visibilidade e explicabilidade sobre um pipeline hoje priorizado no feeling,
  destacando deals de alto valor sendo negligenciados e diferenciando deals
  engajados de prospects frios.

**O que construí a partir disso:** a matriz 2×2 (Valor Esperado × Abandono),
com 4 quadrantes de ação — Trabalhar agora, Resgatar ou soltar, Manter no radar,
Despriorizar — mapeando direto as duas dores da Head de RevOps ("perde tempo em
deal ruim" e "deixa deal bom esfriar"). Cada deal traz drivers em texto, um
indicador de confiança, e filtros por vendedor/manager/região/produto.

### Recomendações

1. **Usar a matriz como visão de segunda-feira**, não o número do score. O
   quadrante "Resgatar ou soltar" (alto valor + esfriando) é onde está o
   dinheiro deixado na mesa hoje.
2. **Tratar a probabilidade como contexto, não previsão.** Com os dados atuais,
   ela não prevê fechamento — priorizar por valor em jogo é mais honesto.
3. **Investir em captura de dados de conta.** Firmografia falta em 2/3 dos
   deals abertos; preencher isso é o que permitiria um scoring de fato preditivo
   no futuro.
4. **Levar o indicador de confiança a sério** — deals de "confiança baixa"
   (produto raro ou sem conta) merecem cautela antes de virar prioridade.

### Limitações

- **A probabilidade não é preditiva** com as features disponíveis (AUC ≈ 0,5).
  Assumido de propósito e comunicado na própria interface.
- **O backtest só valida o ramo "com conta"** — 100% dos deals fechados têm
  conta, então o fallback "só produto" (~68% do pipeline aberto) não tem
  validação empírica possível neste dataset.
- **O multiplicador de estágio é heurístico**, não derivado dos dados: como
  cada deal só registra o estágio final, não dá pra medir win rate condicional
  ao estágio historicamente.
- **A flag "esfriando" sofre de viés de censura temporal** no dataset estático
  (quem segue aberto é, por construção, quem demorou). Contornei tornando o
  limiar relativo, mas num CRM ao vivo a calibração seria diferente.
- **Valor potencial = preço de lista do produto**, já que `close_value` é
  desconhecido antes do fechamento. É uma aproximação.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| Claude Code (Sonnet) | Execução: scripts de auditoria, scoring, backtest e build do app |
| Claude Code (Opus) | Decisões de modelagem que exigiam mais julgamento |
| Claude (chat) | Estratégia: escolha do challenge, desenho da abordagem, revisão crítica de cada fase |
| Claude in Chrome | Verificação do app rodando no navegador durante o desenvolvimento |

### Workflow

1. **Estratégia antes de código** — defini com o Claude (chat) o que um bom 003
   exigia (superar o baseline deles), escolhi o challenge alinhado ao meu forte
   (build), e desenhei a abordagem em fases.
2. **Auditoria** — Claude Code carregou os 4 CSVs e produziu tabelas de win rate,
   joins e disponibilidade de features. Não deixei ele inventar scoring antes de
   olhar os dados.
3. **Modelagem** — co-desenhei o motor de scoring a partir dos números reais
   (shrinkage para amostras pequenas, EV, flag de abandono).
4. **Validação** — backtest com validação cruzada. Aqui o resultado me obrigou a
   repensar a tese inteira da ferramenta.
5. **Build** — app single-file, testado ao vivo no navegador, refinado por
   feedback (esfriando relativo ao filtro, filtros encadeados, limite de lista).

### Onde a IA errou e como corrigi

**Coisas que a IA identificou e corrigiu sozinha** (crédito a ela):
- Mismatch de grafia entre tabelas (GTXPro vs GTX Pro, 1.480 deals) — a
  auditoria que ela rodou expôs, e ela normalizou.
- Bug de exibição (`.prod()` do pandas colidindo com a coluna `product`).
- CORS bloqueando `fetch()` no `file://` — resolveu embutindo os dados no build.
- Lista renderizando 800+ deals de uma vez — limitou a top-50 com aviso.

**Coisas que EU corrigi na IA** (julgamento humano):
- **Vendedor fora do scorer individual.** A IA apontou vendedor como o maior
  preditor. É verdade, mas inútil na visão de um vendedor: dentro do pipeline
  dele o vendedor é constante e não muda ranking nenhum. Movi essa feature pra
  visão do manager.
- **Flag "esfriando" pegava 93% dos deals.** A IA tratou como consequência dos
  dados (correto), mas um flag verdadeiro pra quase tudo não prioriza nada.
  Mudei a definição de absoluta para relativa.
- **A virada de tese depois do backtest.** A IA teria seguido apresentando o
  Valor Esperado como o herói. Quando o backtest mostrou que ele empata com
  "ordenar por preço", decidi reposicionar a ferramenta inteira de "score
  preditivo" para "organizador de ação" — abraçando o achado em vez de escondê-lo.

### O que eu adicionei que a IA sozinha não faria

O julgamento de **desconfiar do próprio resultado e reportá-lo honesto**. Uma
IA rodando o brief sozinha entregaria um dashboard de Valor Esperado convincente
e um AUC apresentado do jeito mais favorável. O que fiz de diferente foi exigir
o backtest anti-vazamento, aceitar que o número era ruim, e transformar essa
limitação no *conceito* da ferramenta — inclusive expondo o AUC 0,485 na própria
interface, pro vendedor. Priorizei o uso real (o que o vendedor pergunta na
segunda de manhã) sobre a pureza estatística e sobre "parecer inteligente".

---

## Evidências

- [x] **Git history** — sequência de commits reflete a evolução fase a fase
      (`git log --oneline --graph`)
- [x] **Diário de processo** — `process-log/diario.md`: decisões e julgamentos
      registrados a cada fase, na hora
- [x] **Screenshots** — `process-log/screenshots/`: app rodando, visão filtrada,
      git history
- [x] **Análises versionadas** — `analysis/`: scripts + summaries de cada fase
      (auditoria, scoring, backtest)

---

_Submissão enviada em: 