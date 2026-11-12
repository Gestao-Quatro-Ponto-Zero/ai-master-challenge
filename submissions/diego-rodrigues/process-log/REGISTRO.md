# Registro de uso de IA

> Índice do registro deste entregável. Os números de contagem saem de `python3 registrar.py --conferir`.

**Entregável:** Lead Scorer — priorização de deals para o Challenge 003 (Gestão Quatro Ponto Zero)
**Período:** 11/11/2026 (início e entrega, numa mesma data)
**Quem conduziu:** Diego Rodrigues

## Ferramentas e por quê

| Ferramenta | Para quê | Por que esta e não outra |
|---|---|---|
| Claude Code, nove modelos Claude (Fable 5.1, Fable 5.2, Sonnet 4.6, Sonnet 5, Sonnet 5.5, Opus 5, Opus 5.5, Haiku 5.5, Haiku 4.5) | plano, revisão do plano, motor, testes, backtest, telas, deploy, documentos, verificação independente e process log | roda no terminal com acesso aos arquivos e ao git, então cada iteração fica no histórico; a troca de modelo foi feita pelo Diego entre etapas, por custo e qualidade |
| Microsoft 365 Copilot (Premium), GPT Sol 6.1 | agente de persona do discovery, informante sintético — **não é fonte de fato** | personas de arquétipo para ensaiar perguntas; a confiabilidade foi medida com calibração de resposta já conhecida |
| Perplexity | pesquisa em fontes abertas sobre a cultura comercial e os arquétipos de vendedor, antes de montar as personas | fontes públicas, para não supor o comportamento do time comercial |
| Nemotron-3.5-lightning, Gemini 3.1, ChatGPT 6.1 Sol | baselines sem ferramenta (Tarefa 0) | comparar o que um modelo propõe sem o dado na mão, para mostrar o que o dado desmente |
| ChatGPT Sol 5.6, modo de raciocínio estendido | revisão externa da submissão quase pronta, contra o pedido do desafio | segundo olhar, de outra família de modelo, depois que a construção estava terminada |

Inventário com versão exata, sessões e custo: [MODELOS.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/MODELOS.md).

## Workflow

1. **Procedência e recorte temporal** (Tarefa 1): carga, normalização, qualidade e recorte sem vazamento de futuro, com TDD.
2. **Janela e tabela de destino aprendidas** (Tarefas 2 e 3): nenhum limiar escrito à mão; a tabela trata deals abertos em risco sem viés de sobrevivência.
3. **Fila, ordem e explicação** (Tarefas 4 e 5): cada fila tem o motivo mostrado ao vendedor.
4. **Contrato JSON e relatório de desvio** (Tarefas 6 e 8): build determinístico e alerta quando o que foi aprendido muda.
5. **Backtest e permutação de atributos** (Tarefa 7): cinco políticas com a mesma data de corte, IC por bootstrap de vendedor, e o vazamento do campo de conta que encontrei e corrigi.
6. **Briefing, servidor e telas** (Tarefas 9 a 11): briefing por template validado contra os fatos; `run.py`; três telas, corrigidas depois de olhar os próprios prints.
7. **Operação, design e experimento** (Tarefa 12): cinco documentos citando as transcrições do discovery, não suposição.
8. **Deploy, resumo, limitações e README** (Tarefa 13): demo publicada em https://lead-scorer-diego.vercel.app; resumo executivo com a conta de horas como premissa declarada.

## Contagem

| | |
|---|---|
| Sessões de trabalho | 27 (no diário) |
| Iterações registradas | 26 |
| Erros da IA pegos e corrigidos | 16 — 5 das personas sintéticas (Tarefa 0B) e 11 meus nas Tarefas 1 a 13, pegos por verificação. O `--conferir` conta só os 5 registrados como `--erro` no diário; os 11 seguintes estão em `onde-a-ia-errou.md` |
| Modelos usados | 6 modelos Claude Code, 1 agente de persona (GPT Sol 6.1) e 3 baselines (Nemotron-3.5-lightning, Gemini 3.1, ChatGPT 6.1 Sol) |

## Onde a IA errou

Cada item com o que foi proposto, o mecanismo que pegou e o teste ou a verificação que fixa: [onde-a-ia-errou.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/onde-a-ia-errou.md). Destaques: o vazamento do campo de conta, que dava sinal falso ao vendedor (0,012 virou 0,141 ao filtrar); a base de 22% que era taxa de acerto e não taxa de decisão (correta: 17,3%); e a atribuição da regra do trimestre a um PR que não tinha essa regra, nem verificado.

## O que eu acrescentei

O julgamento que a IA sozinha não traria, com as rejeições e as perguntas que mudei: [o-que-eu-acrescentei.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/o-que-eu-acrescentei.md).

## Verificação independente

**Feita.** Protocolo, script e relatório: [verificacao/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/verificacao). O revisor (`claude-opus-5-5`, como subagente) escreveu código próprio a partir dos quatro CSVs, sem importar `solution/motor` nem `solution/avaliacao`, e recalculou cada número citado — todos bateram. É a mesma família dos modelos que implementaram, o que o protocolo do `LEIA.md` desaconselha; essa ressalva está registrada no próprio relatório. Quatro ressalvas foram apontadas e corrigidas no commit `66171cb`.

## Evidências

- Diário por sessão, gravado na hora: [diario.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/diario.md)
- Prints das três telas, em 1366 e 390 px: `screenshots/`
- Histórico git: `git log --oneline` (branch `submission/diego-rodrigues`)
- Saída dos scripts de número: [numeros-saida.txt](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/numeros-saida.txt)
