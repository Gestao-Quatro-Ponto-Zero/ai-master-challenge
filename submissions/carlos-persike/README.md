# Submissão — Carlos Persike — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Carlos Persike
- **LinkedIn:** _[preencher antes de abrir o PR]_
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Testei estatisticamente as 4 features "óbvias" pra prever se um negócio fecha — produto,
vendedor, setor e porte da conta — e **nenhuma delas tem relação real com o resultado**
(p ≥ 0,26 em todos os testes; um classificador com essas 4 features juntas tem AUC 0,559,
igual a chute). O único sinal estatisticamente real (p = 1,2×10⁻²⁶) é o tempo desde o
engajamento: negócios perdidos morrem rápido (mediana 14 dias), negócios ganhos demoram mais
(mediana 57 dias) — quem sobrevive mais tempo tem mais chance de fechar, o contrário da
intuição de "deal parado = deal esfriando". Construí uma ferramenta (Streamlit, roda local)
que prioriza os 2.089 negócios abertos por **Valor Esperado = probabilidade histórica de
fechar (pelo tempo de vida do deal) × valor do produto**, com filtro por vendedor/manager/
região, destaque de "Top 5 pra focar hoje" e explicação por negócio em linguagem simples.
Achado operacional extra: 68% do pipeline aberto
não tem conta vinculada no CRM — isso não é acaso, é processo, e impede usar porte da conta
como sinal até ser corrigido.

---

## Solução

### Abordagem

1. **Auditei antes de pontuar.** Antes de escrever qualquer lógica de score, rodei testes de
   independência (chi², correlação ponto-bisserial, Mann-Whitney) entre cada feature óbvia e
   o resultado histórico (Won/Lost). Script: `solution/src/auditoria.py`, saída completa em
   `solution/outputs/auditoria.txt`.
2. **Descartei o que não tem sinal.** Produto, vendedor e porte de conta não têm relação
   estatística com o resultado nesse dataset — incluir isso no score seria inventar uma
   narrativa que os dados não sustentam (testei uma regressão logística com essas 4 features
   e o holdout confirma: AUC 0,559, acurácia igual ao baseline de classe majoritária).
3. **Validei o único sinal real em holdout 80/20**, com baseline de comparação explícito.
   Script: `solution/src/validar_modelo.py`, saída em `solution/outputs/validacao_modelo.json`.
4. **Construí o score em cima do que sobrou**, e só isso: Valor Esperado = probabilidade
   histórica (pela faixa de tempo desde o engajamento) × valor do produto (`sales_price`,
   com o bug de digitação `GTXPro`/`GTX Pro` corrigido na ingestão — sem isso o join de
   preço falha silenciosamente pra 1.147 negócios).
5. **Interface:** Streamlit, porque é o primeiro exemplo do próprio brief e roda numa página
   só — o vendedor abre, filtra pelo nome dele e vê a fila. Sem essa camada o score não serve
   pra nada além de um script que ninguém vai rodar. Tem destaque "Top 5 pra focar hoje",
   visão de detalhe por negócio (conta, produto, probabilidade) e um expander opcional "Como
   o placar é calculado" — quem só quer trabalhar não precisa ler método estatístico pra usar
   a ferramenta.
6. **Testei a lógica de domínio**, não só o app rodando na tela: `solution/src/test_dominio.py`
   cobre a tabela de sobrevivência, a probabilidade por faixa de dias, a ordenação por Valor
   Esperado e a formatação de moeda — 7 testes, `python3 test_dominio.py`.

### Resultado

**Diagnóstico com números** (fonte: `solution/outputs/auditoria.txt`):

| Feature | Teste | Resultado | Tem sinal? |
|---|---|---|---|
| Produto → resultado | chi² | p = 0,372 | Não |
| Vendedor → resultado | chi² | p = 0,264 | Não |
| Receita da conta → resultado | correlação | p = 0,315 | Não |
| Nº funcionários → resultado | correlação | p = 0,492 | Não |
| Dias desde engajamento → resultado | Mann-Whitney | p = 1,2×10⁻²⁶ | **Sim** |

Modelo combinando as 4 features "óbvias" (regressão logística, holdout 20%): **AUC 0,559**,
acurácia igual ao baseline de classe majoritária (0,63) — não generaliza melhor que "sempre
prever Ganho".

Tabela de sobrevivência usada em produção (probabilidade histórica de Ganho por faixa de
dias desde o engajamento, calibrada no dataset completo), validada em holdout: **AUC 0,592**
— sinal real, porém modesto (fonte: `solution/outputs/validacao_modelo.json`).

Achado operacional: **68,5% dos negócios em Engaging e 67,4% dos em Prospecting não têm
conta vinculada** no CRM (contra 0% em Won/Lost) — o vendedor só preenche a conta perto do
fechamento. Isso é por que o score não usa porte de conta: não é só falta de sinal
estatístico, é falta do dado em dois terços do pipeline aberto.

**Proposta de automação:** priorização automática do pipeline aberto por Valor Esperado, com
explicação auditável por linha — não decisão automática de descartar ou fechar deal (ver
Limitações). O vendedor decide; a ferramenta ordena a fila e mostra o porquê.

**Protótipo:**

```bash
cd submissions/carlos-persike/solution
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# baixe o dataset "CRM Sales Predictive Analytics" (Kaggle, CC0):
# https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics
# e coloque os 4 CSVs em ../data/ (accounts.csv, products.csv, sales_teams.csv, sales_pipeline.csv)

streamlit run src/app.py
```

Reproduzir os números citados neste README e rodar os testes:

```bash
cd solution/src
python3 test_dominio.py    # 7 testes de domínio
python3 auditoria.py       # gera outputs/auditoria.txt
python3 validar_modelo.py  # gera outputs/validacao_modelo.json
```

Testado em máquina limpa (venv novo, só `requirements.txt`) antes de considerar pronto.

### Recomendações

Priorizado pra segunda-feira de manhã:

1. **Obrigar preenchimento de conta no CRM antes do estágio Engaging.** Hoje 68% do pipeline
   aberto não tem — isso bloqueia qualquer análise por porte de conta, incluindo as que essa
   submissão testou e descartou por falta de dado, não só falta de sinal.
2. **Corrigir o cadastro `GTXPro` → `GTX Pro`** no catálogo/CRM. É erro de digitação que
   quebra join de preço silenciosamente — sem essa correção, todo relatório que cruza
   pipeline com catálogo de produto perde 1.147 negócios sem avisar.
3. **Adotar a fila de Valor Esperado como apoio, não substituto, da decisão do vendedor.** O
   sinal é real mas modesto (AUC 0,59) — é melhor que ordenar por feeling ou por valor bruto,
   mas não é uma previsão confiável negócio a negócio.
4. **Não usar vendedor, produto ou setor como critério de priorização ou avaliação de
   performance a partir deste dataset** — os dados provam que essas variáveis não têm relação
   com o resultado aqui. Qualquer narrativa "vendedor X fecha mais" nesse dataset é ruído.

### Limitações

- **O sinal é real, mas fraco.** AUC 0,592 em holdout — bem acima de aleatório (0,5) e
  estatisticamente significativo, mas está longe de um previsor confiável negócio a negócio.
  O score ordena a fila; não decide sozinho quais negócios abandonar.
- **Valor do negócio é o preço de tabela do produto, não o valor negociado.** `close_value`
  (valor real de fechamento) só existe para negócios já fechados — não dá pra saber o valor
  real de um negócio aberto com os dados disponíveis. Se o CRM passar a capturar valor
  estimado por oportunidade aberta, o Valor Esperado fica mais preciso.
- **Porte de conta (receita/funcionários) não entra no score** — nem por falta de sinal
  (testado, não tem), nem por falta de dado (68% do pipeline aberto não tem conta).
- **Dataset pequeno para inferência por segmento:** 35 vendedores e 86 contas — mesmo se
  houvesse sinal real, o poder estatístico pra decisão individual seria baixo.
- **Não valida se o vendedor de fato muda comportamento com a ferramenta** — isso exigiria
  instrumentar uso real (quantos negócios da fila top-N o vendedor efetivamente trabalhou) e
  medir taxa de fechamento antes/depois, que este challenge não tem dado pra fazer.

---

## Process Log — Como usei IA

Ver [`process-log/PROCESS_LOG.md`](./process-log/PROCESS_LOG.md) — capturado durante a
construção, não reconstruído no final. Inclui a decomposição inicial, os testes estatísticos
que descartaram a abordagem de classificador de Won/Lost, e a decisão de arquitetura que
isso forçou.

---

## Evidências

- [x] Process log com decomposição, auditoria de sinal e decisões registradas
- [x] Git history (branch `submission/carlos-persike`) — commits granulares por decisão
- [x] Testes automatizados da lógica de domínio (`solution/src/test_dominio.py`)
- [ ] Screenshots / chat exports adicionais: _adicionar se desejar antes do PR_

---

_Submissão enviada em: 2026-08-29_
