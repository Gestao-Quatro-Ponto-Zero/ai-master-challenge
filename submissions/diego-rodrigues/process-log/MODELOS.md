# Inventário de modelos

> Um modelo sem versão não é reproduzível e não passa numa auditoria. Preencha a versão exata, não a família.

| Modelo (id exato) | Papel neste entregável | Como foi acessado | Dado sensível exposto | Custo estimado |
|---|---|---|---|---|
| `claude-haiku-5-5` (**planejado para a geração dos briefings, não executado**: a primeira chamada à API foi recusada por falta de créditos, e nenhum texto da IA foi publicado. Limites previstos: 250 e 150 tokens de saída, teto de 60 chamadas por execução. Dado previsto: só dados fictícios do dataset CC0) | sessões registradas no diário: Tarefa 0; verificações e correções pontuais (Tarefas 1, 3, 6–8 e correções); Tarefa 4 (`pontuar`), Tarefa 5 (`explicar`), Tarefa 6 (`build`), Tarefa 7 (`avaliacao`), Tarefa 8 (`drift`); Tarefa 13 etapa 1 (deploy) e correção do 404 | Claude Code (terminal) | não — só dataset público CC0 | incluído na assinatura |
| `claude-sonnet-4-6` | Tarefa 1 (`carregar`), Tarefa 2 (`janela`) | Claude Code (terminal) | não — só dataset público CC0 | incluído na assinatura |
| `claude-sonnet-5-5` | Tarefa 3 (`aprender`), Tarefa 11 (três telas) | Claude Code (terminal) | não — só dataset público CC0 | incluído na assinatura |
| `claude-sonnet-5` | Tarefa 9 (`ia/`, validador e templates), Tarefa 10 (`run.py`), Tarefa 12 (documentos de operação e experimento), Tarefa 13 etapas 3 e 4 (README e limitações) | Claude Code (terminal) | não — só dataset público CC0 | incluído na assinatura |
| `claude-opus-5` | Tarefa 13 etapa 2 (resumo executivo) | Claude Code (terminal) | não — só dataset público CC0 | incluído na assinatura |
| `claude-haiku-4-5-20251001` | Tarefa 2, nota de atribuição ao PR #242 | Claude Code (terminal) | não — só dataset público CC0 | incluído na assinatura |

Baselines sem ferramenta (Tarefa 0, passo 4), para comparar propostas sem o dado na mão: Nemotron-3.5-lightning (via OpenRouter, gratuito), Gemini 3.1 (interface web, colado pelo Diego), ChatGPT 6.1 Sol (interface web, colado pelo Diego). Nenhum deles entrou no produto.

Os modelos foram trocados pelo Diego entre etapas, por escolha de custo e de qualidade. A coluna "sessões" reproduz o que o diário registra no início de cada sessão; trocas no meio de uma mesma sessão não aparecem nele.

## Fase de planejamento (antes do fork)

Antes de abrir o repositório do desafio, o plano foi escrito e revisado inteiramente dentro do Claude Code, com modelos diferentes dos usados na construção.

| Modelo (id exato) | Papel | Como foi acessado | Dado sensível exposto | Custo estimado |
|---|---|---|---|---|
| `claude-fable-5-1` | primeiro plano de ação para o desafio 003, a partir da descrição da vaga | Claude Code (terminal) | não | incluído na assinatura |
| `claude-fable-5-2`, esforço extra-alto | comparação dos desafios 03 e 04 contra os PRs já enviados; revisão do plano inicial por três ângulos (engenharia de dados, software, operação comercial), origem do plano v2 | Claude Code (terminal) | não | incluído na assinatura |
| `claude-fable-5-2`, `claude-opus-5`, `claude-sonnet-4-6` | plano v2 detalhado e análise exploratória inicial | Claude Code (terminal) | não | incluído na assinatura |
| `claude-haiku-5-5` | HTML interno com as etapas, o passo a passo e o modelo recomendado para cada uma | Claude Code (terminal) | não | incluído na assinatura |
| Perplexity | pesquisa em fontes abertas sobre a cultura comercial e os arquétipos de vendedor, insumo das personas sintéticas | interface web, colado pelo Diego | não — fontes públicas | gratuito |

Conversas exportadas: [chat-exports/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/chat-exports). Documentos que essa fase produziu: [planejamento/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento).

## Revisão final da submissão

| Modelo (id exato) | Papel | Como foi acessado | Dado sensível exposto | Custo estimado |
|---|---|---|---|---|
| ChatGPT Sol 5.6, modo de raciocínio estendido ("think deeper") | revisão externa da entrega contra o pedido do desafio, devolveu um plano de 20 prompts de ajuste | interface web, arquivos e prints enviados manualmente pelo Diego | dados do produto (CSVs fictícios, CC0) e prints da demo; nenhum dado pessoal | gratuito/assinatura pessoal |
| `claude-opus-5-5`, `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-sonnet-5` | auditoria do repositório, triagem do plano de 20 prompts (adotar/adaptar/descartar), execução do README, dos documentos de apoio, deste process log e do PR | Claude Code (terminal) | não | incluído na assinatura |
| `claude-opus-5-5` | verificação independente dos números, como subagente revisor; mesma família dos modelos que implementaram, o que o protocolo de `verificacao/LEIA.md` desaconselha — ver a ressalva no relatório | Claude Code (terminal, subagente) | não — só CSVs públicos e documentos da submissão | incluído na assinatura |

## Informantes sintéticos (personas, usuários simulados, agentes entrevistados)

Um agente que você entrevista é um modelo, e entra neste inventário como qualquer outro — com uma coluna a mais, porque o risco dele é diferente: ele devolve resposta fluente e cordial para qualquer pergunta, e se foi construído a partir dos mesmos dados que você analisou, a "confirmação" que ele dá é circular.

| Agente | Papel | Construído a partir de | É fonte de fato? | Como a confiabilidade foi medida |
|---|---|---|---|---|
| Discovery Personas Sintéticas Vendas G4 · Microsoft 365 Copilot (Premium), modelo GPT Sol 6.1 · versão exata: não exposta pela interface (configuração de 11/11/2026) | informante sintético de discovery, quatro arquétipos (Caio, Helena, André, Renata) | pesquisa de fontes abertas sobre a G4, Perplexity, 11/11/2026 (`fontes-cultura-g4.md`) + fatos conferidos nos CSVs (`agente-personas-config.md`) | **não** — nenhuma resposta dele vira número no entregável; nenhum número do produto vem dele | números do contexto conferidos contra `data/` em 11/11/2026; perguntas de calibração com resposta já conhecida por script, a fazer; acertos e invenções em `onde-a-ia-errou.md` |

Regras ao usar informante sintético:

1. **Separe os modos** em conversas distintas: o agente como personagem (processo e comportamento) e o agente como respondente sobre a base (só calibração). Misturar os dois produz validação circular.
2. **Pré-registre** o que você espera ouvir, e faça commit antes da primeira pergunta. Sem isso, toda resposta confirma o que você já achava.
3. **Nenhuma resposta vira fato.** Vira premissa, com dono e com o teste real que a resolveria.
4. **Rotule no entregável.** "Discovery ensaiado com personas sintéticas", nunca "entrevistei usuários".

## Dado sensível: o que não entrou em prompt nenhum

Liste explicitamente o que foi mantido fora. Declarar o limite vale tanto quanto respeitá-lo.

-
-

## Anonimizações

Quando algo precisou ser anonimizado para entrar num prompt, registre o quê e como.

| O que | Como foi anonimizado | Onde foi usado |
|---|---|---|
| | | |

## Onde a IA não foi usada, e por quê

A decisão de não automatizar é parte do julgamento. Exemplos: encerrar um registro no CRM do cliente, aprovar um número que vai para um executivo, escrever na voz de alguém sem revisão.

-
-
