# Challenge 004 — Estratégia Social Media

## Contexto

Você é o novo AI Master da área de **Marketing**. A empresa investe em conteúdo orgânico e patrocinado em Instagram, TikTok e YouTube. O time de social media posta diariamente mas não tem clareza sobre o que funciona e por quê.

O Head de Marketing te passou um dataset com 52.000 posts de múltiplas plataformas e disse:

> "Temos dados de tudo que postamos e patrocinamos, mas ninguém parou pra analisar direito. Quero entender: o que gera engajamento de verdade? Vale a pena patrocinar influenciadores? Qual tipo de conteúdo deveria ser nossa prioridade? Me dá uma estratégia baseada em dados, não em opinião."

## Os dados

| Arquivo | Descrição | Registros |
|---------|-----------|-----------|
| `social_media_engagement.csv` | Posts com métricas de engajamento, dados de audiência, e informações de patrocínio | ~52.000 |

Colunas principais:
- **Plataforma:** YouTube, TikTok, Instagram (+ outras)
- **Conteúdo:** tipo (video, image, text, mixed), categoria, hashtags, duração
- **Métricas:** views, likes, shares, comments, engagement rate
- **Audiência:** distribuição por idade, gênero, localização
- **Patrocínio:** flag de sponsorship, nome do patrocinador, tipo de disclosure

**Fonte:** [Social Media Sponsorship & Engagement Dataset](https://www.kaggle.com/datasets/omenkj/social-media-sponsorship-and-engagement-dataset) (Kaggle, licença MIT)

Baixe o dataset diretamente do Kaggle.

## O que entregar

### 1. Análise de performance (obrigatório)

Responda com dados:
- **O que gera engajamento?** Por plataforma, tipo de conteúdo, categoria. Vá além do óbvio.
- **Patrocínio funciona?** Compare orgânico vs. patrocinado. O ROI de influencer marketing se justifica?
- **Qual o perfil de audiência que mais engaja?** Existe diferença por plataforma?

### 2. Estratégia recomendada (obrigatório)

Com base na análise:
- **Onde concentrar esforço?** Qual plataforma, tipo de conteúdo, frequência.
- **Patrocinar ou não?** Em que condições. Com que tipo de influenciador.
- **O que parar de fazer?** Tão importante quanto o que começar.

### 3. Algo a mais (diferencial)

Nos surpreenda. Alguns caminhos possíveis:
- Um modelo que prevê engagement antes de postar
- Um gerador de recomendações de conteúdo baseado nos padrões encontrados
- Um dashboard interativo para o time de social media
- Análise de texto dos posts/hashtags que performam melhor
- Qualquer coisa que transforme dados em decisão

### 4. Process log (obrigatório)

Como você usou IA para chegar aqui. Veja o [Guia de Submissão](../../submission-guide.md).

## Dicas

- 52.000 posts é muito dado. Não tente analisar tudo de uma vez — segmente.
- "Vídeos performam melhor que imagens" é óbvio. "Vídeos de 30-60s na categoria X geram 3.2x mais shares que a média" é útil.
- Engagement rate isolado mente. Contextualize com reach, segmento e plataforma.
- Se recomendar "postar mais no TikTok", explique o que postar, para quem, e com que evidência.
- O Head de Marketing não é data scientist. Comunique de forma que ele entenda e aja.
