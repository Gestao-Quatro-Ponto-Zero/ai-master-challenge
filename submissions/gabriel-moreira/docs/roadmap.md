# Roadmap — Lead Scorer

## O que foi construído

Ferramenta de triagem de pipeline por **valor em risco**, não por probabilidade categórica de
conversão. A evidência que sustenta essa escolha: nos 6.711 negócios com desfecho registrado,
conta, setor, escritório, produto e vendedor não preveem ganho/perda — AUC 0,475-0,523 isolada,
testes de permutação com p entre 0,262 e 0,965. Nenhum atributo é exceção. O fit por vendedor é
mecanismo separado de redistribuição de carga, nunca `p̂` (ver [docs/report.md](./report.md) §1,
§2 e §12 e [docs/architecture.md](./architecture.md)). O que esses testes afirmam é que este
histórico **não enxerga** diferença entre vendedores — não que ela seja zero: a dispersão
verdadeira estimada é τ̂=1,08pp e o menor efeito detectável com 80% de poder é τ=3,04pp
([§14](./report.md)). É essa lacuna que o item 3 abaixo existe para fechar.

```
PRIORIDADE = P̂ganho(produto, idade) × VALOR(produto, porte) × URGÊNCIA(idade)   [dólares, auditável]
SCORE      = percentil(PRIORIDADE contra os 4.238 negócios historicamente ganhos)   [0-100, número exposto]
CONFIANÇA  = min(completude, suporte)                                            [0-100, veracidade do dado]
ESTADO     = árvore(sem_precedente, SCORE≥95, CONFIANÇA<50)  →  Priorizar / Acompanhar / Qualificar / Revisão em lote
```

Entregue: API FastAPI + frontend React, sem autenticação (dataset público de demonstração — vendedor,
gerente e escritório são filtros ordinários, não escopo de sessão), validação reprodutível
(`make validate`, 14 seções incluindo três resultados negativos de refinamento testados e descartados)
e suíte de testes (unitário + e2e). Stack e detalhes completos em
[docs/architecture.md](./architecture.md); decisões e porquês em
[decisions-log.md](../process-log/decisions-log.md).

**Limitação central, já documentada:** o modelo diferencia por valor e urgência, não por
probabilidade real — `p̂` varia só entre 0,63 e 0,75, e **apenas por idade**: por produto ele é
constante (o nível colapsa, ver `docs/analise-lead-scoring.md` §3.3), porque não existe dado
comportamental nos 4 CSVs de origem. É a lacuna que os itens abaixo endereçam.

---

## Próximos passos selecionados

### 1. Campo de abandono no CRM

A mediana de idade dos 2.089 negócios abertos é 165 dias — mais velha que o negócio mais longo
que já fechou na história (138 dias). 653 estão abertos há ≥200 dias, alguns há 423. Quase
certamente há negócio morto aí dentro.

Fechar esse negócio por régua de idade — reclassificar em lote como `Lost` quem passou de um
limiar — contaminaria a calibração: seriam desfechos atribuídos por nós, não observados, e eles
não caem por igual entre carteiras. O caminho é registrar o evento, não inferi-lo.

- **Ação:** um campo de desfecho `Abandonado`, com data e motivo, preenchido por quem trabalha o
  negócio — evento registrado, não inferido por idade. O saneamento em lote então vira uma
  operação de CRM auditável, e a calibração pode usar esses desfechos porque alguém os declarou.
- **Esforço:** baixo no código (o motor já trata `Won`/`Lost` genericamente), médio no processo.
- **Impacto de negócio:** desbloqueia a única leitura honesta de "taxa de perda real" — hoje a
  taxa de 63,15% é otimista por construção, porque mede quem fechou e quem nunca fechou não
  conta como perda. Enquanto o campo não existe, a régua de idade **não** é um substituto: ela
  transfere o palpite para dentro do número, onde ninguém mais o vê.

### 2. Persistir histórico de score

Tudo roda in-memory hoje, recalculado a cada carga — não existe série temporal por negócio.

- **Ação:** banco gerenciado (ex.: Supabase) guardando SCORE/ESTADO/CONFIANÇA por negócio a cada
  execução do pipeline.
- **Esforço:** baixo-médio — schema simples, sem mudança na lógica de scoring.
- **Impacto de negócio:** habilita trajetória ("este negócio está piorando há 3 semanas", que a
  foto do dia não mostra), auditoria de decisão, e é pré-requisito técnico direto do A/B do item 3
  e do forecast do item 4 — sem série temporal, nenhum dos dois pode ser medido ao longo do tempo.

### 3. A/B do próprio score — e a alocação aleatorizada que mede o vendedor

Metade dos vendedores prioriza pela ferramenta, metade continua no processo atual; medir receita
por trimestre entre os dois grupos.

O mesmo desenho ataca a pergunta que o backtest §14 diz que este histórico não consegue
responder — mas é preciso ser exato sobre o que ele resolve. Hoje cada vendedor trabalha a
carteira que a operação lhe deu, então taxa de vitória e qualidade de carteira chegam
confundidas. Sortear leads comparáveis entre vendedores quebra essa confusão na origem: a
diferença que sobrar é atribuível a habilidade, não à carteira recebida.

O que a aleatorização **não** faz é comprar poder estatístico. Com τ̂=1,08pp, o backtest §14
dimensiona o custo: seriam necessários ~2.000 negócios fechados por vendedor para detectá-lo com
80% de poder, contra os 220 de hoje — 9× o histórico atual. Logo o experimento se justifica pelo
desenho e pelo acúmulo deliberado de amostra ao longo do tempo, não por um atalho: no curto prazo
ele detecta um efeito grande caso exista (τ≥3,04pp) e produz uma estimativa não-viesada; a
resolução para 1pp chega com os trimestres.

- **Esforço:** baixo em engenharia, médio em processo (requer coordenação com liderança de
  vendas e período de espera para significância estatística).
- **Impacto de negócio:** é a evidência que compra orçamento para a fase seguinte (instrumentação
  comportamental, modelo real) e defende a ferramenta com dado quando alguém perguntar se ela
  vale o custo. Sem isso, o valor de tudo o resto fica em opinião, não em número. O braço de
  alocação aleatorizada tem valor próprio: 1pp de conversão sobre uma carteira de ~220 negócios
  fechados por período é receita real, e é a única via honesta para decidir treinamento,
  distribuição de carga ou remuneração por desempenho — nenhuma das três se sustenta no histórico
  observacional, e a ferramenta não finge o contrário.

### 4. Forecast probabilístico (commit vs. upside)

Somar `p̂ × valor` com intervalo de confiança, agregado por escritório e trimestre.

- **Esforço:** médio — a fórmula unitária já existe; o novo trabalho é agregação, intervalo de
  confiança e visualização por período/escritório.
- **Impacto de negócio:** muda quem compra a ferramenta internamente. Sai de "ferramenta de
  priorização do vendedor" para "instrumento de forecast do CFO/head de vendas" — patrocínio
  mais alto, orçamento maior, e uma segunda razão de existir além da fila individual.

### 5. Modelo de sobrevivência para time-to-close

As curvas de aging atuais (`risco(t)`, `p_ganho(t)`) já são metade de um modelo de sobrevivência;
falta tratar censura formalmente (hoje é um corte fixo em 138 dias) e responder diretamente
"este negócio fecha neste trimestre ou no próximo".

- **Esforço:** médio-alto — requer troca do encolhimento em degraus atual por um modelo de
  sobrevivência real (ex.: Cox, Kaplan-Meier com covariáveis) e nova validação.
- **Impacto de negócio:** responde a pergunta que gestor de vendas mais faz — alocação de esforço
  dentro do trimestre corrente — com mais precisão do que o corte binário de hoje, e melhora a
  acurácia do próprio forecast do item 4.

### 6. Job de sinal externo: notícias da conta

Nenhum dos 4 CSVs de origem carrega sinal comportamental ou de contexto de mercado (ver
[docs/analise-lead-scoring.md §6](./analise-lead-scoring.md)) — hoje a ferramenta só reage
ao que já está no CRM. Um gatilho de mercado (rodada de investimento, expansão, troca de
liderança, notícia negativa) é o tipo de evento que justifica contato imediato e que nenhuma
curva de aging consegue prever.

- **Ação:** job agendado (diário) que busca notícias recentes por conta vinculada (nome da conta
  + domínio/setor, via API de notícias ou busca), filtra por relevância comercial (funding,
  expansão, aquisição, mudança de C-level, sinais negativos) e, quando encontra algo relevante,
  notifica o vendedor responsável pela conta — no canal que já usa (e-mail/Slack), não numa aba
  nova a ser checada.
- **Esforço:** médio — a parte nova é o pipeline de ingestão/filtro de notícias e a integração de
  notificação; o roteamento "conta → vendedor responsável" já existe via `sales_teams.csv`.
- **Impacto de negócio:** é o primeiro sinal de **intenção externa** que a ferramenta passaria a
  ter — hoje ela só prioriza por valor e urgência de funil, nunca por "por que agora". Fecha parte
  da lacuna comportamental apontada em `analise-lead-scoring.md` §6 sem exigir instrumentação do
  CRM, que depende de terceiros para começar a coletar.

---
