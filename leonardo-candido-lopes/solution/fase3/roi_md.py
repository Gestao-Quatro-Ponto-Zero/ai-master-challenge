import json
R=json.load(open('/home/ubuntu/g4_challenge/fase3/roi_results.json')); P=R['P']; S=['conservador','base','otimista']
def n(x,d=0):
    s=f"{x:,.{d}f}"; return s.replace(',','X').replace('.',',').replace('X','.')
def brl(x): return ('−' if x<0 else '')+'R$ '+n(abs(x))
def pc(x,d=1): return n(x*100,d)+'%'
c,b,o=[R[s] for s in S]
row=lambda lab,f,key: f"| {lab} | "+" | ".join(f(R[s][key]) for s in S)+" |"
pb=lambda x: '—  (não se paga)' if x is None else n(x,1)+' meses'
txt=f"""# 06 — Modelo de ROI paramétrico (3 cenários)

**Desafio 002 — Redesign de Suporte · Fase 3** · Autor: Leonardo Candido Lopes · 08/11/2026
Cálculo reproduzível: `fase3/roi_calc.py` → `fase3/roi_results.json`. Todos os valores abaixo saem das fórmulas da seção 2; nenhum foi digitado à mão.

> **Natureza deste documento: [PROJEÇÃO].** Nenhum dos dois datasets traz custo, headcount, volume histórico mensal ou tempo de atendimento. Por isso, **todas as premissas são editáveis** e vêm de (a) benchmarks públicos com fonte, (b) a distribuição real de categorias do Dataset 2 ou (c) estimativa do autor, sempre rotulada. Moeda: **R$**, porque a operação de referência é brasileira. Benchmarks em US$ entram só como referência de ordem de grandeza.

---

## Leitura rápida para o COO

- **Capacidade recuperada (cenário base):** {n(b['H'])} h/mês, ≈ {n(b['FTE'],2)} FTE. O valor econômico potencial é {brl(b['VP'])}/mês.
- **Economia financeira realizada (cenário base):** {brl(b['ER'])}/mês contra um custo recorrente de {brl(b['C'])}/mês. Resultado mensal: **{brl(b['L'])}**. **No cenário base, o projeto não se paga só com economia de caixa.**
- **Ponto de equilíbrio (base):** ~**{n(R['breakeven_V_base'])} chamados/mês** com 50% da capacidade convertida em economia. Se 75% for convertida, cai para {n(R['breakeven_V_real75'])}; se 100%, para {n(R['breakeven_V_real100'])}.
- **Otimista:** {brl(o['L'])}/mês líquido, payback de {pb(o['pb'])}. **Conservador:** {brl(c['L'])}/mês, não se paga.
- **Leitura honesta:** o caso financeiro **depende de escala** (volume) e de **o que a empresa faz com as horas liberadas**. Com volumes menores, a justificativa é **qualidade e controle**: triagem correta, SLA mensurável e auditoria. O caixa vem depois. Isso precisa ser dito ao COO antes do investimento, não depois.

---

## 1. Premissas do modelo

| # | Variável | Conservador | Base | Otimista | Fonte / justificativa | Tipo | Editável? |
|---|---|---:|---:|---:|---|---|---|
| V | Volume mensal de chamados | {n(P['V'][0])} | {n(P['V'][1])} | {n(P['V'][2])} | Não existe nos datasets (o D2 tem 47.837 tickets sem data). Faixa hipotética para um service desk de médio porte. | Hipótese | **Sim — prioridade nº 1** |
| pe | % elegível à automação | {pc(P['pe'][0])} | {pc(P['pe'][1])} | {pc(P['pe'][2])} | **Dados reais do D2:** conservador = Purchase (5,15%) + Storage (5,81%); base = + metade de Access (14,89% × 0,5); otimista = Purchase + Storage + Access inteiro. Ver justificativa no `02_redesign_operacional.md`. | Derivada dos dados + hipótese | Sim |
| ts | Taxa de sucesso da automação (resolve sem humano) | 36% | 50% | 65% | **Gartner (ago/2024, n=5.728):** só 14% dos problemas são totalmente resolvidos em self-service, **36% nos casos "muito simples"**. O conservador usa os 36% porque as classes elegíveis são as mais padronizadas. Base e otimista são hipóteses do autor. | Benchmark + hipótese | Sim |
| aht | Tempo médio de atendimento humano poupado por chamado (min) | {n(P['aht'][0])} | {n(P['aht'][1])} | {n(P['aht'][2])} | **HDI / MetricNet:** tempo de contato no service desk "pouco abaixo de 10 min"; incidentes de 12 a 22 min; reset de senha de 1 a 3 min; requisições de serviço de 35 a 96 min. | Benchmark | Sim |
| tri | Tempo de triagem/roteamento manual poupado por chamado (min) — aplica-se a **todo** o volume | {n(P['tri'][0],1)} | {n(P['tri'][1],1)} | {n(P['tri'][2],1)} | Estimativa do autor. **Sem benchmark público encontrado.** Medir na baseline (KPI 13 do `05_kpis.md`). | Hipótese | **Sim — medir** |
| tf | Fricção por tentativa automática que falha (min de agente) | {n(P['tf'][0],1)} | {n(P['tf'][1],1)} | {n(P['tf'][2],1)} | Estimativa do autor: o agente lê o histórico da tentativa antes de assumir. | Hipótese | Sim |
| r | % de retrabalho por erro de automação (ticket "resolvido" que reabre) | {pc(P['r'][0],0)} | {pc(P['r'][1],0)} | {pc(P['r'][2],0)} | Estimativa do autor. Sem benchmark confiável; medir via taxa de reabertura (KPI 11). | Hipótese | Sim |
| k | Esforço extra no retrabalho (fração do aht, somado à perda da economia) | 0,5 | 0,5 | 0,5 | Estimativa do autor: o cliente reabre irritado e o atendimento demora mais. | Hipótese | Sim |
| ch | Custo-hora carregado do agente (R$) | {n(P['ch'][0],2)} | {n(P['ch'][1],2)} | {n(P['ch'][2],2)} | **salario.com.br (CBO 2124-20, Analista de Suporte Técnico, 2026):** mediana R$ 3.000, média R$ 4.109, média no Sudeste R$ 4.399, jornada de 42h/semana (≈ 182h/mês). Fator de encargos CLT de 1,7 / 1,8 / 2,0 (estimativa usual de mercado, **validar com o RH**). Fórmula: salário × fator ÷ 182. Referência internacional: BLS (mai/2024), mediana de US$ 29,01/h para *computer user support specialists*. | Benchmark + hipótese (encargos) | Sim |
| real | Taxa de realização financeira (% das horas liberadas que viram economia de caixa) | 25% | 50% | 75% | **Decisão de gestão, não de dados.** Economia só acontece se as horas evitarem contratação, hora extra, terceirização ou backlog pago. Ver seção 4. | Hipótese de gestão | **Sim — decisão do COO** |
| tool | Custo mensal de ferramentas de IA (R$) | {n(P['tool'][0])} | {n(P['tool'][1])} | {n(P['tool'][2])} | Estimativa do autor (licença/API de LLM ou NLP + hospedagem). **Substituir por cotação.** | Hipótese | Sim |
| mnt | Custo de manutenção mensal (R$) | {n(P['mnt'][0])} | {n(P['mnt'][1])} | {n(P['mnt'][2])} | Estimativa do autor: fração de analista para curadoria da base de conhecimento, revisão de amostras e retreino. | Hipótese | Sim |
| impl | Custo de implementação, one-time (R$) | {n(P['impl'][0])} | {n(P['impl'][1])} | {n(P['impl'][2])} | Estimativa do autor: integração com o sistema de tickets, base de conhecimento, piloto e treinamento. **Substituir por orçamento.** | Hipótese | Sim |
| FTE | Horas produtivas por FTE/mês | 146 | 146 | 146 | 182h × 80% de utilização. HDI/MetricNet citam utilização sustentável perto de 70–80%. | Benchmark + convenção | Sim |

**Referências de ordem de grandeza (não entram na conta):** MetricNet, custo por ticket na América do Norte: média de US$ 15,56 em 2016 (faixa de US$ 2,93 a 46,69); 2021: voz US$ 17,19, e-mail US$ 16,13, chat US$ 15,72. MetricNet *shift-left*: N1 ≈ US$ 22/ticket vs self-service ≈ US$ 2/ticket.

**Fontes:**
- Gartner — https://www.gartner.com/en/newsroom/press-releases/2024-08-19-gartner-survey-finds-only-14-percent-of-customer-service-issues-are-fully-resolved-in-self-service
- HDI — https://www.thinkhdi.com/~/media/HDICorp/Files/Library-Archive/Insider%20Articles/contact-handle-time.pdf
- MetricNet — https://www.metricnet.com/resources/service-desk-cost-per-ticket-motm · https://www.metricnet.com/resources/metrics-unleashed-shift-left
- BLS — https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm
- salario.com.br — https://www.salario.com.br/profissao/analista-de-suporte-tecnico-cbo-212420/

---

## 2. Fórmulas (explícitas)

```
E   = V × pe                                   chamados elegíveis à automação/mês
S   = E × ts                                   chamados resolvidos automaticamente/mês
F   = E − S                                    tentativas que falham e vão para humano
H_auto = [ S × (1 − r) × aht  −  S × r × k × aht ] / 60     horas poupadas pelo autoatendimento (líquidas de retrabalho)
H_tri  = V × tri / 60                          horas poupadas pela triagem automática (todo o volume)
H_fric = F × tf / 60                           horas perdidas com fricção das falhas
H   = H_auto + H_tri − H_fric                  CAPACIDADE RECUPERADA (h/mês)
FTE = H / 146                                  equivalente em pessoas
VP  = H × ch                                   VALOR ECONÔMICO POTENCIAL da capacidade (R$/mês)
ER  = VP × real                                ECONOMIA FINANCEIRA REALIZADA (R$/mês)
C   = tool + mnt                               custo recorrente mensal
L   = ER − C                                   resultado líquido mensal
ROI mensal           = L / C
ROI potencial mensal = (VP − C) / C            (se 100% da capacidade virasse caixa — teto teórico)
ROI ano 1            = (12 × L − impl) / (impl + 12 × C)
Payback (meses)      = impl / L                (só se L > 0)
```

---

## 3. Resultados por cenário

| Indicador | Conservador | Base | Otimista |
|---|---:|---:|---:|
{row('Chamados elegíveis/mês (E)',lambda x:n(x),'E')}
{row('Chamados automatizados com sucesso/mês (S)',lambda x:n(x),'S')}
{row('Tentativas que falham → humano (F)',lambda x:n(x),'F')}
{row('Horas poupadas — autoatendimento (H_auto)',lambda x:n(x,1),'Ha')}
{row('Horas poupadas — triagem (H_tri)',lambda x:n(x,1),'Ht')}
{row('Horas perdidas — fricção (H_fric)',lambda x:n(x,1),'Hf')}
{row('**Capacidade recuperada (h/mês)**',lambda x:'**'+n(x,1)+'**','H')}
{row('Equivalente em FTE',lambda x:n(x,2),'FTE')}
{row('**Valor econômico potencial (R$/mês)**',lambda x:'**'+brl(x)+'**','VP')}
{row('**Economia financeira realizada (R$/mês)**',lambda x:'**'+brl(x)+'**','ER')}
{row('Custo mensal total da solução',brl,'C')}
{row('Resultado líquido mensal (ER − C)',brl,'L')}
{row('ROI mensal (sobre economia realizada)',lambda x:pc(x,0),'roi')}
{row('ROI potencial mensal (teto teórico)',lambda x:pc(x,0),'roi_pot')}
{row('ROI ano 1 (inclui implementação)',lambda x:pc(x,0),'roi12')}
{row('Payback',pb,'pb')}

**Leitura:**
- **[PROJEÇÃO] Conservador:** a automação é marginal ({n(c['H'],1)} h/mês) e não cobre o custo. Mostra o risco de implantar com volume baixo e escopo estreito.
- **[PROJEÇÃO] Base:** libera ≈ {n(b['FTE'],2)} FTE. Se 100% virasse caixa, o ROI mensal seria {pc(b['roi_pot'],0)}. Com 50% de realização, o resultado mensal é negativo ({brl(b['L'])}). **A decisão no cenário base é estratégica (qualidade, SLA, escala), não de corte de custo.**
- **[PROJEÇÃO] Otimista:** com escala (8.000/mês), escopo maior e tempo de atendimento maior, o retorno fica claro (payback ≈ {pb(o['pb'])}).
- Em todos os cenários, **a triagem (H_tri) responde por parte relevante das horas** (base: {n(b['Ht'],1)} de {n(b['H'],1)} h). Como essa é a premissa sem benchmark, **medir o tempo de triagem real é o primeiro passo do piloto**.

---

## 4. Capacidade recuperada ≠ economia realizada

| Conceito | O que é | Quando vira dinheiro |
|---|---|---|
| **Capacidade recuperada (H)** | Horas de agente que deixam de ser gastas em triagem manual e em tickets resolvidos automaticamente | Sempre existe se a automação funciona, mas é **tempo**, não caixa |
| **Valor econômico potencial (VP)** | H × custo-hora: quanto essas horas "valem" | É um **teto teórico**. Útil para comparar alternativas, nunca para prometer economia |
| **Economia realizada (ER)** | A parte do VP que efetivamente reduz desembolso | Só quando a empresa **(a)** deixa de contratar para absorver crescimento, **(b)** corta hora extra/terceiros, **(c)** reduz multa de SLA, ou **(d)** realoca por decisão formal. **O modelo não assume demissões** |

Por que separar: somar VP como "economia" é o erro mais comum em business cases de IA. Ele infla o ROI e destrói a credibilidade quando o caixa não aparece. Horas liberadas que viram ociosidade valem zero. Horas reinvestidas em N2, backlog (67,3% dos tickets do D1 não estão fechados, mesmo sendo sintético) ou base de conhecimento geram **valor de qualidade**, que deve ser medido por KPI (FCR, CSAT, SLA) e não somado ao ROI financeiro.

> *Contexto profissional externo (não é evidência dos datasets):* no redesign do "Link de Análise Especial", que o Leonardo conduziu e que passou de 2–5 dias para tempo real, o ganho principal veio de consolidar processos e eliminar risco de desatualização e perda financeira. Não veio de corte de pessoas. Por isso o modelo trata a taxa de realização como decisão explícita.

---

## 5. Sensibilidade (uma variável por vez)

Cada linha troca **só** aquela variável pelo valor conservador e depois pelo otimista, mantendo todas as outras no cenário base (resultado base = {brl(R['base_L'])}/mês).

| # | Variável | Resultado mensal com valor conservador | Resultado mensal com valor otimista | Amplitude |
|---:|---|---:|---:|---:|
""" + "\n".join(f"| {i+1} | {x['var']} | {brl(x['cons'])} | {brl(x['ot'])} | {brl(x['amp'])} |" for i,x in enumerate(R['sens'])) + f"""

**Leitura:**
- As 3 variáveis que mais mexem no resultado são **{R['sens'][0]['var']}**, **{R['sens'][1]['var']}** e **{R['sens'][2]['var']}**. Duas delas são decisões de gestão (o que fazer com as horas, quanto investir em manutenção), não de tecnologia.
- Nenhuma variável isolada vira o cenário base para positivo. É preciso combinar escala com realização. **Ponto de equilíbrio (base): ≈ {n(R['breakeven_V_base'])} chamados/mês.**
- A % de retrabalho e a fricção pesam pouco no caixa. Pesam muito na **experiência do cliente**, e por isso são controladas por KPI e risco (`07_riscos.md`), não pelo ROI.

---

## 6. O que falta para tornar o modelo preciso

1. **Volume mensal real** por categoria e canal, com sazonalidade (12 meses de histórico).
2. **Tempo médio de atendimento real por categoria** (hoje vem de benchmark), principalmente Purchase, Storage e Access.
3. **Tempo real de triagem e roteamento**, incluindo re-roteamentos (transferências entre filas).
4. **Custo-hora carregado real** (salário + encargos + benefícios + infraestrutura) por nível (N1/N2).
5. **Cotação real** de ferramenta (licença/API) e **orçamento de implementação**.
6. **Taxa de sucesso medida em piloto** (substitui as premissas de 36/50/65%).
7. **Decisão formal do COO sobre a taxa de realização**: contratações evitadas, terceiros, horas extras.
8. **Custos evitados não modelados:** multas de SLA, churn ligado a CSAT, custo de ticket mal roteado. Ficaram de fora por falta de dados e podem melhorar o caso.
9. **Fila Financeiro/Comercial (B2C)** não entra neste ROI. Ela precisa de um modelo próprio, com custo de chargeback e reembolso.
"""
open('/home/ubuntu/g4_challenge/fase3/06_roi_model.md','w').write(txt); print('ok')
