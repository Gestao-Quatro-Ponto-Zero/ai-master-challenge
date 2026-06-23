# Process Log — Narrativa do Desenvolvimento

## Ferramenta: Claude Code (Opus 4)

Sessao unica de desenvolvimento. Todo o ciclo — dados, motor, frontend, refinamento — foi feito em conversa continua com o Claude Code, usando o preview integrado para validacao visual.

---

## Fase 1: Exploracao de dados

**Objetivo:** Entender o que existe antes de construir qualquer coisa.

Carreguei o dataset do Kaggle (CRM Sales Predictive Analytics) via API `kagglehub`. 4 tabelas: pipeline (8.800 deals), accounts (~85), products (7), sales_teams (35).

**Descoberta critica:** 1.425 dos 2.089 deals ativos nao tem conta vinculada no CRM. Sao 68% do pipeline. Qualquer motor que dependa de setor, porte ou historico da conta falha para a maioria dos deals.

Essa descoberta redirecionou toda a abordagem. Em vez de um motor baseado em atributos da conta, precisei de um que funcionasse com o que realmente existe: vendedor, produto, datas e valor.

**Outros achados:**
- Taxa global de fechamento: 63.2%
- Mediana de fechamento dos deals Won: 57 dias
- 77% dos Won fecham antes de 90 dias, 97% antes de 120
- Vendedores variam de 38% a 72% de taxa de fechamento
- Apenas ~10 de 27 vendedores tem deals em Prospecting

---

## Fase 2: Motor de scoring — 5 versoes

### v1 — Pesos estaticos (50.7%)

Primeira tentativa: pesos fixos para produto, setor e porte da conta. Resultado: 50.7% de precisao. Praticamente aleatorio. Todos os deals ficavam entre 0.45 e 0.55.

**Minha decisao:** Nao adianta usar atributos estaticos. Precisa de sinais derivados do comportamento real.

### v2 — Sinais derivados + bayesiano (57.2%)

Adicionei sinais comportamentais: taxa do vendedor, fit vendedor-produto, sazonalidade. Implementei suavizacao bayesiana para evitar falsos positivos com poucos dados:

```
smoothed = (wins + m * base_rate) / (closed + m), m=10
```

Um vendedor com 2 wins em 2 deals nao parece mais melhor que um com 80 em 100.

**Problema:** Scores ainda comprimidos (0.42-0.59). Sem diferenciacao util.

### v3 — 11 sinais + cascata de proxies (62.7%)

Expandi para 11 sinais incluindo cascata de proxies: quando nao ha historico direto (vendedor nunca vendeu para aquela conta), o motor desce por niveis: Vendedor-Conta > Gestor-Conta > Vendedor-SetorPorte > Vendedor-Setor > Global.

Resultado: 62.7%. Decis monotonicas. Spread de 39pp entre top e bottom.

**Minha decisao:** O motor v3 inicialmente mostrou 70.3%. Questionei se era overfitting com 11 sinais em 8.800 deals. Pedi versao sem usar account_name como proxy direto. Caiu para 62.7% mas era mais honesto.

### v4 — Simplificacao (57.3%)

Cortei para 5 sinais core eliminando redundancias. Resultado: 57.3%. Pior.

**Minha investigacao:** A queda era contraintuitiva (menos sinais deveria reduzir overfitting, nao piorar). Investiguei e encontrei o problema: dupla-suavizacao.

O confidence_blend aplicava:
```
blended = confidence * taxa_bayesiana + (1-confidence) * fallback
```

Mas a taxa bayesiana ja era suavizada em direcao ao global. Aplicar confidence_blend sobre isso dampena tudo para a media. Resultado: todos os deals ficam parecidos.

### v5 — Cascata com taxas raw (63.6%)

Fix: usar taxas brutas (nao bayesianas) no confidence_blend. A cascata de confianca ja faz o papel de regularizacao, nao precisa de dupla-suavizacao.

```
confidence = min(1, n_deals / threshold)
blended = confidence * taxa_raw + (1-confidence) * taxa_fallback
```

Resultado final: 63.6%. Decis monotonicas: D1=82%, D10=39%. Spread de 43pp.

**5 sinais finais:**
1. Taxa do vendedor (30%) — fallback para media global se <20 deals
2. Vendedor x Produto (25%) — fallback para blend vendedor + produto se <10 deals
3. Relacionamento/conta (25%) — cascata: Vendedor-Conta > Gestor-Conta > Vendedor-Setor > Global
4. Taxa do produto (10%) — estavel, >500 deals por produto
5. Sazonalidade (10%) — fallback para media se mes tem <100 deals

---

## Fase 3: Dashboard v1 (index.html)

Construi SPA com 4 abas:
1. Meus Deals — pipeline priorizado com cards expansiveis
2. Visao Gestor — sliders de peso + performance por vendedor
3. Analytics — graficos por setor, produto, porte, escritorio
4. Validacao — decis + explicacao do motor

**Problemas que identifiquei visualmente (nao por testes):**
- Graficos mostrando "0%" — bug JS referenciando propriedade inexistente
- Linguagem tecnica: "Agent-SectorTier", "AUC", "WR"
- Cores dos graficos mudando com filtros (thresholds relativos ao subset)
- Botao de recalcular pesos nao reclassificava os baldes de acao
- Explicacoes duplicadas nos cards
- 88% dos deals no balde "Nutrir" — thresholds calibrados alto demais

Cada bug veio da minha inspecao visual. A IA nao "ve" que um grafico tem cor inconsistente ou que um texto parece generico.

---

## Fase 4: Dashboard v2 (index.html)

Redesenhei do zero com foco no vendedor. Pergunta guia: "O vendedor abre isso na segunda de manha. O que precisa ver?"

**Decisoes de produto (minhas):**

1. **Tela de login** — Vendedor seleciona seu nome, ve preview do perfil antes de entrar. Sem senha (nao e o ponto).

2. **Plano de acao numerado** — A primeira versao da IA mostrava metricas: "13 para resgatar. 27 contas conhecidas." Eu pedi: "o vendedor precisa saber O QUE FAZER". Resultado: "1. Ligue agora para 2 deals prontos para fechar. Comece por Green-Plus. Total: R$ 550."

3. **Kanban com drag & drop** — 5 colunas por acao. O vendedor pode mover deals entre colunas. Cores da borda e barra de chance mudam automaticamente.

4. **"ID Oportunidade: XXXX"** — Para deals sem conta, em vez de "Conta nova" (generico), mostra o ID real. O vendedor sabe qual deal e.

5. **Modal "Resumo dos Deals"** — Visao consolidada. Cada bucket explica o motivo em linguagem direta: "Potencial real, mas passaram de 90 dias. Aja rapido."

6. **Aba "Como Funciona"** — 6 secoes visuais explicando o calculo sem termos tecnicos. Inclui comparacao contas novas vs conhecidas, timeline de urgencia, formula visual.

---

## Fase 5: Refinamentos

**Logo G4:** Baixei o SVG oficial do site g4business.com (`wp-content/uploads/2026/01/logo-g4-completa-branca.svg`). O primeiro logo era uma aproximacao minha em SVG, o usuario pediu o real.

**Ortografia:** Corrigi todos os acentos (voce > voce, acao > acao, etc.) e removi travessoes.

**Emojis:** O usuario pediu para remover. Tinha 🔥⏰🏁📝🌱 nos headers das colunas.

**"Cara de IA":** Rodada especifica de polish:
- Border-radius: padronizei em 8px/4px (estava 16px em tudo)
- Sombras: reduzi para single-layer sutis
- Padding: apertei para densidade de dashboard real
- Textos: cortei bold excessivo e frases verbosas
- Modal: removi backdrop-filter blur, animacao simples de fade
- Cores: atenuei verde/laranja/vermelho para tom profissional

---

## Erros da IA e como corrigi

| O que a IA fez | O que eu fiz |
|----------------|-------------|
| Aplicou confidence_blend sobre taxas ja suavizadas (dupla-suavizacao) | Identifiquei a queda de precisao, investiguei a causa, forcei uso de taxas raw |
| Scores comprimidos 0.42-0.59 | Pedi sinais multiplicativos mais fortes |
| 88% dos deals em "Nutrir" | Recalibrei thresholds na distribuicao real |
| Usou "Agent-SectorTier", "AUC", "WR" na interface | Forcei traducao para linguagem de vendedor em cada iteracao |
| Banner generico com metricas | Exigi plano de acao numerado com nomes e valores |
| Design com border-radius 16px, blur, sombras excessivas | Rodada de polish especifica para parecer ferramenta real |
| Replace_all causou merges de palavras ("vocese", "voceou") | Corrigi manualmente cada ocorrencia |
| Logo SVG aproximado | Baixei o oficial do site da G4 |

---

## O que eu adicionei que a IA nao faria

1. **Problema dos 68%** — A IA nao questionou que a maioria dos deals nao tem conta. Eu vi nos dados e redirecionei o motor.

2. **Direcionamento real** — A IA da resumos e metricas. Eu exigi acoes concretas: "Ligue para X. Comece por Y. Vale Z."

3. **Fix de dupla-suavizacao** — Bug conceitual que a IA nao detectaria sozinha. A queda de precisao entre versoes era o unico sintoma.

4. **Honestidade** — Rejeitei 70.3% (provavelmente overfitting) e aceitei 63.6% como mais realista.

5. **UX de vendedor** — Cada decisao de interface veio de pensar no uso real, nao na tecnologia.

6. **Controle visual** — Cada bug visual veio da minha inspecao no preview. A IA nao ve inconsistencias de cor, tamanho ou tom.

---

## Tempo total: ~6h

| Fase | Tempo | O que |
|------|-------|-------|
| Exploracao de dados | 30min | Kaggle API, estrutura, findings |
| Motor v1-v5 | 1h30 | 5 iteracoes, debug dupla-suavizacao |
| Dashboard v1 | 1h30 | 4 abas, bugs visuais, 6 rodadas de fix |
| Dashboard v2 | 1h30 | Redesign completo, login, kanban, modal |
| Refinamentos | 1h | Logo, ortografia, polish, README |
