# Escopo — Lead Scorer

## 1. Problema

A Head de RevOps pediu algo funcional, não um notebook. Duas dores, na voz dela (paráfrase do briefing):

- **Tempo jogado fora.** Meu time insiste em deal que não fecha. Falta uma lista do que largar.
- **Oportunidade esfriando.** Deal bom fica parado e ninguém avisa. Falta um alerta de urgência.

A dor real é alocação de tempo: não "qual deal tem mais chance", e sim "onde ponho minha próxima hora". Em 31/12/2017, 1.291 dos 1.589 deals em Engaging (81%) estão abertos há mais tempo que o maior ciclo já fechado (138 dias). Eles valem US$ 3,2 mi dos US$ 3,9 mi de tabela do Engaging.

## 2. Para quem

- **Vendedor** (30 com deals). Segunda de manhã: "Onde ponho meu tempo esta semana?"
- **Manager** (6). No 1:1 semanal: "O que do meu time está esfriando ou é lixo?"

## 3. O quê

**MVP, em ordem de prioridade**

1. **Quatro listas:** Foque (vivo, alto valor esperado), Reative (bom, mas esfriando), Limpe (parado além do que o histórico justifica) e Qualifique (Prospecting).
2. **Explicação por deal** (2 a 4 frases) e "Como funciona o score" em 5 linhas.
3. **Filtros** por vendedor, manager e região.
4. **Brief de segunda-feira** por vendedor: 3 para focar, 3 para reativar, o que limpar.
5. **Modo teste:** o que o score teria recomendado numa data passada e o que aconteceu até 31/12/2017.

**As quatro perguntas em aberto do briefing**

- **P1, quatro listas ou uma?** Quatro, em abas: cada uma pede uma ação diferente (avançar, reativar, encerrar no CRM, qualificar). Numa lista única, os 1.291 parados iriam para o fim e ninguém os limparia. E Prospecting não tem score. Cada lista é ordenada pelo score; Limpe e Qualifique, pelo valor de tabela.
- **P2, tela padrão?** A do vendedor, com "Quem é você?" no topo, guardado no endereço (`#vendedor=...`). O manager vê a mesma tela filtrada, mais uma "Carteira do time" só com contagens. Sem taxa de vitória por vendedor: p=0,26, compatível com ruído.
- **P3, o que vale mais no Foque?** Maior valor esperado (chance × preço de tabela). A chance cai de 50% para 7% entre deals de até 30 dias e de 61 a 90 (foto de 30/09/2017), mas o dinheiro é concentrado: 3 produtos dão 83,5% da receita ganha, e o MG Special, o segundo em número de deals, 0,4%. Ordenar só pela idade trata igual um MG Special e um GTX Pro. A urgência vira "faltam X dias".
- **P4, modo teste?** Entra, por cerca de 30 minutos de trabalho. É o diferencial mais forte: a Head de RevOps vê "o que o score diria em 30/06/2017 e o que aconteceu" e decide se confia. Qualifique fica indisponível nele: o CRM não registra quando o deal entrou em Prospecting.

**Fora do escopo.** Escrever no CRM; login; forecast financeiro; avaliar vendedores; score para Prospecting; tempo real; preço e desconto; notificações.

**Tratamento combinado.** Prospecting (500 deals, US$ 1,07 mi) vai para Qualifique, sem score, por preço de tabela. Deal sem conta (1.425, todos abertos) aparece como "Conta não informada", sem penalidade, com alerta de higiene de CRM.

## 4. Como

1. `scorer.clean`: junta os 4 CSVs e corrige "GTXPro" e "technolgy" (8.800 linhas, nenhuma perdida).
2. `scorer.score`: chance de ganho pela idade (aprendida de fotos mensais do passado) × preço de tabela.
3. `scorer.validate`: backtest temporal contra 3 baselines.
4. `scorer.build`: grava `app/data.js` e os briefs.
5. Página em HTML, CSS e JS puros: duplo-clique (`file://`) e GitHub Pages.

**Tese: frescor vale mais que atributos.**

- Atributos não separam. Produto, setor, região, manager e porte ficam entre 60% e 65% de win rate (produto: p=0,37). Variáveis numéricas: AUC ≈ 0,50.
- A idade separa. Na foto de 30/09/2017, deals com até 30 dias foram ganhos em 50% dos casos; 31 a 60 dias, 34%; 61 a 90, 7%; acima de 90, 0%.
- Sem "se idade > 138": o teto é provável artefato do gerador sintético. A curva é estimada e os limiares saem dos dados (bloco 3); 90 e 138 dias, no briefing, são só ponto de partida.
- Atributo só entra se o backtest mostrar ganho. Vendedor nunca entra.

## 5. Por quê assim

- **Streamlit.** É o padrão do baseline e exige servidor; a página estática abre com duplo-clique.
- **ML caixa-preta.** Há pouco a aprender nos atributos: os numéricos têm AUC ≈ 0,50 e, nos categóricos, até o target encoding dentro da amostra (inflado) ficou entre 0,51 e 0,54, com o vendedor no topo: ruído. E não explica o porquê.
- **Score por atributos.** Dá perto de 63% para todo deal: lista plana.
- **Ordenar só por valor.** Tende a levar aos zumbis, que valem a maior parte do Engaging.

## 6. Critérios de sucesso

- **Funciona.** `python -m pytest` passa; `python -m scorer.build --reference-date 2017-12-31` regenera tudo do zero; `index.html` abre em `file://` sem erro de console (Playwright, bloco 4); um revisor independente roda o README (bloco 6).
- **Scoring além do óbvio.** Métrica primária, fixada aqui: receita ganha capturada pelo top 20%, porque a dor é onde pôr a hora. O score tem de superar valor, recência e aleatório (média e percentil 95 de 200 sorteios) nos 4 cortes do backtest; até 1 ponto percentual é empate, e empate não vence. AUC e captura de ganhos não decidem. Se falhar, um único ajuste pré-definido; depois, publica-se a falha. Testes: mudar o que acontece após a data de corte, ou trocar os vendedores de lugar, não altera nenhum score.
- **Vendedor entende.** Acha seus 3 deals de Foque em até 2 interações. Cada card tem de 2 a 4 frases (teste), sem jargão (leitura nos blocos 4 e 6).
- **Interface decide.** A frase de ação ("foque em N, reative M, limpe K") aparece na primeira tela, no celular e no computador; as contagens batem com o SCORING (Playwright); 3 atritos reais corrigidos, com screenshots de antes e depois.
- **Código mantível.** Motor separado da interface, funções puras, testes; nenhum número escrito à mão (testes comparam prosa e arquivos gerados).

## Atualização depois da primeira entrega

- **Visões por perfil.** A tela agora abre em "Quem é você?":
  - o vendedor vê só a própria semana;
  - o manager vê o mapa do time, a pauta do 1:1 e a higiene de carteira, sem taxa de vitória nem ranking por vendedor;
  - RevOps vê tudo.
- **Segregação real de dados continua fora do escopo da versão estática.** A separação entre vendedores é de experiência, não de segurança, e está declarada na interface. O desenho de produção, com login e Row-Level Security, está em [ARQUITETURA_PRODUCAO.md](ARQUITETURA_PRODUCAO.md).
- **Curva de chance corrigida depois do backtest**, a partir da revisão do Rafael. Ver [SCORING.md](SCORING.md).

## 7. Riscos e premissas

**Premissas**

- "Hoje" é 31/12/2017 (parâmetro). O dataset é sintético (CC0); em CRM real, o decaimento seria mais suave.
- O valor do deal aberto é o preço de tabela: nos ganhos, o valor fechado ficou entre 66% e 134% da tabela, com média de 100%.

**Riscos**

- **Zumbi pode ser CRM desatualizado.** Por isso Limpe é confirmar e encerrar ou atualizar, não descartar.
- **Vazamento pela conta.** Os 1.425 deals sem conta estão todos abertos, então "sem conta" equivale a "nunca fechou". Proibido como variável; o bloco 3 testa a guarda.
- **Possível artefato de recorte.** Os fechamentos do 1º trimestre de 2017 têm win rate de 82% (cerca de 61% depois) e o primeiro é em março. O bloco 2 investiga antes de treinar.
- **Recência pode parecer boa em AUC.** O plano de execução (Opus) já tinha visto isso num protótipo; a métrica primária foi fixada aqui, antes do código de avaliação, mas não às cegas.
- **Produto raro e caro.** O GTK 500, de maior preço do catálogo, tem só 25 deals fechados e pode puxar o topo do Foque. O preço aparece em todo card.
- **Sem controle de acesso.** "Quem é você?" não é login.
