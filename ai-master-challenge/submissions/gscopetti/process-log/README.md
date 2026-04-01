## Sobre mim

- **Nome:** Guilherme Sangoi Copetti
- **LinkedIn:** https://www.linkedin.com/in/guilhermecopetti/
- **Challenge escolhido:** Challenge 003 — Lead Scorer

---

## Executive Summary

Desenvolvi um web app funcional de Lead Scoring que transforma os 4 CSVs do CRM em uma ferramenta prática de priorização comercial. O vendedor importa os dados, visualiza seus deals ordenados por prioridade, entende claramente o motivo de cada score e recebe um script de abordagem SPIN Selling pronto para usar.

O projeto passou por **duas versões arquiteturais**. A V1 foi construída no Claude (claude.ai), onde estruturei a arquitetura completa com 7 fatores de scoring, templates SPIN Selling e mapa de delegação para agentes. A V2 nasceu da análise exploratória profunda dos dados — também no Claude — que revelou insights como "deals perdidos morrem em 14 dias" e que 93% dos deals em Engaging estão estagnados. Com essas descobertas, reformulei a arquitetura para 4 pilares com penalizações, incorporando os padrões reais dos dados.

Em todas as etapas, o **AIOS Framework ([Synkra AIOS](https://github.com/SynkraAI/aiox-core))** foi utilizado como orquestrador central, com o **AI Master** coordenando e distribuindo diretrizes para os agentes especializados de desenvolvimento.

---

## Solução

### O que o app faz

O web app processa os quatro arquivos CSV do desafio e entrega:

- **Classificação automática** dos deals ativos em 4 tiers: Hot, Warm, Cool e Cold
- **Explicabilidade completa** — cada deal mostra os fatores que compõem seu score com barras visuais e texto explicativo
- **Script SPIN Selling** personalizado por lead, com dados reais da conta, histórico e produto
- **Dashboard interativo** com KPIs, gráficos de distribuição e tendências
- **Filtros por vendedor, manager, região e produto** — cada vendedor vê seus próprios deals

### Lógica de Scoring — Evolução V1 → V2

Na **V1**, estruturei a arquitetura no Claude (claude.ai) com **7 fatores de scoring** ponderados e geração de scripts SPIN Selling:

| Fator | Peso | O que mede |
| --- | --- | --- |
| Win Rate da Conta | 25% | Histórico de conversão do account |
| Valor do Produto | 20% | Preço do produto (escala logarítmica) |
| Estágio do Pipeline | 15% | Engaging (80pts) vs Prospecting (40pts) |
| Vendedor × Produto | 15% | Win rate do agente naquele produto específico |
| Tempo no Pipeline | 10% | Dias vs ciclo médio do produto |
| Tamanho da Conta | 10% | Revenue + employees normalizados por quartil |
| Mix de Produtos | 5% | Diversidade de séries já compradas |

Na **V2**, após uma análise exploratória profunda dos dados reais, reformulei para **4 pilares com penalizações**, incorporando os padrões descobertos:

```
score = (valor_pilar × 0.40)
      + (momentum_pilar × 0.25)
      + (fit_conta × 0.15)
      + (qualidade_rep × 0.20)
      − penalidades
```

| Pilar | Peso | Base nos dados |
| --- | --- | --- |
| **Valor do Deal** | 40% | log(close_value estimado) normalizado. Deals sem valor usam preço de lista como proxy |
| **Momentum** | 25% | Curva de win rate por tempo: 15-90 dias = score cheio; <8 dias ou >90 dias = penalização progressiva. Baseado na descoberta de que deals 15-30 dias têm 73% de win rate |
| **Fit da Conta** | 15% | Revenue bucket (Small/Mid/Large/Enterprise) × win rate histórica do setor |
| **Qualidade do Rep** | 20% | Win rate do agente normalizada entre mínimo (55%) e máximo (70.4%) observados |

**Penalizações automáticas:**

- Estagnado >90 dias: −25 pts
- Conta faltando: −15 pts
- Deal muito novo <8 dias: −10 pts
- Rep abaixo de 60% win rate: −10 pts

**Por que a evolução?** A V1 foi uma arquitetura sólida baseada em boas práticas de scoring. A V2 incorporou evidências empíricas dos dados — a descoberta de que o momentum (tempo no pipeline) tem um padrão contra-intuitivo levou a aumentar seu peso de 10% para 25% e criar um modelo de penalização progressiva baseado nas curvas reais de conversão.

### Setup — Como rodar

```bash
npm install
npm run dev
# Abrir http://localhost:5173
# Importar os 4 CSVs na tela de Upload
```

**Dependências:** Node 18+, browser moderno.

---

## Abordagem — Duas Versões, Uma Entrega

O projeto foi executado em duas fases arquiteturais, com o **AIOS Framework** coordenando todo o desenvolvimento em ambas:

```
V1 — ARQUITETURA ESTRUTURADA (Claude no claude.ai)
├── Análise dos CSVs e requisitos do desafio
├── Arquitetura com 7 fatores de scoring + SPIN Selling
├── Mapa de delegação para agentes
├── Geração do documento .MD de arquitetura
└── AIOS Master recebe o .MD e coordena agentes de construção

        ⬇ (iteração: análise profunda revela padrões nos dados)

V2 — ARQUITETURA ORIENTADA POR DADOS (Claude no claude.ai)
├── Análise exploratória profunda dos 4 CSVs
├── 7 descobertas que mudaram a abordagem
├── Reformulação para 4 pilares + penalizações
├── AIOS Master coordena refatoração dos agentes
└── Reformulação de design + documentação + entrega
```

### Cronograma Completo

```
──── V1: Arquitetura Estruturada ────
03/03  08:00 – 08:30    →  Entendimento do problema (Notepad)
       08:30 – 09:00    →  Arquitetura V1 no Claude (7 fatores + SPIN)
       09:00 – 09:10    →  Revisão + geração do .MD
       09:10 – 09:20    →  Setup Antigraft + instalação AIOS Framework
       09:20 – 09:50    →  AIOS Master coordena construção (agentes)
       09:50 – 10:00    →  Primeira versão funcional rodando
		   10:00 – 11:00    →  Reformulação de design (Comet + ref. HubSpot)
		   11:00 – 12:00    →  Finalização e submissão
       1300             →  Entrega 

──── V2: Reformulação por Dados ────
14/03     →  Análise exploratória profunda no Claude
             7 descobertas, reformulação para 4 pilares
          →  AIOS Master coordena refatoração do scoring
          →  Finalização + documentação
          →  Entrega
```

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
| --- | --- |
| **Claude (claude.ai)** | V1: Arquitetura completa com 7 fatores, templates SPIN, mapa de agentes. V2: Análise exploratória profunda, 7 descobertas nos dados, reformulação para 4 pilares com penalizações |
| **AIOS Framework (Synkra AIOS)** | Orquestração central em TODAS as etapas — o AI Master sempre coordenou e distribuiu diretrizes para os agentes de desenvolvimento |
| **Claude Code (terminal)** | Instalação do AIOS, setup do projeto, execução via agentes coordenados pelo AI Master |
| **Comet (plugin IA)** | Construção e adaptação do design system |
| **Notepad (local)** | Organização pessoal de cronograma e checklist |

### Stack Técnica

| Camada | Tecnologia |
| --- | --- |
| Framework | React 18 + TypeScript + Vite |
| Estilização | Tailwind CSS |
| Componentes | Shadcn/UI |
| Gráficos | Recharts |
| CSV Parsing | PapaParse |
| Estado | Context API + useReducer |
| Orquestração | **AIOS Framework (Synkra AIOS)** — `.aios-core/` — sistema de agentes, tasks, workflows, templates e regras |
| AI Master | **Claude Code** — modo AIOS Master Agent (`.claude/`) — coordenou todas as fases |
| IDE | Antigraft |

---

### Workflow — Timeline Detalhada

### V1 — Arquitetura Estruturada

| Hora | Fase | O que aconteceu | Papel da IA |
| --- | --- | --- | --- |
| 08:00 | Planejamento | Abri o Notepad e estruturei o problema: o que entregar, o que tenho, como submeter. Defini blocos de tempo. Listei que precisava de dashboard web + lead scoring + script SPIN Selling | Não aplicável (organização humana pura) |
| 08:10 | Leitura do desafio | Li o challenge 003 completo. Identifiquei que explainability e uso real eram os diferenciais mais valorizados | Não aplicável (interpretação humana) |
| 08:30 | Arquitetura V1 | Abri o Claude (claude.ai), enviei os 4 CSVs + link do desafio. Contextualizei que a solução deveria ser web app com dashboard, importação de CSVs, classificação de leads, mini-relatório e script SPIN Selling. Pedi para direcionar as tarefas para squads de agentes | Claude analisou os dados (8.800 deals, 85 accounts, 35 vendedores), mapeou relacionamentos entre tabelas, criou arquitetura com 7 fatores de scoring ponderados, templates SPIN Selling, e mapa de delegação para 5 agentes |
| 08:45 | Revisão crítica | Copiei o texto completo do challenge e pedi ao Claude para comparar a arquitetura com os requisitos, identificando gaps | Claude identificou: "GTXPro" vs "GTX Pro" quebraria o join, 1.425 deals sem account precisavam de tratamento nullable, scoring deveria ser por deal (não por account). Arquitetura corrigida |
| 08:55 | Geração do .MD | Pedi ao Claude para gerar o `Arquitetura_lead_scorer.md` completo com especificações, fórmulas, critérios de aceite por agente e mapa de delegação | Claude gerou documento de ~500 linhas: análise de dados, alertas de qualidade, stack, 7 fatores detalhados, templates SPIN, 5 fases, instruções por agente |
| 09:00 | Setup | Abri o Antigraft, criei o projeto "Desafio G4" do zero | Não aplicável (ação manual) |
| 09:05 | AIOS Install | No terminal do Claude Code, instalei o AIOS Framework (Synkra AIOS). Isso criou a estrutura `.aios-core/` com sistema de agentes, tasks, workflows e templates | Claude Code executou a instalação e configurou a estrutura multi-agentes |
| 09:10 | Injeção da arquitetura | Copiei o `Arquitetura_lead_scorer.md` gerado no claude.ai para dentro da pasta de arquitetura do projeto no AIOS | Não aplicável (transferência manual de contexto — ponte humana entre ferramentas) |
| 09:15 | AIOS Master — Kick-off | Pedi ao **AI Master** para ler o arquivo de arquitetura e iniciar a coordenação do projeto | AI Master leu a arquitetura, entendeu as 5 fases, identificou os agentes necessários e começou a distribuir diretrizes e tarefas |
| 09:20 | Fase 1 — Dados | AI Master coordenou agente de dados: parsing dos CSVs, normalização ("GTXPro" → "GTX Pro"), tipos TypeScript, DataContext | Agente implementou parser com PapaParse, tratamento de campos vazios, join das 4 tabelas |
| 09:30 | Fase 2 — Scoring | AI Master coordenou agente de analytics: 7 fatores de scoring, hook useLeadScoring, métricas agregadas | Agente implementou funções puras, normalização log-scale, classificação em 4 tiers |
| 09:35 | Fases 3+4 — Paralelo | AI Master disparou em paralelo: agente de conteúdo (templates SPIN) e agente de frontend (layout, dashboard, componentes) | Agentes trabalharam simultaneamente conforme diretrizes do Master |
| 09:45 | Integração | AI Master coordenou integração: scores + scripts na tabela de leads e painel de detalhes | Fluxo completo: Upload → Scoring → Dashboard → Tabela → Detalhes + Script |
| 09:50 | **V1 funcional** | Projeto rodando no browser com dados reais, scoring de 7 fatores | Validação humana: importei CSVs, verifiquei top deals |
| 10:00 | Design — Pesquisa | Pesquisei referências de dashboards SaaS. Decidi usar HubSpot como inspiração visual | Decisão estética humana |
| 10:10 | Design — Comet | Usei Comet (plugin IA) para criar design system baseado na referência HubSpot | Comet gerou paleta e componentes. Ajustei manualmente a tipografia |
| 10:30 | Design — Aplicação | AI Master coordenou aplicação do design system: dark mode profissional, hierarquia visual, badges nos tiers | IA aplicou estilos; eu validei e ajustei contrastes e espaçamentos |
| 11:00 | Documentação | Organizei README, process log, screenshots e evidências | ChatGPT auxiliou na estruturação textual |
| 11:30 | Revisão final | Revisei scoring, scripts SPIN, fluxo completo do app | Validação humana: top 10 deals, filtros, explicabilidade |
| 12:00 | Commit e push | AI Master coordenou organização final das pastas de submissão | Claude Code auxiliou nos comandos git |
| 13:00 | **Entrega** | Submissão finalizada | — |

### V2 — Reformulação Orientada por Dados

| Hora | Fase | O que aconteceu | Papel da IA |
| --- | --- | --- | --- |
| — | Análise exploratória | Voltei ao Claude (claude.ai) e pedi análise profunda dos dados brutos. "Entenda profundamente os dados antes de criar a arquitetura." | Claude executou 5 comandos de análise: contagens, distribuições, joins, win rates por segmento, tempos de ciclo |
| — | **Descoberta 1** | Win rate global é 63.5%, mas variância real está nos agentes (55% a 70.4% — diferença de 15pp) | Insight da IA: scorer precisa ponderar qualidade individual do rep com mais peso |
| — | **Descoberta 2** | Deals perdidos morrem em 14 dias (mediana), deals ganhos demoram 57 dias. Deals entre 15-30 dias têm win rate de 73% — **inverte a intuição de que deal rápido é deal quente** | Insight da IA que mudou fundamentalmente o pilar de momentum |
| — | **Descoberta 3** | 93% dos deals em Engaging estão estagnados (>90 dias no pipeline, mediana de 165 dias) | IA identificou que o scorer precisa separar "estagnado com potencial" de "estagnado sem chance" |
| — | **Descoberta 4** | Win rate por produto varia apenas 60-65% (irrelevante), mas expected value varia 445× entre MG Special (EV=36) e GTK 500 (EV=16.024) | IA concluiu: rankear por EV, não por chance de fechar |
| — | **Descoberta 5** | Win rate por setor varia de 61% (Finance) a 65% (Marketing). Efeito pequeno mas real | IA recomendou manter como componente de peso moderado |
| — | **Descoberta 6** | 1.425 deals sem conta associada (16% do pipeline aberto) | IA propôs penalização de -15 pontos e marcação "dados incompletos" na UI |
| — | **Descoberta 7** | GTK 500 é outlier: 40 deals com EV médio de 16.024, quase 3× o segundo colocado | IA sugeriu atenção imediata a qualquer deal GTK 500 aberto |
| — | Nova arquitetura | Com as 7 descobertas, Claude reformulou o scoring para 4 pilares: Valor (40%), Momentum (25%), Fit da Conta (15%), Qualidade do Rep (20%), com penalizações automáticas | IA redesenhou a fórmula inteira baseada em evidências empíricas dos dados |
| — | Mapeamento de sinais | Pedi ao Claude quais colunas do CSV alimentam cada pilar | Claude mapeou: 8 colunas do pipeline, 3 do accounts, 2 do sales_teams, 2 do products — com tratamento explícito dos 1.425 nulos |
| — | AIOS Master — Refatoração | Levei a nova arquitetura (4 pilares) de volta ao projeto. Pedi ao **AI Master** para coordenar a refatoração do scoring e da UI | AI Master redistribuiu tarefas: agente de analytics refatorou o scoring para 4 pilares + penalizações, agente de frontend atualizou os componentes de explicabilidade |

---

## Onde a IA errou e como corrigi

### 1. Scoring genérico vs orientado por dados (V1 → V2)

**O que a IA fez:** Na V1, o Claude criou uma arquitetura sólida com 7 fatores baseados em boas práticas gerais de scoring — win rate, valor, estágio, performance do vendedor, etc. Funcional, mas sem refletir os padrões específicos dos dados.

**O problema:** Ao analisar os dados profundamente na V2, descobri que o tempo no pipeline tinha apenas 10% de peso na V1, mas os dados 
mostravam que esse é um dos sinais mais fortes: deals entre 15-30 dias têm 73% de win rate, enquanto deals <8 dias têm apenas 53%. 
O pilar de momentum precisava ser muito mais relevante.

**Minha correção:** Reformulei para 4 pilares, elevando o Momentum de 10% para 25% de peso e criando uma curva de penalização progressiva baseada nas faixas reais dos dados. Também adicionei penalizações automáticas que a V1 não tinha (estagnação >90d, deal muito novo <8d, rep fraco).

### 2. Normalização do valor do produto

**O que a IA fez:** Na implementação, o agente de analytics usou normalização linear para o valor do produto.

**O problema:** O GTK 500 custa $26.768 e o MG Special custa $55 — diferença de 487×. Com normalização linear, todos os outros produtos teriam score próximo de zero neste fator.

**Minha correção:** Identifiquei o problema ao ver scores concentrados (~30 pts em média). Instruí a IA a implementar escala logarítmica: `(log(price) / log(max_price)) × 100`. Distribuição resultante equilibrada.

### 3. Deals sem account (1.425 de 2.089 ativos)

**O que a IA fez:** Na V2, o Claude propôs penalização de -15 pontos para deals sem conta. Na implementação, porém, o agente inicialmente atribuía score zero a esses deals.

**O problema:** Eliminar quase 70% dos deals ativos do scoring é inaceitável.

**Minha correção:** Mantive a penalização de -15 pontos da V2, mas garanti que os demais pilares (valor, momentum, qualidade do rep) são calculados normalmente. A UI marca esses deals como "Conta não identificada" em vez de escondê-los.

### 4. Tipografia e design system

**O que a IA fez:** O Comet gerou um design system com tipografia sem boa legibilidade.

**Minha correção:** Descartei a tipografia, pesquisei o design system da HubSpot, e reapliquei manualmente as escolhas de fonte, peso e espaçamento.

### 5. Scripts SPIN genéricos

**O que a IA fez:** Os primeiros templates SPIN saíam vagos, sem aproveitar dados reais.

**Minha correção:** Refinei as variáveis para incluir dados concretos: nome do account, setor, produtos comprados, produtos nunca comprados (cross-sell), deals perdidos (win-back), métricas do vendedor.

---

## O que eu adicionei que a IA sozinha não faria

### 1. Estruturação do problema antes de qualquer IA

Antes de abrir o Claude, sentei com o Notepad e decompus: o que o vendedor precisa, o que tenho nos dados, o que entregar, como submeter, e cronograma por bloco de tempo. A IA executa bem com instrução clara — essa clareza foi contribuição minha.

### 2. Decisão de iterar: V1 → V2


A V1 funcionava. A decisão de voltar ao Claude, pedir análise profunda dos dados, e reformular a arquitetura inteira com base em evidências empíricas foi humana. A IA não decide sozinha "vou refazer meu trabalho porque posso fazer melhor" — eu decidi que os dados tinham mais a dizer.

### 3. Ponte entre Claude conversacional e AIOS Framework

O documento .MD serviu como "contrato" entre o planejamento (Claude no claude.ai) e a execução (agentes no AIOS). Criei uma ponte entre duas ferramentas de IA que não se comunicam nativamente. Essa estratégia de orquestração foi humana.

### 4. Validação de coerência do scoring

Após a implementação, abri o app e verifiquei manualmente se os top deals faziam sentido. A IA calcula, mas eu validei: "esse account com alto win rate vendendo GTK 500 em Engaging deveria ser Hot". Verificação humana é o que garante confiança.

### 5. Gestão de tempo e priorização

Quando às 09:50 a V1 estava rodando, a decisão de parar, analisar os dados profundamente, e reformular toda a arquitetura (V2) em vez de apenas polir a UI foi estratégica. Depois, dedicar 1 hora inteira ao design também — porque ferramenta que parece amadora não gera confiança.

### 6. AIOS Master como orquestrador constante

Em todas as etapas eu direcionei o trabalho via AI Master, não via código direto. Essa decisão de sempre passar pelo orquestrador garantiu consistência entre os agentes e rastreabilidade das decisões.

---

## Resultados

A aplicação permite que o vendedor:

- Saiba exatamente quais deals priorizar na sua carteira
- Entenda o impacto de cada fator no score (explicação visual por pilar)
- Tenha um roteiro SPIN Selling estruturado para abordar o cliente
- Filtre por vendedor, região, manager ou produto
- Visualize o pipeline com clareza em dashboard profissional

O scoring da V2 se mostrou mais preciso que a V1 por incorporar os padrões reais dos dados — especialmente o momentum (tempo no pipeline) que subiu de 10% para 25% de peso.

---

## Recomendações

1. **Integração com CRM** — Eliminar upload manual conectando à API do Salesforce/HubSpot
2. **Calibração com dados reais** — Coletar conversões futuras e ajustar pesos com base em resultados
3. **Piloto com time comercial** — Testar com 5-10 vendedores e medir impacto na taxa de fechamento
4. **Modelo preditivo** — Segunda fase: treinar ML com os 6.711 deals históricos (Won/Lost) como labels
5. **Notificações** — Integrar com Slack/email para alertas de mudança de tier

---

## Limitações

- Scoring baseado em regras e heurísticas (4 pilares + penalizações), não em modelo preditivo treinado
- 1.425 deals ativos (68%) sem account vinculado — recebem penalização de -15 pts e score parcial
- Dados estáticos (upload manual de CSVs), sem conexão com CRM em tempo real
- Scripts SPIN gerados por templates parametrizados (IA generativa é opcional)
- Sem persistência entre sessões — dados processados em memória
- Sem autenticação — qualquer pessoa com a URL acessa

---

## Evidências

| Tipo | Localização | Descrição |
| --- | --- | --- |
| Arquitetura V1 | `docs/Arquitetura_lead_scorer.md` | Documento .MD com 7 fatores, SPIN Selling e mapa de agentes — gerado no Claude, injetado no AIOS |
| Chat V1 — Arquitetura | `process-log/chat-exports/claude-v1-arquitetura-7-fatores.md` | Conversa no claude.ai: análise dos CSVs, 7 fatores, templates SPIN, mapa de delegação |
| Chat V2 — Exploração | `process-log/chat-exports/claude-v2-analise-profunda-dados.md` | Conversa no claude.ai: 5 comandos de análise, 7 descobertas nos dados, reformulação para 4 pilares |
| Screenshots | `process-log/screenshots/` | Capturas de tela das conversas com IA e do app funcional |
| Screen Recording | `process-log/` | Gravação do workflow de desenvolvimento |
| Notepad Original | `process-log/notepad-planejamento.txt` | Anotações de planejamento feitas antes de usar qualquer IA |
| Estrutura AIOS | `.aios-core/` | Framework de agentes com tasks, workflows, templates e regras — usado em todas as etapas |
| Config AI Master | `.claude/` | Configuração do Claude Code em modo AIOS Master Agent |
| Git History | Commits do repositório | Mensagens documentando cada fase |

---

*Submissão enviada em: 28/03/2026*