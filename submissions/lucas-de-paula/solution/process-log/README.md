# Process Log — Evidências

Esta pasta contém as evidências do processo de uso de IA na construção da solução.

## Conteúdo

| Item | Descrição |
|---|---|
| `../PROCESS_LOG.md` | Log completo do processo (5 fases) |
| `screenshots/` | Screenshots das iterações com IA |

## Evidências principais

1. **Git history** — https://github.com/oetnegro/lead-scorer-g4/commits/main
   ~30 commits descritivos mostrando a evolução de MVP até Coach de IA

2. **Live app** — https://lead-scorer-g4.vercel.app
   Funcional em produção com os dados reais do challenge

3. **Vídeo demo** — https://www.youtube.com/watch?v=_cXS8DyBenQ
   Demo completo da solução em produção

## Screenshots das iterações com IA

| # | Arquivo | O que evidencia |
|---|---|---|
| 01 | `01-arquitetura-definida-pre-codigo.png` | Telas e componentes definidos pelo usuário **antes** de começar a codar — análise prévia, não delegação |
| 02 | `02-decisao-foco-no-vendedor.png` | Usuário direciona: "a ferramenta precisa funcionar para o vendedor, não só parecer boa" |
| 03 | `03-priorizacao-grupos-features.png` | Usuário organiza features em 4 grupos de prioridade — decisão estrutural própria |
| 04 | `04-decisao-local-vs-supabase.png` | Decisão arquitetural: CSV local primeiro, Supabase depois — com raciocínio explícito |
| 05 | `05-erro-deserializacao-datas.png` | Bug real capturado: datas chegando como string JSON, não como Date — debugging genuíno |
| 06 | `06-correcoes-confirmadas-tabela.png` | Tabela de 4 bugs corrigidos com status ✅ — evidência de teste e validação real |
| 07 | `07-usuario-corrige-ux-tooltip.png` | Usuário identifica z-index incorreto no tooltip e instrui correção específica |
| 08 | `08-analise-criterios-challenge.png` | Usuário analisa critérios do challenge vs o que foi entregue — decisão estratégica consciente |
| 09 | `09-usuario-corrige-logica-kpi.png` | Usuário corrige lógica do KPI "Em risco" (31–90d apenas, não incluir zumbis) — steering crítico |
| 10 | `10-app-producao-dados-reais.png` | App funcionando em produção no Vercel com dados reais do pipeline |

---

## Calibração dos Pesos — Justificativa com Dados Reais

Os 4 pesos foram definidos **antes do código**, a partir de análise manual dos 4 CSVs do challenge.

| Componente | Peso | Dado do dataset que justifica |
|---|---|---|
| Stage + Momentum | 30pts | 1.479 dos 2.092 deals ativos (71%) estão em Engaging há +90d. Timing é o sinal mais acionável e o mais diferenciador entre deals |
| Produto / Ticket | 25pts | Variância de 486× no ticket: GTK 500 = R$26.768 vs MG Special = R$55. 1 GTK = 486 MG Specials em impacto de receita |
| Qualidade da Conta | 25pts | Receita das contas varia de <100M a >2.000M (20×). Empresas enterprise fecham negócios maiores com win rate mais previsível |
| Win Rate do Agente | 20pts | Agentes do mesmo time variam de 20% a 70% — diferença de 3.5× na probabilidade de fechamento real |

### Por que MG Special tem 3/25 — e por que o alto volume não muda isso

**Dados do dataset:**
- MG Special: **1.651 deals** (79% do pipeline) × R$55 = R$90.805 de potencial total
- GTK 500: **41 deals** (2% do pipeline) × R$26.768 = R$1.097.488 de potencial total

O GTK 500 tem **12× mais potencial de receita com 40× menos deals**.

O alto volume do MG Special é precisamente o motivo para não elevar seu peso. Se o peso fosse 15–20pts, vendedores com carteira mista teriam incentivo errado: priorizariam MG Specials pela quantidade em vez de GTK 500 pelo valor unitário.

**O peso baixo força a diferenciação correta:** dentro dos 1.651 deals MG Special, a priorização acontece pelos outros 3 componentes (stage, conta, win rate) — os sinais reais de quem vai fechar primeiro. O score distingue os MG Special urgentes dos estagnados sem precisar inflar o peso do produto.

O scoring reflete impacto de receita por deal, não popularidade de produto. **3/25 é intencional e calibrado nos dados.**
