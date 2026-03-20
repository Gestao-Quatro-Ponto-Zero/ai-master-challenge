# Submissão — Wendel Castro — Challenge 004

## Sobre mim

- **Nome:** Wendel Castro
- **LinkedIn:** [linkedin.com/in/wendelcastro](https://linkedin.com/in/wendelcastro)
- **Challenge escolhido:** 004 — Estratégia Social Media

## Resumo Executivo

Analisei 52.214 posts cross-platform para responder três perguntas: o que gera engajamento, se patrocínio vale a pena, e qual deve ser a estratégia. Logo na exploração dos dados, identifiquei que o dataset é sintético (gerado por algoritmo), o que muda completamente a abordagem. Em vez de forçar insights falsos em dados sem variância real, construí a metodologia completa, documentei o que faria com dados reais, e entreguei um dashboard interativo pronto para receber dados de produção. Transparência sobre limitações é tão importante quanto a análise em si.

## Solução

### Abordagem

Comecei pelo que qualquer analista deveria começar: olhar os dados antes de rodar qualquer modelo. Carreguei o CSV, verifiquei distribuições, calculei estatísticas básicas. Foi aí que percebi que algo não batia: views variando de 9.676 a 10.551 (num universo de 52K posts), correlações praticamente zero entre todas as variáveis numéricas, distribuições perfeitamente uniformes entre plataformas.

Ao invés de ignorar isso e entregar "insights" fabricados, decidi tratar de frente: documentar a natureza sintética dos dados, aplicar a metodologia completa como exercício de competência, e entregar o ferramental pronto para quando os dados reais chegarem.

Usei o Claude Code como copiloto durante todo o processo. Eu definia o que analisar, ele gerava o código, eu validava os resultados e direcionava os próximos passos.

### Resultados / Findings

**1. Dados sintéticos: a primeira descoberta**

O dataset foi gerado por algoritmo (provavelmente Faker + distribuições uniformes). Evidências:
- Views: média 10.100, std 100 (range de apenas 875 unidades)
- Engagement rate: varia de 17,88% a 22,23% (range de 4,35pp para 52K posts)
- Correlação entre views, likes, shares e comments: próxima de zero
- Distribuição por plataforma: exatamente ~20% cada
- Nomes de sponsors: padrão Faker ("Johnson LLC", "Smith PLC")
- Descrições e comentários: lorem ipsum em inglês

**2. Análise de Performance (mesmo com dados sintéticos)**

Apliquei a metodologia completa como demonstração de competência:

| Cruzamento | Melhor | Pior | Delta |
|-----------|--------|------|-------|
| Plataforma | RedNote (19.91%) | Instagram (19.90%) | 0.01pp |
| Tipo | Text (19.92%) | Video (19.90%) | 0.02pp |
| Categoria | Lifestyle (19.91%) | Tech (19.90%) | 0.01pp |
| Orgânico vs Patrocinado | Orgânico (19.91%) | Patrocinado (19.90%) | 0.01pp |

Os deltas são estatisticamente insignificantes, o que confirma dados aleatórios.

**3. O que eu faria com dados reais**

Com dados de produção da empresa, essa mesma metodologia revelaria:
- Quais combinações de plataforma + tipo + categoria realmente performam
- Se micro-criadores (10-50K seguidores) entregam melhor ROI que mega-criadores
- Padrões temporais reais (dias, horários, sazonalidade)
- Se patrocínio vale o investimento controlando por variáveis confusoras
- Quais hashtags correlacionam com engajamento acima da média

**4. Análise de 11 dimensões realizadas**

Mesmo com a limitação dos dados, executei análises em:
1. Plataforma x Tipo de conteúdo
2. Plataforma x Categoria
3. Tamanho do criador (5 tiers)
4. Orgânico vs Patrocinado (controlado por tier e plataforma)
5. Categoria de patrocinador
6. Perfil demográfico (idade, gênero, localização)
7. Tipo e local de disclosure
8. Performance de hashtags
9. Tamanho do conteúdo
10. Análise temporal (dia da semana, evolução mensal)
11. Combinações triplas (plataforma + tipo + categoria)

### Recomendações

**Para o Head de Marketing, com transparência:**

1. **Prioridade 1: Implementar coleta de dados estruturada.** O dataset atual não permite decisões confiáveis. Antes de definir estratégia, a empresa precisa de dados reais com tracking adequado.

2. **Prioridade 2: Usar o dashboard entregue como ferramenta de monitoramento.** A estrutura está pronta. Basta conectar dados reais e o time de social media tem visibilidade diária.

3. **Prioridade 3: Rodar a mesma análise com dados reais.** O código está pronto, documentado, e funciona. Quando os dados chegarem, os insights saem em minutos.

4. **Prioridade 4: Testar hipóteses com A/B testing.** Mesmo com boa análise de dados históricos, a forma mais confiável de saber o que funciona é testar. Sugestão: testar orgânico vs patrocinado com criadores do mesmo tier, na mesma plataforma, com mesmo tipo de conteúdo.

**Quick wins (implementáveis esta semana):**
- Conectar dados reais ao dashboard
- Definir KPIs por plataforma (não usar engagement rate isolado)
- Criar tag system para categorizar conteúdo de forma consistente

### Limitações

- Dataset sintético: insights numéricos não são confiáveis para decisões reais
- Sem dados de custo: não foi possível calcular ROI real de patrocínios
- Sem dados de alcance (reach): engagement rate sem contexto de reach pode enganar
- Plataformas Bilibili e RedNote podem não ser relevantes para o mercado-alvo
- Análise temporal limitada pela uniformidade artificial dos dados

## O Algo a Mais

### Dashboard Interativo (Streamlit)

Construí um dashboard completo com:
- Filtros por plataforma, tipo, categoria, patrocínio e período
- KPIs em tempo real
- 5 abas: Visão Geral, Orgânico vs Patrocinado, Audiência, Creators, Recomendador
- Heatmaps de performance cruzada
- Recomendador de conteúdo baseado em perfil similar
- Nota de transparência sobre natureza dos dados

**Para rodar:**
```bash
# 1. Instalar dependências
pip install streamlit plotly pandas seaborn matplotlib

# 2. Baixar o dataset do Kaggle e colocar em solution/dataset/
# Link: https://www.kaggle.com/datasets/omenkj/social-media-sponsorship-and-engagement-dataset

# 3. Rodar o dashboard
cd submissions/wendel-castro/solution
streamlit run dashboard.py
```

### Análise Exploratória Completa (Python)

Script completo que gera 7 gráficos e análise em 11 dimensões:
```bash
python analise_completa.py
```

---

## Process Log — Como usei IA

O process log completo está em [`process-log/process-log.md`](process-log/process-log.md), com:

- **7 fases detalhadas** do workflow, separando o que eu direcionei vs. o que a IA executou
- **9 screenshots** da interação com o Claude Code (CLI), documentando desde a exploração inicial até o redirecionamento das recomendações
- **3 erros documentados** da IA e como corrigi cada um
- **6 contribuições exclusivamente humanas** que a IA sozinha não faria

O momento mais relevante: a IA processou 52K linhas sem questionar e gerou recomendações baseadas em deltas de 0.01pp. Fui eu que identifiquei os dados sintéticos, descartei os insights falsos, e redirecionei para recomendações de processo. As evidências visuais desse momento estão nas screenshots 4-6.

---

*Submissão enviada em: 16/03/2026 | Atualizada em: 20/03/2026*
