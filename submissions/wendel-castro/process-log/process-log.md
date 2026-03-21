# Process Log — Como usei IA neste challenge

## Nota sobre as evidências visuais

O trabalho original foi feito via **Claude Code** — uma interface de IA via linha de comando (CLI no terminal), não uma interface de chat com UI visual. É assim que eu trabalho no dia a dia: terminal aberto, Claude como copiloto, eu direcionando cada passo.

Na primeira submissão, não incluí screenshots porque o foco estava na entrega. Ao receber o feedback de revisão, reproduzi os momentos-chave do processo com documentação visual. As screenshots anexas são reproduções fiéis do fluxo original — os mesmos comandos, os mesmos dados, as mesmas decisões. O código e os resultados são idênticos.

---

## Ferramentas usadas

| Ferramenta | Para quê | Quem direcionou |
|-----------|---------|-----------------|
| Claude Code (Claude Opus 4, via CLI) | Copiloto principal. Gerou código Python, executou análises, construiu dashboard | Eu direcionava; Claude executava |
| WebSearch/WebFetch (via Claude Code) | Pesquisa sobre a G4 Educação: site, LinkedIn, YouTube, entrevistas | Eu pedia tópicos específicos; Claude buscava |
| Python + Pandas | Processamento e análise estatística do dataset | Claude gerava; eu validava outputs |
| Plotly + Matplotlib + Seaborn | Geração dos 7 gráficos de análise | Eu definia o que visualizar; Claude implementava |
| Streamlit | Dashboard interativo com 5 abas | Eu definia UX e conteúdo das abas; Claude construía |

---

## Workflow detalhado: como o processo aconteceu de verdade

### Fase 1: Pesquisa de contexto (antes de tocar nos dados)

**O que fiz:** Antes de abrir o dataset, pedi ao Claude para pesquisar a fundo sobre a G4 Educação. Queria entender quem ia ler minha entrega, o que valorizam, como pensam sobre IA.

**O que pedi ao Claude:**
- "Pesquisa sobre a G4 Educação: quem são, o que fazem, quem são os fundadores"
- "Busca entrevistas do Alfredo Soares e do João Vitor sobre uso de IA na empresa"
- "O que a G4 espera de um AI Master? Olha o LinkedIn, vagas abertas, cultura"

**O que descobri:**
- A G4 quadruplicou o faturamento com praticamente a mesma equipe usando IA
- Eles buscam profissionais que usam IA como alavanca, não como muleta
- O CPTO (João Vitor) valoriza senso crítico e transparência sobre o que a IA faz e não faz

**Decisão minha:** Isso moldou minha abordagem inteira. Entendi que entregar "40 páginas de insights bonitos" seria pior do que entregar menos, mas com honestidade e profundidade.

---

### Fase 2: Exploração inicial dos dados

**O que pedi ao Claude:** "Carrega o CSV e me dá o panorama completo: shape, tipos, distribuições, nulos."

**O que o Claude me mostrou:** *(ver screenshot 01)*
- 52.214 linhas x 27 colunas
- 27 variáveis cobrindo plataforma, conteúdo, métricas, criador, audiência, patrocínio
- Nulos apenas em hashtags (8.743) e comments_text (8.688)
- Parecia um dataset robusto à primeira vista

**O que pedi em seguida:** "Agora me mostra as estatísticas descritivas das métricas numéricas: views, likes, shares, comments, follower_count."

**O que apareceu — e o que me chamou atenção:** *(ver screenshot 02)*

```
Views:  min=9.676  max=10.551  std=100.03
Likes:  min=1.354  max=1.668   std=38.92
Shares: min=227    max=380     std=17.31
```

Eu olhei esses números e pensei: "Isso não é normal." Em 52 mil posts reais, views variam de 0 a milhões. Aqui, o range total é de 875 unidades. O desvio padrão de views é 100 — isso é uma distribuição absurdamente apertada.

Olhei a distribuição por plataforma: Bilibili 20.30%, YouTube 20.10%, Instagram 19.96%, RedNote 19.92%, TikTok 19.72%. Quase exatamente 20% cada. Em dados reais, plataformas têm distribuições muito diferentes.

**Decisão minha:** Pedi ao Claude para calcular a matriz de correlação entre todas as métricas numéricas. Se os dados fossem reais, views e likes deveriam ter correlação forte. Se fossem sintéticos, tudo ficaria próximo de zero.

---

### Fase 3: Confirmação — dados sintéticos

**O que o Claude me mostrou:** *(ver screenshot 03)*

```
Correlação views x likes:    0.0008
Correlação views x shares:  -0.0074
Correlação likes x shares:   0.0053
```

Todas as correlações próximas de zero. Em dados reais de social media, views-likes tem correlação tipicamente acima de 0.7. Aqui: 0.0008.

Mais evidências:
- Engagement rate por plataforma: range total de **0.01 ponto percentual** (19.8993% a 19.9098%)
- Orgânico vs patrocinado: delta de **0.001pp** — estatisticamente insignificante
- Nomes de sponsors com padrão da biblioteca Faker: "Zamora, Robinson and Sanchez", "Wright-Thompson", "Morris and Sons"
- Descrições de conteúdo em lorem ipsum genérico

**Veredicto:** Dataset gerado por algoritmo (provavelmente Faker + distribuições uniformes/normais apertadas). Não representa dados reais de social media.

---

### Fase 4: O momento de decisão — onde a IA errou e eu corrigi

**O que o Claude gerou primeiro:** *(ver screenshot 04)*

A IA, sem questionar a qualidade dos dados, produziu 5 "insights":
1. "RedNote tem o melhor engagement rate (19.91%) → Concentrar esforços no RedNote"
2. "Conteúdo tipo Text performa melhor que Video → Investir mais em posts de texto"
3. "Conteúdo orgânico tem engagement superior → Reduzir investimento em patrocínio"
4. "Categoria Lifestyle lidera → Focar em lifestyle"
5. "Vídeos performam melhor que imagens → Priorizar formato vídeo"

**Minha reação:** *(ver screenshot 04)*

"Isso não faz sentido. A diferença entre plataformas é 0.01 ponto percentual. Não dá pra recomendar concentrar em RedNote por causa de 0.01pp. Os dados são sintéticos, essas recomendações são baseadas em ruído."

**Resposta do Claude após meu redirecionamento:**

O Claude reconheceu o erro: os deltas de 0.01pp são ruído estatístico, não sinal. Recomendar estratégia com base em diferenças insignificantes seria irresponsável. Concordou em redirecionar para recomendações de processo em vez de conteúdo.

**Por que isso importa:** A IA processou 52K linhas sem questionar. Gerou recomendações bonitas, estruturadas, que pareciam profissionais. Mas estavam erradas. Sem meu senso crítico, a entrega teria "insights" baseados em ruído aleatório. Esse é o risco real de usar IA sem supervisão humana.

---

### Fase 5: Recomendações reais — priorizadas por mim

**O que eu direcionei:** "Refaz as recomendações. Sem insights de conteúdo baseados em dados sintéticos. Foca em processo: o que a empresa precisa fazer ANTES de poder tomar decisões de conteúdo."

**Resultado:** *(ver screenshot 05)*

4 recomendações priorizadas por impacto e viabilidade:

| Prioridade | Recomendação | Por que essa ordem |
|-----------|-------------|-------------------|
| 1 | Implementar coleta de dados estruturada | Sem dados reais, qualquer estratégia é chute |
| 2 | Conectar dados reais ao dashboard entregue | Ferramenta pronta, falta input |
| 3 | Rodar a mesma análise com dados de produção | Código pronto, insights em minutos |
| 4 | A/B testing para validar hipóteses | Mais confiável que análise retrospectiva |

**Decisão minha (não da IA):** A IA inicialmente listou ~20 possibilidades. Eu cortei para 4 priorizadas. Porque o Head de Marketing precisa de clareza, não de opções infinitas. Também adicionei quick wins implementáveis na mesma semana.

---

### Fase 6: Análise completa em 11 dimensões

Mesmo sabendo que os dados são sintéticos, executei a análise completa. O objetivo mudou: não era mais "gerar insights", era **demonstrar a metodologia pronta para dados reais**.

**O que eu definia vs. o que o Claude executava:**

| Eu definia | Claude executava |
|-----------|-----------------|
| "Cruza plataforma x tipo x categoria" | Código pandas com groupby e pivot tables |
| "Segmenta criadores em 5 tiers por followers" | Função de binning com pd.cut |
| "Compara orgânico vs patrocinado controlando por tier" | Análise estratificada com filtros |
| "Mostra evolução temporal por mês" | Parsing de datas e agrupamento mensal |
| "Analisa hashtags: quais correlacionam com engagement" | Explosão de hashtags, agrupamento, ranking |

Eu validava cada output. Quando os resultados mostravam deltas irrelevantes (porque sintéticos), eu não descartava — documentava a limitação e seguia. A metodologia é o entregável, não os números.

---

### Fase 7: Dashboard interativo

**O que eu defini:**
- 5 abas: Visão Geral, Orgânico vs Patrocinado, Audiência, Creators, Recomendador
- Filtros globais por plataforma, tipo, categoria, patrocínio e período
- KPIs no topo de cada aba
- Heatmaps de performance cruzada
- Recomendador de conteúdo baseado em perfil similar
- **Nota de transparência** sobre a natureza dos dados (adição minha, não sugerida pela IA)

**O que o Claude implementou:** Dashboard completo em Streamlit + Plotly. Eu testei cada aba, ajustei labels, e validei que os filtros funcionavam corretamente.

---

## Onde a IA errou e como corrigi

### Erro 1: Não identificou dados sintéticos
**O que aconteceu:** O Claude carregou 52K linhas, calculou estatísticas, e seguiu em frente como se fosse um dataset normal.
**Como percebi:** Olhei os números. Views com std de 100, correlações ~0, distribuições uniformes perfeitas. Não é assim que dados de social media se comportam.
**Como corrigi:** Pedi cálculo explícito de correlações. Confirmei a hipótese. Redirecionei toda a abordagem.

### Erro 2: Gerou recomendações baseadas em ruído
**O que aconteceu:** Com os dados processados, o Claude gerou insights como "RedNote tem melhor engagement" e "Invista mais em texto".
**Como percebi:** A diferença entre plataformas era 0.01pp. Isso não é insight, é ruído estatístico.
**Como corrigi:** Descartei as recomendações de conteúdo. Redirecionei para recomendações de processo (corrigir coleta, A/B testing).

### Erro 3: Path do Windows com acentos
**O que aconteceu:** Python não conseguiu ler o CSV porque o caminho tinha "Inteligência Artificial" com acento.
**Como corrigi:** Claude sugeriu usar raw strings. Problema técnico simples, resolvido em 1 minuto.

---

## O que eu adicionei que a IA sozinha não faria

1. **Senso crítico com os dados.** A IA processou 52K linhas sem questionar. Fui eu que olhei os números e disse "isso não faz sentido, investiga mais". Sem essa intervenção, a entrega teria insights falsos.

2. **Decisão de ser transparente.** A IA teria gerado 40 páginas de "insights" bonitos baseados em ruído. Eu decidi que honestidade é mais valioso que parecer impressionante. Documentei a limitação dos dados como a primeira descoberta, não como uma nota de rodapé.

3. **Contexto de marketing real.** Trabalho com marketing de conteúdo educacional. Sei que:
   - Engagement rate isolado não conta a história toda
   - Micro-influenciadores costumam ter ROI melhor que mega-influenciadores
   - A/B testing é mais confiável que análise retrospectiva
   - O Head de Marketing precisa de clareza, não de complexidade

   Esse contexto direcionou toda a entrega.

4. **Priorização das recomendações.** A IA listou ~20 possibilidades. Eu cortei para 4 priorizadas por impacto e viabilidade, mais 3 quick wins. Porque executivo não quer cardápio — quer direção.

5. **Tom de comunicação.** Cada documento foi ajustado pro meu tom. A IA escreve de um jeito formal e genérico. Eu escrevo direto, com convicção, porque quem vai defender essa entrega numa entrevista sou eu.

6. **Nota de transparência no dashboard.** Adicionei um aviso sobre a natureza dos dados diretamente na interface. A IA não sugeriu isso — para ela, dados são dados.

---

## Evidências visuais

As screenshots abaixo documentam momentos-chave da interação com o Claude Code (CLI no terminal):

| # | Arquivo | Momento | O que demonstra |
|---|---------|---------|-----------------|
| 1 | [16.41.08](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.41.08.jpeg) | Exploração inicial do dataset | Claude carregando o CSV, gerando panorama geral (52K linhas, 27 colunas) |
| 2 | [16.45.10](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.45.10.jpeg) | Estatísticas das métricas de engagement | Números que levantaram a bandeira: views std=100, distribuições uniformes |
| 3 | [16.45.10 (1)](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.45.10%20(1).jpeg) | Correlações entre métricas | Confirmação técnica: todas as correlações ~0 — dados sintéticos |
| 4 | [16.47.48](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.47.48.jpeg) | Código dos insights errados | Claude gerando recomendações baseadas em ruído estatístico |
| 5 | [16.48.07](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.48.07.jpeg) | Output dos insights errados | "RedNote tem melhor engagement" — delta de 0.01pp, sem significância |
| 6 | [16.50.51](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.50.51.jpeg) | **Minha correção + redirecionamento** | **Momento-chave:** eu dizendo "isso não faz sentido" e Claude reconhecendo o erro |
| 7 | [16.52.31](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.52.31.jpeg) | Código das recomendações revisadas | Reconstrução das recomendações focando em processo, não conteúdo |
| 8 | [16.52.51](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.52.51.jpeg) | Recomendações priorizadas (parte 1) | Prioridades 1-4 com ações concretas |
| 9 | [16.53.27](screenshots/WhatsApp%20Image%202026-03-20%20at%2016.53.27.jpeg) | Recomendações priorizadas (parte 2) | Quick wins + nota sobre processo > conteúdo |

A sequência conta a história completa: a IA processou os dados sem questionar → eu identifiquei o problema → redirecionei → resultado final focado em processo.

### Demais evidências

- Todo o código está na pasta `solution/`
- Os 7 gráficos gerados estão em `solution/charts/`
- O dashboard pode ser rodado com `streamlit run solution/dashboard.py`
- O git history mostra a evolução dos commits

---

## Reflexão final

A IA foi essencial neste challenge. Sem ela, o volume de código e análise levaria dias. Com ela, levou horas. Mas a IA sozinha teria entregado um trabalho errado — insights bonitos baseados em dados falsos.

O valor que eu adicionei foi o julgamento: saber quando os números não fazem sentido, ter coragem de ser transparente, e priorizar o que realmente importa. Isso é o que um AI Master faz — não é ser substituído pela IA, é saber dirigi-la.

---

*Wendel Castro | Março 2026*
