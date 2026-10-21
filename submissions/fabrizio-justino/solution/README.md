# Lead Scorer — Challenge 003 (Vendas / RevOps)

## Executive summary

Construímos uma ferramenta web que diz a cada vendedor, na segunda-feira, **o que atacar, o que
nutrir e o que limpar** no pipeline, e explica o porquê de cada score. O principal achado veio
de testar antes de confiar:

- **Perfil não prevê nada neste histórico.** Vendedor, conta, produto e setor não separam ganho
  de perda (AUC ~0,50, cara ou coroa).
- **O tempo prevê.** A chance de um deal ganhar até o fim do trimestre, dada a idade dele, tem
  AUC de 0,63 a 0,72 e é calibrada num backtest sem vazamento.
- **62% do pipeline está morto.** Nenhum deal do histórico ganhou depois de 138 dias em
  Engaging (0 de 13.871 no backtest), e 1.291 dos 2.089 deals abertos já passaram disso.

A ferramenta prioriza pelo que dá para ganhar no trimestre e liga um **modo emergência** no
último mês, quando a meta está em risco, com a lista de deals que fecha o gap. Ela também envia
e-mails semanais separados para equipe e gestão. Uma camada de IA escreve os textos sobre
números do motor, sempre conferidos; sem chave, tudo funciona com textos automáticos.

Ferramenta para o vendedor abrir na segunda-feira e saber **onde focar**. Cada deal aberto
recebe:

- um **score de prioridade (0–100)**;
- uma **ação recomendada**;
- a **chance calibrada** de ganhar no prazo e o **valor esperado**;
- os **motivos** do score, em linguagem de vendedor.

Em volta disso:

- **alertas e lembretes por stage**;
- um **modo emergência** para fim de trimestre com meta em risco;
- uma **visão de time** para o manager;
- uma lista de **cross-sell**.

Stack: backend **FastAPI** + frontend **Next.js 15 / shadcn/ui / Tailwind**.

```
backend/   FastAPI + pandas
  app/config.py       pesos, limites, janelas — tudo ajustável sem mexer na lógica
  app/dados.py        carga dos 4 CSVs + snapshot(t): o pipeline como estava na data t
  app/scoring.py      benchmarks, estimador de chance, score explicável, ação
  app/calibracao.py   backtest semanal + recalibração isotônica da chance
  app/metricas.py     meta, ritmo, cobertura, velocidade, capacidade, qualidade de dado
  app/emergencia.py   gap da meta, lista de resgate, deal grande esfriando
  app/alertas.py      alertas por deal/stage e lembretes do time
  app/crosssell.py    "próximo produto" por conta
  app/motor.py        orquestra tudo para uma data (com cache)
  app/consultas.py    regra de cada consulta (usada pela API, pela IA e pelos e-mails)
  app/ia.py           camada de IA (OpenAI): briefing, explicação, chat, resgate, rascunhos, win-loss
  app/emails.py       e-mails de equipe e de gestão (gera arquivos ou envia via SMTP)
  app/main.py         API
  .env.example        credenciais EXCLUSIVAS deste projeto (copiar para .env)
  config/             destinatarios.exemplo.json (copiar para destinatarios.json)
  data/               dataset CRM Sales Predictive Analytics (CC0)
  tests/              testes da API, da IA (com LLM simulado) e dos e-mails
frontend/  Next.js — repassa /api/* para o backend (next.config.mjs)
(../docs e ../process-log ficam ao lado desta pasta, na submissão)
```

## Setup

Pré-requisitos: **Python 3.11+** e **Node 20+**.

```bash
# 1. Backend (porta 8000) — o startup leva ~6s (roda o backtest de calibração)
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000

# 2. Frontend (porta 3001) — em outro terminal
cd frontend
npm install
npm run dev
```

Abra **http://localhost:3001**. No Windows, `start.bat` na raiz faz os dois passos.

**IA e e-mails (opcional):** copie `backend/.env.example` para `backend/.env` e preencha.

- **IA:** `LEAD_SCORER_OPENAI_API_KEY` é uma chave de uma conta OpenAI criada **só para este
  projeto**. A chave é lida apenas dessa variável; um `OPENAI_API_KEY` genérico do ambiente é
  ignorado. Sem chave, tudo funciona com textos automáticos.
- **E-mails:** veja a seção "E-mails automáticos".

- Testes do backend: `cd backend && python -m pytest -q` (23 testes).
- A API documentada fica em http://localhost:8000/docs.

| Variável | Padrão | Para quê |
|---|---|---|
| `LEAD_SCORER_DATA_REFERENCIA` | último `close_date` (2017-12-31) | data padrão da tela |
| `LEAD_SCORER_META_FATOR` | `1.0` | meta = média trimestral × fator (ex.: `1.1` = +10%) |
| `LEAD_SCORER_DATA_DIR` | `backend/data` | apontar para outro export do CRM |
| `LEAD_SCORER_API_URL` (frontend) | `http://localhost:8000` | onde o Next encontra o backend |

### Como usar

1. **Escolha a data.** O dataset termina em 31/12/2017, que é o último dia do trimestre.
   O seletor "Ver o pipeline em" reconstrói o pipeline de qualquer segunda-feira anterior sem
   olhar o futuro. O botão **"Simular pressão de fim de trimestre"** leva a 04/12/2017, a 27
   dias do fechamento, onde o modo emergência liga.
2. **Filtre** por região → manager → vendedor.
3. **Veja os cards de ação** e clique para filtrar.
4. **Abra um deal** para ver "Por que score X?" e "O que fazer".
5. **Use as abas:**
   - **Alertas:** fila do mais grave para o mais leve.
   - **Time:** ritmo, cobertura, carga.
   - **Cross-sell.**
   - **Como o score funciona:** o backtest.

## Lógica

### O que os dados mostraram (e mudou o desenho)

| Pergunta | Resultado |
|---|---|
| Vendedor, conta, produto, setor, histórico da conta, afinidade do vendedor separam ganho de perda? | **Não.** AUC 0,49–0,52 num backtest temporal (0,50 = cara ou coroa). Setor, região, manager e porte têm win rate de 61–66% em todas as faixas. |
| O deal vai ganhar **até o fim do trimestre**, dado há quanto tempo ele está em Engaging? | **Sim.** AUC 0,63 entre deals dentro do ciclo; 0,72 no pipeline inteiro. |
| Deal que passou do maior ciclo já fechado (138 dias) ainda ganha? | **Nunca.** Em 13.871 observações do backtest, 0 ganharam. Hoje são 1.291 deals (62% do pipeline aberto). |
| Ganhos se concentram no fim do trimestre? | **Sim.** Fechamentos no último mês do trimestre ganham 81%, contra 52% nos outros meses. |
| close_value ≈ preço de tabela? | Sim, razão média de 0,996. Usado como "desconto histórico" por produto. |

Conclusão: neste histórico, a única coisa que dá para prever é **o tempo**. Por isso o score
responde a pergunta da segunda-feira: *"o que eu consigo ganhar neste trimestre?"*. Atributos
que não separam ganho de perda ficaram de fora, porque colocá-los no score seria ruído com cara
de precisão.

### Chance de ganhar no prazo

`P(ganhar até o fim do horizonte | deal tem N dias em Engaging)`. O horizonte é o fim do
trimestre, ou o do próximo se faltarem menos de 7 dias. O cálculo tem duas etapas:

1. **Estimador com censura** (`Benchmarks.chance_bruta`). Usa só o que já tinha fechado na
   data de referência e conta, no denominador, os deals ainda abertos que já passaram da
   janela sem fechar. Sem esse termo, o estimador ignora quem nunca fecha e fica otimista
   demais: no backtest, previa 80% quando o real era 30%.
2. **Recalibração isotônica, rolling-origin** (`calibracao.py`). O backtest tem 38
   segundas-feiras (62.483 observações). A taxa real de cada faixa, forçada a ser crescente,
   vira a probabilidade usada. Para cada data *t*, a curva só usa observações cujo desfecho
   já era conhecido em *t*: simular 04/12/2017 não enxerga nada posterior a essa data. Sem
   histórico suficiente (antes de ~julho/2017), a tela avisa e mostra a chance bruta. A chance
   real sobe de ~5% para ~41–47% e estabiliza: neste dataset, nenhum deal passa disso.
3. **Faixa de incerteza** (Wilson 95%) sobre a amostra de deals daquela idade, mostrada no
   detalhe do deal. No platô da calibração, a faixa é estreita de verdade (milhares de
   deals por faixa), e a tela mostra "±<1 p.p.". O sinal é fraco, não impreciso.
4. **Prospecting não recebe chance** (fica "n/d"): o CRM não tem data de engajamento para
   esses deals, então não existe histórico comparável. Eles seguem uma trilha própria, com a
   ação **Primeiro contato**, e ficam fora do valor esperado.

### Score de prioridade (0–100)

| Pilar | Peso | Cálculo |
|---|---|---|
| Chance de ganhar no prazo | 60 | chance calibrada ÷ a maior chance possível no horizonte |
| Valor do deal | 25 | preço em escala log (o catálogo vai de US$ 55 a US$ 26.768, um fator de 500×) |
| Engajamento e dados | 15 | Engaging > Prospecting; conta preenchida |

**Valor esperado** = chance × preço de tabela × desconto histórico do produto. É ele que
ordena os deals dentro de cada ação e monta a lista de resgate.

**Por que duas métricas:** o **score** serve à leitura humana. É um número de 0 a 100 que se
explica em três barras e decide a **ação**. O **valor esperado** serve à ordenação, porque é
a conta honesta de "quanto isso vale para o trimestre".

**Ação recomendada:**

| Ação | Regra |
|---|---|
| **Atacar agora** | top 15% de score entre os deals vivos da data (~7 por vendedor numa semana típica) |
| **Nutrir** | entre os percentis 60 e 85 |
| **Primeiro contato** | Prospecting (trilha própria, sem chance) |
| **Requalificar** | passou de 138 dias e preço ≥ US$ 1.000 |
| **Encerrar** | passou de 138 dias e preço < US$ 1.000 |
| **Baixa prioridade** | o restante |

- **Os cortes são percentis por data, não números fixos.** A curva de calibração muda com a
  data (rolling-origin): com cortes fixos de 85/70, "Atacar agora" variava de 82 a 893 deals
  conforme a semana.
- **"Requalificar" não é "continuar tentando".** Fora do ciclo a chance é zero, caro ou
  barato. Significa perguntar ao cliente e, se o projeto continuar, **encerrar este deal e
  abrir uma oportunidade nova, com o relógio zerado**.
- **Limitação conhecida:** em datas com horizonte longo (ex.: 31/12, a 90 dias), quase todo
  deal vivo bate o teto da chance, e o desempate passa a ser o valor.

A lista é ordenada pela ação primeiro: um zumbi caro nunca fica acima de um deal saudável.

### Alertas e lembretes

| Situação | Alerta |
|---|---|
| Prospecting sem engajamento | lembrete: agendar o 1º contato |
| Engaging até 14 dias (mediana de vida dos deals perdidos) | **zona de risco**: crítico se o valor for alto, senão lembrete |
| Engaging além do ciclo típico do produto | **reta final**: crítico se o valor for alto, senão lembrete |
| Deal grande (top 10%) acima do ciclo mediano ou que caiu de faixa em 7 dias | **esfriando**: crítico |
| Deal na lista de resgate da meta do próprio vendedor | **resgate**: crítico |
| Deal além de 138 dias | só no detalhe do deal, e agregado num alerta de **limpeza em massa** |
| Conta não preenchida | só no detalhe do deal, e agregado por vendedor em **qualidade de dado** |

**Crítico** = valor relevante (quartil superior de preço) + prazo + ação concreta, no máximo
**3 por vendedor**. O excedente é rebaixado para atenção, priorizando o maior valor esperado.
Antes dessa regra eram 1.292 críticos; agora são ~45 a 90, conforme a data.

Lembretes do recorte:

- **Fim de trimestre.**
- **Time sem deal fechável:** nenhum "Atacar agora" e cobertura < 1×.
- **Sobrecarga:** carga ≥ 3× a capacidade, com sugestão de redistribuição para quem tem folga
  no mesmo escritório e melhor taxa naquele produto.
- **Limpeza em massa.**
- **Qualidade de dado.**

### Modo emergência

Liga quando, ao mesmo tempo:

- falta ≤ 30 dias para o fim do trimestre, que é a janela onde os ganhos se concentram;
- a **projeção** (fechado no trimestre + valor esperado no trimestre de quem está em Engaging)
  não bate a **meta** (média trimestral fechada × `META_FATOR`).

Ele mostra o gap e a **lista de resgate**: o menor conjunto de deals, do maior valor esperado
no trimestre para o menor, entre os que ainda têm ≥ 5% de chance de ganhar a tempo, cujo valor
cobre o que falta. Em 04/12/2017 o time tem US$ 1,81M fechados de US$ 3,03M de meta,
projeção de US$ 2,37M, e a lista de resgate tem 250 deals.

### Camada de IA (OpenAI)

A IA **interpreta e escreve; nunca calcula**. Score, chance, valor, alertas e gap vêm do motor,
que é determinístico, calibrado e testado. Um LLM calculando probabilidade seria pior e
impossível de auditar.

| Recurso | Onde aparece |
|---|---|
| **Briefing de segunda** (vendedor, manager ou RevOps, conforme o filtro) | topo da tela e e-mails |
| **Explicação do deal** ("Em uma frase") | painel lateral do deal |
| **Pergunte ao pipeline**: chat com *tool calling* sobre as mesmas consultas da API | aba Perguntar |
| **Plano de resgate** por vendedor | painel de emergência e e-mails |
| **Rascunhos**: follow-up, requalificação, nota de encerramento | painel lateral do deal e e-mail do vendedor |
| **Análise de win-loss** do trimestre (3–5 insights) | aba Time e e-mail de gestão |

**Regras contra alucinação** (`app/ia.py`):

1. **Só fatos prontos.** O LLM recebe só fatos já formatados como devem aparecer ("US$ 4.821",
   "41%"), e o prompt proíbe calcular.
2. **Números conferidos.** Todo número da resposta é conferido contra os fatos. Se não bater, a
   IA refaz uma vez; depois disso, entra o texto-template.
3. **Narrativa proibida bloqueada.** Frases que atribuem chance a vendedor, conta ou setor
   (exatamente o que os dados mostraram não prever) são barradas.
4. **Fallback e transparência.** Sem chave ou com erro, o texto-template assume e a tela nunca
   quebra. Cada texto mostra o selo **"gerado por IA"** ou **"texto automático"**.
5. **Cache e log.** Há cache em memória e em disco (`backend/.cache_ia/`), e cada chamada
   (fatos, resposta, problemas, modelo) é registrada em `backend/logs/ia.jsonl`.
6. **Limite no chat:** `LEAD_SCORER_IA_MAX_PERGUNTAS_DIA` perguntas por dia.

Modelo: `LEAD_SCORER_LLM_MODEL` (padrão `gpt-4o`), trocável por configuração.

### E-mails automáticos (equipe e gestão)

`python -m app.emails` monta um e-mail por pessoa, para a data de referência:

| Público | Para quem | Conteúdo |
|---|---|---|
| **Equipe** | cada vendedor com pipeline ou meta | briefing da semana; ritmo; emergência com lista e plano de resgate pessoal; "Atacar agora"; críticos do dia; rascunho de follow-up pronto; limpeza |
| **Gestão** | cada manager | briefing do time; meta × projeção; plano de resgate do time; ritmo por vendedor (cobertura, carga, deals sem conta); alertas de gestão (sobrecarga com redistribuição, time sem deal fechável, limpeza, qualidade de dado); análise do trimestre |
| **Gestão** | Head de RevOps | o mesmo da gestão, consolidado, com uma tabela por manager |

```bash
cd backend
python -m app.emails --data 2017-12-04                   # gera os HTMLs em saida_emails/2017-12-04/ (abra o index.html)
python -m app.emails --data 2017-12-04 --publico gestao  # só gestão
python -m app.emails --modo enviar                       # envia de verdade (ver travas abaixo)
```

**Travas de segurança:**

- O modo padrão é `arquivo`: só gera os HTMLs, não envia nada.
- Para enviar, são necessárias três coisas: `--modo enviar` (ou `LEAD_SCORER_EMAIL_MODO=enviar`),
  SMTP próprio em `LEAD_SCORER_SMTP_*` e `config/destinatarios.json` com endereços reais.
- O arquivo de exemplo usa `@example.com`, e o envio recusa esses endereços.
- `LEAD_SCORER_EMAIL_REDIRECIONAR` manda **todos** os e-mails para um único endereço de teste.
- A interface só **pré-visualiza** (aba E-mails). Não existe botão de enviar na tela.

**Agendamento** (toda segunda às 7h, no Agendador de Tarefas do Windows):

```bat
schtasks /Create /TN "LeadScorer-Emails" /SC WEEKLY /D MON /ST 07:00 ^
  /TR "cmd /c cd /d C:\caminho\para\solution\backend && python -m app.emails --modo enviar"
```

Em produção, sem `--data`, o envio usa a data mais recente do pipeline.

### Métricas do time

| Métrica | Como é calculada |
|---|---|
| **Ritmo** | % da meta atingida × % do trimestre decorrido |
| **Cobertura** | valor esperado até o fim do trimestre ÷ o que falta para a meta; < 1× = nem fechando o provável a meta é batida |
| **Velocidade** | ciclo mediano dos ganhos do vendedor × mediana do time |
| **Capacidade** | lei de Little: throughput dos últimos 90 dias × ciclo médio do vendedor; **carga** = deals vivos em Engaging ÷ capacidade |
| **Qualidade de dado** | % dos deals abertos sem conta |

## Recomendações

1. **Limpar o pipeline já.** 1.291 deals (62%) passaram de 138 dias, e nenhum deal assim ganhou
   no histórico. Encerrar os baratos e requalificar os caros (abrindo uma oportunidade nova)
   deixa as taxas, a cobertura e a atenção do time honestas.
2. **Trabalhar o último mês do trimestre como janela de fechamento.** É onde os ganhos se
   concentram (81% contra 52%). O modo emergência e a lista de resgate existem para isso.
3. **Cadastrar a meta real** por vendedor e por time. Hoje ela é derivada da média histórica,
   e essa é a parte mais frágil da emergência.
4. **Coletar o que o CRM não tem:** data do último contato, atividades e stages
   intermediários. Como os atributos atuais não preveem o resultado, o sinal que falta
   provavelmente está aí.
5. **Pilotar com medição:** por um trimestre, metade dos times com a ferramenta e metade sem,
   com botões de feedback ("fiz", "não faz sentido") nos alertas, medindo taxa de ganho, ciclo e
   % de zumbis.

## Limitações

- **O dataset é sintético e o sinal é fraco.** A chance satura em ~41% e, entre deals dentro
  do ciclo, a AUC é moderada (0,63). A ferramenta ordena bem "quem dá para ganhar neste
  trimestre", mas não sabe *por que* um deal específico vai ganhar.
- **A calibração precisa de histórico.** Ela é rolling-origin (sem vazamento), mas antes de
  ~julho/2017 não há desfechos suficientes, e a chance mostrada é a bruta, otimista nas faixas
  altas. A tela avisa.
- **Prospecting não tem datas no dataset.** Esses deals ficam sem chance ("n/d"), fora do
  valor esperado, e só existem na data final.
- **Não existe meta real.** A meta é a média dos trimestres completos anteriores (o Q1/2017 só
  tem março e é descartado), ajustável por `META_FATOR`.
- **O cross-sell é quase trivial aqui:** toda conta já comprou GTX e MG, então a sugestão é
  sempre o GTK 500.
- **Sobrecarga de 3× não aparece** quando os zumbis são excluídos (pico de ~1,9×). Ela só existe
  por causa deles, e a limpeza resolve.
- **Sem escrita no CRM e sem login.** A ferramenta recomenda, mas não encerra deals.
- **A IA ainda não foi testada com chamadas reais.** O fluxo inteiro (validação, retry,
  fallback, cache, loop de ferramentas) tem testes com um LLM simulado, mas a primeira rodada
  com a chave real deve ser acompanhada pelo log `logs/ia.jsonl`.
- **A validação de números é deliberadamente simples.** Ela confere se cada número existe nos
  fatos, não se ele foi usado no lugar certo. Números até 10 passam, para permitir enumerações.
  Para produção: um conjunto fixo de ~20 deals e 10 perguntas com respostas esperadas, rodado a
  cada troca de modelo ou de prompt.
- **Dados saem para um provedor externo** quando a IA está ligada: nomes de conta e de vendedor
  e valores, mas nenhum contato pessoal, porque o dataset não tem. Em produção, use um plano
  com acordo de processamento de dados e sem treino com os dados (LGPD).

### O que precisaria para escalar

1. **Dados:** conectar à API do CRM (no lugar dos CSVs) com um job diário que grava o snapshot
   em banco (ex.: Postgres), para ter histórico real de snapshots.
2. **Calibração em produção:** re-treinar a calibração semanalmente, só com o passado, e
   monitorar a curva previsto × real.
3. **Entrega:** login por vendedor. O e-mail semanal já existe; faltam o envio agendado em
   servidor (não no PC local) e um canal de chat (ex.: Slack) para os críticos.
4. **Ciclo de feedback:** botões "encerrar em lote" / "redistribuir" que escrevem no CRM, e
   registro de quais alertas viraram ação.
5. **Features novas:** coletar o que o CRM não tem hoje (atividades, último contato, stage
   intermediários), que é onde provavelmente está o sinal que falta.

## Link público (deploy opcional)

Não é exigido pela submissão. Fica preparado caso se queira um link: ele roda **sem chave de
IA**, em modo template, sem custo e sem dado saindo para fora.

1. **Backend no Render:** New → Blueprint, apontando para este repositório. O `render.yaml`
   usa `backend/Dockerfile`. Anote a URL gerada (ex.: `https://lead-scorer-api.onrender.com`).
2. **Frontend no Vercel:** importe o repositório com Root Directory `frontend` e defina a
   variável `LEAD_SCORER_API_URL` com a URL do backend. O Next repassa `/api/*` para ela.
3. Confira `https://<frontend>/api/saude`.

No plano free, o backend dorme sem uso: o primeiro acesso leva de 30 a 60 segundos.

## Documentos

- [docs/DECISOES.md](../docs/DECISOES.md): por que tempo em vez de perfil, por que 138 dias, por
  que a IA não calcula, e outras perguntas da banca.
- [docs/DEMO.md](../docs/DEMO.md): roteiro de demo de 3 minutos.
- [docs/exemplos-emails/](../docs/exemplos-emails/): 3 e-mails gerados pela ferramenta (vendedor, manager, RevOps).
- [process-log/PROCESS_LOG.md](../process-log/PROCESS_LOG.md): como a IA foi usada para construir.
