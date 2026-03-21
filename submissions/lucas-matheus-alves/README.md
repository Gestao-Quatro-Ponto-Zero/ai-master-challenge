# Submissão — Lucas Matheus Alves da Silva — Challenge de Marketing Analytics

---

## Sobre mim

- **Nome:** Lucas Matheus Alves da Silva
- **LinkedIn:** : https://www.linkedin.com/in/lucas-matheus-3809aa1
- **Challenge escolhido:**:  Challenge 004 — Estratégia Social Media
---

## Executive Summary

Construímos o G4 Venus, um sistema completo de inteligência para decisões de marketing em redes sociais, processando 52.214 posts reais de cinco plataformas entre maio de 2023 e maio de 2025. A métrica central desenvolvida — o G-Factor — resolve um problema que planilhas convencionais não resolvem: comparar creators de tamanhos completamente diferentes numa mesma escala justa, eliminando o viés de audiência que distorce qualquer análise de influencer marketing. O achado mais importante foi estatístico: nenhuma das cinco plataformas apresentou diferença significativa de engajamento entre posts orgânicos e patrocinados, o que significa que patrocínio serve para alcance e não para engajamento — uma inversão completa da hipótese inicial do time. A principal recomendação é concentrar budget de patrocínio exclusivamente em Instagram e RedNote, migrar conteúdo de Tech do YouTube para o Bilibili, e substituir produção de vídeo por formatos Mixed e Texto, que superam vídeo em engajamento em todas as cinco plataformas.

Link para acesso: https://claude.ai/public/artifacts/dbc495fd-d2e4-4b59-abf8-50f1deca6bec

---

## Solução

**G4 Venus — Social Media Intelligence System**

Dashboard interativo com cinco abas navegáveis construído com identidade visual G4 — azul marinho `#0d2137`, dourado `#c9a96e`, tipografia Playfair Display e Inter — entregando análise completa de 52.214 posts com pipeline Python reproduzível e Recomendador de estratégia por plataforma e categoria.

**Outputs gerados:**

| Arquivo | Conteúdo |
|---|---|
| `dados_completos_5plat.csv` | 52.214 linhas com todas as métricas derivadas |
| `lift_roi_5plat.csv` | 314 grupos validados com lift orgânico vs patrocinado |
| `roi_financeiro_5plat.csv` | 60 segmentos com ROI proxy ordenados por retorno |
| `dashboard_social_media.html` | Dashboard G4 Venus completo e interativo |
| `analise_sponsorship.py` | Pipeline Python documentado em português |

---

## Abordagem

O trabalho começou às **15h40 com papel e caneta**, sem acesso ao computador. Essa restrição foi deliberadamente aproveitada: forçou que o problema fosse entendido antes de qualquer tentativa de solução técnica.

**Por onde comecei**

Leitura do enunciado sem anotar nada nos primeiros 20 minutos. O objetivo era identificar o que o Head de Marketing realmente precisava, não o que estava escrito literalmente. Três perguntas centrais foram isoladas: o que gera engajamento, quando patrocínio vale o investimento, e onde concentrar esforço e budget.

**Como decompus**

No papel foram identificadas três limitações analíticas em sequência. Primeira: engajamento absoluto não compara posts de alcances diferentes — precisava de uma taxa. Segunda: ER isolado ainda mente porque não controla pelo tamanho do creator — precisava de normalização contextual. Terceira: a diferença entre orgânico e patrocinado precisava ser testada estatisticamente, não apenas observada visualmente.

**O que priorizei**

A normalização contextual foi a prioridade técnica central — tudo dependia de ter uma métrica justa antes de fazer qualquer comparação. O G-Factor foi formulado primeiro no Grok ainda pelo celular, antes do PC estar disponível. Só depois vieram as análises de patrocínio, ROI e timing.

**Linha do tempo real:**
```
15h40 → 17h00   Papel, caneta e Grok no celular — planejamento e fórmulas
17h00 → 18h00   Claude — pipeline Python e análise dos 52.214 posts
18h00 → 18h45   Claude — dashboard e identidade visual G4 Venus
18h45 → 19h20   Replit — refinamento de código, operações e UX
19h20 → 19h50   Claude — versão final, process log e entrega
```

---

## Resultados / Findings

**Métricas desenvolvidas**

$$\text{engagement\_total} = \text{likes} + \text{shares} + \text{comments}$$

$$\text{ER} = \frac{\text{engagement\_total}}{\max(\text{views},\ 1)} \times 100$$

$$\text{G\_Factor} = \frac{\text{ER}_{\text{individual}}}{\text{mediana(ER)}_{\text{(platform, tier)}}}$$

$$\text{lift\_G} = \frac{\text{G\_Factor}_{\text{patrocinado}}}{\text{G\_Factor}_{\text{orgânico}}}$$

$$\text{ROI\%} = \frac{(\text{engagement\_total} \times 0{,}03) - \text{custo\_tier}}{\text{custo\_tier}} \times 100$$

$$t = \frac{\bar{x}_1 - \bar{x}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}}$$

$$\text{CV} = \frac{\sigma(\text{G\_Factor})}{\mu(\text{G\_Factor})}$$

**Principais descobertas**

- **RedNote** tem o maior ER do dataset (19.91%) e representava 20% dos posts — estava completamente fora da análise anterior
- **Bilibili** supera YouTube em Tech por **0.029pp** — a maior diferença de plataforma por categoria encontrada
- **Formato Mixed** supera Video em engajamento em todas as 5 plataformas, apesar de Video representar 60% do volume produzido
- **Patrocínio não move engajamento** em nenhuma plataforma — p-valor mínimo encontrado foi 0.13 (TikTok), todas acima do threshold de 0.05
- **Instagram e RedNote** são as únicas plataformas com delta positivo de patrocinado sobre orgânico, mesmo que não significativo estatisticamente
- **Micro creators** (10k–100k) têm CV do G-Factor de até **4.3%** versus menos de **1%** nos Mega — maior variância significa maior chance de outlier positivo por menor custo
- **Disclosure explícita** tem ER **0.009pp maior** que a implícita e não traz nenhuma desvantagem mensurável
- **Cosméticos e Alimentação** são as categorias de patrocínio com maior ER — Moda é consistentemente a pior

**Top 5 combinações por engajamento (mín. 30 posts):**

| # | Plataforma | Formato | Categoria | Tier | ER |
|---|---|---|---|---|---|
| 1 | Instagram | Mixed | Beleza | Micro | 20.10% |
| 2 | YouTube | Mixed | Lifestyle | Micro | 20.04% |
| 3 | RedNote | Mixed | Beleza | Micro | 20.04% |
| 4 | Instagram | Texto | Beleza | Médio | 19.99% |
| 5 | TikTok | Imagem | Lifestyle | Micro | 19.99% |

---

## Recomendações

Em ordem de impacto e facilidade de execução imediata:

1. **Fazer já — 30 minutos** — Personalizar o calendário de postagem por plataforma: RedNote na Sexta, TikTok no Sábado, Bilibili na Quinta. Zero custo adicional de produção.

2. **Fazer já — 30 minutos** — Converter 100% das divulgações para explícitas. ER +0.009pp, sem risco legal, sem nenhuma desvantagem.

3. **Fazer já — próximo ciclo** — Concentrar todo budget de patrocínio em Instagram e RedNote. Suspender patrocínio em TikTok e YouTube para objetivos de engajamento — o orgânico supera o patrocinado nessas plataformas.

4. **Fazer já — próximo ciclo** — Encerrar deals com Mega creators para objetivos de ER. ROI proxy de -99.9% com G-Factor idêntico ao orgânico. Usar o arquivo `lift_roi_5plat.csv` e só fechar novos deals com creators com G-Factor histórico ≥ 1.05 no nicho alvo.

5. **Semana 1 — 2 a 3 dias de produção** — Criar posts Mixed de Lifestyle no RedNote publicados na Sexta. Maior engajamento cruzado encontrado no dataset.

6. **Semana 1 — 1 semana de planejamento** — Mover conteúdo de Tech do YouTube para o Bilibili. Ganho imediato de 0.029pp sem produção adicional.

7. **Planejar — 1 a 2 semanas** — Testar Beauty no TikTok aos Sábados. Maior ER de Beleza entre todas as plataformas nessa combinação.

8. **Planejar — 1 trimestre** — Desenvolver conteúdo voltado para audiência 50+ no Bilibili. Segmento com maior ER da plataforma (19.93%) e pouco explorado.

---

## Limitações

**O dataset é provavelmente sintético.** A distribuição de views é artificialmente uniforme — concentrada entre 9.676 e 10.551, com desvio padrão de apenas 100 para uma média de 10.100. Em dados reais de redes sociais a distribuição seria log-normal com variância muito maior. Todas as análises são metodologicamente corretas, mas os valores absolutos e os tamanhos de efeito precisariam ser revalidados com dados reais de produção antes de qualquer decisão financeira.

**O ROI proxy é uma estimativa de referência, não uma medida real.** O coeficiente de R$ 0,03 por engajamento é uma aproximação baseada em CPM médio de mercado brasileiro de 2024. O valor real varia por setor, plataforma e objetivo de campanha — podendo ser 50 vezes maior para marcas de luxo ou 3 vezes menor para e-commerce de massa. Os custos por tier também são estimativas de mercado, não contratos reais.

**Patrocínio e orgânico não foram controlados por qualidade de criativo.** O t-test compara ER médio entre grupos mas não controla por variáveis de confundimento como qualidade do criativo, relevância do produto para a audiência ou nível de autenticidade da divulgação. Uma análise mais rigorosa exigiria controle experimental ou scoring de qualidade de criativo.

**O modelo não captura retorno além do engajamento direto.** Brand awareness, crescimento de seguidores, tráfego para site, geração de leads e conversão em vendas não estão no dataset. O sistema mede bem o que os dados permitem medir, mas não deve ser usado como única fonte de verdade para decisões de patrocínio de alto valor. Outro ponto a adicionar é que o dataset não contempla plataformas de nichos

**O Recomendador é baseado em padrões históricos, não em previsão.** Mudanças de algoritmo nas plataformas, sazonalidade não capturada e tendências emergentes de formato não estão modeladas. O sistema precisa ser reprocessado periodicamente com dados novos para manter relevância.Infelizmente não pude usar algoritmos de inteligência artificial como XGBoost ou mesmo escolhas binarias mais simples

**Interface e experiência do usuário no Recomendador.** O Recomendador funciona analiticamente — as lógicas de recomendação estão corretas e os dados que alimentam as respostas são reais — mas apresenta problemas de UX e UI que não foi possível resolver dentro do tempo disponível e que gostaríamos muito de corrigir em versões futuras. O formulário não dá feedback visual claro durante o preenchimento, a área de resultado aparece de forma abrupta sem transição, e em telas menores os elementos se sobrepõem comprometendo a leitura. A correção desses pontos está no topo da lista de prioridades para a próxima iteração.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Grok (celular) | Formulação do G-Factor, arquitetura conceitual do pipeline e levantamento da hipótese estatística — tudo antes de ter acesso ao PC |
| Claude | Implementação do pipeline Python, análise dos 52.214 posts, geração dos CSVs, construção do dashboard, aplicação da identidade visual G4 Venus e redação do process log |
| Replit | Refinamento do código para robustez operacional, stress test com variações de dataset e ajuste da linguagem do dashboard para vocabulário executivo |

---

### Workflow

**1. 15h40 — Papel e caneta: leitura e primeiras fórmulas**

Antes de qualquer ferramenta, leitura do enunciado com papel e caneta. Identificação das três perguntas centrais e das três limitações analíticas em sequência. Primeiras fórmulas deduzidas manualmente:
```
engajamento = likes + shares + comments
ER = (engajamento / max(views, 1)) × 100
```

Identificação da necessidade de normalização contextual — anotada como "precisamos de um ER relativo ao contexto do creator", sem fórmula ainda.

**2. 16h25 — Grok no celular: G-Factor e arquitetura**

Com a necessidade identificada no papel, o Grok foi usado para transformar a intuição em fórmula. A pergunta levada ao Grok descrevia o problema completo: creator X, Y seguidores, público F ou M, faixa etária H, horário A, dia B, categoria C, com ou sem collab, hashtags T — qual número único resume se o post performou acima ou abaixo do esperado? O G-Factor emergiu:
```
G_Factor = ER_individual / mediana(ER) do grupo (platform, tier)
lift_G = G_Factor_patrocinado / G_Factor_orgânico
t = (x̄₁ - x̄₂) / √(s₁²/n₁ + s₂²/n₂)
```

**3. 17h00 — Claude: pipeline e análise completa**

Com o PC disponível, o Claude implementou o pipeline completo. Fórmulas derivadas nessa etapa:
```
like_rate = (likes / max(views, 1)) × 100
share_rate = (shares / max(views, 1)) × 100
comment_rate = (comments / max(views, 1)) × 100
valor_gerado = engagement_total × 0,03
ROI% = ((valor_gerado - custo) / custo) × 100
CV = desvio_padrão(G_Factor) / média(G_Factor)
```

**4. 18h00 — Claude: dashboard e identidade visual**

Construção do dashboard com identidade G4 Venus. Quatro versões com erros de JavaScript antes da versão estável — causa raiz identificada e corrigida pelo Claude.

**5. 18h45 — Replit: refinamento**

Iteração sobre variações do código, stress test com datasets variados e reformulação da linguagem para executivos.

**6. 19h20 — Claude: versão final e entrega**

Consolidação de todos os outputs e redação do process log completo.

---

### Onde a IA errou e como corrigi

**Filtro incorreto de plataformas** — O Claude aplicou o filtro inicial do brief (apenas Instagram, TikTok e YouTube) sem questionar. Bilibili e RedNote — 40% do dataset — foram ignorados nas primeiras versões. Eu questionei a completude dos dados e o Claude verificou o CSV original, identificando as duas plataformas ausentes. O reprocessamento revelou que RedNote tem o maior ER do dataset e mudou completamente as recomendações estratégicas.

**Valores invertidos no gráfico de orgânico vs patrocinado** — O Claude hardcodeu os valores do gráfico de comparação org vs spon com os dados do Instagram invertidos — patrocinado aparecia menor quando na realidade supera o orgânico nessa plataforma. Identifiquei ao revisar os números contra o CSV e o Claude corrigiu com verificação sistemática de todos os valores.

**Três versões de JavaScript que quebravam** — O Claude gerou três versões consecutivas do dashboard com erros de JavaScript (`goTab is not defined`, `SyntaxError: Unexpected token`). A causa raiz eram caracteres UTF-8 acima de ASCII 127 dentro do bloco script e dependência de Chart.js via CDN bloqueada pelo ambiente. Eu pressionei por diagnóstico da causa raiz em vez de aceitar correções sintomáticas, e o Claude reescreveu o JS em ES5 puro sem dependências externas.

**Linguagem técnica demais para o público-alvo** — As primeiras versões do dashboard usavam terminologia de dados — "Engagement Rate", "disclosure type", "tier". Eu identifiquei que o Head de Marketing não é data scientist e forcei a reformulação completa da linguagem para "taxa de engajamento", "tipo de divulgação" e "tamanho de creator".

---

### O que eu adicionei que a IA sozinha não faria

**O planejamento analógico inicial.** Papel e caneta antes de qualquer ferramenta não foi romantismo — foi método. Identificar as três limitações do ER em sequência lógica (absoluto → relativo → normalizado) antes de abrir o computador garantiu que o G-Factor fosse a métrica certa antes de qualquer linha de código ser escrita. A IA tende a ir direto para a solução técnica; o humano precisa garantir que é o problema certo sendo resolvido.

**A nomeação G4 Venus e o raciocínio por trás.** Venus é o nome romano de Afrodite, deusa do amor, da beleza e da sedução. Redes sociais são fundamentalmente plataformas de exposição, vaidade e conexão emocional — os mesmos domínios de Afrodite. O dataset é dominado por categorias de Beauty e Lifestyle. Influenciadores vendem imagem, presença e desejo de pertencimento. Nenhuma IA chegaria nessa conexão conceitual sozinha — ela emergiu de um raciocínio sobre o que o sistema representa, não apenas o que ele faz.

**A decisão de questionar o filtro de plataformas.** O Claude seguiu o brief sem questionar. Eu percebi que 40% dos dados estava sendo ignorado e forcei a verificação. RedNote e Bilibili não estavam no brief original, mas estavam no dataset — e mudaram completamente a análise.

**O critério de qualidade que guiou todas as decisões.** A pergunta "o Head de Marketing sabe o que fazer na segunda-feira depois de ler isso?" foi anotada no papel às 15h40 e usada como filtro para cada decisão subsequente — quais métricas incluir, qual linguagem usar, qual ordem de prioridade das recomendações. Esse critério não veio da IA, veio da leitura atenta do enunciado.

---

### Evidências

- `dados_completos_5plat.csv` — dataset completo processado com todas as métricas
- `lift_roi_5plat.csv` — tabela de lift com 314 grupos validados
- `roi_financeiro_5plat.csv` — ROI proxy por 60 segmentos
- `analise_sponsorship.py` — pipeline Python completo documentado em português
- `dashboard_social_media.html` — dashboard G4 Venus interativo
- `g_factor_explainer_interativo` — Versão interativa


---

*Submissão enviada em: 20 - 03 - 2026*