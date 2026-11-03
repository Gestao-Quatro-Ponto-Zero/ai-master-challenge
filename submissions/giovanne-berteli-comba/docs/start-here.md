# A entrega em uma página

> **Aprendizado central:** acurácia não é economia. A objeção do candidato ao
trabalho adicional do fluxo individual levou à triagem em lote e a uma comparação
manual/assistida instrumentada. [Veja o aprendizado, o protocolo e como participar](operational-learning.md).

**Decisão para a empresa:** validar a fila e a instrumentação; testar assistência
à triagem com confirmação humana e medir o ganho líquido antes de expandir.

| Pergunta | Resposta e decisão |
| --- | --- |
| Qual era o problema? | Entender onde o suporte perde tempo, o que automatizar e demonstrar algo funcionando. |
| O que encontramos? | 5.700/8.469 não encerrados, incluindo 1.403 Critical; 1.102/2.769 encerrados avaliados deram nota 1–2. O arquivo não informa abertura ou esforço ativo: duração, SLA e desperdício real em horas não são mensuráveis. |
| O que construímos? | Diagnóstico com fontes; triagem IT individual/em lote com confirmação, histórico e anomalias; painel, exportação, simulador e ensaio manual/assistido pronto para participação humana. |
| O que o modelo mostrou? | Macro F1 0,844612 contra 0,646094 do baseline de texto em 7.175 casos IT. Sugestões padrão: 1.951/7.175 (27,19%), com 1.884/1.951 concordâncias (96,57%). Houve 67 divergências, 50 de classes especializadas: toda sugestão precisa de confirmação. |
| Qual o próximo passo do negócio? | Conferir Critical/status, distinguir espera do cliente de trabalho do agente, investigar motivos das notas e comparar fluxo atual/assistido num piloto com novos dados. |
| Qual benefício esperar? | A hipótese de referência é 29,75 h/mês; cenários vão de −26,67 a +74,75 h/mês. São premissas para planejar um piloto, sem economia medida ou de caixa. |

Os datasets cumprem papéis diferentes: atendimento descreve fila/satisfação;
IT avalia a classificação em seu próprio domínio. Não há junção ou transferência
validada de desempenho. Fontes: [diagnóstico](operational-diagnosis.md),
[avaliação](final-evaluation.md), [premissas](../data/diagnosis-assumptions.json).

## Meu papel e o papel da IA

O candidato **escolheu o desafio, definiu requisitos de anomalias e evidências,
confrontou os erros do setup/tour e orientou esta rodada para clareza, reprodução
e valor de negócio**. A IA **auditou dados, propôs métodos, escreveu a implementação,
calculou resultados e executou testes** sob essa direção. A triagem local usa
TF-IDF e regressão logística; IA generativa foi usada no desenvolvimento.

Exemplos: o relato humano de falha ao repetir o setup levou ao reuso de treino
válido; o CodeTour que não aparecia levou ao workspace com inicializador e teste
na extensão real. [Correções e falas preservadas](../process-log/README.md).
Não foi realizada adjudicação humana dos rótulos nem medição de ganho operacional.

## Experimente e confira

No início da aplicação, escolha **Perfil de visualização**:

- **Empresa** (padrão): resultados de atendimento, ações propostas, capacidade e, na aplicação completa, triagem em lote.
- **Instrutor**: guia de avaliação, autoria humano/IA, diagnóstico com fontes,
  benchmark IT, demonstração e evoluções futuras. No modo completo, inclui lote, **Experimento**, Triagem
  e Revisão/exportação; na consulta de agregados, explica como habilitá-las.

Leia esta página sem instalar nada. Em **Linux x86_64/glibc**, na raiz do repo:

```bash
bash submissions/giovanne-berteli-comba/run.sh --overview
```

Isso abre diagnóstico, resultados, simulador e evoluções usando agregados salvos,
sem baixar datasets ou treinar. O primeiro preparo do ambiente requer internet.
Para a demonstração completa, use o mesmo comando **sem `--overview`** e siga o
[roteiro de cinco minutos](demo-guide.md). A interface estará em
[127.0.0.1:8501](http://127.0.0.1:8501); Ctrl+C encerra o servidor.
Veja [setup e reprodução por objetivo](prototype.md) para os pré-requisitos.

## Confira a implementação com CodeTour

Com **VS Code instalado**, execute na raiz do repositório:

```bash
bash submissions/giovanne-berteli-comba/review.sh
```

O comando abre o workspace correto e confere/instala a extensão oficial CodeTour.
Clique em **Start CodeTour** na notificação; ele também aparece no Explorer.
São **13 paradas**, do problema à implementação e às evidências. A instalação da
extensão requer internet. Para ler sem VS Code ou extensão, siga o
[roteiro em Markdown](code-tour.md). O mesmo comando está no Guia do instrutor da aplicação.

## O que podemos afirmar sobre a qualidade

Há evidência de implementação funcional e melhora de classificação sobre o baseline
de texto deste projeto. O diagnóstico quantifica fila/notas e explicita dados ausentes;
ele responde parcialmente às perguntas sobre gargalos, mas não comprova duração,
causas de insatisfação ou desperdício real em horas. O benefício operacional e a
transferência para uma empresa precisam de piloto com novos dados. Esses limites
permitem defender uma entrega verificável sem antecipar uma nota da seleção ou
comparação com seu baseline privado, que não foi acessado.

## O que ficou para evolução

Foram pensadas IA analista sobre métricas calculadas, integração com Google Sheets,
email, Discord/canal interno, bot e helpdesk. São **evoluções planejadas, fora do
escopo entregue**, com benefícios e dependências descritos no
[roadmap](future-roadmap.md). A entrega priorizou um fluxo verificável e reproduzível.

## Faça a comparação com participação humana

Execute o modo completo, selecione **Instrutor → Experimento** e siga as duas etapas.
São oito tickets por etapa, distintos e provenientes do treino; os rótulos ficam
ocultos até concluir ambas. Identifique sua participação como **Operador (declarado)**;
automação usa o tipo próprio. Tempo, concordância, correções e falhas serão registrados,
inclusive resultados desfavoráveis. [Roteiro e limites do ensaio](operational-learning.md).
A ferramenta não apresenta execução automatizada como ganho humano ou ROI real.
