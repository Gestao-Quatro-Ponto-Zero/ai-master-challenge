# Process Log — Lead Scorer · Lucas de Paula

Evidência do processo de uso de IA na construção da solução.
**Ferramentas usadas:** Claude Code (Anthropic) · Claude agente PM personalizado · Gemini 2.0 Flash (Google)

---

## Fase 1 — Leitura humana antes de qualquer prompt

**Por que não joguei o desafio direto na IA:** tenho um agente de Product Manager customizado no Claude que uso nos meus produtos. Se eu jogasse o challenge direto nele, ele poderia trazer uma solução genérica ou enviesar minha leitura dos dados antes de eu ter feito a minha própria análise.

**O que fiz primeiro:**
- Li o README do desafio inteiro sozinho
- Baixei os 4 CSVs e abri em planilha — analisei campo a campo
- Identifiquei os dados mais relevantes: `deal_stage`, `days_in_stage` (calculado), `close_value`, `account_revenue`, `product_price`, histórico Won/Lost por agente
- Conclusão própria antes de qualquer prompt: o maior problema do pipeline é a falta de visibilidade sobre zumbis e a ausência de um critério objetivo de priorização

Tenho experiência com ferramentas de pré-vendas (tenho um SaaS voltado para essa área), então sabia exatamente qual dor a Head de RevOps estava descrevendo.

**Insights que só surgiram porque eu olhei os dados antes:**
- 71% dos deals em Engaging são zumbis +90d — a IA não saberia calibrar isso sem ver a distribuição real
- GTK 500 custa 486× mais que MG Special — esse dado justificou dar peso 25 ao componente Produto
- Win rate real varia de ~20% a ~70% no mesmo time — ignorado no CRM, fundamental para o score

---

## Fase 2 — Decomposição do problema com agente PM

Após entender os dados, usei meu agente PM para estruturar o produto — não para gerar código, mas para pensar em:
- Qual seria o usuário-alvo real (vendedor, manager ou RevOps)?
- Quais features resolveriam o problema vs. seriam nice-to-have?
- Qual seria a jornada de uso (segunda de manhã, abre o app, o que precisa ver?)

**Decisões que tomei — não a IA:**
- Foco no gestor/manager, não no vendedor individual (ele precisa de visão de portfólio)
- Score com explicação por componente — "por que esse deal tem 83?" é mais útil que só o número
- Interface web funcional, não notebook ou script
- Slack ao invés de email — gerentes usam Slack, não configuram SMTP
- Gemini ao invés de GPT ou Claude para o AI Coach — custo/performance para análise de deal individual
- Removi a feature de "visão do vendedor" (separada) por ser complexa e fora do foco do teste

---

## Fase 3 — Construção com Claude Code

Todo o desenvolvimento foi feito com **Claude Code** (CLI), com eu direcionando cada etapa.

### Como usei a IA estrategicamente:

**O que eu pedia:**
- Implementar features específicas já com a lógica definida por mim
- Sugerir padrões de código (ex: estrutura de componentes Next.js)
- Debugar erros de TypeScript e de build

**O que eu não deixava para a IA decidir:**
- Os pesos do scoring (eu calibrei com base nos dados reais)
- Quais features entravam ou saíam (cada decisão foi minha)
- O design de UX (eu direcionava o layout, cores, hierarquia)

### Onde a IA errou — e como corrigi:

| Erro | O que aconteceu | Como resolvi |
|---|---|---|
| `scoreDeals()` com 1 argumento | IA chamou a função sem o parâmetro `winRates` obrigatório | Identifiquei o erro de TypeScript e pedi para importar `calcAgentWinRates` + `loadPipeline` |
| Hydration mismatch | `HowToUsePanel` usava `localStorage` diretamente no `useState` (roda no SSR do server) | Corrigi inicializando como `true` e ajustando em `useEffect` |
| URL errada no Vercel | Estava testando na URL com hash de deploy antigo (imutável) | Identifiquei o padrão da URL e dirigi o teste para a URL de produção |
| Email com SMTP | Primeira versão usava nodemailer — complexo demais para o gestor configurar | Decidi trocar por Slack webhook (mais simples, mais adotado) |
| `Em risco` incluía zumbis | Lógica `days > 30` capturava deals +90d que já tinham card próprio | Corrigi para `days > 30 && days <= 90` — grupos mutuamente exclusivos |
| KPI "Alta prioridade" com overlap | Score ≥70 é cross-cutting e se sobrepunha aos grupos de stage — total não fechava | Substituí por "Saudável (≤30d)" — funil fecha matematicamente |
| Gemini model name | IA usou nome incorreto de modelo na API | Corrigido para `gemini-2.0-flash`; expus o erro real no response para debug |

### Onde gastamos mais tempo:

1. **Deploy no Vercel** — variáveis de ambiente não sobem com o `.gitignore`; precisei configurar manualmente no painel (SUPABASE URL, anon key, service role, ADMIN_TOKEN, VIEWER_TOKEN, GEMINI_API_KEY) e fazer redeploy. Também tive confusão com a URL de deploy imutável vs. URL de produção.

2. **KPI funil fechado** — o card "Alta prioridade" era cross-cutting (overlap com outros grupos), o que confundia o gestor; substituí por "Saudável (≤30d)" para que os 4 grupos somassem exatamente o total.

3. **Hydration mismatch no Next.js** — SSR rodava `localStorage` no servidor, onde `window` é undefined. Erros de hidratação React (#418, #423, #425) apareceram em produção mas não em desenvolvimento. Corrigi o padrão de inicialização.

### Onde gastamos menos tempo:

- **Scoring engine** — a lógica já estava clara na minha cabeça pela análise dos dados; foi só implementar
- **Componentes visuais** — Claude Code é muito bom em Tailwind/React
- **Integração Gemini** — a API é simples e direta; o prompt estruturado retornou JSON limpo na primeira tentativa

---

## Fase 4 — Iterações de produto

Várias features foram adicionadas ou removidas durante o desenvolvimento com base no meu julgamento:

**Adicionadas (decisão minha):**
- KPI cards com funil fechado (Saudável + Em risco + Prospecting + Zumbis = total)
- ScoreBreakdown modal com explicação componente a componente
- Coach de IA com Gemini — analisar deal individual com contexto real do pipeline
- Action tags por deal com urgency note dinâmica
- WelcomeModal com guia de boas-vindas (para onboarding em vídeo)
- Responsividade mobile (o manager vai acessar pelo celular)
- Anotações por deal (contexto local do vendedor)
- Integração Slack com webhook salvo no Supabase
- Filtros por vendedor, manager e região

**Removidas (decisão minha):**
- `nodemailer` / SMTP — complexidade desnecessária para o avaliador, substituído por Slack
- "Visão do vendedor" separada — escopo grande, avaliador quer visão de gestão
- Feature de conta como filtro extra — já está no pipeline, redundante

---

## Fase 5 — O que eu adicionei que a IA sozinha não faria

1. **A lógica dos pesos** — calibrei A=30, B=25, C=25, D=20 com base na leitura dos dados reais, não em heurísticas genéricas. Um LLM sozinho chutaria pesos sem olhar a distribuição dos produtos (GTK 500 custa 486× MG Special).

2. **A decisão de usar Slack** — entendo que gestores de vendas B2B usam Slack como canal primário. A IA sugeriu email; eu corrigi.

3. **O KPI "Saudável (≤30d)"** — a IA criou "Alta prioridade (score ≥70)" que se sobrepunha aos outros grupos. Eu identifiquei o problema de comunicação para o gestor e propus o grupo que fechava o funil matematicamente.

4. **O foco no gestor** — o challenge diz "vendedor", mas com 35 vendedores e 2.092 deals ativos, a ferramenta mais útil é para quem gerencia o portfólio inteiro.

5. **O AI Coach com contexto de pipeline** — não pedi só para a IA analisar o deal; mandei os benchmarks do pipeline junto (ciclo médio 52d, threshold de score ≥70) para que a análise retornasse orientação relativa ao contexto real, não genérica.

6. **As recomendações de integração de canais** — integrar WhatsApp, e-mail e tráfego pago para recepção centralizada e distribuição automática de leads pelo pipeline. Isso vai além do scoring — é uma visão de plataforma de operação comercial que veio da minha experiência com o produto de pré-vendas que desenvolvo.

---

## Ferramentas e iterações

| Ferramenta | Uso |
|---|---|
| **Claude Code** | Desenvolvimento principal — todo o código da aplicação |
| **Claude (agente PM)** | Fase de produto — estruturar visão, features, prioridades |
| **Gemini 2.0 Flash** | Feature de IA Coach embarcada no produto |
| **Supabase** | Banco de dados (pipeline + configurações Slack) |
| **Vercel** | Deploy e variáveis de ambiente |

**Número de iterações relevantes:** ~30 sessões de edição de código, com múltiplos ciclos de "implementa → testa → ajusta → decide".

**Git history como evidência adicional:** todos os commits estão no repositório com mensagens descritivas mostrando a evolução — de MVP básico até Coach de IA e responsividade mobile.

**Repositório:** https://github.com/oetnegro/lead-scorer-g4
