# Felipe Freire — Challenge 004: Estratégia Social Media

## Resumo executivo

Analisei 52.214 posts e não encontrei um vencedor acionável por plataforma, formato ou perfil de audiência. As diferenças são materialmente pequenas e o patrocínio não apresentou ganho detectável após controles: efeito de **−0,0010 p.p.** no engagement, com **IC95% de −0,0095 a +0,0074 p.p.**. Como o arquivo não contém custos, conversões ou receita, não é possível calcular ROI com honestidade.

**Decisão recomendada:** não ampliar patrocínio indiscriminadamente. Instrumentar custos e conversões, testar hipóteses controladas e escalar somente quando o efeito incremental superar o break-even aprovado.

## Respostas diretas ao desafio

| Pergunta | Resposta baseada nos dados | Ação |
|---|---|---|
| O que gera engagement? | Nenhuma variável disponível separa performance de forma material; diferenças máximas entre plataformas e formatos são 0,0105 e 0,0121 p.p. | Não realocar orçamento por rankings deste arquivo; testar hipóteses pré-especificadas. |
| Patrocínio funciona? | Não há ganho ajustado detectável em engagement, views, share rate ou views/follower. | Suspender expansão não experimental e exigir custo, outcome e comparador. |
| Qual audiência mais engaja? | Não há perfil validado; diferenças são pequenas e os dados de audiência são agregados por post. | Usar os cruzamentos apenas para formular testes, não para targeting causal. |
| O que não funciona? | Patrocínio indiscriminado, escolha por média, contratação por seguidores e chamar alcance de ROI. | Adotar política de testes incrementais com condições de parada. |

## O que fazer na segunda-feira

1. Congelar a expansão de campanhas sem custo, conversão e comparador definidos.
2. Adicionar `campaign_id`, fee, mídia, produção, reach único, cliques, conversões, receita/margem e janela de atribuição.
3. Aprovar métrica primária, efeito mínimo relevante e break-even.
4. Iniciar três testes controlados de conteúdo, cadência e patrocínio.
5. Usar o dashboard para monitoramento descritivo, sempre conferindo `n` e limitações.

O plano com owners, métricas e condições de decisão está em [`reports/30-day-experiment-plan.md`](reports/30-day-experiment-plan.md).

## Dashboard

O dashboard Streamlit responde explicitamente às perguntas do desafio, permite auditar audiência por plataforma/conteúdo/categoria e mantém tamanho amostral e limitações visíveis.

### [Abrir dashboard público](https://felipe-social-media-intelligence.streamlit.app/)

Não requer instalação ou login. O app publicado usa somente o asset analítico compacto versionado nesta submissão.

![Dashboard — visão geral](outputs/figures/dashboard/dashboard-01-visao-geral.png)

![Dashboard — audiência](outputs/figures/dashboard/dashboard-02-audiencia.png)

![Dashboard — exploração](outputs/figures/dashboard/dashboard-03-exploracao.png)

Para executar:

```powershell
cd submissions/felipe-freire
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_pipeline.ps1
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Instruções detalhadas: [`docs/technical-setup.md`](docs/technical-setup.md).

## Caminho de leitura

- [Solução completa](solution/README.md) — abordagem, resultados, limitações e uso de IA.
- [Relatório executivo](reports/executive-report.md) — respostas e recomendações em linguagem de negócio.
- [Plano operacional de 30 dias](reports/30-day-experiment-plan.md) — como produzir evidência para decidir investimento.
- [Registro de estratégia](reports/strategy-register.md) — owners, KPIs, guardrails e stop conditions.
- [Process log](process-log/README.md) — conversas, vídeos, imagens, erros e correções.
- [Veredicto de revisão](reports/review-verdict.md) — auditoria adversarial da entrega.

## Limitações essenciais

O dataset tem fortes sinais de geração sintética, não contém posts com engagement zero e possui inconsistências de creator. Também não inclui custos, conversões, receita, timezone ou frequência planejada. O desenho é observacional: os resultados descrevem este arquivo e não demonstram causalidade.

## Diferencial: uso inteligente de IA

A IA foi usada como sistema de trabalho, não como fonte de verdade. Claude Code e Codex foram separados em agentes/gates de planejamento, dados, análise, estatística, estratégia, dashboard, engenharia, escrita e revisão. Rankings aparentes foram rejeitados após validação; ML recebeu `NO-GO` por ausência de sinal; falhas `Connection closed mid-response` foram recuperadas por manifest sem presumir etapas concluídas.

A arquitetura, os prompts e o protocolo de handoff estão em [`docs/agent-architecture.md`](docs/agent-architecture.md), [`.claude/agents/`](.claude/agents/) e [`docs/handoff-protocol.md`](docs/handoff-protocol.md).

## Sobre mim

- **Nome:** Felipe de Oliveira Freire
- **Atuação:** Cientista/Analista de Dados
- **LinkedIn:** https://www.linkedin.com/in/felipe-freire-659615284/
- **PR:** https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/91
- **Dashboard público:** https://felipe-social-media-intelligence.streamlit.app/

---

**Felipe de Oliveira Freire**

*Cientista/Analista de Dados*
