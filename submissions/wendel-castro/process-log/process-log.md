# Process Log — Como usei IA neste challenge

## Ferramentas usadas

| Ferramenta | Para quê |
|-----------|---------|
| Claude Code (Claude Opus) | Copiloto principal. Gerou código, analisou dados, construiu dashboard, ajudou a estruturar entregas |
| WebSearch/WebFetch (via Claude Code) | Pesquisa sobre a G4, entendimento do contexto da empresa |
| Python + Pandas + Plotly + Streamlit | Stack de análise e visualização |

## Workflow: como o processo aconteceu de verdade

### Passo 1: Entender antes de executar

Antes de abrir o dataset, pesquisei a fundo sobre a G4. Queria entender quem ia ler minha entrega, o que valorizam, como pensam sobre IA. Pedi ao Claude para varrer a web: site da G4, LinkedIn, YouTube, podcasts, entrevistas do Alfredo Soares e do João Vitor (CPTO).

Descobri que a G4 quadruplicou o faturamento com praticamente a mesma equipe usando IA. Entendi que eles buscam profissionais que usam IA como alavanca, não como muleta. Isso moldou minha abordagem inteira.

### Passo 2: Exploração dos dados

Pedi ao Claude para carregar o CSV e me dar o panorama: shape, tipos, distribuições, nulos. Ele gerou o código, eu li os resultados.

Foi aí que percebi que algo estava estranho. Views com desvio padrão de 100 em 52K posts? Engagement rate variando 4 pontos percentuais no total? Distribuições exatamente iguais entre plataformas?

Pedi para o Claude calcular correlações entre variáveis numéricas. Todas próximas de zero. Confirmei: dados sintéticos.

**Decisão minha (não da IA):** Ao invés de fingir que os dados são reais e forçar insights, decidi ser transparente. Isso é o que um profissional de verdade faz. A IA não sugeriu isso. Eu que decidi que honestidade importa mais que parecer que achei algo impressionante.

### Passo 3: Análise completa mesmo assim

Mesmo sabendo que os dados são sintéticos, executei a análise em 11 dimensões. Por quê? Porque o que importa é demonstrar que sei fazer. O código funciona. A metodologia é sólida. Quando os dados reais chegarem, os insights saem na hora.

Eu definia o que cruzar (plataforma x tipo x categoria x tier do criador). O Claude gerava o código. Eu validava se os resultados faziam sentido. Quando não faziam (porque dados sintéticos), eu documentava.

### Passo 4: Dashboard

Pedi ao Claude para construir um dashboard em Streamlit com 5 abas. Eu defini o que cada aba deveria ter e como o time de social media usaria no dia a dia. Ele implementou. Eu testei, ajustei, e adicionei a nota de transparência sobre os dados.

### Passo 5: Recomendações

Aqui é onde a IA sozinha não funciona. As recomendações vieram de mim, baseadas em experiência real com marketing de conteúdo. A IA me ajudou a estruturar, mas o julgamento de dizer "prioridade 1 é corrigir a coleta de dados antes de definir estratégia" veio da minha vivência.

## Onde a IA errou e como corrigi

1. **Não percebeu os dados sintéticos sozinha.** Na primeira análise, o Claude gerou insights como "RedNote tem melhor engagement". Fui eu que olhei os números, vi que a diferença era 0.01pp, e questionei. Aí pedimos para calcular correlações e confirmamos que era tudo ruído.

2. **Recomendações genéricas.** As primeiras sugestões do Claude eram do tipo "invista mais em vídeo" e "foque nas plataformas com melhor engagement". Descartei. Com dados sintéticos, recomendações baseadas em deltas de 0.01pp não fazem sentido. Redirecionei para recomendações de processo (melhorar coleta, implementar A/B testing).

3. **Path do Windows com acentos.** O Python não conseguiu ler o arquivo por conta de encoding no caminho (pasta "Inteligência Artificial" com acento). Claude corrigiu usando raw strings.

## O que eu adicionei que a IA sozinha não faria

1. **Senso crítico com os dados.** A IA processou 52K linhas sem questionar. Fui eu que olhei e disse "isso não faz sentido, investiga mais".

2. **Decisão de ser transparente.** A IA teria felizmente gerado 40 páginas de "insights" falsos. Eu decidi que honestidade é mais valioso.

3. **Contexto de marketing real.** Trabalho com marketing de conteúdo educacional. Sei que engagement rate isolado não conta a história toda. Sei que micro-influenciadores costumam ter ROI melhor. Sei que A/B testing é mais confiável que análise retrospectiva. Esse contexto direcionou toda a entrega.

4. **Tom de comunicação.** A IA escreve de um jeito. Eu escrevo de outro. Cada documento foi ajustado pro meu tom, pro meu jeito de explicar. Porque quem vai defender essa entrega numa entrevista sou eu, não a IA.

5. **Priorização das recomendações.** A IA listou 20 possibilidades. Eu escolhi 4 priorizadas por impacto e viabilidade. Porque o Head de Marketing precisa de clareza, não de opções infinitas.

## Evidências

- Todo o código está na pasta `solution/`
- Os gráficos gerados estão em `solution/charts/`
- O dashboard pode ser rodado com `streamlit run solution/dashboard.py`
- Este process log é a documentação do processo
- O histórico de conversa com o Claude Code pode ser exportado mediante solicitação

---

*Wendel Castro | Março 2026*
