# Checklist de aderencia ao Challenge 002

## Requisitos obrigatorios

| Requisito | Status | Onde esta |
|---|---|---|
| Diagnostico operacional com Dataset 1 | Concluido | `operational-diagnosis.md`, painel admin |
| Gargalos por canal, prioridade e tipo | Concluido | `operational-diagnosis.md` |
| Combinacoes criticas | Concluido | `operational-diagnosis.md` |
| Analise de satisfacao | Concluido com ressalva | `operational-diagnosis.md` |
| Desperdicio em horas | Concluido | `operational-diagnosis.md` |
| Uso dos dois datasets | Concluido | Dataset 1 para diagnostico; Dataset 2 para classificador |
| Proposta do que automatizar | Concluido | `automation-blueprint.md` |
| Proposta do que nao automatizar | Concluido | `automation-blueprint.md` |
| Fluxo pratico com IA e humano | Concluido | `automation-blueprint.md`, `flask_app.py` |
| Protótipo funcional | Concluido | `flask_app.py` |
| Process log | Concluido | `process-log/ai-workflow.md` |

## Critérios de qualidade

### Usou ambos os datasets?

Sim.

- Dataset 1: diagnostico operacional, backlog, CSAT, tempos, assuntos recorrentes.
- Dataset 2: treino e validacao do classificador de tickets.

### O diagnostico tem numeros concretos?

Sim.

Principais numeros:

- 8.469 tickets analisados.
- 5.700 abertos ou pendentes.
- 2.769 fechados com CSAT e resolucao.
- mediana corrigida de resolucao: 11,6h.
- p90 corrigido: 21,7h.
- 8.733,5 horas acima da mediana.
- pior combinacao de CSAT relevante: `Phone + High + Refund request`, CSAT 2,29.

### A proposta de automacao e realista?

Sim. A proposta nao automatiza 100% da operacao.

Automatiza:

- deflexao de duvidas simples;
- busca em conhecimento existente;
- classificacao;
- priorizacao;
- abertura de ticket enriquecida;
- sugestao de rota.

Mantem humano em:

- criticidade alta;
- reembolso;
- cancelamento;
- perda de dados;
- baixa confianca;
- excecao de politica;
- casos sensiveis.

### O prototipo funciona com dados reais?

Sim.

O app usa:

- dados historicos do Dataset 1 para analise e base inicial;
- Dataset 2 para treinar classificador;
- SQLite local para tickets novos e resolucoes humanas no demo.

### A comunicacao e executiva?

Sim. O README principal resume problema, achados, recomendacoes, limitacoes e impacto. Os detalhes tecnicos ficam nos documentos de apoio.

## Pontos de diferenciacao

1. A solucao tenta evitar o ticket antes de abrir chamado, nao apenas classificar depois.
2. Tickets abertos ja carregam contexto, categoria, confianca e prioridade.
3. O admin consegue resolver tickets e alimentar uma base de conhecimento.
4. O prototipo inclui autenticacao simples para publicacao controlada.
5. Ha guardrails de custo e prompt injection para uso com OpenAI API.
6. A entrega documenta problemas reais de qualidade dos dados, em vez de esconder inconsistencias.

## Riscos assumidos e mitigacoes

| Risco | Mitigacao |
|---|---|
| Dataset 1 menor que o briefing | Documentado como limitacao |
| Timestamps inconsistentes | Regra de correcao documentada |
| Texto sintetico/ruidoso | Uso limitado para demo/RAG, nao conclusao sem ressalva |
| Dataset 2 sem chave com Dataset 1 | Usado como base complementar de classificacao, nao join |
| API OpenAI com custo | Limites de input, chamadas por sessao e output |
| Prompt injection | Bloqueios simples e prompt de sistema restritivo |
| SQLite local em deploy | Adequado para demo; recomendacao de Postgres/Supabase em producao |
