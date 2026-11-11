# Registro de uso de IA

> Índice do registro deste entregável. Os números de contagem saem de `python3 registrar.py --conferir`.

**Entregável:** Lead Scorer — priorização de deals para o Challenge 003 (Gestão Quatro Ponto Zero)
**Período:** 11/11/2026 (início e entrega, numa mesma data)
**Quem conduziu:** Diego Rodrigues

## Ferramentas e por quê

| Ferramenta | Para quê | Por que esta e não outra |
|---|---|---|
| Claude Code, seis modelos Claude (Sonnet 4.6, Sonnet 5, Sonnet 5.5, Opus 5, Haiku 5.5, Haiku 4.5) | motor, testes, backtest, telas, deploy, documentos e process log | roda no terminal com acesso aos arquivos e ao git, então cada iteração fica no histórico; a troca de modelo foi feita pelo Diego entre etapas, por custo e qualidade |
| Microsoft 365 Copilot (Premium), GPT Sol 6.1 | agente de persona do discovery, informante sintético — **não é fonte de fato** | personas de arquétipo para ensaiar perguntas; a confiabilidade foi medida com calibração de resposta já conhecida |
| Nemotron-3.5-lightning, Gemini 3.1, ChatGPT 6.1 Sol | baselines sem ferramenta (Tarefa 0) | comparar o que um modelo propõe sem o dado na mão, para mostrar o que o dado desmente |

Inventário com versão exata, sessões e custo: [MODELOS.md](MODELOS.md).

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

Cada item com o que foi proposto, o mecanismo que pegou e o teste ou a verificação que fixa: [onde-a-ia-errou.md](onde-a-ia-errou.md). Destaques: o vazamento do campo de conta, que dava sinal falso ao vendedor (0,012 virou 0,141 ao filtrar); a base de 22% que era taxa de acerto e não taxa de decisão (correta: 17,3%); e a atribuição da regra do trimestre a um PR que não tinha essa regra, nem verificado.

## O que eu acrescentei

O julgamento que a IA sozinha não traria, com as rejeições e as perguntas que mudei: [o-que-eu-acrescentei.md](o-que-eu-acrescentei.md).

## Verificação independente

Protocolo, script e relatório: [verificacao/](verificacao/). **Pendente:** é a etapa 6 da Tarefa 13 e ainda não foi feita. O `LEIA.md` existe; o relatório não.

## Evidências

- Diário por sessão, gravado na hora: [diario.md](diario.md)
- Prints das três telas, em 1366 e 390 px: `screenshots/`
- Histórico git: `git log --oneline` (branch `submission/diego-rodrigues`)
- Saída dos scripts de número: [numeros-saida.txt](../docs/numeros-saida.txt)
