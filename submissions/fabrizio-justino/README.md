# Submissão — Fabrizio Justino — Challenge 003

## Sobre mim

- **Nome:** Fabrizio Justino
- **LinkedIn:** [linkedin.com/in/fabrizio-justino-1b13152a](https://www.linkedin.com/in/fabrizio-justino-1b13152a)
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma ferramenta web que diz a cada vendedor, na segunda-feira, **o que atacar, o que
nutrir e o que limpar** no pipeline, com o porquê de cada score. O achado central veio de testar
antes de confiar:

- **Perfil não prevê nada neste histórico.** Vendedor, conta, produto e setor não separam ganho
  de perda (AUC ~0,50).
- **O tempo prevê.** A chance de ganhar até o fim do trimestre, dada a idade do deal, tem AUC
  de 0,63 a 0,72, num backtest sem vazamento.
- **62% do pipeline aberto está morto.** Nenhum deal ganhou depois de 138 dias em Engaging (0 de
  13.871 no backtest), e 1.291 dos 2.089 deals abertos já passaram disso.

**Principal recomendação:** limpar esses deals já e tratar o último mês do trimestre como
janela de fechamento. É onde os ganhos se concentram (81% contra 52%), e a ferramenta liga um
modo emergência com a lista de deals que fecha o gap da meta.

---

## Solução

Aplicação **FastAPI + Next.js** que roda local com um comando (`start.bat`). Setup, lógica
completa e limitações estão em **[solution/README.md](solution/README.md)**.

### Abordagem

1. **Dados antes do score.** EDA e backtest temporal antes de definir qualquer peso. Foi isso que
   mostrou que as features "óbvias" não funcionam.
2. **Esqueleto, depois pressão.** Primeiro o motor de regras com alertas por stage; depois o
   modo emergência de fim de trimestre.
3. **Calibrar e medir.** Todo número exibido ao vendedor é conferido contra o que aconteceu, num
   backtest *rolling-origin* de 38 segundas-feiras que só usa o que se sabia em cada data.
4. **IA como camada de texto, não de cálculo.** O motor é determinístico e testado. O LLM só
   escreve sobre números prontos, e cada número é verificado.
5. **Revisão externa antes de entregar**, com cada ponto medido antes de ser aceito ou recusado.

### Resultados / Findings

| Pergunta | Resultado |
|---|---|
| Vendedor, conta, produto, setor, histórico da conta e afinidade preveem ganho? | **Não.** AUC 0,49–0,52 |
| A idade do deal prevê ganho **até o fim do trimestre**? | **Sim.** AUC 0,63 (vivos) · 0,72 (pipeline inteiro) |
| Deal com mais de 138 dias ainda ganha? | **Nunca.** 0 de 13.871 no backtest |
| Ganhos se concentram no fim do trimestre? | **Sim.** 81% no último mês contra 52% nos outros |

**O que a ferramenta entrega:**

- **Para o vendedor:**
  - score 0–100 explicado em 3 barras, com uma frase por pilar;
  - ação recomendada (Atacar agora / Nutrir / Primeiro contato / Requalificar / Encerrar /
    Baixa prioridade);
  - chance calibrada com faixa de incerteza e valor esperado.
- **Alertas por stage:** zona de risco, reta final, deal grande esfriando, lista de resgate.
  Só é crítico o que tem valor + prazo + ação, com no máximo 3 por vendedor; antes dessa regra
  eram 1.292 "críticos".
- **Modo emergência** no último mês do trimestre: meta × projeção e a menor lista de deals que
  cobre o gap. Em 04/12/2017, faltavam US$ 1,23M, e a lista tem 250 deals em ordem de ataque.
- **Visão de time:** ritmo (% da meta × % do trimestre), cobertura do que falta, carga ×
  capacidade, deals sem conta e sugestão de redistribuição.
- **E-mails semanais** separados para equipe e gestão. Exemplos em
  [docs/exemplos-emails/](docs/exemplos-emails/).
- **Camada de IA (OpenAI)**, toda conferida:
  - briefing de segunda;
  - explicação do deal;
  - chat sobre o pipeline;
  - plano de resgate;
  - rascunhos de e-mail;
  - análise do trimestre.

  Sem chave, tudo funciona com textos automáticos.
- **23 testes automatizados**, incluindo "snapshot não vaza o futuro", "calibração monotônica",
  "zumbi nunca ganhou" e "teto de 3 críticos".

Roteiro de demo de 3 minutos: [docs/DEMO.md](docs/DEMO.md). Respostas curtas para as perguntas
prováveis da banca: [docs/DECISOES.md](docs/DECISOES.md).

### Recomendações

1. **Limpar o pipeline já:** encerrar os 1.291 deals além de 138 dias (os caros: perguntar ao
   cliente e, se continuar, reabrir como oportunidade nova). Isso deixa taxas, cobertura e
   atenção honestas.
2. **Tratar o último mês do trimestre como janela de fechamento**, usando o modo emergência e a
   lista de resgate.
3. **Cadastrar a meta real** por vendedor e por time. A meta derivada da média histórica é a
   parte mais frágil da emergência.
4. **Coletar o que o CRM não tem:** último contato, atividades, stages intermediários. É onde
   provavelmente está o sinal que falta.
5. **Pilotar com medição:** metade dos times com a ferramenta por um trimestre, com feedback nos
   alertas, medindo taxa de ganho, ciclo e % de zumbis.

### Limitações

- O dataset é sintético e o sinal é fraco: a chance calibrada satura em ~41–47%, e a ferramenta
  ordena "o que dá para ganhar no trimestre" sem saber *por que* um deal específico ganha.
- A calibração só existe a partir de ~julho/2017; antes disso a tela avisa e mostra a chance
  bruta.
- Prospecting não tem datas no CRM, então esses deals ficam sem chance ("n/d").
- Não existe meta real: ela é derivada da média trimestral.
- A camada de IA foi testada com um LLM simulado; ainda não rodou com uma chave real. O envio
  SMTP real também não foi testado (os e-mails são gerados em arquivo).
- Não há login, escrita no CRM nem registro de feedback.

Detalhes e o que seria preciso para escalar: [solution/README.md](solution/README.md#limitações).

---

## Process Log — Como usei IA

> Versão completa, com a linha do tempo de cada prompt, erro e correção:
> **[process-log/PROCESS_LOG.md](process-log/PROCESS_LOG.md)**

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| **Claude Code** (VS Code, Claude Opus 5.5) | Rodar a EDA e os backtests, escrever e testar todo o código, revisar os e-mails gerados, guiar o fork/PR |
| **Claude (navegador) e ChatGPT** | Revisões críticas do projeto (planos das rodadas 2, 3 e 4), coladas no Claude Code como segunda opinião |
| **OpenAI** (dentro do produto) | Camada de texto da ferramenta, com conta e chave exclusivas do projeto |

### Workflow

1. **Kickoff:** colei o enunciado no Claude Code e defini a stack (FastAPI + Next.js) e o
   escopo do protótipo (local, sem login nem banco).
2. **EDA:** pedi a análise dos dados antes de qualquer peso. Ela achou o bug `GTXPro` × `GTX Pro`,
   o teto de 138 dias e o efeito de fim de trimestre.
3. **Esqueleto:** motor de regras + tela + alertas por stage, na minha direção: "esqueleto
   primeiro, depois emergência e pressão".
4. **Rodada 2:** plano em 4 blocos (qualificar, informar, aproveitar, pressionar). Cortei ICP e
   produto × porte, e **a calibração derrubou o score** (AUC 0,50).
5. **Redesenho:** alvo trocado para "ganha até o fim do trimestre", com estimador com censura e
   calibração isotônica.
6. **IA + e-mails:** 6 recursos de IA com validação de números; e-mails divididos em equipe e
   gestão, como pedi.
7. **Revisão externa:** cada ponto foi medido antes de ser aceito. Daí vieram rolling-origin,
   cortes por percentil, trilha de Prospecting e faixa de incerteza.
8. **Entrega:** questionei a necessidade de deploy; o guia pedia PR, não link. Fork e PR feitos
   com Git e GitHub CLI.

### Onde a IA errou e como corrigi

| Erro | Correção |
|---|---|
| 1º score não previa nada (AUC 0,50) | Backtest de calibração → novo alvo, com AUC 0,63/0,72 |
| Chance otimista (previa 80%, real 30%) | Censura dos deals que nunca fecham + recalibração isotônica |
| Calibração "colava" do futuro ao simular datas | Rolling-origin, com teste automatizado |
| Cortes fixos: "Atacar" variava de 82 a 893 deals | Cortes por percentil |
| "Requalificar" incoerente com "0 de 13.871 ganharam" | Virou "encerrar e reabrir como oportunidade nova" |
| Cobertura errada (~0,2× para todos) | Valor esperado ÷ o que falta para a meta |
| Texto na tela afirmava um AUC que nunca foi medido | Corrigido para o que foi testado |
| E-mail prometia "estes deals cobrem o que falta" sem conferir | O texto passou a depender do cálculo |
| 1.292 alertas "críticos" | Regra valor + prazo + ação, com no máximo 3 por vendedor |

A tabela completa (12 itens) está no [process log](process-log/PROCESS_LOG.md#3-onde-a-ia-errou-e-como-foi-corrigido).

### O que eu adicionei que a IA sozinha não faria

- **Direção de produto:** a "emergência e pressão" de fim de trimestre e os alertas por stage.
- **Cortes de escopo:** "não vamos fazer" ICP e produto × porte, quando o sinal seria fraco.
- **E-mails por público:** "dividindo em equipe e gestão, com alertas e análises".
- **Governança:** conta e chave de IA exclusivas do projeto.
- **Revisão independente**, trazida de outras ferramentas (Claude no navegador e ChatGPT).
- **Questionar complexidade:** "pra que vamos precisar de tudo isso?" evitou um deploy que o
  guia não pede.

**Por que cortei o ICP?** Porque os dados disseram que não funciona. Os atributos de perfil que
testei no backtest (vendedor, conta, produto, histórico da conta e afinidade) deram AUC entre
0,49 e 0,52, ou seja, cara ou coroa; setor e porte tinham win rate parecido em todas as faixas
(61–66%). Manter o ICP no score seria colocar um pilar bonito que não prevê nada e que ainda
engana o vendedor, que passaria a confiar num "fit" que não existe. O que prevê é o tempo, então
o score foi construído em cima dele. O cadastro da conta continua sendo usado no cross-sell,
onde faz sentido.

**Por que pedi a emergência no fim do trimestre?** Porque é ali que o dinheiro se decide. No
histórico, deal que fecha no último mês do trimestre ganha 81%, contra 52% nos outros meses.
Além disso, a data de referência do dataset cai exatamente no fechamento de trimestre, então a
pressão é real, não inventada. Também não queria um alerta a mais na pilha. Queria algo que
respondesse "quanto falta e quais deals cobrem isso". Por isso a emergência só liga nos últimos
30 dias, e só se a projeção não bater a meta. Quando liga, ela mostra o gap e a lista de resgate
com nome e valor.

**Por que usei duas IAs para revisar?** Para a IA não corrigir a própria prova. Quem construiu
o código tende a achar que está certo, porque tem os mesmos pontos cegos de quando escreveu.
Então uma construía e a outra revisava sem ter acompanhado a construção, olhando só o resultado.
Cada uma pega coisas diferentes, e quando as duas concordam, eu confio mais. A decisão final
ficava comigo: as duas sugeriam, eu decidia o que entrava.

---

## Evidências

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [x] Git history: commits nesta branch
- [x] Outro: [process log narrativo](process-log/PROCESS_LOG.md), com cada prompt, erro e
  correção; [e-mails gerados pela ferramenta](docs/exemplos-emails/);
  [23 testes automatizados](solution/backend/tests/)

---

_Submissão enviada em: 21/10/2026_
