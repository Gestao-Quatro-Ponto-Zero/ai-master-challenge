# Submissao — Victor Almeida — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Victor Almeida
- **LinkedIn:** https://www.linkedin.com/in/victoralmeidadeveloper/
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary
EU USEI AI EM TODOS OS PASSOS DESSE DOCUMENTO E DO DESENVOLVIMENTO.

Construi uma ferramenta funcional de priorizacao de pipeline que resolve o problema central da Head de RevOps: vendedores gastando tempo em deals que nao vao fechar. A aplicacao calcula um score de 0-100 para cada deal ativo combinando 5 componentes (stage, valor, velocidade, seller-fit e saude da conta), identifica deals "zumbis" que inflam o pipeline, e gera recomendacoes especificas de proxima acao para cada oportunidade. A analise revelou que **47% dos deals em Engaging estao parados ha mais do que o dobro do tempo esperado**, representando pipeline inflado que distorce o forecast. O vendedor abre a ferramenta, filtra pelo seu nome, e sabe exatamente onde focar.

---

## Solucao

### Abordagem

Antes de escrever qualquer codigo, investi tempo significativo entendendo o problema de negocio e os dados.

**Fase 1 — Setup e decomposicao do problema**

Comecei configurando o `CLAUDE.md` na raiz do projeto com o contexto completo do challenge, regras de submissao e criterios de qualidade. Depois, extrai toda a conversa de analise inicial do Claude Chat para um `INSTRUCTIONS.md` e pedi ao Claude Code que lesse esse contexto junto com o README do challenge para gerar o PRD. O ponto aqui foi: antes de codar qualquer coisa, eu precisava de um mapa claro do que construir.

**Fase 2 — Exploracao profunda dos dados**

Carreguei os 4 CSVs no Claude Chat e pedi analise profunda. Descobertas que moldaram o design:

- **Achado contra-intuitivo:** deals que levam 91-150 dias para fechar tem win rate de 71.1%, superior aos de 0-15 dias (56.1%). Isso me fez usar P75 (88 dias) como referencia de velocidade em vez da mediana (57 dias), evitando penalizar deals que ainda tem boa chance.
- **Pipeline massivamente inflado:** mediana dos deals ativos em Engaging = 165 dias, vs 57 dias dos que fecham. 88.3% dos deals ativos estao acima do dobro da mediana Won.
- **68.5% dos deals em Engaging nao tem conta associada** — isso limita estruturalmente os componentes de seller-fit e saude da conta. O peso desses componentes (10% e 15%) reflete essa limitacao.
- **Inconsistencia GTXPro:** "GTXPro" no pipeline vs "GTX Pro" no catalogo de produtos (1.480 deals afetados). Normalizado no carregamento.

**Fase 3 — Specs tecnicas (PRD → SPECS → validacao cruzada)**

Criei specs detalhadas para cada modulo: data model, scoring engine, deal zombie, NBA, filtros, metricas, pipeline view. O processo foi iterativo — Claude Chat revisava as specs e encontrava inconsistencias, eu validava com Claude Code contra os dados reais, e vice-versa. Esse ping-pong entre as duas ferramentas funcionou como sistema de checks cruzados.

Exemplo concreto: Claude Chat gerou um documento de correcoes com 8 itens. Levei ao Claude Code, que concordou com 6 e discordou de 2 com justificativa. Voltei ao Claude Chat com as discordancias — ele concordou que Claude Code estava certo. Esse tipo de iteracao e o que garante qualidade.

**Fase 4 — Implementacao com TDD e validacao continua**

Implementei modulo por modulo com Claude Code, criando testes antes da implementacao. A cada modulo, validava contra os dados reais. Criei um arquivo TASKS.md para rastrear o progresso. Resultado final: 188 testes cobrindo todos os modulos, 100% passando.

### Resultados

**Aplicacao funcional** — Streamlit app com:

- **Scoring de 5 componentes** com pesos calibrados: Stage (35%), Valor (25%), Velocidade (15%), Seller-Fit (10%), Saude da Conta (15%)
- **Sistema de Deal Zumbi** que identifica 750 deals (36% do pipeline ativo) parados alem do dobro da referencia temporal, com classificacao em faixas de gravidade
- **Next Best Action (NBA)** com 7 regras priorizadas que geram recomendacoes especificas por deal (ex: "Deal em risco — parado ha 145 dias. Enviar case de sucesso do setor technology")
- **Filtros hierarquicos** com cascata Regiao → Manager → Vendedor, mais filtros por produto, setor, faixa de score e toggle de zumbis
- **Dashboard de metricas** com KPIs, distribuicao por faixa de score, e grafico de saude do pipeline
- **Explainability completa** — cada deal tem breakdown dos 5 componentes com explicacao textual em linguagem acessivel
- **188 testes automatizados** cobrindo data loader, scoring engine, deal zombie, NBA, filtros, metricas, pipeline view, formatters e fluxo E2E

**Distribuicao de scores (calibrada):**

| Faixa | Deals | % |
|-------|------:|--:|
| Critico (0-39) | 144 | 6.9% |
| Risco (40-59) | 516 | 24.7% |
| Atencao (60-79) | 1.413 | 67.6% |
| Alta Prioridade (80-100) | 16 | 0.8% |

Os 16 deals em "Alta Prioridade" sao genuinamente os melhores: todos em Engaging, com velocidade saudavel e bom produto.

### Recomendacoes

1. **Limpeza imediata do pipeline:** 750 deals zumbis representam valor inflado no forecast. Agendar revisao de pipeline por vendedor com filtro de zumbis.
2. **Foco nos 16 deals de alta prioridade:** sao as oportunidades com maior probabilidade de fechar — priorizar reunioes de proposta.
3. **Atencao as contas problematicas:** Hottechi (82 losses), Kan-code (72), Konex (63) — reavaliar se vale continuar investindo tempo.
4. **Associar contas aos deals:** 68.5% dos deals ativos nao tem conta no CRM, limitando a inteligencia da ferramenta.

### Limitacoes

- **Deals em Prospecting nao tem dados temporais** — o dataset nao registra quando o deal entrou em Prospecting (`created_date` nao existe). Velocidade recebe score neutro (50) e deals em Prospecting nao sao classificados como zumbi. Decisao consciente documentada nas specs.
- **Score maximo de Prospecting e ~62.8** — consequencia dos pesos e do score neutro de velocidade. Analisei se deveria ajustar e conclui que nao: faz sentido que Engaging (ja qualificado) tenha prioridade sobre Prospecting.
- **Seller-Fit limitado por dados** — 68.2% dos deals ativos nao tem conta associada, recebendo score neutro. Baixar o threshold de 5 para 3 deals salvaria apenas 17 deals de 1.451. Irrelevante.
- **Dataset e estatico (CC0 Kaggle)** — em producao, seria necessario integracao com CRM real e atualizacao continua.

---

## Process Log — Como usei IA

> **Este bloco e obrigatorio.** Sem ele, a submissao e desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|---------------|
| Claude Chat (Opus) | Analise exploratoria dos dados, revisao de specs, validacao cruzada com dados reais, identificacao de bugs, calibracao de scoring |
| Claude Code (Opus) | Implementacao dos modulos, criacao de testes, correcao de bugs, geracao de CLAUDE.md e PRD |

### Workflow

**1. Setup do ambiente de IA**
- Criei `CLAUDE.md` na raiz com contexto do challenge, regras e criterios
- Extrai conversa inicial do Claude Chat → `INSTRUCTIONS.md`
- Claude Code leu INSTRUCTIONS.md + CLAUDE.md + README do challenge → gerou PRD

**2. Exploracao dos dados**
- Carreguei os 4 CSVs no Claude Chat para analise profunda
- Descobri padroes: win rate vs tempo (contra-intuitivo), pipeline inflado, 68.5% sem conta
- Claude Chat validou todas as constantes das specs contra os dados reais

**3. Especificacao iterativa (o ciclo mais importante)**
- Escrevi specs tecnicas para 7 modulos
- Claude Chat revisou → encontrou inconsistencias entre specs
- Claude Chat gerou documento de correcoes (8 itens)
- Levei ao Claude Code → concordou com 6, discordou de 2 com justificativa
- Voltei ao Claude Chat com as discordancias → concordou que Claude Code estava certo
- Atualizei specs com as correcoes validadas

**4. Implementacao com TDD**
- Claude Code implementou modulo por modulo seguindo specs corrigidas
- Testes unitarios criados junto com o codigo
- TASKS.md para rastrear progresso

**5. Calibracao do scoring (3 iteracoes)**
- v1: 82% dos deals em "Risco", 0% em "Alta Prioridade" → inutil
- Diagnostico: decay muito agressivo + pesos desbalanceados
- v2: ajustei pesos (velocity 25%→15%, stage 30%→35%) e suavizei decay
- v3: fine-tuning de stage scores (Prospecting 30→15, Engaging 70→90)
- Final: distribuicao diferenciada com 4 faixas funcionais

**6. Validacao final**
- 188 testes automatizados: data loader, scoring engine, deal zombie, NBA, filtros, metricas, pipeline view, formatters, E2E
- Resultado: 188/188 passando (100%)
- Bug encontrado durante desenvolvimento: deals caindo entre fronteiras das faixas de score (float vs int) → corrigido
- 3 pontos analisados e conscientemente mantidos (Prospecting teto 62.8, Account Health max 72.5, Seller Fit concentrado em 50)

### Onde a IA errou e como corrigi

| O que a IA fez | Problema | O que eu fiz |
|----------------|----------|--------------|
| Specs referenciavam `created_date` | Campo nao existe no dataset | Validei contra CSV, redefini tratamento de Prospecting: score neutro, sem zombie, sem NBAs temporais |
| Primeira calibracao: 82% numa faixa | Scoring nao diferenciava nada | Iterei 3 vezes em pesos e decay table ate distribuicao funcional |
| Spec dizia "nao corrigir" typo `technolgy`, outra dizia "corrigir" | Contradicao entre specs | Analisei que JOIN é por `account` nao por `sector` → corrigir não quebra nada → decidi corrigir |
| Claude Chat sugeriu NBA-07 (Deal Sem Conta) | 68% dos deals disparariam → ruido | Descartei. Metrica pro manager + "Sem conta" na tabela ja cobrem |
| Claude Chat sugeriu renomear `product_price` para `sales_price` | E nome de parametro, n˜o de coluna | Claude Code justificou: clareza semantica > consistencia mecanica. Concordei |
| Faixas de score com limites inteiros | Deals com score float (39.7) caem entre faixas | Encontrado na validacao com testes → corrigido |

### O que eu adicionei que a IA sozinha nao faria

- **Usar P75 em vez de mediana como referencia de velocidade:** veio da analise dos dados, nao de prompt generico. IA sozinha teria usado mediana e classificado 88% como zumbi (inutil).
- **Decisao de NAO ajustar componentes "comprimidos":** Account Health max 72.5 e Seller Fit concentrado em 50 sao consequencias dos dados reais. A tentacao e ajustar pra "espalhar mais", mas seria inflar numeros sem informacao real.
- **Sistema de checks cruzados:** usar Claude Chat e Claude Code como revisores um do outro, nao como oraculo unico. Quando discordaram, analisei as justificativas e tomei a decisao.
- **Curadoria de features:** descartei sugestoes que adicionariam complexidade sem valor. "O que nao colocar" e tao importante quanto "o que colocar".
- **Contexto de produto:** sou co-fundador de um SaaS para dealerships e trabalho com RevOps. Isso informou decisoes como priorizar explainability sobre sofisticacao do modelo.

---

## Evidencias

- [x] Narrativa escrita detalhada (este documento)
- [x] Vídeos do meu workflow dentro de `process-log/videos-workflow`
- [x] Screenshots da interação com a AI, dentro de `process-log/printscreen-claude`
- [x] Chat das implementações das fases dentro de `process-log/implementacao-fases-chat-claude-code`
- [x] Git history mostrando evolucao do codigo
- [x] 188 testes automatizados com resultados (188/188 = 100%)
- [x] Testes E2E do fluxo completo da aplicacao

---

## Como rodar

```bash
# Na raiz do repositorio
cd submissions/victor-almeida/solution

# Instalar dependencias
pip install -r requirements.txt

# Rodar a aplicacao
streamlit run app.py

# Rodar os testes
python -m pytest tests/ -v
```

A aplicacao abre em `http://localhost:8501`. Os dados CSV estao incluidos na pasta `data/`.

---

*Submissao enviada em: 2026-03-22*
