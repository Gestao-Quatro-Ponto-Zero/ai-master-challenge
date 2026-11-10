# Auditoria das sessões — Challenge 003

A sessão #1 (orquestração) confere cada entrega das outras sessões antes do commit. Registro do que foi entregue, do que foi conferido e do que estava errado.

| Sessão | Papel | Pasta |
|---|---|---|
| #2 | Dados | `solution/data/`, `solution/analysis/` |
| #3 | Score | `solution/scoring/`, `solution/data/scored/` |
| #4 | App | `solution/app/` |
| #5 | QA e baseline | `solution/qa/` |

---

## 09/11 ~21:50 — Estado encontrado quando a #1 assumiu

Até então, a #1 só tinha lido o repositório e os arquivos de contexto. Não baixou nem analisou dados, então não havia nada a passar para a #2.

Ao assumir, a pasta já tinha trabalho das outras sessões, ainda sem auditoria e sem commit:

| Arquivo | Sessão provável | Situação |
|---|---|---|
| `solution/data/raw/*.csv` (5 arquivos, incluindo `metadata.csv`) | #2 | Baixados do Kaggle; aguardando o aviso de etapa da #2 |
| `solution/data/clean/*` + `solution/data/clean.py` + `cleaning_report.json` | #2 | Em andamento (gravados entre 21:48 e 21:49) |
| `solution/qa/baseline.md` | #5 | Em andamento |
| `solution/app/index.html` + `app/sample/` | #4 | Em andamento, com amostra no formato do contrato |
| `solution/analysis/`, `solution/scoring/`, `solution/data/scored/` | #2, #3 | Vazios |

**O que estava faltando:**
- `decisoes.md` estava em branco. As decisões da Etapa 0 só foram registradas agora (linhas 1–9), a partir da narrativa da preparação.
- Nada versionado. O `.gitignore` oficial ignora `submissions/`, então o git não via nenhum desses arquivos.

**Decisões técnicas já tomadas pela #2 que ainda dependem do Leandro** (aparecem no `cleaning_report.json` e serão levadas a ele com a entrega da #2):
- Data de referência fixa em 2017-12-31, a última `close_date` do arquivo.
- Correção de nomes: `GTXPro` virou `GTX Pro` (1.480 deals) e o setor `technolgy` foi corrigido (12 contas).
- Faixas de porte por tercis de receita e de funcionários.

---

## 09/11 — #5 QA: etapa 1 (baseline) e etapa 2 (checklist)

**Entregue:** `solution/qa/baseline.md`, que reconstrói a entrega típica de uma IA só com o brief e traz 12 erros dela medidos nos dados e 20 armadilhas para marcar, e `solution/qa/checklist.md`, o checklist de entrega.

**Conferência:** a #1 recalculou os números de forma independente, com um script próprio sobre `data/raw/`, data de referência 2017-12-31 e o typo de setor e o nome do produto corrigidos.

| Afirmação da #5 | Recalculado pela #1 | Situação |
|---|---|---|
| 8.800 deals; 4.238 Won / 2.473 Lost / 1.589 Engaging / 500 Prospecting; win rate 63,2% | Igual | ✅ |
| Diferença de win rate entre o melhor e o pior grupo: produto 4,8 p.p. | 4,8 (60,0–64,8) | ✅ |
| Setor 3,6 p.p. | 3,67 → **3,7** | ⚠️ truncado em vez de arredondado |
| Manager 2,3 p.p. | 2,3 | ✅ |
| Região 1,3 p.p. | 1,38 → **1,4** | ⚠️ truncado em vez de arredondado |
| Win rate por quartil de funcionários 64,1 / 61,4 / 63,9 / 63,2 | Igual | ✅ |
| Abertos sem conta: 1.088/1.589 Engaging, 337/500 Prospecting (68%) | Igual (68,2%) | ✅ |
| Correlação 1º × 2º semestre: conta −0,08; vendedor 0,36; win rate do vendedor 55,0–70,4%, mínimo de 79 deals | Igual | ✅ |
| Duração mediana: Lost 14 dias, Won 57; ciclo máximo 138 | Igual | ✅ |
| Chance de ganhar, para deals que já duraram d dias: 63 / 69 / 71 / 76% (d = 0, 14, 90, 120) | 63,2 / 68,6 / 71,3 com "≥ d"; em 120 dá 75,1 com "≥" e 75,6 com "> 120" | ⚠️ critério de corte não declarado; com "≥", o certo é 75% |
| 1.291/1.589 Engaging acima de 138 dias (mediana 165) | Igual | ✅ |
| `close_value` ÷ preço de tabela nos Won: mediana 1,00 (0,66–1,34) | Mediana 1,00, mín–máx 0,66–1,34 | ✅ |
| Fim de trimestre fecha 78–83% Won contra 49–57% nos outros meses | 78,5–82,8 contra 48,6–56,8 | ✅ |
| 5 vendedores sem deals | Os mesmos 5 nomes | ✅ |

**Problemas encontrados:**
1. **Bloqueante:** o item H1 do `checklist.md` cita nominalmente as empresas do candidato que não podem aparecer na entrega, justamente na regra que proíbe citá-las. O commit fica retido, porque o histórico do git vai junto no PR.
2. Arredondamento de setor (3,7) e região (1,4), e o critério de "depois de d dias" a declarar. Não muda nenhuma conclusão.

**Encaminhamento:** devolvido à #5 para corrigir os três pontos. O commit de `solution/qa/` sai depois da correção.

**Retorno da #5 (conferido):**
1. H1 reescrito de forma genérica. A busca por nomes de empresas, projetos e e-mails nos dois arquivos deu zero ocorrências, e os dois estão em LF. ✅
2. Setor 3,7 p.p. e região 1,4 p.p., com nota de que a diferença é calculada antes de arredondar. ✅
3. **A #1 errou neste ponto.** A #5 já usava o mesmo corte estrito (ciclo > d) nos quatro pontos, então o 76% (75,6) estava coerente. A #1 tinha comparado com "≥ d". A #5 declarou o corte e mostrou as duas versões: > d = 63,2 / 68,7 / 71,1 / 75,6%; ≥ d = 63,2 / 68,6 / 71,3 / 75,1%. A #1 conferiu: o ciclo mínimo é 1 dia, por isso d = 0 dá o mesmo nas duas. ✅

**Resultado:** `solution/qa/` aprovado e commitado.

---

## 09/11 — #2 Dados: limpeza e análise de sinal

**Entregue:**
- `data/raw/`: os 5 CSVs originais. A #2 moveu para cá os arquivos que estavam soltos em `data/`, sem alterar nada.
- `data/clean.py` gera `data/clean/` (as tabelas limpas, `deals.csv` com tudo junto e `cleaning_report.json`). As regras de limpeza estão em `data/README.md`.
- `analysis/signal.py` gera `analysis/signal_summary.json` e `analysis/tables/` (32 CSVs). A leitura está em `analysis/findings.md`.

**Conferência:**

| Verificação | Como | Resultado |
|---|---|---|
| Reprodutibilidade | Copiei `data/` e `analysis/` para uma pasta à parte, rodei os dois scripts e comparei os arquivos gerados com os entregues | ✅ Os 39 arquivos são idênticos, byte a byte |
| Coorte sem viés (engajados de 01/03 a 15/08/2017) | Recalculado | ✅ n = 3.718; fechou em 0–14 dias = 1.737 deals, 54,2%; em 15 dias ou mais = 1.981 deals, 67,2% |
| Fim de trimestre | Recalculado | ✅ 2.574 deals, 80,7%, contra 4.137 deals, 52,3% |
| Fim de semana como sinal de dado sintético | Recalculado sobre `engage_date` | ✅ 28,7% (a #2 diz 28,6%; a diferença é de base ou de arredondamento, sem efeito) |
| Engaging com mais de 138 dias e engajados nos últimos 90 dias | Recalculado | ✅ 1.291 e 110 |
| Variáveis sem sinal, p-valores e teste fora do tempo | Tabelas reproduzidas byte a byte; os spreads batem com os da #1 na auditoria da #5 | ✅ |
| Termos proibidos e fim de linha | Busca por nomes e e-mails; checagem de CRLF | ✅ Nenhuma ocorrência; tudo em LF |

**Achado da auditoria, levado ao Leandro junto com as decisões:** só **7 dos 1.589 Engaging** abertos têm até 14 dias, e só 18 têm até 30. O único sinal do dataset (as duas primeiras semanas) praticamente não se aplica ao pipeline atual. Na prática, nada nos dados ordena os deals abertos por chance. O que dá para usar é o valor (preço de tabela, ±10%), o estado do deal (dentro ou fora do ciclo histórico) e a qualidade do cadastro (sem conta).

**Resultado:** `data/` e `analysis/` aprovados e commitados. As decisões 1 a 6 do `findings.md` vão ao Leandro antes de a #3 construir o score.

---

## 09/11 — Pesquisa: como o G4 avalia (feita pela #1, a pedido do Leandro)

Leitura pública do repositório oficial, sem login e sem nenhuma interação:
- 239 PRs, 116 do challenge 003. Nenhum foi mesclado; os fechados foram todos fechados pelos próprios autores.
- O avaliador comentou em março, com notas de 0 a 10 de um assistente de avaliação por IA. **Correção feita pela #5:** a #1 tinha escrito que as notas 6,4 / 7,0 / 7,3 não foram aprovadas. Na verdade, a 7,0 e uma das 7,3 foram aprovadas em 23/03, depois que os candidatos acrescentaram uma seção mostrando onde conduziram a IA. A 6,4 não avançou (13/04, depois de 4 rodadas), e a outra 7,3 ficou sem decisão pública.
- Critérios citados nas devolutivas:
  - "Uso de IA" pesa 30% da nota;
  - o process log precisa mostrar onde o candidato corrigiu ou redirecionou a IA, e que hipóteses ele tinha antes;
  - a evidência tem que estar dentro do repositório;
  - dependências commitadas são bloqueador;
  - arquivos fora da pasta da submissão fazem a entrega ser devolvida.
- Desde 24/03 o retorno é por e-mail.

## 09/11 — #5 QA: benchmark dos 10 PRs mais completos do 003

**Entregue:** `solution/qa/benchmark-prs.md`. Os 10 PRs mais completos (ranqueados pela #1 por sinais de completude) foram lidos, e os 8 links publicados foram abertos. O texto está anonimizado (A–J).

**Conferência:**

| Item | Resultado |
|---|---|
| Anonimização | ✅ Nenhum nome nem login de candidato. A busca automática só achou a palavra "dias", um falso positivo |
| Termos proibidos e fim de linha | ✅ Nenhum termo; LF |
| Deals que fecham no 1º mês do trimestre duram no máximo 13 dias (mediana 7); no 2º e no 3º mês, até 125 e 138 | ✅ Recalculado: 1.779 deals, mediana 7, máximo 13; 68/125; 75/138 |
| Controlando pelo mês de fechamento, o efeito das 2 semanas some (3º mês: rápidos 86% × lentos 81%) | ✅ |
| Controlando pelo mês de início, o efeito fica (rápidos × lentos: 50×69, 57×64, 63×69) | ✅ 50×69, **56×63**, 63×69 (diferença de arredondamento) |

**Achado que muda a estratégia:** os cinco achados de dados que tratávamos como diferencial (chance plana, 81% parados, 68% sem conta, data fixa, GTXPro) aparecem em 6 dos 10 concorrentes. A fórmula que a #3 esboçou (valor + curva de idade) é, em essência, a de 3 deles. Daqui em diante, o diferencial precisa vir de três coisas:
1. a validação, comparando a fila também com "mais novo primeiro", regra que nem os melhores conseguiram superar;
2. o que a ferramenta faz: o ciclo de ação e a limpeza do pipeline;
3. o diagnóstico de dados sintéticos, que nenhum dos 10 fez.

**Encaminhamentos:**
- #5: nota curta no item E do `baseline.md` (a subida até 76% vem do corte de 2016 e do fim de trimestre). Liberada pela #1, porque complementa sem mudar a conclusão.
- #2: acrescentar ao `findings.md` a regra do 1º mês do trimestre e a distinção entre controlar pelo início e pelo fechamento.
- #3: incluir "mais novo primeiro" no backtest e rever o componente "conta" (hoje tiraria 20 pontos de 68% do pipeline). As duas coisas vão ao Leandro junto com as decisões pendentes.
- #4: o `COMO-RODAR.md` precisa acompanhar o desenho final dos componentes.

## 09/11 — #5 QA: critérios reais do avaliador e nota no baseline

**Entregue:** seção "Critérios reais do avaliador" no `benchmark-prs.md` (casos K–R, anonimizados); seção 9 do `checklist.md` com 16 itens verificáveis (A1–A16, dos quais A8 e A9 são bloqueadores); nota no item E do `baseline.md`, liberada pela #1.

**Conferência:** nenhum nome de candidato nem do avaliador nos 3 arquivos (a busca só achou a palavra "Fontes", falso positivo). Nenhum termo proibido; tudo em LF. A correção da #5 sobre as notas aprovadas foi aceita e registrada acima. O caso "AUC 0,43" que a #1 citou existe (comentário público no PR 46, de 24/03); só não estava nos arquivos que a #5 leu.

**Ponto que vai ao Leandro junto com as decisões do score:** no único 003 aprovado, o primeiro pedido do avaliador foi aproveitar mais dados do dataset. Por isso, mesmo que a chance por segmento saia do score, a entrega precisa de uma tabela com cada atributo das 4 tabelas → testado → resultado → onde aparece (no score, como contexto na tela ou fora) (A11), e de contexto da conta, do produto e do time no detalhe do deal (A12).

## 09/11 — #2 Dados: origem fictícia e duas evidências novas

**Entregue:** `findings.md`, `signal.py` e `signal_summary.json` atualizados, mais 3 tabelas novas (ciclo por mês do trimestre; efeito das 2 semanas controlado pelo mês de fechamento e pelo mês de início).

**Conferência:**
- Reprodução numa cópia separada: os 42 arquivos saíram idênticos. ✅
- Números iguais aos recalculados pela #1 na auditoria do benchmark. ✅
- Ressalva honesta da #2: o efeito das 2 semanas só é forte para quem começou no 1º mês do trimestre (49,7% × 68,9%). No 2º mês não é significativo e no 3º fica no limite. ✅
- Origem documentada: o dataset é o "CRM Sales Opportunities" da Maven Analytics, de uma empresa fictícia de hardware. Várias contas têm nomes de ficção (Acme Corporation, Bluth Company, Bubba Gump). Com isso, "parecem sintéticos" passa a ser "são fictícios", com duas linhas de prova separadas: a fonte e os padrões medidos. ✅
- Sem termos proibidos; tudo em LF. ✅

## 10/11 — Banco: duas versões das migrations, decisão da #1

Por mensagens que chegaram fora de ordem, a #2 e a #4 escreveram o banco ao mesmo tempo:
- #2: 9 migrations, conferidas só por parser (sintaxe, prefixos, FKs), commit 749312e;
- #4: 18 migrations, validadas executando num Postgres em memória (PGlite, sem conexão externa), com conferência pelo catálogo e 45 testes de uso.

**Decisão da #1:** a base oficial é a versão da #4, porque foi validada por execução e já está alinhada ao app. A #2 passa a mantê-la em solution/db/ e faz em cima dela as próximas migrations. A versão da #2 fica no histórico do git e numa pasta fora do repositório; nada foi apagado.

**Segurança:** uma revisão automática apontou, na versão da #2, um limite de gravação contornável (contava correlation_id enviado pelo cliente) e a isenção do usuário "sistema" acessível sem login. A versão escolhida tem o mesmo risco por outro caminho (correlation_id como parâmetro; função de contexto "sistema"). A correção entra antes de qualquer aplicação no banco: correlation_id gerado no servidor, reuso recusado e contexto "sistema" só por um papel de carga separado do app.

## 10/11 — Parada geral, causa dos conflitos e regras de coordenação

**O que deu errado, e foi erro de orquestração da #1:**
1. A #1 pediu as migrations à #4 e, minutos depois, passou para a #2. A troca ficou na fila da #4, que seguiu escrevendo: duas versões do banco.
2. A #1 liberou a #5 para aplicar a versão antiga e corrigiu em seguida. A #5 aplicou a versão certa (lote 1 da #2).
3. Mensagens enfileiradas ou retidas por diferença de modo de permissão fizeram sessões trabalharem com decisões já superadas.
4. A instalação do app (node_modules, ~310 pacotes) dentro do Google Drive, somada a 5 sessões e validadores, deixou a máquina com ~500 MB livres.

**O que foi feito:** o Leandro parou as sessões. A #1 apagou o node_modules (que se regenera com npm install), moveu as versões antigas do banco para fora do repositório (sem apagar) e commitou o estado (7ab3bec). O lote 1 está no banco e confere: 9 tabelas, 8.800 deals, 85 contas, 43 usuários, 9.006 linhas de auditoria.

**Regras aprovadas (decisão 39):** ordens numeradas com confirmação; dono único por pasta; sequência no mesmo artefato; até 2 sessões pesadas por vez; dependências fora do Drive; mesmo modo de permissão; quadro de status (local).

## 10/11 — Lote 2 aplicado; a 0026 foi aplicada antes do ajuste

A #5 aplicou 0007–0026 no Supabase, sem erro. Contagem: 29 tabelas, 60 FKs (RESTRICT, validadas e com índice), 68 funções, 3 views, 86 gatilhos, 104 índices. Os dados foram preservados: 8.800 deals, 85 contas, 43 usuários, receita ganha de US$ 10.005.534.

**Erro de orquestração da #1:** o aviso "não aplicar a 0026 ainda" chegou à #5 depois que ela já tinha aplicado a 0026 original (commit d6c4f12). A #1 já tinha commitado a 0026 ajustada (4017322), o que deixava o repositório diferente do banco. Correção, proposta pela #5: a 0026 do repositório volta à versão aplicada, e o ajuste (teto exato) entra como migration nova, 0027.

