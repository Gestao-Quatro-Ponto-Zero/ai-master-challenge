# Submissao — Vinicius Landare — Challenge 004

## Sobre mim

- **Nome:** Vinicius Landare
- **LinkedIn:** [linkedin.com/in/vinicius-landare](https://linkedin.com/in/vinicius-landare)
- **Challenge escolhido:** Challenge 004 — Estrategia Social Media

---

## Executive Summary

Analisei 52.214 publicacoes de 5 plataformas sociais (Instagram, TikTok, YouTube, Bilibili, RedNote) usando metodologia Hypothesis-Driven Analysis para responder as 4 entregas obrigatorias do Head de Marketing. Construi um dashboard interativo em Next.js que transforma dados brutos em acoes concretas: quais combinacoes de plataforma/formato/audiencia funcionam, quando postar, como investir em patrocinio, e o que parar de fazer imediatamente. A principal recomendacao: **priorizar carrossel e texto para jovens adultos (19-25) em RedNote/Bilibili, usando micro e nano-influenciadores**.

---

## Solucao

Dashboard interativo protegido por senha que responde diretamente as 4 entregas obrigatorias do desafio.

**Stack:** Next.js 16 + TypeScript + Tailwind CSS v4 + shadcn/ui + Recharts

**Pre-requisitos:** Node.js 18+ e npm instalados.

**Como rodar o dashboard:**

```bash
# 1. Entrar na pasta do projeto
cd social-metrics

# 2. Instalar dependencias
npm install

# 3. Iniciar o servidor de desenvolvimento
npm run dev

# 4. Abrir no navegador
# http://localhost:3456

# 5. Digitar a senha de acesso
# Senha: g4social2024
```

**Senha de acesso ao dashboard:** `g4social2024`

**6 abas do dashboard:**

| Aba | Entrega do desafio | O que mostra |
|-----|-------------------|--------------|
| Desempenho | Engagement drivers + O que nao funciona | Ranking de plataformas, formatos, top 10 melhores e piores combinacoes |
| Patrocinio | Sponsorship effectiveness | Organico vs patrocinado por plataforma e tier de influenciador, ROI |
| Publico-alvo | Audience profile engagement | 5 perfis de audiencia (Gen Z Jovem a Boomers) com estrategia personalizada |
| Mercados | Audience profile (por localizacao) | Brasil vs 7 mercados globais com detalhamento |
| Quando Postar | Engagement drivers (temporal) | Analise temporal por dia da semana e hora do dia |
| Plano de Acao | Strategic recommendations | 4 acoes rapidas, politica de patrocinio, o que parar, plano por audiencia |

---

## Abordagem

### Metodologia: Hypothesis-Driven Analysis (Priming Analitico)

Escolhi esta metodologia apos comparar 4 alternativas:

| Metodologia | Por que descartei |
|-------------|-------------------|
| EDA Livre | Gera relatorio generico — exatamente o que o briefing pede para NAO fazer |
| Framework-First (RFM, AARRR) | Frameworks de compra nao se aplicam a dados de engajamento |
| CRISP-DM | Robusto demais para o escopo — gestor quer respostas, nao pipeline de ML |
| **Hypothesis-Driven** | **Escolhida** — parte das perguntas reais do gestor, cada analise responde uma pergunta de negocio |

### Sequencia de trabalho:

1. **Compreensao do desafio** — Li o briefing, CONTRIBUTING.md, submission-guide e submissoes anteriores antes de escrever qualquer codigo
2. **Setup da stack** — Next.js 16 + TypeScript + shadcn/ui como diferencial visual
3. **Reconhecimento dos dados** — 52.214 posts, 27 colunas, dados simulados com distribuicoes uniformes
4. **Formulacao de hipoteses** — Cada uma vinculada a uma pergunta real do Head de Marketing
5. **Analise com Python/pandas** — Scripts locais processando os 52K registros, gerando JSONs agregados
6. **Dashboard interativo** — 6 abas com visualizacoes, insights e recomendacoes acionaveis
7. **Revisao de compliance** — Auditei cada hipotese para garantir cobertura completa

---

## Resultados / Findings

### Patrocinio reduz engagement vs organico?

**Resposta: Nao — a diferenca e minima (0.009pp)**

- Organico: 19.905% | Patrocinado: 19.906%
- Nano-influenciadores no Bilibili e YouTube tem o melhor retorno de patrocinio (+0.17pp e +0.11pp)
- Mega-influenciadores no TikTok mostram queda quando patrocinados — manter organico

### Micro-creators performam melhor que mega-influencers?

**Resposta: Sim, marginalmente**

- Rankings por tier confirmam que nano e micro-creators entregam melhor taxa de engajamento
- A diferenca e pequena (dados simulados), mas a direcao e consistente

### Qual a combinacao ideal de plataforma x formato x idade?

**Resposta: Depende da audiencia**

- **19-25 (35% do volume):** RedNote + Carrossel + Lifestyle = 20.04%
- **13-18 (15%):** Instagram + Carrossel + Tech = 20.04%
- **26-35 (30%):** RedNote + Texto + Tech = 20.00%
- **36-50 (15%):** RedNote + Carrossel + Tech = 20.07%
- **50+ (5%):** Instagram + Imagem + Beleza = 20.09%
- Diferenca total entre melhor e pior combinacao: ~1.25pp (dados simulados)

### A audiencia brasileira se comporta diferente dos outros mercados?

**Resposta: Nao significativamente**

- Brasil: 2o lugar entre 8 mercados (19.912%), atras apenas do UK (19.915%)
- Diferenca entre o melhor (UK) e pior (India): apenas 0.02pp
- Nao e necessaria estrategia localizada — comportamento e similar entre mercados

### Existem conteudos com engagement zero ou padroes de baixa performance?

**Resposta: Nao ha engagement zero, mas existem combinacoes consistentemente piores**

- Piores combinacoes identificadas nas "10 piores" do ranking
- Recomendacao de corte: carrossel de estilo de vida para 36-50 no TikTok (19.74%)

---

## Recomendacoes

### Implementar esta semana:
1. Priorizar carrossel e texto para jovens adultos (19-25) em RedNote e Bilibili
2. Publicar nos horarios de pico: 7h, 11h, 18h e 21h
3. Usar exatamente 2 hashtags por publicacao
4. Concentrar conteudo de valor nas sextas e domingos

### Politica de patrocinio:
- **Investir:** Nano e micro-influenciadores (ate 50mil seg.) no Bilibili, YouTube e Instagram
- **Nao investir:** Mega-influenciadores no TikTok e YouTube — manter organico
- **Regra:** Manter conteudo organico para mega-influenciadores

### Parar de fazer:
- Carrossel de estilo de vida para 36-50 no TikTok
- Moda no Instagram com mega-influenciadores
- Publicacoes nos horarios 15h-16h e 22h-23h

---

## Limitacoes

1. **Dados simulados:** O dataset tem distribuicoes muito uniformes (~1.25pp de variacao total). Em dados reais, as diferencas seriam 5-20pp. Os rankings relativos e direcoes de tendencia sao validos, mas os valores absolutos nao refletem cenarios reais.

2. **Conteudo dos posts:** As colunas `content_description` e `comments_text` contem texto lorem ipsum simulado, impossibilitando analise de sentimento ou tematica do conteudo.

3. **Temporalidade:** Sem sazonalidade real nos dados — padroes temporais (dia/hora) podem nao refletir comportamento genuino de audiencia.

4. **Amostragem por mercado:** ~6.500 posts por mercado e suficiente para medias, mas insuficiente para analises granulares por mercado + plataforma + formato.

5. **Metricas de conversao:** O dataset tem apenas metricas de engajamento (likes, shares, comments). Nao ha dados de conversao, vendas ou ROI real.

---

## Process Log — Como usei IA

> Este bloco documenta o uso estrategico de IA ao longo de toda a construcao da solucao.

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| Claude Code (Claude Opus 4.6) | Arquitetura do sistema, analise de dados, geracao de scripts Python, construcao do dashboard Next.js, revisao de codigo e fundamentacao metodologica |
| Python + pandas | Processamento e analise dos 52K posts — clustering, testes de hipoteses, geracao de dados agregados |
| Next.js 16 + shadcn/ui + Recharts | Dashboard interativo como diferencial da entrega |
| Git + GitHub | Versionamento e submissao via Pull Request |

### Meu processo de pensamento (antes de qualquer ferramenta)

1. **Anotacoes manuais** — Fiz anotacoes com os elementos principais: o que o gestor pediu, quais dados existem, formato de entrega. Clareza antes de tocar em qualquer ferramenta.
2. **Decisao pelo frontend** — A equipe de social media precisa visualizar dados, nao ler planilhas. Essa decisao veio antes da IA.
3. **Contextualizacao da missao** — Alimentei o contexto da IA com briefing completo, regras e exemplos antes de qualquer geracao. Isso evitou que a IA criasse codigo sem entender o escopo.
4. **Fundamentos identificados no briefing:** O gestor quer respostas concretas sobre engajamento real e ROI de patrocinio. O dataset de 52K posts limita a janela de contexto — preciso de processamento local. Lembrei de Data Priming como metodologia de cruzamento.
5. **Interacao dirigida** — Cada hipotese testada, cada visualizacao construida, cada remocao de conteudo irrelevante foi decisao minha. A IA executou, a direcao estrategica foi minha.

### Workflow

**Etapa 1 — Compreensao do desafio (antes de qualquer codigo)**

Usei o Claude Code para mapear completamente o repositorio do desafio: README, CONTRIBUTING.md, submission-guide.md, template de submissao e submissoes anteriores. Isso me deu visao completa do que era esperado.

**Etapa 2 — Setup da stack**

Claude Code criou o projeto Next.js 16 com TypeScript, Tailwind CSS v4, shadcn/ui e Prisma. Encontramos um bug do Turbopack com acentos no path — corrigi trocando para webpack.

**Etapa 3 — Reconhecimento dos dados**

Script Python de reconhecimento sobre os 52.214 posts. Questionei o Claude sobre processar 52K no contexto — ele admitiu que nao cabe. Definimos: pandas local processa, apenas resultados agregados entram no contexto para interpretacao.

**Etapa 4 — Fundamentacao metodologica**

Exigi que o Claude comparasse 4 metodologias antes de escolher. Isso me permite defender a escolha de Hypothesis-Driven Analysis para o gestor.

**Etapa 5 — Analise e construcao do dashboard**

Hipoteses testadas, 30+ JSONs gerados, dashboard com 6 abas interativas. Iteramos sobre design (paleta G4, SVG inline, sem emojis), UX (fonte Inter, dados explicativos) e compliance (analise de mercados adicionada apos auditoria, secao de disclosure removida por nao ser pergunta do gestor).

### Onde a IA errou e como corrigi

| O que aconteceu | Como corrigi |
|-----------------|-------------|
| Claude montou toda a stack antes de eu ler o briefing — priorizou dashboard sobre analise | Redirecionei: analise de dados e o core, dashboard e diferencial |
| Turbopack crashava com acentos no path | Identifiquei o bug, troquei para webpack |
| Prisma v7 mudou a API — Claude gerou codigo do v6 | Iteramos ate encontrar a sintaxe correta |
| Claude sugeriu carregar todo o CSV no contexto | Questionei proativamente — definimos processamento local com pandas |
| Na primeira abordagem, Claude ia fazer EDA livre | Pedi fundamentacao metodologica antes de executar |
| Dashboard tinha emojis — visual amador | Exigi SVG inline, sem emojis, paleta G4 |
| Textos de patrocinio nos cards sem fundamentacao | Forcei adicionar os dados reais (organico vs patrocinado com diferenca em pp) |
| Analise de mercados (Brasil) faltava no dashboard | Fiz auditoria de compliance e identifiquei a lacuna |
| Claude criou secao de "disclosure type" que nao foi pedida pelo gestor | Questionei a relevancia, confirmei que nao era pergunta do briefing, e mandei remover |

### O que eu adicionei que a IA sozinha nao faria

1. **Redirecionamento estrategico:** A IA comecou construindo um SaaS. Eu li o briefing e entendi que o desafio avalia capacidade analitica, nao engenharia. Sem essa correcao, teriamos entregue um sistema bonito que nao responde nenhuma pergunta do gestor.

2. **Questionamento sobre janela de contexto:** Perguntei se 52K registros caberiam no contexto. Isso levou a arquitetura correta (pandas local -> JSONs agregados -> dashboard).

3. **Exigencia de fundamentacao metodologica:** Em vez de aceitar "vamos analisar", exigi comparacao de 4 metodologias com justificativa.

4. **Foco em acionaveis reais:** A cada insight generico, forcei a pergunta: "o que o Head de Marketing faz com isso segunda-feira?".

5. **Auditoria de compliance:** Identifiquei que a analise de mercados (Brasil) faltava e exigi implementacao. Tambem identifiquei que o Claude havia criado uma secao sobre "disclosure type" que nao era pergunta do gestor — mandei remover para manter foco no que foi pedido.

6. **Design profissional:** Exigi paleta G4, remocao de emojis, SVG inline, dados fundamentados nos cards, senha de acesso.

### Evidencias

- [x] Process log documentado em tempo real
- [x] Git history mostrando evolucao do codigo
- [x] Dashboard funcional com 6 abas cobrindo todas as hipoteses
- [x] Scripts de analise Python gerando 30+ JSONs de dados
- [x] Senha de acesso ao dashboard: `g4social2024`

---

**Submissao enviada em:** 2026-03-11
