# Process Log — Como usei IA neste desafio

> Documento obrigatório que evidencia o uso estratégico de IA ao longo de toda a construção da solução do Challenge 004 — Estratégia Social Media.

---

## Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| Claude Code (Claude Opus 4.6) | Arquitetura do sistema, análise de dados, geração de scripts Python, construção do dashboard Next.js, revisão de código e fundamentação metodológica |
| Python + pandas | Processamento e análise dos 52K posts — clustering, testes de hipóteses, geração de dados agregados |
| Next.js 16 + shadcn/ui + Recharts | Dashboard interativo como diferencial da entrega |
| Git + GitHub | Versionamento e submissão via Pull Request |

---

## Workflow — Passo a passo de como trabalhei

### Etapa 1: Compreensão do desafio antes de qualquer código

Antes de tocar em qualquer ferramenta, usei o Claude Code para mapear completamente o repositório do desafio (`ai-master-challenge`). O agente explorou:

- O README principal do desafio
- O `CONTRIBUTING.md` com regras de submissão
- O `submission-guide.md` com critérios de avaliação
- O template de submissão em `templates/submission-template.md`
- O README específico do Challenge 004 (Estratégia Social Media)
- Submissões anteriores de outros candidatos para entender o padrão de qualidade esperado

**Decisão minha (não da IA):** Percebi que o desafio pede análise de dados com insights acionáveis, não apenas um sistema web. Isso redirecionou toda a abordagem — o dashboard seria o diferencial, não o core.

### Etapa 2: Setup inicial da stack (e correção de rota)

Pedi ao Claude Code para montar a stack tecnológica do projeto. Ele criou:

- Projeto Next.js 16 com TypeScript, Tailwind CSS v4, shadcn/ui
- Prisma ORM com schema para PostgreSQL
- Componentes de dashboard (Card, Table, Chart, Tabs, etc.)

**Problemas encontrados e corrigidos:**
1. **Turbopack + acentos no path:** O Turbopack (bundler padrão do Next.js 16) crashava por causa do acento em "Estratégia" no caminho da pasta. Erro: `byte index 32 is not a char boundary`. Solução: usar webpack via `next build --webpack`.
2. **Prisma v7 — API mudou:** O Claude gerou o import do PrismaClient no padrão do Prisma v6. No v7, é obrigatório usar um adapter (`@prisma/adapter-pg`). Corrigi isso iterando com o Claude até o build compilar limpo.

**Decisão minha:** Após ler o briefing completo do desafio, percebi que montamos a stack antes de entender o escopo real. Redirecionei: a análise de dados é o coração, o dashboard é o diferencial. Reorganizamos prioridades.

### Etapa 3: Download e reconhecimento dos dados

O dataset de 52.214 posts estava disponível no Kaggle (Social Media Sponsorship & Engagement Dataset).

**Discussão sobre janela de contexto:** Questionei o Claude sobre a capacidade de processar 52K registros. A resposta foi honesta — a janela de contexto **não comporta** carregar todos os dados. A estratégia adotada:
- Dados brutos ficam em disco (CSV)
- Scripts Python/pandas processam localmente (52K é trivial para pandas)
- Apenas resultados agregados entram no contexto do Claude para interpretação
- Dashboard consome JSONs estáticos gerados pelos scripts

**Decisão minha:** Mantive os dados brutos sempre disponíveis no sistema para que a equipe de social media possa gerar novos insights no futuro — não apenas os pré-processados.

### Etapa 4: Escolha e fundamentação da metodologia

Antes de sair analisando, pedi ao Claude para pesquisar a **metodologia de Priming Analítico** e comparar com alternativas. O agente pesquisou na web e trouxe:

- O framework Hypothesis-Driven Analysis (Kellogg School, IBM Garage)
- O modelo CRISP-DM
- Técnicas de clustering para segmentação de audiência
- Como gerar acionáveis de verdade a partir de dados demográficos (idade, gênero, localização)

**Comparação de 4 metodologias:**

| Metodologia | Veredito para este desafio |
|-------------|---------------------------|
| EDA Livre | Descartada — gera relatório genérico, exatamente o que o briefing pede para NÃO fazer |
| Hypothesis-Driven (Priming) | **Escolhida** — parte das perguntas do Head de Marketing, cada análise responde uma pergunta real |
| Framework-First (RFM, AARRR) | Descartada — frameworks de compra não se aplicam a dados de engajamento |
| CRISP-DM | Descartada — robusto demais para o escopo, gestor quer respostas, não um pipeline de ML |

**Por que Hypothesis-Driven:**
1. O briefing já lista as perguntas que precisam de resposta — não estamos explorando às cegas
2. Dados simulados com distribuições uniformes punem análise livre (gráficos "planos")
3. O teste do "So What?" garante que cada insight tem uma ação vinculada
4. Comunicação clara para executivo — cada hipótese vira uma recomendação

**Decisão minha:** Escolhi esta metodologia porque o desafio avalia capacidade de gerar acionáveis, não capacidade de fazer EDA bonita. A metodologia garante que tudo que entregamos responde a uma pergunta real de negócio.

### Etapa 5: Data Priming — Reconhecimento dos dados

Rodei um script de reconhecimento via Claude Code sobre os 52.214 posts. Descobertas:

**Estrutura:**
- 52.214 posts, 27 colunas
- 5 plataformas: Instagram, TikTok, YouTube, Bilibili, RedNote
- 4 tipos de conteúdo: video, image, mixed, text
- 3 categorias: beauty, lifestyle, tech
- 5 faixas etárias: 13-18, 19-25, 26-35, 36-50, 50+
- 8 localizações: USA, UK, Brazil, Germany, Russia, Japan, India, China
- 5.000 creators distintos (1K a 1M seguidores)
- Posts patrocinados vs orgânicos com 7 categorias de sponsor

**Alerta identificado — distribuições uniformes:**
- Views: média 10.100 ± 100 (variação de ~1%)
- Likes: média 1.510 ± 39
- Shares: média 300 ± 17
- Comments: média 200 ± 14

Isso indica dados simulados com baixa variância nos valores absolutos. **Implicação:** os insights precisam vir dos cruzamentos (plataforma × tipo × idade × patrocínio), não dos valores isolados.

**Dados faltantes:**
- `hashtags`: 8.743 nulos (16.7%)
- `comments_text`: 8.688 nulos (16.6%)
- Sem impacto na análise quantitativa principal

### Hipóteses formuladas para teste

Com base no briefing do gestor e no reconhecimento dos dados:

| ID | Hipótese | Pergunta de negócio que responde |
|----|----------|----------------------------------|
| H1 | Patrocínio explícito reduz engagement rate vs. orgânico | "Patrocínio funciona?" |
| H2 | Micro-creators (10K-50K) têm melhor engagement rate que mega-influencers (500K+) | "Qual perfil de creator investir?" |
| H3 | Existe combinação ideal de plataforma × tipo de conteúdo × faixa etária | "Onde concentrar esforço?" |
| H4 | O comportamento da audiência brasileira difere significativamente dos outros mercados | "Precisamos de estratégia localizada?" |
| H5 | Determinados tipos de conteúdo têm engagement zero ou próximo de zero sistematicamente | "O que parar de fazer?" |

---

## Onde a IA errou e como corrigi

| O que aconteceu | Como corrigi |
|-----------------|-------------|
| Claude montou toda a stack Next.js antes de eu ler o briefing completo — prematuramente priorizou o dashboard sobre a análise | Redirecionei após ler o briefing: análise de dados é o core, dashboard é diferencial |
| Turbopack crashava com acentos no path da pasta | Identifiquei o bug, trocamos para webpack no build |
| Prisma v7 mudou a API — Claude gerou código do v6 | Iteramos até encontrar a sintaxe correta com adapter |
| Claude sugeriu carregar todo o CSV no contexto para análise | Questionei proativamente — definimos a arquitetura de processamento local com pandas |
| Na primeira abordagem, Claude ia fazer EDA livre | Pedi fundamentação metodológica antes de executar — levou à escolha do Hypothesis-Driven |
| Claude criou seção de "disclosure type" (explícito vs implícito) que não foi pedida pelo gestor | Questionei a relevância durante a revisão — confirmei que não era pergunta do briefing e mandei remover para manter foco no que foi pedido |

---

## O que eu adicionei que a IA sozinha não faria

1. **Redirecionamento estratégico:** A IA começou construindo um SaaS. Eu li o briefing e entendi que o desafio avalia capacidade analítica com insights acionáveis, não engenharia de software. Sem essa correção, teríamos entregue um sistema bonito que não responde nenhuma pergunta do Head de Marketing.

2. **Preocupação com janela de contexto:** Questionei se 52K registros caberiam no contexto. Isso levou à arquitetura correta de processamento (pandas local → resultados agregados → contexto do Claude → interpretação).

3. **Exigência de fundamentação metodológica:** Em vez de aceitar "vamos usar priming", exigi que o Claude explicasse POR QUE essa metodologia e não outra, com comparação direta. Isso me permite defender a escolha para o gestor.

4. **Visão de reuso dos dados brutos:** A IA ia processar e descartar. Eu mantive os dados brutos disponíveis para que a equipe de social media possa gerar novos insights futuros — não só os que estamos entregando agora.

5. **Foco em acionáveis reais:** A cada momento em que o Claude trazia um insight genérico, eu forçava a pergunta: "o que o Head de Marketing faz com isso segunda-feira?". Isso moldou toda a abordagem.

6. **Documentação como processo, não como relatório:** Este process log está sendo escrito em tempo real, não retroativamente. Cada decisão está documentada no momento em que foi tomada.

7. **Remoção de análise irrelevante:** O Claude criou uma seção inteira sobre "disclosure type" (divulgação explícita vs implícita de patrocínio) com dados, gráficos e recomendações. Questionei: "Isso é uma questão do gestor? Não vi essa pergunta." Confirmei no briefing que não era — mandei remover. A IA tende a gerar mais conteúdo do que o necessário para parecer completa. O valor está em saber o que cortar.

---

### Etapa 6: Construção do dashboard interativo

Com os 30+ JSONs gerados pela análise, construí o dashboard em Next.js 16:

- **6 abas** cobrindo todas as 6 hipóteses do desafio
- **Design G4:** paleta navy (#0F1B2D) + coral (#E8734A), logo G4, SVG inline (sem emojis)
- **Fonte Inter** para melhor leitura + JetBrains Mono para dados numéricos
- **Autenticação:** tela de login com senha usando sessionStorage
- **Responsivo:** funciona em desktop e mobile

**Iterações de design dirigidas por mim (não pela IA):**
- Removi todos os emojis e substituí por SVG inline — visual mais profissional
- Exigi que os cards de patrocínio mostrassem dados reais (orgânico vs patrocinado com diferença em pp)
- Auditei as 6 hipóteses e identifiquei que H4 (Brasil) e H5 (Divulgação) estavam faltando — criei a aba "Mercados"
- Troquei fonte Geist por Inter após feedback de legibilidade

### Etapa 7: Revisão de compliance e README

Auditei cada hipótese do briefing contra o dashboard:

| Hipótese | Status | Onde está |
|----------|--------|-----------|
| Engagement drivers (plataforma, tipo, categoria, creator) | Coberta | Aba "Desempenho" + "Quando Postar" |
| Sponsorship effectiveness (orgânico vs patrocinado) | Coberta | Aba "Patrocínio" |
| Audience profile engagement (por faixa etária) | Coberta | Aba "Público-alvo" |
| O que não funciona (padrões de baixa performance) | Coberta | Aba "Desempenho" (bottom 10) |
| Brasil vs outros mercados | Coberta | Aba "Mercados" |
| Recomendações estratégicas priorizadas | Coberta | Aba "Plano de Ação" |

---

## Evidências

- [x] Process log documentado em tempo real
- [x] Git history mostrando evolução do código com AI-assisted development
- [x] Dashboard funcional com 6 abas cobrindo todas as hipóteses
- [x] Scripts de análise Python gerando 30+ JSONs de dados
- [x] README no formato de submissão com resultados e recomendações
- [x] Screenshots das conversas e do dashboard em `assets/captura-de-tela/`

---

*Documento atualizado em tempo real durante a execução do desafio.*
*Última atualização: 2026-03-11*
