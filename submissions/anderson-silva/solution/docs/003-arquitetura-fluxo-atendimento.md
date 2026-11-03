# Arquitetura do fluxo de atendimento: registros por etapa

- **Status:** versão final da submissão, 2026-11-03. Campo `auto_ack_at` acrescentado no item 153.
- **Origem:** conversa registrada nos itens 58 a 66 do [audit trail](../../process-log/002-audit-trail.md). Faz parte da proposta de melhoria da captura de dados do suporte.
- **Autoria:**
  - Direção e correções da pessoa candidata: registrar o fechamento de forma explícita, tratar o suporte como uma sequência de tentativas e interações, exigir começo, meio e fim em tudo, e a observação sobre a base de conhecimento.
  - Estrutura, etapas e nomes dos campos: propostos pela IA e aprovados pela pessoa candidata.

## Por que esta arquitetura existe

O Dataset 1 do desafio não tem data e hora de abertura do ticket. As colunas "First Response Time" e "Time to Resolution" guardam data e hora, não duração, e em 1.365 dos 2.769 tickets fechados a resolução vem antes da primeira resposta. Com esse dado, não dá para medir quanto o cliente esperou nem quanto a equipe trabalhou. Esta arquitetura define o que cada etapa do atendimento deve registrar e para quê.

Quando o suporte resolve de primeira, o fluxo passa uma única vez pela etapa de tentativa. Quando não resolve, ele volta à tentativa quantas vezes for preciso, e cada passagem fica registrada com começo, meio e fim.

## Três níveis, cada um com começo, meio e fim

| Nível | Começo | Meio | Fim |
|---|---|---|---|
| Ticket | Abertura | As tentativas | Fechamento |
| Tentativa | Ação iniciada | Interações e esperas | Resultado |
| Interação (mensagem, chamada ou chat) | Início do contato | Conteúdo | Término do contato |

Além disso, toda mudança de etapa grava um evento no **histórico de status**: `status_from`, `status_to`, `changed_at` e `changed_by`.

## Fluxograma

```
 CLIENTE ABRE O TICKET
        │
        ▼
 [1] ABERTURA ─────────────────► opened_at, canal, público ou privado,
        │                         produto, tipo, prioridade, descrição,
        │                         auto_ack_at (confirmação automática)
        ▼
 [2] TRIAGEM E ATRIBUIÇÃO ─────► assigned_at, fila, atendente, nível
        │
        ▼
 [3] PRIMEIRA RESPOSTA ────────► first_response_at (só resposta humana)
        │
        ▼
 ┌─► [4] TENTATIVA n
 │      ├─ começo ─────────────► attempt_started_at, ação, responsável, nível
 │      ├─ meio ───────────────► interações (início, fim, autor, canal)
 │      │                         e esperas do cliente (histórico de status)
 │      └─ fim ────────────────► attempt_ended_at, resultado, motivo
 │      │
 │      ▼
 │   Resolveu?
 │      │ não: nova tentativa, escalonamento ou transferência
 └──────┘
        │ sim
        ▼
 [5] RESOLUÇÃO ────────────────► resolved_at, código de resolução,
        │                         categoria confirmada, quem resolveu
        ▼
 [6] FECHAMENTO ───────────────► closed_at, motivo do fechamento
        │
        ▼
 [7] PESQUISA DE SATISFAÇÃO ───► survey_sent_at, survey_answered_at, nota
        │
        ▼
 O problema voltou?
        │ sim
        ▼
 [8] REABERTURA ───────────────► reopened_at, motivo; volta para [4]

 Se o problema não voltou: FIM.

 Em toda passagem de etapa: histórico de status
```

## O que cada etapa registra e para quê

As finalidades remetem às três perguntas do Diretor: (1) onde o fluxo trava, (2) o que impacta o CSAT e (3) quanto se perde em horas e custo.

| Etapa | Registro | Finalidade |
|---|---|---|
| 1. Abertura | `opened_at`, canal, público ou privado, produto, tipo, prioridade, descrição | Inicia o relógio da espera do cliente. Permite separar os tickets por canal, prioridade e tipo (pergunta 1). Mede o risco de exposição. |
| 1. Abertura, confirmação | `auto_ack_at` | Registra a confirmação automática de recebimento. Não conta como primeira resposta, para não esconder o tempo de fila. |
| 2. Triagem e atribuição | `assigned_at`, fila, atendente anonimizado, nível | Mede o tempo parado na fila (pergunta 1). É a base do custo por nível (pergunta 3). |
| 3. Primeira resposta | `first_response_at`, só para resposta de uma pessoa | Mede o tempo até a primeira resposta humana (perguntas 1 e 2). |
| 4. Tentativa, começo | `attempt_number`, `attempt_started_at`, ação, responsável (pessoa ou automação), nível | Mostra quantas tentativas cada caso exige e quais ações se repetem, o que indica candidatos à automação. |
| 4. Tentativa, meio | Interações com `interaction_started_at`, `interaction_ended_at`, autor e canal; esperas do cliente pelo histórico de status | Dá o tempo de trabalho efetivo (pergunta 3). Separa a espera da equipe da espera do cliente (pergunta 1). Mostra a troca de canal (pergunta 2). |
| 4. Tentativa, fim | `attempt_ended_at`, resultado (resolveu, não resolveu, escalonou, transferiu), motivo | Mostra onde e por que as tentativas falham, e quantos casos se resolvem na primeira tentativa. |
| 5. Resolução | `resolved_at`, código de resolução, categoria confirmada, quem resolveu | Mostra o que se repete e pode ser automatizado, e qual é o efeito real da automação. |
| 6. Fechamento | `closed_at`, motivo (confirmado pelo cliente, prazo esgotado, cancelado) | Dá o tempo total e separa resolver de fechar. |
| 7. Pesquisa | `survey_sent_at`, `survey_answered_at`, nota | Mostra o que impacta o CSAT e quem deixa de responder (pergunta 2). |
| 8. Reabertura | `reopened_at`, motivo | Mede o retrabalho e as resoluções que não eram de verdade. |
| Toda passagem | Histórico de status | Mostra onde o ticket fica parado e quanto tempo passa em cada status. |

## Calculados pelo sistema, nunca digitados

| Indicador | Origem |
|---|---|
| `minutes_to_first_response`, `minutes_to_resolution`, `minutes_to_close` | Diferença entre os marcos |
| `attempts_count` | Contagem de tentativas; igual a 1 quando resolveu de primeira |
| `interactions_count`, troca de canal | Registros de interação |
| Tempo de trabalho efetivo | Soma do início ao fim das interações da equipe |
| Custo do ticket | Tempo de trabalho multiplicado pelo custo por hora do nível (tabela do financeiro) |
| Espera da equipe e espera do cliente | Histórico de status |
| `reopen_count` | Contagem de reaberturas |

## Regras de validação

- A ordem dos marcos é sempre abertura, primeira resposta, resolução e fechamento, nesta sequência.
- `first_response_at` só registra resposta de uma pessoa. A confirmação automática fica em `auto_ack_at` e nunca entra em `minutes_to_first_response`.
- Toda tentativa e toda interação têm começo e fim, e o fim nunca vem antes do começo.
- Um ticket não é resolvido nem fechado enquanto houver tentativa em aberto.
- Não existe resolução sem código de resolução.

## Limitação: esta versão ainda é superficial

Aqui os registros servem para medir. Eles poderiam ir além: cada problema, cada tentativa e cada solução poderia alimentar uma base de conhecimento, por exemplo com RAG (busca em documentos para embasar a resposta de uma IA) ou outros métodos. Essa base se alimentaria sozinha a cada atendimento e aprimoraria a automação de algumas respostas. O ganho seria uma resposta mais rápida, automática e assertiva.

Esse aprofundamento não é objetivo do desafio. Fica registrado aqui, sem desenvolvimento.
