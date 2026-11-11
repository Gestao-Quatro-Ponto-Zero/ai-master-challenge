# Inventário de modelos

> Um modelo sem versão não é reproduzível e não passa numa auditoria. Preencha a versão exata, não a família.

| Modelo (id exato) | Papel neste entregável | Como foi acessado | Dado sensível exposto | Custo estimado |
|---|---|---|---|---|
| `claude-haiku-5-5` | implementação, testes, análise (sessão da Tarefa 0) | Claude Code (terminal) | não — só dataset público CC0 | incluído na assinatura |

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
