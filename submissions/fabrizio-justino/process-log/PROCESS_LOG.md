# Process Log — Lead Scorer

> Resumo nas 5 perguntas do guia de submissão. Logo abaixo, a linha do tempo completa como
> evidência: cada prompt, cada erro e cada correção.

## 1. Ferramentas de IA usadas e por quê

| Ferramenta | Para quê | Por quê |
|---|---|---|
| **Claude Code** (extensão VS Code, Claude Opus 5.5) | Rodar a EDA e os backtests, escrever e testar todo o código, revisar os e-mails gerados, guiar o fork/PR | Agente com acesso aos arquivos e ao terminal: roda o código, mede e corrige no mesmo fluxo, em vez de só sugerir |
| **Claude (navegador) e ChatGPT** | Revisões críticas do projeto (planos das rodadas 2, 3 e 4), coladas no Claude Code | Uma segunda opinião independente de quem escreveu o código |
| **OpenAI** (dentro do produto) | Camada de texto da ferramenta: briefing, explicações, chat, rascunhos | Escolha minha de provedor; conta e chave exclusivas do projeto |

## 2. Como decompus o problema antes de promptar

1. **Olhar os dados antes de definir o score:** pedi a EDA antes de qualquer peso.
2. **Esqueleto primeiro, pressão depois:** "começar com o esqueleto, depois repassar com situação
   de emergência e pressão; trabalhar com alertas e lembretes dos stages".
3. **Qualificar → informar → aproveitar → pressionar:** o plano da rodada 2, em 4 blocos.
4. **IA como camada de interpretação**, nunca como quem calcula (rodada 3).
5. **Revisão externa antes de entregar** (rodada 4).

## 3. Onde a IA errou e como foi corrigido

| Erro | Como apareceu | Correção |
|---|---|---|
| **1º score não previa nada** (AUC 0,50: score 80 ganhava igual ao 50) | Backtest de calibração que eu pedi | Troca do alvo para "ganha até o fim do trimestre" (AUC 0,63/0,72); pilares sem sinal saíram |
| **Estimador de chance otimista** (previa 80%, real 30%) | Curva previsto × real | Censura dos deals que nunca fecham + recalibração isotônica |
| **Calibração usava o futuro** ao simular datas passadas | Revisão externa | Rolling-origin, com teste automatizado |
| **Cortes fixos de ação** ("Atacar" de 82 a 893 deals conforme a data) | Medição depois do rolling-origin | Cortes por percentil |
| **"Requalificar" incoerente** com a regra "0 de 13.871 ganharam" | Revisão externa | Virou "encerrar e reabrir como oportunidade nova" |
| **Prospecting com chance que a própria IA sabia ser otimista** | Revisão externa | Trilha própria, com chance "n/d" |
| **Cobertura errada** (~0,2× para todos) | Releitura dos e-mails | Valor esperado ÷ o que falta para a meta |
| **Texto da tela afirmava "AUC" de porte/setor, que nunca foi medido** | A própria IA, ao revisar | Texto corrigido para o que foi de fato testado |
| **E-mail prometia "estes deals cobrem o que falta" sem conferir** | Leitura dos e-mails como vendedor | O texto agora depende de a lista cobrir ou não |
| **Zumbi caro no topo da lista** | Rodando o sistema de verdade | Ordenação por ação antes do valor |
| **1.292 alertas "críticos"** (crítico virou ruído) | Contagem | Regra valor + prazo + ação, com no máximo 3 por vendedor |
| Bugs menores: `GTXPro` × `GTX Pro`, nome da conta em minúsculas, idade como float, porta ocupada | Rodando | Corrigidos na hora |

## 4. O que eu adicionei que a IA sozinha não faria

- **Direção de produto:** a ideia de "emergência e pressão" de fim de trimestre e os alertas por
  stage.
- **Cortes de escopo:** "não vamos fazer" ICP e produto × porte, quando a IA avisou que o sinal
  seria fraco.
- **E-mails por público:** "dividindo em equipe e gestão, com alertas e análises".
- **Segurança e governança:** conta e chave de IA exclusivas do projeto.
- **Revisão independente** do trabalho, trazida de outras ferramentas (Claude no navegador e
  ChatGPT).
- **Questionar complexidade:** perguntei "pra que vamos precisar de tudo isso", o que evitou um
  deploy que o guia não exige.

### Nas minhas palavras

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

## 5. Quantas iterações

São **5 rodadas** em ~20 prompts meus, e cada rodada terminou com testes e medição:

1. **Esqueleto:** motor de regras + tela + alertas (7 testes).
2. **Qualificação e pressão:** métricas, emergência, alertas. Aqui a calibração derrubou o score.
3. **Redesenho do score:** chance no prazo com censura e calibração.
4. **IA + e-mails:** 6 recursos de IA, e-mails de equipe e gestão (20 testes).
5. **Revisão externa:** rolling-origin, percentis, Prospecting, incerteza, cobertura, revisão
   dos e-mails, docs da banca (23 testes).

---

# Linha do tempo detalhada

## Sessão 1 — 2026-10-20

### 1. Kickoff
- Colei o enunciado do challenge no Claude Code.
- **Decisões minhas (via perguntas da IA):** stack FastAPI + Next.js + shadcn/ui (em vez de
  Streamlit), dados em memória (pandas), sem login nem banco para o protótipo. Eu baixo o
  dataset do Kaggle.
- Scaffold do backend e do frontend criado para este projeto.

### 2. Dataset
- Baixado via `kagglehub.dataset_download("agungpambudi/crm-sales-predictive-analytics")`
  (snippet colado por mim, executado pela IA) → copiado para `backend/data/`.

### 3. EDA (scripts gerados e rodados pela IA)
Achados que mudaram o desenho do score:
- **Bug de dados:** pipeline usa `GTXPro`, tabela de produtos usa `GTX Pro` → normalizar no load.
- **Features "óbvias" quase não discriminam:** win rate por setor/região/manager/produto fica
  entre 61–65%. Por vendedor 55–70%, por conta 53–75%.
- **Backtest temporal** (taxas suavizadas calculadas com deals fechados antes de 2017-07,
  avaliadas em deals engajados depois): AUC ≈ 0,52 para vendedor, conta e produto, inclusive
  combinados. Ou seja, o histórico categórico **não prevê** o resultado de forma confiável →
  não dá pra vender o score como "probabilidade de fechar".
- **Losses morrem cedo:** mediana de duração de Lost = 14 dias vs Won = 57 dias. Um deal que
  sobreviveu 90+ dias ganha 71%; 120+ dias, 76%. Tempo no pipeline é sinal real.
- **Teto do ciclo:** nenhum deal fechado durou mais de 138 dias. Na data de referência
  (2017-12-31), **81% dos deals em Engaging já passaram de 138 dias** → pipeline cheio de
  "zumbis" que precisam ser requalificados ou encerrados.
- **Efeito fim de trimestre:** deals fechados em mar/jun/set/dez ganham 81% vs 52% nos outros
  meses.
- **68% dos deals abertos não têm conta preenchida** → problema de higiene de CRM.
- Valor por produto varia 500x (MG Special US$55 vs GTK 500 US$26.768); close_value ≈ preço
  de lista (razão média 0,996).
- 8 dos 35 vendedores não têm deal aberto; Darcel Schlecht tem 194.

### 4. Desenho do score (proposto pela IA, validado por mim)
- A IA propôs um score de regras em 4 pilares: timing 35, valor 30, fit 20, dados 15.
  O fit ficou com peso baixo **por causa do backtest**.
- **Minha direção:** "começar com o esqueleto, depois repassar com situação de emergência e
  pressão; trabalhar com alertas e lembretes dos stages".

### 5. Esqueleto (gerado pela IA)
- **Backend:** `config.py` (pesos/limites), `dados.py` (carga + fix GTXPro), `scoring.py`
  (benchmarks calculados do histórico, nada hardcoded: zona de risco = mediana de duração
  dos Lost, teto = maior ciclo fechado), `alertas.py` (por stage: `prospecting_parado`,
  `zona_de_risco`, `reta_final`, `fora_do_ciclo`, `sem_conta`; do time: `fim_trimestre`,
  `sobrecarga`, `higiene_crm`; severidade critico/atencao/lembrete, pensando no modo
  emergência que vem depois), `main.py` (FastAPI).
- **Frontend:** filtros em cascata (região → manager → vendedor), lembretes do time no topo,
  cards de ação clicáveis, tabela priorizada, painel lateral com "Por que score X?" (barra
  por pilar + frase) e "O que fazer" (alertas), fila de alertas, aba "Como funciona".
- **Testes:** 7 smoke tests da API (ordenação, soma dos pilares = score, filtros, alerta de
  zumbi, ordem por severidade). `next build` com checagem de tipos passando.

### 6. Bugs pegos rodando de verdade
- `"betasoloin"`: o `.capitalize()` deixava o nome da conta em minúsculas → troca por
  maiúscula só no 1º caractere.
- `idade_dias` virava float (95.0) por causa dos NaN de Prospecting → `Int64`.
- Moeda em formato americano (26,768) → formato BR.
- **Porta 3000 ocupada** por outro app rodando na máquina → Lead Scorer foi para a 3001.
- **Ordenação errada:** o top 1 do Melvin era um "Requalificar" de score 61 (zumbi caro) acima
  de deals saudáveis → ordenar por ação e depois por score. Teste atualizado.
- Achado de negócio no teste: o time do Melvin Marxen não tem nenhum deal em "Atacar agora".

## Sessão 1 (cont.) — rodada 2: qualificar, informar, aproveitar, pressionar

### 7. Plano meu
Colei um plano em 4 blocos: (1) qualificar os leads com ICP, produto × porte, histórico da
conta, afinidade do vendedor e calibração por backtest; (2) informar com valor esperado,
velocidade, cobertura e qualidade de dado; (3) aproveitar com capacidade × carga, limpeza em
massa e cross-sell; (4) pressionar com o modo emergência (meta em risco no fim do trimestre,
lista de resgate, gatilho de deal grande esfriando, teto de 3 críticos por vendedor, alerta de
manager, ritmo do trimestre).
- A IA avisou que ICP e produto × porte provavelmente dariam sinal fraco → **decisão minha:
  não fazer**.
- A IA propôs separar **score (chance)** de **valor esperado**, para a calibração fazer sentido.

### 8. Infra de backtest
- `dados.snapshot(t)`: reconstrói o pipeline como estava na data t. Os deals que fecharam
  depois voltam a ser Engaging, e o desfecho real fica guardado à parte. É a base da
  calibração sem vazamento e da simulação de datas na interface.
- O PowerShell ficou indisponível (verificador de segurança sem resposta) por ~5 tentativas.
  A IA parou de tentar, escreveu o código sem rodar e testou quando a ferramenta voltou.

### 9. A calibração derrubou o score (o momento mais importante do projeto)
- O primeiro score (timing + histórico da conta + afinidade + dados) teve **AUC 0,500** no
  backtest: score 80 ganhava o mesmo que score 50 (64–69% em todas as faixas).
- Diagnóstico por pilar: timing 0,51, conta 0,49, afinidade 0,49, idade crua 0,52. O
  "histórico da conta" é inútil neste dataset: 85 contas com ~100 deals cada, e quase toda conta
  "perdeu algo nos últimos 90 dias".
- **Virada:** a IA trocou o alvo de "ganha algum dia" (imprevisível) para **"ganha até o fim
  do trimestre"**. Com a chance empírica dada a idade do deal, a AUC foi para 0,67.
- A calibração quebrava nas faixas altas (previa 80%, real 30%) por **viés de sobrevivência**:
  o histórico só enxerga quem fechou, não os zumbis. A correção foi tratar os deals ainda
  abertos como observações censuradas, o que levou a AUC a 0,75 no diagnóstico e deixou a
  curva monotônica até ~40%. Por cima, a recalibração isotônica.
- Medido no app: AUC 0,63 entre deals vivos e 0,72 no pipeline inteiro. **A regra dos 138
  dias foi validada: 13.871 observações de zumbi, 0 ganharam depois.**
- Pilares sem sinal saíram do score, pela mesma regra que usei para cortar o ICP. A
  afinidade continua só para sugerir redistribuição.

### 10. Ajustes que os números pediram
- "Atacar agora" com corte 70 dava ~16 deals por vendedor, porque a chance satura e muitos
  deals empatam. O corte foi para 85 (~5 por vendedor/semana), com a justificativa no `config.py`.
- Emergência "ativa" com 0 dias restantes → desliga no último dia.
- 891 alertas de atenção → alerta de stage em deal de valor baixo virou lembrete.
- Críticos: 1.292 → ~45–90, pela regra valor + prazo + ação, com teto de 3 por vendedor.
- Achados honestos documentados: sobrecarga 3× só existe por causa dos zumbis; cross-sell é
  sempre GTK 500.
- A IA tinha escrito na tela que porte/setor tinham "AUC 0,49–0,52", mas isso não foi medido.
  Ela corrigiu o texto para refletir só o que foi de fato testado.

### 11. Entrega da rodada
- Backend: `calibracao.py`, `metricas.py`, `emergencia.py`, `crosssell.py`, `motor.py` (cache
  por data); todos os endpoints aceitam `data`. 11 testes passando, entre eles "zumbi nunca
  ganhou", "calibração monotônica", "teto de 3 críticos" e "snapshot não vaza o futuro".
- Frontend: seletor de data + botão "Simular pressão", painel de emergência com lista de
  resgate, abas Time e Cross-sell, gráfico de calibração, colunas de chance e valor esperado,
  sugestões de redistribuição no alerta de sobrecarga. `next build` passando.

## Sessão 1 (cont.) — rodada 3: camada de IA e e-mails

### 12. Plano de IA (meu) e decisões
- Colei um plano: o LLM como **camada de interpretação** em cima do motor, nunca calculando o
  score. Seis recursos (briefing, explicação do deal, chat com tool calling, plano de resgate,
  rascunhos, win-loss narrado), com regras contra alucinação (só fatos prontos, validação de
  números, proibição da narrativa "essa conta tem perfil bom", fallback, cache, log).
- A IA perguntou o provedor e o escopo. **Decisões minhas:** só OpenAI, os 6 recursos, e
  **e-mails automáticos divididos em equipe e gestão, com alertas e análises**.
- **Decisão minha:** uma conta OpenAI e uma chave **exclusivas** para o case. A IA fez a chave
  ser lida só de `LEAD_SCORER_OPENAI_API_KEY`, passada explicitamente ao cliente. Isso importa
  porque o SDK, por padrão, pegaria qualquer `OPENAI_API_KEY` que estivesse no ambiente. O SMTP
  também ficou com namespace próprio, num `backend/.env` do projeto.

### 13. Implementação
- `consultas.py`: a regra de cada consulta saiu do `main.py`, para a API, as ferramentas da IA e
  os e-mails usarem o mesmo código.
- `ia.py`:
  - os fatos são pré-formatados exatamente como devem aparecer ("US$ 4.821", "41%");
  - `problemas_no_texto` confere cada número e bloqueia frases proibidas;
  - `_gerar` segue o fluxo cache → template se não houver chave → LLM → validação → 1 retry →
    template;
  - o chat usa function calling sobre 7 consultas, com resultados também pré-formatados e
    validados.
- `emails.py`: HTML inline compatível com clientes de e-mail. O modo padrão só gera arquivos, o
  envio recusa destinatários `@example.com` e há a opção de redirecionar tudo para um endereço
  de teste.
- Frontend: card de briefing no topo, "Em uma frase" e rascunhos no deal, botão "Montar plano de
  resgate", análise do trimestre na aba Time, abas Perguntar e E-mails (pré-visualização, sem
  botão de enviar). Selo "gerado por IA" / "texto automático" em todo texto.
- Testes: +9 com um LLM **simulado** (número inventado → retry → template; texto válido → cache;
  frase proibida; loop de ferramenta; rascunho JSON; e-mails em arquivo; envio recusa
  `@example.com`). **20 testes passando**, `next build` passando.
- Rodada real de e-mails em 04/12/2017 (modo arquivo, sem chave): **37 e-mails** gerados (30
  vendedores, 6 managers, RevOps), todos com a emergência no assunto.

### 14. O que ainda não foi verificado
- Chamadas reais à OpenAI: a chave exclusiva ainda não existe neste ambiente. Na primeira rodada
  com a chave, conferir o `backend/logs/ia.jsonl` (quantas respostas caíram na validação).
- Envio SMTP real: só testei a recusa de destinatário de exemplo.

## Sessão 1 (cont.) — rodada 4: revisão externa

### 15. Revisão (colada por mim) e o que os dados disseram de cada ponto
Colei uma revisão crítica (feita no Claude do navegador / ChatGPT, a partir da minha descrição, sem acesso ao
código). A IA de código **mediu cada ponto antes de mexer**:

**Pontos que não se confirmaram como descritos:**
- **"Atacar agora inalcançável"**: não se confirmou. Os pontos de chance são relativos à maior
  chance possível; havia 155 a 198 deals em "Atacar", e o Melvin tinha 35. O "zero" era do
  score antigo.
- **README "em construção"**: já tinha sido fechado.

**Pontos que procederam:**
- **Cortes fixos (85/70) eram frágeis.** Isso apareceu depois do rolling-origin: "Atacar" variava
  de 82 a 893 conforme a data. Os cortes viraram **percentis por data** (top 15%), o que dá
  ~7 a 8 deals por vendedor de maio a dezembro.
- **"Requalificar" incoerente com chance zero.** Passou a significar "perguntar ao cliente e, se
  continuar, encerrar e abrir uma oportunidade nova".
- **Vazamento na calibração.** Agora é **rolling-origin**: a curva de cada data só usa desfechos
  já conhecidos nela; sem histórico suficiente, a tela avisa.
- **Prospecting com chance otimista.** Ganhou uma trilha própria, **Primeiro contato**, com
  chance "n/d" e fora do valor esperado.
- **Faixa de incerteza (Wilson)** no detalhe do deal. No platô ela é estreita de verdade (±<1
  p.p.), e a tela diz isso em vez de mostrar "40%–40%".
- **Score × valor esperado:** documentado (o score serve à leitura e à ação, o valor esperado
  à ordenação).

**Achado extra da IA ao revisar os e-mails:** a **cobertura** dava ~0,2× para todos no fim do
trimestre, porque dividia o valor esperado até o fechamento pela média de um trimestre inteiro.
Ela passou a ser valor esperado ÷ **o que falta** para a meta (em 04/12 vai de 0,31× a 0,69×
entre os times).

### 16. Revisão dos e-mails (lidos como vendedor e como manager)
- "Juntos, estes deals cobrem o que falta" podia ser falso. Agora o texto depende de a lista
  cobrir ou não a meta e diz quantos deals não aparecem.
- Na emergência, a coluna passou a ser **"se fechar"**, e não "valor esperado".
- Sem IA, o briefing repetia o resumo: sai do e-mail do vendedor. Foi criado um **resumo de 3
  linhas** no topo ("Feche / Encerre / Falta"), para quem lê no celular.
- O plano de resgate em template virou bullets (até 8 vendedores, 3 deals cada), e o próximo
  passo do e-mail de gestão passou a ser de gestão.
- O rascunho sem conta não diz mais "Olá, equipe cliente".

### 17. Entrega do case
- `docs/DECISOES.md` (10 perguntas da banca, com números) e `docs/DEMO.md` (roteiro de 3 min).
- Deploy: `backend/Dockerfile` (imagem **testada localmente**: sobe e responde), `render.yaml`
  e instruções do Vercel no README. O link público fica sem chave de IA.
- 23 testes passando, `next build` passando.

## Sessão 2 — 2026-10-21: entrega

### 18. Deploy? Perguntei "pra que vamos precisar de tudo isso"
- A IA tinha preparado um deploy (Render + Vercel) por sugestão da revisão. Eu questionei. A
  IA explicou que é opcional e propôs vídeo + zip como alternativa mais barata.
- Ao ler o `submission-guide.md`, ficou claro que **não se exige link**, mas **se exige um Pull
  Request**. Decisão: sem deploy (os arquivos ficaram prontos, sem uso); Git, só para o PR.
- Autenticação do GitHub feita pelo navegador (`gh auth login`), sem nenhuma credencial passar
  pela conversa com a IA.

### 19. Pull Request, passo a passo
- Instalei Git e GitHub CLI via winget, orientado pela IA.
- `gh auth login` falhou na primeira vez: o navegador abriu, mas a autorização não voltou para o
  terminal. A IA diagnosticou pelo `gh auth status` e pela ausência do arquivo de configuração,
  e o login foi refeito até o fim.
- Fork e clone pelo `gh`. A IA errou os flags duas vezes (`--clone=true`, depois `--remote`
  junto com o nome do repositório), leu a mensagem de erro e corrigiu.
- **Armadilha do repositório:** o `.gitignore` do desafio ignora `submissions/`, o que contradiz
  o CONTRIBUTING. Como o PR não pode alterar arquivos fora da pasta, a solução foi
  `git add -f` só na pasta da submissão.
- Estrutura conforme o CONTRIBUTING: `README.md` (template oficial preenchido), `solution/`,
  `process-log/`, `docs/`. Ficaram de fora `node_modules`, `.next`, `.env`, cache da IA, logs e
  destinatários. Entraram 3 e-mails de exemplo.

### Próximos passos (fora do escopo da entrega)
- Criar a chave OpenAI do projeto, rodar os e-mails com IA e revisar os textos.
- Produção, passo 1: feedback salvo ("fiz / não faz sentido / encerrei") + "mudanças da semana".
