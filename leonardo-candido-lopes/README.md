# Submissão — Leonardo Candido Lopes — Challenge 002

## Sobre mim

- **Nome:** Leonardo Candido Lopes
- **LinkedIn:** https://www.linkedin.com/in/leonardo-candido-lopes-04ab06267/
- **Challenge escolhido:** 002 — Redesign de Suporte (Operações / CX)

---

## Executive Summary

Desenvolvi um diagnóstico de suporte, um redesign operacional e um protótipo funcional de triagem assistida usando os dois datasets públicos indicados no desafio. A principal decisão analítica foi não transformar o Dataset 1 em indicadores operacionais: a auditoria encontrou fortes sinais de artificialidade e inconsistências que impedem conclusões confiáveis sobre SLA, produtividade e satisfação. O Dataset 2 sustentou um classificador de oito categorias de TI com F1-macro de 0,8403 em teste; porém, como o detector de domínio não possui validação representativa, a versão final bloqueia o roteamento automático e mantém confirmação humana. O ROI é apresentado como projeção paramétrica, não como economia comprovada; no cenário-base, o resultado líquido estimado é negativo.

## Solução

### Abordagem

1. **Auditoria antes da modelagem.** Avaliei estrutura, completude, consistência e utilidade dos dois conjuntos antes de definir quais conclusões poderiam ser sustentadas.
2. **Separação dos domínios.** O Dataset 1 representa tickets B2C de suporte ao consumidor; o Dataset 2 representa chamados internos de TI. Não forcei uma junção entre eles nem tratei as taxonomias como equivalentes.
3. **Redesign operacional.** Estruturei a atuação em automação restrita, assistência por IA e decisão humana, com regras explícitas de segurança, escalonamento e rastreabilidade.
4. **Modelo e protótipo.** Treinei o classificador apenas no Dataset 2 e integrei a inferência a uma API FastAPI e a uma interface Next.js.
5. **Contenção orientada por evidência.** Ao identificar que o detector de domínio não era confiável e que o limiar de similaridade usado numa versão intermediária não discriminava domínio, removi esse critério. A versão final mantém a categoria como sugestão e não libera roteamento automático.

### Resultados / Findings

#### Dados e diagnóstico

- **Dataset 1 — Customer Support Ticket Dataset:** a auditoria encontrou inconsistências estruturais e semânticas fortes, incluindo placeholders em descrições, emails de exemplo, resoluções padronizadas sem valor operacional e campos temporais que não sustentam métricas confiáveis. A conclusão é de fortes evidências de artificialidade, não de comprovação documental da origem. Por isso, o dataset foi usado para demonstrar limites de qualidade e formular hipóteses, não para declarar tempos reais de resolução, SLA ou produtividade.
- **Dataset 2 — IT Service Ticket Classification Dataset:** usado como base do classificador de chamados internos de TI, mantendo sua taxonomia original de oito categorias. A limpeza, quarentena, split e avaliação estão documentados em `solution/fase4/ml/00_pipeline_audit.md`, `solution/fase4/ml/process_log_ml.md` e `solution/fase4/ml/splits/`.
- Os dois datasets não possuem chave de ligação válida. A análise os utiliza de forma complementar, sem sugerir que pertencem à mesma operação.

#### Redesign operacional

A proposta separa:

- **Automação:** apenas tarefas repetitivas e de baixo risco, condicionadas à validação real do domínio, à qualidade da categoria e a um piloto controlado.
- **Assistência por IA:** classificação sugerida, prioridade estimada, fila recomendada e justificativa para o agente confirmar.
- **Atuação humana obrigatória:** privilégios administrativos, baixa confiança, domínio não identificado, casos fora de escopo e situações de risco.
- **Escalonamento:** sinais de comprometimento de conta e incidentes críticos seguem regras explícitas de escalonamento.

A versão final do protótipo não executa ações em sistemas externos e não realiza roteamento automático. Essa restrição é intencional: o detector de domínio não foi validado com amostra representativa de tickets fora do domínio.

#### Modelo

- **Pipeline:** TF-IDF (1–2-gramas, até 50 mil features) + LinearSVC calibrado por isotonic regression.
- **F1-macro:** 0,8403 no conjunto de teste (n = 6.766); baseline ingênuo: 0,0556.
- **F1-macro em textos sem quase-vizinho no treino:** 0,8204 (n = 5.740), leitura mais conservadora para textos novos.
- **Categoria mais fraca:** Administrative rights, F1 = 0,7597 e recall = 0,673.
- **Casos ponta a ponta:** 12/15 atendem aos critérios definidos para a suíte final. Permanecem três falhas documentadas: pedido de compra em linguagem natural classificado como Hardware; categoria incorreta em solicitação de privilégio administrativo (com revisão humana acionada); e mensagem sobre almoço corporativo classificada como TI e encaminhada para assistência, em vez de ser reconhecida como fora de escopo.
- Os números de cobertura/precisão por limiar (65,6%/95,8% e 83,0%/91,0%) medem o classificador de categoria antes da regra final R9. **Não representam cobertura/precisão do roteamento operacional final.**
- **Política final:** 0 decisões AUTOMATIC; decisões que chegariam à automação são rebaixadas para ASSISTED pela regra R9, até que o domínio seja validado com dados reais representativos.

#### Protótipo funcional

A aplicação combina:

- **Frontend:** Next.js, com páginas de triagem, métricas e explicação do sistema.
- **Backend:** FastAPI, com endpoints `/classify`, `/health`, `/test-cases` e `/model-metadata`.
- **Inferência:** modelos salvos em `solution/fase4/ml/model/` e regras de segurança explícitas.
- **Rastreabilidade:** domínio, categoria prevista, confiança, top-3, prioridade, decisão, regra acionada e justificativa.

O protótipo recomenda classificação e encaminhamento; não executa ações, não concede acessos, não responde ao cliente e não altera tickets em plataformas externas.

#### ROI

O ROI é um modelo paramétrico com cenários conservador, base e otimista. As premissas não observadas nos datasets estão identificadas como hipóteses ou benchmarks. No cenário-base, a capacidade recuperada projetada é de aproximadamente 150 horas/mês (cerca de 1,03 FTE), mas a economia financeira realizada estimada é de R$ 3.049/mês diante de R$ 5.000/mês de custo recorrente, resultando em **−R$ 1.951/mês**. Portanto, o cenário-base não demonstra payback financeiro; a justificativa depende de qualidade, controle, capacidade e escala. A capacidade recuperada não é apresentada como economia de caixa automática.

### Recomendações

1. **Não ativar automação autônoma nesta etapa.** Rodar um piloto em shadow mode com tickets reais, revisão humana e amostragem estratificada.
2. **Validar o detector de domínio.** Coletar exemplos reais de TI e de mensagens corporativas fora de TI, com rótulos revisados por pessoas da operação; só então recalibrar a decisão de domínio.
3. **Medir a operação antes de monetizar o ROI.** Registrar volume, AHT, tempo de triagem, reabertura, escalonamento, resolução no primeiro contato e custo efetivo.
4. **Corrigir a taxonomia de Purchase e Administrative rights.** Revisar exemplos e rótulos de origem, ampliar vocabulário de compras em linguagem natural e manter privilégios sob aprovação humana.
5. **Reavaliar limiares com dados do piloto.** Não reutilizar automaticamente os limiares atuais se a distribuição real diferir do Dataset 2.

### Limitações

- O Dataset 1 não sustenta indicadores operacionais reais; sua artificialidade é uma inferência apoiada em evidências, não uma declaração documental de proveniência.
- O Dataset 2 é de TI interna e em inglês; não representa automaticamente suporte B2C, outros idiomas ou a operação do G4.
- O detector de domínio não foi validado em amostra representativa. O resultado de validação anteriormente perfeito é inválido como evidência de generalização, pois os negativos usados eram sintéticos.
- O classificador apresenta erros conhecidos, especialmente em Purchase e Administrative rights.
- O conjunto de teste tem diferenças de proporção em Purchase em relação ao treino, documentadas no process log.
- O protótipo depende da execução local da API Python e do frontend Next.js. Não há implantação pública permanente incluída nesta submissão.
- Os screenshots incluídos registram versões de desenvolvimento e devem ser lidos em conjunto com o log e os resultados pós-R9; não são evidência de que a versão final roteie automaticamente.
- O ROI é projeção baseada em premissas editáveis, não resultado observado.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Uso |
|---|---|
| Abacus AI | Execução assistida de análise exploratória, scripts, treinamento, avaliação, regras de decisão, API, interface e captura de evidências. |
| ChatGPT | Estruturação do problema, decomposição das fases, elaboração de instruções para a execução, questionamento de premissas, revisão de inconsistências e documentação das decisões. |
| Python / bibliotecas de dados e ML | Execução dos pipelines, avaliação e geração dos artefatos reproduzíveis. |
| Playwright | Captura automatizada de evidências da interface. |

### Workflow

1. Li o desafio e defini que as decisões deveriam ser sustentadas por dados e fontes, sem preencher lacunas com suposições apresentadas como fatos.
2. Auditei o Dataset 1 e identifiquei sinais fortes de artificialidade e inconsistências; decidi não usá-lo para declarar KPIs operacionais reais.
3. Analisei o Dataset 2, documentei limpeza e quarentena, separei treino/validação/teste e avaliei modelos para classificação de TI.
4. Desenhei o fluxo operacional, a matriz de automação, os KPIs e o ROI paramétrico, identificando premissas sem dados observados.
5. Construí o classificador, as regras de segurança e o protótipo web integrado à API.
6. Ao revisar a regra R9, identifiquei que o limiar de similaridade 0,49 havia sido interpretado incorretamente como mediana in-domain. A análise posterior mostrou que era a mediana de uma população mista e que similaridade não discriminava domínio. O critério foi removido.
7. Como não havia sinal validado para autorizar roteamento autônomo, decidi manter o humano no loop: R9 rebaixa para ASSISTED qualquer caso que chegaria a AUTOMATIC. As falhas conhecidas foram preservadas e documentadas.

### Onde a IA errou e como corrigi

- **Dataset 1:** a estrutura anunciada poderia induzir o uso de métricas como se fossem reais. A auditoria de qualidade levou à restrição explícita das conclusões.
- **Detector de domínio:** o resultado de validação inicialmente perfeito não generalizava, pois os negativos eram sintéticos e continham pistas artificiais. Foi reclassificado como não validado.
- **Regra de similaridade R9:** a justificativa original do corte 0,49 estava incorreta. O corte foi removido, sem substituição por outro número não validado.
- **Classificador:** erros em Purchase, Administrative rights e mensagens fora de escopo foram mantidos visíveis; não foram escondidos para melhorar artificialmente a taxa de aprovação.

### O que eu adicionei que a IA sozinha não faria

- Priorizei integridade analítica sobre produzir métricas atraentes quando os dados não sustentavam as conclusões.
- Mantive separados os domínios B2C e TI interna, sem forçar uma integração artificial.
- Questionei a fundamentação estatística do limiar de similaridade e determinei sua remoção após a evidência contraditória.
- Aceitei perder utilidade de automação para preservar segurança e transparência enquanto a validação de domínio não existir.
- Explicitei que capacidade recuperada, valor econômico potencial e economia financeira realizada são conceitos diferentes.

### Evidências

- `process-log/process_log_ml.md` — registro técnico cronológico das decisões, iterações, erros e correções da Fase 4.
- `process-log/chat-exports/` — instruções, decisões e prompts de trabalho preservados durante as fases.
- `solution/fase4/evidencias/` — capturas da interface e respostas brutas associadas.
- `solution/fase4/ml/test_results_pos_ajuste.json` — resultado dos casos após a correção final R9 v4.

**Nota de integridade:** os arquivos de `chat-exports/` são registros de prompts e decisões enviados durante o trabalho, não uma transcrição integral de todas as respostas da conversa do Abacus. O process log técnico complementa esses registros.

---

Submissão preparada em: 12/11/2026
