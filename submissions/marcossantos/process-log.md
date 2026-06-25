# Process Log — Lead Scorer

Documentação do processo de construção da solução, decisões tomadas e uso de IA.

---

## Ferramenta de IA utilizada

**Claude (Anthropic)** via claude.ai — utilizado como pair programmer ao longo de toda a construção, desde o design da arquitetura até a geração de código, debugging e documentação.

---

## Como a IA foi usada

A abordagem foi colaborativa e iterativa — não "gere tudo de uma vez", mas uma conversa técnica estruturada onde cada decisão foi discutida antes de ser implementada.

### Padrão de uso em cada módulo

```
1. Apresentar o problema / requisito
2. Discutir arquitetura antes de codar
3. Gerar o código módulo por módulo
4. Debugar erros reais (com mensagens copiadas do terminal)
5. Iterar e melhorar
```

---

## Linha do tempo do desenvolvimento

### Fase 1 — Arquitetura

**Prompt inicial:**
> "Fiz tudo porém faltou esse arquivo para rodar: requirements.txt — como poderíamos começar? Pensei em algo como uma dashboard ou algo do tipo, talvez com Java trabalhando no back"

**Decisão tomada com IA:**
A IA sugeriu abandonar Java/Spring Boot em favor de Python + FastAPI pelo fit natural com pandas para processar CSVs, e React + Tailwind no frontend. A justificativa foi pragmática: menos boilerplate, setup mais rápido, pandas é a ferramenta certa para o trabalho.

**Arquitetura definida antes de escrever qualquer código:**
```
CSV files → loader.py → scoring engine → FastAPI → React frontend
```

**Checklist de qualidade aplicado antes de codar:**
Antes de começar, revisamos os critérios do challenge contra a arquitetura proposta e identificamos gaps — a primeira versão tinha apenas features óbvias (stage, valor, tamanho da conta). A IA identificou que faltavam features não-óbvias e explainability real, e a arquitetura foi revisada antes de qualquer linha de código.

---

### Fase 2 — Backend core (scoring engine)

**Decisões de design discutidas:**

**Por que scoring por regras e não ML?**
O enunciado deixa claro que a Head de RevOps quer algo útil, não um modelo perfeito. Regras bem explicadas entregam mais valor imediato que um XGBoost sem interface. ML foi listado como próximo passo, não como entrega.

**Por que 6 fatores e não mais?**
Cada fator precisa ser explicável ao vendedor. Mais fatores = mais complexidade = menos confiança do usuário. Os 6 escolhidos cobrem dimensões independentes do deal.

**Features não-óbvias escolhidas e justificativa:**

| Feature | Por que não-óbvia | Impacto |
|---|---|------|
| Velocity Score | Compara vs. média histórica *do produto específico*, não uma média global | Captura esfriamento contextualizado |
| Product Win Rate | Produtos têm WR muito diferentes nos dados reais | GTX Pro 65% vs MG Special 30% |
| Agent Performance | Win rate histórico do vendedor responsável | Contexto humano que CRMs ignoram |
| Notes Activity | Contato recente documentado prediz engajamento | Único fator dinâmico — muda em tempo real |

**Estrutura de código — por que módulos separados:**
```
factors.py   → cada fator = função isolada (testável independentemente)
engine.py    → só orquestra, não tem lógica própria
main.py      → só rotas, zero lógica de negócio
```
Essa separação foi uma decisão explícita para atender o critério "código limpo o suficiente pra outro dev dar manutenção".

---

### Fase 3 — Debugging no Windows

**Problemas reais encontrados e como foram resolvidos com IA:**

**Problema 1 — pandas não instala:**
```
error: metadata-generation-failed — pandas 2.2.2
Encountered error while generating package metadata
```
**Causa:** versão pinada tentava compilar do source, precisava do Visual Studio Build Tools.  
**Solução:** trocar `==` por `>=` no requirements.txt para o pip escolher wheels pré-compiladas.

**Problema 2 — uvicorn não encontrado:**
```
bash: uvicorn: command not found
```
**Causa:** instalado no user path do Windows, Git Bash não encontra.  
**Solução:** `python -m uvicorn main:app --reload --port 8000`

**Problema 3 — ModuleNotFoundError:**
```
ModuleNotFoundError: No module named 'models.schemas'
```
**Causa:** Python não adiciona o diretório atual ao path automaticamente no Windows.  
**Solução:** `$env:PYTHONPATH = "."` no PowerShell antes de subir o servidor.

**Problema 4 — CSVs não encontrados:**
```
FileNotFoundError: .../submissions/marcossantos/data/sales_pipeline.csv
```
**Causa:** `DATA_DIR` no loader.py apontava 3 níveis acima, mas os CSVs estavam em `backend/data/`.  
**Solução:** corrigir para `Path(__file__).parent` — uma linha.

**Aprendizado:** todos esses problemas foram debugados colando a mensagem de erro exata no chat e recebendo a causa + solução diretamente, sem pesquisa manual.

---

### Fase 4 — Features avançadas

Após o core funcionando, três módulos foram adicionados em sequência, cada um com a mesma estrutura de discussão → arquitetura → código:

**JWT + Roles**

Decisão de não usar `python-jose`: a biblioteca tem histórico de vulnerabilidades e adiciona dependência externa desnecessária. JWT foi implementado com `hmac` + `hashlib` do Python padrão — mais seguro para demo e sem dependência adicional.

Sistema de roles implementado como filtro automático na API — o vendedor não precisa passar parâmetros, o backend aplica o filtro baseado no token. Isso evita que um agent acesse dados de outro passando `?agent=outro` na URL.

**Sistema de Alertas**

Decisão chave: usar `asyncio` com `run_in_executor` para o scheduler — pandas é síncrono e bloquearia o event loop do FastAPI se rodado diretamente em uma coroutine.

Deduplicação por chave `tipo::opportunity_id` — evita spam de alertas repetidos a cada rodada do scheduler sem precisar de banco de dados.

**Deal Notes alimentando o scoring**

Integração entre módulos: `factor_notes_activity()` em `factors.py` importa `get_days_since_last_note()` de `notes/store.py`. O import foi colocado dentro da função para evitar circular import no topo do módulo.

**Analytics**

Decisão de restringir a `manager` e `admin` via `require_role()` — agents não têm contexto para interpretar métricas de time. A lógica de filtro por role foi centralizada em `_resolve_filters()` no router para não duplicar em cada rota.

---

### Fase 5 — Frontend

**Decisões de design:**

**Paleta CRM profissional:**
- Sidebar azul-marinho `#0F1C2E` — familiar para usuários de Salesforce/HubSpot
- Score bars coloridas inline na tabela — visual imediato sem precisar ler número
- Fundo cinza frio com superfícies brancas — denso mas legível

**Token em memória, não localStorage:**
Decisão de segurança — localStorage é vulnerável a XSS. Token vive no estado React e some ao fechar a aba, que é o comportamento correto para uma ferramenta B2B.

**Proxy Vite:**
`vite.config.js` configurado para fazer proxy de `/api/*` para `localhost:8000` — elimina CORS em desenvolvimento sem precisar de configuração extra no backend.

**Componentes de analytics em SVG puro:**
Gráficos de barra implementados sem biblioteca (recharts, chart.js). Decisão pragmática — para barras horizontais simples, SVG/CSS é suficiente e elimina dependência.

---

## Decisões que não tomei e por quê

| Alternativa considerada | Por que não foi feita |
|---|---|
| Banco de dados (SQLite/PostgreSQL) | Overhead desnecessário para demo — CSVs + JSON files cumprem o requisito |
| ML (XGBoost/LightGBM) | Sem interface não entrega valor; regras explicáveis > modelo black box para esse público |
| React Router para navegação | Uma SPA simples com estado é suficiente — evita configuração extra |
| bcrypt para senhas | Demo only — documentado nas limitações com caminho para produção |
| Refresh token | Sessão de 8h é suficiente para uma jornada de trabalho |

---

## O que eu faria diferente com mais tempo

1. **Testes automatizados** — `pytest` para o scoring engine (especialmente os fatores, que têm lógica numérica que merece cobertura)
2. **Sincronizar `users.json` com o CSV** — um script de setup que lê os agentes do `sales_teams.csv` e gera os usuários automaticamente, eliminando a necessidade de edição manual
3. **WebSocket para alertas** — em vez de polling a cada 60s no frontend, push real do backend quando novo alerta é detectado
4. **Tela de onboarding** — primeira vez que um manager abre o analytics, um tour explicando o que cada métrica significa
5. **Export para CSV** — botão "exportar pipeline" na tabela de deals para integrar com ferramentas existentes do time

---

## Métricas do projeto

| Item | Quantidade |
|------|-----------|
| Arquivos Python criados | 18 |
| Arquivos React/JS criados | 14 |
| Rotas de API implementadas | 19 |
| Fatores de scoring | 6 |
| Tipos de alerta | 4 |
| Módulos backend | 6 (data, scoring, auth, alerts, notes, analytics) |
| Linhas de código (aprox.) | ~2.800 |

---

## Conclusão

O uso de IA foi central em todas as fases — não como gerador de código cego, mas como par técnico que discutiu trade-offs, identificou gaps nos critérios de qualidade, debugou erros reais e manteve consistência arquitetural ao longo de múltiplas sessões.

O resultado é uma solução que vai além do mínimo pedido: não é só um script que prioriza deals, é uma plataforma com autenticação, alertas automáticos, histórico de contatos e analytics — tudo construído com separação de responsabilidades clara e código que outro dev consegue dar manutenção.