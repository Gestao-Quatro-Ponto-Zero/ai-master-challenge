# Submissão — Ronaldo Tkotz — Challenge 001 (Diagnóstico de Churn)

## Sobre mim

- **Nome:** Ronaldo Tkotz
- **LinkedIn:** [linkedin.com/in/ronaldoeng](https://www.linkedin.com/in/ronaldoeng/)
- **Challenge escolhido:** 001 — Diagnóstico de churn da RavenStack

---

## Como avaliar esta submissão

Sugiro esta ordem, do mais rápido ao mais profundo:

| # | O quê | Tempo | Link |
|---|---|---|---|
| 1 | **Relatório de diagnóstico:** as três perguntas do desafio, com gráficos e a lista de contas | ~10 min | **[Abrir no navegador](https://raw.githack.com/ronaldomt/ai-master-challenge/submission/ronaldo-tkotz/submissions/ronaldo-tkotz/solution/relatorio-churn.html)** · [Markdown no GitHub](solution/relatorio-churn.md) |
| 2 | **Vídeo da ferramenta:** visão geral, recorte (drill-down), analista de IA e montagem do PowerPoint | 2 min | **[Assistir no Google Drive](https://drive.google.com/file/d/14ctMS_deoJNzGt1KyqubhB7UHZZSIxQn/view?usp=sharing)** · [cópia no repositório](solution/demo/ravenstack-demo.mp4) |
| 3 | **Ferramenta publicada** (opcional): telas, recorte, analista que responde em SQL e montagem de apresentação | livre | **[ravenstack-churn.vercel.app](https://ravenstack-churn.vercel.app)**; o login e a senha de avaliador estão na descrição do pull request |
| 4 | **Como usei IA:** este README (seção Process Log) e o diário com o crédito de cada decisão | ~10 min | [`decisions.md`](process-log/decisions.md) · [conversas exportadas](process-log/chat-exports/) |

O GitHub mostra arquivos `.html` como código. O link "Abrir no navegador" serve a mesma página do repositório pelo raw.githack, que a entrega como página. Se ele não abrir, baixe o [`relatorio-churn.html`](solution/relatorio-churn.html) e abra no Chrome. A página tem um botão no topo para baixar o relatório em Markdown.

### Onde está cada entrega pedida

| O desafio pede | Onde está |
|---|---|
| 1. O que está causando o churn (causa raiz, cruzando tabelas) | Relatório, seção 1 |
| 2. Segmentos mais em risco, com contas específicas | Relatório, seção 2, e a lista em [`contas-em-risco.csv`](solution/contas-em-risco.csv) (72 contas para agir e 110 para conciliar) |
| 3. O que a empresa deveria fazer (ações priorizadas com impacto estimado) | Relatório, seção 3: nove ações com dono, prazo e impacto |
| Diferencial: dashboard interativo e automação para o CS | A ferramenta (item 3 acima) e o [código](solution/app/) |
| Process log (obrigatório) | Seção Process Log abaixo, [`decisions.md`](process-log/decisions.md) (D1 a D56), [conversas exportadas](process-log/chat-exports/), [scripts de verificação](process-log/verification/), histórico do git e as planilhas do Gemini (em Evidências) |

---

## Executive Summary

Cruzei as cinco tabelas da RavenStack numa base SQL validada e conferi cada afirmação contra o dado.

O churn não tem uma causa única. Plano, uso, erros, suporte, satisfação, país e trial mudam pouco a chance de cancelar quando olhados sozinhos. Somados, formam uma colcha de retalhos.

A causa raiz é que a empresa não registra o churn de forma que permita explicá-lo:

- o motivo registrado não tem relação com o que o cliente escreveu (p = 0,955);
- um quarto dos cancelamentos é silencioso;
- nenhum ticket tem hora de abertura;
- o CRM e o faturamento discordam sobre 110 contas que ainda pagam US$ 2,07 mi de MRR.

O segmento mais exposto é **DevTools** (31% de churn contra 19%, o único corte significativo).

A recomendação principal é conciliar o CRM com o faturamento e corrigir a captura do motivo, com um agente classificador. Em paralelo, o CS deve agir já sobre 72 contas com sinais acumulados (US$ 1,46 mi de MRR) e sobre 33 renovações anuais sem auto-renew (US$ 1,08 mi de ARR).

---

## Solução

| Entrega | Onde |
|---|---|
| **Relatório de diagnóstico (o deliverable principal)** | Página com gráficos e botão para baixar o Markdown: **[abrir no navegador](https://raw.githack.com/ronaldomt/ai-master-challenge/submission/ronaldo-tkotz/submissions/ronaldo-tkotz/solution/relatorio-churn.html)** (arquivo: [`relatorio-churn.html`](solution/relatorio-churn.html)). O mesmo texto em Markdown: [`relatorio-churn.md`](solution/relatorio-churn.md) |
| Contas específicas: lista A (agir) e lista B (conciliar) | [`solution/contas-em-risco.csv`](solution/contas-em-risco.csv) |
| Renovações anuais em 90 dias sem auto-renew | [`process-log/verification/outputs/12_renovacoes_90d_sem_autorenew.csv`](process-log/verification/outputs/12_renovacoes_90d_sem_autorenew.csv) |
| Base SQL a partir dos CSVs (schema, tipagem, 43 checagens, views) | [`solution/sql/`](solution/sql/) e o banco em `solution/app/data/ravenstack.db` |
| **Vídeo de 2 minutos mostrando a ferramenta** (narração e legendas) | **[assistir no Google Drive](https://drive.google.com/file/d/14ctMS_deoJNzGt1KyqubhB7UHZZSIxQn/view?usp=sharing)**; cópia em [`solution/demo/ravenstack-demo.mp4`](solution/demo/ravenstack-demo.mp4), legenda em [`ravenstack-demo.srt`](solution/demo/ravenstack-demo.srt); como foi feito: [`process-log/video/`](process-log/video/) |
| Ferramenta interativa (opcional): telas, drill-down, analista com SQL, apresentação | https://ravenstack-churn.vercel.app ([código](solution/app/)); login e senha de avaliador na descrição do pull request |

### Estrutura da pasta e como rodar

A submissão segue a estrutura do `CONTRIBUTING.md`:

```
submissions/ronaldo-tkotz/
├── README.md                  ← este arquivo (template do G4)
├── solution/                  ← a solução
│   ├── relatorio-churn.md         ← o relatório (deliverable principal)
│   ├── relatorio-churn.html       ← o mesmo relatório em página, com gráficos e download do .md
│   ├── contas-em-risco.csv        ← contas específicas (listas A e B)
│   ├── demo/                      ← vídeo de 2 minutos da ferramenta, com legenda
│   ├── sql/                       ← CSV → SQLite: schema, tipagem, checagens, views
│   └── app/                       ← a ferramenta (Next.js), com o banco em data/ravenstack.db
└── process-log/               ← evidências de uso de IA
    ├── decisions.md               ← diário: cada decisão, de quem foi (humano ou IA) e como foi verificada
    ├── chat-exports/              ← as conversas com a IA (Claude Code), exportadas e sanitizadas
    ├── verification/              ← scripts numerados e as saídas de cada checagem
    ├── dashboard/                 ← o desenho do dashboard feito à mão
    ├── video/                     ← roteiro e scripts que gravaram o vídeo
    └── mapa-entrega-e-dados.md
```

Para refazer os números (Python 3, sem dependências além da biblioteca padrão, a partir de `submissions/ronaldo-tkotz/`):

```bash
python -I solution/sql/build_db.py <pasta_com_os_5_csv_do_kaggle> /tmp/ravenstack.db   # recria o banco e imprime as checagens
python -I process-log/verification/21_sinais_e_contas.py                                # números do relatório e a lista de contas
python -I process-log/verification/22_relatorio_html.py                                 # gera o relatorio-churn.html a partir do .md (usa a biblioteca markdown)
```

Os scripts 01 a 18 usam pandas e leem os CSVs (`python -I 15_ponte_mrr_conta.py <pasta_dos_csv>`). Para rodar a ferramenta localmente, siga o [README do app](solution/app/README.md).

### Abordagem

1. **Exploração com verificação** (scripts 01 a 18). A IA levantava as hipóteses, eu contestava, e cada contestação virava um script com saída salva.
2. **Recomeço sobre uma base SQL confiável** (D14). Os CSVs foram carregados sem alteração, as tabelas foram tipadas com chaves e domínios, e as inconsistências foram contadas sem ser corrigidas.
3. **Definições fixadas antes dos números** (D17 a D21, D36):
   - data de corte em 31/12/2024;
   - churn é o evento em `churn_events`;
   - a taxa por conta usa o `churn_flag`.
4. **O dashboard foi desenhado de trás para frente** (D19, D22): primeiro o que o CEO precisa ver, depois as consultas.
5. **O diagnóstico final** (D51) juntou os achados num relatório, conferiu de novo cada ponto no banco (`21_sinais_e_contas.py`) e montou a lista de contas.

### Resultados / Findings

Estão resumidos no relatório. Os principais:

- **Não há causa única.** Os modelos ficam com AUC de 0,44 a 0,54, abaixo de um placebo (0,56). A soma dos sinais sobe a taxa de churn devagar: 18,9% sem nenhum sinal e 33% com 4 ou mais (6 contas).
- **O churn não é registrado de forma explicável.**
  - Só 22% dos comentários batem com o motivo, e 25% dos cancelamentos não têm comentário.
  - Os 2.000 tickets foram abertos à 00:00:00.
  - 13.198 registros de uso e 1.077 tickets têm data anterior ao cadastro da conta.
  - 110 contas "canceladas" ainda pagam US$ 2,07 mi de MRR.
  - O pico de dezembro/2024 é provavelmente um artefato da `end_date`.
- **A satisfação mede o atendimento, não o produto.** Ela não varia com a taxa de erro da conta, e não existe medida da experiência com o produto.
- **Segmentos:**
  - DevTools tem 31% de churn, contra 19,4% no resto (p = 0,009).
  - O trial é 19% da base e 23% do churn.
  - Cinco recursos beta têm erro de 7,5% a 9,5%, contra 5,2% a 6,1% na versão estável.

### Recomendações

Estão em ordem de prioridade, com dono, prazo e impacto estimado na seção 3 do relatório:

1. Conciliar o CRM com o faturamento.
2. Corrigir a captura de dados, com um agente classificador do motivo.
3. CS nas listas A e de renovação.
4. Revisar o onboarding de DevTools.
5. Montar um monitor de engajamento com um programa de retenção.
6. Levar para a ativação os recursos das assinaturas longas.
7. Baixar o erro dos recursos beta.
8. Medir a experiência com o produto.
9. Só então, o modelo preditivo.

### Limitações

- Os dados são sintéticos, e alguns padrões parecem do gerador (o pico de dezembro, NRR de 140% e comentários fixos).
- Com 110 contas canceladas, diferenças de 3 a 5 pontos não se distinguem do acaso.
- A lista de contas é uma fila de atenção, não uma probabilidade de churn.
- As estimativas de impacto servem para ordenar as ações, não para orçamento.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| Claude Code (Claude Opus) | Scripts de verificação em Python, base SQL, código da ferramenta (Next.js), checagem de cada hipótese no banco, redação dos rascunhos |
| Claude (whiteboard) | Desenho do dashboard (D22) |
| Gemini (no Google Sheets) | Minha análise exploratória inicial nas planilhas (links nas evidências). Os números que trouxe dela foram conferidos contra os CSVs (D12, D52) |
| DeepSeek | O analista dentro da ferramenta: responde em SQL, monta telas e escreve a apresentação |
| Datasette | Navegar no banco SQL durante a exploração |
| Vercel + GitHub | Publicação da ferramenta com deploy automático (D48) |

### Workflow

1. Li o desafio e pedi à IA uma decomposição antes de qualquer conclusão (D1).
2. A IA rodou a primeira exploração. Contestei a primeira versão em seis pontos (D5), e cada ponto virou um script de verificação.
3. Trouxe hipóteses de negócio:
   - maturidade das contas (D7);
   - renovação anual (D8);
   - identidade da conta separada da identidade da assinatura (D10);
   - taxa de churn subindo (D11);
   - concentração do ARR perdido (D12).

   A IA testou cada uma no dado, e o diário registra o que conferiu e o que não conferiu.
4. Decidi recomeçar sobre uma camada SQL validada (D14) e fixei a data de corte e a definição de churn (D17, D20).
5. Desenhei o dashboard e as telas. A IA implementou, e eu revisei cada tela na tela (D22 a D50).
6. No fechamento, escrevi os achados e as recomendações. A IA conferiu cada ponto no banco e apontou o que não se sustentava. Ajustei a leitura, e a IA redigiu o relatório e a lista (D51).

**Iterações:** a conversa principal tem 93 mensagens minhas entre 14 e 17/11, o diário tem 56 decisões registradas, e o git tem um commit por etapa, cada um dizendo o que foi meu e o que foi da IA.

O diário completo, com o crédito de cada decisão (humano ou IA), está em [`process-log/decisions.md`](process-log/decisions.md). Os scripts e as saídas estão em [`process-log/verification/`](process-log/verification/).

### Onde a IA errou e como corrigi

- **"500 de 500 contas ativas" (D5):** a IA tratou a tabela de assinaturas como verdade. Eu apontei as 110 contas com `churn_flag`, e daí saiu o achado da contradição entre CRM e faturamento (US$ 2,07 mi).
- **"0 contas sem assinatura em todos os trimestres" (D4):** a IA só tinha checado 31/12. A contagem por trimestre corrigiu o gráfico antes de publicar.
- **"O cliente costuma abrir outra assinatura" (D8):** a planilha que eu pedi como prova mostrou que, em 95,5% dos casos, a conta já tinha outra assinatura ativa. A frase sugeria uma renovação que não existe.
- **"Quase toda assinatura encerrada é compensada" (D10 → D11):** a soma por trimestre escondeu a aceleração da taxa mensal. Minha réplica com o churn ratio mês a mês expôs isso.
- **Inferências numa etapa que deveria ser só de checagens (D14):** pedi para tirar as interpretações e manter só as contagens.
- **O Gemini inventou números na transcrição da planilha (D52):** a aba de transcrição dizia 486 tickets escalados (o CSV tem 95, e a aba de cálculo dele também), módulos "Custom Workflows" e "API Integrations" (os recursos vão de `feature_1` a `feature_40`) e US$ 1,15 mi de reembolsos (o total real é US$ 8.652). No export dele, os ~55% do ARR perdido eram dos EUA, não do Reino Unido (D12). Tudo foi pego conferindo contra os CSVs antes de entrar na análise.
- **Efeito de maturidade que não existia (D7):** a IA quase concluiu que contas antigas cancelam mais. O efeito vinha de 35 contas sem data de evento, que ela tinha datado em 31/12. A checagem de sensibilidade derrubou o efeito.
- **Estrutura da submissão fora do esquema (D54, D56):** a IA pôs a entrega numa subpasta `001-churn/`, herdada de um plano para os quatro desafios, e deixou publicado o primeiro rascunho do diagnóstico. Apontei os dois antes do PR. A pasta passou a seguir o `CONTRIBUTING.md`, e o rascunho saiu.
- **A janela do analista não rolava (D55):** uma resposta longa ficava cortada. Eu notei durante o uso, e a IA reproduziu e corrigiu o problema.

### O que eu adicionei que a IA sozinha não faria

- **A leitura de colcha de retalhos:** nenhuma causa isolada, várias diferenças pequenas que precisam ser vistas juntas, e a ferramenta como o lugar onde elas se juntam.
- **As observações que viraram as provas mais fortes:**
  - o horário dos tickets sempre à meia-noite;
  - o motivo do churn incompatível com o comentário;
  - a ideia de um agente classificador para corrigir o motivo.
- **A contestação da primeira versão (D5)** e as hipóteses de negócio (D7, D8, D10, D11, D12), que levaram aos achados da contradição entre tabelas, do calendário de renovação e da ponte de MRR por conta.
- **A decisão de recomeçar sobre SQL validado** e de desenhar o dashboard de trás para frente.
- **As recomendações de negócio:**
  - revisão do onboarding;
  - recursos das assinaturas longas na jornada de ativação;
  - monitor de engajamento com programa de retenção;
  - atenção ao churn silencioso e às contas com muitos tickets;
  - a leitura financeira diferente para contas em trial.
- **A separação entre fato e inferência** em cada réplica (D7): o número pode ser verdadeiro sem provar a causa.

---

## Evidências

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [x] Outro: vídeo de 2 minutos da ferramenta em uso, gravado por automação, com narração e legendas ([Google Drive](https://drive.google.com/file/d/14ctMS_deoJNzGt1KyqubhB7UHZZSIxQn/view?usp=sharing) · [`solution/demo/`](solution/demo/))
- [x] Chat exports: [`process-log/chat-exports/`](process-log/chat-exports/). São a conversa principal com o Claude Code (14 a 17/11) e a conversa lateral que trouxe as análises do Gemini. Ficaram as mensagens, as respostas e a lista de ferramentas chamadas. Saíram as saídas das ferramentas e os dados pessoais (o [README da pasta](process-log/chat-exports/README.md) diz o critério).
- [x] Git history: cada commit `[001]` diz o que foi meu e o que foi da IA
- [x] Outro: o diário de decisões ([`process-log/decisions.md`](process-log/decisions.md), D1–D56), os scripts de verificação com as saídas ([`process-log/verification/`](process-log/verification/)), o desenho do dashboard ([`process-log/dashboard/`](process-log/dashboard/)) e a ferramenta publicada
- [x] Outro: minhas análises exploratórias no Google Sheets com o Gemini, abertas para leitura:
  - [Churn Analitcs](https://docs.google.com/spreadsheets/d/1sKF8GP8BQWzq41tUhrFkaac7xq-FtixMqFXpHvxXQVY/edit?usp=sharing)
  - [Copy of Churn Analitcs](https://docs.google.com/spreadsheets/d/1udHeyyVl7g8Uq-EWYCEEtZ76hsll3ap8YljO9XHM_uE/edit?usp=sharing)
  - [Churn Analitcs_V3](https://docs.google.com/spreadsheets/d/1vxy5i3QP5ydSK1Xs5h5CfzRLLbWPKvrAyYf-pu7vVMc/edit?usp=sharing)

---

_Submissão enviada em: 17/11/2026_
