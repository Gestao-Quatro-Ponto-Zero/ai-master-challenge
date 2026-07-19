# Blueprint de automacao com IA

## Objetivo

Reduzir carga operacional do suporte em duas frentes:

1. **Antes do ticket:** resolver ou defletir duvidas simples com IA/RAG.
2. **Depois do ticket:** abrir chamados melhor qualificados, com categoria, prioridade, confianca e contexto para o humano.

A proposta evita a armadilha de automatizar tudo. IA atua como camada de suporte e triagem; humano continua responsavel por casos sensiveis, ambiguos ou de alto risco.

---

## Modelo usado no prototipo

- Fonte de treino: Dataset 2, `all_tickets_processed_improved_v3.csv`, com 47.837 tickets rotulados.
- Algoritmo: TF-IDF com unigramas/bigramas + regressao logistica balanceada.
- Validacao: holdout estratificado de 20%.
- Resultado: accuracy de 86,5% e macro F1 de 86,6%.

Esse modelo foi escolhido por ser simples, local, explicavel e suficiente para demonstrar triagem automatizada sem depender de uma API externa.

---

## Fluxo proposto

```text
Cliente entra
|
|-- Descreve duvida em linguagem natural
|
|-- IA/RAG consulta base de conhecimento
|     |-- FAQ interno derivado dos assuntos recorrentes
|     |-- resolucoes humanas salvas no prototipo
|
|-- Se a resposta tem confianca suficiente:
|     |-- cliente resolve sem abrir ticket
|
|-- Se nao resolveu ou o caso exige humano:
|     |-- cliente abre ticket
|     |-- sistema envia contexto da conversa
|     |-- classificador sugere categoria
|     |-- regra sugere prioridade
|     |-- admin recebe fila qualificada
|
|-- Humano resolve
|
|-- Resolucao humana alimenta a base de conhecimento
```

---

## O que automatizar

| Caso | Automacao recomendada | Motivo |
|---|---|---|
| Duvidas simples recorrentes | Resposta via IA/RAG antes do ticket | Reduz volume e tempo de espera |
| Problemas com resposta conhecida | Recuperar caso similar | Reaproveita conhecimento operacional |
| Novo ticket aberto pelo cliente | Classificacao automatica | Reduz triagem manual |
| Ticket com informacao incompleta | Coleta de contexto antes de escalar | Melhora qualidade do atendimento humano |
| Resolucao humana validada | Entrada na base de conhecimento | Aumenta reaproveitamento futuro |
| Alta confianca e baixo risco | Roteamento assistido | Acelera fila sem tirar humano do processo |

---

## O que nao automatizar

| Caso | Por que manter humano |
|---|---|
| Prioridade critica | Alto risco operacional e reputacional |
| Reembolso sensivel | Pode envolver politica, contrato e impacto financeiro |
| Cancelamento | Sinal de churn; exige retencao e julgamento |
| Perda de dados | Alto risco e potencial impacto grave |
| Baixa confianca da IA | Evita resposta errada com aparencia de certeza |
| Excecao de politica | Precisa autonomia humana |
| Cliente muito insatisfeito | Exige empatia, negociacao e contexto |

---

## Regras do prototipo

### Guardrails de uso

- Limite de caracteres por pergunta.
- Limite de chamadas de IA por sessao.
- Limite de tokens de resposta.
- Bloqueio simples de prompt injection.
- Fallback local quando nao existe `OPENAI_API_KEY`.

### Decisao operacional

- Casos com termos de alto risco como `refund`, `cancel`, `data loss`, `security` ou `critical`: prioridade `Critical`.
- Baixa confianca do classificador: prioridade maior e revisao humana.
- Resposta da IA sem base suficiente: recomendar abertura de ticket.
- Ticket aberto: sempre preserva pergunta original, resposta da IA, categoria, confianca e prioridade sugerida.

---

## Painel admin

O admin ve:

- tickets historicos;
- backlog;
- CSAT medio;
- mediana corrigida de resolucao;
- macro F1 do classificador;
- canais com maior tempo medio;
- assuntos recorrentes;
- fila de tickets abertos no prototipo;
- resolucoes humanas salvas na base de conhecimento.

---

## ROI estimado

Nos tickets fechados, ha 8.733,5 horas acima da mediana de resolucao. Essa nao e uma economia garantida, mas e um teto de desperdicio operacional observado.

O impacto esperado vem de:

- tickets simples evitados antes de entrar na fila;
- menor tempo de triagem;
- tickets abertos com contexto melhor;
- menos reencaminhamento;
- reaproveitamento de resolucoes humanas.

Exemplo de formula para piloto:

```text
economia = tickets defletidos * minutos economizados / 60 * custo hora agente
```

---

## Como escalar em producao

1. Corrigir instrumentacao dos timestamps.
2. Definir taxonomia real de suporte.
3. Migrar SQLite para Postgres/Supabase.
4. Criar base vetorial para RAG.
5. Revisar resolucoes humanas antes de entrarem na base.
6. Medir deflection rate, escalation rate, CSAT, reopen rate e override rate.
7. Retreinar classificador periodicamente com dados reais da operacao.
8. Liberar automacoes gradualmente por categoria e confianca.
