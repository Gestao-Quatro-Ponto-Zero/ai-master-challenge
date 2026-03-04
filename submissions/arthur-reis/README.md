# Submissão — Arthur Reis — Challenge 002: Redesign de Suporte

## Sobre mim

- **Nome:** Arthur Reis
- **LinkedIn:** [seu LinkedIn aqui]
- **Challenge escolhido:** 002 — Redesign de Suporte G4 Tech

---

## Como acessar a solução

| Arquivo | Como abrir | O que é |
|---------|-----------|---------|
| `solution/diagnostico-e-proposta.html` | Abrir no browser (duplo clique) | Entregáveis 1 e 2 — Diagnóstico Operacional + Proposta de Automação com IA |
| `solution/app.html` | Abrir no browser (duplo clique) | Entregável 3 — Protótipo interativo do pipeline SIM/TALVEZ/NÃO |
| `solution/diagnostico-e-proposta.py` | `python3 diagnostico-e-proposta.py` | Gera o diagnostico-e-proposta.html (requer `pip3 install plotly pandas`) |
| `process-log/DEVLOG.md` | Qualquer editor de texto | Log completo de decisões, erros e correções |

> **Nenhuma instalação necessária para visualizar a solução.** Abra `diagnostico-e-proposta.html` e `app.html` diretamente no browser.

---

## Executive Summary

A operação de suporte da G4 Tech tem 67.3% dos tickets sem resolução — não por falta de capacidade humana, mas por ausência de inteligência no processo. A análise de 8.469 tickets revelou dois problemas estruturais distintos: tickets "Open" que nunca receberam sequer uma primeira resposta (falha de capacidade) e tickets "Pending" abandonados sem follow-up automático (falha de processo). A proposta é uma plataforma interna com pipeline de decisão SIM/TALVEZ/NÃO: IA resolve o que é repetível, entrega contexto pronto para o que exige julgamento humano, e aprende continuamente com cada ticket resolvido.

---

## Solução

### Abordagem

Comecei pelos dados: 8.469 tickets, 5 tipos, 4 canais, 3 status. A primeira hipótese (problema localizado em algum canal ou tipo específico) foi refutada pelos dados — as taxas de fechamento são quase idênticas em todos os recortes (~32–34%), o que revelou um problema sistêmico, não pontual.

Em seguida, quantifiquei o custo operacional do problema, identifiquei o que é automatizável por tipo de ticket e desenhei a proposta em 3 fases, priorizando o que gera resultado mais rápido com menor complexidade técnica.

O protótipo foi construído para demonstrar o pipeline de decisão da plataforma com tickets reais em português, cobrindo todas as categorias.

### Resultados / Findings

**Bloco 1 — Onde o fluxo trava:**
- 67.3% dos tickets não foram resolvidos (2.819 Open + 2.881 Pending)
- Distribuição uniforme entre canais e tipos confirma: o problema é o processo, não o canal
- 32.9% dos tickets Open nunca receberam first response — fila sem capacidade de atendimento 24/7
- TTR dos resolvidos: mediano ~6.4h, 100% abaixo de 24h — o problema não é a velocidade de resolução, é iniciar o atendimento

**Bloco 2 — CSAT:**
- Ratings estatisticamente aleatórios (Pearson r = -0.0035, F-stats < 1.5 em todos os recortes)
- Sistema de CSAT não funciona — dados não refletem satisfação real
- Impossível medir impacto de qualquer melhoria sem CSAT real

**Bloco 3 — Custo do desperdício:**
- ~12.520 horas de agente na operação total
- Combinações mais críticas: Social media × Cancellation (26.2% fechados), Phone × Cancellation (27.7%)
- Potencial de automação: Billing e Product inquiry até 85%, Technical issue ~60%, Cancellation: nunca automatizar

### Recomendações

1. **Fase 1 (semanas 1–4):** follow-up automático nos 2.881 tickets Pending + CSAT real. Impacto estimado: +19pp de resolução, ~547 tickets reativados. Sem ML, sem risco.
2. **Fase 2 (meses 1–2):** pipeline de decisão SIM/TALVEZ/NÃO em produção. Classificação automática na primeira mensagem, fila humana com contexto estruturado.
3. **Fase 3 (meses 2–4):** respostas automáticas para casos SIM em Billing e Product inquiry via Claude API + RAG.
4. **Cancellation request:** nunca automatizar. SLA máximo de 2h, agentes especializados em retenção, contexto completo do histórico do cliente.

### Limitações

**Limitação crítica — qualidade dos dados fornecidos para ML:**
Os dois datasets do challenge foram gerados sinteticamente para análise de métricas operacionais — não para treino de modelos de NLP.

- **Dataset 1 `Ticket Subject`:** média de 15.7 caracteres, textos genéricos ("Hardware issue", "Delivery problem") quase idênticos ao nome da categoria — sem sinal semântico para classificação.
- **Dataset 1 `Ticket Description`:** templates com variáveis não preenchidas (`{product_purchased}`) e frases aleatórias concatenadas sem coerência — dado sintético inválido para NLP.

Consequência: qualquer modelo de ML treinado nesses dados retorna ~20–21% de confiança em todas as classes (distribuição uniforme = sem aprendizado real). Após 3 iterações de arquitetura (TF-IDF → keywords → sentence-transformers multilíngue), o problema foi rastreado até a origem: o material de treino não tem sinal.

O protótipo usa classificação por regras semânticas (keyword-based PT/EN) — explícita, auditável e confiável — em vez de ML treinado em dado sintético. Em produção real, o classificador seria treinado nos tickets históricos da própria empresa, onde o sinal semântico existe.

**Outras limitações:**
- CSAT do dataset é estatisticamente aleatório — impossível construir análise de correlação satisfação × operação
- Custo financeiro calculado com benchmark de mercado (R$ 45/h) — sem acesso ao custo real da empresa
- Projeções de cobertura por fase são estimativas baseadas em benchmarks de mercado, não em dados históricos da G4 Tech

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude (Cowork) | Diagnóstico, análise dos dados, construção do diagnostico.py, proposta de automação (Bloco 4), decisões de arquitetura, README |
| Claude Code | Iterações do app.py, debugging de erros Python, auditoria de qualidade dos dados |

### Workflow

1. Upload dos datasets → análise exploratória com Claude → identificação dos achados principais
2. Construção do BRIEFING.md com os achados validados (números reais, não recalculados)
3. Geração do diagnostico.py (Blocos 1–3) + validação dos gráficos e números
4. Adição do Bloco 4 completo ao diagnóstico (pipeline, stack, roadmap, base de conhecimento, melhoria contínua)
5. Três iterações do app.py em busca de classificação ML confiável → auditoria dos dados → decisão de pivotar para protótipo de fluxo
6. Construção do app.html com 3 caminhos completos e conteúdo realista em português
7. Identificação do dual-output: qualquer resposta SIM com promessa de prazo gera tarefa interna de execução para o operador — documentado no protótipo e no Bloco 4
8. Documentação contínua no DEVLOG de cada decisão, erro e ponto de inflexão

### Onde a IA errou e como corrigi

**Erro principal:** nas 3 iterações do app.py, o Claude iterou em algoritmos (TF-IDF → keywords → sentence-transformers) sem auditar a qualidade dos dados de treino. O problema raiz era o dado, não o algoritmo. Identifiquei o problema ao testar o app com tickets reais em português e perceber que a confiança era sempre ~21% — distribuição uniforme, sinal de que o modelo não aprendeu nada.

**Como corrigi:** solicitei auditoria direta das colunas candidatas a treino. O Claude executou a análise, confirmou os problemas (`{product_purchased}` literal, média de 15.7 chars no Subject) e documentou a causa raiz. Decisão de arquitetura tomada por mim: protótipo de fluxo com classificação confiável em vez de ML em dado sintético.

**Outros erros menores:** n8n e Evolution API sugeridos inicialmente para a proposta de automação — descartados por mim, substituídos por arquitetura interna com Claude API.

### O que eu adicionei que a IA sozinha não faria

- **Julgamento de qualidade:** perceber que 21% de confiança em todos os tickets não era problema de algoritmo, era problema de dado
- **Decisão de arquitetura:** escolher protótipo de fluxo confiável em vez de insistir em ML instável para uma demo
- **Limites de automação:** a decisão de nunca automatizar Cancellation request é julgamento de negócio, não técnico
- **Contexto de produto:** reconhecer que a proposta não deve depender de ferramentas externas (n8n, Evolution API) — a empresa precisa de arquitetura própria escalável
- **Fechamento do loop:** identificar que resposta automática satisfatória não é suficiente — qualquer resposta que promete ação com prazo precisa gerar uma tarefa interna para o operador executar. A IA responde. O humano entrega. Isso é diferente de "automatizar respostas" — é fechar o ciclo entre promessa e entrega

### Relato pessoal (SEM IA)

Ao iniciar o desafio, tinha algo relativamente claro na cabeça e de fato parecia que concluiria em 1-2 horas no máximo, mas ao chegar próximo ao suposto final, principalmente na parte do app protótipo o processo começou a rodar em circulos, tal qual acontece quando estou fazendo algo no lovable, quanto maior a aplicação e mais proxima de acabar mais aparecem dificuldades e a IA começa a sair da linha mestra.

Depois de queimar um pouco de neurônio e paciência com o claude, consegui chegar numa entrega satisfatória de visualização do fluxo completo para implementação futura.

Aprendi muito com esse desafio e confesso que me deu vontade de fazer os outros, mas nesse momento vou seguir as instruções e ficar com essa boa entrega.



---

## Evidências

- [x] DEVLOG completo em `process-log/DEVLOG.md` — todas as decisões, erros e correções registrados
- [x] Screenshot em `process-log/screenshots/` — terminal mostrando testes e iterações
- [x] Gravação de tela (parcial — ~3h): [Ver no Google Drive](https://drive.google.com/file/d/1JW9byj0-lwX4g0f9FuUfKe20Y8F5dHm1/view?usp=sharing) · Nota: gravação interrompeu automaticamente. Restante documentado no DEVLOG.
- [x] Chat export em `process-log/chat-exports/conversa-challenge-002.pdf` — 190 mensagens da conversa completa com Claude
- [x] Git history (branch `submission/arthur-reis`)

---

*Submissão enviada em: 2026-03-04*
