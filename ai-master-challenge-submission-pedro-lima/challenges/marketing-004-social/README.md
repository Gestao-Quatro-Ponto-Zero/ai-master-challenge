# Challenge 004 — Estratégia Social Media

**Área:** Marketing
**Tipo:** Análise + Estratégia
**Time budget:** 4-6 horas

---

## Contexto

Você é o novo AI Master da área de **Marketing**. A empresa investe em conteúdo orgânico e patrocinado em Instagram, TikTok e YouTube, trabalhando com criadores e influenciadores de diferentes tamanhos e categorias.

O time de social media posta diariamente em múltiplas plataformas, faz parcerias com patrocinadores, mas não tem clareza sobre o que realmente funciona — e o que é desperdício.

O Head de Marketing te passou um dataset com 52.000 posts e disse:

> *"Temos dados de tudo que postamos e patrocinamos nos últimos anos, mas ninguém parou pra analisar direito. Quero entender três coisas: o que gera engajamento de verdade, se vale a pena patrocinar influenciadores, e qual deveria ser nossa estratégia de conteúdo. Me dá uma estratégia baseada em dados, não em opinião. E se puder me dar uma ferramenta pra acompanhar isso no dia a dia, melhor ainda."*

---

## Dados disponíveis

Um dataset rico com ~52.000 posts cross-platform:

**Dataset:** [Social Media Sponsorship & Engagement Dataset](https://www.kaggle.com/datasets/omenkj/social-media-sponsorship-and-engagement-dataset) (licença MIT)

| Categoria | Colunas |
|-----------|---------|
| **Plataforma** | Platform (YouTube, TikTok, Instagram, Bilibili, RedNote) |
| **Conteúdo** | Content type (Video, Image, Text, Mixed), Category, Hashtags, Content length/duration |
| **Métricas** | Views, Likes, Shares, Comments, Engagement rate |
| **Criador** | Creator ID, Follower count |
| **Audiência** | Audience age distribution, Gender distribution, Location |
| **Patrocínio** | `is_sponsored` (flag), Sponsor name, Sponsor category, Disclosure type |
| **Temporal** | Post date, Language |

### O que torna esse dataset interessante

- **Orgânico vs. patrocinado**: flag `is_sponsored` permite comparar ROI de patrocínio diretamente
- **Cross-platform**: mesmo tipo de conteúdo performando diferente por plataforma
- **Audiência**: dados demográficos permitem análise por persona/segmento
- **Volume**: 52K posts é massa suficiente pra análise estatística robusta

---

## O que entregar

### 1. Análise de performance (obrigatório)

Responda com dados — não com achismo:

- **O que gera engajamento?** Por plataforma, tipo de conteúdo, categoria, tamanho de creator. Vá além do óbvio ("vídeos performam melhor que imagens" não é insight).
- **Patrocínio funciona?** Compare orgânico vs. patrocinado em engagement rate, alcance, custo implícito. Em que condições patrocinar vale a pena? Com que tipo de influenciador?
- **Qual o perfil de audiência que mais engaja?** Existe diferença por plataforma? Por tipo de conteúdo? Por categoria?
- **O que NÃO funciona?** Tão importante quanto saber o que funciona.

### 2. Estratégia recomendada (obrigatório)

Com base na análise, recomende:

- **Onde concentrar esforço?** Qual plataforma, tipo de conteúdo, frequência de postagem, faixa de creator.
- **Política de patrocínio.** Patrocinar ou não? Em que condições? Com que perfil de influenciador? Qual o threshold de seguidores/engagement que justifica investimento?
- **O que parar de fazer.** Identifique investimentos com baixo retorno baseado nos dados.
- **Quick wins.** O que pode ser implementado esta semana com base nos findings.

### 3. Algo a mais (diferencial)

Nos surpreenda. Caminhos possíveis:
- Modelo preditivo de engagement (input: características do post → output: engagement estimado)
- Dashboard interativo para o time de social media acompanhar performance
- Gerador de recomendações de conteúdo baseado em padrões dos top performers
- Análise de hashtags — quais combinações correlacionam com alto engagement?
- Segmentação de audiência com clustering
- Qualquer coisa que transforme dados em decisão recorrente

### 4. Process log (obrigatório)

Evidências de como você usou IA. Leia o [Guia de Submissão](../../submission-guide.md).

---

## Critérios de qualidade

- A análise vai além do superficial? (engajamento médio por plataforma é tabela 1, não a conclusão)
- Os insights são acionáveis? O Head de Marketing sabe o que fazer na segunda-feira?
- A comparação orgânico vs. patrocinado é justa? (controla por tamanho de creator, plataforma, categoria?)
- As recomendações são priorizadas? (não é uma lista de 20 ideias sem ordem)
- A comunicação é clara para um executivo não-técnico?

---

## Dicas

- 52.000 posts é muito dado. Segmente antes de analisar — por plataforma, por período, por categoria.
- "Vídeos performam melhor que imagens" é o que a IA vai dizer se você colar o brief. "Vídeos de 30-60s na categoria Tech, com creators de 10K-50K seguidores, geram 3.2x mais shares que a média da plataforma" é o que um AI Master entrega.
- Engagement rate isolado mente. Contextualize com reach, plataforma e tamanho do creator.
- Se recomendar "postar mais no TikTok", explique **o que** postar, **para quem**, **quando**, e com **que evidência** dos dados.
- O Head de Marketing não é data scientist. Se ele não entender seu output em 5 minutos, você perdeu.
- Cuidado com o viés de survivorship: posts com muito engagement são visíveis, mas quantos posts tiveram engagement zero?
