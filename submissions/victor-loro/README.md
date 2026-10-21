# Submissão — Victor Loro — Challenge ai-master-challenge

## Sobre mim

- **Nome:Victor
- **LinkedIn:https://www.linkedin.com/in/victor-loro-0a984033/
- **Challenge escolhido:Estratégia Social Media

---

## Executive Summary

Analisei um dataset sintético de 52.214 posts de redes sociais e construí um dashboard interativo (HTML) e um Excel de apoio para orientar decisões de conteúdo e influenciadores. Os dados são altamente homogêneos (engagement rate ~19,9%), então a vantagem está em diferenças relativas e volume nos segmentos certos — não em “truques” de engajamento. A principal recomendação é priorizar RedNote + Lifestyle, TikTok + Beauty e Bilibili + Tech, misturar mid/micro com macro na pirâmide de influência e usar um score de creator (ER × volume) em vez de só o maior ER isolado

---

## Solução

Dashboard HTML avançado — upload de CSV no navegador; recalcula KPIs, preditivo de engagement, hashtags (top vs bottom 25%), clusters (plataforma × categoria × idade), pirâmide de influência (nano → mega), horários/dias, recomendações, o que fazer / não fazer, 5 melhores combinações, filtro de período, score de creators e módulo financeiro (CPE, CPA/CPL, ROAS, CPV/VTR, split por plataforma e criativo). Funciona com colunas faltando

### Abordagem

Exploração — confirmei homogeneidade do dataset (ER quase constante), segmentos por plataforma/categoria/idade, patrocinado vs orgânico e ausência de custo/cliques/VTR no CSV.
Priorização — primeiro um Excel estático; depois HTML interativo com upload; depois preditivo, hashtags, clusters, pirâmide, horários, do/don’t e financeiro com inputs do usuário.
Critério de creators — ao ver andrew69 com ER ~21% e só 3 posts, ajustei o ranking para score = ER × log10(posts+1) e mínimo configurável (padrão 3), para não crowoar outliers de amostra pequena.


### Resultados / Findings

Performance quase idêntica entre orgânico e patrocinado; ROI depende do custo de mídia negociado.
Plataformas / categorias com leve vantagem relativa: RedNote + Lifestyle; TikTok + Beauty; Bilibili + Tech; público 50+ com ER alto e volume baixo (oportunidade).
Pirâmide: ER praticamente igual entre nano, micro, mid e macro; engajamento por follower favorece nano/micro. Mix sugerido em eficiência: ~60% mid/micro + ~40% macro.
Creators: ranking por score (não só ER). Ex.: andrew69 é o maior ER com ≥3 posts, mas some se o mínimo for 5.
Hashtags: sinal fraco no dataset; regra prática ~2 hashtags.
Horários: dependem de post_date; o dashboard extrai hora e dia e ranqueia automaticamente.
Financeiro: projeção de CPE (via ER dos dados), CPA/CPL, ROAS, CPV e splits — com CPM, CTR, conversão e VTRs informados pelo usuário.



### Recomendações

Focar budget e creators em RedNote Lifestyle, TikTok Beauty e Bilibili Tech; públicos 19–25, 26–35 e 50+.Usar score de creator (ER × volume) e mínimo de posts configurável para negociar séries. Misturar mid/micro (eficiência) com macro (alcance); não pagar prêmio só por ser mega.


### Limitações

Dataset sintético e homogêneo: diferenças de ER são pequenas; generalizar para dados reais exige validação.
CSV sem custo, impressões pagas, cliques, CTR real ou VTR — o financeiro é projeção com inputs do usuário.
Modelo preditivo é de efeitos relativos (deltas vs média), não ML treinado (boosting etc.)
Não implementei bot agendado da xAI para e-mail diário (não disponível como produto final para o usuário).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
|  Grok      | Análise do CSV, construção do HTML, critério de creators, módulo financeiro |


### Workflow

_Descreva passo a passo como você trabalhou. Onde a IA entrou em cada etapa?_

1.Análise dos dados e adequação a todos os detalhes citados e pedidos
2.Iterei o HTML: preditivo, hashtags, clusters, recomendações, do/don’t, pirâmide, horários, financeiro, filtro de período e score de creators
3.Questionei o ranking de creators (andrew69); validei no CSV (3 posts) e ajustei critério + texto de critério no dashboard.


### Onde a IA errou e como corrigi

Critério inicial de mínimo 5 posts escondia o maior ER (andrew69). Passei a exigir explicação escrita, conferi no CSV e mudei para mínimo 3 + score ER × log(volume).
Versões antigas do HTML tinham recomendações estáticas ou incompletas (sem do/don’t, sem top 5 combinações, VTR apertado). Pedi revisões explícitas até ficar utilizável pelo time.


### O que eu adicionei que a IA sozinha não faria

Exigir critério transparente de creators e validar um caso concreto no dado bruto.
Pedir visão de gerente de marketing (pirâmide, CPE/ROAS, do/don’t acionáveis) e criação de html operacional para time de marketing.
Definir o que o dashboard precisa fazer sem todas as colunas e com dados novos no futuro, para virar rotina semanal e não só um one-shot.

---

## Evidências

https://x.com/i/grok/share/98d88cf0414548cdb06950f25d1db2e2
https://grok.com/share/c2hhcmQtNQ_30ad5822-67a3-40ee-ae65-749b83cd75d7

---

_Submissão enviada em: 21/10/2026_
