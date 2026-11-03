# Guia para revisar a entrega

Comece pelo [README](../README.md), que reúne resultado, execução e uso de IA.
Para inspecionar a implementação, siga o [CodeTour ou roteiro em Markdown](code-tour.md).
Para abrir o editor já no contexto certo, execute na raiz:
`bash submissions/giovanne-berteli-comba/review.sh` (ou `bash review.sh` na submissão).
O tour aparece no Explorer e é oferecido na primeira visita ao workspace.
O protótipo abre com um comando; as evidências finais podem ser lidas sem carregar
modelos ou executar novamente o teste consumido.

A [investigação antes da submissão](pre-submission-review.md), solicitada em
03/11/2026, avalia compreensão, autoria humano/IA, reprodução e uso dos resultados
para decisões. Ela também prioriza melhorias imediatas e integrações futuras;
essas propostas ainda não foram implementadas.

## O que conferir e onde

| Pergunta do desafio/revisor | Evidência | O que ela não demonstra |
| --- | --- | --- |
| Onde o fluxo pode estar travando? | [Diagnóstico](operational-diagnosis.md), [150 segmentos](../data/diagnosis-segments.csv), [auditoria](data-audit.md) | Proporção não encerrada não mede idade/duração/causa do atraso |
| O que afeta satisfação? | [Populações, distribuições e três associações](operational-diagnosis.md) | Notas só de encerrados; associações exploratórias sem causalidade ou efeito convincente |
| Quanto se desperdiça? | [Premissas](../data/diagnosis-assumptions.json) e [cenários, incluindo negativo](operational-diagnosis.md) | Horas são hipóteses; não houve esforço ativo observado nem economia medida |
| Foram usados ambos os datasets? | [Papéis e limites D02](../knowledge/dataset-usage.md) | Não há join, taxonomia comum ou transferência validada de acurácia |
| O que automatizar e onde humano atua? | [Proposta/fluxo](automation-proposal.md), [contrato](../knowledge/solution-scope.md), [protótipo](prototype.md) | Nenhum envio externo, decisão empresarial autônoma ou resolução automática |
| Funciona além dos exemplos da tela? | [7.175 casos finais](final-evaluation.md), [resultado agregado](../data/final-evaluation.json) | Os três exemplos de treino da UI são demonstração, não a avaliação do modelo |
| Como anomalias e falhas são tratadas? | [Testes](review-evidence/final-evaluation-tests.txt), [runtime/faults](final-evaluation.md) e [core/repositório](code-tour.md) | Raridade não é erro confirmado; fixtures não são adjudicação humana |
| Outra pessoa consegue iniciar? | [Setup](prototype.md), [reprodução limpa/offline](review-evidence/setup-reproduction.json) | Bootstrap testado em Linux x86_64/glibc; primeira instalação exige rede/escrita/espaço |
| Como IA e julgamento humano se combinaram? | [Process log](../process-log/README.md), [cobertura das capturas](conversation-coverage.md) e seção do README | Capturas não provam completude do histórico nem uso de ferramentas só discutidas |

## Decisões e alternativas

| Decisão | Alternativa descartada ou limitada | Rastro |
| --- | --- | --- |
| Humano escolheu o 002 após comparar opções | Recomendar 004 apenas pela contagem de PRs não estabelecia aderência/chance | [Preparação](../process-log/01-preparation-and-foundation.md) |
| Agente separou diagnóstico e benchmark | Misturar labels, inventar join ou mapear nomes não forneceria ground truth | [D02](../process-log/07-dataset-usage.md) |
| Proposta local assistida com confirmação | LLM remoto, integração externa e autonomia não eram necessários para o escopo | [S01](../process-log/10-automation-scope.md) |
| Grupos similares inteiros e protocolo prévio | Divisão aleatória por linha poderia espalhar textos parecidos; teste não seleciona parâmetros | [V00](../process-log/11-evaluation-protocol.md) |
| Candidato confrontou o setup real | Passos manuais e traceback ao repetir treino foram corrigidos por inicializador idempotente | [Correção](../process-log/13-setup-fix.md) |
| Versão congelada foi avaliada sem retuning | Não escolher novo modelo/limiar depois de conhecer erros finais | [V01](../process-log/14-final-evaluation.md) |

As decisões humanas comprovadas são escolha do desafio, requisitos de anomalias,
finalidade do process log e cobrança sobre o uso real do setup. Os métodos, stack
e parâmetros são escolhas técnicas do agente no escopo autorizado; não implicam
aprovação humana de negócio ou revisão dos rótulos.

## Como ler a força da evidência

- **Medido/calculado:** contagens dos arquivos, métricas com rótulos fornecidos,
  execução de software, amostra local de latência. Há fontes, código, saídas e hashes.
- **Premissa:** custos adimensionais, minutos/economia dos cenários, política de
  especialista e metas de aceitação. Não são políticas confirmadas de uma empresa.
- **Pendente/indisponível:** identidade final, adjudicação humana, validação na
  operação de clientes, implantação/PR e observações individuais do relógio externo.

Hashes verificam identidade/alteração, não semântica dos rótulos ou aprovação de
negócio. O maior risco observado permanece visível: 50 dos 67 erros na fila padrão
eram de classes especializadas. Não se apresenta 96,57% de concordância no
subconjunto como percentual de tickets resolvidos.

## Verificar sem outra avaliação final

Na pasta da submissão, após o setup:

```bash
python3 -I scripts/check_review_evidence.py
.venv/bin/python -I scripts/check_final_evaluation.py
python3 -I scripts/check_foundation.py
```

O primeiro verifica a apresentação/tour/cobertura. O segundo reagrega os registros
salvos, sem prever ou treinar; o terceiro confere os contratos/recibo da fundação.
Não apague a tentativa final nem altere o freeze para apresentar outra avaliação
como inédita. Uma reprodução em outro ambiente precisa registrar suas diferenças.

## Próximo passo e itens de envio

O [teste real do CodeTour](review-evidence/codetour-discovery.json) reproduz a
ausência de descoberta na raiz e a navegação das 11 âncoras no workspace de revisão.
Perfis de teste são isolados; o inicializador preserva a janela anterior e não
altera arquivos/configurações do repositório pai. VS Code é um pré-requisito local;
se a extensão faltar no perfil, sua instalação precisa de acesso ao Marketplace.

P01 deve confirmar nome e LinkedIn, conferir template/escopo/setup final e preparar
o envio via PR conforme as regras do repositório. E01 não cria commit, push ou PR,
nem inventa dados do candidato. A [tabela oficial F01–F07](architecture-review.md#lista-oficial-para-validação)
continua sendo a única fonte do estado dos achados de arquitetura.
