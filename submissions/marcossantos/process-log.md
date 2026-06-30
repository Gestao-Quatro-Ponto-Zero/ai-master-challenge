# Process Log — Lead Scorer

Documentação do processo de construção da solução, decisões tomadas e uso de IA.

---

## Ferramenta de IA utilizada

**Claude (Anthropic)** via claude.ai — utilizado como pair programmer ao longo de toda a construção, desde o design da arquitetura até geração de código, debugging e documentação.

---

## Como a IA foi usada

A abordagem foi colaborativa e iterativa — não "gere tudo de uma vez", mas uma conversa técnica estruturada onde cada decisão foi discutida antes de ser implementada.

### Padrão de uso em cada módulo

```
1. Apresentar o problema / requisito
2. Discutir arquitetura antes de codar
3. Gerar o código módulo por módulo
4. Debugar erros reais (mensagens copiadas do terminal)
5. Iterar e melhorar
```

---

## Linha do tempo do desenvolvimento

### Fase 1 — Arquitetura

**Prompt inicial:**
> "Como poderíamos começar? Pensei em algo como uma dashboard, talvez com Java trabalhando no back"

**Decisão tomada com IA:**
A IA sugeriu abandonar Java/Spring Boot em favor de Python + FastAPI pelo fit natural com pandas para processar CSVs, e React no frontend. Justificativa pragmática: menos boilerplate, setup mais rápido para demo local.

**Checklist de qualidade aplicado antes de codar:**
Antes de escrever qualquer linha, revisamos os critérios do challenge contra a arquitetura proposta e identificamos gaps — a primeira versão tinha só features óbvias. A IA identificou que faltavam features não-óbvias e explainability real, e a arquitetura foi revisada antes de qualquer código.

---

### Fase 2 — Backend core (scoring engine)

**Por que scoring por regras e não ML?**
O enunciado deixa claro que a Head de RevOps quer algo útil, não um modelo perfeito. Regras bem explicadas entregam mais valor imediato que um XGBoost sem interface. ML foi listado como próximo passo, não como entrega.

**Features não-óbvias escolhidas:**

| Feature | Por que não-óbvia | Impacto |
|---|---|---|
| Velocity Score | Compara vs. média histórica do produto específico, não média global | Captura esfriamento contextualizado |
| Product Win Rate | Produtos têm WR muito diferentes nos dados reais | GTX Pro 65% vs MG Special 30% |
| Agent Performance | Win rate histórico do vendedor responsável | Contexto humano que CRMs ignoram |
| Notes Activity | Contato recente documentado prediz engajamento | Único fator dinâmico — muda em tempo real |

**Estrutura de código — separação de responsabilidades:**
```
factors.py   → cada fator = função isolada e testável
engine.py    → só orquestra, não tem lógica própria
main.py      → só rotas, zero lógica de negócio
```

---

### Fase 3 — Debugging no Windows

**Problemas reais encontrados e resolvidos com IA:**

| Erro | Causa | Solução |
|---|---|---|
| `pandas metadata-generation-failed` | Versão pinada tentava compilar do source | Trocar `==` por `>=` no requirements.txt |
| `uvicorn: command not found` | Instalado no user path, Git Bash não encontra | `python -m uvicorn main:app` |
| `ModuleNotFoundError: models.schemas` | Python não adiciona `.` ao path no Windows | `$env:PYTHONPATH = "."` no PowerShell |
| `FileNotFoundError: sales_pipeline.csv` | `DATA_DIR` apontava 3 níveis acima | Corrigir para `Path(__file__).parent` |
| `index.html` / `main.jsx` não encontrados | Arquivos não chegaram ao download | Reenvio individual dos arquivos |

Todos debugados colando a mensagem de erro exata no chat e recebendo causa + solução diretamente.

---

### Fase 4 — Features avançadas (JWT, Alertas, Notes, Analytics)

**JWT sem biblioteca externa:**
Decisão de não usar `python-jose` — tem histórico de vulnerabilidades. Implementado com `hmac` + `hashlib` do Python padrão. Mais seguro para demo, sem dependência adicional.

**Filtro automático por role na API:**
O vendedor não passa parâmetros — o backend aplica o filtro baseado no token. Evita que um agent acesse dados de outro passando `?agent=outro` na URL.

**Scheduler de alertas com asyncio:**
pandas é síncrono e bloquearia o event loop do FastAPI se rodado diretamente em uma coroutine. Solução: `run_in_executor` para rodar a detecção em thread pool separada.

**Deduplicação de alertas:**
Chave `tipo::opportunity_id` — evita spam de alertas repetidos a cada rodada do scheduler sem precisar de banco de dados.

**Deal Notes alimentando o scoring:**
`factor_notes_activity()` em `factors.py` importa `get_days_since_last_note()` de `notes/store.py`. Import feito dentro da função para evitar circular import no topo do módulo.

**Analytics restrito por role:**
Lógica de filtro centralizada em `_resolve_filters()` no router para não duplicar em cada rota. Managers veem automaticamente só o próprio time.

---

### Fase 5 — Frontend CRM

**Decisões de design:**

**Paleta CRM profissional:**
Sidebar azul-marinho `#0F1C2E` — familiar para usuários de Salesforce/HubSpot. Score bars coloridas inline na tabela — visual imediato sem precisar ler número.

**Token em memória, não localStorage:**
localStorage é vulnerável a XSS. Token vive no estado React e some ao fechar a aba — comportamento correto para ferramenta B2B.

**Proxy Vite:**
`vite.config.js` configurado para fazer proxy de `/api/*` para `localhost:8000` — elimina CORS em desenvolvimento.

**SVG puro nos gráficos de analytics:**
Para barras horizontais simples, SVG/CSS é suficiente e elimina dependência de recharts/chart.js.

---

### Fase 6 — Segurança e Notificações

**Bcrypt para senhas:**
Substituiu comparação em texto plano. Work factor 12 — bom equilíbrio entre segurança e velocidade. Migração automática no startup: `migrate_plain_passwords()` converte senhas antigas para hash sem intervenção manual.

**Gmail SMTP com App Password:**
Senha normal do Gmail não funciona via SMTP. App Password é gerada em `myaccount.google.com/apppasswords` e colocada no `.env` — nunca no código.

**Dois tipos de notificação:**
- Alerta crítico: imediato, disparado pelo detector quando `severity == critical`
- Resumo diário: agendado via `DigestScheduler` no horário configurado em `.env`

**`.gitignore` adicionado:**
`.env`, `alerts.json` e `notes.json` excluídos do controle de versão — credenciais e dados de runtime não devem ser commitados.

---

## Decisões que não tomei e por quê

| Alternativa | Por que não |
|---|---|
| Banco de dados | Overhead desnecessário para demo |
| ML (XGBoost) | Sem interface não entrega valor; regras explicáveis > modelo black box |
| React Router | SPA simples com estado é suficiente |
| Refresh token | Sessão de 8h cobre uma jornada de trabalho |
| WebSocket para alertas | Polling de 60s é suficiente para o contexto |

---

## O que eu faria diferente com mais tempo

1. **Testes automatizados** — `pytest` para o scoring engine
2. **Script de sync de usuários** — gerar `users.json` automaticamente a partir do `sales_teams.csv`
3. **WebSocket** — alertas em push real-time em vez de polling
4. **Export CSV** — botão "exportar pipeline" na tabela de deals
5. **Onboarding** — tour explicativo na primeira abertura do analytics

---

## Métricas do projeto

| Item | Quantidade |
|------|-----------|
| Arquivos Python | 22 |
| Arquivos React/JS | 14 |
| Rotas de API | 22 |
| Fatores de scoring | 6 |
| Tipos de alerta | 4 |
| Módulos backend | 7 (data, scoring, auth, alerts, notes, analytics, notifications) |
| Linhas de código (aprox.) | ~3.200 |

---

## Conclusão

O uso de IA foi central em todas as fases — não como gerador de código cego, mas como par técnico que discutiu trade-offs, identificou gaps nos critérios de qualidade, debugou erros reais e manteve consistência arquitetural ao longo de múltiplas sessões.

O resultado vai além do mínimo pedido: não é só um script que prioriza deals, é uma plataforma com autenticação segura (bcrypt + JWT), alertas automáticos com notificação por email, histórico de contatos que alimenta o scoring, e analytics completo para managers — tudo com separação de responsabilidades clara e código que outro dev consegue manter.