# Submissão — Felipe de Oliveira Freire — Challenge 004

## Sobre mim

- **Nome:** Felipe de Oliveira Freire
- **LinkedIn:** [linkedin.com/in/felipe-freire-659615284](https://www.linkedin.com/in/felipe-freire-659615284/)
- **Challenge escolhido:** Challenge 004 — Estratégia Social Media

---

## Executive Summary

Analisei 52.214 publicações com um pipeline reproduzível e transformei os resultados em um [dashboard público](https://felipe-social-media-intelligence.streamlit.app/) orientado à decisão. Não encontrei um vencedor acionável por plataforma, formato ou audiência; as diferenças observadas são pequenas e o efeito ajustado do patrocínio foi de **−0,0010 p.p.**, com **IC95% de −0,0095 a +0,0074 p.p.** Como o dataset não contém custos, conversões ou receita, ele não permite calcular ROI nem sustentar causalidade. A principal recomendação é interromper a expansão indiscriminada, instrumentar o funil e escalar somente experimentos cujo efeito incremental supere um break-even previamente aprovado.

---

## Solução

### Abordagem

Comecei pelo problema de negócio e pelo contrato dos dados, antes de procurar rankings ou construir modelos. A execução seguiu cinco gates:

1. validei schema, qualidade, duplicidades, valores ausentes e sinais de dados sintéticos;
2. construí uma camada processada reproduzível, com contratos e testes;
3. comparei plataforma, formato, patrocínio e audiência usando tamanho amostral, efeito prático, intervalos de confiança e modelos ajustados;
4. submeti Machine Learning a um gate de utilidade e registrei `NO-GO`, pois o sinal disponível não justificava um modelo preditivo;
5. traduzi a evidência em decisões, experimentos, guardrails e um dashboard para o Head de Marketing.

A implementação, os comandos e a rastreabilidade técnica estão na [solução completa](solution/README.md) e no [guia de execução](docs/technical-setup.md).

### Resultados / Findings

| Pergunta do desafio | Resposta baseada nos dados | Implicação prática |
|---|---|---|
| O que gera engagement? | Nenhuma variável disponível separa performance de forma material; as diferenças máximas entre plataformas e formatos são **0,0105** e **0,0121 p.p.** | Não realocar orçamento com base nos rankings deste arquivo. |
| Patrocínio funciona? | Não há ganho ajustado detectável em engagement, views, share rate ou views/follower. | Suspender expansão não experimental e exigir custo, outcome e comparador. |
| Qual audiência mais engaja? | Não há perfil validado; as diferenças são pequenas e a audiência é uma categoria agregada do post, não um atributo individual. | Usar os cruzamentos para formular testes, não para targeting causal. |
| O que não funciona? | Patrocínio indiscriminado, escolha por média, contratação por seguidores e tratar alcance como ROI. | Adotar testes incrementais com critérios de escala e parada. |

O dashboard torna essas respostas explícitas, mantém `n` e limitações visíveis e oferece um briefing editável de experimento com métrica, break-even, guardrail e regra de decisão.

### [Abrir o dashboard público](https://felipe-social-media-intelligence.streamlit.app/)

Não requer instalação ou login.

![Dashboard — visão geral](outputs/figures/dashboard/dashboard-01-visao-geral.png)

![Dashboard — audiência](outputs/figures/dashboard/dashboard-02-audiencia.png)

![Dashboard — exploração](outputs/figures/dashboard/dashboard-03-exploracao.png)

Documentos complementares:

- [Relatório executivo](reports/executive-report.md)
- [Plano operacional de 30 dias](reports/30-day-experiment-plan.md)
- [Registro de estratégia, owners, KPIs e stop conditions](reports/strategy-register.md)

### Recomendações

Em ordem de prioridade, a empresa deveria:

1. **Congelar a expansão sem mensuração:** não ampliar campanhas que não tenham custo, conversão e comparador definidos.
2. **Instrumentar o funil:** registrar `campaign_id`, mídia, fee, produção, alcance único, cliques, conversões, receita/margem e janela de atribuição.
3. **Aprovar a regra de decisão:** definir métrica primária, efeito mínimo relevante, break-even e guardrails antes de observar o resultado.
4. **Executar três testes controlados:** conteúdo, cadência e patrocínio, cada um com owner, amostra e condição de parada.
5. **Escalar apenas evidência incremental:** usar o dashboard como monitoramento descritivo e promover somente variantes cujo limite inferior do efeito supere o break-even.

### Limitações

- O dataset apresenta fortes sinais de geração sintética, não contém posts com engagement zero e possui inconsistências de creator.
- Não há custos, conversões, receita, timezone ou frequência planejada; portanto, ROI e eficiência econômica não podem ser calculados.
- A audiência é agregada por publicação e não representa o perfil individual de quem interagiu.
- O desenho é observacional. Os resultados descrevem este arquivo e não demonstram causalidade.
- Não recomendo generalizar os números para campanhas futuras sem validação em dados reais e experimentos controlados.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** A IA foi usada como sistema de trabalho e contraponto, não como fonte de verdade; decisões foram mantidas somente quando sustentadas pelos dados e pelos gates de qualidade.

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code | Planejamento inicial, exploração, implementação do pipeline e coordenação dos agentes especialistas. |
| Codex | Continuidade após interrupções, verificação independente, integração, testes, dashboard e revisão da entrega. |
| ChatGPT | Discussão de hipóteses, arquitetura multiagentes e crítica do processo; a conversa foi preservada nas evidências. |
| Gemini | Validação complementar de ideias e comparação de alternativas; a conversa compartilhada foi registrada. |

### Workflow

**Quantidade de iterações:** foram necessárias **19 iterações versionadas da entrega**, contadas pelos commits exclusivos desta branch até a adequação final ao template. Elas cobrem implementação inicial, correção de escopo, revisão da narrativa executiva, publicação, transformação do dashboard em ferramenta de decisão, branding, acessibilidade visual, temas, internacionalização, atualização das evidências e conformidade final. Testes e revisões internas executados dentro do mesmo commit não foram inflados como iterações separadas; a sequência completa pode ser auditada no [histórico da PR #91](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/91/commits).

1. Li o desafio e converti as perguntas em critérios verificáveis e entregáveis.
2. Modelei uma arquitetura de agentes com responsabilidades limitadas, contexto mínimo e contratos de handoff.
3. O Data Engineer auditou o dataset e preparou a camada analítica; o Software Engineer criou a fundação técnica, contratos e testes.
4. Data Analyst e Statistician mediram diferenças, incerteza e efeitos ajustados antes de qualquer recomendação.
5. Revisei os resultados e rejeitei rankings que eram numericamente diferentes, mas materialmente irrelevantes.
6. O gate de ML foi encerrado como `NO-GO`, evitando fabricar valor preditivo com sinal sintético e fraco.
7. O Marketing Strategist converteu evidências em hipóteses testáveis; o Dashboard Builder transformou-as em uma interface acionável.
8. O Software Engineer integrou o fluxo e os testes; Executive Writer e Reviewer passaram a entrega por ciclos de clareza e consistência.
9. Fiz inspeção visual, corrigi tema, contraste, idiomas e navegação e publiquei o dashboard para acesso sem instalação.
10. Preservei conversas, vídeos, imagens, erros, correções e histórico Git em um manifesto de evidências.

### Onde a IA errou e como corrigi

- **Confundiu diferença numérica com recomendação:** rankings iniciais pareciam indicar vencedores. Eu exigi tamanho de efeito, intervalo de confiança, controles e relevância prática; a conclusão mudou para “sem vencedor acionável”.
- **Sugeriu Machine Learning sem utilidade comprovada:** apliquei um gate de valor preditivo e registrei `NO-GO`, em vez de entregar um modelo que aprenderia ruído sintético.
- **Arriscou extrapolar alcance para retorno:** removi qualquer alegação de ROI porque faltam custos, conversões, receita e atribuição.
- **Perdeu continuidade em respostas longas:** o Claude Code retornou `Connection closed mid-response`. Conferi arquivos e manifests antes de retomar apenas as etapas incompletas, sem presumir sucesso.
- **Gerou problemas visuais e de tradução:** fiz testes manuais em temas claro/escuro e nos três idiomas, corrigi contraste, labels internos e componentes embutidos.

### O que eu adicionei que a IA sozinha não faria

Meu principal julgamento foi recusar uma resposta vistosa, mas frágil. Eu defini a fronteira entre descrição e causalidade, decidi não treinar ML sem sinal útil, transformei “não há vencedor” em uma política de experimentação e incluí break-even, owners, guardrails e stop conditions para que o Head de Marketing consiga agir. Também desenhei a divisão de autoridade entre agentes, revisei visualmente o produto e mantive as limitações próximas de cada decisão, mesmo quando isso tornava a narrativa menos promocional.

A arquitetura, os prompts e o protocolo de handoff estão em [Arquitetura de agentes](docs/agent-architecture.md), [Prompts dos agentes](.claude/agents/) e [Protocolo de handoff](docs/handoff-protocol.md).

---

## Evidências

- [x] [Screenshots das conversas e do processo](process-log/evidence/images/)
- [x] [Screen recordings do workflow](process-log/evidence/videos/)
- [x] [Chat export cronológico](process-log/chat-export.md) e [links das conversas externas](process-log/evidence/links/linksdechats.txt)
- [x] [Git history e Pull Request #91](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/91)
- [x] [Manifesto de evidências com inventário e hashes](process-log/evidence-manifest.md)
- [x] [Process Log completo](process-log/README.md)

---

*Submissão enviada em: 16 de julho de 2026*

**Felipe de Oliveira Freire**<br>
*Cientista/Analista de Dados*
